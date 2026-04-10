# Well-Architected Notes — AMPscript Development

## Relevant Pillars

- **Performance** — AMPscript Lookup calls execute at send time, once per subscriber. Non-PK field lookups on large DEs perform full table scans at send time and can degrade send throughput. Choosing the right lookup function (single `Lookup()` vs. `LookupOrderedRows()` with count cap) and ensuring lookup fields are DE primary keys are direct performance decisions.
- **Reliability** — AMPscript evaluated without a subscriber context returns empty strings for all data calls, which can cause emails to render without personalization rather than failing visibly. Null guards (`EMPTY()`, `IF @rowCount > 0`) and ELSE branches ensure content remains valid even when data is missing. Missing ELSE branches cause partial or blank content blocks in production.
- **Security** — AMPscript can read from any DE accessible to the Marketing Cloud Business Unit. There are no row-level or field-level access controls on Lookup calls within AMPscript. Sensitive fields (PII, financial data) stored in DEs are accessible to any AMPscript author with content editing permissions. Data exposure risk must be managed at the DE access and BU permission level, not at the AMPscript level.
- **Operational Excellence** — AMPscript embedded in email templates with no fallback paths, no comments, and no named variables is difficult to maintain and debug. Using descriptive variable names (`@loyaltyTier` vs. `@x`), adding brief inline comments for non-obvious logic, and centralizing complex logic in one `%%[ ... ]%%` block at the top of the content area reduces maintenance burden.
- **Scalability** — `LookupRows()` caps at 2,000 rows. Designs that rely on subscriber-scoped DEs with bounded row counts scale predictably. Designs that use non-subscriber-scoped DEs or lookup on non-PK fields break as DE volume grows. Pre-aggregating data into subscriber-scoped DEs via SQL Query Activity is the scalable alternative to complex in-email AMPscript lookups.

## Architectural Tradeoffs

**AMPscript vs. SSJS for per-subscriber rendering:** AMPscript is evaluated per subscriber at send time and is the preferred language for subscriber-level data retrieval and conditional rendering inside email, SMS, and push content. SSJS is preferred for platform API calls (HTTP requests, SOAP/REST), complex string and date manipulation beyond AMPscript's built-in functions, and Cloud Page server-side logic. Mixing both in a single email content area is valid but increases debugging complexity — prefer AMPscript-first and escalate to SSJS only when a specific capability requires it.

**Pre-send aggregation vs. in-email lookup:** Performing complex multi-DE joins or aggregations inside AMPscript using nested `Lookup()` calls on non-PK fields degrades send performance and makes email content harder to debug. The well-architected alternative is to run SQL Query Activities in Automation Studio before the send to pre-aggregate data into a flat, subscriber-scoped DE, and then use a simple `Lookup()` or `AttributeValue()` in the email. This separates data preparation from presentation and makes each component testable independently.

**Inline expressions vs. block logic in subject lines:** Subject lines must use only inline `%%= ... =%%` expressions. This limits the complexity of subject line personalization to what can be expressed as a single function call or variable reference. Complex logic (conditionals, computed values) must be set in the email body block and referenced via a variable in the subject line — a pattern that requires the body block to execute before the subject line, which Marketing Cloud handles correctly because body blocks precede subject rendering in the evaluation order.

## Anti-Patterns

1. **Lookup on non-PK fields without a pre-send aggregation plan** — Running `LookupRows("Orders_DE", "Region", "WEST")` where Region is not a PK field on a 5M-row DE causes a full table scan at send time for every subscriber. On large sends this degrades throughput for all concurrent sends in the BU. Correct approach: index (via PK design) or pre-aggregate.

2. **Using SSJS for subscriber-level personalization that AMPscript handles natively** — SSJS initialization overhead in email content is unnecessary for straightforward Lookup-and-render patterns. It also makes the content unavailable for SMS and push channels. Use AMPscript for per-subscriber rendering; reserve SSJS for API calls and Cloud Page logic.

3. **No ELSE branch on conditional blocks** — Omitting `%%[ ELSE ]%%` from an `IF/ELSEIF` chain causes the content area to render empty for any subscriber who does not match a defined condition. This is especially dangerous in promotional emails where a blank section looks broken to subscribers and can suppress engagement. Always include an ELSE with a safe default.

## Official Sources Used

- AMPscript Overview — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/ampscript.html
- LookupRows Function Reference — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/lookuprows.html
- AMPscript FOR Loop Reference — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/for.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
