# Well-Architected Notes — Data Loader CSV Column Mapping

## Relevant Pillars

- **Reliability** — every load that silently drops a column because of FLS, case mismatch, or polymorphic ambiguity is a data-quality incident waiting to surface in a downstream report. Reliability of CSV loading is bound by the strictness of pre-load validation: a job with `state: JobComplete` is necessary but not sufficient evidence of data correctness.
- **Operational Excellence** — mappings authored ad hoc through a UI cannot be diffed, versioned, or replayed. `.sdl` files (Data Loader) and equivalent JSON config (Bulk V2 callers) make CSV loads behave like deployable artefacts. Pair with a pre-load checker run in CI and a post-load diff query in the runbook.
- **Cost Optimization** — failed and silently-corrupted loads are pure waste: API calls consumed, processing time spent, and remediation effort burned to detect and fix the corruption. Salesforce per-org daily API limits (15K + 1K per licence; Bulk V2 batches do not count as individual API calls but the job creation and status polls do) make repeated re-loads expensive. Map once, validate once, load once.
- **Security** — every CSV column is a write path. FLS, profile-level field permissions, and CRUD on the target object all gate whether the column actually writes. A user with FLS `Read-Only` on a field will load that field as null and the job will report success. Any production load runbook must include an FLS pre-check on the loading user.
- **Performance** — pre-resolving lookup IDs via per-row SOQL before the load is the dominant performance cost in many migrations. External-ID upsert binding (`Account.External_Account_Id__c` headers) shifts that resolution into the bulk job itself, where it parallelises across batches and avoids the per-row API call.
- **Scalability** — CSVs that work at 100 rows often break at 100K rows because the failure modes change. Bulk V2 errors per-batch, not per-row; a single bad polymorphic header errors out an entire 10K-row batch. The pre-load checker becomes more valuable as scale grows.

## Architectural Tradeoffs

- **`.sdl` mapping file vs in-tool mapping** — `.sdl` adds an artefact to maintain but makes the load reproducible. For one-off admin tasks, the UI mapping is fine. For any scheduled or repeatable load, the `.sdl` is mandatory.
- **External ID upsert vs pre-resolved IDs** — upsert binding via External ID column shifts complexity from the loader (no SOQL needed) to data hygiene (External ID fields must be `Unique = true`). For most production data, the upsert path wins; for one-off backfills with messy External IDs, pre-resolution is safer.
- **Bulk V1 (with `#N/A`) vs Bulk V2 (no null sentinel)** — V1's `#N/A` and "Insert Null Values" checkbox give finer control; V2's blank-cell-equals-null rule is simpler but less expressive. New pipelines should default to V2 for throughput and modern endpoint support; legacy migrations relying on `#N/A` semantics need explicit V1 selection in Data Loader settings.
- **Per-row pre-resolution of Record Type vs caching at pipeline level** — if RecordTypeId is needed in many loads, a pipeline-level cache (one SOQL query, served from memory for the run) beats per-row resolution. The cost is staleness — invalidate the cache on Record Type metadata deploys.
- **Lock the CSV to the strictest tool's rules vs maintaining per-tool variants** — authoring a single CSV that satisfies Bulk V2 (the strictest) means it works everywhere, at the cost of more upfront discipline. Per-tool variants drift and break when one is updated and others are not.

## Anti-Patterns

1. **Trusting `JobComplete` as proof of correctness** — Bulk V2 says the rows were accepted, not that every column you mapped wrote a value. FLS, case mismatches, and polymorphic ambiguity all produce green jobs with missing data. Always run a post-load diff query.
2. **Hand-curating a "required fields" list from setup screenshots** — required-ness is the union of `nillable`, `defaultedOnCreate`, `createable`/`updateable`, validation rules, master-detail relationships, and active record types. Pull it from describe; do not transcribe from screenshots.
3. **Mapping CSV columns by visual similarity** — `Date` matches more than one date-typed field on most objects. Always use the exact field API name in the header.
4. **Using picklist labels instead of API names** — works in unrestricted picklists, silently writes labels, breaks every downstream filter. Always translate labels to API names pre-load.
5. **Reusing a Data Loader CSV in a Bulk V2 pipeline without re-validation** — the case-insensitivity tolerance of Data Loader hides bugs that V2 surfaces. The CSV must be re-validated against V2 rules before the migration.
6. **Loading polymorphic lookups by Salesforce Id without External ID columns** — couples the CSV producer to Salesforce, forces per-row pre-resolution, and makes the load non-idempotent. Use type-explicit External ID columns.
7. **Leaving the column present-but-blank to "use the default"** — the field default does not fire for blank cells. Drop the column from the CSV entirely if you want the default to apply.

## Official Sources Used

- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- Bulk API 2.0 Ingest CSV Format — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/datafiles_csv_valid.htm
- Bulk API 2.0 Ingest Job CRUD — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/walkthrough_upload_data.htm
- Data Loader Guide — https://help.salesforce.com/s/articleView?id=sf.data_loader.htm&type=5
- Data Loader Field Mapping (`.sdl`) — https://help.salesforce.com/s/articleView?id=sf.loader_field_mapping.htm&type=5
- SOAP API Developer Guide — DescribeSObjectResult — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_describesobjects_describesobjectresult.htm
- External ID and Upsert — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_upsert.htm
- Polymorphic Foreign Keys — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/datafiles_polymorphic_relationships.htm
- Workbench (Data Manipulation) — https://help.salesforce.com/s/articleView?id=000384982&type=1
- Date Formats and Time Zones in Bulk API — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/datafiles_date_format.htm
