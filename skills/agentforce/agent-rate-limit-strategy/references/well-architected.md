# Well-Architected Notes — Agent Rate Limit Strategy

**Scalability:** a per-user budget converts a shared, exhaustible entitlement into an
isolated one, so a single misbehaving caller degrades only itself. The gate must be
cheaper than the call it guards — a single counter read rather than an aggregate query,
and policy in custom metadata, which the Apex Developer Guide documents as exempt from
the per-transaction SOQL query limit.

**Cost Optimization:** consumption is metered per persona and the thresholds live in
deployable metadata, so a traffic shift is a data change rather than a release. Note that
Salesforce does not publish a universal per-org Agentforce token ceiling in the developer
documentation; thresholds must be derived from the org's own usage pages and contract,
and this skill deliberately ships no default.

**Operational Excellence:** the alertable signal is refusal rate, not absolute
consumption. Rising consumption is ordinary growth; rising refusals are a defect or an
abuser.

## Official Sources Used

- Apex Governor Limits — 100 SOQL queries and 150 DML statements per synchronous transaction, and the custom metadata exemption ("In a single Apex transaction, custom metadata records can have unlimited SOQL queries") — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Platform API limits — concurrent long-running request allocation and the REQUEST_LIMIT_EXCEEDED exception code — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm
- Platform Events Developer Guide — publishing behaviour and allocations for the consumption ledger — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Custom Metadata Types — getInstance() access from Apex — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_custom_metadata_get.htm
- Agentforce Developer Guide — agent invocation surface — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
