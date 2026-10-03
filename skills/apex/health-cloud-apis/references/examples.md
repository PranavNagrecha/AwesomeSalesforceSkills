# Examples — Health Cloud APIs

## Example 1: Choosing Between the SObject API and the Healthcare API

**Context:** An integration developer connects a third-party analytics platform to Health Cloud to retrieve patient condition data.

**Problem:** The developer first tried `GET /services/data/v60.0/healthcare/fhir/R4/Condition` with an app that had only the `api` scope, following an outdated guide. That path is not the Healthcare API, and the analytics platform did not need FHIR at all.

**Solution:**

1. The analytics platform needs records, not FHIR resources, so it uses the SObject API with a normal org token:

```http
GET /services/data/v67.0/query?q=SELECT+Id,PatientId,ConditionSeverity+FROM+HealthCondition HTTP/1.1
Host: MyDomainName.my.salesforce.com
Authorization: Bearer <org access token>
```

2. A separate EHR feed that does need FHIR R4 uses the Healthcare API host and a token whose app holds `system_condition_read` (or `user_condition_read`) plus `refresh_token`:

```http
GET /clinical-summary/fhir-r4/v1/Condition HTTP/1.1
Host: api.healthcloud.salesforce.com
Authorization: Bearer <access token issued to the external client app>
Accept: application/fhir+json
```

UNVERIFIED (2026-10-03): the `Accept: application/fhir+json` header and the search parameters a Condition read accepts are not shown in the fetched guide pages; check the Healthcare API reference for the Clinical Summary module.

**Why it works:** Each consumer uses the layer that matches its contract. The analytics feed avoids custom scopes, regional hosts, and bundle limits; the EHR feed gets FHIR R4 resources from the documented host.

---

## Example 2: Handling HTTP 424 in a Batch Bundle

**Context:** A nightly job writes CarePlan and Goal resources through a `batch` Bundle. Some entries return 424.

**Problem:** The CarePlan entry failed validation. Every Goal entry that referenced the CarePlan through its `urn:uuid:` placeholder was cancelled with 424, so the log shows many "Failed Dependency" lines and one real error.

**Solution:**

1. Before sending, record each entry's `fullUrl` placeholder and which entries reference it.
2. On the response, list the entries whose status is not 2xx and not 424; these are the root failures.
3. Fix the root cause (here, a missing required CarePlan field).
4. Resend only the failed root and the entries that depended on it. Entries that succeeded are already committed, because the API supports only `batch` bundles.
5. If more than a small share of a run returns 424, stop the run and alert, rather than retrying blindly.

**Why it works:** A 424 is the API telling you it cancelled a dependent action. Fixing the root and resending only what failed avoids duplicate writes.

---

## Anti-Pattern: Using the SObject Endpoint for FHIR Payloads

**What practitioners do:** Send FHIR R4 Bundle JSON to `/services/data/vXX.X/sobjects/` expecting FHIR handling.

**What goes wrong:** The SObject endpoint expects SObject field maps. It rejects the body or stores only fields that happen to match the SObject schema, and the response is SObject JSON, not FHIR.

**Correct approach:** Send FHIR payloads to the Healthcare API host (`https://api.healthcloud.salesforce.com/{module}/fhir-r4/v1/{Resource}`, or the regional and sandbox variants). Use the SObject API for records and the Business APIs under `/connect/health` for business operations.

See [`healthcare-api-examples.md`](healthcare-api-examples.md) for the deployable scope metadata and complete request bodies.
