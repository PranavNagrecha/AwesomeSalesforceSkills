#!/usr/bin/env python3
"""Static checks for Tableau-in-Lightning embedding anti-patterns.

Anti-patterns detected:

  1. Hardcoded Tableau host URL in LWC JavaScript / HTML.
  2. JWT generation with long expiry (>1 hour) in Apex.
  3. Apex source containing a hardcoded long string assigned to a
     `secret` / `clientSecret` / similar variable.
  4. RLS implemented as a `viz-filter` against a user-identity field
     in the LWC (security via UI filter is wrong).

Stdlib only.

Usage:
    python3 check_tableau_embedding_in_lightning.py --src-root .
    python3 check_tableau_embedding_in_lightning.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_TABLEAU_URL_RE = re.compile(
    r"['\"]https?://[^'\"]*tableau[^'\"]*['\"]",
    re.IGNORECASE,
)

# JWT expiry > 1 hour: addHours(N) where N >= 1, or addDays / addMonths
_JWT_LONG_EXPIRY_RE = re.compile(
    r"\.add(Hours|Days|Months|Years)\s*\(\s*(\d+)\s*\)",
    re.IGNORECASE,
)

_SECRET_LITERAL_RE = re.compile(
    r"\b(secret|clientSecret|signingKey|privateKey)\s*=\s*['\"][A-Za-z0-9_\-+/=]{20,}['\"]",
    re.IGNORECASE,
)

# RLS-via-UI-filter heuristic: a viz-filter constructed with an LWC-
# captured user identity attribute (currentUserEmail, etc.).
_VIZ_FILTER_RLS_RE = re.compile(
    r"document\.createElement\s*\(\s*['\"]viz-filter['\"]\s*\)[\s\S]{0,300}?\.(field|value)\s*=\s*[\s\S]{0,200}?(currentUser|userEmail|user\.email|UserInfo)",
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    if path.suffix.lower() in (".js", ".html"):
        for m in _TABLEAU_URL_RE.finditer(text):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: literal Tableau URL "
                f"`{m.group(0)}` in LWC source — host changes (region "
                "migration) break this. Read from Custom Metadata "
                "(llm-anti-patterns.md § 1, gotchas.md § 4)."
            )

        for m in _VIZ_FILTER_RLS_RE.finditer(text):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: row-level security "
                "expressed as a viz-filter using user identity in LWC — "
                "client-side filters are not security controls. Enforce RLS "
                "via a Tableau data-source filter using USERNAME() "
                "(llm-anti-patterns.md § 6)."
            )

    if path.suffix.lower() == ".cls":
        for m in _JWT_LONG_EXPIRY_RE.finditer(text):
            unit = m.group(1).lower()
            n = int(m.group(2))
            # Long if >= 1 hour
            if (unit == "hours" and n >= 1) or unit in ("days", "months", "years"):
                findings.append(
                    f"{path}:{_line_no(text, m.start())}: JWT expiry uses "
                    f".add{m.group(1)}({n}) — long-lived embed JWTs amplify "
                    "leak risk. Use a 5-minute expiry (llm-anti-patterns.md "
                    "§ 2, gotchas.md § 3)."
                )

        for m in _SECRET_LITERAL_RE.finditer(text):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: secret-like literal "
                "assigned to a secret-named variable — store the Tableau "
                "Connected App secret in Named Credential or protected "
                "Custom Metadata (llm-anti-patterns.md § 4)."
            )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for ext in ("*.js", "*.html", "*.cls"):
        for p in root.rglob(ext):
            findings.extend(_scan(p))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC and Apex source for Tableau-embedding anti-patterns: "
            "hardcoded host URLs, long-lived JWTs, secret literals, and "
            "RLS expressed as a UI-filter."
        ),
    )
    parser.add_argument(
        "--src-root",
        default=".",
        help="Root of the LWC / Apex source tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Tableau-embedding anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
