#!/usr/bin/env python3
"""Static checks for SandboxPostCopy implementations.

Catches the high-confidence anti-patterns documented in this skill:

  1. Class implementing `SandboxPostCopy` declared `public` (not
     `global`) — interface contract requires `global`.
  2. `runApexClass` method declared `public` (not `global`).
  3. Class implements `SandboxPostCopy` but has no
     `Test.testSandboxPostCopyScript` reference anywhere in the
     project — likely no test class.
  4. Email-masking code without `'.invalid' NOT LIKE` filter (or
     equivalent already-masked check) — non-idempotent re-run risk.

Stdlib only.

Usage:
    python3 check_sandbox_post_refresh_automation.py --src-root .
    python3 check_sandbox_post_refresh_automation.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_IMPLEMENTS_RE = re.compile(
    r"\b(public|global|private|protected)\s+(?:virtual\s+|abstract\s+|with\s+sharing\s+|without\s+sharing\s+)*class\s+(\w+)\s+implements\s+(?:[^\{]*?)SandboxPostCopy",
    re.IGNORECASE,
)

_RUN_APEX_METHOD_RE = re.compile(
    r"\b(public|global|private|protected)\s+void\s+runApexClass\s*\(\s*SandboxContext",
    re.IGNORECASE,
)

_EMAIL_MASK_RE = re.compile(
    r"u\.Email\s*=\s*u\.Email\.replace\s*\(\s*['\"]@['\"]",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_apex(path: Path) -> tuple[list[str], bool]:
    """Returns (findings, file_implements_post_copy_interface)."""
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"], False

    impl_match = _IMPLEMENTS_RE.search(text)
    is_post_copy = impl_match is not None
    if is_post_copy:
        modifier = impl_match.group(1).lower()
        cls_name = impl_match.group(2)
        if modifier != "global":
            findings.append(
                f"{path}:{_line_no(text, impl_match.start())}: class `{cls_name}` "
                f"implements SandboxPostCopy with `{modifier}` access — must be "
                "`global`. The interface contract requires it "
                "(references/llm-anti-patterns.md § 1)"
            )

        method_match = _RUN_APEX_METHOD_RE.search(text)
        if method_match is not None:
            method_modifier = method_match.group(1).lower()
            if method_modifier != "global":
                findings.append(
                    f"{path}:{_line_no(text, method_match.start())}: "
                    "`runApexClass(SandboxContext)` is declared "
                    f"`{method_modifier}` — must be `global` to satisfy the "
                    "interface contract "
                    "(references/llm-anti-patterns.md § 1)"
                )

    # Idempotency check on email-masking pattern.
    for m in _EMAIL_MASK_RE.finditer(text):
        # Look backwards to the enclosing for-loop's SOQL query for an
        # already-masked filter.
        prelude = text[max(0, m.start() - 800):m.start()]
        has_already_masked_filter = (
            "NOT LIKE" in prelude
            and (".invalid" in prelude or "+sandbox" in prelude)
        )
        if not has_already_masked_filter:
            findings.append(
                f"{path}:{_line_no(text, m.start())}: email masking "
                "(`u.Email.replace('@', ...)`) without an already-masked filter "
                "in the enclosing query — re-runs will compound the mask "
                "(`alice+sandbox+sandbox@...`). Filter `WHERE Email NOT LIKE "
                "'%.invalid'` "
                "(references/llm-anti-patterns.md § 2)"
            )

    return findings, is_post_copy


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []
    has_post_copy_classes = False
    has_test_post_copy_script = False

    for apex in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        f, is_post_copy = _scan_apex(apex)
        findings.extend(f)
        if is_post_copy:
            has_post_copy_classes = True
        try:
            if "testSandboxPostCopyScript" in apex.read_text(encoding="utf-8", errors="ignore"):
                has_test_post_copy_script = True
        except OSError:
            pass

    if has_post_copy_classes and not has_test_post_copy_script:
        findings.append(
            f"{root}: project has SandboxPostCopy implementation(s) but no "
            "`Test.testSandboxPostCopyScript` reference anywhere — likely no "
            "test class. Required for production deploy under the 75% "
            "org-wide coverage rule "
            "(references/llm-anti-patterns.md § 7)"
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex source for SandboxPostCopy anti-patterns "
            "(non-global class/method, missing test class, "
            "non-idempotent email masking)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no SandboxPostCopy anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
