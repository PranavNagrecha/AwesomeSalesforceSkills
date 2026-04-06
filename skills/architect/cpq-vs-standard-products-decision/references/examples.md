# Examples — CPQ vs Standard Products Decision

## Example 1: Mid-Market SaaS Company with Simple Catalog

**Context:** A SaaS company sells 12 software products with annual subscriptions. Each product has a single list price. Reps occasionally offer 10-15% discounts that require manager approval. The team has 20 sales reps.

**Problem:** The VP of Sales is pushing for Salesforce CPQ because a competitor uses it. The CFO wants to know if the $18,000/year licensing cost is justified.

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

---

## Anti-Pattern: Building a Custom CPQ on Standard Objects

**What practitioners do:** Rather than purchasing CPQ licenses, the team builds custom bundle logic using junction objects, Apex pricing calculators, and Flow-based guided selling on top of standard Products and Pricebooks. They estimate 3 months of development.

**What goes wrong:** The initial build takes 6-8 months instead of 3. Edge cases in bundle exclusion rules, volume tier boundaries, and mid-contract amendments require ongoing patches. Each pricing change request takes 2-3 sprint cycles. After 18 months, maintenance cost exceeds what CPQ licensing would have been, and the custom solution still lacks features like quote document generation and advanced approvals.

**Correct approach:** If the requirements analysis shows 3 or more CPQ-native features are needed (bundles, guided selling, discount schedules, subscriptions, advanced approvals), invest in CPQ licensing rather than custom development. Reserve custom development for orgs where the requirements genuinely stay within standard object capabilities.
