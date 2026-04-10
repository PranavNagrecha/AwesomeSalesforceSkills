# LLM Anti-Patterns — CPQ Architecture Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ architecture. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Direct DML for External CPQ Integration

**What the LLM generates:** Integration code that POSTs directly to `/services/data/vXX.0/sobjects/SBQQ__Quote__c` or `SBQQ__QuoteLine__c` to create or update CPQ records from an external system, treating CPQ objects like any other Salesforce SObject.

**Why it happens:** LLMs are trained on general Salesforce integration patterns where standard REST API DML is the correct approach. CPQ's managed-package-enforced requirement to use ServiceRouter is a CPQ-specific constraint not reflected in general Salesforce integration training data.

**Correct pattern:**

```http
POST /services/apexrest/SBQQ/ServiceRouter
Content-Type: application/json

{
  "saver": "SBQQ.QuoteService.save",
  "model": { "record": { ... }, "lineItems": [ ... ] }
}
```

**Detection hint:** Any code referencing `/services/data/vXX/sobjects/SBQQ__` for write operations is using the wrong integration path. Flag immediately.

---

## Anti-Pattern 2: Storing Full QCP JavaScript Inline Without Size Check

**What the LLM generates:** A complete Quote Calculator Plugin implementation written directly into `SBQQ__Code__c`, often with a note that "the field accepts up to the Salesforce long text area maximum."

**Why it happens:** LLMs often cite generic Salesforce field limits (e.g., 131,072 for Long Text Area) without flagging that this is a hard ceiling, not a safe working limit. They also default to the simpler inline approach because the Static Resource loader pattern requires knowledge of CPQ-specific deployment mechanics.

**Correct pattern:**

```javascript
// SBQQ__Code__c should contain ONLY the loader:
(function() {
  var req = new XMLHttpRequest();
  req.open('GET', '/resource/YourCPQPlugin', false);
  req.send(null);
  if (req.status === 200) { eval(req.responseText); }
})();

// Full plugin code lives in Static Resource: YourCPQPlugin
```

**Detection hint:** If generated QCP code is longer than ~500 lines or exceeds 80,000 characters and it is all in `SBQQ__Code__c`, the Static Resource pattern is missing.

---

## Anti-Pattern 3: Assuming Price Rules Can Run Before Discount Schedules

**What the LLM generates:** A pricing design where a Price Rule sets a "floor price" or "adjusted base price" that is intended to be the input to a Discount Schedule, assuming Price Rules can be sequenced before Discount Schedules.

**Why it happens:** LLMs reason about the CPQ pricing waterfall from general pricing system patterns where rule order is often configurable. The CPQ waterfall is fixed and non-configurable — this is a CPQ-specific constraint that contradicts general pricing system intuition.

**Correct pattern:**

```text
Fixed Waterfall (cannot be reordered):
  1. List Price
  2. Contracted Price
  3. Block Price
  4. Discount Schedules  ← always before Price Rules
  5. Price Rules         ← always after Discount Schedules
  6. Net Price

Design approach: Price Rules adjust the price AFTER Discount Schedules.
If pre-discount-schedule pricing logic is needed, capture it in a
formula field before the waterfall runs, not via a Price Rule.
```

**Detection hint:** Any design document or explanation claiming that Price Rules "run first" or can be "ordered before" Discount Schedules is incorrect. Flag and correct.

---

## Anti-Pattern 4: Recommending 3+ Level Nested Bundles for Product Hierarchy

**What the LLM generates:** A bundle architecture that mirrors the product catalog taxonomy with 3 or more nesting levels — e.g., Product Family > Product Line > Individual SKU — because this "accurately represents the product hierarchy."

**Why it happens:** LLMs optimize for modeling accuracy and often recommend data structures that match domain concepts. They are not trained on the performance impact of CPQ bundle nesting on SOQL counts and Apex CPU consumption.

**Correct pattern:**

```text
Maximum 2 nesting levels:
  Parent Product (visible in QLE)
    └─ Component Product (visible or hidden)

For visual grouping within a flat bundle, use:
  SBQQ__FeatureName__c on Product Option records
  → Groups options visually without adding a nesting level

For conditional inclusion logic, use:
  SBQQ__OptionConstraint__c records
  → Controls which options require/exclude other options
  → No performance overhead of additional nesting
```

**Detection hint:** Any bundle architecture diagram showing 3+ nesting levels should trigger a review. Ask whether the hierarchy can be flattened using Feature grouping and Option Constraints.

---

## Anti-Pattern 5: Treating Large Quote Mode as a Quote-Level Toggle

**What the LLM generates:** Instructions to "enable Large Quote Mode on quotes that exceed 200 lines" implying a per-quote setting, or code that sets a quote-level field to opt specific quotes into async calculation.

**Why it happens:** LLMs infer that a "large quote mode" would logically be a per-quote property — the name implies it. The actual implementation is primarily account-level (`SBQQ__LargeQuote__c` on Account) or globally configured via CPQ Settings, not per-quote.

**Correct pattern:**

```text
Large Quote Mode enablement options:
  1. Account-level: Set SBQQ__LargeQuote__c = true on Account record
     → All quotes for that Account use async calculation
  2. Global: Enable via CPQ Package Settings > Large Quote Threshold
     → All quotes exceeding the threshold use async calculation

There is NO native per-quote Large Quote Mode toggle.
Design implication: Large Quote Mode is an account segmentation decision,
not a quote-by-quote runtime decision.
```

**Detection hint:** Any code or design that references a quote-level Large Quote Mode field (not Account-level) is likely incorrect. Verify field exists on Account, not on `SBQQ__Quote__c`.

---

## Anti-Pattern 6: Generating Multi-Currency Architecture That Assumes Dated Exchange Rate Support

**What the LLM generates:** A multi-currency CPQ design that uses dated exchange rates (Salesforce's Advanced Currency Management feature) to ensure CPQ prices reflect the exchange rate at a specific date, without flagging that CPQ does not natively honor dated exchange rates.

**Why it happens:** Salesforce does support Advanced Currency Management with dated exchange rates for standard objects. LLMs apply this general Salesforce capability to CPQ without knowing that the CPQ managed package does not integrate with dated exchange rates.

**Correct pattern:**

```text
CPQ multi-currency reality:
  - All CPQ price fields stored in corporate currency
  - Conversion to transaction currency uses CURRENT org exchange rate
  - Advanced Currency Management dated exchange rates are NOT
    honored by the CPQ pricing engine
  
Workaround options:
  A. Pricebook-per-currency: Maintain separate pricebooks with 
     pre-converted prices. No dynamic conversion. Requires price 
     maintenance per currency change.
  B. Custom Apex snapshot: On quote status transition, capture 
     current exchange rate in a custom field for audit/reporting.
  C. Custom rate table: Use a custom object as exchange rate lookup; 
     QCP reads the rate and applies conversion in plugin code.
```

**Detection hint:** Any CPQ multi-currency design that references "dated exchange rates" or "Advanced Currency Management" without explicitly noting the CPQ limitation should be flagged.
