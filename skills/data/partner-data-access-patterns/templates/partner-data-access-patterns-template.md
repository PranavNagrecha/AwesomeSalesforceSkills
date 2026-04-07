# Partner Data Access Design Template

Use this template when designing or reviewing data access for partner (channel) users in a Salesforce Partner Community.

## Scope

**Skill:** `data/partner-data-access-patterns`

**Request summary:** (describe the partner data access requirement being addressed)

---

## 1. License Inventory

| User Segment | License Type | Hierarchy Available | PRM Objects Available |
|---|---|---|---|
| (e.g., Field Reps) | Partner Community / CC+ / CC | Yes (3-tier) / Yes (1-role) / No | Yes / No |
| (e.g., Regional Managers) | | | |
| (e.g., Executives) | | | |

**Key constraint identified:** (note any license/capability mismatch)

---

## 2. OWD Audit

| Object | Internal OWD | External OWD | Notes |
|---|---|---|---|
| Lead | | | |
| Opportunity | | | |
| Deal Registration | | | |
| (custom objects) | | | |

**Grant Access Using Hierarchies enabled:** Yes / No / Verify (per object if custom)

---

## 3. Partner Account — Role Hierarchy Mapping

For each partner account in scope:

| Partner Account | Account Owner | Executive-Tier Users | Manager-Tier Users | User-Tier Users |
|---|---|---|---|---|
| (Account Name) | | | | |

**Ownership stability:** Stable / At risk (note accounts with frequent ownership changes)

---

## 4. Sharing Requirements Analysis

List each data-sharing requirement and the mechanism to satisfy it:

| Requirement | Within-Account? | Cross-Account? | Mechanism | Notes |
|---|---|---|---|---|
| Manager sees rep Opportunities | Yes | No | Role hierarchy (no rule needed) | |
| Co-sell Opps visible to partner B | No | Yes | Criteria-based sharing rule | Field: Type = "Co-Sell" |
| Specific deal handoff | No | Yes | Manual share (exception) | Log entry required |

---

## 5. Sharing Rule Specifications

For each sharing rule identified above:

### Rule: (Rule Name)

- **Object:**
- **Rule type:** Criteria-based / Owner-based
- **Criteria:** (field = value)
- **Share with:** (Public Group / Role / Role and Subordinates)
- **Access level:** Read Only / Read/Write
- **Justification:** (why this rule is needed; what hierarchy cannot provide)

---

## 6. Manual Share Log

| Record Type | Record ID / Criteria | Shared With | Access Level | Reason | Granted By | Review Date |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## 7. Validation Checklist

- [ ] License type confirmed for every partner user segment
- [ ] External OWD explicitly set for all in-scope objects (not relying on defaults)
- [ ] Role hierarchy tiers mapped and verified for each active partner account
- [ ] Account ownership stability assessed; governance process in place for changes
- [ ] Sharing rules implement minimum necessary access; no open cross-account rules
- [ ] PRM objects confirmed accessible only to Partner Community licensees
- [ ] Manual shares logged with review dates
- [ ] End-to-end access validated by logging in as test user in each partner tier

---

## 8. Deviations and Notes

(Record any deviations from standard pattern, exceptions granted, and the business reason)
