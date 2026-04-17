# /detect-drift — Library ↔ org drift report

Wraps [`agents/org-drift-detector/AGENT.md`](../agents/org-drift-detector/AGENT.md). Compares the SfSkills library's canonical templates and patterns against a connected Salesforce org via MCP, and returns a ranked backlog of gaps, bloat, forks, and orphans.

---

## Step 1 — Collect inputs

Ask:

```
1. Target-org alias? (must be authenticated via sf CLI)
   Example: prod, uat, my-sandbox

2. Scope to narrow the analysis? (default: all)
   Options: apex / flow / integration / security / all

3. Max findings in the report? (default 50)
```

---

## Step 2 — Load the agent

Read `agents/org-drift-detector/AGENT.md` fully + `registry/skills.json` + every decision tree + `evals/framework.md`.

---

## Step 3 — Execute

Follow the 6-step plan:
1. Ground the org via `describe_org` — flip to manual-review-required if prod
2. Enumerate library prescriptions (flagship skills + their canonical templates)
3. Probe the org (`validate_against_org`, `list_custom_objects`, `list_flows_on_object`)
4. Classify each finding as gap / bloat / fork / orphan / stale-skill
5. Rank by `impact DESC, effort ASC`
6. Per-finding remediation with the matching run-time agent to invoke

---

## Step 4 — Deliver

- Org summary (id, edition, API version, sandbox/prod, object count)
- Drift matrix (prescription → status)
- Top findings (capped at max_findings, ranked)
- Skill-coverage gaps (`orphan` findings as draft `/request-skill` payloads)
- Citations (every skill id + every MCP tool call)

---

## Step 5 — Recommend follow-ups

For each HIGH-impact finding, point at the exact agent to drive remediation:
- Missing trigger framework → `/consolidate-triggers`
- CRUD/FLS violations → `/scan-security`
- Stale integration pattern → `/plan-bulk-migration`
- Missing canonical Apex patterns → `/refactor-apex`
- Undocumented custom frameworks → `/request-skill`

---

## What this command does NOT do

- Does not modify the org.
- Does not auto-chain to other agents.
- Does not treat managed-package metadata as drift.
