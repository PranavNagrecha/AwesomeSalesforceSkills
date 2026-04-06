# Territory Design Requirements — Work Template

Use this template when gathering and documenting requirements for a Salesforce Enterprise Territory Management (ETM) territory model design. Complete all sections before handing off to the enterprise-territory-management skill for configuration.

---

## Scope

**Project / Request:** (describe the business context — new model, redesign, expansion)

**Go-to-Market Motion:** (Geographic | Named Account | Industry Overlay | Hybrid)

**Salesforce Edition:** (Enterprise | Performance | Unlimited — affects territory limit)

**Territory-Based Forecasting Required:** (Yes | No)

---

## Team and Account Inventory

| Metric | Value |
|---|---|
| Total active sales users requiring territory coverage | |
| Total active accounts in org | |
| Accounts with reliable BillingState/BillingCountry populated | |
| Accounts with no billing location data | |
| Named accounts to be managed separately (if applicable) | |
| Expected territory count (initial design) | |
| User-to-territory ratio (territory count divided by user count) | |

**Ratio flag:** Target is approximately 3:1. Flag if ratio is above 10:1 or below 1:1 and document remediation plan.

---

## Coverage Model Selection

**Primary coverage model type:** (Geographic | Named Account | Hybrid)

**Overlay model required:** (Yes | No — if Yes, describe below)

**Overlay description:** (e.g., Industry Overlay for Healthcare vertical across all geo territories)

**Rationale:** (why this coverage model fits the go-to-market motion)

---

## Territory Hierarchy Design

**Proposed hierarchy depth:** (number of levels — target 3-5)

**Hierarchy levels:**

| Level | Name | Example Node | Purpose / Forecast Consumer |
|---|---|---|---|
| 1 | (e.g., National) | (e.g., United States) | (e.g., VP of Sales forecast rollup) |
| 2 | (e.g., Region) | (e.g., US West) | (e.g., Regional VP forecast rollup) |
| 3 | (e.g., Rep Territory) | (e.g., California) | (e.g., Individual rep coverage) |

**Independence from role hierarchy confirmed:** (Yes | No — note any intentional alignment)

---

## Territory Types

| Territory Type Name | Priority Value | Coverage Purpose |
|---|---|---|
| (e.g., Geographic) | (e.g., 10) | (e.g., Primary geographic coverage) |
| (e.g., Named Account) | (e.g., 5) | (e.g., Strategic account overlay) |
| (e.g., Industry Overlay) | (e.g., 8) | (e.g., Healthcare vertical access) |

**Priority values:** Lower integer = higher priority for Opportunity Territory Assignment. Confirm ordering is intentional.

---

## Assignment Rule Criteria

For each leaf-level territory, document the filter criteria. Verify:
- All fields are of supported type (text, picklist, numeric, checkbox — NOT date)
- Criteria at the same hierarchy level are mutually exclusive for primary coverage
- No territory has more than 10 filter conditions

| Territory Name | Field | Operator | Value | Criteria Count |
|---|---|---|---|---|
| (e.g., US West - California) | BillingState | equals | CA | 1 |
| (e.g., US West - Pacific NW) | BillingState | in | OR; WA; AK; HI | 1 |
| ... | | | | |

**Criteria field type audit:**

- [ ] All proposed criteria fields confirmed as text, picklist, numeric, or checkbox
- [ ] No date fields used as criteria (if date-based segmentation needed, proxy field documented below)

**Date field proxy fields required:**

| Proposed Date Criterion | Proxy Field Name | Field Type | Population Method |
|---|---|---|---|
| (e.g., ContractRenewalDate__c) | (e.g., RenewalQuarter__c) | (e.g., Picklist) | (e.g., Flow on contract update) |

---

## Catch-All Territory

**Catch-all territory defined:** (Yes | No)

**Catch-all territory name:** (e.g., "Unassigned US")

**Catch-all territory level:** (which hierarchy level — typically top or regional)

**Accounts expected in catch-all:** (estimate and business intent)

---

## Named Account Handling (if applicable)

**Named account list size:** (number of accounts)

**Change frequency:** (Static | Annual | Quarterly | Monthly)

**Assignment method:**

- [ ] Rule-based (exact-match rules) — recommended for static lists only
- [ ] Custom flag field (e.g., IsNamedAccount__c checkbox) with single rule per territory
- [ ] Manual assignment — recommended for frequently-changing lists

**Named account field / mechanism:** (describe the field or process)

---

## Access and Sharing Pre-Conditions

**Account OWD setting:** (Public Read/Write | Private | Public Read Only)

**Note:** ETM access is additive. If reps must be restricted to territory accounts only, Account OWD must be Private. Document this as a pre-condition for the sharing-and-visibility skill.

**Access restriction requirement:** (Yes | No)

**If Yes — OWD change required:** (Yes | No — if Yes, raise as a separate sharing-and-visibility workstream)

---

## Territory Limit Check

**Enterprise Edition default limit:** 1,000 territories per model

**Projected territory count (full build-out):** ___

**Limit increase required:** (Yes | No)

**If Yes — Salesforce Support case raised:** (Yes | No | Pending)

---

## Open Decisions and Dependencies

| Decision | Owner | Due Date | Blocking? |
|---|---|---|---|
| (e.g., Confirm named account list) | (Sales Ops) | | Yes |
| (e.g., Confirm BillingState data quality) | (Admin) | | Yes |
| (e.g., ETM territory limit increase) | (Salesforce Support) | | Yes |

---

## Sign-Off Checklist

- [ ] Coverage model type confirmed with sales leadership
- [ ] Hierarchy depth confirmed (3-5 levels) with forecast consumers identified per level
- [ ] All assignment rule criteria fields confirmed as supported types
- [ ] Mutual exclusivity of primary coverage criteria verified
- [ ] Named account handling approach agreed
- [ ] Account OWD reviewed against access requirements
- [ ] Projected territory count is below 1,000 (or limit increase is in progress)
- [ ] User-to-territory ratio is approximately 3:1 (or deviation is documented)
- [ ] Catch-all territory is defined
- [ ] Open decisions are resolved or have owners and dates
- [ ] Requirements document is complete and ready for enterprise-territory-management configuration skill

---

## Notes and Deviations

(Record any deviations from standard patterns, unusual business requirements, or decisions that override default guidance — include the business rationale.)
