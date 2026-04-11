# Examples — Health Cloud APIs

## Example 1: Calling the FHIR Healthcare API vs. Standard SObject API

**Context:** An integration developer is building a connector between a third-party analytics platform and Salesforce Health Cloud to retrieve patient condition data. They need to determine which API to use.

**Problem:** The developer attempts to call the FHIR Healthcare API endpoint but receives a 403 Forbidden error. The Connected App was configured for the standard `api` OAuth scope only.

**Solution:**
1. Navigate to Setup > App Manager > find the Connected App used for the integration.
2. Edit the OAuth settings and add the `healthcare` scope to the selected OAuth scopes.
3. Re-authenticate to obtain a new access token that includes the `healthcare` scope.
4. Call the FHIR Healthcare API: `GET https://{instance}.salesforce.com/services/data/v60.0/healthcare/fhir/R4/Condition?patient={patientId}`
5. The response is a FHIR Bundle JSON structure containing Condition entries.
6. Parse each bundle entry to extract the clinical data.

For non-FHIR use cases (internal integrations, reporting): use the standard SObject API instead — `GET /services/data/v60.0/sobjects/HealthCondition?fields=Id,Name,PatientId` — which does not require the `healthcare` scope and returns simpler SObject JSON.

**Why it works:** The two API layers serve different use cases. FHIR Healthcare API is for FHIR-conformant interoperability (external FHIR clients, EHR integration). Standard SObject API is for internal Salesforce integrations and reporting. Choosing correctly avoids scope configuration complexity and unnecessary bundle handling overhead.

---

## Example 2: Handling HTTP 424 Errors in FHIR Bundle Operations

**Context:** A batch integration creates CarePlan and CarePlanGoal records using FHIR bundle transactions. The bundle processes but some entries return HTTP 424.

**Problem:** The CarePlan entry in the bundle failed with a validation error. All CarePlanGoal entries that reference the CarePlan via `fullUrl` returned HTTP 424 (Failed Dependency), making the error cascade confusing — the developer cannot find a 4xx error on the CarePlan entry itself.

**Solution:**
1. In bundle response processing, check all entries for HTTP 424 status.
2. Build a dependency graph: trace each 424 entry back to the bundle entry it references via `request.url` or `fullUrl`.
3. Find the root cause entry — the one with a 4xx/5xx error that is NOT 424.
4. Fix the root cause (in this case, a validation error on the CarePlan — a required field was missing).
5. Retry the full bundle after fixing the root cause.
6. Implement a circuit breaker: if a bundle returns >10% 424 errors, log the full bundle for debugging rather than retrying immediately.

**Why it works:** HTTP 424 is a dependency-failure indicator, not an independent error. Always trace 424 errors back to their root cause entry before attempting a fix. Fixing downstream 424 entries without addressing the root cause will not resolve the issue.

---

## Anti-Pattern: Using Standard SObject Endpoint for FHIR Operations

**What practitioners do:** Send FHIR R4 bundle payloads to the standard SObject endpoint (`/services/data/vXX.0/sobjects/`) expecting FHIR-conformant responses, because this is the standard Salesforce REST API endpoint.

**What goes wrong:** The standard SObject endpoint does not understand FHIR bundle JSON format. It returns an error that the request body does not match the expected SObject format, or (worse) silently ignores FHIR-specific fields and stores only fields that match the SObject schema. The response is also plain SObject JSON, not FHIR bundle format.

**Correct approach:** FHIR operations must use the FHIR Healthcare API endpoint: `/services/data/vXX.0/healthcare/fhir/R4/{ResourceType}`. Standard SObject API is for standard platform operations. Do not mix endpoints.
