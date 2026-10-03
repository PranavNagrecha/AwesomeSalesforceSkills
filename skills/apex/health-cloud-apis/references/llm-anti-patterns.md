# LLM Anti-Patterns — Health Cloud APIs

Common mistakes AI coding assistants make when generating or advising on Health Cloud API usage. Facts cite the Salesforce Healthcare API guide (developer.salesforce.com/docs/industries/health/guide) and the Agentforce Health Developer Guide, Summer '26.

## Anti-Pattern 1: Putting the FHIR API under `/services/data`

**What the LLM generates:** `GET https://{instance}.my.salesforce.com/services/data/v60.0/healthcare/fhir/R4/Condition/{id}`.

**Why it happens:** Every other Salesforce REST API sits under `/services/data`, so the model extrapolates. An earlier version of this skill made the same mistake.

**Correct pattern:** The Healthcare API URL format is `<Domain name>/<FHIR module>/<FHIR version>/<API version>/<Resource type>`, for example `https://api.healthcloud.salesforce.com/clinical-summary/fhir-r4/v1/Condition`; sandboxes insert `/sandBox/` after the host, and EU, CA, and AU orgs use `eu.`, `ca.`, or `au.` prefixed hosts. Keep `/services/data/vXX.X/sobjects/...` for records and `/services/data/vXX.X/connect/health/...` for Business APIs.

**Detection hint:** A URL containing both `/services/data/` and `fhir`.

---

## Anti-Pattern 2: Inventing a `healthcare` OAuth scope

**What the LLM generates:** An app configuration with `api healthcare refresh_token` scopes, and advice that the `healthcare` scope unlocks all FHIR calls.

**Why it happens:** Scope names like `api` and `refresh_token` are well known, and the model invents a matching name for the product.

**Correct pattern:** The Healthcare API uses OAuth custom scopes per resource and method, for example `user_condition_read`, `system_carePlan_write`, `system_bundle_write`, created in the org and assigned to the external client app. The app must also have the `refresh_token` scope.

**Detection hint:** The literal scope string `healthcare` in app metadata, token requests, or setup instructions.

---

## Anti-Pattern 3: Sending FHIR Bundles larger than 30 entries

**What the LLM generates:** Chunking logic that groups 200 resources per Bundle because that is the familiar Salesforce collection size.

**Why it happens:** REST Composite and sObject Collections limits are common knowledge; the Healthcare API limit is not.

**Correct pattern:** At most 30 entries per call, and at most 10 of them read or search requests. Chunk on both counts.

**Detection hint:** A bundle chunk size constant greater than 30, or a Bundle JSON array with more than 30 entries.

---

## Anti-Pattern 4: Treating 424 entries as independent errors

**What the LLM generates:** Retry logic that resends each 424 entry on its own, or logs 424s as separate failures.

**Why it happens:** 424 is rare outside WebDAV, so the model applies generic 4xx handling.

**Correct pattern:** 424 means the entry depended on another entry that failed, so the API cancelled it. Find the non-424 root failure, fix it, then resend the root and its dependents. Because only `batch` bundles exist, entries that succeeded are already committed; do not resend them.

**Detection hint:** Retry code that filters on status 424 without first locating the referenced entry.

---

## Anti-Pattern 5: Using the FHIR API for internal, high-throughput work

**What the LLM generates:** An internal analytics feed that reads clinical data through the Healthcare API because the data is clinical.

**Why it happens:** The model associates clinical data with FHIR by default.

**Correct pattern:** Use the SObject API or Bulk API 2.0 for internal consumers. The Healthcare API is capped at 30 entries per bundle, Salesforce recommends at most five concurrent requests, and typical response time is about three seconds.

**Detection hint:** An internal consumer with no FHIR conformance requirement calling `api.healthcloud.salesforce.com`.

---

## Anti-Pattern 6: Promising atomic `transaction` bundles

**What the LLM generates:** `{"resourceType": "Bundle", "type": "transaction", "entry": [...]}` with a claim that CarePlan and Goals commit together.

**Why it happens:** FHIR R4 defines `transaction` bundles and the model assumes every server implements them.

**Correct pattern:** The Healthcare API supports only Bundle type `batch`. Design for partial success, or use a Salesforce-side atomic path (a Business API or the SObject API with `allOrNone`) when resources must commit together.

**Detection hint:** `"type": "transaction"` in any Bundle sent to the Healthcare API.

---

## Anti-Pattern 7: Passing SMART on FHIR wildcard scopes through unchanged

**What the LLM generates:** An onboarding guide that tells an EHR vendor to request `patient/*.read` or `system/*.*`.

**Why it happens:** SMART scopes are the FHIR ecosystem default.

**Correct pattern:** The Healthcare API guide says SMART on FHIR scope formats are not supported because Salesforce does not allow wildcard characters in OAuth scopes. Map each SMART scope to the specific Salesforce custom scopes.

**Detection hint:** Scope strings containing `/*.` in configuration for the Healthcare API.
