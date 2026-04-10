# Gotchas — CPQ Data Model

Non-obvious Salesforce CPQ platform behaviors that cause real production problems.

## Gotcha 1: Standard Quote Is NOT the CPQ Quote

**What happens:** In CPQ orgs the standard `Quote` object may appear populated because CPQ can sync a copy of the CPQ quote header to it. But `Quote.TotalPrice`, `Quote.LineItems`, and `QuoteLineItem` records do not carry CPQ-calculated pricing — they carry a synced snapshot that may be hours or days stale. Code or reports that read from standard `Quote` in a CPQ org are reading the wrong source.

**When it occurs:** Any time a developer or integration queries `SELECT TotalPrice FROM Quote WHERE OpportunityId = :id` in an org with CPQ installed. Also occurs in Flow when the standard "Get Records" element targets `Quote` for pricing decisions.

**How to avoid:** Always query `SBQQ__Quote__c` for CPQ pricing data. Use `SBQQ__Primary__c = true` to find the primary quote on an opportunity. Only use standard `Quote` if the downstream system (e.g., a DocuSign integration) explicitly requires it and you understand it may be a synced copy.

---

## Gotcha 2: Direct DML on Calculated Price Fields Corrupts Quote Totals

**What happens:** Writing directly to `SBQQ__NetPrice__c`, `SBQQ__CustomerPrice__c`, or `SBQQ__RegularPrice__c` on `SBQQ__QuoteLine__c` via Apex DML saves the value but does not invoke the CPQ pricing engine. The quote-level `SBQQ__NetAmount__c` rollup becomes stale. Approval thresholds, discount validation rules, and CPQ pricing waterfall reports all operate on incorrect values. On the next CPQ-triggered save the engine overwrites the manually set value.

**When it occurs:** Any direct `update` DML on `SBQQ__QuoteLine__c` that touches a CPQ-managed price field. Also occurs in data loads (Data Loader, Bulk API) used to bulk-adjust prices without going through the CPQ Quote API.

**How to avoid:** Route all programmatic price changes through the CPQ Quote API (`SBQQ.QuoteService.read`, `calculate`, `save`). For bulk operations, batch through the REST-based CPQ Quote API endpoint rather than Bulk API direct DML.

---

## Gotcha 3: Wrong Child Relationship Names in SOQL Return Zero Rows

**What happens:** The child relationship from `SBQQ__Quote__c` to `SBQQ__QuoteLine__c` is `SBQQ__LineItems__r`, not `QuoteLineItems` or `LineItems`. Using an incorrect relationship name in a subquery compiles without error but returns an empty list, making the bug appear as a data problem rather than a query problem.

**When it occurs:** Writing subqueries on `SBQQ__Quote__c` without consulting the CPQ object model reference. Common mistakes: `QuoteLineItems`, `SBQQ__QuoteLines__r`, `LineItems__r`.

**How to avoid:** Use the correct relationship names from the CPQ package schema:
- `SBQQ__Quote__c` → `SBQQ__QuoteLine__c`: `SBQQ__LineItems__r`
- `SBQQ__Quote__c` → `SBQQ__QuoteLineGroup__c`: `SBQQ__LineItemGroups__r`
- `SBQQ__DiscountSchedule__c` → `SBQQ__DiscountTier__c`: `SBQQ__DiscountTiers__r`
- `SBQQ__PriceRule__c` → `SBQQ__PriceAction__c`: `SBQQ__PriceActions__r`
- `SBQQ__PriceRule__c` → `SBQQ__PriceCondition__c`: `SBQQ__Conditions__r`

Verify in Setup > Object Manager > (object name) > Fields & Relationships > Child Relationships, or use the SOAP describe endpoint.

---

## Gotcha 4: Subscriptions Are Per-Line, Not Per-Contract

**What happens:** When a CPQ quote is contracted, the system creates one `SBQQ__Subscription__c` per contracted quote line with a subscription-type product. Developers expecting one subscription object per contract are surprised to find 5, 10, or 50 subscription records for a single contract. Renewal generation, amendment logic, and subscription reporting must iterate over all subscription records for a contract.

**When it occurs:** Any code or Flow that assumes `SBQQ__Subscription__c WHERE SBQQ__Contract__c = :id` returns a single record. Also surprises developers who build reports counting subscriptions per customer — the count reflects contracted lines, not contracted deals.

**How to avoid:** Always aggregate `SBQQ__Subscription__c` by `SBQQ__Contract__c` with `COUNT()` or loop through all records. When building renewal flows, retrieve all active subscriptions for the contract and pass the full set to the renewal quote builder.

---

## Gotcha 5: Price Rules Without Tight Conditions Fire on Every Line and Every Save

**What happens:** An `SBQQ__PriceRule__c` with no entry conditions (or very broad conditions) executes its `SBQQ__PriceAction__c` records against every single quote line on every CPQ pricing pass. In a 50-line quote with 10 broadly-scoped price rules, the pricing engine evaluates 500 rule-line combinations on every save. This can cause CPU time limit errors and unpredictable price overrides.

**When it occurs:** Price rules configured with the Evaluation Scope set to "Always" and no conditions, or conditions that match all products. Especially problematic when the price action uses a formula that itself queries related data.

**How to avoid:** Scope price rules with specific conditions: filter by Product Family, Product Code, or a custom field on the quote or quote line. Set the evaluation order to minimize unnecessary evaluations. Monitor the CPQ pricing calculator plugin logs in the Developer Console to profile which rules are firing.

---

## Gotcha 6: SBQQ__Subscription__c Is Not Standard Asset

**What happens:** Salesforce has a standard `Asset` object commonly used to track purchased products. CPQ also has its own `SBQQ__Asset__c` object for asset-based quoting. `SBQQ__Subscription__c` is a third, separate object for recurring subscription tracking. All three can exist in the same org. Code that queries `Asset` for renewal data will miss recurring subscriptions. Code that queries `SBQQ__Asset__c` may miss subscriptions if asset-based quoting is not enabled.

**When it occurs:** Integrations that assume a universal "purchased product" object. Also occurs in custom renewal automations that query `Asset WHERE AccountId = :id` expecting to find all contracted products.

**How to avoid:** Use `SBQQ__Subscription__c` for recurring subscription tracking in CPQ orgs. Use `SBQQ__Asset__c` only if the CPQ package configuration uses asset-based quoting (check `SBQQ__Quote__c.SBQQ__Type__c` for "Amendment" flows). Use standard `Asset` only for non-CPQ tracked items.
