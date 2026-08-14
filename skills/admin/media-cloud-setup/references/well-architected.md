# Well-Architected Notes — Media Cloud Setup

## Relevant Pillars

### Scalability

Ad delivery is the highest-volume data in a media business by orders of magnitude, and almost none of it belongs in the CRM. A single flight can serve more impressions in a day than the org holds records in total. Scalable Media Cloud implementations keep Salesforce at the grain of the commercial artefact — `AdOpportunity`, `AdQuote`, `AdQuoteLine`, `AdOrderItem` and their children — and hold delivery as a daily rollup per line, with a pointer back to the ad server's own report for the granular evidence. Storage then scales with sold lines, not with served impressions.

### Reliability

The quote and order families mirror each other rather than sharing records: `AdQuoteLineAdTarget` / `AdOrderLineAdTarget`, `AdQuoteLineDeliverySchedule` / `AdOrderItemDeliverySchedule`, `AdQuoteLineHiatus` / `AdOrderLineHiatus`, and so on. Anything a customisation writes to one side is absent on the other, and the failure shows up as an order that trafficks with default dates or no targeting — an operational incident with a revenue consequence, discovered by the ad ops team rather than by a test. Reliability here means the quote-to-order transition is tested with every child populated, asserted on the order side.

### Operational Excellence

The integration path is prescribed, not open. The AdTech Integration API supplies "integration APIs and apps for integrating Media Cloud Advertising Sales Management (ASM) with external adtech systems," requires connecting a MuleSoft instance, and on deployment "Salesforce creates a named credential for the integration instance." Using the generated named credential rather than a hand-rolled endpoint keeps credentials out of source, keeps the callout on the supported path, and keeps the org from diverging at each release. It also makes the MuleSoft dependency a budget decision taken deliberately at design time instead of a surprise at build time.

## Architectural Tradeoffs

**Shipped integration vs. bespoke callouts.** The shipped path carries a MuleSoft dependency and constrains the payload shape; bespoke Apex callouts are free of both and diverge from the product at every release. Choose bespoke only where the ad server genuinely is not supported, and record that decision — it is a permanent maintenance commitment, not a shortcut.

**Rollup grain vs. dispute resolution.** Daily-per-line rollups keep storage sane and answer most questions. Hourly or per-creative grain answers more questions and multiplies row count by the same factor. Pick the grain from the disputes that actually occur, and store the source report identifier either way so the fine detail remains reachable.

**One quote with many lines vs. one quote per channel.** A cross-channel sponsorship modelled as a single `AdQuote` with an `AdQuoteLine` per channel — each carrying its own `AdQuoteMediaTypeProperty` — aggregates cleanly for the deal and lets each line run its own recognition rule. Splitting into separate quotes per channel simplifies each one and loses the deal-level view the salesperson negotiated against.

## Anti-Patterns

1. **Modelling ad sales as custom `Media_*__c` objects.** The shipped objects are standard and prefixed `Ad`. A parallel custom model cannot feed the AdTech integration, the revenue rules, or the packaged UI, and every week it exists is another week of migration to undo.

2. **Inferring child object names from a prefix pattern.** The order-side children split between `AdOrderItem…` (space spec, creative size, delivery frequency and schedule, print issue, units split) and `AdOrderLine…` (ad target, hiatus, target expression, target value). A name completed from the pattern rather than copied from the reference is the single most common defect in generated code for this domain.

3. **Loading raw impression logs for auditability.** Row-level delivery in Salesforce fills storage, slows the reconciliation window, and duplicates data the ad server already retains. Store the aggregate and the source report identifier; point at the source for the rest.

## Official Sources Used

- Media Cloud Developer Guide — Media Cloud Standard Objects — verbatim descriptions for `AdOpportunity`, `AdOpportunityLineItem`, `AdQuote`, `AdQuoteLine`, `AdQuoteMediaTypeProperty`, `AdOrderItem`, `AdOrderItemAdSpaceSpec`, `AdOrderItemCreativeSizeType`, `AdOrderItemDeliveryFrequency`, `AdOrderItemDeliverySchedule`, `AdOrderItemPrintIssue`, `AdOrderItemUnitsSplit`, `AdOrderLineAdTarget`, `AdOrderLineHiatus`, `AdOrderLineTargetExpression`, `AdOrderLineTargetValue`, and the quote-side mirrors (verified 2026-08-14) — https://developer.salesforce.com/docs/atlas.en-us.media_developer_guide.meta/media_developer_guide/media_cloud_standard_objects_overview.htm
- Media Cloud AdTech Integration API — Get Started — the MuleSoft-connected integration path and the generated named credential specifying "the URL of a callout endpoint and its required authentication parameters" (verified 2026-08-14) — https://developer.salesforce.com/docs/industries/media-cloud/guide/get-started.html
- Media Cloud Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.media_developer_guide.meta/media_developer_guide/media_industries_dev_guide.htm
- Object Reference for the Salesforce Platform — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
