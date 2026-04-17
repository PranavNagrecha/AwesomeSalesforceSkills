# Picklist Governor Agent

## What This Agent Does

Governs picklist hygiene across an sObject (or the full org): Global Value Set adoption vs inline picklists, inactive-value drift, label/API drift, translation coverage, dependent picklist correctness, picklist values used by formulas/flows/integrations, and the "picklist chain" anti-pattern (field A drives field B drives field C). Returns findings + a consolidation plan for migration from inline picklists to Global Value Sets.

**Scope:** One sObject per invocation (or `org` for a horizontal scan; sampled).

---

## Invocation

- **Direct read** — "Follow `agents/picklist-governor/AGENT.md` for Opportunity"
- **Slash command** — [`/govern-picklists`](../../commands/govern-picklists.md)
- **MCP** — `get_agent("picklist-governor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/picklist-and-value-sets`
4. `skills/admin/picklist-field-integrity-issues`
5. `skills/admin/multi-language-and-translation`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `scope` | yes | `object:<ApiName>` \| `org` |
| `target_org_alias` | yes |
| `include_inactive` | no | default `true` — inactive values are part of the audit |

---

## Plan

1. **Inventory picklists** — For the object: `tooling_query("SELECT QualifiedApiName, DataType, ValueSet FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '<object>' AND DataType IN ('Picklist','MultiselectPicklist')")`. `ValueSet` JSON is the source of truth for values, restricted flag, and value-set reference.
2. **GVS inventory** — `tooling_query("SELECT DeveloperName, MasterLabel, IsActive, ValueSet FROM GlobalValueSet")`. Map which object picklists use which GVS.
3. **Per picklist, score:**
   - **GVS-eligible inline picklist** — inline values that exactly match an existing GVS → P1 (migrate to GVS).
   - **Restricted flag** — unrestricted picklists on persona-facing fields → P1 (invites data-quality drift).
   - **Inactive-value drift** — > 10% of the picklist's values are inactive → P2.
   - **Label/API name drift** — API name and label meaningfully differ → P2 (readability).
   - **Translation coverage** — if the org has > 1 active language (probe `tooling_query("SELECT IsoCode FROM Language WHERE IsActive = true")`) and the picklist lacks translations → P1.
   - **Dependent picklist correctness** — fetch `tooling_query("SELECT Id, CustomFieldDefinitionId FROM CustomFieldDefinition WHERE … ")` plus `tooling_query` on `PicklistDependency` / describe API; identify controlling → controlled chains > 2 levels deep (e.g. Status → Sub-Status → Reason-Code → Final-Code). Chains > 2 are P1 — consider flattening.
4. **Usage probe** — for each picklist, is it referenced by:
   - Any formula field on the same object? (`tooling_query` on CustomField metadata)
   - Any VR? (`list_validation_rules`)
   - Any Flow? (`list_flows_on_object` + Metadata text search)
   - Any integration mapping? (heuristic: field label shows up in `NamedCredential` endpoint names — best-effort).
5. **Emit consolidation plan** — for inline → GVS migrations, propose the target GVS, the rename steps, and the data-migration consideration (rows with inactive values can't always be replaced silently).

---

## Output Contract

1. **Summary** — picklist count, GVS adoption %, max severity, confidence.
2. **Per-picklist findings** — table.
3. **Dependency graph** — controlling → controlled chains visualized.
4. **Consolidation plan** — candidate migrations with step-by-step.
5. **Process Observations**:
   - **What was healthy** — GVS adoption, translation coverage, restricted-picklist discipline.
   - **What was concerning** — deep dependency chains, unrestricted persona-facing picklists, orphan GVSes.
   - **What was ambiguous** — picklists used only by inactive artifacts (flows/VRs paused).
   - **Suggested follow-up agents** — `record-type-and-layout-auditor` (if RT-level picklist filtering is implicated), `field-impact-analyzer` for any picklist whose values drive downstream integrations.
6. **Citations**.

---

## Escalation / Refusal Rules

- Picklist has > 500 values → refuse per-value audit; recommend splitting into GVS + controlled vocabulary.
- Multi-language org but 0% translation coverage across picklists → return org-level P0 in Process Observations, suggest `skills/admin/multi-language-and-translation` as the first step.

---

## What This Agent Does NOT Do

- Does not modify picklist values in the org.
- Does not deploy GVS migrations.
- Does not clean data rows with invalid picklist values (separate data-fix project).
- Does not auto-chain.
