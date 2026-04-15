# Well-Architected Notes — Nonprofit Data Quality

## Relevant Pillars

- **Reliability** — The core data quality concern in NPSP is reliability of constituent data: addresses that are deliverable, rollup totals that are accurate, and Contacts that are not duplicated. NPSP's TDTM trigger framework and `npsp__Address__c` object model exist to enforce reliable data state. Bypassing them (native merge, direct address field updates) introduces silent data corruption.
- **Operational Excellence** — Sustainable data quality requires instrumented, repeatable processes: scheduled address verification batches, monitored NPSP Contact Merge workflows, and periodic NCOA runs (if licensed). Ad hoc manual corrections do not scale. Automation via NPSP's built-in batch processing and the Insights Platform integration is the operational path.
- **Security** — Address data and constituent PII managed through NPSP requires appropriate field-level security on `npsp__Address__c`. Geocoding API keys (for Google Geocoding) and SmartyStreets auth IDs should be stored in Named Credentials, not hardcoded in Custom Metadata or custom settings exposed to non-admin profiles.

## Architectural Tradeoffs

**NPSP Data Importer vs. direct API insert for constituent loads:**
Staging constituent records through `npsp__DataImport__c` and processing via the NPSP Data Importer adds steps but is the only path that applies NPSP Contact Matching Rules during load — preventing duplicates at ingestion time. Direct Contact insertion via Bulk API bypasses matching rules and increases post-load deduplication burden. For orgs with active NPSP Contact Matching Rules, always prefer the staging path for bulk constituent loads.

**Real-time address verification vs. batch verification:**
Real-time verification (trigger-based on `npsp__Address__c` create/update) provides immediate feedback but counts against per-transaction callout limits (max 100 callouts per transaction). Batch verification via `ADDR_Addresses_TDTM` processes records in configurable chunks but adds latency. For high-volume constituent loads, disable real-time verification during import and run the batch afterward.

**NPSP NCOA (Insights Platform Data Integrity) vs. third-party NCOA:**
Insights Platform Data Integrity provides tight integration with `npsp__Address__c` field updates but requires a separate premium license and is incompatible with Agentforce Nonprofit. Third-party NCOA services (e.g., BriteVerify, National Processing Company) can process address files externally and return corrections as CSV, which can then be re-imported to `npsp__Address__c` via Data Loader. The trade-off is manual integration effort vs. licensing cost and compatibility constraints.

## Anti-Patterns

1. **Using standard Salesforce Duplicate Rules as the sole duplicate prevention gate for NPSP orgs** — Standard Duplicate Rules fire post-insert via the standard platform framework and do not integrate with the NPSP Data Importer's batch processing model. NPSP Contact Matching Rules are required for import-time duplicate detection. Standard rules can supplement but cannot replace NPSP-specific matching.

2. **Using native Salesforce merge for NPSP household Contact deduplication** — Native `Database.merge()` or the standard Contacts list view merge does not invoke NPSP's TDTM handler chain. Rollup fields on the Household Account become stale or incorrect. Any org that deduplicates NPSP Contacts at scale must use NPSP Contact Merge or a custom Apex implementation that explicitly invokes NPSP's rollup recalculation.

3. **Editing Contact or Account mailing address fields directly in NPSP** — Any direct update to `MailingStreet`, `MailingCity`, or related fields on Contact (or `BillingStreet` etc. on Household Account) is overwritten by NPSP's address sync on the next synchronization event. All address management must operate on `npsp__Address__c` objects.

## Related Skills in This Repo

- `data/constituent-data-migration` — Upstream skill; address quality should be enforced at import time
- `data/npsp-data-model` — Reference for `npsp__Address__c` object structure and field relationships
- `data/large-scale-deduplication` — For org-wide deduplication beyond NPSP-specific household Contact merging

## Official Sources Used

- NPSP Address Management Overview — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Addresses_Overview.htm&type=5
- About National Change of Address Updates (NPSP) — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_NCOA.htm&type=5
- Configure Duplicate Detection and NPSP Contact Merge — https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Contact_Merge.htm&type=5
- Insights Platform Data Integrity (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/insights-platform-data-integrity
- NPSP Documentation Overview — https://help.salesforce.com/s/articleView?id=sfdo.NPSP.htm&type=5
