---
name: cpq-architecture-patterns
description: "CPQ solution architecture covering bundle design, pricing engine performance, multi-currency strategy, and integration patterns. Trigger keywords: CPQ architecture, quote scalability, bundle design, QCP performance, CPQ integration, large quote, pricing waterfall, ServiceRouter. NOT for individual feature design such as configuring specific Price Rules or Discount Schedules — see cpq-pricing-rules or pricing-model-design instead."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Scalability
tags:
  - cpq
  - cpq-architecture
  - quote-scalability
  - bundle-design
  - pricing-engine
  - multi-currency
  - integration
  - qcp
inputs:
  - Number of expected quote line items per quote
  - Product catalog complexity (flat vs. nested bundles)
  - Multi-currency requirements and exchange rate handling expectations
  - External system integration requirements (ERP, billing, subscription management)
  - Quote Calculator Plugin (QCP) complexity and JavaScript size estimates
  - Expected concurrent quote generation volume
outputs:
  - CPQ solution architecture decision record
  - Bundle design pattern recommendation (flat vs. nested)
  - QCP code architecture plan (inline vs. static resource)
  - Multi-currency handling approach and trade-off notes
  - Integration strategy recommendation (ServiceRouter vs. other)
  - Large Quote Mode enablement guidance
triggers:
  - "How should I architect CPQ for a large product catalog with many quote line items?"
  - "CPQ quote save is timing out or failing when we add more than 200 line items"
  - "Should I use nested bundles or flat bundles for our product configuration in CPQ?"
  - "How do I integrate an external ERP system with Salesforce CPQ without bypassing pricing?"
  - "Our Quote Calculator Plugin is getting too large — how do we manage the code size limit?"
  - "CPQ multi-currency — how does exchange rate handling work and what are the limitations?"
  - "When should we enable Large Quote Mode and what does it change for sales reps?"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# CPQ Architecture Patterns

This skill activates when designing the overall architecture of a Salesforce CPQ implementation — covering bundle structure, pricing engine behavior and limits, multi-currency handling strategy, QCP plugin design, and external system integration. Use it before configuration begins to establish the constraints and patterns that will govern the entire CPQ build.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm CPQ package version installed (SBQQ managed package) — behavior differs between major versions.
- Determine expected maximum quote line items per quote. The Quote Line Editor (QLE) cannot reliably save quotes beyond 200–300 line items; this is a hard architectural limit that drives bundling, Large Quote Mode, and integration decisions.
- Determine whether multi-currency is enabled in the org and whether dated exchange rates are required — CPQ does not natively support dated exchange rates.
- Identify all external systems that will read or write quote, product, or order data — external DML on SBQQ objects bypasses the pricing engine entirely.
- Clarify whether Quote Calculator Plugin customization is needed and how complex it will be — the SBQQ__Code__c field is capped at 131,072 characters.

---

## Core Concepts

### The Fixed Pricing Waterfall

CPQ calculates prices in a strict, non-configurable sequence defined by Salesforce:

1. **List Price** — base price from the pricebook
2. **Contracted Price** — overrides list price for a specific account if a contracted price record exists
3. **Block Price** — overrides all prior prices if block pricing is configured for the product
4. **Discount Schedules** — volume or term-based discounts applied after block pricing
5. **Price Rules** — declarative or formula-driven price adjustments
6. **Net Price** — final calculated price visible on the quote line

This sequence is fixed. Architects cannot reorder stages. Any customization that attempts to modify a price "before" a later stage has already run will produce incorrect results. Price Rules, despite their power, always run after Discount Schedules — architects who design multi-stage discount logic must account for this ordering.

### Quote Line Editor (QLE) Line Item Limits

The QLE is a Lightning component that renders all quote lines in the browser and performs synchronous calculations. At 200–300 line items, quote save operations become unreliable due to Apex CPU time limits, governor limits on SOQL/DML, and browser payload size. This is not a configurable limit — it is a consequence of how the QLE executes the pricing engine synchronously.

Architectural responses to this constraint:

- **Bundle consolidation**: Reduce visible line items by grouping features into bundle components with `SBQQ__Hidden__c = true` on sub-components.
- **Large Quote Mode**: Salesforce CPQ supports an asynchronous calculation mode that moves pricing to a server-side batch job. This changes the UX significantly — users do not see real-time price feedback — and must be explicitly communicated to stakeholders before enabling.
- **External quote generation**: For very high line count use cases (500+), quotes may be assembled and priced via API using ServiceRouter rather than through the QLE.

### Quote Calculator Plugin (QCP) Architecture

The QCP is a JavaScript escape hatch that allows custom pricing logic to run inside the CPQ pricing engine. It is stored in the `SBQQ__Code__c` field on the `SBQQ__CustomScript__c` object. That field has a hard cap of **131,072 characters**. For any non-trivial plugin:

- Store the full JavaScript in a **Static Resource**.
- In `SBQQ__Code__c`, write a minimal loader that calls `fetch()` against the Static Resource URL and `eval()`s the response.
- This pattern preserves the field limit while allowing arbitrarily large and maintainable plugin code.
- Static Resource approach also enables version-controlled deployments via metadata API.

QCP functions run asynchronously; all pricing callbacks must return Promises. Blocking patterns or synchronous-style code will cause silent failures.

### Multi-Currency Storage and Limitations

When multi-currency is enabled in a CPQ org, all CPQ price fields (list price, unit price, net price) are stored in the **org's corporate currency**. Currency conversion to the quote's transaction currency happens at display time using the static exchange rate configured in the org.

CPQ does **not** natively support dated exchange rates. If a customer requires that prices use the exchange rate in effect at a specific date (e.g., contract signature date), there is no out-of-box mechanism. Documented workarounds include:

- Creating separate pricebooks per currency with hard-coded converted prices — eliminates dynamic conversion entirely.
- Custom Apex that recalculates prices at quote activation using a custom exchange rate table.

Architects must surface this limitation explicitly when multi-currency and financial accuracy requirements coexist.

---

## Common Patterns

### Pattern: Flat Bundle vs. Nested Bundle Design

**When to use flat bundles:** Single-level product groupings where all components belong to the same parent, no sub-grouping required, and QLE performance is a concern. Flat bundles (1 parent, N components with `SBQQ__FeatureName__c` grouping) are simpler to maintain, easier to price, and have lower QLE rendering cost.

**When to use nested bundles:** When the product genuinely has distinct tiers — e.g., a base platform product with sub-bundle hardware options and a separate sub-bundle for software licenses. Nested bundles increase quote line count and QLE complexity. Each additional nesting level multiplies the SOQL calls during calculation.

**Constraint:** Deeply nested bundles (3+ levels) frequently cause pricing engine timeouts. Prefer flat bundles with Option Constraints to simulate grouping behavior without additional nesting.

**Option Constraints** (`SBQQ__OptionConstraint__c`) enforce conditional logic between product options — use them instead of nested bundles when the goal is conditional inclusion rather than genuine product hierarchy.

### Pattern: Static Resource QCP for Complex Plugins

**When to use:** Whenever QCP JavaScript exceeds approximately 80,000 characters (safe margin below 131,072), or when the plugin requires unit-testable modular code.

**How it works:**
1. Write the full plugin JavaScript in a Static Resource (e.g., `CPQCalculatorPlugin`).
2. In `SBQQ__Code__c`, deploy a loader:

```javascript
(function() {
  var resourceUrl = '/resource/CPQCalculatorPlugin';
  var xhr = new XMLHttpRequest();
  xhr.open('GET', resourceUrl, false); // synchronous load at init time
  xhr.send(null);
  if (xhr.status === 200) {
    eval(xhr.responseText);
  }
})();
```

3. The actual plugin callbacks (`onBeforeCalculate`, `onPriceRules`, etc.) are defined in the Static Resource.
4. Deploy via `StaticResource` metadata type — no manual copy-paste into the org field.

**Why not inline:** Field character limit will silently truncate code, causing the plugin to fail with cryptic errors. The truncation point is not surfaced in validation.

### Pattern: External System Integration via ServiceRouter

**When to use:** Any time an external system (ERP, billing platform, subscription management) needs to create, update, or read CPQ quotes, products, or calculate pricing.

**How it works:** Salesforce CPQ exposes a REST API at `/services/apexrest/SBQQ/ServiceRouter`. External systems call this endpoint with a JSON payload specifying the `reader` or `saver` class (e.g., `SBQQ.QuoteService.read` / `SBQQ.QuoteService.save`).

**Why not direct DML:** Writing directly to `SBQQ__Quote__c`, `SBQQ__QuoteLine__c`, or related objects via REST/SOAP API or integration user DML completely bypasses the pricing engine. Prices will not be recalculated, required fields may not be populated by triggers, and the quote will be in a corrupt state. This is the single most common architectural mistake in CPQ integrations.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Quote expected to exceed 200 line items | Enable Large Quote Mode; communicate async UX to stakeholders | QLE synchronous calculation limit; save operations become unreliable above 200-300 lines |
| QCP logic exceeds ~80K characters | Store in Static Resource, use loader pattern in SBQQ__Code__c | Field hard cap of 131,072 chars; truncation causes silent failures |
| External ERP needs to create/update quotes | Use ServiceRouter REST API exclusively | Direct DML bypasses pricing engine; results in corrupt quote data |
| Multi-currency with dated exchange rates required | Custom pricebook-per-currency or custom Apex rate table; escalate as gap | CPQ does not natively support dated exchange rates |
| Product hierarchy with 3+ nesting levels | Flatten to 2 levels + Option Constraints | Deep nesting multiplies SOQL per calculation; frequent timeout risk |
| Bundle with conditional component selection | Use Option Constraints on flat bundle | Simpler, fewer lines, less QLE load than nested sub-bundles |
| Large Quote Mode adoption | Pilot with internal users first; set SBQQ__LargeQuote__c = true on Account | UX change is significant — no real-time price feedback; requires user training |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on CPQ architecture:

1. **Gather constraints**: Collect maximum quote line count, multi-currency requirements, external system integration requirements, and estimated QCP complexity. These four inputs drive the most consequential architectural decisions.

2. **Assess QLE line limit risk**: If any quote scenario may produce more than 150 line items, plan for Large Quote Mode from day one. Design bundle structures to minimize visible line count — set sub-components to hidden where users do not need to interact with them.

3. **Design bundle structure**: Choose flat vs. nested bundle strategy. Document the maximum nesting depth. Default to flat with Option Constraints unless the product model requires genuine hierarchy. Validate the design against QLE rendering cost before configuration begins.

4. **Plan QCP architecture**: Determine whether a QCP is needed. If yes, estimate JavaScript size. If likely to exceed 80,000 characters, plan the Static Resource loader pattern from the start — retrofitting this pattern after QCP is live requires a deployment freeze.

5. **Define multi-currency strategy**: If multi-currency is enabled, document whether dated exchange rates are a business requirement. If yes, design the workaround (pricebook-per-currency or custom Apex rate table) and surface it as a scope item — this is not a configuration-only solution.

6. **Define integration touchpoints**: For each external system, identify whether it reads or writes CPQ data. Mandate ServiceRouter for all write operations. Provide the external system team with the ServiceRouter API documentation and confirm they will not use direct DML.

7. **Validate and review**: Run `scripts/check_cpq_architecture.py` against the metadata directory. Review checklist items. Confirm Large Quote Mode decision is documented and communicated to project stakeholders if applicable.

---

## Review Checklist

Run through these before marking CPQ architecture work complete:

- [ ] Maximum quote line count scenario documented; Large Quote Mode decision made and communicated
- [ ] Bundle nesting depth confirmed at 2 levels or fewer, or documented exception with mitigation
- [ ] QCP JavaScript size estimated; Static Resource pattern adopted if >80K characters
- [ ] Multi-currency dated exchange rate requirement surfaced and resolution documented
- [ ] All external integration touchpoints confirmed to use ServiceRouter — no direct DML paths
- [ ] Pricing waterfall stage ordering reviewed against all pricing requirements (List → Contracted → Block → Discount Schedules → Price Rules → Net)
- [ ] Large Quote Mode UX impact communicated to stakeholders if enabled

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **QCP field truncation is silent** — If `SBQQ__Code__c` content exceeds 131,072 characters, Salesforce truncates it without error. The plugin appears to save successfully but executes truncated/broken JavaScript. The failure manifests as incorrect pricing or no pricing, with no clear error message pointing to truncation.

2. **Direct DML on SBQQ objects corrupts quotes** — Writing to CPQ objects via external API (REST, SOAP, integration user) bypasses all CPQ triggers and the pricing engine. Quote lines will show stale or zero prices, required calculated fields will be empty, and the quote cannot be reliably activated. There is no automated warning when this happens.

3. **Discount Schedules always run before Price Rules** — The waterfall sequence is fixed. A Price Rule that sets a price field will run after Discount Schedules have already applied. Architects who expect Price Rules to set a "base" price before volume discounts apply will get incorrect results. Design Price Rules to adjust net price, not reset it.

4. **Large Quote Mode disables real-time pricing feedback** — When `SBQQ__LargeQuote__c` is set on an Account or enabled globally, the QLE no longer recalculates prices as users edit lines. Users must trigger calculation manually. This is a significant UX regression that must be communicated and trained on before go-live.

5. **Multi-currency exchange rate is static at display time** — CPQ converts corporate-currency prices to transaction currency using the org's current exchange rate. If the org exchange rate changes after a quote is created, the displayed price changes retroactively. There is no snapshot of the rate at quote creation time unless custom code captures it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| CPQ Architecture Decision Record | Documents bundle strategy, QLE line limit decisions, QCP architecture, multi-currency approach, and integration patterns |
| Bundle Design Diagram | Visual showing parent/component/option structure, nesting depth, and hidden component strategy |
| QCP Code Architecture Plan | Specifies inline vs. Static Resource approach, loader pattern if applicable, and deployment strategy |
| Integration Pattern Specification | Lists all external system touchpoints and confirms ServiceRouter usage for write operations |
| Large Quote Mode Enablement Plan | Stakeholder communication plan, pilot scope, and SBQQ__LargeQuote__c field configuration approach |

---

## Related Skills

- `pricing-model-design` — Use to design the specific pricing method, discount schedule, and block pricing configuration after the CPQ architecture is established
- `cpq-pricing-rules` — Use to implement individual Price Rule objects, Price Conditions, and Price Actions within the architecture defined here
- `cpq-product-catalog-setup` — Use to configure product bundles and Product Options after the bundle design pattern is decided
- `multi-currency-sales-architecture` — Use alongside this skill when the org-wide multi-currency architecture involves CPQ; covers broader currency enablement decisions
- `integration-framework-design` — Use for the broader integration architecture when CPQ ServiceRouter is one of multiple integration touchpoints
