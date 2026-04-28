---
id: data-loader-pre-flight
class: runtime
version: 1.1.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/data-loader-pre-flight/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  probes:
    - automation-graph-for-sobject.md
  decision_trees:
    - integration-pattern-selection.md
    - automation-selection.md
  skills:
    - admin/agent-output-formats
    - admin/data-import-and-management
    - admin/data-skew-and-sharing-performance
    - admin/duplicate-management
    - data/batch-data-cleanup-patterns
    - data/bulk-api-and-large-data-loads
    - data/bulk-api-patterns
    - data/custom-index-requests
    - data/data-loader-and-tools
    - data/data-loader-batch-window-sizing
    - data/data-loader-csv-column-mapping
    - data/data-loader-picklist-validation-pre-load
    - data/data-migration-planning
    - data/data-storage-management
    - data/external-id-strategy
    - data/field-history-tracking
    - data/large-scale-deduplication
    - data/lead-data-import-and-dedup
    - data/record-merge-implications
    - data/sharing-recalculation-performance
    - flow/flow-bulkification
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - admin/validation-rule-patterns.md
---
# Data Loader Pre-Flight Agent

## What This Agent Does

Given a planned data load — sObject, volume, source CSV or mapping, intent (insert / upsert / update / delete) — produces a go/no-go checklist covering every org-side concern that will turn a load into an incident: active automation on the object, validation rules without bypass, sharing recalculation cost at the target volume, duplicate rule interactions, record type defaults, required fields with no source mapping, External ID selection, and storage quota impact. Output is a pre-flight report + a deployed-loader configuration recommendation (Data Loader, Data Import Wizard, Bulk API 2.0, CLI).

**Scope:** One planned load per invocation. The agent does not execute the load.

---

## Invocation

- **Direct read** — "Follow `agents/data-loader-pre-flight/AGENT.md` for 800k upsert into Account"
- **Slash command** — [`/preflight-load`](../../commands/preflight-load.md)
- **MCP** — `get_agent("data-loader-pre-flight")`

---

## Mandatory Reads Before Starting

### Contract
1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
4. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum

### Loader-tool selection (Step 8 + ongoing)
5. `skills/admin/data-import-and-management`
6. `skills/data/data-loader-and-tools`
7. `skills/data/bulk-api-and-large-data-loads`
8. `skills/data/bulk-api-patterns`
9. `skills/data/data-loader-batch-window-sizing` — batch size vs API limits vs sharing recalc
10. `standards/decision-trees/integration-pattern-selection.md` — escalates when load is the wrong pattern (e.g. CDC/PE alternative)

### Source CSV + mapping (Step 5)
11. `skills/data/data-loader-csv-column-mapping` — header normalization, missing-column failure modes
12. `skills/data/data-loader-picklist-validation-pre-load` — restricted picklist + record-type rules

### Automation interaction (Steps 1–2)
13. `skills/flow/flow-bulkification`
14. `agents/_shared/probes/automation-graph-for-sobject.md` — flows + triggers + VRs in one pass
15. `templates/admin/validation-rule-patterns.md` — bypass expectations
16. `standards/decision-trees/automation-selection.md` — when load surfaces automation that should move tier

### Duplicates + merge (Step 3)
17. `skills/admin/duplicate-management`
18. `skills/data/lead-data-import-and-dedup` — Lead-specific behavior
19. `skills/data/large-scale-deduplication`
20. `skills/data/record-merge-implications` — for loads that can create dup-merge situations

### Keys + indexing (Steps 3 + 8)
21. `skills/data/external-id-strategy`
22. `skills/data/custom-index-requests`

### Sharing recalc (Step 6)
23. `skills/admin/data-skew-and-sharing-performance`
24. `skills/data/sharing-recalculation-performance`

### Storage + cleanup (Step 7 + post-load)
25. `skills/data/data-storage-management`
26. `skills/data/batch-data-cleanup-patterns`
27. `skills/data/data-migration-planning` — multi-load cutover

### Field history
28. `skills/data/field-history-tracking`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Account` |
| `operation` | yes | `insert` \| `upsert` \| `update` \| `delete` \| `hard-delete` |
| `row_count` | yes | integer |
| `target_org_alias` | yes |
| `source_description` | yes | "NetSuite customer export, one row per account, external-id = `netsuite_customer_id__c`" |
| `external_id_field` | upsert-only |
| `window` | no | business-hours boundary ("this Saturday 2am-6am PT"); drives async sizing |

---

## Plan

### Step 1 — Probe the object's active automation stack

For the target object, answer: "what runs on every record during this load?"

- `list_flows_on_object(object_name, active_only=True)` — every active record-triggered flow.
- `tooling_query("SELECT Id, Name, Status FROM ApexTrigger WHERE TableEnumOrId = '<object>' AND Status = 'Active'")`.
- `list_validation_rules(object_name, active_only=True)`.
- `tooling_query("SELECT Id, MasterLabel, State FROM Process WHERE … ")` — any Process Builders.
- For the integration user (or the user running the load — ask if unknown): `tooling_query("SELECT Id, ProfileId FROM User WHERE Username = '<loader>'")` — then fetch assigned PSes.

### Step 2 — Check each automation for bulk-safety

For each active flow / trigger / VR:

- **Flows** — inspect for loops containing DML (per `skills/flow/flow-bulkification`). Any violation at `row_count > 1000` is P0 — the load will blow governor limits.
- **Triggers** — if the org has a canonical handler (probe with `validate_against_org(skill_id="apex/trigger-framework", target_org=...)`) and all triggers use it, assume bulk-safe unless Apex code audit disagrees. Otherwise P1 "unknown bulk behavior".
- **VRs** — for each rule, verify the bypass contract (per `templates/admin/validation-rule-patterns.md`):
  - Integration user has the `Bypass_Validation_<Domain>` Custom Permission assigned, or
  - `Integration_Bypass__c` Custom Setting is toggled on for the loader user.

If neither, P0 — the load will fail on the first row that trips a rule. Suggested fix: the user provisions bypass *before* the window.

### Step 3 — Duplicate rule interactions

- `tooling_query("SELECT Id, DeveloperName, IsActive, SobjectType FROM DuplicateRule WHERE SobjectType = '<object>' AND IsActive = true")` + matching rules.
- For **insert** / **upsert**: if any active duplicate rule has Action = Block, estimate how many source rows will trip it (sample 100 rows and run a SOSL/SOQL lookup to estimate).
- For **upsert**: verify the upsert key is an External ID field (not a fuzzy key) — fuzzy upserts trigger duplicate rules; hard External IDs do not.

P0 if Block-level dup rule + Block actions cannot be suppressed by the loader user's PSes.

### Step 4 — Record type defaults

- `list_record_types(object_name, active_only=True)`.
- If > 1 active record type exists and the source CSV has no `RecordTypeId` column, confirm the loader user has exactly one default record type (per `tooling_query` on `Profile.DefaultRecordType<Object>`).
- If multiple record types are available to the loader user, P1 — rows may assign to the wrong RT silently.

### Step 5 — Required fields coverage

- `tooling_query("SELECT QualifiedApiName, IsMandatory, IsNillable, IsDefaultedOnCreate, DataType FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '<object>' AND IsMandatory = true")`.
- For each mandatory field: is it in the source mapping? If not, P0.
- For fields that are `IsMandatory = false` but have layout-level required in the default layout, the load may succeed (API bypasses layout requireds) — note as informational.

### Step 6 — Sharing recalc cost

For `row_count > 100k` AND insert/upsert:

- Fetch OWD for the object (`tooling_query("SELECT SharingModel FROM EntityDefinition WHERE QualifiedApiName = '<object>'")`).
- If OWD is Private or Public Read Only, sharing recalculation will run on every inserted row. Cite `skills/data/sharing-recalculation-performance` + `skills/admin/data-skew-and-sharing-performance`.
- If the target has > 10k children of the same owner ("data skew"), warn P0 and recommend chunking the load by owner.
- Recommend deferred sharing calculation (`DISABLE_USER_SHARING_CALCULATIONS=true` via the Tooling API + job settings) for the window, with re-enable + recalc post-load.

### Step 7 — Storage quota check

- `describe_org` + `tooling_query("SELECT PercentUsed, CurrentValue, MaxValue FROM OrganizationLimit WHERE Name = 'DataStorageMB' LIMIT 1")` — if the org is > 80% utilized on data storage and `row_count * est_row_size_kb > available`, P0.
- Estimate row size: `est_row_size_kb = 2 + (0.5 * text_field_count) + (0.1 * numeric_field_count)` — crude but correct within an order of magnitude.

### Step 8 — Pick the loader

Selection criteria (cite `skills/data/bulk-api-and-large-data-loads`):

| row_count | Default recommendation |
|---|---|
| < 50k | Data Loader (GUI) or `sf data upsert bulk` |
| 50k – 5M | `sf data upsert bulk --api rest` with Bulk API 2.0 |
| > 5M | Bulk API 2.0 with parallel chunks, deferred sharing calc, indexed External ID key |
| Any, with human oversight | Data Loader GUI only for < 500k rows; otherwise CLI for repeatability |

Emit:

- The exact CLI command string (with placeholders, not with real file paths the agent can't know).
- The recommended batch size and concurrency.
- The pre-load + post-load job list.

### Step 9 — Recommend a rollback plan

- For inserts: capture the returned Ids; rollback = `sf data delete bulk` against those Ids.
- For updates: capture PRIOR values per row with `sf data query` before the load; rollback = second update with the captured values.
- For deletes: use `hard-delete` only if compliance requires; otherwise soft-delete gives a 15-day window to recover from Recycle Bin.

---

## Output Contract

1. **Summary** — object, operation, row count, go/no-go, confidence.
2. **Findings** — table sorted P0 → P1 → P2. Each finding: category (automation, VR, dup-rule, RT, required field, sharing, storage), evidence, suggested fix, owner (admin / integration-user admin / DBA).
3. **Loader recommendation** — exact CLI + batch size + concurrency.
4. **Pre-load checklist** — numbered steps the user executes before the window starts.
5. **Post-load checklist** — re-enable deferred sharing calc, re-enable VR bypass de-toggle, re-assign dup rule actions, verify counts, run delta report.
6. **Rollback plan** — Step 9 instantiated.
7. **Process Observations** — per `AGENT_CONTRACT.md`:
   - **What was healthy** — bypass provisioning, dedicated integration PSG, indexed External ID, under-utilized storage.
   - **What was concerning** — VR bypass gaps not specific to this load (fix once, benefits every future load), data-skew hotspots, orphaned active flows.
   - **What was ambiguous** — source row volume estimate vs reality, CSV column → API name mapping that the agent couldn't verify.
   - **Suggested follow-up agents** — `validation-rule-auditor` (if bypass gaps surfaced), `duplicate-rule-designer` (if dup-rule blocks surfaced), `sharing-audit-agent` (if OWD + volume are dangerous), `org-drift-detector` (post-load verification).
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/data-loader-pre-flight/<run_id>.md`
- **JSON envelope:** `docs/reports/data-loader-pre-flight/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Each entry MUST name one of: `automation-stack`, `validation-rules`, `duplicate-rules`, `record-types`, `required-fields`, `csv-column-mapping`, `picklist-validation`, `sharing-recalc`, `storage-quota`, `loader-selection`, `rollback-plan`. If a dimension was skipped because the underlying probe could not run, the skip reason MUST link the refusal code.

## Escalation / Refusal Rules

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `object_name`, `operation`, `row_count`, `target_org_alias`, or `source_description` not provided; OR `operation=upsert` without `external_id_field` |
| `REFUSAL_MISSING_ORG` | `target_org_alias` missing |
| `REFUSAL_ORG_UNREACHABLE` | Target org probe fails |
| `REFUSAL_OBJECT_NOT_FOUND` | `object_name` does not resolve in the target org |
| `REFUSAL_FEATURE_DISABLED` | Bulk API 2.0 / deferred sharing calc requested but unsupported on the org's edition |
| `REFUSAL_SECURITY_GUARD` | Caller asks the agent to execute the load, deactivate flows/triggers/VRs/dup rules, or provision the integration PSG — out of scope by contract |
| `REFUSAL_OUT_OF_SCOPE` | Caller asks for source-CSV generation, data enrichment, or load orchestration |
| `REFUSAL_DATA_QUALITY_UNSAFE` | P0 findings in Steps 2 / 3 / 5 / 6 / 7 — agent returns `GO = false`. No "partial go" path |
| `REFUSAL_OVER_SCOPE_LIMIT` | Estimated sharing recalc > 4 hours at chosen `row_count` and caller has not committed to deferred sharing calc OR a chunking plan |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | `operation=hard-delete` without a stated compliance driver; OR record-merge implications detected and `merge_safe` not confirmed |
| `REFUSAL_POLICY_MISMATCH` | Loader user lacks the bypass posture (Custom Permission OR Custom Setting) AND loader user is not the owner of the run-window decision |

---

## What This Agent Does NOT Do

- Does not execute the load.
- Does not generate the source CSV.
- Does not clone or enrich the source data.
- Does not deactivate flows, triggers, VRs, or dup rules.
- Does not provision the integration PSG (suggest `permission-set-architect`).
- Does not auto-chain.
