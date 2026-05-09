#!/usr/bin/env python3
"""Detect LWC jest a11y testing setup and assertion gaps.

Walks an SFDX-style force-app/ tree plus the project root and reports:

1. `package.json` missing `@salesforce/sfdx-lwc-jest` devDependency
2. `jest.config.js` missing OR not extending the official Salesforce preset
3. LWC components (under `force-app/main/default/lwc/<name>/`) with NO
   `__tests__/` directory at all
4. LWC test files (`*.test.js`) that contain a render harness but make NO
   accessibility-related assertions (no `aria-`, no `role=`, no
   `activeElement`, no `KeyboardEvent`, no `axe`)
5. LWC test files that query through `document.querySelector` instead of
   `shadowRoot.querySelector` (Anti-Pattern 2)
6. LWC test files that use real timers (`setTimeout` inside the test body) —
   a sign of incorrect async handling (Anti-Pattern 6)

Stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_jest_testing_with_accessibility.py
        [--root force-app/main/default]
        [--project-root .]

Exit codes:
    0  no findings
    1  findings present (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

OFFICIAL_PRESET_RE = re.compile(
    r"@salesforce/sfdx-lwc-jest(?:/config)?", re.IGNORECASE
)

A11Y_SIGNAL_RE = re.compile(
    r"\baria-|"
    r"role\s*=\s*['\"][a-z]+['\"]|"
    r"\.getAttribute\(\s*['\"](?:aria-|role|tabindex)|"
    r"shadowRoot\.activeElement|"
    r"new\s+KeyboardEvent|"
    r"\baxe\s*\(",
    re.IGNORECASE,
)

DOCUMENT_QUERY_RE = re.compile(
    r"\bdocument\.(?:querySelector|getElementById)\b"
)
SETTIMEOUT_IN_TEST_RE = re.compile(
    r"\bsetTimeout\s*\(", re.IGNORECASE
)
RENDER_HARNESS_RE = re.compile(
    r"\bcreateElement\s*\(", re.IGNORECASE
)
SHADOWROOT_QUERY_RE = re.compile(
    r"\.shadowRoot\.(?:querySelector|getElementById)\b"
)


def check_package_json(project_root: Path) -> list[str]:
    findings: list[str] = []
    pkg = project_root / "package.json"
    if not pkg.exists():
        findings.append(
            "package.json not found at project root — cannot verify "
            "@salesforce/sfdx-lwc-jest is installed"
        )
        return findings
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"package.json could not be parsed: {exc}")
        return findings
    deps = {}
    deps.update(data.get("devDependencies") or {})
    deps.update(data.get("dependencies") or {})
    if "@salesforce/sfdx-lwc-jest" not in deps:
        findings.append(
            "package.json: @salesforce/sfdx-lwc-jest not listed in "
            "(dev)Dependencies — install with `npm install --save-dev "
            "@salesforce/sfdx-lwc-jest`"
        )
    scripts = data.get("scripts") or {}
    has_test_script = any(
        "lwc-jest" in (v or "") or "sfdx-lwc-jest" in (v or "")
        for v in scripts.values()
    )
    if not has_test_script:
        findings.append(
            "package.json: no script invoking sfdx-lwc-jest — add "
            '"test:unit": "sfdx-lwc-jest" to scripts'
        )
    return findings


def check_jest_config(project_root: Path) -> list[str]:
    findings: list[str] = []
    cfg = project_root / "jest.config.js"
    if not cfg.exists():
        findings.append(
            "jest.config.js not found at project root — sfdx-lwc-jest expects "
            "a config file extending @salesforce/sfdx-lwc-jest/config"
        )
        return findings
    try:
        text = cfg.read_text(encoding="utf-8")
    except OSError as exc:
        findings.append(f"jest.config.js could not be read: {exc}")
        return findings
    if not OFFICIAL_PRESET_RE.search(text):
        findings.append(
            "jest.config.js: does not reference @salesforce/sfdx-lwc-jest — "
            "ensure the file extends the official preset"
        )
    return findings


def find_lwc_dirs(root: Path) -> list[Path]:
    lwc_root = root / "lwc"
    if not lwc_root.exists():
        return []
    return [d for d in lwc_root.iterdir() if d.is_dir()]


def check_lwc_test_coverage(root: Path) -> tuple[list[str], list[Path]]:
    """Returns (no-test findings, list of test files for assertion checks)."""
    findings: list[str] = []
    test_files: list[Path] = []
    for comp_dir in find_lwc_dirs(root):
        tests_dir = comp_dir / "__tests__"
        if not tests_dir.exists():
            findings.append(
                f"lwc/{comp_dir.name}/: no __tests__/ directory — "
                "component has no jest tests at all"
            )
            continue
        comp_tests = list(tests_dir.glob("*.test.js"))
        if not comp_tests:
            findings.append(
                f"lwc/{comp_dir.name}/__tests__/: no *.test.js files found"
            )
            continue
        test_files.extend(comp_tests)
    return findings, test_files


def check_test_file(fp: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = fp.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    has_render = bool(RENDER_HARNESS_RE.search(text))
    has_a11y = bool(A11Y_SIGNAL_RE.search(text))

    if has_render and not has_a11y:
        findings.append(
            f"{fp}: renders a component (createElement) but contains no "
            "a11y-related assertions (no aria-, role=, activeElement, "
            "KeyboardEvent, or axe call) — consider adding accessibility "
            "assertions"
        )

    if DOCUMENT_QUERY_RE.search(text) and SHADOWROOT_QUERY_RE.search(text):
        # Mixed usage — flag the document.* hits.
        for i, line in enumerate(text.splitlines(), start=1):
            if DOCUMENT_QUERY_RE.search(line):
                findings.append(
                    f"{fp}:{i}: document.querySelector/getElementById will "
                    "not pierce shadow DOM — use element.shadowRoot.* instead"
                )
                break
    elif DOCUMENT_QUERY_RE.search(text) and not SHADOWROOT_QUERY_RE.search(text):
        findings.append(
            f"{fp}: only uses document.querySelector / getElementById — "
            "queries inside an LWC must go through element.shadowRoot.*"
        )

    # setTimeout inside test bodies — note this excludes setTimeout in
    # commented imports / mocks.
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if SETTIMEOUT_IN_TEST_RE.search(line):
            findings.append(
                f"{fp}:{i}: setTimeout inside a test — prefer "
                "`await Promise.resolve()` chains or jest fake timers; real "
                "timers make tests slow and flaky"
            )
            break

    return findings


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Check LWC jest a11y testing setup, coverage, and "
            "assertion patterns."
        ),
    )
    p.add_argument(
        "--root",
        default="force-app/main/default",
        help="Root of LWC metadata (default: force-app/main/default).",
    )
    p.add_argument(
        "--project-root",
        default=".",
        help="Project root containing package.json / jest.config.js.",
    )
    args = p.parse_args()

    project_root = Path(args.project_root)
    metadata_root = Path(args.root)

    findings_count = 0

    pkg_findings = check_package_json(project_root)
    if pkg_findings:
        print("\n## package.json setup")
        for f in pkg_findings:
            print(f"  - {f}")
        findings_count += len(pkg_findings)

    cfg_findings = check_jest_config(project_root)
    if cfg_findings:
        print("\n## jest.config.js setup")
        for f in cfg_findings:
            print(f"  - {f}")
        findings_count += len(cfg_findings)

    if metadata_root.exists():
        coverage_findings, test_files = check_lwc_test_coverage(metadata_root)
        if coverage_findings:
            print("\n## LWC components missing tests")
            for f in coverage_findings:
                print(f"  - {f}")
            findings_count += len(coverage_findings)

        per_test_findings: list[str] = []
        for tf in test_files:
            per_test_findings.extend(check_test_file(tf))
        if per_test_findings:
            print("\n## Test files missing a11y assertions or using wrong patterns")
            for f in per_test_findings:
                print(f"  - {f}")
            findings_count += len(per_test_findings)
    else:
        print(
            f"\nNote: metadata root not found at {metadata_root} — "
            "skipped per-component checks",
            file=sys.stderr,
        )

    if findings_count == 0:
        print("No LWC jest a11y testing issues detected.")
        return 0

    print(f"\nTotal findings: {findings_count}")
    print("See SKILL.md and references/llm-anti-patterns.md for remediation.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
