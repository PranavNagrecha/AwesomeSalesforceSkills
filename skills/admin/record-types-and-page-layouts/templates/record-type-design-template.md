# Record Type Design Template

Complete this before creating Record Types. The template forces the design decisions that prevent RT proliferation and picklist wipe incidents.

---

## Context

| Property | Value |
|----------|-------|
| **Object** | TODO: e.g. Opportunity |
| **Business process / Project** | TODO |
| **Author** | TODO |
| **Date** | TODO: YYYY-MM-DD |
| **Lightning Experience enabled?** | ☐ Yes / ☐ No |
| **Dynamic Forms considered?** | ☐ Yes — concluded not suitable because: TODO / ☐ No — Classic org |

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
| Total RT count on this object AFTER this addition | TODO: if >8, stop and redesign |

**Decision:** ☐ Create Record Type(s) / ☐ Use alternative (specify: TODO)

---

## Record Type Matrix

One row per Record Type. Keep the number to the minimum needed.

| Property | RT 1 | RT 2 | RT 3 |
|----------|------|------|------|
| **Label** | TODO | TODO | TODO |
| **Developer Name** | TODO | TODO | TODO |
| **Description** | TODO: Business purpose | TODO | TODO |
| **Page Layout** | TODO | TODO | TODO |
| **Assigned Profiles/PSGs** | TODO | TODO | TODO |
| **Assigned personas** | TODO: e.g. Sales AEs | TODO | TODO |
| **Approximate user count** | TODO | TODO | TODO |

---

## Picklist Value Mapping

For each picklist field that differs by Record Type, document the available values:

### Field: [Picklist Field Name]

| Value | RT 1 | RT 2 | RT 3 |
|-------|:----:|:----:|:----:|
| TODO: e.g. Prospecting | ✅ | ❌ | ✅ |
| TODO | TODO | TODO | TODO |

*(Repeat for each differentiating picklist field)*

---

## Validation Rules Scoped per Record Type

| Rule Name | Scoped to RT | Formula Condition |
|-----------|-------------|------------------|
| TODO | TODO RT Developer Name | `RecordType.DeveloperName = "TODO"` |

---

## Flow Entry Criteria per Record Type

| Flow | Entry Criteria | RT Scope |
|------|---------------|---------|
| TODO | TODO | `{!$Record.RecordType.DeveloperName} = "TODO"` |

---

## Migration Plan (if changing existing model)

| Phase | Action | Records Affected | RT Change | Picklist Risk | Sandbox Tested |
|-------|--------|-----------------|-----------|--------------|---------------|
| 1 | Audit records with at-risk picklist values | TODO | TODO → TODO | ⚠️ Check: TODO values | ☐ |
| 2 | Update picklist values to target RT values | TODO count | — | — | ☐ |
| 3 | Reassign Record Types | TODO count | TODO → TODO | Low (values already migrated) | ☐ |
| 4 | Update Profile/PSG RT assignments | — | — | — | ☐ |
| 5 | Decommission old RTs (if applicable) | — | — | — | ☐ |

**Rollback plan:** If RT reassignment causes data issues, revert via mass update back to original RT. Document the original RT assignment before making changes.

---

## Testing Protocol

| Test Scenario | Expected Result | Tested By | Date |
|--------------|----------------|-----------|------|
| Create record as Persona A user — correct RT available | ✅ RT 1 appears in selection | TODO | |
| Create record as Persona A user — wrong RT not available | ✅ RT 2 NOT shown | TODO | |
| Save record — correct picklist values shown | ✅ Only RT-appropriate values visible | TODO | |
| Change Record Type — verify picklist impact | ✅ No unexpected field wipes | TODO | |
| API call creating record without RT specified | ✅ Default RT applied correctly | TODO | |

---

## Approval

| Role | Name | Approved | Date |
|------|------|----------|------|
| Salesforce Admin | TODO | ☐ | |
| Business Owner | TODO | ☐ | |
| Data/Integration Team (if RT affects integrations) | TODO | ☐ | |
