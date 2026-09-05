#!/usr/bin/env python3
"""check_lwc_testing.py — audit an LWC source tree for Jest harness defects.

Stdlib only. Reads a Salesforce source tree (``--manifest-dir``) and reports the
harness failures that make an LWC Jest suite flaky or falsely green.

Rules
-----
ERROR  test file appends to ``document.body`` with no ``afterEach`` DOM cleanup
ERROR  ``jest.mock`` of an ``@salesforce/`` scoped module without ``{ virtual: true }``
ERROR  test file contains zero ``expect(`` assertions
WARN   component bundle has no ``__tests__/`` folder
WARN   an ``expect(`` follows a wire ``.emit(``/``.error(`` with no awaited microtask
WARN   test imports the legacy ``register*TestWireAdapter`` API
WARN   a ``.forceignore`` exists but does not ignore ``__tests__``

Exit codes
----------
1  ``--manifest-dir`` does not exist, or any ERROR was reported
0  otherwise (WARNs alone do not fail unless ``--strict`` promotes them)

Usage
-----
    python3 check_lwc_testing.py --manifest-dir force-app/main/default/lwc
    python3 check_lwc_testing.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- patterns --

# jest.mock('<specifier>' ... ) — capture the specifier and the whole call text.
JEST_MOCK_RE = re.compile(r"jest\.mock\(\s*['\"]([^'\"]+)['\"]")
SALESFORCE_MODULE_RE = re.compile(r"^@salesforce/")
LEGACY_ADAPTER_RE = re.compile(r"\bregister(Apex|Lds|)TestWireAdapter\b")
MODERN_ADAPTER_HINT = (
    "createApexTestWireAdapter / createLdsTestWireAdapter / createTestWireAdapter "
    "from '@salesforce/sfdx-lwc-jest', or emit() directly on the imported adapter"
)
# A wire emission: getRecord.emit(...), adapter.error(...), .emitError(...)
EMIT_RE = re.compile(r"\.\s*(emit|emitError|error)\s*\(")
EXPECT_RE = re.compile(r"\bexpect\s*\(")
# Anything that yields to the microtask queue before the next assertion.
MICROTASK_RE = re.compile(
    r"await\s|\breturn\s+Promise\s*\.\s*resolve\s*\(|Promise\s*\.\s*resolve\s*\(\s*\)\s*\.\s*then|"
    r"\bflushPromises\s*\(|process\s*\.\s*nextTick|setTimeout\s*\("
)
BLOCK_START_RE = re.compile(r"^\s*(?:it|test)(?:\.\w+)?\s*\(")
TEST_FILE_RE = re.compile(r"\.(test|spec)\.(js|ts)$")


# ------------------------------------------------------------------ finding --

class Finding:
    __slots__ = ("level", "where", "message")

    def __init__(self, level: str, where: str, message: str) -> None:
        self.level = level
        self.where = where
        self.message = message

    def render(self) -> str:
        return f"{self.level}: {self.where}: {self.message}"


# ------------------------------------------------------------- file finding --

def component_bundles(root: Path) -> list[Path]:
    """A bundle is a directory holding <dirname>.js next to <dirname>.js-meta.xml."""
    bundles: list[Path] = []
    for meta in sorted(root.rglob("*.js-meta.xml")):
        bundle = meta.parent
        if (bundle / f"{bundle.name}.js").exists():
            bundles.append(bundle)
    return bundles


def test_files(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*")) if p.is_file() and TEST_FILE_RE.search(p.name)]


def find_forceignore(root: Path) -> Path | None:
    """Look for .forceignore at the tree root, then walk up to 4 parents."""
    candidate = root / ".forceignore"
    if candidate.is_file():
        return candidate
    here = root.resolve()
    for _ in range(4):
        here = here.parent
        candidate = here / ".forceignore"
        if candidate.is_file():
            return candidate
    return None


# ------------------------------------------------------------------- checks --

def strip_comments(text: str) -> str:
    """Blank out // and /* */ comments so they cannot satisfy or trip a rule."""
    out = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return re.sub(r"//[^\n]*", "", out)


def check_jest_mock_virtual(path: Path, text: str) -> list[Finding]:
    """Every jest.mock of a @salesforce/* module must pass { virtual: true }.

    The module has no file on disk, so without the flag Jest throws
    "Cannot find module" at collection time and the whole suite fails.
    """
    findings: list[Finding] = []
    for match in JEST_MOCK_RE.finditer(text):
        specifier = match.group(1)
        if not SALESFORCE_MODULE_RE.match(specifier):
            continue
        # Scan forward, balancing parens, to find the end of this jest.mock call.
        depth = 0
        end = match.end()
        for idx in range(match.start(), len(text)):
            char = text[idx]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        call = text[match.start():end]
        if "virtual" not in call:
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                Finding(
                    "ERROR",
                    f"{path}:{line}",
                    f"jest.mock('{specifier}') has no `{{ virtual: true }}` option — "
                    "the @salesforce scoped module is compiler-generated and has no file "
                    "on disk, so Jest cannot resolve it and the suite fails to load.",
                )
            )
    return findings


def check_dom_cleanup(path: Path, text: str) -> list[Finding]:
    """jsdom is shared across every test in a file; leftovers leak between tests."""
    if "document.body.appendChild" not in text:
        return []
    if "afterEach" not in text:
        return [
            Finding(
                "ERROR",
                str(path),
                "appends to document.body but has no `afterEach` — the jsdom instance is "
                "shared across all tests in the file, so mounted elements leak into later "
                "tests (lwc_guide unit-testing-using-jest-create-tests L12363).",
            )
        ]
    after = text[text.index("afterEach"):]
    if "removeChild" not in after and "innerHTML" not in after:
        return [
            Finding(
                "ERROR",
                str(path),
                "has an `afterEach` that never removes mounted elements — add the "
                "`while (document.body.firstChild) document.body.removeChild(...)` loop.",
            )
        ]
    return []


def check_assertions_present(path: Path, text: str) -> list[Finding]:
    if EXPECT_RE.search(text):
        return []
    return [
        Finding(
            "ERROR",
            str(path),
            "contains no `expect(` — the file runs the component but asserts nothing, "
            "so it can never fail and counts as false coverage.",
        )
    ]


def _blocks(lines: list[str]) -> list[tuple[int, list[str]]]:
    """Split a test file into (start_line, lines) chunks, one per it()/test()."""
    starts = [i for i, ln in enumerate(lines) if BLOCK_START_RE.match(ln)]
    if not starts:
        return [(1, lines)]
    blocks: list[tuple[int, list[str]]] = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        blocks.append((start + 1, lines[start:end]))
    return blocks


def check_emit_without_flush(path: Path, text: str) -> list[Finding]:
    """An assertion straight after a wire emission reads the pre-rerender DOM."""
    findings: list[Finding] = []
    for offset, block in _blocks(text.splitlines()):
        emit_at = None
        for idx, line in enumerate(block):
            if EMIT_RE.search(line) and "jest.fn" not in line:
                emit_at = idx
                continue
            if emit_at is None:
                continue
            if EXPECT_RE.search(line):
                between = block[emit_at:idx + 1]
                if not any(MICROTASK_RE.search(b) for b in between):
                    findings.append(
                        Finding(
                            "WARN",
                            f"{path}:{offset + idx}",
                            "asserts after a wire emission with no awaited microtask in "
                            "between — rerender is asynchronous, so add "
                            "`await Promise.resolve();` before the assertion "
                            "(lwc_guide unit-testing-using-wire-utility L12549).",
                        )
                    )
                emit_at = None
    return findings


def check_legacy_adapter(path: Path, text: str) -> list[Finding]:
    match = LEGACY_ADAPTER_RE.search(text)
    if not match:
        return []
    line = text.count("\n", 0, match.start()) + 1
    return [
        Finding(
            "WARN",
            f"{path}:{line}",
            f"uses the legacy `{match.group(0)}` API. Registering the adapter under test "
            "was the Spring '21-and-earlier shape and is no longer recommended "
            "(lwc_guide unit-testing-using-wire-utility L12562). Modern form: "
            f"{MODERN_ADAPTER_HINT}.",
        )
    ]


def check_missing_tests(bundle: Path) -> list[Finding]:
    tests_dir = bundle / "__tests__"
    if tests_dir.is_dir() and any(TEST_FILE_RE.search(p.name) for p in tests_dir.rglob("*")):
        return []
    return [
        Finding(
            "WARN",
            str(bundle),
            "component bundle has no `__tests__/` test file — Jest runs JavaScript files "
            "in the __tests__ directory of the bundle "
            "(lwc_guide create-components-tests L761).",
        )
    ]


def check_forceignore(root: Path) -> list[Finding]:
    path = find_forceignore(root)
    if path is None:
        return []
    body = path.read_text(encoding="utf-8", errors="ignore")
    if "__tests__" in body:
        return []
    return [
        Finding(
            "WARN",
            str(path),
            "exists but never ignores `__tests__` — add `**/__tests__/**` so push/pull "
            "and deploy commands skip the test folder "
            "(lwc_guide unit-testing-using-jest-create-tests L12329).",
        )
    ]


# --------------------------------------------------------------------- main --

def run(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_forceignore(root))

    for bundle in component_bundles(root):
        findings.extend(check_missing_tests(bundle))

    for path in test_files(root):
        raw = path.read_text(encoding="utf-8", errors="ignore")
        text = strip_comments(raw)
        findings.extend(check_jest_mock_virtual(path, text))
        findings.extend(check_dom_cleanup(path, text))
        findings.extend(check_assertions_present(path, text))
        findings.extend(check_emit_without_flush(path, text))
        findings.extend(check_legacy_adapter(path, text))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit an LWC source tree for Jest harness defects.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the LWC source tree (for example force-app/main/default/lwc).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote every WARN to an ERROR (use in CI).",
    )
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: --manifest-dir not found: {root}")
        return 1

    scanned_bundles = component_bundles(root)
    scanned_tests = test_files(root)
    if not scanned_bundles and not scanned_tests:
        print(f"WARN: {root}: no LWC bundles and no *.test.js files found — nothing to check.")
        return 0

    findings = run(root)
    if args.strict:
        for finding in findings:
            if finding.level == "WARN":
                finding.level = "ERROR"

    for finding in sorted(findings, key=lambda f: (f.level != "ERROR", f.where)):
        print(finding.render())

    errors = sum(1 for f in findings if f.level == "ERROR")
    warns = len(findings) - errors
    print(
        f"\n{len(scanned_bundles)} bundle(s), {len(scanned_tests)} test file(s) scanned — "
        f"{errors} ERROR, {warns} WARN"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
