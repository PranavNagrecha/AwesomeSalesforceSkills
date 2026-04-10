# Gotchas — CPQ Architecture Patterns

Non-obvious Salesforce CPQ platform behaviors that cause real production problems in this domain.

## Gotcha 1: SBQQ__Code__c Truncation Is Silent

**What happens:** When `SBQQ__Code__c` on the `SBQQ__CustomScript__c` object is saved with content exceeding 131,072 characters, Salesforce silently truncates the field value at the character limit. There is no validation error, save failure, or warning in the UI or API response. The field reports a successful save.

**When it occurs:** During deployment or manual entry of a Quote Calculator Plugin that has grown through iterative development. Teams typically hit this limit only after significant feature development — by which time the plugin is already in production or UAT.

**How to avoid:** Measure QCP JavaScript size during development: `wc -c CPQPlugin.js`. If approaching 80,000 characters, adopt the Static Resource loader pattern immediately. Set a CI check on the Static Resource file size as a deployment gate. Never rely on the UI save to validate field length compliance.

---

## Gotcha 2: Price Rules Run After Discount Schedules — Always

**What happens:** The CPQ pricing waterfall sequence is fixed at: List Price → Contracted Price → Block Price → Discount Schedules → Price Rules → Net Price. Price Rules cannot be moved earlier in the sequence. A Price Rule that attempts to establish a base price or apply a preliminary discount will be evaluated after Discount Schedules have already modified the price.

**When it occurs:** When architects design a two-stage discount model — for example, a volume discount (intended to run via Discount Schedules) followed by a partner tier discount (intended to run via Price Rules). If the partner tier discount is designed as a percentage of the pre-volume-discount price, it will instead apply to the post-volume-discount price, producing lower-than-expected net prices.

**How to avoid:** Design all multi-stage pricing logic with the fixed waterfall in mind. If a Price Rule must reference a pre-Discount-Schedule price, use a custom formula field to capture the price before the waterfall runs, or restructure the discount logic to use a single stage. Never design pricing logic that assumes Price Rules run before any discount stage.

---

## Gotcha 3: Direct API DML Bypasses the Pricing Engine Entirely

**What happens:** Creating or updating `SBQQ__Quote__c`, `SBQQ__QuoteLine__c`, or related CPQ records via Salesforce REST API, SOAP API, Bulk API, or Data Loader bypasses all CPQ managed package triggers and pricing engine logic. Net prices remain zero or stale, required CPQ-managed fields are not populated, and the quote enters a state that the QLE and activation process cannot handle correctly.

**When it occurs:** Integration developers unfamiliar with CPQ assume they can use standard Salesforce APIs to write quote data — a reasonable assumption for standard objects. The problem only becomes visible after data is written and the sales rep opens the quote.

**How to avoid:** Mandate ServiceRouter (`/services/apexrest/SBQQ/ServiceRouter`) for all external write operations on CPQ objects from day one of integration design. Document this constraint in the integration specification. Include a check in code review or data migration runbooks that flags any direct DML against `SBQQ__*` objects.

---

## Gotcha 4: Multi-Currency Exchange Rate Changes Retroactively Affect Existing Quotes

**What happens:** CPQ stores all prices in corporate currency and converts to transaction currency at display time using the org's current active exchange rate. When the org exchange rate is updated (e.g., monthly forex update), all existing quotes in non-corporate currencies display updated prices — even quotes that were already presented to customers.

**When it occurs:** Finance teams update exchange rates as part of normal operations. Sales reps then see previously sent quote prices change, which can cause customer disputes or contract validity issues. There is no native CPQ mechanism to freeze the exchange rate at quote creation or presentation.

**How to avoid:** If financial accuracy over time is required, implement a custom field to snapshot the exchange rate at quote creation (or at the "Presented" status transition) and use that snapshot in reports and document generation. For multi-currency deals where currency risk is a genuine business concern, evaluate the pricebook-per-currency architecture where prices are pre-converted and locked.

---

## Gotcha 5: Large Quote Mode Is Account-Level, Not Quote-Level

**What happens:** Large Quote Mode is primarily controlled by the `SBQQ__LargeQuote__c` checkbox on the Account record (or by a CPQ package setting). There is no native way to enable Large Quote Mode for specific quotes while leaving other quotes on the same account in standard mode.

**When it occurs:** Architects plan to selectively enable Large Quote Mode only for unusually large quotes, expecting to make a per-quote decision. In practice, the flag on the Account applies to all quotes for that Account. If a large enterprise account needs Large Quote Mode for complex product quotes, all of that account's small standard quotes will also use async calculation — changing the UX for sales reps working on routine renewals.

**How to avoid:** Design Large Quote Mode as an account-tier decision rather than a per-quote decision. Segment accounts by expected quote complexity. For mixed-complexity accounts, consider whether the async UX is acceptable across all quote types before enabling the flag. Communicate the UX change to all affected sales users — not just those working on large quotes.

---

## Gotcha 6: Nested Bundle Calculation Timeout Under Apex CPU Limits

**What happens:** Each level of bundle nesting multiplies the number of SOQL queries and Apex operations executed during pricing recalculation. A 3-level nested bundle with multiple sub-bundle options can consume significant Apex CPU time per save, particularly when combined with Price Rules and Discount Schedules. At scale, this causes intermittent `System.LimitException: Apex CPU time limit exceeded` errors during quote save.

**When it occurs:** During UAT or early production use when realistic quote volumes are first tested. Development and unit testing typically use small quotes that do not expose the limit. The failure emerges only when representative product configurations with realistic quantities are tested.

**How to avoid:** Limit bundle nesting to 2 levels maximum. Benchmark pricing calculation time on representative quotes before go-live using CPQ's built-in calculation logging (enable via CPQ Settings > Show Calculation Logs). If calculation time approaches 10 seconds on representative quotes, flatten the bundle structure and use Option Constraints to achieve equivalent selection behavior.
