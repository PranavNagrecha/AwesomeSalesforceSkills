# Well-Architected Notes — FSC Document Generation

## Relevant Pillars

- **Security** — Compliance document workflows in FSC handle regulated financial data (account balances, investment positions, client PII). OmniStudio DocGen must be scoped to run under an Apex service class that enforces `with sharing` where appropriate, and DocGen permission set licenses must be granted at the minimum-necessary level (Runtime for automated jobs, User for manual triggers, Designer only for template authors). ContentDocument sharing must be explicitly controlled via `ContentDocumentLink` — overly permissive visibility settings can expose client financial statements to unauthorized portal users. Document Builder must be excluded from any workflow involving PCI-in-scope data given its explicit exclusion from Salesforce's PCI DSS compliance attestation.

- **Reliability** — The DocGen API enforces a hard server-side cap of 1000 documents per hour per org. Batch account statement jobs must be designed with chunked processing (200 records per batch execution), explicit HTTP response-code handling, and retry logic for rate-limit rejections (429/503). Partial batch completions caused by hitting the cap without error handling are a known failure mode. Every compliance document workflow must write an `AuthorizationFormConsent` record as an atomic post-generation step — if this write fails, the workflow should roll back or alert, not silently complete without a compliance record.

- **Operational Excellence** — Nightly statement runs, disclosure delivery jobs, and compliance record writes must produce observable audit artifacts: a `StatementRun__c` (or equivalent) log record per batch execution, per-document error flags, and query-accessible `AuthorizationFormConsent` status fields. Compliance officers must be able to pull a SOQL report of all disclosures delivered in a date range without engineering support. Template version management must use OmniStudio DocGen's built-in versioning — hotfixes to live disclosure templates require documented change control aligned with regulatory approval workflows.

## Architectural Tradeoffs

**OmniStudio DocGen vs Document Builder:** DocGen has a steeper setup cost (DataRaptor design, template authoring in DocGen Designer, permission set license management) but is the only FSC-supported option for PCI-in-scope or FINRA-governed documents. Document Builder is faster for non-compliance use cases but must not be used where Salesforce's PCI DSS compliance attestation matters. Choosing Document Builder for speed and later discovering the compliance gap requires a full rebuild.

**Interactive OmniScript Delivery vs Batch API:** Interactive delivery via OmniScript is appropriate for onboarding and annual review workflows where a human advisor triggers the document. Batch API generation via Apex is necessary for any multi-account statement run. The two patterns are not interchangeable — OmniScript requires a user session and is not suitable for headless scheduled processing.

**AuthorizationFormConsent Granularity:** A single `AuthorizationForm` can have many `AuthorizationFormConsent` records (one per contact delivery event). Over years, high-volume disclosure workflows can accumulate millions of consent records. Archive or big-object offload strategy must be planned from day one for orgs with 50,000+ clients and annual disclosure cycles, to prevent SOQL performance degradation on consent queries.

## Anti-Patterns

1. **Treating DocGen as a standalone feature without compliance record writes** — Generating and storing a PDF without writing an `AuthorizationFormConsent` record means the workflow cannot prove regulatory disclosure delivery. This is the most common FSC document generation anti-pattern: technically functional, compliance-incomplete. Every automated disclosure workflow must include the consent record write as a non-optional step.

2. **Using Document Builder for FSC compliance documents** — Document Builder is excluded from Salesforce's PCI DSS compliance scope. Using it for account statements, disclosures, or any document containing regulated financial data creates a compliance gap that is difficult to audit and expensive to remediate after the fact.

3. **Missing rate-limit handling in DocGen batch callouts** — Batch Apex that calls the DocGen API without inspecting HTTP response codes and implementing back-off/retry will silently drop documents when the 1000/hour cap is hit. The job shows success but thousands of clients have no statement. Always handle 429 and 503 responses explicitly.

## Official Sources Used

- FSC Admin Guide — Document Generation Overview — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_doc_gen.htm
- OmniStudio DocGen Foundations (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/omnistudio-document-generation-foundations
- Disclosures and Consent Management in FSC (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/fsc-disclosures-and-consent-management
- Personas and Permission Set Licenses for OmniStudio DocGen — https://help.salesforce.com/s/articleView?id=sf.os_docgen_permission_set_licenses.htm
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
