#!/usr/bin/env python3
"""Build or verify the normative SFAEF requirement catalog."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
REQ_RE = re.compile(r"^(SFAEF-(?P<doc>\d{3})-(?P<num>\d{3}))\.\s*(?P<statement>.+?)\s*$")


def infer_level(statement: str) -> str:
    upper = statement.upper()
    for level in ("MUST NOT", "SHOULD NOT", "MUST", "SHOULD", "MAY"):
        if level in upper:
            return level
    return "NORMATIVE"


def collect_requirements(root: Path = ROOT) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: dict[str, str] = {}
    for path in sorted((root / "spec").glob("[0-9][0-9][0-9]-*.md")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = REQ_RE.match(line.strip())
            if not match:
                continue
            requirement_id = match.group(1)
            rel = path.relative_to(root).as_posix()
            if requirement_id in seen:
                raise ValueError(f"duplicate requirement {requirement_id}: {seen[requirement_id]} and {rel}:{line_no}")
            seen[requirement_id] = f"{rel}:{line_no}"
            statement = match.group("statement").strip()
            rows.append(
                {
                    "requirement_id": requirement_id,
                    "spec_file": rel,
                    "line": line_no,
                    "level": infer_level(statement),
                    "statement": statement,
                    "implementation_status": "unimplemented",
                    "implementation_paths": "",
                    "test_paths": "",
                    "review_evidence": "",
                }
            )
    rows.sort(key=lambda item: item["requirement_id"])
    return rows


def render_csv(rows: Iterable[dict[str, object]]) -> str:
    from io import StringIO

    fieldnames = [
        "requirement_id",
        "spec_file",
        "line",
        "level",
        "statement",
        "implementation_status",
        "implementation_paths",
        "test_paths",
        "review_evidence",
    ]
    buf = StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def render_json(rows: list[dict[str, object]]) -> str:
    return json.dumps(
        {
            "schema_version": "0.9.0",
            "count": len(rows),
            "requirements": rows,
        },
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"


def check_or_write(path: Path, content: str, check: bool) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if check:
        if current != content:
            print(f"DRIFT: {path.relative_to(ROOT)}")
            return False
        print(f"OK: {path.relative_to(ROOT)}")
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"WROTE: {path.relative_to(ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if generated files differ")
    args = parser.parse_args()
    try:
        rows = collect_requirements()
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    ok_csv = check_or_write(ROOT / "implementation" / "requirements.csv", render_csv(rows), args.check)
    ok_json = check_or_write(ROOT / "implementation" / "requirements.json", render_json(rows), args.check)
    print(f"Requirements: {len(rows)}")
    return 0 if ok_csv and ok_json else 1


if __name__ == "__main__":
    raise SystemExit(main())
