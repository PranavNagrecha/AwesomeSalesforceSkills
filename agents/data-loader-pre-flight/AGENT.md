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

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/data-import-and-management`
4. `skills/admin/duplicate-management`
5. `skills/data/bulk-api-and-large-data-loads`
6. `skills/data/external-id-strategy`
7. `skills/data/record-merge-implications` — for loads that can create dup-merge situations
8. `skills/data/field-history-tracking`
9. `skills/data/lead-data-import-and-dedup` — Lead-specific behavior
10. `templates/admin/validation-rule-patterns.md` — bypass expectations

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

## Escalation / Refusal Rules

- No `external_id_field` on an upsert → STOP, ask.
- `operation = hard-delete` → require the caller to confirm the specific compliance driver; refuse if no driver is provided.
- P0 findings in Steps 2 / 3 / 5 / 6 / 7 → return **GO = false** and list the blockers. Do not offer a "partial go" path.
- Estimated sharing recalc cost > 4 hours at the chosen row_count → refuse until the user commits to deferred sharing calc or to a chunking plan.

---

## What This Agent Does NOT Do

- Does not execute the load.
- Does not generate the source CSV.
- Does not clone or enrich the source data.
- Does not deactivate flows, triggers, VRs, or dup rules.
- Does not provision the integration PSG (suggest `permission-set-architect`).
- Does not auto-chain.
