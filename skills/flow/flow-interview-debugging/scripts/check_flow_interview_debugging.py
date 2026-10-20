#!/usr/bin/env python3
"""Checker for flow-interview-debugging.

Two modes:

  (no arguments)        Package-shape smoke check: the skill folder has the required files.
  --manifest-dir DIR    Scan every ``*.flow-meta.xml`` under DIR for the debug anti-patterns
                        this skill documents (SKILL.md step 5; references/llm-anti-patterns.md):

  FID01  A DML (recordCreates/recordUpdates/recordDeletes), Action (actionCalls) or
         Subflow element with no <faultConnector> (SKILL.md "Instrument every
         fallible element").
  FID02  A <faultConnector> on a <recordLookups> whose target element is named or
         labelled "not found" / "none" / "missing" / "empty" -- zero rows is a success,
         not a fault (Anti-Pattern 1).
  FID03  A <screens> element reached from a <faultConnector> in a flow whose processType
         is not "Flow" -- there is no UI to render into (Anti-Pattern 2).
  FID04  A reference to an invented $Flow global: CurrentElement, ErrorElement, FaultCode,
         StackTrace, InterviewId (Anti-Pattern 3).

Exit codes: 1 when --manifest-dir does not exist; findings exit 0 unless --strict (then 1).
A directory with no flow files prints one WARN and exits 0 (1 with --strict).

Usage:
    python3 check_flow_interview_debugging.py --manifest-dir force-app/main/default [--strict]
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REQUIRED = [
    "SKILL.md",
    "references/examples.md",
    "references/gotchas.md",
    "references/well-architected.md",
    "references/llm-anti-patterns.md",
    "templates",
    "scripts",
]

FALLIBLE = {
    "recordCreates": "Create Records",
    "recordUpdates": "Update Records",
    "recordDeletes": "Delete Records",
    "actionCalls": "Action",
    "subflows": "Subflow",
}
NOT_FOUND_WORDS = ("not found", "notfound", "none", "missing", "empty", "no record")
INVENTED_GLOBALS = re.compile(
    r"\$Flow\.(CurrentElement|ErrorElement|FaultCode|StackTrace|InterviewId)\b"
)


def local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child(elem, name):
    for c in elem:
        if local(c.tag) == name:
            return c
    return None


def text(elem, name) -> str:
    c = child(elem, name)
    return (c.text or "").strip() if c is not None else ""


def fault_target(elem) -> str:
    fc = child(elem, "faultConnector")
    return text(fc, "targetReference") if fc is not None else ""


def check_flow(path: Path, root_dir: Path) -> list[str]:
    rel = path.relative_to(root_dir) if root_dir in path.parents else path
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{rel}: not well-formed XML ({exc}); not checked"]

    raw = path.read_text(encoding="utf-8", errors="replace")
    process_type = text(root, "processType")
    named = {text(c, "name"): c for c in root if text(c, "name")}
    findings: list[str] = []

    for node in root:
        tag = local(node.tag)
        name = text(node, "name") or "<unnamed>"
        if tag in FALLIBLE and child(node, "faultConnector") is None:
            findings.append(
                f"{rel}: FID01 {FALLIBLE[tag]} element '{name}' has no fault connector -- "
                "a failure here is invisible until the error email (SKILL.md step 5)"
            )
        target = fault_target(node)
        if not target:
            continue
        tnode = named.get(target)
        if tag == "recordLookups" and tnode is not None:
            blob = f"{target} {text(tnode, 'label')}".lower()
            if any(w in blob for w in NOT_FOUND_WORDS):
                findings.append(
                    f"{rel}: FID02 fault connector on Get Records '{name}' leads to '{target}', a "
                    "not-found branch; zero rows is a success -- use a Decision with IsNull "
                    "(llm-anti-patterns.md Anti-Pattern 1)"
                )
        if tnode is not None and local(tnode.tag) == "screens" and process_type != "Flow":
            findings.append(
                f"{rel}: FID03 fault connector on '{name}' leads to Screen '{target}' in a "
                f"processType '{process_type or '(unset)'}' flow; no UI exists -- log first, use "
                "Custom Error to block the save (llm-anti-patterns.md Anti-Pattern 2)"
            )

    for lineno, line in enumerate(raw.splitlines(), 1):
        m = INVENTED_GLOBALS.search(line)
        if m:
            findings.append(
                f"{rel}:{lineno}: FID04 '$Flow.{m.group(1)}' is not a documented global; pass the "
                "element name as a literal (llm-anti-patterns.md Anti-Pattern 3)"
            )
    return findings


def shape_check() -> int:
    base = Path(__file__).resolve().parents[1]
    missing = [r for r in REQUIRED if not (base / r).exists()]
    if missing:
        print(f"ERROR [flow-interview-debugging] missing files: {missing}", file=sys.stderr)
        return 1
    print("[flow-interview-debugging] shape OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan flow metadata for the debug anti-patterns documented in flow-interview-debugging."
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root of the metadata source tree. Omit to run the package-shape check only.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any finding (and on an empty directory).",
    )
    args = parser.parse_args()

    if args.manifest_dir is None:
        return shape_check()

    root_dir = Path(args.manifest_dir)
    if not root_dir.exists():
        print(f"ERROR: manifest directory not found: {root_dir}")
        return 1

    flows = sorted(root_dir.rglob("*.flow-meta.xml")) if root_dir.is_dir() else [root_dir]
    if not flows:
        print(f"WARN: no *.flow-meta.xml files found under {root_dir}; nothing to check.")
        return 1 if args.strict else 0

    findings: list[str] = []
    for f in flows:
        findings.extend(check_flow(f, root_dir))
    for f in findings:
        print(f"WARN: {f}")
    print(f"Scanned {len(flows)} flow file(s): {len(findings)} finding(s).")
    return 1 if (findings and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
