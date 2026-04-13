# CRM Analytics Permission and Sharing — Work Template

Use this template when configuring CRM Analytics app sharing, dataset row-level security, or sharing inheritance for an org.

## Scope

**Skill:** `analytics-permission-and-sharing`

**Request summary:** (fill in what the user asked for — e.g., "restrict Opportunity dataset so reps see only their own rows")

---

## Context Gathered

Record answers to the Before Starting questions before taking any action.

- **License status:** (list which users have CRM Analytics Plus or Growth PSL assigned — check Setup > Users > PSL Assignments)
- **Target app:** (name of the Analytics app being shared)
- **Target datasets:** (list datasets that need row-level security configured)
- **Source objects:** (Salesforce objects feeding each dataset — determines eligibility for sharing inheritance)
- **Sharing inheritance eligible?** (Yes only if source object is Account, Case, Contact, Lead, or Opportunity)
- **3,000-row risk:** (identify any users who could access 3,000+ source records — these users will bypass sharing inheritance)
- **Dataset schema column names:** (copy exact column names from the dataset schema viewer for any columns referenced in predicates)

---

## Security Architecture Plan

Fill this table before configuring anything:

| Dataset | Security Method | Object (if sharing inheritance) | Predicate / Backup Predicate | Bypass for admins? |
|---|---|---|---|---|
| `<DatasetApiName>` | Predicate / Sharing Inheritance / None (documented) | `Account` / N/A | `'OwnerId' == "$User.Id"` / `'false'` | Yes — `"$User.HasViewAllData" == "true"` |
| | | | | |

---

## App Sharing Configuration

| User or Public Group | Role | Rationale |
|---|---|---|
| `<UserName or GroupName>` | Viewer / Editor / Manager | (e.g., "Sales reps — consume only") |
| | | |

---

## Dataset Security Configuration

For each dataset, record the exact configuration applied:

### Dataset: `<DatasetApiName>`

- **Security method:** Predicate / Sharing Inheritance / None (documented)
- **Predicate text:**
  ```
  <paste exact SAQL predicate here>
  ```
- **Predicate character count:** _____ / 5,000 max
- **Column names verified from schema:** [ ] Yes — list columns: `_____, _____`
- **Backup predicate (sharing inheritance only):** `'false'` / other: _____
- **Salesforce object (sharing inheritance only):** _____

---

## Validation Test Log

Record test results after applying configuration. Test must be performed as a non-admin user (not System Admin or View All Data):

| Test User | Dataset | Expected Rows | Actual Rows | Pass / Fail | Notes |
|---|---|---|---|---|---|
| `<Username>` | `<DatasetApiName>` | Only user's own records | | | |
| `<Username>` | `<DatasetApiName>` | Zero rows (backup predicate) | | | |

---

## Checklist

Work through these before marking the task complete:

- [ ] Every target user has CRM Analytics Plus or Growth PSL assigned (verified in Setup)
- [ ] App-level sharing configured with correct Viewer/Editor/Manager roles
- [ ] All sensitive datasets have a predicate or sharing inheritance configured (no unintentional all-visible datasets)
- [ ] Sharing inheritance backup predicate is explicitly set to `'false'` on all datasets using sharing inheritance
- [ ] Predicate column names verified against dataset schema (case-sensitive, copied from schema viewer — not typed from memory)
- [ ] Predicate SAQL length is under 5,000 characters for each predicate
- [ ] Row-level security tested by logging in as a non-admin user and confirming lens returns only expected rows
- [ ] Security architecture table above is complete and saved as part of org documentation

---

## Notes

Record any deviations from the standard pattern and the reason:

- (e.g., "Opportunity dataset intentionally has no predicate — dashboard shows aggregate totals only, no PII; documented in security architecture doc dated 2026-04-13")
