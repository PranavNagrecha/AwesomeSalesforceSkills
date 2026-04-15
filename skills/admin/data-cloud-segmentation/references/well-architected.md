# Well-Architected Notes — Data Cloud Segmentation

## Relevant Pillars

- **Performance** — Segment type and refresh schedule selection directly affect platform compute consumption and data freshness. Rapid Publish segments consume more processing resources than Standard segments and are quota-limited to 20 per org. Incremental refresh reduces compute for large segments by evaluating only changed records.
- **Reliability** — Hard limits (9,950 segments, 20 Rapid Publish segments, 100 activations with related attributes, 10M profile threshold for related attributes) create failure modes that are silent and difficult to diagnose at runtime. Reliable designs track these limits proactively rather than reacting after failures.
- **Operational Excellence** — Segment refresh and activation publish are independently scheduled. Operational hygiene requires both schedules to be explicitly configured and reviewed together. Stale segment inventories that approach the 9,950 limit require active lifecycle management.

## Architectural Tradeoffs

**Standard vs. Rapid Publish vs. Incremental:**
- Standard is the safe default for most business use cases — it evaluates full history, has no org quota pressure, and supports any filter date range.
- Rapid Publish trades org quota (20 total) and data history (7-day lookback only) for sub-4-hour refresh frequency. Use it only when the business outcome genuinely requires hourly audience updates and the filter criteria fit within the 7-day window.
- Incremental refresh is the most compute-efficient option for large data volumes but requires a data model that supports change detection. If the underlying DMO does not have reliable change timestamps, Incremental will miss changes and under-count segment membership.

**Segment Granularity vs. Limit Headroom:**
- Creating a separate segment per campaign or per A/B variant is intuitive but consumes segment quota rapidly. Large orgs should design reusable base segments with activation-level filtering or use Waterfall segments to subdivide a single audience into mutually exclusive buckets.
- The 9,950 segment limit incentivizes composing fewer, more flexible segments over creating many narrow ones.

**Related Attributes and Population Size:**
- The 20 related attribute cap and 10M population threshold for related attributes create a design tension: the largest audiences (most impactful for at-scale marketing) have the fewest attribute options. For very large segments, push attribute enrichment to the activation target's native data model rather than relying on Data Cloud related attribute delivery.

## Anti-Patterns

1. **Treating segment refresh as activation delivery** — Designing a workflow that assumes faster segment refresh automatically means faster data in the downstream system. The correct architecture explicitly configures both the segment refresh schedule and the activation publish schedule and aligns them to the delivery SLA.

2. **Rapid Publish for long-lookback segments** — Using Rapid Publish refresh on segments that filter on data older than 7 days, producing silently under-counted audiences. The correct architecture restricts Rapid Publish to use cases with filter windows of 7 days or less and uses Standard refresh for all others.

3. **Unbounded segment proliferation** — Creating a separate Standard segment for every campaign, every A/B test variant, and every team request without a decommission process. As org count approaches 9,950, creation failures begin with no warning. The correct architecture establishes a segment governance process including retirement criteria and uses Waterfall or Dynamic segments to consolidate related audiences.

4. **Activating without null identity filter** — Publishing an activation without filtering out profiles missing the downstream system's required identifier (email, phone). The correct architecture always adds an explicit IS NOT NULL filter on the required field before activating.

## Related Skills

- admin/data-cloud-identity-resolution — segments evaluate unified profiles; identity resolution quality determines segment accuracy
- admin/data-cloud-calculated-insights — calculated insights can be used as segment filter attributes; required when segment criteria include aggregated metrics (e.g., lifetime spend)
- admin/data-cloud-activation-development — for building custom activation targets beyond native connectors

## Official Sources Used

- Publish a Segment in Data Cloud — https://help.salesforce.com/s/articleView?id=sf.c360_a_publish_segment.htm
- Create a Data Cloud Activation for a Segment — https://help.salesforce.com/s/articleView?id=sf.c360_a_create_data_cloud_activation.htm
- Learn to Navigate Data 360 Segmentation Effectively (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/customer-360-audiences-segmentation
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
