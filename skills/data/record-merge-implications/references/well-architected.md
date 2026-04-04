# Well-Architected Notes — Record Merge Implications

## Relevant Pillars

- **Reliability** — Merges that silently discard field values or fail mid-batch on converted Leads produce unreliable data outcomes. Reliable merge operations require explicit field resolution, pre-merge validation, and verification of child record re-parenting after the merge completes.
- **Trust** — Record merges permanently delete records and cannot be undone. Ensuring that business-critical data (owners, field values, Campaign Member responses) is preserved and that external ID mappings are maintained is fundamental to data integrity and user trust in the platform.

## Architectural Tradeoffs

**UI merge vs. Apex merge:** The UI merge provides a field selection screen and is the lowest-risk approach for individual or small-batch merges. Apex `Database.merge()` is required for bulk programmatic deduplication but carries data-loss risk if field copying is not implemented explicitly. For any merge involving more than ~50 records, Apex with explicit field mapping is required.

**Automated deduplication vs. manual review:** Fully automated merge jobs (driven by Duplicate Management match rules) are faster but may incorrectly merge non-duplicate records. Human-review queues for merge candidates above a certain confidence threshold reduce false-positive merges that are costly to remediate.

## Anti-Patterns

1. **Calling Database.merge() without first copying fields from losing records** — Silent data loss. Always read losing record fields and update master before merging.
2. **Not filtering converted Leads before a Lead merge batch** — Causes FIELD_INTEGRITY_EXCEPTION failures in bulk jobs.
3. **Assuming external systems will auto-resolve old record IDs** — EntityId redirects work in standard API calls but not all integrations follow redirects. Maintain an ID mapping table.

## Official Sources Used

- Salesforce Help — Merge Duplicate Accounts — https://help.salesforce.com/s/articleView?id=sf.accounts_merge.htm
- Salesforce Help — Merge Duplicate Contacts — https://help.salesforce.com/s/articleView?id=sf.contacts_merge.htm
- Salesforce Help — Merge Duplicate Leads — https://help.salesforce.com/s/articleView?id=sf.leads_merge.htm
- Apex Developer Guide — Database.merge() — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_methods_system_database.htm
- Salesforce Help — Merge Fields in a Record — https://help.salesforce.com/s/articleView?id=sf.basics_merge_records.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
