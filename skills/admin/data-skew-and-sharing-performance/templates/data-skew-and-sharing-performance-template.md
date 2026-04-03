# Data Skew and Sharing Performance — Work Template

Use this template when diagnosing and mitigating data skew in a Salesforce org.

## Scope

**Skill:** `data-skew-and-sharing-performance`

**Request summary:** (fill in: what symptom was reported — slow sharing recalculation / lock errors / specific object)

---

## Context Gathered

Answer these before proposing any changes:

- **Suspected objects:** (list object API names)
- **OWD for each object:** Private / Public Read Only / Public Read/Write / Controlled by Parent
- **Role hierarchy in use?** Yes / No
- **Top owners by record count:** (paste report results: Owner Name — Record Count)
- **Top parents by child count:** (paste report results: Parent Account — Child Count)
- **Active sharing rules sourced from roles or public groups?** (Yes/No — list rule names if yes)
- **Error messages observed:** (e.g., "Group membership operation already in progress")

---

## Diagnosis

### Ownership Skew Check

| User / Queue | Object | Record Count | Skewed? (>10k) |
|---|---|---|---|
| (fill in) | (fill in) | (fill in) | Yes / No |

### Parent-Child Skew Check

| Parent Record | Child Object | Child Count | Skewed? (>10k) |
|---|---|---|---|
| (fill in) | (fill in) | (fill in) | Yes / No |

---

## Recommended Approach

Select the applicable pattern from SKILL.md:

- [ ] **Pattern 1 — Distribute Ownership:** Remove skewed users from the role hierarchy, or distribute records across multiple queues/users.
- [ ] **Pattern 2 — Break Up Skewed Parent Accounts:** Re-parent children across multiple segmented parent accounts. Evaluate "Controlled by Parent" OWD.
- [ ] **Pattern 3 — Sequence Maintenance Operations:** Schedule role/group changes in non-overlapping windows. Add retry logic to integrations.

**Rationale:** (explain which pattern applies and why)

---

## Mitigation Plan

| Action | Target Object / Record | Owner / Responsible Party | Completion Criteria |
|---|---|---|---|
| (e.g., Redistribute Lead ownership from Marketing Import User) | Lead | Admin / Integration Team | No single owner has >10,000 Leads |
| (e.g., Re-parent Contacts from Unassigned Contacts account) | Contact | Data Team | No single Account has >10,000 Contacts |
| (e.g., Add retry logic to provisioning integration) | Integration Code | Dev Team | Provisioning retries on lock error |

---

## Checklist

- [ ] No single user or queue owns more than 10,000 records of any single object.
- [ ] No single Account (or other parent) has more than 10,000 child records in any child object.
- [ ] "Parking lot" users that must hold large record counts are placed outside the role hierarchy or at the top and never moved.
- [ ] Child objects where sharing can follow the parent are configured as "Controlled by Parent" OWD.
- [ ] Integration processes that update role/group structure include retry logic for lock errors.
- [ ] Bulk reassignment operations are batched in off-peak windows.
- [ ] Sharing recalculation background jobs are monitored after any large role or ownership change.

---

## Notes

(Record any deviations from the standard pattern and why — e.g., business constraint preventing ownership redistribution, reason "Controlled by Parent" was not applicable)
