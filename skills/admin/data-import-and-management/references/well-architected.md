# Well-Architected Mapping: Data Import and Management

## Pillars Addressed

### Reliability

Good load design prevents duplicates, broken relationships, and partial cutovers.

- External IDs and upsert design preserve identity across reruns.
- Reconciliation steps catch silent failures before users depend on bad data.

### Scalability

Bulk tooling and batch design determine whether a load works at real production volume.

- Bulk API and chunking patterns prevent admin tooling from becoming the bottleneck.
- Load-order design reduces lock contention and failed retries.

### Operational Excellence

Runbooks, rollback plans, and rehearsals separate controlled migrations from heroic recovery work.

- Clear cutover ownership and checkpointing make failures diagnosable.
- Explicit automation and duplicate-rule handling reduce surprise during release windows.

## Pillars Not Addressed

- **Security** - this skill touches permissions only as a prerequisite for running loads, not as a security-design pattern.
- **User Experience** - the concern here is cutover safety, not end-user page behavior.

## Official Sources Used

- **Data Loader Guide** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf) — Settings reference for import batch size, Insert null values, and Assignment rule (the "Turning On Bulk API Silently Changes What Batch Size Means", "Blanks Do Not Clear Fields", and "Assignment Rule Overrides OwnerId" gotchas); the `process-conf.xml` sample bean, the process configuration parameter table, and the `.sdl` mapping syntax behind `references/metadata-examples.md` §2-3; `encrypt.bat` / `process.bat` usage; hard-delete prerequisites and the Bulk API Hard Delete permission; date formats, `sfdc.timezone`, and the GMT recommendation; Data Import Wizard vs Data Loader selection thresholds (under 50,000 records, fewer than 50 fields)
- **Bulk API 2.0 and Bulk API Developer Guide** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf) — job state machine Open → UploadComplete → InProgress → JobComplete/Failed/Aborted; the create-job request body (`operation`, `externalIdFieldName`, `lineEnding`, `columnDelimiter`, `assignmentRuleId`, `contentType`); the required UploadComplete PATCH; 10,000-record automatic batching, the 5-minute batch budget and 20 automatic retries; the `successfulResults` / `failedResults` / `unprocessedrecords` resources and the failed-vs-unprocessed distinction; parent-lookup-by-External-ID CSV column headers and their indexing constraint; the 300 multiple-match upsert failure
- **Salesforce Developer Limits and Allocations Quick Reference** (App Limits Cheat Sheet) — the numeric allocations quoted in the Decision Matrix and gotchas: 15,000 batches per rolling 24 hours shared across Bulk API and Bulk API 2.0; 150,000,000 records per 24 hours; 10 MB per Bulk API batch and 150 MB (base64) per Bulk API 2.0 job with a 100 MB practical ceiling; 7-day results lifespan; 24-hour maximum open job; the 2,000-record threshold above which Bulk API 2.0 is the right tool; 131,072 characters per field and 400,000 per record
- **Apex Developer Guide** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf) — API 21.0+ Bulk API trigger chunking: governor limits reset between the 200-record trigger invocations of one request but static variables do not, which is the grounding for the "Static Variables Are Not Reset" gotcha and for the Proactive Trigger on static recursion guards
- **Metadata API Developer Guide** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — the `CustomField` property table: `externalId` (returned only for AutoNumber, Email, Number, Text), `unique` and `caseSensitive` as independent booleans, and `length` for Text — the External ID field XML in `references/metadata-examples.md` §1 and the non-unique-upsert gotcha
- **Object Reference for the Salesforce Platform** (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) — `AssignmentRule` (read-only, `Active`, `SobjectType`, and the note that assignment rules can be specified when creating or upserting Cases and Leads via Bulk API) and `DuplicateRule` (`IsActive`, `sObjectType`, and the View Setup and Configuration requirement from Summer '20) behind the pre-load SOQL in `references/metadata-examples.md` §6
- **REST API Developer Guide** — sObject Collections (`/services/data/vXX.X/composite/sobjects`) as the synchronous alternative below the Bulk threshold: up to 200 records per upsert call against an external ID, `allOrNone` rollback semantics, and HTTP 300 when an external ID matches more than one record
