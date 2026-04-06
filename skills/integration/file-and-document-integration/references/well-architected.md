# Well-Architected Notes — File And Document Integration

## Relevant Pillars

- **Security** — File uploads are an attack vector. Salesforce has no built-in virus scanning for CRM uploads, so organizations must implement external callout-based scanning. File sharing via ContentDocumentLink ShareType must be explicitly controlled to prevent unintended data exposure. Named Credentials should be used for all external service authentication (scanning APIs, external storage).

- **Reliability** — Asynchronous virus scanning introduces a window where unscanned files are accessible. The scanning Queueable must handle callout failures gracefully — retry logic, dead-letter tracking, and alerting on persistent failures. File upload integrations must handle `STORAGE_LIMIT_EXCEEDED` and `REQUEST_ENTITY_TOO_LARGE` errors without silent data loss.

- **Scalability** — File storage consumption scales with record volume. Organizations with high-volume file integrations must monitor storage allocation proactively. Querying VersionData in bulk hits Apex heap limits — batch processing must use scope size 1. REST multipart upload supports 2 GB per file but imposes network throughput requirements on the integration infrastructure.

- **Performance** — Base64 encoding inflates payload by 33%, wasting bandwidth and increasing upload time. Multipart upload is the performant path for files over a few MB. Files Connect avoids storage consumption entirely by virtualizing external file access, but introduces latency dependent on the external system's response time.

- **Operational Excellence** — File integrations require monitoring for storage consumption trends, scanning failure rates, and upload error patterns. The Scan_Status__c field pattern provides operational visibility into the virus scanning pipeline. External Data Source configuration for Files Connect must be maintained as external system authentication changes.

## Architectural Tradeoffs

### Store in Salesforce vs. Surface from External System

Storing files as ContentVersion provides full Salesforce-native search, preview, versioning, and sharing — but consumes file storage allocation. Surfacing files via Files Connect avoids storage consumption and keeps the external system as the source of truth — but is read-only, adds latency, and requires ongoing External Data Source maintenance. The choice depends on whether users need to collaborate on files within Salesforce or simply reference them.

### Synchronous vs. Asynchronous Virus Scanning

Synchronous scanning (blocking the upload until scan completes) would be ideal for security but is architecturally impossible in Salesforce — trigger-context callouts require async patterns. The Queueable approach creates a brief accessibility window for unscanned files. Mitigations include: restricting file download via a custom check on Scan_Status__c in a before-download trigger or Flow, or quarantining files in a restricted Library until scan completes.

### Base64 vs. Multipart Upload

Base64 is simpler to implement — it is a standard sObject insert with a Blob field. Multipart is more complex but supports files up to 2 GB and avoids encoding overhead. For integrations where file size is unpredictable or could grow, multipart is the only forward-compatible choice. For integrations where files are guaranteed small (profile images, icons), base64 is acceptable.

## Anti-Patterns

1. **Using Attachment instead of ContentVersion** — The Attachment object is legacy. It lacks versioning, sharing granularity, preview support, and modern Lightning integration. New implementations should always use ContentVersion. Migrating from Attachment to ContentVersion later is a data migration project.

2. **Assuming Salesforce scans uploaded files for viruses** — This is a dangerous assumption with compliance implications. Salesforce does not scan CRM-uploaded files. Organizations in regulated industries (financial services, healthcare) must implement external scanning or risk audit findings.

3. **Querying VersionData in bulk without heap-size awareness** — Loading multiple file binaries into memory simultaneously causes heap limit exceptions. File processing must be chunked to one record at a time in async contexts.

## Official Sources Used

- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference (ContentVersion, ContentDocument, ContentDocumentLink) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Apex Developer Guide (callout and async patterns) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
