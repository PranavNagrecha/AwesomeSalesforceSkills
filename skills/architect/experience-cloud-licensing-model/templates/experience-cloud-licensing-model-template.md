# Experience Cloud License Selection — Decision Framework Template

Use this template to document and justify the Experience Cloud external user license selection for a portal or community project.

---

## Project Context

**Portal name / working title:** _______________

**Target audience:**
- [ ] B2C (end customers / consumers)
- [ ] B2B (business customers, not partners)
- [ ] Channel partners (resellers, distributors, dealers)
- [ ] Mixed audience (describe below)

**Mixed audience details (if applicable):** _______________

**Estimated total external user count:** _______________

**Estimated daily active user percentage (DAU%):** ______%

---

## Gate 1 — CRM Object Access Requirements

List all Salesforce standard objects that external users must read, create, or edit:

| Object | Access Needed (R/C/E/D) | Notes |
|---|---|---|
| Case | | |
| Knowledge | | |
| Account | | |
| Contact | | |
| Lead | | |
| Opportunity | | |
| Contract | | |
| Custom Objects | | |

**Gate 1 result:**
- [ ] Leads, Opportunities, or Contracts required → **minimum tier: Partner Community**
- [ ] No Leads/Opps/Contracts required → continue to Gate 2

---

## Gate 2 — Sharing Model Requirements

Describe the record visibility requirement for external users:

**Can record access be expressed as "share with all users whose Account matches the record's Account lookup"?**
- [ ] Yes → Sharing Sets are sufficient → **Customer Community may be viable**
- [ ] No, need criteria-based conditions → **minimum tier: Customer Community Plus**
- [ ] No, need per-account manager/user hierarchy → **minimum tier: Partner Community**

**Sharing model description:** _______________

**Gate 2 result:** _______________

---

## Gate 3 — Report and Dashboard Requirements

Do any external users need to view Salesforce Reports or Dashboards?

- [ ] No → Customer Community remains viable
- [ ] Yes → **minimum tier: Customer Community Plus**

**Notes:** _______________

---

## License Tier Selection

Based on Gate 1, 2, and 3 results:

| Gate | Result | Minimum Tier Indicated |
|---|---|---|
| Gate 1 (CRM objects) | | |
| Gate 2 (Sharing model) | | |
| Gate 3 (Reports) | | |

**Selected license tier:** _______________

**Justification:** _______________

---

## Login-Based vs Member-Based Analysis

Complete this section after selecting the license tier.

| Factor | Value |
|---|---|
| Total external users | |
| Expected DAU% | |
| Estimated daily logins | users × DAU% |
| Estimated monthly login credits needed | daily logins × 30 |
| Member seat cost (per user/month at contracted rate) | |
| Login credit cost (per credit at contracted rate) | |
| Member-based total monthly cost | seats × per-user rate |
| Login-based total monthly cost | credits × per-credit rate |
| Break-even DAU% (crossover point) | |

**Recommended billing variant:**
- [ ] Member-based — reason: _______________
- [ ] Login-based — reason: _______________

**Credit exhaustion risk assessment (login-based only):** _______________

---

## Upgrade Path Risk Assessment

**Conditions that would require a license tier upgrade:**

1. _______________
2. _______________

**Estimated user count affected by a tier upgrade:** _______________

**Profile migration effort estimate:**
- [ ] Low (< 500 users, single profile)
- [ ] Medium (500–5,000 users)
- [ ] High (> 5,000 users or multiple profiles)

**Recommendation:** Start at selected tier / Start one tier higher to hedge (circle one)

**Rationale:** _______________

---

## Final Decision Summary

| Item | Decision |
|---|---|
| License tier | |
| Billing variant (member/login) | |
| Sharing mechanism | |
| Upgrade trigger conditions | |
| Architecture decision record reference | |

**Architect sign-off:** _______________ **Date:** _______________
