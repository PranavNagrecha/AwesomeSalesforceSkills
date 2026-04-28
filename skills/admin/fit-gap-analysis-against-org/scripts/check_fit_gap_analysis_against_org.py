#!/usr/bin/env python3
"""Checker script for Fit-Gap Analysis Against Org skill.

Validates a fit-gap matrix file (JSON list or JSON wrapper, or a markdown table)
against the canonical row contract documented in the skill SKILL.md and
templates/fit-gap-analysis-against-org-template.md.

Stdlib only — no pip dependencies.

Checks performed:
  1. Every row has a `tier` from the 5-enum.
  2. Every row has an `effort` from the 4-enum.
  3. Every row has a `risk_tag` array (may be empty); tags drawn from the canonical taxonomy.
  4. Every Custom row has a non-empty `recommended_agents`.
  5. Every Unfit row has `recommended_agents == ["architecture-escalation"]` and a non-null `decision_tree_branch` containing "standards/decision-trees/".
  6. Every row has a `requirement_id`.
  7. requirement_ids are unique across the matrix.

Usage:
    python3 check_fit_gap_analysis_against_org.py --file matrix.json
    python3 check_fit_gap_analysis_against_org.py --file matrix.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VALID_TIERS = {"Standard", "Configuration", "Low-Code", "Custom", "Unfit"}
VALID_EFFORTS = {"S", "M", "L", "XL"}
VALID_RISK_TAGS = {
    "license-blocker",
    "data-skew",
    "governance",
    "customization-debt",
    "no-AppExchange-equivalent",
}
VALID_AGENTS = {
    "object-designer",
    "flow-builder",
    "apex-builder",
    "architecture-escalation",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a fit-gap matrix file against the canonical contract.",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the matrix file (JSON or markdown).",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict]:
    """Load matrix rows from JSON or markdown table.

    JSON forms accepted:
      - top-level list of row objects
      - top-level object with key 'rows' that is a list of row objects
    Markdown form accepted:
      - the first markdown table whose header includes 'Tier' and 'Effort' columns
    """
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("rows"), list):
            return data["rows"]
        raise ValueError(
            "JSON must be a list of rows or an object with a 'rows' list."
        )
    if suffix in (".md", ".markdown"):
        return _parse_markdown_table(text)
    raise ValueError(f"Unsupported file extension: {suffix}")


def _parse_markdown_table(text: str) -> list[dict]:
    lines = [ln.rstrip() for ln in text.splitlines()]
    in_table = False
    headers: list[str] = []
    rows: list[dict] = []
    for line in lines:
        if not line.startswith("|"):
            if in_table:
                # table ended
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not in_table:
            # detect header
            if any(c.lower() == "tier" for c in cells) and any(
                c.lower() == "effort" for c in cells
            ):
                headers = cells
                in_table = True
            continue
        # in_table: skip the separator row
        if all(set(c) <= set("- :") for c in cells):
            continue
        if len(cells) != len(headers):
            continue
        row: dict = {}
        for h, v in zip(headers, cells):
            key = _normalize_header(h)
            row[key] = v
        # post-process risk_tag and recommended_agents from comma-separated strings
        if "risk_tag" in row and isinstance(row["risk_tag"], str):
            row["risk_tag"] = _split_csv(row["risk_tag"])
        if "recommended_agents" in row and isinstance(row["recommended_agents"], str):
            row["recommended_agents"] = _split_csv(row["recommended_agents"])
        if "recommended_skills" in row and isinstance(row["recommended_skills"], str):
            row["recommended_skills"] = _split_csv(row["recommended_skills"])
        rows.append(row)
    return rows


def _normalize_header(header: str) -> str:
    h = header.strip().lower()
    mapping = {
        "id": "requirement_id",
        "requirement id": "requirement_id",
        "requirement": "title",
        "tier": "tier",
        "effort": "effort",
        "risk tags": "risk_tag",
        "risk tag": "risk_tag",
        "recommended agent": "recommended_agents",
        "recommended agents": "recommended_agents",
        "recommended skills": "recommended_skills",
        "appexchange alternatives": "appexchange_alternatives",
        "decision tree branch": "decision_tree_branch",
        "notes": "notes",
    }
    return mapping.get(h, re.sub(r"[^a-z0-9_]+", "_", h).strip("_"))


def _split_csv(value: str) -> list[str]:
    if not value or value.strip() in ("—", "-", ""):
        return []
    return [v.strip() for v in re.split(r"[;,]", value) if v.strip()]


def check_rows(rows: list[dict]) -> list[str]:
    issues: list[str] = []
    seen_ids: set[str] = set()

    if not rows:
        issues.append("No rows found in matrix file.")
        return issues

    for index, row in enumerate(rows, start=1):
        prefix = f"row {index}"
        rid = row.get("requirement_id") or row.get("id")
        if not rid:
            issues.append(f"{prefix}: missing requirement_id")
        else:
            prefix = f"row {index} ({rid})"
            if rid in seen_ids:
                issues.append(f"{prefix}: duplicate requirement_id")
            seen_ids.add(rid)

        tier = row.get("tier")
        if tier not in VALID_TIERS:
            issues.append(
                f"{prefix}: tier '{tier}' not in 5-enum {sorted(VALID_TIERS)}"
            )

        effort = row.get("effort")
        if effort not in VALID_EFFORTS:
            issues.append(
                f"{prefix}: effort '{effort}' not in {sorted(VALID_EFFORTS)}"
            )

        risk_tag = row.get("risk_tag")
        if risk_tag is None:
            issues.append(f"{prefix}: risk_tag field missing (use [] for none)")
        elif not isinstance(risk_tag, list):
            issues.append(f"{prefix}: risk_tag must be a list, got {type(risk_tag).__name__}")
        else:
            for tag in risk_tag:
                if tag not in VALID_RISK_TAGS:
                    issues.append(
                        f"{prefix}: risk_tag '{tag}' not in canonical taxonomy "
                        f"{sorted(VALID_RISK_TAGS)}"
                    )

        agents = row.get("recommended_agents") or []
        if not isinstance(agents, list):
            issues.append(
                f"{prefix}: recommended_agents must be a list, got {type(agents).__name__}"
            )
            agents = []

        if tier == "Custom":
            if not agents:
                issues.append(f"{prefix}: Custom row has empty recommended_agents")
            else:
                for ag in agents:
                    if ag not in VALID_AGENTS:
                        issues.append(
                            f"{prefix}: recommended_agent '{ag}' not in "
                            f"{sorted(VALID_AGENTS)}"
                        )

        if tier == "Unfit":
            if agents != ["architecture-escalation"]:
                issues.append(
                    f"{prefix}: Unfit row must have recommended_agents == "
                    f"['architecture-escalation'], got {agents}"
                )
            branch = row.get("decision_tree_branch")
            if not branch or "standards/decision-trees/" not in str(branch):
                issues.append(
                    f"{prefix}: Unfit row missing decision_tree_branch under "
                    f"standards/decision-trees/"
                )
            notes = row.get("notes") or ""
            if not notes.strip():
                issues.append(f"{prefix}: Unfit row missing architecture-escalation note")

        if tier in {"Standard", "Configuration", "Low-Code"}:
            if not agents:
                issues.append(
                    f"{prefix}: {tier} row has empty recommended_agents"
                )

    return issues


def main() -> int:
    args = parse_args()
    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    try:
        rows = load_rows(path)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: failed to load matrix: {exc}", file=sys.stderr)
        return 2

    issues = check_rows(rows)

    if not issues:
        print(f"OK: {len(rows)} rows passed all fit-gap checks.")
        return 0

    print(f"FAIL: {len(issues)} issue(s) found across {len(rows)} row(s).", file=sys.stderr)
    for issue in issues:
        print(f"  - {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
