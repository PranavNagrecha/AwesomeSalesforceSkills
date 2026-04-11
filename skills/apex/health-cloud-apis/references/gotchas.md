# Gotchas — Health Cloud APIs

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `healthcare` OAuth Scope Required for FHIR Healthcare API

**What happens:** All FHIR Healthcare API requests return HTTP 403 Forbidden even with a valid access token and correct endpoint.

**When it occurs:** When the Connected App used for FHIR Healthcare API calls is configured with only the standard `api` OAuth scope, without the `healthcare` scope. This is easy to miss because the `api` scope works for all other Salesforce API endpoints.

**How to avoid:** For any integration using the FHIR Healthcare API (`/services/data/vXX.0/healthcare/fhir/R4/`), explicitly add the `healthcare` scope to the Connected App OAuth settings. After updating the scope, existing access tokens must be regenerated — cached tokens will still be rejected until they expire and are replaced.

---

## Gotcha 2: FHIR Bundle Limit Is 30 Entries (Not the Standard API Batch Limit)

**What happens:** FHIR bundle requests with more than 30 entries are rejected with an error indicating the bundle exceeds the maximum allowed size, even though standard SObject collections support up to 200 records.

**When it occurs:** When developers assume FHIR bundle limits match standard Salesforce API batch limits (200 for Bulk API, 200 for composite API). The FHIR Healthcare API has its own 30-entry bundle limit.

**How to avoid:** Implement bundle chunking for all FHIR batch operations: split the operation into bundles of maximum 30 entries. Additionally, limit read/search operations within a bundle to 10 per bundle. Build a generic chunking utility rather than hardcoding bundle sizes in each integration.

---

## Gotcha 3: HTTP 424 Errors Cascade from Root Bundle Entry Failures

**What happens:** A bundle with 20 entries has 1 root failure and 19 HTTP 424 failures. The error log appears to show 19 errors of type "Failed Dependency" but the real cause is a single validation error on the first entry.

**When it occurs:** When FHIR bundles include dependent resources (e.g., CarePlan + all CarePlanGoals + all CarePlanTasks in one bundle). If the CarePlan entry fails, all dependent entries return 424 rather than a descriptive error.

**How to avoid:** Always scan bundle responses for HTTP 424 before attempting to debug individual entry failures. Build a dependency resolver: map each 424 entry to the bundle entry it references, find the root non-424 failure, fix it, and retry. Log the full bundle request and response for debugging.

---

## Gotcha 4: FHIR Healthcare API and Standard SObject API Return Different Response Formats

**What happens:** Code that uses the FHIR Healthcare API endpoint expects SObject JSON and incorrectly parses the FHIR bundle response, or vice versa. The data appears incorrect or missing even though the API call succeeded.

**When it occurs:** When integration code switches between API layers without updating the response parser, or when copy-pasted code from a non-FHIR integration is adapted for a FHIR use case.

**How to avoid:** Build separate response parsers for each API layer. FHIR Healthcare API returns FHIR Bundle JSON (`resourceType: "Bundle"`, entries array with `resource` objects). Standard SObject API returns SObject JSON (flat field map). Never reuse the same parser for both.
