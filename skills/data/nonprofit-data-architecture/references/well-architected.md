# Well-Architected Notes — Nonprofit Data Architecture

## Relevant Pillars

- **Reliability** — NPSP rollup calculations depend on the CRLP engine running without interference. Mixed CRLP/legacy mode is the primary reliability threat. Ensuring exactly one rollup engine is active, and that the NPSP Health Check passes, is the foundational reliability requirement. PMM service delivery records are the authoritative source for program participation reporting; their accuracy depends on staff consistently recording deliveries in real time.

- **Performance** — The CRLP engine processes rollup recalculations asynchronously and at high volume. Custom Apex triggers on Opportunity that perform synchronous aggregate SOQL to recompute rollup-like values will create governor limit failures at scale. NPSP's CRLP is designed to handle high-volume Opportunity inserts via the Rollup State mechanism; custom alternatives rarely replicate this correctly. For high-volume data loads (migrations, annual appeal gift imports), use the NPSP Data Import Batch process rather than direct DML to avoid triggering CRLP recalculations row-by-row.

- **Scalability** — Household Accounts that aggregate giving across many individual Contacts in large families or organizations can generate unusually large rollup recalculation workloads. CRLP's Filter Groups must be kept minimal — each additional active Rollup__mdt record adds to recalculation time per Opportunity save. Design custom rollups conservatively and test under load before enabling in production.

- **Operational Excellence** — NPSP and PMM are managed packages with their own release cadences. Schema changes between versions can add or deprecate fields. Maintaining a package version inventory and testing in a sandbox before upgrading is essential. The NPSP Health Check tool surfaces configuration drift and should be run after every major schema change, package upgrade, or batch import.

- **Security** — HH_Account records are the financial unit for a constituent household. Sharing rules on Account and Opportunity must be designed with the understanding that gift data on the HH Account is visible to all users with Account read access who can navigate to the household. Constituent data (Contact) may have different sensitivity requirements than giving data (Opportunity on HH Account). Object-level and field-level security must be set separately for NPSP namespace fields — they are not automatically restricted.

## Architectural Tradeoffs

**CRLP real-time updates vs. batch processing for custom rollups:**
CRLP provides near-real-time rollup recalculation, which is valuable for constituent-facing portals or reporting that needs current data. However, enabling many custom Rollup__mdt records increases the synchronous processing load per Opportunity save. For rollups that are only consumed in scheduled reports, consider whether daily batch recalculation is sufficient, reducing the per-transaction overhead.

**PMM service delivery granularity vs. reporting complexity:**
Recording every service delivery as an individual pmdm__ServiceDelivery__c record provides maximum granularity for program reporting but creates high-volume tables in orgs with intensive programs. Organizations that run daily group services (e.g., meal programs) should consider the reporting query performance implications of millions of ServiceDelivery records before designing at maximum granularity.

**Household Account model vs. per-constituent giving tracking:**
The HH_Account model ties giving history to the household unit, which is the correct model for joint household cultivation. However, orgs that need strict per-individual giving attribution (e.g., for matching gift validation or individual tax acknowledgments) must always query via `npsp__Primary_Contact__c` on Opportunity, not via the Account. This means HH Account rollup fields cannot be used for per-individual attribution — only Contact-level rollup fields are appropriate.

## Anti-Patterns

1. **Bypassing the CRLP engine with custom Apex rollup triggers** — Writing a custom `Trigger` on `Opportunity` that performs its own aggregate SOQL and updates `npo02__TotalOppAmount__c` directly conflicts with CRLP. When both run, they overwrite each other's values in unpredictable order. The correct extension point for custom rollup logic is a new `Rollup__mdt` custom metadata record via the CRLP UI, not a custom trigger on the rollup target field.

2. **Treating rollup fields as authoritative for financial reporting** — NPSP rollup fields (`npo02__TotalOppAmount__c`, etc.) are calculated summaries, not ledger entries. They can become stale due to a failed CRLP batch, a CRLP/legacy conflict, or a data load that bypassed triggers. Financial reports must always aggregate from raw `Opportunity` records, not from rollup fields. Rollup fields are appropriate for display and segmentation, not for audit-grade totals.

3. **Storing program participation data in custom objects instead of PMM** — Orgs that build bespoke program enrollment objects outside the PMM framework lose NPSP's built-in Program Management reports, the Salesforce.org AppExchange ecosystem integrations that expect PMM objects, and the standard PMM data quality framework. If PMM is available, use it — custom alternatives create permanent maintenance burden and integration incompatibility.

## Official Sources Used

- NPSP Data Model Gallery — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_erd_nonprofit_success_pack.htm
- Nonprofit Cloud Data Model Developer Guide (Spring '26) — https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud_dev.meta/nonprofit_cloud_dev/npc_data_model.htm
- Trailhead: Explore the NPSP Data Model — https://trailhead.salesforce.com/content/learn/modules/npsp-data-model
- NPSP Documentation Overview — https://powerofus.force.com/s/article/NPSP-Documentation
- Customizable Rollups Developer Documentation — https://powerofus.force.com/s/article/NPSP-Customizable-Rollups
- Program Management Module Documentation — https://powerofus.force.com/s/article/PMM-Documentation
