#!/usr/bin/env python3
"""Checker script for the lwc-debugging-devtools skill.

Scans LWC JavaScript bundles for runtime-debugging anti-patterns:

  1. Committed `debugger;` statements — should never ship in production.
  2. Bare `console.log(this.<expr>)` or `console.log(record...)` that will
     print a Proxy handle under Lightning Web Security. Recommend wrapping
     with `JSON.parse(JSON.stringify(...))` or `structuredClone(...)`.
  3. `alert(...)` calls — classic non-LWC debugging pattern that blocks the
     main thread and is almost never legitimate inside a Lightning component.

Findings are emitted as line-numbered warnings. Stdlib only; no pip deps.

Usage:
    python3 check_lwc_debugging_devtools.py [--manifest-dir path]

Exit codes:
    0 — no findings
    1 — one or more findings
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# A literal `debugger;` statement. We allow optional leading whitespace and
# allow the line to be preceded by `;` or start-of-line. We deliberately do
# NOT try to match inside comments — that has false positives and the check
# is advisory.
DEBUGGER_RE = re.compile(r"(^|[\s;{])debugger\s*;")

# console.log(this.<anything>) — where the first argument begins with
# `this.` and is NOT already wrapped in JSON.parse/JSON.stringify or
# structuredClone. We detect the start of the argument list.
CONSOLE_LOG_THIS_RE = re.compile(
    r"console\.(log|info|debug|warn|error)\s*\(\s*"
    r"(?![^)]*JSON\.parse\s*\(\s*JSON\.stringify)"
    r"(?![^)]*structuredClone\s*\()"
    r"(?:[^,)]*,\s*)?"  # optional leading label argument, e.g. console.log('x', this.y)
    r"this\."
)

# console.log(record...) — bare variable name starting with `record`.
# Same unwrap-exclusion as above.
CONSOLE_LOG_RECORD_RE = re.compile(
    r"console\.(log|info|debug|warn|error)\s*\(\s*"
    r"(?![^)]*JSON\.parse\s*\(\s*JSON\.stringify)"
    r"(?![^)]*structuredClone\s*\()"
    r"(?:[^,)]*,\s*)?"
    r"record\w*"
)

# alert(...) — any call.
ALERT_RE = re.compile(r"(^|[\s;{(])alert\s*\(")

LINE_COMMENT_RE = re.compile(r"^\s*//")


@dataclass
class Finding:
    path: Path
    line_no: int
    rule: str
    message: str
    snippet: str

    def format(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        return f"{rel}:{self.line_no} [{self.rule}] {self.message} :: {self.snippet.strip()}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC JavaScript files for runtime debugging anti-patterns: "
            "committed debugger statements, Proxy-opaque console.log calls, "
            "and alert() usage."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory to scan. The checker walks this tree and inspects "
            "every .js file under a 'lwc' directory (case-insensitive). "
            "Default: current directory."
        ),
    )
    parser.add_argument(
        "--all-js",
        action="store_true",
        help="Scan every .js file, not just those under an lwc/ directory.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Core scanning
# ---------------------------------------------------------------------------


def iter_candidate_files(root: Path, all_js: bool) -> list[Path]:
    if not root.exists():
        return []
    out: list[Path] = []
    for p in root.rglob("*.js"):
        if not p.is_file():
            continue
        if all_js:
            out.append(p)
            continue
        # Default: only files under a path segment named 'lwc' (case-insensitive).
        if any(part.lower() == "lwc" for part in p.parts):
            out.append(p)
    return sorted(out)


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        findings.append(
            Finding(
                path=path,
                line_no=0,
                rule="io-error",
                message=f"could not read file: {exc}",
                snippet="",
            )
        )
        return findings

    for idx, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip("\n")

        # Skip pure line comments — do not flag lint hints in commented code.
        if LINE_COMMENT_RE.match(line):
            continue

        if DEBUGGER_RE.search(line):
            findings.append(
                Finding(
                    path=path,
                    line_no=idx,
                    rule="debugger-statement",
                    message="committed `debugger;` statement — remove before commit",
                    snippet=line,
                )
            )

        if CONSOLE_LOG_THIS_RE.search(line):
            findings.append(
                Finding(
                    path=path,
                    line_no=idx,
                    rule="console-log-proxy-this",
                    message=(
                        "console logging `this.<expr>` will print a Proxy handle under "
                        "LWS; wrap with JSON.parse(JSON.stringify(...)) or structuredClone(...)"
                    ),
                    snippet=line,
                )
            )
        elif CONSOLE_LOG_RECORD_RE.search(line):
            findings.append(
                Finding(
                    path=path,
                    line_no=idx,
                    rule="console-log-proxy-record",
                    message=(
                        "console logging a record-shaped object will print a Proxy handle "
                        "under LWS; wrap with JSON.parse(JSON.stringify(...)) or "
                        "structuredClone(...)"
                    ),
                    snippet=line,
                )
            )

        if ALERT_RE.search(line):
            findings.append(
                Finding(
                    path=path,
                    line_no=idx,
                    rule="alert-usage",
                    message=(
                        "alert() is not a debugging primitive in LWC — use a Sources "
                        "breakpoint or an LWS-safe console.log"
                    ),
                    snippet=line,
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir).resolve()
    if not root.exists():
        print(f"ERROR: manifest directory not found: {root}", file=sys.stderr)
        return 2

    files = iter_candidate_files(root, all_js=args.all_js)
    if not files:
        print(f"No LWC .js files found under {root}.")
        return 0

    all_findings: list[Finding] = []
    for f in files:
        all_findings.extend(scan_file(f))

    if not all_findings:
        print(f"Scanned {len(files)} file(s). No findings.")
        return 0

    # Group by rule for a deterministic, readable report.
    by_rule: dict[str, list[Finding]] = {}
    for f in all_findings:
        by_rule.setdefault(f.rule, []).append(f)

    print(
        f"Scanned {len(files)} file(s). Found {len(all_findings)} issue(s) "
        f"across {len(by_rule)} rule(s):",
        file=sys.stderr,
    )
    for rule in sorted(by_rule):
        items = by_rule[rule]
        print(f"\n[{rule}] {len(items)} finding(s)", file=sys.stderr)
        for f in items:
            print(f"  {f.format(root)}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
