# Well-Architected Notes — Record Merge Implications

## Relevant Pillars

- **Reliability** — Merges that silently discard field values or fail mid-batch on converted Leads produce unreliable data outcomes. Reliable merge operations require explicit field resolution, pre-merge validation, and verification of child record re-parenting after the merge completes.
- **Trust** — Record merges delete the losing records; undelete is possible but child re-parenting cannot be undone (apexdev 264 L8444-8445). Ensuring that business-critical data (owners, field values, Campaign Member responses) is preserved and that external ID mappings are maintained is fundamental to data integrity and user trust in the platform.

## Architectural Tradeoffs

**UI merge vs. Apex merge:** The UI merge provides a field selection screen and is the lowest-risk approach for individual or small-batch merges. Apex `Database.merge()` is required for bulk programmatic deduplication but carries data-loss risk if field copying is not implemented explicitly. For any merge involving more than ~50 records, Apex with explicit field mapping is required.

**Automated deduplication vs. manual review:** Fully automated merge jobs (driven by Duplicate Management match rules) are faster but may incorrectly merge non-duplicate records. Human-review queues for merge candidates above a certain confidence threshold reduce false-positive merges that are costly to remediate.

## Anti-Patterns

1. **Calling Database.merge() without first copying fields from losing records** — Silent data loss. Always read losing record fields and update master before merging.
2. **Not filtering converted Leads before a Lead merge batch** — Causes failures in bulk jobs (UNVERIFIED (2026-10-20): the converted-Lead exclusion and its exception are Help-only).
3. **Assuming external systems will auto-resolve old record IDs** — the corpus describes `MasterRecordId` on the deleted record (object_reference 264 L12945-12952), not a redirect (UNVERIFIED (2026-10-20): no EntityId redirect is documented). Maintain an ID mapping table.

## Official Sources Used

- Salesforce Help — Merge Duplicate Accounts — https://help.salesforce.com/s/articleView?id=sf.accounts_merge.htm
- Salesforce Help — Merge Duplicate Contacts — https://help.salesforce.com/s/articleView?id=sf.contacts_merge.htm
- Salesforce Help — Merge Duplicate Leads — https://help.salesforce.com/s/articleView?id=sf.leads_merge.htm
- Apex Developer Guide 264 L8173-8353 (Merging Records, Merge Considerations), L15557-15572 (Triggers and Merge Statements), L8444-8446 (Undelete Considerations); Object Reference 264 L12945-12952 (`MasterRecordId`); REST API 264 L17232 (QueryAll); Apex Reference 262 L208422-208497 (`Database.merge` overloads)
- Apex Developer Guide — Database.merge() — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_methods_system_database.htm
- Salesforce Help — Merge Fields in a Record — https://help.salesforce.com/s/articleView?id=sf.basics_merge_records.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
