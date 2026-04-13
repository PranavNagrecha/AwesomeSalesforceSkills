# Analytics Security Architecture — Work Template

Use this template when designing or auditing row-level security and dataset access controls in CRM Analytics.

## Scope

**Skill:** `analytics-security-architecture`

**Request summary:** (fill in what the user asked for — e.g., "Design row-level security for the Sales Pipeline Analytics app so reps see only their own opportunities and managers see their team's opportunities")

---

## Context Gathered

Before working, record answers to the Before Starting questions from SKILL.md:

- **Datasets in scope and their sources:**
  - Dataset name: _______________, Source object: _______________, Connector: _______________
  - Dataset name: _______________, Source object: _______________, Connector: _______________
- **Access model for each dataset:**
  - [ ] Owner-based (`OwnerId` equals running user)
  - [ ] Role-hierarchy-based (role hierarchy determines access scope)
  - [ ] Entitlement-based (custom junction object or account team / territory)
  - [ ] Other: _______________
- **Maximum row count any single user can see in the source object:** _______________
  - [ ] Confirmed under 3,000 — sharing inheritance may be viable
  - [ ] Could exceed 3,000 — sharing inheritance requires backup predicate of `'false'`; consider hand-written predicate for high-volume users
- **View All Data holders:** List any Analytics-licensed users with the View All Data permission: _______________
- **Entitlement dataset available:** [ ] Yes — dataset name: _______________ [ ] No — must be built

---

## Layer-by-Layer Security Design

### Layer 1 — App-Level Sharing

| User / Group | Role (Viewer / Editor / Manager) | Justification |
|---|---|---|
| | | |
| | | |

### Layer 2 — Dataset-Level Access

| Dataset | Users / Groups Granted Access | Access Type |
|---|---|---|
| | | |
| | | |

### Layer 3 — Row-Level Security (Predicate or Sharing Inheritance)

For each dataset, fill in one of the following:

#### Dataset: _______________

**Approach:** [ ] Security predicate   [ ] Sharing inheritance + backup predicate

**If security predicate:**

- Verified column names from Analytics Studio schema tab: _______________
- Predicate string (must be under 5,000 characters):
  ```
  '_____' == "$User._____"
  ```
- Predicate character count: _______________

**If sharing inheritance:**

- Sharing inheritance: [ ] Enabled
- Maximum rows for any user in source object: _______________
- Backup predicate: `'false'`   [ ] Confirmed set

---

## Cross-Dataset Security Design (if applicable)

Complete this section if any dataset uses entitlement-based access that requires an augment step.

**Entitlement dataset name:** _______________

**Entitlement dataset schema:**

| Column | Description |
|---|---|
| UserId | Salesforce User ID of the authorized user |
| _____________ | Joining dimension (e.g., AccountId, TerritoryId) |

**Augment step design:**

- Left dataset (main): _______________
- Right dataset (entitlement): _______________
- Join key (left): _______________ = Join key (right): _______________
- Output column embedded in main dataset: _______________

**Predicate on augmented dataset:**

```
'_______________' == "$User.Id"
```

**Entitlement dataset refresh cadence:** _______________

---

## Checklist

Work through these before marking the security design complete:

- [ ] Every dataset exposed in production dashboards has an explicit predicate or sharing inheritance configuration.
- [ ] Any dataset using sharing inheritance has a backup predicate of `'false'` set.
- [ ] All predicate column name references verified as case-exact matches against the live dataset schema (not the source object field API name).
- [ ] Predicate length confirmed under 5,000 characters for each dataset.
- [ ] Cross-dataset security uses an augment step to embed user-scoped columns — no predicate references a separate dataset.
- [ ] App-level sharing roles and dataset-level grants scoped correctly.
- [ ] View All Data holders identified, documented, and handled (license removed or permission removed, or exception approved).
- [ ] Security tested end-to-end in a sandbox with at least three user personas:
  - [ ] User who should see a narrow slice — sees correct restricted data.
  - [ ] User who should see a broader slice — sees correct broader data.
  - [ ] User who should see zero rows — dashboard shows empty (not an error).
- [ ] Entitlement dataset refresh schedule confirmed and aligned with entitlement data change cadence.

---

## Deviations from Standard Pattern

Document any intentional deviations from the patterns in SKILL.md and the reason for each:

| Deviation | Reason | Approved by |
|---|---|---|
| | | |

---

## Notes

(Record any other decisions, open questions, or follow-up items here.)
