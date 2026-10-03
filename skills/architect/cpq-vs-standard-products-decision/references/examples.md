# Examples — CPQ vs Standard Products Decision

## Example 1: Mid-Market SaaS Company with Simple Catalog

**Context:** A SaaS company sells 12 software products with annual subscriptions. Each product has a single list price. Reps occasionally offer 10-15% discounts that require manager approval. The team has 20 sales reps.

**Problem:** The VP of Sales is pushing for Salesforce CPQ because a competitor uses it. The CFO wants to know if the $18,000/year licensing cost is justified (20 users at the older $75/month list price; UNVERIFIED (2026-10-03): current pricing not fetched).

**Solution:**

```text
Requirements Analysis:
- Products: 12 (no bundles, no options)
- Pricing: Single list price per product, no volume tiers
- Discounting: Manual percentage, max 15%, manager approval
- Subscriptions: Annual only, no co-terming needed
- PDF Generation: Simple one-page quote

Standard Objects Coverage:
- Products + Standard Pricebook: covers catalog ✓
- Custom field "Discount_Percent__c" on QuoteLineItem: covers discounting ✓
- Validation rule enforcing max 15%: covers guardrail ✓
- Standard Approval Process on Quote: covers manager approval ✓
- Standard Quote Template: covers PDF generation ✓

Recommendation: Standard Products + Pricebooks
Savings: $54,000 over 3 years in licensing alone
```

**Why it works:** The requirements map entirely to standard object capabilities. None of the CPQ-specific features (bundles, guided selling, discount schedules, co-terming) are needed. Custom fields and an approval process close the only gaps.

---

## Example 2: Enterprise Telecom with Complex Bundles

**Context:** A telecom company sells solutions that bundle hardware (routers, switches), software licenses, installation services, and ongoing support contracts. Each bundle has required components, optional add-ons, and mutually exclusive choices (e.g., choose Router A or Router B but not both). Pricing depends on volume tiers, contract term length, and customer-specific negotiated rates. 150 sales reps create quotes.

**Problem:** The team attempted to build bundle logic using custom junction objects and Apex triggers on standard Products. After 8 months of development, the solution handles 60% of scenarios, but edge cases in mutual exclusion rules and volume tier calculations cause incorrect pricing on roughly 5% of quotes.

**Solution:**

```text
Requirements Analysis:
- Products: 300+ with parent-child bundle relationships
- Pricing: Volume tiers × contract term × customer contracted rates
- Bundles: Required, optional, and mutually exclusive components
- Guided Selling: Question-based flow to narrow bundle selection
- Subscriptions: Multi-year with co-terming and mid-term amendments
- Approvals: 3-tier chain based on discount %, deal size, and product mix

CPQ Coverage:
- Product Bundles with Option Constraints: covers inclusion/exclusion ✓
- Discount Schedules (multi-dimensional): covers volume × term pricing ✓
- Contracted Prices: covers customer-specific rates ✓
- Guided Selling: covers question-based product recommendation ✓
- Subscription/Amendment model: covers co-terming ✓
- Advanced Approvals: covers multi-tier routing ✓

Recommendation: Salesforce CPQ
Cost: $135,000/year in licensing (150 users × $75/month)
Justification: Custom solution already cost $200K+ in development and
still has 5% error rate. CPQ handles all scenarios natively.
```

**Why it works:** The complexity of bundle rules, multi-dimensional pricing, and subscription management exceeds what custom development on standard objects can reliably maintain. The 5% quote error rate in the custom solution demonstrates the risk of homegrown pricing engines.

**Read this with the 2026 lifecycle notice.** The CPQ Developer Guide (v67.0) states the package "continues to be available for existing customers" with "no longer any new feature development". The recommendation above holds as written only for a company that already holds a CPQ subscription. A net-new telecom customer should run the same requirements matrix against Revenue Cloud (`architect/revenue-cloud-architecture`) and check whether Industries EPC licences already enable `ProductRelatedComponent`. The $75 price is the older list price (UNVERIFIED (2026-10-03)).

---

## Anti-Pattern: Building a Custom CPQ on Standard Objects

**What practitioners do:** Rather than purchasing CPQ licenses, the team builds custom bundle logic using junction objects, Apex pricing calculators, and Flow-based guided selling on top of standard Products and Pricebooks. They estimate 3 months of development.

**What goes wrong:** The initial build takes 6-8 months instead of 3. Edge cases in bundle exclusion rules, volume tier boundaries, and mid-contract amendments require ongoing patches. Each pricing change request takes 2-3 sprint cycles. After 18 months, maintenance cost exceeds what CPQ licensing would have been, and the custom solution still lacks features like quote document generation and advanced approvals.

**Correct approach:** If the requirements analysis shows 3 or more CPQ-native features are needed (bundles, guided selling, discount schedules, subscriptions, advanced approvals), invest in CPQ licensing rather than custom development. Reserve custom development for orgs where the requirements genuinely stay within standard object capabilities.

---

## Example 3: Sizing Queries and a Worked Decision Record at Renewal

**Context:** A distributor has used Salesforce CPQ for three years. The subscription renews in five months. The CFO asks whether to renew or move quoting back to standard Products and Price Books.

**Step 1: measure, using standard objects plus the CPQ quote object.**

```soql
-- Q1. Catalog size in price book entries, by price book and currency
--     (CurrencyIsoCode exists only when multicurrency is enabled; drop it otherwise)
SELECT Pricebook2Id, CurrencyIsoCode, COUNT(Id) entries
FROM PricebookEntry
WHERE IsActive = true
GROUP BY Pricebook2Id, CurrencyIsoCode

-- Q2. Who actually builds quotes in CPQ (licence baseline), last 12 months
SELECT CreatedById, COUNT(Id) quotes
FROM SBQQ__Quote__c
WHERE CreatedDate = LAST_N_MONTHS:12
GROUP BY CreatedById
ORDER BY COUNT(Id) DESC

-- Q3. Who edits quotes they did not create (deal desk, sales engineering)
SELECT LastModifiedById, COUNT(Id) quotes
FROM SBQQ__Quote__c
WHERE LastModifiedDate = LAST_N_MONTHS:12
GROUP BY LastModifiedById

-- Q4. Legacy standard-quote history that reports may still read
SELECT COUNT() FROM Quote
```

Q3 undercounts editors because it sees only the last modifier per quote. Enable field history on the quote object or use event monitoring if the licence count is contested. UNVERIFIED (2026-10-03): grouping `SBQQ__Quote__c` by `CreatedById` and `LastModifiedById` assumes the standard audit fields are groupable on this managed object, which holds for standard and custom objects generally; confirm with a describe call.

**Step 2: the decision record,** at `docs/adr/0063-cpq-renewal-fy27.md` in the Salesforce delivery repository. It deploys nothing; if it chose the standard path, the build would scope `CustomObject` (Product2, Quote, QuoteLineItem field changes) and `ApprovalProcess` members in `package.xml`.

```markdown
# ADR-0063: Renew Salesforce CPQ for 12 months; freeze new price rules

## Status
Accepted (2026-10-03), Revenue Architecture Board + CFO

## Context
- Lifecycle: CPQ Developer Guide v67.0 notice, read 2026-10-03: the
  package "continues to be available for existing customers", has "no
  longer any new feature development", support "for the duration of
  your contract"; licences can be added and subscriptions renewed.
- Q1: 340 products, 6 price books, 3 currencies = 6,120 active entries.
- Q2/Q3: 58 users created quotes; 11 more edited quotes they did not
  create. Licence need: 69, not the 50 budgeted for reps.
- 140 bundles with option constraints; 22 discount schedules.
- Standard-path gap: plain Sales Cloud has no bundle object;
  ProductRelatedComponent needs Commerce, Industries, or Subscription
  Management licences, which we do not hold.
- Q4: 18,400 legacy Quote records still feed two finance reports.

## Decision
Renew CPQ for 12 months at 69 licences. Freeze new price rules except
through change control. Start a Revenue Cloud evaluation in Q2
(architect/revenue-cloud-architecture), decided by month 8.

## Consequences
### Positive
- No quoting disruption during the busiest two quarters.
### Negative
- Every unmet CPQ requirement stays unmet; there is no roadmap.
- 19 more licences than budgeted.
- If the evaluation slips past month 8, the next renewal is forced.

## Alternatives Considered
### Return to standard Products and Price Books
Rejected for now: 140 constrained bundles would become custom objects
we own; the 18,400-record history split already costs report effort.
### Renew for 36 months
Rejected: locks in a feature-frozen product past the evaluation.

## Review Trigger
Month 8 decision on Revenue Cloud. Owner: Revenue Architect.

## Date
2026-10-03
```

**Why it works:** the licence count and catalog size are measured, the lifecycle premise is quoted with its version, and the record states its own exit condition.

