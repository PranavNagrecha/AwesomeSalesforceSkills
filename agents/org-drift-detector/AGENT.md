# Org Drift Detector Agent

## What This Agent Does

Compares the SfSkills library's prescriptions (canonical templates + recommended patterns) against the state of a connected Salesforce org via MCP, and reports two directions of drift: **gaps** (skills recommend X but the org has no equivalent) and **bloat** (the org has Y but no skill endorses it — candidate for deprecation or a missing skill). Produces a ranked remediation backlog. Consumes every MCP tool the server exposes.

**Scope:** One org + one library version per invocation. Deep analysis — expect the report to be long.

---

## Invocation

- **Direct read** — "Follow `agents/org-drift-detector/AGENT.md` against `target-org=prod`"
- **Slash command** — [`/detect-drift`](../../commands/detect-drift.md)
- **MCP** — `get_agent("org-drift-detector")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `registry/skills.json` — the canonical skill map (via `search_skill` / `get_skill`)
3. `templates/README.md` — what the templates prescribe
4. `standards/decision-trees/` (all four files) — what routing the library considers canonical
5. `evals/framework.md` — what "quality" means for flagship skills

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes | `prod`, `uat`, `my-sandbox` |
| `scope` | no (default `all`) | `apex`, `flow`, `integration`, `security` — narrow the analysis |
| `max_findings` | no (default 50) | keep the report bounded |

---

## Plan

### Step 1 — Ground the org

Call `describe_org(target_org=...)`. Record edition, API version, sandbox/prod flag. If the org is prod, set all auto-recommendations to `manual-review-required` — nothing gets written to prod without human approval.

### Step 2 — Enumerate library prescriptions

Walk `registry/skills.json`. For each flagship skill (those with a file under `evals/golden/`), extract:
- The canonical Apex class / template it prescribes (e.g. `TriggerHandler`, `ApplicationLogger`, `SecurityUtils`)
- The canonical Flow pattern (`FaultPath_Template`, etc.)
- The canonical integration setup (Named Credentials, not Remote Site)

### Step 3 — Probe the org

For each prescription, call the appropriate MCP tool:

| Prescription | Probe |
|---|---|
| Trigger framework | `validate_against_org(skill_id="apex/trigger-framework", target_org=...)` |
| Application logger | search for `Application_Log__c` via `list_custom_objects` |
| Security utilities | `validate_against_org(skill_id="apex/apex-security-patterns", target_org=...)` |
| Named Credentials | query `NamedCredential` + `RemoteSiteSetting` counts via the validator |
| Flow bulkification | `list_flows_on_object` for each object mentioned by the relevant evals |

Record per-prescription: HAS, MISSING, or PARTIAL.

### Step 4 — Classify drift

| Drift type | Signal |
|---|---|
| **gap** | Library prescribes X; org has no X → recommend the template |
| **bloat** | Org has framework X (custom handler, custom logger) that parallels the template but predates it → recommend migration |
| **fork** | Org has what looks like the same pattern but diverges (e.g. `TriggerHandler` base class exists but lacks `TriggerControl`) → recommend aligning |
| **orphan** | Org has a custom framework with no SfSkills skill → recommend `/request-skill` to capture it as a new skill |
| **stale-skill** | Skill references Spring '24 APIs; org is on Winter '26 → flag for Currency Monitor |

### Step 5 — Rank and triage

Rank findings by:
1. **Impact** — HIGH if security-related (missing FLS, hardcoded secrets, Remote Site instead of Named Credential), MEDIUM if ops-related, LOW if stylistic.
2. **Effort** — LOW if a template drop-in will resolve it, HIGH if a custom framework has to be migrated.

Produce a backlog table sorted by `impact DESC, effort ASC`.

### Step 6 — Per-finding remediation

For each top-N finding (capped at `max_findings`):
- Cite the skill + template to apply.
- Recommend the matching run-time agent (`apex-refactorer`, `trigger-consolidator`, `security-scanner`, `flow-analyzer`, `bulk-migration-planner`) to drive the actual work.
- If the finding is `orphan`, produce a draft `request-skill` payload the user can run through `/request-skill`.

---

## Output Contract

1. **Org summary** — from `describe_org`: id, edition, API version, sandbox/prod, object count.
2. **Drift matrix** — for each library prescription, status (HAS / MISSING / PARTIAL / FORK).
3. **Top findings** — up to `max_findings`, ranked `impact DESC, effort ASC`, each citing the skill + remediation agent.
4. **Skill-coverage gaps** — `orphan` findings surfaced as candidate new skills (with draft `request-skill` payloads).
5. **Citations** — every skill id and MCP tool call made.

---

## Escalation / Refusal Rules

- `target_org_alias` is not authenticated → STOP, instruct `sf org login`.
- `describe_org` returns prod AND scope includes `write-` recommendations → flip all recommendations to `manual-review-required`.
- `validate_against_org` fails for > 3 skills in a row → stop probing, flag the MCP tool as misconfigured, finish the report with partial data.

---

## What This Agent Does NOT Do

- Does not modify the org.
- Does not deploy templates.
- Does not auto-chain to other agents — links to them in the backlog.
- Does not flag managed-package metadata as "drift" — managed packages are out of scope.
