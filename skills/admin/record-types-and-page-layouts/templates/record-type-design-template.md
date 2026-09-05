# Record Type Design Template

Complete this before creating Record Types. The template forces the design decisions that prevent RT proliferation and picklist wipe incidents.

---

## Context

| Property | Value |
|----------|-------|
| **Object** | _(e.g. Opportunity)_ |
| **Business process / Project** | _(fill in)_ |
| **Author** | _(fill in)_ |
| **Date** | _(YYYY-MM-DD)_ |
| **Lightning Experience enabled?** | ☐ Yes / ☐ No |
| **Dynamic Forms considered?** | ☐ Yes — concluded not suitable because: _(reason)_ / ☐ No — Classic org |

---

## Decision: Do You Need a Record Type?

Answer each question:

| Question | Answer |
|----------|--------|
| Do different user groups need DIFFERENT PICKLIST VALUES? | ☐ Yes → RT likely needed / ☐ No |
| Do different user groups need DIFFERENT PAGE LAYOUTS? | ☐ Yes → RT or Dynamic Forms / ☐ No |
| Is the only difference which FIELDS ARE VISIBLE? | ☐ Yes → Use Dynamic Forms, not RT / ☐ No |
| Is the only difference DEFAULT FIELD VALUES? | ☐ Yes → Use a Flow, not RT / ☐ No |
| Is the only difference REQUIRED FIELDS? | ☐ Yes → Use a scoped Validation Rule, not RT / ☐ No |
| Total RT count on this object AFTER this addition | _(count)_ — if >8, stop and redesign |

**Decision:** ☐ Create Record Type(s) / ☐ Use alternative _(specify)_

---

## Record Type Matrix

One row per Record Type. Keep the number to the minimum needed.

| Property | RT 1 | RT 2 | RT 3 |
|----------|------|------|------|
| **Label** | _(fill in)_ | | |
| **Developer Name** | _(API name; letter first, no spaces, no trailing or doubled underscore)_ | | |
| **Description** | _(business purpose; max 255 chars, and readable by every user with object access — no sensitive detail)_ | | |
| **Business Process** | _(required on Lead, Opportunity, Solution, Case; must be blank on every other object)_ | | |
| **Page Layout** | _(layout name)_ | | |
| **Assigned Profiles/PSGs** | _(profile owns the default and the layout; permission set can only add visibility)_ | | |
| **Assigned personas** | _(e.g. Sales AEs)_ | | |
| **Approximate user count** | _(count)_ | | |

---

## Picklist Value Mapping

For each picklist field that differs by Record Type, document the available values:

### Field: [Picklist Field Name]

| Value | RT 1 | RT 2 | RT 3 |
|-------|:----:|:----:|:----:|
| _(e.g. Prospecting)_ | ✅ | ❌ | ✅ |
| _(value)_ | | | |

*(Repeat for each differentiating picklist field)*

---

## Validation Rules Scoped per Record Type

| Rule Name | Scoped to RT | Formula Condition |
|-----------|-------------|------------------|
| _(rule name)_ | _(RT Developer Name)_ | `RecordType.DeveloperName = "<RT_Developer_Name>"` |

---

## Flow Entry Criteria per Record Type

| Flow | Entry Criteria | RT Scope |
|------|---------------|---------|
| _(flow name)_ | _(entry criteria)_ | `{!$Record.RecordType.DeveloperName} = "<RT_Developer_Name>"` |

---

## Migration Plan (if changing existing model)

| Phase | Action | Records Affected | RT Change | Picklist Risk | Sandbox Tested |
|-------|--------|-----------------|-----------|--------------|---------------|
| 1 | Audit records with at-risk picklist values | _(count)_ | _(from)_ → _(to)_ | ⚠️ Check: _(values absent on the target RT)_ | ☐ |
| 2 | Update picklist values to target RT values | _(count)_ | — | — | ☐ |
| 3 | Reassign Record Types | _(count)_ | _(from)_ → _(to)_ | Low (values already migrated) | ☐ |
| 4 | Update Profile/PSG RT assignments | — | — | — | ☐ |
| 5 | Decommission old RTs (if applicable) | — | — | — | ☐ |

**Rollback plan:** If RT reassignment causes data issues, revert via mass update back to original RT. Document the original RT assignment before making changes.

---

## Testing Protocol

| Test Scenario | Expected Result | Tested By | Date |
|--------------|----------------|-----------|------|
| Create record as Persona A user — correct RT available | ✅ RT 1 appears in selection | _(tester)_ | |
| Create record as Persona A user — wrong RT not available | ✅ RT 2 NOT shown | _(tester)_ | |
| Save record — correct picklist values shown | ✅ Only RT-appropriate values visible | _(tester)_ | |
| Change Record Type — verify picklist impact | ✅ No unexpected field wipes | _(tester)_ | |
| API call creating record without RT specified | ✅ Default RT applied correctly | _(tester)_ | |

---

## Deployment Artefacts

Every row must exist in source before the change is deployable. Shapes are in `references/metadata-examples.md`.

| Artefact | File | Present |
|---|---|---|
| Record types | `objects/<Object>` — `recordTypes` block, or `objects/<Object>/recordTypes/<Name>.recordType-meta.xml` | ☐ |
| Business process (Lead / Opportunity / Solution / Case only) | same object file — `businessProcesses` block | ☐ |
| Page layouts | `layouts/<Object>-<Layout Name>.layout-meta.xml` | ☐ |
| Record type visibility | `profiles/*.profile-meta.xml` and/or `permissionsets/*.permissionset-meta.xml` — `recordTypeVisibilities` | ☐ |
| Default record type | `profiles/*.profile-meta.xml` only — `<default>true</default>`; permission sets cannot set it | ☐ |
| Layout assignment | `profiles/*.profile-meta.xml` only — `layoutAssignments`; permission sets have no such element | ☐ |
| Manifest naming every record type explicitly (`RecordType` rejects `*`) | `manifest/*.xml` | ☐ |
| Checker clean | `python3 scripts/check_record_type_layouts.py --manifest-dir <dir>` | ☐ |

---

## Approval

| Role | Name | Approved | Date |
|------|------|----------|------|
| Salesforce Admin | _(name)_ | ☐ | |
| Business Owner | _(name)_ | ☐ | |
| Data/Integration Team (if RT affects integrations) | _(name)_ | ☐ | |
