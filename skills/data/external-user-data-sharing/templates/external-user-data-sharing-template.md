# External User Data Sharing — Design Template

Use this template when designing or documenting the sharing model for external (portal / community) users.

---

## Scope

**Skill:** `external-user-data-sharing`

**Request summary:** (describe what record visibility is being configured and for which community/portal)

---

## External User Context

| Field | Value |
|---|---|
| Experience Cloud site name | |
| External user license type | Customer Community (HVP) / Customer Community Plus / Partner Community |
| Approximate external user count | |
| Objects that require external access | (list each object) |

---

## Internal vs. External OWD Audit

Complete this table for every object that external users need to access.

| Object | Internal OWD | Current External OWD | Required External OWD | Change Needed? |
|---|---|---|---|---|
| Case | | | | |
| Account | | | | |
| Contact | | | | |
| Opportunity | | | | |
| (Custom Object) | | | | |

Notes on OWD changes:
- External OWD cannot be set more permissive than internal OWD.
- Changing External OWD triggers an org-wide sharing recalculation — plan a maintenance window.

---

## Sharing Mechanism Selection

For each object requiring external access, select the mechanism based on the license type.

| Object | License Type | Mechanism | Justification |
|---|---|---|---|
| | Customer Community (HVP) | Sharing Set | Only mechanism for HVP; criteria rules ignored |
| | Customer Community Plus | Criteria-Based Sharing Rule | Full sharing model applies |
| | Partner Community | Sharing Rule / Role Hierarchy | Full sharing model + 3-tier hierarchy applies |

---

## Sharing Set Configuration (HVP Only)

Complete one block per Sharing Set needed.

**Sharing Set:** [Name]

| Profile(s) | Object | Relationship Path | Access Level |
|---|---|---|---|
| [Customer Community User] | Case | User.AccountId → Case.AccountId | Read/Write |
| [Customer Community User] | | | |

Relationship path notes:
- Verify the relationship field is populated on actual records before finalizing the path.
- SOQL to verify: `SELECT Id, AccountId FROM [Object] WHERE AccountId != null LIMIT 5`

---

## External Sharing Rule Configuration (CC Plus / Partner Community)

Complete one block per sharing rule needed.

**Rule:** [Name]

| Object | Rule Type | Criteria / Owner Group | Share With | Access Level |
|---|---|---|---|---|
| | Criteria-based | [Field] = [Value] | Customer Portal Users — [Role Group] | Read Only |
| | Owner-based | [Queue or Role] | Partner Community Users | Read/Write |

---

## Partner Community Role Hierarchy (if applicable)

| Account | Partner Executive | Partner Manager | Partner User |
|---|---|---|---|
| [Account Name] | [User Name] | [User Name] | [User Name] |

Hierarchy notes: Higher roles can see records owned by lower roles within the same account. Cross-account visibility requires explicit sharing rules.

---

## Validation Plan

- [ ] External OWD set to correct value for each object
- [ ] Sharing Set / sharing rules configured with correct relationship paths
- [ ] Background sharing recalculation job completed
- [ ] Test login: Customer Community (HVP) test user sees correct records
- [ ] Test login: Customer Community Plus test user sees correct records
- [ ] Test login: Partner Community test user sees correct records with hierarchy
- [ ] Negative test: portal users cannot see records outside their account scope

---

## Notes

Record any deviations from the standard pattern and the reason for the deviation.
