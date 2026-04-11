# Well-Architected Notes — Constituent Data Migration

## Relevant Pillars

- **Trustworthiness** — Constituent data is the core asset of a nonprofit Salesforce org. Household rollup fields, giving histories, and relationship records are used for major gift strategy, grant reporting, and board-level metrics. A corrupted import that bypasses NPSP triggers produces silently wrong data — rollups show zero even when donations exist — that can persist for months before detection. Data integrity is the primary pillar for this skill.
- **Reliability** — The migration process must be repeatable and recoverable. Large migrations should be chunked, monitored, and verifiable at each stage. Failed rows must be identifiable and re-importable without creating duplicates. Staging in `npsp__DataImport__c` provides a natural checkpoint between data load and processing.
- **Security** — Constituent records include personally identifiable information (PII): names, emails, addresses, and giving history. Migration workflows must restrict access to `npsp__DataImport__c` to authorized staff only. Staging files containing donor PII must not be stored in unsecured locations. Field-level security on sensitive Contact fields should be reviewed before import.
- **Operational Excellence** — The correct import path (`BDI_DataImport` batch class via NPSP Data Importer) is more complex than direct Data Loader use, but it is operationally superior: it provides a per-row status field (`npsp__Status__c`), an error message field (`npsp__ImportedDate__c`), and a UI results screen. These observability features make post-import validation and error remediation tractable at scale.
- **Performance** — Apex CPU time limits and batch size constraints require careful configuration for large migrations. The NPSP Data Importer batch size must be tuned to prevent CPU limit errors on complex rows. Very large migrations (100k+ records) should be chunked into separate import runs to avoid SOQL query limit errors within a single batch transaction.

## Architectural Tradeoffs

**Staging-then-process vs. direct API insert:**
Staging to `npsp__DataImport__c` adds a step but is the only path that preserves NPSP data integrity. Direct Contact insertion is faster to set up but produces unfixable data corruption without a full re-import. Always choose the staging path.

**NPSP Data Importer UI vs. programmatic BDI_DataImport invocation:**
The UI is appropriate for one-time or occasional migrations. Programmatic invocation (`Database.executeBatch(new BDI_DataImport(...))`) is appropriate for recurring automated pipelines. Both paths invoke the same `BDI_DataImport` code and produce the same data quality outcomes.

**Contact Matching Rule strictness:**
Loose matching reduces duplicates but risks merging distinct individuals. Strict matching preserves uniqueness but may create duplicates for constituents with identical names. Tune the matching rule on a pilot batch before committing to full migration. There is no universally correct setting — it depends on org data quality and constituent naming patterns.

## Anti-Patterns

1. **Direct Contact insertion via Data Loader** — Bypasses NPSP triggers, produces orphaned households and stale rollups. The speed gain is illusory; remediation costs far exceed the time saved.
2. **Using the standard Salesforce Data Import Wizard for NPSP orgs** — The wizard is designed for standard Salesforce orgs. It has no awareness of NPSP's household model, does not invoke TDTM, and should never be used for constituent records in NPSP.
3. **Loading all migration data in a single giant batch run** — Without chunking, a single failed batch transaction can fail thousands of rows atomically. Chunking into smaller runs limits blast radius and enables faster retry of error rows.

## Official Sources Used

- NPSP Documentation Overview — https://powerofus.force.com/s/article/NPSP-Overview (NPSP Data Importer behavior, npsp__DataImport__c staging object, Contact Matching Rules)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (architecture quality framing)
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm (staging record load via API)
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm (sObject semantics and field behavior)
