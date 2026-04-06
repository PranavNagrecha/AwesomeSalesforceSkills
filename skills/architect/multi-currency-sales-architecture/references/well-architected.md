# Well-Architected Notes — Multi-Currency Sales Architecture

## Relevant Pillars

- **Reliability** — Currency conversion is a financial calculation. Incorrect conversions directly affect revenue reporting, forecasting, and compliance. The system must produce consistent, auditable numbers regardless of when a report is run or who runs it. Silent fallback to static rates when dated rates are missing is a reliability risk that must be mitigated with monitoring.

- **Performance** — Querying `DatedConversionRate` in Apex for custom conversion logic adds SOQL overhead. Bulk operations on currency-bearing records must be designed to minimize rate lookups — for example, by pre-loading all relevant rates for the batch's date range into a map rather than querying per record.

- **Operational Excellence** — Exchange rate maintenance is an ongoing operational burden. Without automation and monitoring, rate gaps accumulate silently. The operational model must define who is responsible for rates, how they are loaded, and how gaps are detected and remediated.

- **Scalability** — As the number of active currencies and historical date ranges grows, the `DatedConversionRate` table grows linearly. Orgs with 20+ currencies and multi-year history accumulate thousands of rate records. Custom Apex that queries this table must be designed for this volume.

## Architectural Tradeoffs

1. **ACM vs. standard multi-currency.** ACM provides historical accuracy but is irreversible and adds complexity. Standard multi-currency is simpler but retroactively changes all conversions when rates update. The decision hinges on whether the org needs point-in-time financial accuracy or can tolerate current-rate-only views. See Decision Guidance in SKILL.md.

2. **Native roll-ups vs. custom aggregation.** Native roll-up summary fields are zero-code and performant but always use the static rate, producing incorrect totals when ACM is enabled and rates have diverged. Custom Apex or Flow aggregation is accurate but adds maintenance burden and must handle bulk scenarios. The tradeoff is accuracy vs. maintenance cost.

3. **Live conversion vs. snapshotted values.** Relying on Salesforce's live `ConvertedAmount` fields means values update as rates change — which is correct for current views but problematic for audits. Snapshotting converted amounts into custom fields at close time provides audit stability but requires trigger logic and additional storage.

## Anti-Patterns

1. **Enabling ACM without a rate maintenance plan** — ACM is only as good as its dated exchange rate data. Enabling it without an automated rate-loading pipeline and gap-monitoring process means the org has the complexity of ACM but still produces incorrect conversions when rates are missing.

2. **Trusting native roll-ups for financial totals under ACM** — Using declarative roll-up summary fields to aggregate currency amounts and presenting them to finance as accurate totals. Under ACM, these roll-ups use the static rate and will not match the sum of child records' dated-rate conversions. This creates audit findings.

3. **Assuming all objects support dated rates** — Designing an architecture that depends on dated rate conversion for custom objects or non-supported standard objects. Only a subset of standard objects (Opportunity, OpportunityLineItem, and a few others) use dated rates. Custom objects always use the static rate, requiring manual Apex-based conversion.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Manage Multiple Currencies — https://help.salesforce.com/s/articleView?id=sf.admin_currency.htm
- Salesforce Object Reference: CurrencyType — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_currencytype.htm
