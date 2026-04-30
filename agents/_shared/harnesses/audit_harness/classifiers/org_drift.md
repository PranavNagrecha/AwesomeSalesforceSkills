# Classifier: org_drift

## Purpose

Compare the SfSkills library's prescriptions (canonical templates + recommended patterns) against the state of a connected org, reporting two directions of drift: **gaps** (skills recommend X but the org has no X) and **bloat** (the org has Y but no skill endorses it — candidate for deprecation or a missing skill). Produces a ranked remediation backlog. Consumes every MCP tool the server exposes. Not an audit of any single artifact — this is a horizontal sweep.

## Replaces

`org-drift-detector` (now a deprecation stub pointing at `audit-router --domain org_drift`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `scope` | no | `all` (default) \| `apex` \| `flow` \| `integration` \| `security` |
| `max_findings` | no | default `50` |

## Inventory Probe

1. `describe_org(target_org)` — edition, API version, sandbox/prod flag. Prod flips all recommendations to `manual-review-required`.
2. Walk `registry/skills.json` for flagship skills (those with files under `evals/golden/`). Extract prescribed templates + patterns.
3. Per-prescription probes:
   - Trigger framework: `validate_against_org(skill_id="apex/trigger-framework", target_org=...)`.
   - Application logger: `list_custom_objects` text-search for `Application_Log__c`.
   - Security utilities: `validate_against_org(skill_id="apex/apex-security-patterns", target_org=...)`.
   - Named Credentials vs Remote Site: query via `list_named_credentials` + `tooling_query("SELECT COUNT() FROM RemoteSiteSetting WHERE IsActive = true")`.
   - Flow bulkification: `list_flows_on_object` per object mentioned in flagship evals.
4. Skill currency: cross-reference skill `salesforce-version` with `describe_org` API version to detect stale prescriptions.

Inventory columns (beyond id/name/active): `prescription_skill`, `probe_result` (HAS / MISSING / PARTIAL / FORK / ORPHAN), `api_version_gap`.

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `DRIFT_GAP` | P1 | Library prescribes a template/pattern; org has no equivalent | skill + prescription + probe result | Recommend the canonical template; route remediation to the matching run-time agent |
| `DRIFT_BLOAT` | P1 | Org has a custom framework parallel to a canonical template (e.g. custom trigger handler predating `TriggerHandler`) | org artifact + matching template | Plan migration to canonical template — cite `apex-refactorer` / `trigger-consolidator` |
| `DRIFT_FORK` | P1 | Org has the same pattern but diverges (e.g. `TriggerHandler` base class exists but lacks `TriggerControl`) | org artifact + divergence | Align with canonical shape |
| `DRIFT_ORPHAN` | P2 | Org has a custom framework with no corresponding SfSkills skill | org artifact + absence in registry | Author a new skill via `/request-skill`; emit the draft payload |
| `DRIFT_STALE_SKILL` | P2 | Prescribing skill's `salesforce-version` is older than the org's current release | skill version + org version | Flag for `currency-monitor` |
| `DRIFT_SECURITY_GAP` | P0 | Missing security prescription (FLS enforcement, no Named Credentials, Remote Site usage on integration endpoints) | prescription + probe | Immediate remediation — route via `security-scanner` |
| `DRIFT_INTEGRATION_LEGACY` | P1 | Org uses `RemoteSiteSetting` for any external endpoint a skill prescribes via Named Credential | endpoint + remote site count | Migrate to Named Credential |

## Patches

None. Drift findings are pointers to the skill + the matching run-time agent (`apex-refactorer`, `trigger-consolidator`, `security-scanner`, `flow-analyzer`, etc.) — mechanical patches are emitted by those downstream agents, not by `org_drift` itself.

## Mandatory Reads

- `registry/skills.json` — via `search_skill` / `get_skill`
- `skills/devops/metadata-diff-between-sandboxes` — when drift question is "what differs between two specific orgs"
- `templates/README.md`
- `standards/decision-trees/` — all four files
- `evals/framework.md`

## Escalation / Refusal Rules

- `target_org_alias` not authenticated → `REFUSAL_MISSING_ORG`.
- `describe_org` returns prod AND scope includes write-style recommendations → flip all recommendations to `manual-review-required`.
- `validate_against_org` fails for > 3 skills in a row → stop probing, flag MCP tool as misconfigured, finish with partial data. `REFUSAL_NEEDS_HUMAN_REVIEW`.
- Finding count > `max_findings` (default 50) → truncate to top-N ranked by `impact DESC, effort ASC`. `REFUSAL_OVER_SCOPE_LIMIT`.

## What This Classifier Does NOT Do

- Does not modify the org.
- Does not deploy templates.
- Does not auto-chain — links to run-time agents in the backlog.
- Does not flag managed-package metadata as drift (out of scope).
