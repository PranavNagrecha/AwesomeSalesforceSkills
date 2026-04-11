# LLM Anti-Patterns — Health Cloud APIs

Common mistakes AI coding assistants make when generating or advising on Health Cloud API usage.

## Anti-Pattern 1: Treating FHIR Healthcare API as Interchangeable with Standard SObject API

**What the LLM generates:** Code that calls `/services/data/vXX.0/sobjects/HealthCondition` expecting FHIR R4 bundle responses, or code that sends FHIR bundle JSON to the standard SObject endpoint.

**Why it happens:** LLMs know that Health Cloud uses both FHIR R4 objects and standard SObjects. Without knowing the distinct API endpoints for each layer, they conflate them into a single API surface.

**Correct pattern:**
Standard SObject endpoint: `/services/data/vXX.0/sobjects/HealthCondition/{id}` — returns SObject JSON, no FHIR formatting, no `healthcare` scope required. FHIR Healthcare API: `/services/data/vXX.0/healthcare/fhir/R4/Condition/{id}` — returns FHIR R4 resource JSON, requires `healthcare` OAuth scope.

**Detection hint:** If code uses the `/sobjects/` path with FHIR bundle parsing, or uses the `/healthcare/fhir/R4/` path expecting SObject JSON, the endpoints are being mixed.

---

## Anti-Pattern 2: Omitting `healthcare` OAuth Scope for FHIR Healthcare API

**What the LLM generates:** Connected App configuration or OAuth flow code that requests only the `api` scope for FHIR Healthcare API calls.

**Why it happens:** The `api` scope covers almost all Salesforce API operations. LLMs recommend it as the default scope for any Salesforce API integration without knowing the FHIR-specific `healthcare` scope requirement.

**Correct pattern:**
FHIR Healthcare API calls require the `healthcare` scope in addition to the `api` scope. Connected Apps used for FHIR Healthcare API must explicitly include `healthcare` in the OAuth scope list. Without it, all FHIR Healthcare API requests return HTTP 403.

**Detection hint:** If the Connected App configuration or token request includes `api` but not `healthcare` for an integration using FHIR Healthcare API endpoints, the scope is missing.

---

## Anti-Pattern 3: Sending FHIR Bundles Larger Than 30 Entries

**What the LLM generates:** Batch clinical data processing code that assembles FHIR bundles based on the standard Salesforce API limit (200 records) rather than the FHIR Healthcare API bundle limit (30 entries).

**Why it happens:** Standard Salesforce API collection limits (200 for REST composite, 200 for Bulk API) are well-known. The FHIR Healthcare API bundle limit (30 entries) is a FHIR-specific constraint not inferrable from general Salesforce API knowledge.

**Correct pattern:**
FHIR Healthcare API bundles are limited to 30 entries maximum, with a sub-limit of 10 read/search operations per bundle. Bulk clinical data operations must implement bundle chunking: split operations into batches of max 30 entries. Also limit read/search operations to 10 per bundle.

**Detection hint:** If batch processing code divides operations into chunks based on 200 (or any number > 30) for FHIR bundle operations, the FHIR bundle limit is not being respected.

---

## Anti-Pattern 4: Ignoring HTTP 424 Dependency Failures

**What the LLM generates:** Bundle response handling code that treats all 4xx responses as independent errors, logs the HTTP 424 responses as distinct failures, and attempts to retry each 424 entry independently.

**Why it happens:** HTTP 424 is an uncommon status code. LLMs handle it with generic 4xx error handling patterns without knowing its specific meaning in FHIR bundle context (a dependency on a failed entry).

**Correct pattern:**
HTTP 424 means "the entry I reference in this bundle failed." Retry logic must: (1) identify the root non-424 failure, (2) fix the root cause, (3) retry the full bundle. Retrying individual 424 entries without fixing the root cause will always produce the same 424 result.

**Detection hint:** If error handling code counts or logs HTTP 424 as a distinct error category without tracing it back to the root bundle entry failure, the dependency semantics are being ignored.

---

## Anti-Pattern 5: Using FHIR Healthcare API for High-Throughput Internal Operations

**What the LLM generates:** Internal Salesforce-to-Salesforce integrations (e.g., cross-org sync, analytics data feeds) that use the FHIR Healthcare API because the data is clinical, even when FHIR compliance is not required.

**Why it happens:** LLMs associate clinical Health Cloud data with FHIR and recommend FHIR Healthcare API for all clinical data operations. The performance implications of bundle limits vs. standard API throughput are not considered.

**Correct pattern:**
For internal integrations and analytics pipelines where FHIR R4 conformance is not required, use the standard SObject REST or Bulk API. The FHIR Healthcare API has lower throughput (30-entry bundles vs. 200-record Bulk API batches) and should be used only where FHIR R4 conformance is a requirement (external FHIR clients, EHR interoperability).

**Detection hint:** If the integration is internal (Salesforce to Salesforce or Salesforce to an internal analytics system) and uses FHIR Healthcare API without a FHIR conformance requirement, the API layer choice is unnecessarily constraining throughput.
