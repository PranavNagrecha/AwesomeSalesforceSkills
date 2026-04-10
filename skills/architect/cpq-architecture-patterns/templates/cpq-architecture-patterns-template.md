# CPQ Architecture Patterns — Work Template

Use this template when designing or reviewing the architecture of a Salesforce CPQ implementation. Complete all sections before beginning CPQ configuration or integration development.

---

## Scope

**Skill:** `cpq-architecture-patterns`

**Request summary:** (describe the CPQ implementation — industry, product catalog scale, integration context, and go-live timeline)

**Requestor / stakeholder:** 

**Date:**

---

## 1. Constraint Gathering

Answer all questions before proceeding to architecture decisions.

### Quote Line Count

- Maximum expected quote line items per quote: ___
- Typical (median) quote line count: ___
- Is this count based on final visible lines, or do hidden bundle components inflate it? ___

**Decision threshold:** If max expected lines exceed 150, plan for Large Quote Mode from the start.

### Multi-Currency

- Is multi-currency enabled in the org? Yes / No
- Does the business require dated exchange rates (rate locked at quote date)? Yes / No
- If yes: document the workaround approach selected (see Decision Guidance in SKILL.md): ___

### External Integration

List all external systems that will read or write CPQ data:

| System | Operation (Read / Write) | Objects Accessed | Integration Method |
|--------|--------------------------|------------------|--------------------|
| | | | |
| | | | |

**Requirement:** All write operations MUST use ServiceRouter. Direct DML on SBQQ objects is prohibited.

### Quote Calculator Plugin

- Is a QCP required? Yes / No
- If yes, estimated JavaScript lines of code: ___
- Estimated character count (run `wc -c` on the JS file): ___
- Is the QCP likely to exceed 80,000 characters? Yes / No / Unknown

**Decision threshold:** If yes or unknown, use Static Resource loader pattern.

---

## 2. Bundle Architecture Decision

### Bundle Strategy

Select one:
- [ ] **Flat bundle** — 1 parent, N components. All components belong to the same parent. No sub-bundles.
- [ ] **2-level nested bundle** — Parent with sub-bundle components. Justified by: ___
- [ ] **3+ level nested bundle** — REQUIRES documented exception and mitigation plan (see below)

**Exception documentation (if 3+ levels):**

Reason 3+ levels are required: ___

Mitigation for pricing engine timeout risk: ___

### Option Constraints

- Are Option Constraints (`SBQQ__OptionConstraint__c`) used to replace conditional nesting? Yes / No
- List constraint rules to be configured: ___

### Hidden Components

List bundle components that will be set to `SBQQ__Hidden__c = true`:

| Product | Bundle Parent | Reason for Hidden |
|---------|---------------|-------------------|
| | | |

---

## 3. QCP Architecture Plan

*(Complete only if QCP is required)*

### Approach

- [ ] **Inline** — Code stored directly in `SBQQ__Code__c`. Confirmed size < 80,000 characters.
- [ ] **Static Resource loader** — Minimal loader in `SBQQ__Code__c`; full code in Static Resource.

### Static Resource Details (if applicable)

- Static Resource name: ___
- Deployment method: Salesforce DX metadata / change set / other: ___
- Source control location: ___

### QCP Callbacks Required

- [ ] `onBeforeCalculate`
- [ ] `onAfterCalculate`
- [ ] `onBeforePriceRules`
- [ ] `onAfterPriceRules`
- [ ] `onInit`

### Performance Considerations

- Does QCP make async callouts? Yes / No — If yes, document the callout targets and expected latency: ___
- Does QCP access custom objects? Yes / No — If yes, document SOQL query count per calculation cycle: ___

---

## 4. Large Quote Mode Decision

- [ ] **Large Quote Mode NOT required** — Max line count confirmed below 150 visible lines.
- [ ] **Large Quote Mode required** — Confirmed via constraint gathering above.

If Large Quote Mode required:

- Enablement method: Account-level (`SBQQ__LargeQuote__c`) / Global CPQ setting
- Accounts in scope for enablement: ___
- Stakeholder communication plan: ___
- User training plan: ___

---

## 5. Pricing Waterfall Verification

Verify that the pricing requirements can be satisfied by the fixed waterfall sequence:

| Waterfall Stage | Requirement Met? | Configuration Required |
|-----------------|------------------|------------------------|
| List Price | | Pricebook entries |
| Contracted Price | | Contracted Price records per account |
| Block Price | | Block Pricing configuration per product |
| Discount Schedules | | Schedule type, tiers, application method |
| Price Rules | | Price Conditions and Price Actions |
| Net Price | | Verify expected output |

**Confirm:** No pricing requirement assumes Price Rules run before Discount Schedules. Yes / No

If No, document how the requirement will be re-architected: ___

---

## 6. Multi-Currency Architecture (if applicable)

*(Complete only if multi-currency is enabled)*

- Exchange rate handling approach:
  - [ ] Accept static conversion at display time (default CPQ behavior)
  - [ ] Pricebook-per-currency (pre-converted prices, no dynamic conversion)
  - [ ] Custom Apex snapshot at quote status transition
  - [ ] Custom rate table with QCP lookup

- Dated exchange rate requirement: Yes / No
- If Yes — workaround selected and documented: ___

---

## 7. Integration Architecture

For each external system identified in Section 1:

**System:** ___

- Write path confirmed as ServiceRouter: Yes / No
- ServiceRouter endpoint: `/services/apexrest/SBQQ/ServiceRouter`
- `saver` class used: `SBQQ.QuoteService.save` / other: ___
- Integration user CPQ permission set assigned: Yes / No / TBD

**Prohibited patterns confirmed absent:**
- [ ] No direct POST to `/services/data/vXX/sobjects/SBQQ__Quote__c`
- [ ] No direct POST to `/services/data/vXX/sobjects/SBQQ__QuoteLine__c`
- [ ] No Bulk API loads to SBQQ objects without ServiceRouter

---

## 8. Review Checklist

Complete before marking architecture design done:

- [ ] Max quote line count documented; Large Quote Mode decision made
- [ ] Bundle nesting depth confirmed at 2 levels or fewer (or exception documented)
- [ ] QCP JavaScript size estimated; Static Resource pattern adopted if >80K characters
- [ ] Multi-currency dated exchange rate requirement surfaced; resolution documented
- [ ] All external system integration touchpoints confirmed to use ServiceRouter
- [ ] Pricing waterfall stage ordering reviewed against all pricing requirements
- [ ] Large Quote Mode UX impact communicated to stakeholders if applicable
- [ ] `python3 scripts/check_cpq_architecture_patterns.py --manifest-dir <path>` run with no critical issues

---

## Notes

Record any deviations from standard patterns, unresolved decisions, or follow-up items here.
