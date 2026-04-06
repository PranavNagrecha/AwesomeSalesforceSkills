---
name: picklist-field-integrity-issues
description: "Use when picklist data quality has degraded: unrestricted picklists accepting garbage API values, dependent picklist relationships bypassed by integrations, record type picklist value mappings drifting out of sync, or orphaned values appearing in reports. NOT for initial picklist creation or Global Value Set design (use picklist-and-value-sets), NOT for record type configuration itself (use record-types-and-page-layouts)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "picklist field has values that should not exist in the org"
  - "unrestricted picklist accepting junk data from API integrations"
  - "dependent picklist rules are not enforced when records are created via Data Loader"
  - "record type picklist value mapping is out of sync after deployment"
  - "how do I audit picklist values that violate the intended value set"
  - "picklist has hundreds of orphaned values from old imports"
tags:
  - picklist-integrity
  - unrestricted-picklist
  - dependent-picklist-bypass
  - record-type-mapping-drift
  - data-quality
  - picklist-audit
inputs:
  - "Object and field API names for the affected picklist(s)"
  - "Whether the picklist is restricted or unrestricted"
  - "Integration channels writing to the field (API, Data Loader, Bulk API, Flow)"
  - "Record types in use on the object and their expected picklist value subsets"
outputs:
  - "Picklist integrity audit report identifying invalid, orphaned, or unmapped values"
  - "Remediation plan with specific steps to restrict, clean, or re-map values"
  - "Validation rule or Apex trigger template to enforce integrity at the data layer"
dependencies:
  - picklist-and-value-sets
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Picklist Field Integrity Issues

Use this skill when picklist data quality has degraded in a Salesforce org. This covers three systemic integrity gaps the platform does not prevent by default: unrestricted picklists silently accepting arbitrary API values, dependent picklist relationships that are only enforced in the UI, and record type picklist value mappings that drift after deployments or manual edits. If the problem is creating or designing a picklist from scratch, use `picklist-and-value-sets` instead.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Is the picklist restricted or unrestricted?** Unrestricted picklists accept any string value via the API, even values not in the defined value set. Restricted picklists reject undefined values with `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`. This distinction is the single biggest driver of picklist data integrity problems.
- **What channels write to this field?** If only Lightning UI users create records, dependent picklist filtering works. If Data Loader, REST API, Bulk API, middleware, or Flows (in system context) also write records, dependent picklist rules are not enforced and any value can land in the field.
- **Are record types involved?** Each record type maintains its own subset of available picklist values. After deployments, sandbox refreshes, or manual edits, these mappings can silently drift so that values appear in one record type that were only intended for another.

---

## Core Concepts

### Restricted vs Unrestricted Picklists

Every custom picklist field in Salesforce is either **restricted** or **unrestricted**. This setting is controlled by the "Restrict picklist to the values defined in the value set" checkbox on the field definition.

**Unrestricted (default for many legacy fields):** The API treats the field as a text field that happens to have suggested values. Any string written via SOAP API, REST API, Bulk API, or Data Loader is accepted — even if it does not match any defined value. Over time this produces orphaned values that pollute reports, break automations that check `ISPICKVAL()`, and confuse users who see unexpected entries.

**Restricted:** The API rejects any value not in the active value set. Writes fail with error code `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`. Global Value Set-backed picklists are always restricted. Custom picklists can be toggled to restricted at any time, but toggling does NOT retroactively clean existing invalid data — it only prevents new violations.

**Key implication:** Converting an unrestricted picklist to restricted is safe for future writes but leaves historical garbage in place. You must audit and clean existing data separately.

### Dependent Picklist Enforcement Gap

Dependent picklist relationships (where a controlling field filters the available values of a dependent field) are enforced **only in the Lightning UI and Classic UI**. They are not enforced by:

- SOAP API / REST API / Bulk API
- Data Loader (all modes)
- Apex DML (unless you write custom validation)
- Flow record-creates running in system context
- Platform events that trigger record creation

This means any integration or automation that creates or updates records programmatically can write a dependent picklist value that violates the controlling-dependent mapping. The record saves successfully with no error. This is documented Salesforce platform behavior, not a bug.

**Practical impact:** Organizations that rely on dependent picklists for data segmentation (e.g., Country controls State) often discover after months of API imports that thousands of records have State values that don't belong to their Country.

### Record Type Picklist Value Mapping Drift

Each record type on an object defines which picklist values are available for each picklist field. These mappings are stored in `RecordType` metadata and deployed via Metadata API, change sets, or SFDX.

**How drift happens:**

1. **Deployment gaps:** A developer adds a new picklist value to the field but forgets to add it to the appropriate record type mappings. The value exists but is invisible to users of that record type.
2. **Sandbox refresh timing:** A record type mapping is updated in production but the sandbox was refreshed before the change. Development continues against stale mappings.
3. **Manual Setup edits:** An admin adds a value to one record type but forgets others. There is no built-in alert or audit trail for record type picklist mapping changes.
4. **Global Value Set updates:** Adding a value to a GVS makes it available on the field, but it is NOT automatically added to any record type mapping. Admins must manually add it to each record type that should see it.

**Detection is hard:** The platform does not surface "this value exists on the field but is not mapped to any record type" as a warning. The only way to find drift is to compare the field's value set against each record type's mapping — either manually in Setup or programmatically via the Metadata API or UI API.

---

## Common Patterns

### Pattern 1: Audit and Restrict an Unrestricted Picklist

**When to use:** An unrestricted picklist has accumulated invalid values from API writes or imports and you need to clean it up and prevent future violations.

**How it works:**

1. Query all distinct values currently in the field:
   ```sql
   SELECT Status__c, COUNT(Id) FROM Case GROUP BY Status__c
   ```
2. Compare the query results against the defined picklist values (via Setup or Metadata API retrieve of the `CustomField`)
3. For each invalid value, decide: replace with a valid value, or set to null
4. Use Data Loader or an Apex batch to update records carrying invalid values
5. Toggle the field to **Restricted** in Setup (Object Manager > Field > Edit > check "Restrict picklist to the values defined in the value set")
6. Test that API writes of invalid values now fail with `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`

**Why not skip the audit:** Toggling to restricted without cleaning data first leaves orphaned values on existing records. Reports still show the garbage. `ISPICKVAL()` checks in formulas and validation rules may not handle the unexpected values correctly.

### Pattern 2: Enforce Dependent Picklist Rules at the Data Layer

**When to use:** Dependent picklist relationships must hold even for records created via API or integration.

**How it works:**

1. Document the controlling-dependent value matrix (Setup > Object Manager > [Dependent Field] > Field Dependencies)
2. Build a validation rule or before-insert/before-update Apex trigger that enforces the mapping:

   ```apex
   // Validation rule approach (for simple mappings)
   // Error condition: Country is "United States" but State is not a valid US state
   AND(
     ISPICKVAL(Country__c, "United States"),
     NOT(
       OR(
         ISPICKVAL(State__c, "California"),
         ISPICKVAL(State__c, "New York"),
         ISPICKVAL(State__c, "Texas")
       )
     )
   )
   ```

3. For complex matrices, use a Custom Metadata Type to store the valid combinations and an Apex trigger to validate against it
4. Test via API to confirm invalid combinations are now rejected

**Why not the alternative:** Relying on the UI-only enforcement is invisible — you will not know records are being created with invalid combinations until a report or downstream process breaks.

### Pattern 3: Detect and Fix Record Type Picklist Value Mapping Drift

**When to use:** After a deployment, sandbox refresh, or manual edit, you suspect record type picklist mappings are out of sync with the intended configuration.

**How it works:**

1. Retrieve the `RecordType` metadata for the object via Metadata API or SFDX:
   ```bash
   sf project retrieve start --metadata RecordType:Account.Enterprise
   ```
2. In the retrieved XML, examine the `<picklistValues>` blocks. Each block lists which values are active for that record type on that field.
3. Compare against the field's full value set (from the `CustomField` metadata or `GlobalValueSet` metadata)
4. Identify values that are:
   - On the field but not mapped to any record type (invisible to all users)
   - Mapped to a record type but inactive on the field (silently ignored)
   - Mapped inconsistently across record types (unintentional)
5. Fix by updating the record type metadata and redeploying, or manually via Setup > Record Types > Picklists Available for Editing

**Why not manual-only:** With 5+ record types and 20+ picklist fields, manual comparison in Setup is error-prone and does not scale. A scripted approach catches drift that humans miss.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Unrestricted picklist with known API consumers | Audit existing data, then toggle to restricted | Prevents future garbage; one-time cleanup for historical data |
| Unrestricted picklist but cannot break existing integrations | Add validation rule instead of restricting | Validation rules return actionable errors; restriction returns a generic error code |
| Dependent picklist with API/integration writes | Add validation rule or Apex trigger to enforce mapping | UI-only enforcement leaves a data quality gap for all non-UI channels |
| Simple dependent mapping (< 20 combinations) | Validation rule with ISPICKVAL | No code; declarative; easy to maintain |
| Complex dependent mapping (50+ combinations) | Custom Metadata Type + Apex trigger | Scales without hardcoding; deployable across environments |
| Record type picklist drift suspected | Script a metadata retrieve and compare | Manual Setup audit does not scale beyond a few record types |
| New value added to Global Value Set | Manually add to each record type that needs it | GVS value additions are NOT auto-mapped to record types |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Identify the integrity issue category** — Determine whether the problem is unrestricted picklist pollution, dependent picklist bypass, record type mapping drift, or a combination. Query the field to see what values actually exist in data versus what the value set defines.
2. **Gather field metadata** — Retrieve the `CustomField` or `GlobalValueSet` definition to confirm restricted/unrestricted status, the active value set, and any dependent picklist configuration. Check how many record types exist and whether they have divergent picklist mappings.
3. **Audit current data** — Run a `GROUP BY` SOQL query on the affected field to identify all distinct values and their record counts. Flag any value that does not appear in the active value set as an orphan.
4. **Design the remediation** — For orphaned values: decide replace or null. For dependent picklist bypass: draft a validation rule or Apex trigger. For record type drift: prepare updated metadata. Use the templates in this skill package.
5. **Implement and test** — Apply the fix in a sandbox. Test that invalid API writes are now rejected. Confirm that valid UI and API operations still succeed. Verify record type mappings are consistent.
6. **Clean historical data** — Run Data Loader or Apex batch updates to fix existing records that carry invalid values. Verify with a re-run of the audit query.
7. **Document and monitor** — Record what was fixed and why. Set up a scheduled report or dashboard to surface any new orphaned values (a canary for regression).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed whether each affected picklist is restricted or unrestricted
- [ ] Queried actual field values and compared against the defined value set
- [ ] Orphaned/invalid values identified with record counts
- [ ] Data cleanup plan documented (replace vs null for each invalid value)
- [ ] For dependent picklist issues: validation rule or trigger deployed and tested via API
- [ ] For record type drift: all record type mappings reviewed and corrected
- [ ] Restricted flag toggled where appropriate (after data cleanup)
- [ ] Downstream impacts checked: validation rules, flows, formulas, reports, dashboards
- [ ] Monitoring mechanism in place (scheduled report or periodic audit query)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Toggling to restricted does not clean existing data** — When you check "Restrict picklist to the values defined in the value set," Salesforce only enforces the restriction on future writes. All existing records keep their current values, even if those values are not in the defined value set. You must clean historical data separately.

2. **Global Value Set values are not auto-added to record type mappings** — Adding a new value to a Global Value Set makes it available on the field definition, but it does NOT automatically appear in any record type's picklist mapping. Admins must manually add the value to each record type. This is the most common source of "I added the value but users can't see it" tickets.

3. **Dependent picklist with no mapped values shows ALL values** — If a controlling value has zero dependent values mapped in the dependency matrix, the dependent picklist shows the entire value set — not an empty list. This is the opposite of what admins expect and silently undermines the filtering intent.

4. **API-created records bypass dependent picklist validation silently** — Records created via API, Data Loader, or Bulk API with invalid controlling-dependent combinations save without any error or warning. There is no after-the-fact flag on the record indicating it violated the dependency. The only way to detect this is to query and cross-check.

5. **Inactive values on restricted picklists still exist on records** — Deactivating a value on a restricted picklist prevents future selection but does not remove it from existing records. If you then query for that value, records still appear. If you try to update such a record without changing the picklist value, the save succeeds (the platform does not re-validate unchanged fields). But if you try to set the field to the same inactive value on a new record, it fails.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Picklist Integrity Audit Report | List of all orphaned/invalid values per field with record counts and recommended action |
| Remediation Plan | Step-by-step cleanup instructions: data updates, restriction toggles, validation rules, and record type mapping fixes |
| Dependent Picklist Enforcement Template | Validation rule or Apex trigger template that enforces the controlling-dependent mapping at the data layer |

---

## Related Skills

- `picklist-and-value-sets` — use for initial picklist design, Global Value Set creation, and standard value management; this skill picks up where that one ends when data quality has degraded
- `record-types-and-page-layouts` — use for record type configuration; this skill covers the specific problem of record type picklist value mapping drift
- `large-scale-deduplication` — use when picklist integrity issues are part of a broader data quality remediation effort
