# Gotchas — Health Cloud APIs

Non-obvious behaviors that cause real integration failures. "HAPI guide" means the Salesforce Healthcare API developer guide at developer.salesforce.com/docs/industries/health/guide (pages Get Started, Authorization, Call the API, Considerations, FAQ, Consent), fetched 2026-10-03. "Health Dev Guide" means the Agentforce Health Developer Guide, Summer '26 (health_cloud_dev_guide.pdf).

## Gotcha 1: The Healthcare API Does Not Live Under `/services/data`

**What happens:** An integration calls `https://{instance}/services/data/v60.0/healthcare/fhir/R4/Condition` and gets a 404, or builds an entire client around that path.

**When it occurs:** The FHIR R4 Healthcare API uses its own domain and path: `<Domain name>/<FHIR module>/<FHIR version>/<API version>/<Resource type>`. The guide's examples are `api.healthcloud.salesforce.com/clinical-summary/fhir-r4/v1/Condition` for production and `api.healthcloud.salesforce.com/sandBox/clinical-summary/fhir-r4/v1/Condition` for a sandbox. Regional domains are `eu.api.healthcloud.salesforce.com`, `ca.api.healthcloud.salesforce.com`, and `au.api.healthcloud.salesforce.com`. An earlier version of this skill documented the `/services/data/vXX.0/healthcare/fhir/R4/` path; the HAPI guide does not support it.

**How to avoid:** Keep the base URL in configuration per region and environment. Use the org's `/services/data` endpoints only for the SObject API and the Business APIs. The checker flags the old path as `HC-URL-01`.

**Source:** HAPI guide, Call the API; Get Started (data centers US East, EU, CA, AU).

---

## Gotcha 2: There Is No `healthcare` Scope; Each Resource Has Custom Scopes

**What happens:** The team adds a `healthcare` scope to the app, tokens still fail against Healthcare API resources, and no one can say which scope is missing.

**When it occurs:** The HAPI guide lists OAuth custom scopes per resource and method, for example `user_condition_read OR user_all_read OR system_all_read` for `GET Condition`, `system_claim_write OR system_all_write` for `POST/PUT Claim`, and `system_bundle_read OR system_bundle_write` for `POST Bundle`. The custom scopes are created in the org and assigned to the external client app, and "you must assign the refresh_token scope to the external client app." An earlier version of this skill required a `healthcare` scope; it is not in the guide.

**How to avoid:** Map each resource and method to the narrowest scope, create the scopes (metadata type `OauthCustomScope`), and assign them with `refresh_token` to the app. Avoid `system_all_write` unless the consumer genuinely writes every resource.

**Source:** HAPI guide, Authorization (custom scopes table and refresh_token note); Metadata API Developer Guide v67.0, OauthCustomScope.

---

## Gotcha 3: Only `batch` Bundles Exist, so Nothing Rolls Back Together

**What happens:** A designer sends CarePlan plus Goals as a `transaction` Bundle expecting all-or-nothing behavior; the request is rejected, or a batch partly succeeds and leaves a CarePlan with no Goals.

**When it occurs:** "We only support Bundle type operations where the Bundle resource type is batch." An earlier version of this skill's Well-Architected notes described atomic `transaction` bundles; that is not supported.

**How to avoid:** Design every Bundle as a batch: make writes idempotent (use business identifiers), read each entry's status, and resend failed roots with their dependents. If two resources must commit together, write them through a path that is atomic on the Salesforce side, such as a Business API or the SObject API with `allOrNone`.

**Source:** HAPI guide, Get Started (Bundle).

---

## Gotcha 4: 424 Means "My Dependency Failed", Not a Separate Error

**What happens:** A bundle of 20 entries returns one validation failure and 19 entries with 424; the log shows 19 "Failed Dependency" errors and the real cause is buried.

**When it occurs:** Entries that reference another entry through a `urn:uuid:` placeholder. "In cases where a dependent action encounters an error, the API cancels the execution of any requested dependent action and returns an HTTP status reason code 424." Multi-level dependencies are supported and increase response time.

**How to avoid:** Build a dependency map from `fullUrl` placeholders to references before sending. On response, find the non-424 failures first, fix them, and resend only those roots and their dependents. Keep dependency depth shallow.

**Source:** HAPI guide, Get Started (Bundle).

---

## Gotcha 5: Thirty Entries per Call, Ten of Them Reads

**What happens:** A bundle sized like a REST Composite or Bulk batch (200 records) is rejected, or a read-heavy bundle with 15 searches fails.

**When it occurs:** "You can have up to 30 entries in a single call. Up to 10 of these entries can be read or search requests."

**How to avoid:** Chunk at 30 entries and count reads separately. For large loads into the clinical model, use the SObject API or Bulk API 2.0 instead of the Healthcare API.

**Source:** HAPI guide, Get Started (Note).

---

## Gotcha 6: Five Concurrent Requests, About Three Seconds Each

**What happens:** A parallel loader with 20 workers sees intermittent failures that disappear when rerun slowly.

**When it occurs:** "Salesforce recommends limiting the number of concurrent requests in your org to five. If you exceed this number, the API request can fail." The expected response time "is approximately 3 seconds."

**How to avoid:** Cap concurrency at five per org across all clients, add retry with backoff, and size batch windows from the three-second figure.

**Source:** HAPI guide, Considerations.

---

## Gotcha 7: The API Stores Whatever Codes You Send

**What happens:** Procedures arrive with wrong CPT codes, the API accepts them, and reporting is wrong months later.

**When it occurs:** "Salesforce doesn't support FHIR semantic validation (codeset validation). The system calling the API is expected to send the right FHIR codes."

**How to avoid:** Validate codes in the source system or middleware before the call, and name an owner for code-set quality in the integration design.

**Source:** HAPI guide, Considerations.

---

## Gotcha 8: SMART on FHIR Scope Strings Are Not Accepted

**What happens:** An EHR vendor's client requests `patient/*.read` and authorization fails.

**When it occurs:** "The format of SMART on FHIR scopes is not supported because Salesforce doesn't allow usage of wildcard characters in the OAuth Scopes."

**How to avoid:** Translate SMART scopes to the Salesforce custom scopes in the authorization table during onboarding. Route SMART app launch requirements to `apex/fhir-integration-patterns`.

**Source:** HAPI guide, Considerations.

---

## Gotcha 9: The API Is Off Until Terms, SKU, and Data Model Are in Place

**What happens:** Every call fails in a new org even though auth looks right.

**When it occurs:** Before use, an admin must "read and accept the terms and conditions of usage and enable access to Industry APIs", and the org must have the Salesforce Healthcare API SKU (a no-cost add-on for Health Cloud customers per the guide). The clinical objects also need the FHIR-Aligned Clinical Data Model org preference; Experience Cloud users need the FHIR R4 for Experience Cloud Sites permission set. The FAQ lists Winter '23 (API v56.0) as the minimum release.

**How to avoid:** Put terms, SKU, org preference, and permission sets on the go-live checklist before any build work.

**Source:** HAPI guide, Consent and FAQ; Health Dev Guide, Clinical Data Model (org pref note).

---

## Gotcha 10: Business APIs and the Healthcare API Return Different Shapes

**What happens:** Code that parses FHIR Bundles is pointed at a Business API, or vice versa, and fields come back empty.

**When it occurs:** Business APIs follow Connect REST API conventions (for example `MedStatementInputPayload` request bodies with `referenceResource` and `salesforceId` references). The Healthcare API exchanges FHIR R4 resources. The SObject API returns flat field maps.

**How to avoid:** Keep one parser per layer and name it after the layer. Never switch a client between layers without changing the parser.

**Source:** Health Dev Guide, Health Cloud Business APIs (REST Reference, Medication Statements POST).

---

## Gotcha 11: Unverified Claims Carried From an Earlier Version

**What happens:** Designs rely on behaviors that the current guides do not document.

**When it occurs:** UNVERIFIED (2026-10-03): an earlier version of this skill described a `Patient/{id}/$everything` operation and a 403 response for a missing scope. Neither appears in the fetched HAPI guide pages.

**How to avoid:** Test these against a sandbox before depending on them, and record the result here.

**Source:** None found.
