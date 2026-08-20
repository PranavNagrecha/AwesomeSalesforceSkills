#!/usr/bin/env python3
"""Build or verify a deterministic manifest for the framework specification package."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "FRAMEWORK_MANIFEST.json"
EXCLUDE = {"FRAMEWORK_MANIFEST.json", "SHA256SUMS.txt", "VALIDATION_REPORT.md"}
EXCLUDE_PREFIXES = ("validation/",)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect() -> dict:
    records = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCLUDE or rel.endswith(".pyc") or rel.startswith(EXCLUDE_PREFIXES):
            continue
        records.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})
    def count(pattern: str) -> int:
        return len(list(ROOT.glob(pattern)))
    def csv_count(rel: str) -> int:
        path = ROOT / rel
        return max(0, sum(1 for _ in path.open(encoding="utf-8")) - 1) if path.exists() else 0
    return {
        "schema_version": "0.9.0",
        "framework": "SfSkills Salesforce AI Engineering Framework",
        "specification_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "research_freeze": "2026-08-19",
        "counts": {
            "files": len(records),
            "bytes": sum(item["bytes"] for item in records),
            "requirements": max(0, sum(1 for _ in (ROOT / "implementation" / "requirements.csv").read_text(encoding="utf-8").splitlines()) - 1),
            "products": count("products/definitions/*.json"),
            "agents": count("agents/definitions/*.json"),
            "commands": count("commands/specs/*.json"),
            "evidence_tools": count("mcp/tool-specs/*.json"),
            "context_packs": count("context/context-packs/*.json"),
            "qa_scenarios": count("qa/scenarios/*.json"),
            "schemas": count("schemas/*.json"),
            "research_sources": count("research/sources/*.json"),
            "legacy_skills_covered": csv_count("migration/catalogs/current-skills.csv"),
            "legacy_agents_covered": csv_count("migration/catalogs/current-agents.csv"),
            "legacy_commands_covered": csv_count("migration/catalogs/current-commands.csv"),
            "legacy_mcp_tools_covered": csv_count("migration/catalogs/current-mcp-tools.csv"),
        },
        "files": records,
    }


def render() -> str:
    return json.dumps(collect(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != content:
            print("DRIFT: FRAMEWORK_MANIFEST.json")
            return 1
        print("OK: FRAMEWORK_MANIFEST.json")
        return 0
    OUT.write_text(content, encoding="utf-8")
    print("WROTE: FRAMEWORK_MANIFEST.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
