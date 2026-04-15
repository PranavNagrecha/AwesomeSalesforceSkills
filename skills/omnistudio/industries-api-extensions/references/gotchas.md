# Gotchas — Industries API Extensions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: TM Forum API Is ID-Driven — Product Names and External Codes Are Silently Ignored or Return 404

**What happens:** A TMF679 or TMF622 request body that uses a product name, offering code, or external catalog identifier in the `productOffering` or `productSpecification` fields either returns HTTP `404 Not Found` or processes the request without matching any actual product, resulting in a generic error response or an empty qualification result.

**When it occurs:** Any time an external BSS system constructs TM Forum payloads using catalog codes, ERP item numbers, or human-readable product names rather than Salesforce record IDs. Teams migrating from non-Salesforce catalog systems frequently run into this because their existing TM Forum integration with other platforms used name or code as the primary key.

**How to avoid:** Implement an ID-resolution step before constructing any TM Forum request. Use a SOQL query or a dedicated catalog lookup endpoint to map the external product code to the Salesforce `ProductOffering__c.Id`. Cache the mapping for short periods (minutes, not hours) to avoid stale ID references after catalog updates. Never pass a product name or external code as the `id` value in a TM Forum JSON body.

---

## Gotcha 2: MuleSoft Gateway Deprecation Is a Silent Connectivity Break, Not an API Version Error

**What happens:** When the MuleSoft gateway path for Communications Cloud TM Forum APIs is removed after the Winter '27 deprecation date, requests routed through the old gateway URL fail with a network-level connection error or a generic `503 Service Unavailable`, not a Salesforce API error with a clear deprecation message. Monitoring systems that check for Salesforce error codes may not flag the outage as a Salesforce issue.

**When it occurs:** Any Communications Cloud implementation that still uses the MuleSoft gateway URL for TM Forum API calls as of Winter '27. Organizations that integrated before Direct Access was generally available are at highest risk because the MuleSoft path was the only option available to them at integration time.

**How to avoid:** Audit all Communications Cloud API integrations now. Check whether the TM Forum endpoint URL in use includes a MuleSoft gateway hostname or the standard Salesforce instance URL. Direct Access endpoints use the org's `my.salesforce.com` instance domain. If the integration routes through a separate MuleSoft org or gateway URL, it is on the deprecated path. Migrate to Direct Access before Winter '27. Test by verifying that Direct Access is enabled in Setup > Communications Cloud API settings, and update all hardcoded gateway URLs.

---

## Gotcha 3: Insurance Connect API Rollback Means No Partial Success — But Also No Diagnostic Record

**What happens:** When the Insurance Policy Business Connect API returns a failure (non-2xx), the entire transaction is rolled back. This is correct behavior, but it means there is no `InsurancePolicy` record to inspect for diagnosis. Practitioners who check for the policy record after a failed call and find nothing sometimes conclude the API call was never received or that a network error occurred, when the actual failure was a payload validation error.

**When it occurs:** During integration testing or debugging when the request payload has a missing required field (such as an invalid `productId` or a `coverageType` value not configured in the org's Insurance Cloud setup). The API returns a descriptive error body, but developers look at the database rather than the HTTP response body.

**How to avoid:** Always read the full HTTP response body on non-2xx responses from Insurance Connect API calls. The error body contains a structured message that identifies the failing validation rule. Do not look for orphaned records in the database as a debugging strategy — the rollback guarantees they do not exist. Use the Connect API error body as the primary diagnostic source. Log the full response including status code and body in integration middleware for all non-2xx outcomes.

---

## Gotcha 4: E&U Integration Procedure Version Must Match the Installed Package Version

**What happens:** In managed package (non-native) E&U Cloud orgs, the `sfiEnergy_UpdateAssetStatus` Integration Procedure exists in multiple versions. If the org is running an older managed package version, the `POST /connect/energy/asset-status-updates` endpoint may delegate to a different IP version than expected, or the endpoint may not exist at all if the package version predates Direct Connect API support.

**When it occurs:** During upgrades or when a sandbox is refreshed from a production org that is on a different package version than the sandbox's installed version. The Connect API endpoint version and the active IP version must align.

**How to avoid:** Before implementing E&U API integrations, verify the installed Energy and Utilities Cloud package version in Setup > Installed Packages. Confirm the Connect API endpoint is documented for that package version in the E&U release notes for that release. After a package upgrade, re-test the endpoint against a refreshed sandbox before deploying to production.

---

## Gotcha 5: Service Process Studio Connect API Output Schema Is Dynamic — Not Fixed at the Endpoint Level

**What happens:** The response body from a Service Process Studio Connect API call (`POST /connect/service-processes/{processApiName}/runs`) varies per process definition. There is no fixed response schema at the endpoint level. A consuming system that hardcodes field names from a response it saw in one environment may silently fail when the process definition is updated, because the output parameter names or structure may change.

**When it occurs:** When a Service Process definition is modified (output parameters renamed, added, or removed) and the consuming integration is not updated to match. The API does not return a schema-change error; it returns the updated response shape. Consumers relying on the old field names receive empty or null values.

**How to avoid:** Treat the Service Process Connect API response as contract-driven. Version the process API name when making breaking output changes (e.g., `myProcessV2` vs `myProcess`). Document the expected output schema in the integration middleware and include a contract test that validates response shape after any process definition change. Do not assume output field stability across Service Process definition updates.
