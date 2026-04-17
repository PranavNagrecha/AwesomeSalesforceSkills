# Record Type & Layout Auditor Agent

## What This Agent Does

Audits the Record Type + Page Layout surface on a target sObject: record-type count vs persona count, page-layout assignment coverage, picklist value set per record type, master-default-record-type drift, and the relationship between record types and Lightning Record Pages. Identifies the three common failure patterns: record-type proliferation, Master Layout as primary, and orphan record types.

**Scope:** One sObject per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/record-type-and-layout-auditor/AGENT.md` for Case"
- **Slash command** — [`/audit-record-types`](../../commands/audit-record-types.md)
- **MCP** — `get_agent("record-type-and-layout-auditor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/record-type-strategy-at-scale`
4. `skills/admin/record-types-and-page-layouts`
5. `skills/admin/picklist-and-value-sets`
6. `skills/admin/picklist-field-integrity-issues`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `object_name` | yes | `Case` |
| `target_org_alias` | yes |

---

## Plan

1. **Inventory record types** — `list_record_types(object_name)`. Fetch each record type's metadata via `tooling_query("SELECT Id, DeveloperName, Metadata FROM RecordType WHERE Id = '<id>'")` to read business process + picklist value mappings.
2. **Inventory page layouts** — `tooling_query("SELECT Id, Name, SobjectType, LayoutType, CreatedDate, LastModifiedDate FROM Layout WHERE EntityDefinition.QualifiedApiName = '<object>'")` (via Tooling).
3. **Inventory assignments** — profile/PS → RT → Layout map. Use `tooling_query` on `ProfileLayout` / `PermissionSetAssignmentFieldLevelSecurity` equivalents; fall back to the `--metadata Profile` export if Tooling API lacks coverage.
4. **Score against patterns:**
   - **Record-type count > 6** on a single object → P1 (record-type proliferation). Cite `skills/admin/record-type-strategy-at-scale`.
   - **Master Layout as primary assignment** for any active persona → P1.
   - **Orphan record type** (no active users assigned) → P1.
   - **Inactive record type still referenced by active flows/VRs** → P0.
   - **Description blank** on any RT → P2.
   - **Picklist value sets diverge widely across RTs on the same field** → P2 (consider GVS with record-type filter).
5. **Lightning Record Page ↔ RT mapping** — `tooling_query` on `FlexiPageRegionAssignment` and `ProfilePageAssignment`. Record types without a dedicated LRP default to a generic page — P2 if the RT is persona-specific.
6. **Emit findings + remediation suggestions.**

---

## Output Contract

1. **Summary** — object, RT count, layout count, max severity, confidence.
2. **Record type table** — each RT with layout, active user count, LRP assignment, description quality.
3. **Findings** — sorted by severity with evidence.
4. **Remediation suggestions** — consolidation candidates (RTs that could merge), deprecation candidates (orphan RTs), rename candidates (naming drift).
5. **Process Observations**:
   - **What was healthy** — Master Layout not in active rotation, RTs named per convention.
   - **What was concerning** — RT proliferation over time (compare CreatedDate clustering), RTs whose Business Process points at an inactive sales/service process.
   - **What was ambiguous** — RTs shared across Record Types (implicit inheritance via relationships).
   - **Suggested follow-up agents** — `lightning-record-page-auditor` (for the page-layer audit), `picklist-governor` (if picklist drift is the main story).
6. **Citations**.

---

## Escalation / Refusal Rules

- Object has > 20 record types → sample top 8 by assignment volume; flag count as P1.
- Inactive RT referenced by active flows → P0 escalation, recommend `flow-analyzer` before any further change.

---

## What This Agent Does NOT Do

- Does not activate/deactivate record types.
- Does not modify layouts or LRPs.
- Does not redesign picklist values (that's `picklist-governor`).
- Does not auto-chain.
