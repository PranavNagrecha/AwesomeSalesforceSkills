#!/usr/bin/env python3
"""Checker script for AMPscript Development skill.

Scans HTML/AMPscript content files for common AMPscript anti-patterns and
structural issues. Uses stdlib only — no pip dependencies.

Checks performed:
  1. Block syntax (%%[ ... ]%%) detected in subject-line files
  2. FOR loops without a preceding RowCount guard (IF @rowCount > 0)
  3. Unicode smart/curly quotes inside AMPscript blocks
  4. Variable references (@var) used before a SET statement
  5. LookupRows calls without capturing return value in a variable

Usage:
    python3 check_ampscript_development.py [--help]
    python3 check_ampscript_development.py --content-dir path/to/html/files
    python3 check_ampscript_development.py --file path/to/single/file.html
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BLOCK_SYNTAX_RE = re.compile(r'%%\[')
_INLINE_ONLY_FILENAMES = re.compile(
    r'(subject|preheader|header)', re.IGNORECASE
)
_FOR_LOOP_RE = re.compile(r'FOR\s+@\w+\s*=\s*1\s+TO\s+', re.IGNORECASE)
_ROWCOUNT_GUARD_RE = re.compile(
    r'IF\s+@\w*[Rr]ow[Cc]ount\w*\s*>\s*0', re.IGNORECASE
)
_SMART_QUOTE_RE = re.compile(r'[\u201c\u201d\u2018\u2019]')
_AMPSCRIPT_BLOCK_RE = re.compile(r'%%\[(.*?)%%\]', re.DOTALL)
_SET_RE = re.compile(r'\bSET\s+(@\w+)\s*=', re.IGNORECASE)
_VAR_USE_RE = re.compile(r'(?<!\bSET\s{0,20})(@\w+)', re.IGNORECASE)
_LOOKUPROWS_NO_ASSIGN_RE = re.compile(
    r'(?<!SET\s{0,20}@\w{1,80}\s*=\s*)LookupRows\s*\(', re.IGNORECASE
)


def check_file(path: Path) -> list[str]:
    """Return a list of issue strings for the given file."""
    issues: list[str] = []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    # ------------------------------------------------------------------
    # Check 1: Block syntax in subject/preheader files
    # ------------------------------------------------------------------
    if _INLINE_ONLY_FILENAMES.search(path.stem):
        if _BLOCK_SYNTAX_RE.search(content):
            issues.append(
                f"{path}: block syntax %%[ found in a subject/preheader file. "
                "Subject lines support only inline %%=...=%% syntax."
            )

    # ------------------------------------------------------------------
    # Check 2: FOR loops without a RowCount > 0 guard in the same file
    # ------------------------------------------------------------------
    if _FOR_LOOP_RE.search(content) and not _ROWCOUNT_GUARD_RE.search(content):
        issues.append(
            f"{path}: FOR loop detected but no 'IF @rowCount > 0' guard found. "
            "Always guard loops with RowCount check to avoid empty markup."
        )

    # ------------------------------------------------------------------
    # Check 3: Smart/curly quotes inside AMPscript blocks
    # ------------------------------------------------------------------
    for block_match in _AMPSCRIPT_BLOCK_RE.finditer(content):
        block_text = block_match.group(1)
        if _SMART_QUOTE_RE.search(block_text):
            issues.append(
                f"{path}: smart/curly quote character found inside an AMPscript "
                "block (%%[...%%]). Replace with straight ASCII double quotes."
            )
            break  # one warning per file is enough

    # ------------------------------------------------------------------
    # Check 4: Variable referenced before SET in same block
    # ------------------------------------------------------------------
    for block_match in _AMPSCRIPT_BLOCK_RE.finditer(content):
        block_text = block_match.group(1)
        declared: set[str] = set()
        # Walk line by line within the block
        for line in block_text.splitlines():
            set_match = _SET_RE.match(line.strip())
            if set_match:
                declared.add(set_match.group(1).lower())
            else:
                # Check for any @var usage not in a SET statement
                for var_match in re.finditer(r'(@\w+)', line):
                    var = var_match.group(1).lower()
                    # Skip system variables
                    if var in ('_subscriberkey', '_messagecontext', '_emailname'):
                        continue
                    if var not in declared:
                        issues.append(
                            f"{path}: variable '{var_match.group(1)}' may be used "
                            "before it is declared with SET."
                        )
                        declared.add(var)  # suppress duplicate warnings for same var

    # ------------------------------------------------------------------
    # Check 5: LookupRows call result not assigned to a variable
    # ------------------------------------------------------------------
    # Simple heuristic: LookupRows( not preceded by "= " on same line
    for line_no, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if re.search(r'\bLookupRows\s*\(', stripped, re.IGNORECASE):
            if not re.search(r'SET\s+@\w+\s*=\s*LookupRows\s*\(', stripped, re.IGNORECASE):
                # Could be a multi-line assignment — only warn on lines that look standalone
                if not re.search(r'=\s*LookupRows\s*\(', stripped, re.IGNORECASE):
                    issues.append(
                        f"{path}:{line_no}: LookupRows() call result may not be "
                        "assigned to a variable. Use SET @rows = LookupRows(...)."
                    )

    return issues


def check_ampscript_development(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found by scanning content files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Content directory not found: {manifest_dir}")
        return issues

    # Scan for HTML, HTM, and AMPscript files
    extensions = ("*.html", "*.htm", "*.ampscript", "*.amp")
    files_scanned = 0
    for ext in extensions:
        for fpath in sorted(manifest_dir.rglob(ext)):
            issues.extend(check_file(fpath))
            files_scanned += 1

    if files_scanned == 0:
        # Not an error — just informational; the checker is content-directory agnostic
        print(
            f"INFO: No HTML/AMPscript files found in {manifest_dir}. "
            "Pass --content-dir pointing to a directory containing .html or .amp files.",
            file=sys.stderr,
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check AMPscript content files for common anti-patterns and structural issues."
        ),
    )
    parser.add_argument(
        "--content-dir",
        "--manifest-dir",  # alias for repo convention compatibility
        default=".",
        dest="content_dir",
        help="Directory containing HTML/AMPscript content files (default: current directory).",
    )
    parser.add_argument(
        "--file",
        dest="single_file",
        default=None,
        help="Check a single file instead of a directory.",
    )
    args = parser.parse_args()

    if args.single_file:
        issues = check_file(Path(args.single_file))
    else:
        issues = check_ampscript_development(Path(args.content_dir))

    if not issues:
        print("No AMPscript issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
