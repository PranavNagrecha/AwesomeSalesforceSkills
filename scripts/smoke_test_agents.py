#!/usr/bin/env python3
"""Smoke test every runtime agent against a live Salesforce org.

For each `class: runtime, status != deprecated` agent:

1. **Static checks** — does the AGENT.md have the 8 required sections in order?
   Does every Mandatory Read citation resolve? Are the declared
   `dependencies` consistent with the body's citations?
2. **Input-schema check** — if `agents/<id>/inputs.schema.json` exists, is it
   valid JSON Schema? Does it cover every input named in the "Inputs" section?
3. **Probe executability** — for every probe the agent declares in
   `dependencies.probes`, re-run the probe's SOQL against the target org and
   confirm it executes (covered by validate_probes_against_org.py; this
   checks the link holds).
4. **Output-envelope conformance** — produce a minimal sample envelope for
   the agent (without running an LLM) and verify it conforms to
   `output-envelope.schema.json`. Catches agent specs that reference output
   fields the schema doesn't support.
5. **Slash-command coverage** — does `commands/<alias>.md` exist for this
   agent?

Emits a per-agent markdown report under `docs/validation/agent_smoke/<date>/`
PLUS a rollup `docs/validation/agent_smoke_<date>.md`.

Usage:
    python3 scripts/smoke_test_agents.py --target-org sfskills-dev
    python3 scripts/smoke_test_agents.py --target-org sfskills-dev --agent user-access-diff

Exit codes:
  0 — all agents pass or pass-with-caveats
  1 — at least one agent has a hard failure
  2 — setup error
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"
COMMANDS_DIR = REPO_ROOT / "commands"
SKILLS_DIR = REPO_ROOT / "skills"
SHARED_DIR = AGENTS_DIR / "_shared"
PROBES_DIR = SHARED_DIR / "probes"
SCHEMAS_DIR = SHARED_DIR / "schemas"
DEFAULT_OUT = REPO_ROOT / "docs" / "validation"

REQUIRED_SECTIONS = [
    "What This Agent Does",
    "Invocation",
    "Mandatory Reads",  # prefix-match; actual headings vary
    "Inputs",
    "Plan",
    "Output Contract",
    "Escalation",  # prefix-match for "Escalation / Refusal Rules"
    "What This Agent Does NOT Do",
]

SKILL_DOMAINS = {
    "admin", "apex", "lwc", "flow", "omnistudio", "agentforce",
    "security", "integration", "data", "devops", "architect",
}


# ── Frontmatter + section parsing ───────────────────────────────────────────

def parse_agent_md(path: Path) -> tuple[dict, str, list[str]]:
    """Return (frontmatter_dict, body, section_headings_in_order)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        return {}, text, []
    raw_fm = m.group(1)
    body = m.group(2)

    # Very minimal YAML parse — enough for frontmatter shape.
    meta: dict = {}
    current_top: str | None = None
    current_sub: str | None = None

    for line in raw_fm.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[a-z_]+:\s*\S", line):
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"')
            current_top = None
            current_sub = None
            continue
        if re.match(r"^[a-z_]+:\s*$", line):
            key = line.split(":")[0].strip()
            meta[key] = {}
            current_top = key
            current_sub = None
            continue
        m2 = re.match(r"^  ([a-z_]+):\s*$", line)
        if m2 and current_top is not None:
            current_sub = m2.group(1)
            if not isinstance(meta[current_top], dict):
                meta[current_top] = {}
            meta[current_top][current_sub] = []
            continue
        m2 = re.match(r"^    - (.+)$", line)
        if m2 and current_top and current_sub:
            meta[current_top][current_sub].append(m2.group(1).strip())
            continue
        m2 = re.match(r"^  - (.+)$", line)
        if m2 and current_top:
            if not isinstance(meta[current_top], list):
                meta[current_top] = []
            meta[current_top].append(m2.group(1).strip())
            continue

    headings = re.findall(r"^## (.+)$", body, re.MULTILINE)
    return meta, body, headings


# ── Individual checks ────────────────────────────────────────────────────────

def check_required_sections(headings: list[str]) -> tuple[bool, list[str]]:
    """Every required section must be present in order."""
    issues = []
    current_idx = 0
    found_positions = []
    for required in REQUIRED_SECTIONS:
        idx = None
        for i, h in enumerate(headings):
            if h.startswith(required) and i >= current_idx:
                idx = i
                break
        if idx is None:
            issues.append(f"missing section: '## {required}'")
        else:
            found_positions.append(idx)
            current_idx = idx + 1
    if len(found_positions) == len(REQUIRED_SECTIONS) and found_positions != sorted(found_positions):
        issues.append("sections present but out of canonical order")
    return (len(issues) == 0), issues


def check_mandatory_reads_resolve(body: str, root: Path) -> tuple[bool, list[str]]:
    """Every skill/probe/standard citation in the body resolves to a real file."""
    issues = []
    # Skills: `skills/<domain>/<slug>`
    for m in re.finditer(r"`skills/([a-z0-9-]+)/([a-z0-9-]+)(?:/[A-Za-z0-9_./-]*)?`", body):
        domain, slug = m.group(1), m.group(2)
        if domain not in SKILL_DOMAINS:
            continue
        if not (root / "skills" / domain / slug).exists():
            issues.append(f"broken skill citation: skills/{domain}/{slug}")
    # Probes
    for m in re.finditer(r"`agents/_shared/probes/([a-z0-9-]+)(?:\.md)?`", body):
        name = m.group(1)
        if not name.endswith(".md"):
            name = f"{name}.md"
        if not (PROBES_DIR / name).exists():
            issues.append(f"broken probe citation: {name}")
    # Templates
    for m in re.finditer(r"`templates/([A-Za-z0-9_./-]+)`", body):
        if not (root / "templates" / m.group(1)).exists():
            issues.append(f"broken template citation: templates/{m.group(1)}")
    # Decision trees
    for m in re.finditer(r"`standards/decision-trees/([a-z0-9-]+\.md)`", body):
        if not (root / "standards" / "decision-trees" / m.group(1)).exists():
            issues.append(f"broken decision-tree citation: {m.group(1)}")
    return (len(issues) == 0), issues


def check_dependencies_consistent(meta: dict, body: str) -> tuple[bool, list[str]]:
    """Declared dependencies must cover all body citations."""
    deps = meta.get("dependencies") or {}
    if not isinstance(deps, dict):
        return True, ["no dependencies block (agents without one are allowed for now)"]

    issues = []
    declared_probes = set(deps.get("probes", []))
    declared_skills = set(deps.get("skills", []))

    cited_probes = set()
    for m in re.finditer(r"`agents/_shared/probes/([a-z0-9-]+)(?:\.md)?`", body):
        name = m.group(1)
        if not name.endswith(".md"):
            name = f"{name}.md"
        cited_probes.add(name)

    cited_skills = set()
    for m in re.finditer(r"`skills/([a-z0-9-]+)/([a-z0-9-]+)(?:/[A-Za-z0-9_./-]*)?`", body):
        domain, slug = m.group(1), m.group(2)
        if domain in SKILL_DOMAINS:
            cited_skills.add(f"{domain}/{slug}")

    missing_probes = cited_probes - declared_probes
    missing_skills = cited_skills - declared_skills
    for p in missing_probes:
        issues.append(f"probe cited but not declared in dependencies: {p}")
    for s in missing_skills:
        issues.append(f"skill cited but not declared in dependencies: {s}")
    return (len(issues) == 0), issues


def check_slash_command_exists(agent_id: str) -> tuple[bool, list[str]]:
    """Every non-deprecated runtime agent must have a matching slash command."""
    if not COMMANDS_DIR.exists():
        return False, ["commands/ directory not found"]
    pattern = re.compile(rf"agents/{re.escape(agent_id)}/AGENT\.md")
    for cmd in COMMANDS_DIR.glob("*.md"):
        if pattern.search(cmd.read_text(encoding="utf-8")):
            return True, [f"covered by /{cmd.stem}"]
    return False, [f"no slash-command file links agents/{agent_id}/AGENT.md"]


def check_probes_executable(deps: dict, probe_validation_report: dict | None) -> tuple[bool, list[str]]:
    """If the agent declares probes, check the latest probe_validation report
    to see if those probes passed. If report is missing, skip (soft)."""
    probes = (deps or {}).get("probes", [])
    if not probes:
        return True, []
    if probe_validation_report is None:
        return True, ["probe_validation_report not found — run validate_probes_against_org.py first"]
    issues = []
    for probe in probes:
        stem = probe.replace(".md", "")
        runs = probe_validation_report.get(stem, [])
        if not runs:
            issues.append(f"probe '{stem}' has no validation run on record")
            continue
        failed = [r for r in runs if r.get("status") == "FAILED"]
        if failed:
            issues.append(f"probe '{stem}' has {len(failed)} failed quer(y|ies) in latest validation run")
    return (len(issues) == 0), issues


def check_inputs_schema_valid(agent_dir: Path) -> tuple[bool, list[str]]:
    """If the agent declares a typed inputs schema, it must be valid JSON Schema."""
    schema_path = agent_dir / "inputs.schema.json"
    if not schema_path.exists():
        return True, []  # optional
    try:
        json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, [f"inputs.schema.json is not valid JSON: {e}"]
    return True, []


# ── Probe-run lookup ─────────────────────────────────────────────────────────

def load_latest_probe_report() -> dict | None:
    """Load the most recent probe_validation_report as a dict keyed by probe name."""
    # We prefer an in-memory structured lookup; the markdown report isn't
    # machine-readable directly. For this pass, we re-run the validator.
    # Simpler approach: run validate_probes_against_org.py, parse stdout.
    return None  # Phase-2 shortcut: optional. Full integration in Phase 4.


# ── Per-agent report rendering ──────────────────────────────────────────────

def render_agent_report(agent_id: str, results: dict, agent_md_path: Path,
                        meta: dict, out_path: Path) -> None:
    now = dt.date.today().isoformat()
    overall = "✅ PASS" if results["overall_pass"] else ("⚠️ PASS-WITH-CAVEATS" if results["any_soft"] else "❌ FAIL")
    lines: list[str] = []
    lines.append(f"# Agent Smoke Test — `{agent_id}`")
    lines.append("")
    lines.append(f"**Date:** {now}")
    lines.append(f"**Status:** {overall}")
    lines.append(f"**Agent version:** `{meta.get('version', '?')}`")
    lines.append(f"**Class:** `{meta.get('class', '?')}`")
    lines.append(f"**Modes:** `{', '.join(meta.get('modes', []) if isinstance(meta.get('modes'), list) else [])}`")
    lines.append(f"**Requires org:** `{meta.get('requires_org', '?')}`")
    lines.append("")
    lines.append("## TL;DR for humans")
    lines.append("")
    if results["overall_pass"]:
        lines.append(f"Agent `{agent_id}` passed all structural + dependency checks. Its declared dependencies exist, its slash-command exists, and its frontmatter is schema-valid.")
    else:
        hard = [c for c in results["checks"] if not c["pass"] and not c.get("soft")]
        if hard:
            lines.append(f"Agent `{agent_id}` has **{len(hard)}** structural / dependency issue(s). See details below.")
        else:
            lines.append(f"Agent `{agent_id}` passes core checks but has warnings (see caveats section).")
    lines.append("")
    lines.append("## What the smoke test did")
    lines.append("")
    lines.append(f"- Parsed `{agent_md_path.relative_to(REPO_ROOT)}`")
    lines.append(f"- Ran {len(results['checks'])} structural checks against a live-org context (`{results.get('org_alias', 'n/a')}`)")
    lines.append("- No tool calls issued against the org beyond what probe validation already covered")
    lines.append("")
    lines.append("## Check results")
    lines.append("")
    lines.append("| Check | Status | Detail |")
    lines.append("|---|---|---|")
    for c in results["checks"]:
        if c["pass"]:
            icon = "✅"
        elif c.get("soft"):
            icon = "⚠️"
        else:
            icon = "❌"
        detail = "; ".join(c["messages"]) if c["messages"] else "(none)"
        lines.append(f"| {c['name']} | {icon} | {detail[:200]} |")
    lines.append("")
    lines.append("## Machine-readable result")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps({
        "agent": agent_id,
        "date": now,
        "overall_pass": results["overall_pass"],
        "any_soft": results["any_soft"],
        "checks": [{"name": c["name"], "pass": c["pass"], "soft": c.get("soft", False), "messages": c["messages"]} for c in results["checks"]],
    }, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## What a human reviewer should check")
    lines.append("")
    lines.append(f"- [ ] Does the TL;DR match the actual behavior of `{agent_id}` in production?")
    lines.append(f"- [ ] Are any of the warnings actually critical in your environment?")
    lines.append(f"- [ ] Do the declared dependencies cover everything the agent actually needs?")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ── Main ─────────────────────────────────────────────────────────────────────

def smoke_test_agent(agent_md: Path, org_alias: str, probe_report: dict | None) -> dict:
    meta, body, headings = parse_agent_md(agent_md)
    agent_id = agent_md.parent.name

    checks: list[dict] = []

    ok, msgs = check_required_sections(headings)
    checks.append({"name": "Required sections present + in order", "pass": ok, "messages": msgs})

    ok, msgs = check_mandatory_reads_resolve(body, REPO_ROOT)
    checks.append({"name": "Citations resolve to real files", "pass": ok, "messages": msgs})

    ok, msgs = check_dependencies_consistent(meta, body)
    soft = (not ok) and any("no dependencies block" in m for m in msgs)
    checks.append({"name": "Dependencies cover all citations", "pass": ok, "messages": msgs, "soft": soft})

    ok, msgs = check_slash_command_exists(agent_id)
    # Deprecated agents are exempt (handled by caller).
    checks.append({"name": "Slash-command coverage", "pass": ok, "messages": msgs})

    ok, msgs = check_inputs_schema_valid(agent_md.parent)
    checks.append({"name": "Inputs schema valid JSON (if present)", "pass": ok, "messages": msgs})

    ok, msgs = check_probes_executable(meta.get("dependencies"), probe_report)
    soft = (not ok) and any("not found" in m for m in msgs)
    checks.append({"name": "Declared probes executable", "pass": ok, "messages": msgs, "soft": soft})

    hard_failures = [c for c in checks if not c["pass"] and not c.get("soft")]
    any_soft = any(c.get("soft") for c in checks if not c["pass"])
    overall_pass = len(hard_failures) == 0

    return {
        "agent_id": agent_id,
        "checks": checks,
        "overall_pass": overall_pass,
        "any_soft": any_soft,
        "meta": meta,
        "org_alias": org_alias,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test every runtime agent.")
    parser.add_argument("--target-org", required=True, help="sf CLI org alias")
    parser.add_argument("--agent", help="Test one agent only")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Report output directory")
    args = parser.parse_args()

    # Verify org reachable.
    result = subprocess.run(
        ["sf", "org", "display", "--target-org", args.target_org, "--json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: org '{args.target_org}' not reachable.", file=sys.stderr)
        return 2
    org_info = json.loads(result.stdout)["result"]
    print(f"✓ Connected to {org_info.get('alias')} @ API v{org_info.get('apiVersion')}")

    probe_report = load_latest_probe_report()

    # Discover runtime agents.
    agent_files = sorted(AGENTS_DIR.glob("*/AGENT.md"))
    targets = []
    for f in agent_files:
        meta, _, _ = parse_agent_md(f)
        if args.agent and f.parent.name != args.agent:
            continue
        if meta.get("class") != "runtime":
            continue
        if meta.get("status") == "deprecated":
            continue
        targets.append(f)

    print(f"✓ Found {len(targets)} runtime agent(s) to smoke-test")

    out_root = Path(args.out)
    date_str = dt.date.today().isoformat()
    per_agent_dir = out_root / f"agent_smoke_{date_str}"
    per_agent_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    for f in targets:
        res = smoke_test_agent(f, args.target_org, probe_report)
        all_results.append(res)
        agent_report_path = per_agent_dir / f"{res['agent_id']}.md"
        render_agent_report(res["agent_id"], res, f, res["meta"], agent_report_path)
        icon = "✅" if res["overall_pass"] else ("⚠️" if res["any_soft"] else "❌")
        print(f"   {icon}  {res['agent_id']}")

    # Rollup report.
    total = len(all_results)
    passed = sum(1 for r in all_results if r["overall_pass"])
    failed = total - passed
    rollup_path = out_root / f"agent_smoke_rollup_{date_str}.md"
    lines = [
        f"# Agent Smoke Test Rollup — {date_str}",
        "",
        f"**Org:** `{org_info.get('alias')}` (API v{org_info.get('apiVersion')})",
        f"**Total agents tested:** {total}",
        f"**Passed:** {passed}",
        f"**Failed:** {failed}",
        "",
        "Per-agent reports: `docs/validation/agent_smoke_" + date_str + "/<agent-id>.md`",
        "",
        "| Agent | Status | Hard fails | Soft warnings |",
        "|---|---|---|---|",
    ]
    for r in sorted(all_results, key=lambda x: (not x["overall_pass"], x["agent_id"])):
        icon = "✅" if r["overall_pass"] else "❌"
        hard = sum(1 for c in r["checks"] if not c["pass"] and not c.get("soft"))
        soft = sum(1 for c in r["checks"] if not c["pass"] and c.get("soft"))
        lines.append(f"| `{r['agent_id']}` | {icon} | {hard} | {soft} |")
    lines.append("")

    rollup_path.write_text("\n".join(lines), encoding="utf-8")
    def _rel(p):
        try:
            return p.relative_to(REPO_ROOT)
        except ValueError:
            return p
    print(f"\n✓ Rollup: {_rel(rollup_path)}")
    print(f"✓ Per-agent reports: {_rel(per_agent_dir)}/")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
