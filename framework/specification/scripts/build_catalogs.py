#!/usr/bin/env python3
"""Generate human-readable catalogs from canonical SFAEF JSON definitions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(cell(v) for v in row) + " |" for row in rows)
    return "\n".join(lines)


def products() -> str:
    items = [load(p) for p in sorted((ROOT / "products" / "definitions").glob("*.json"))]
    rows = []
    for item in items:
        rows.append([
            item["id"], item["title"], item.get("lifecycle_status", ""),
            ", ".join(item.get("command_ids", [])),
            len(item.get("agent_ids", [])), len(item.get("tool_ids", [])),
            len(item.get("known_truth_scenarios", [])),
        ])
    return "# Product catalog\n\nGenerated from `products/definitions/*.json`. Do not edit manually.\n\n" + md_table(
        ["ID", "Product", "Lifecycle", "Commands", "Agents", "Tools", "Scenarios"], rows
    ) + "\n"


def agents() -> str:
    items = [load(p) for p in sorted((ROOT / "agents" / "definitions").glob("*.json"))]
    rows = [[i["id"], i["kind"], i.get("product_id", "—"), ", ".join(i.get("tool_ids", [])) or "—", i["purpose"]] for i in items]
    return "# Agent catalog\n\nGenerated from `agents/definitions/*.json`. Do not edit manually.\n\n" + md_table(
        ["Agent", "Kind", "Product", "Evidence tools", "Purpose"], rows
    ) + "\n"


def commands() -> str:
    items = [load(p) for p in sorted((ROOT / "commands" / "specs").glob("*.json"))]
    out = ["# Command API reference", "", "Generated from `commands/specs/*.json`. Do not edit manually.", ""]
    for item in items:
        out += [f"## `/{item['id']}`", "", item["purpose"], "", f"- Product: `{item.get('product_id') or 'framework'}`", f"- Version: `{item['version']}`", f"- Agents: {', '.join('`'+x+'`' for x in item.get('agent_ids', [])) or 'none'}", f"- Tools: {', '.join('`'+x+'`' for x in item.get('tool_ids', [])) or 'none'}", f"- Permissions: {', '.join('`'+x+'`' for x in item.get('permissions', [])) or 'none'}", f"- Terminal statuses: {', '.join('`'+x+'`' for x in item.get('allowed_statuses', []))}", ""]
        args = item.get("arguments", [])
        if args:
            out += [md_table(["Argument", "Type", "Required", "Description"], [[a["name"], a.get("type", "any"), a.get("required", False), a.get("description", "")] for a in args]), ""]
    return "\n".join(out).rstrip() + "\n"


def tools() -> str:
    items = [load(p) for p in sorted((ROOT / "mcp" / "tool-specs").glob("*.json"))]
    out = ["# Evidence-tool API reference", "", "Generated from `mcp/tool-specs/*.json`. These are product-facing normalized contracts, not a promise to duplicate every upstream Salesforce tool.", ""]
    for item in items:
        out += [f"## `{item['id']}`", "", item["purpose"], "", f"- Version: `{item['version']}`", f"- Read only: `{str(item['read_only']).lower()}`", f"- Permission classes: {', '.join('`'+x+'`' for x in item.get('permission_classes', []))}", f"- Target pinning: `{str(item.get('requires_target_pinning', False)).lower()}`", f"- Maximum model-visible page: `{item.get('max_page_bytes', 'n/a')}` bytes", f"- Unknown-tool default: `{item.get('unknown_tool_default', 'deny')}`", f"- Upstream candidates: {', '.join('`'+x+'`' for x in item.get('upstream_candidates', [])) or 'none'}", ""]
        args = item.get("arguments", [])
        if args:
            out += [md_table(["Argument", "Type", "Required"], [[a["name"], a.get("type", "any"), a.get("required", False)] for a in args]), ""]
        tests = item.get("required_tests", [])
        if tests:
            out += ["Required contract tests: " + "; ".join(tests) + ".", ""]
    return "\n".join(out).rstrip() + "\n"


def contexts() -> str:
    items = [load(p) for p in sorted((ROOT / "context" / "context-packs").glob("*.json"))]
    rows = [[i["product_id"], i["id"], i["target_files"], i["hard_files"], i["max_tool_page_bytes"], len(i.get("conditional_packs", [])), i.get("standalone_supported", False)] for i in items]
    return "# Context-pack catalog\n\nGenerated from `context/context-packs/*.json`.\n\n" + md_table(
        ["Product", "Pack", "Target files", "Hard files", "Tool bytes", "Conditional packs", "Standalone"], rows
    ) + "\n"


def scenarios() -> str:
    items = [load(p) for p in sorted((ROOT / "qa" / "scenarios").glob("*.json"))]
    rows = [[i["id"], i["product_id"], i["domain"], ", ".join(i.get("lane_support", [])), len(i.get("required_findings", [])), i["setup_summary"]] for i in items]
    return "# Known-truth scenario catalog\n\nGenerated from `qa/scenarios/*.json`. Ground truth is finding/evidence based, not exact prose.\n\n" + md_table(
        ["Scenario", "Product", "Domain", "Lanes", "Required findings", "Setup"], rows
    ) + "\n"


def sources() -> str:
    items = [load(p) for p in sorted((ROOT / "research" / "sources").glob("*.json"))]
    rows = [[i["id"], i["publisher"], i["title"], i["source_tier"], i["reviewed_at"], i["status"], ", ".join(i.get("affects", []))] for i in items]
    return "# Research source catalog\n\nGenerated from `research/sources/*.json`. URLs and source records must be rechecked before release-sensitive implementation or public claims.\n\n" + md_table(
        ["ID", "Publisher", "Source", "Tier", "Reviewed", "Status", "Affects"], rows
    ) + "\n"


def requirements() -> str:
    data = load(ROOT / "implementation" / "requirements.json")
    rows = [[r["requirement_id"], r["level"], r["spec_file"], r["line"], r["statement"]] for r in data["requirements"]]
    return "# Normative requirement catalog\n\nGenerated from numbered specifications. Implementation status belongs in the repository traceability working copy, not this immutable source catalog.\n\n" + md_table(
        ["Requirement", "Level", "Source", "Line", "Statement"], rows
    ) + "\n"


GENERATORS = {
    "PRODUCT_CATALOG.md": products,
    "AGENT_CATALOG.md": agents,
    "COMMAND_API.md": commands,
    "EVIDENCE_TOOL_API.md": tools,
    "CONTEXT_PACK_CATALOG.md": contexts,
    "SCENARIO_CATALOG.md": scenarios,
    "SOURCE_CATALOG.md": sources,
    "REQUIREMENT_CATALOG.md": requirements,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    ok = True
    out_dir = ROOT / "catalogs"
    out_dir.mkdir(exist_ok=True)
    for name, generator in GENERATORS.items():
        content = generator()
        path = out_dir / name
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if args.check:
            if current != content:
                print(f"DRIFT: {path.relative_to(ROOT)}")
                ok = False
            else:
                print(f"OK: {path.relative_to(ROOT)}")
        else:
            path.write_text(content, encoding="utf-8")
            print(f"WROTE: {path.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
