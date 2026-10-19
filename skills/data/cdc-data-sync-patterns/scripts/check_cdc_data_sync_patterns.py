#!/usr/bin/env python3
"""Checker for the cdc-data-sync-patterns skill.

Scans subscriber source (.py, .js, .ts, .java, .go, .cs, .cls, .trigger) for
replication mistakes described in the Change Data Capture Developer Guide and the
Pub/Sub API Subscribe reference. A file counts as a CDC subscriber when it
mentions ChangeEventHeader, changeType, or a ChangeEvents channel.

Severity:
  ERROR  reads changeType but never mentions GAP_ (gap events are processed as
         normal changes); checks a GAP_ prefix but never mentions GAP_OVERFLOW
         (overflow events have only a dummy record ID, so record lookups miss
         every change past the first 100,000 in the transaction).
  WARN   subscribes but never saves a replay ID; uses EARLIEST or CometD -2 as a
         fixed replay option; reads only recordIds[0] (merged events carry
         several IDs); a GAP_ branch that only logs or continues.

Exit codes: 0 clean or WARN only; 1 on ERROR, missing directory, or WARN with
--strict. An empty directory prints a WARN and exits 0. Stdlib only.

Usage:
    python3 check_cdc_data_sync_patterns.py --manifest-dir path/to/subscriber [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".cs", ".cls", ".trigger"}
CDC_RE = re.compile(r"ChangeEventHeader|changeType|change_type|/data/ChangeEvents|ChangeEvent\b", re.IGNORECASE)
CHANGETYPE_RE = re.compile(r"changeType|change_type", re.IGNORECASE)
GAP_RE = re.compile(r"GAP_")
GAP_PREFIX_RE = re.compile(r"""(?:startswith|startsWith|StartsWith|HasPrefix)\s*\(\s*(?:\w+\s*,\s*)?["']GAP_["']""")
OVERFLOW_RE = re.compile(r"GAP_OVERFLOW")
SUBSCRIBE_RE = re.compile(r"\bsubscribe\s*\(|\bSubscribe\b|FetchRequest|replay_preset|replayPreset|cometd", re.IGNORECASE)
SAVE_REPLAY_RE = re.compile(r"replay[_]?id.*\b(?:save|set|put|write|persist|commit|store|upsert|insert)\b|\b(?:save|set|put|write|persist|commit|store|upsert|insert)\w*\s*\(.*replay[_]?id", re.IGNORECASE)
FIXED_EARLIEST_RE = re.compile(r"""replay_?preset\s*[=:]\s*["']?EARLIEST|ReplayPreset\.EARLIEST|setReplay\(\s*-2\s*\)|replay_?id\s*[=:]\s*-2\b""", re.IGNORECASE)
FIRST_ID_RE = re.compile(r"""recordIds["']?\]?\s*(?:\[\s*0\s*\]|\.get\(\s*0\s*\))""", re.IGNORECASE)
LOG_ONLY_GAP_RE = re.compile(r"GAP_[^\n]*\n(?:\s*(?:#|//)[^\n]*\n)*\s*(?:log\w*|logger\.\w+|console\.log|System\.debug)\([^\n]*\)\s*;?\s*\n\s*(?:continue|return)\b", re.IGNORECASE)


def line_of(src: str, m: re.Match) -> int:
    return src.count("\n", 0, m.start()) + 1


def scan(path: Path) -> list[tuple[str, str]]:
    src = path.read_text(encoding="utf-8", errors="replace")
    if CDC_RE.search(src) is None:
        return []
    out: list[tuple[str, str]] = []
    ct = CHANGETYPE_RE.search(src)
    if ct is not None and GAP_RE.search(src) is None:
        out.append(("ERROR", f"{path}:{line_of(src, ct)}: reads changeType but never handles GAP_ events; gap events carry no field data"))
    gp = GAP_PREFIX_RE.search(src)
    if gp is not None and OVERFLOW_RE.search(src) is None:
        out.append(("ERROR", f"{path}:{line_of(src, gp)}: GAP_ prefix check with no GAP_OVERFLOW branch; overflow events have only a dummy record ID and need an entity re-sync"))
    sub = SUBSCRIBE_RE.search(src)
    if sub is not None and SAVE_REPLAY_RE.search(src) is None:
        out.append(("WARN", f"{path}:{line_of(src, sub)}: subscribes but never saves a replay ID; a restart cannot resume where it stopped"))
    fe = FIXED_EARLIEST_RE.search(src)
    if fe is not None:
        out.append(("WARN", f"{path}:{line_of(src, fe)}: EARLIEST / -2 as a fixed replay option replays everything retained; resume from a stored replay ID instead"))
    fi = FIRST_ID_RE.search(src)
    if fi is not None:
        out.append(("WARN", f"{path}:{line_of(src, fi)}: only recordIds[0] is read; merged change and gap events carry several record IDs"))
    lg = LOG_ONLY_GAP_RE.search(src)
    if lg is not None:
        out.append(("WARN", f"{path}:{line_of(src, lg)}: GAP_ branch only logs and skips; the change must be retrieved and applied"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag CDC replication mistakes (cdc-data-sync-patterns skill).")
    ap.add_argument("--manifest-dir", default=".", help="Root of the subscriber source to scan")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in EXTENSIONS)
    if not files:
        print(f"WARN: no source files under {root}; nothing to check")
        return 0

    findings: list[tuple[str, str]] = []
    for f in files:
        findings.extend(scan(f))
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = len(findings) - errors
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    print(f"Scanned {len(files)} file(s): {errors} ERROR, {warns} WARN")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
