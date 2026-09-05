# LLM Anti-Patterns — API Contract Documentation

Common mistakes AI coding assistants make when generating or advising on Salesforce API contract documentation.

---

## Anti-Pattern 1: Fabricating Specific Numeric Rate Limits

**What the LLM generates:** "Salesforce allows 15,000 API calls per day for Enterprise Edition."

**Why it happens:** LLMs have seen various Salesforce limit numbers in training data without knowing they are dynamic, org-specific values.

**The correct pattern:** API request limits vary by org edition and add-on licenses. Never document a hardcoded number. Always retrieve the actual limit from `GET /services/data/vXX.0/limits` (returns `DailyApiRequests.Max`) or reference the Salesforce Developer Limits Quick Reference cheatsheet.

**Detection hint:** Any specific numeric daily API limit in documentation without a source from the `/limits` resource or official cheatsheet is unverified and potentially wrong.

---

## Anti-Pattern 2: Assuming OpenAPI Beta Covers All APIs

**What the LLM generates:** "Use the Salesforce OpenAPI beta endpoint to generate documentation for all your APIs including custom Apex REST."

**Why it happens:** LLMs generalize the OpenAPI generator to all Salesforce APIs without knowing the scope limitation.

**The correct pattern:** The Salesforce OpenAPI beta covers only standard sObjects REST API (CRUD operations). Custom Apex `@RestResource` endpoints, Composite API, and Connect REST API require hand-authored specs.

**Detection hint:** Any recommendation to use the OpenAPI beta for custom Apex REST endpoint documentation is incorrect.

---

## Anti-Pattern 3: Treating 403 REQUEST_LIMIT_EXCEEDED the Same as 429 Throttling

**What the LLM generates:** "Implement exponential backoff retry on all 4xx errors including 403."

**Why it happens:** LLMs generalize error handling patterns without knowing the semantic difference between 403 (resource exhausted) and 429 (transient throttle).

**The correct pattern:** HTTP 403 `REQUEST_LIMIT_EXCEEDED` means the 24-hour daily budget is exhausted. Exponential backoff will not help until the rolling window resets. Document these as separate error conditions with separate recovery procedures.

**Detection hint:** Any error handling guide that applies the same retry logic to 403 and 429 is conflating two different error conditions.

**Sharper still:** the REST API Developer Guide's Status Codes and Error Responses table does not list 429 at all, so a contract that attributes 429 to Salesforce is describing the gateway or middleware in front of it. And `REQUEST_LIMIT_EXCEEDED` itself covers two conditions — the exhausted 24-hour allocation *and* the concurrent long-running-request cap — which need different recoveries. See `references/gotchas.md` gotchas 3 and 4.

---

## Anti-Pattern 4: Documenting SLA Percentages from Developer Docs

**What the LLM generates:** "Salesforce guarantees 99.9% uptime for REST API calls."

**Why it happens:** LLMs extrapolate SLA numbers from general cloud service expectations or training data about other platforms.

**The correct pattern:** Salesforce API SLA uptime and latency commitments are in trust.salesforce.com and Order of Service agreements — not in developer documentation. Do not document SLA percentages based on developer docs; reference trust.salesforce.com instead.

**Detection hint:** Any SLA percentage cited from developer documentation is unverified. SLA commitments require checking trust.salesforce.com and the Order of Service.

---

## Anti-Pattern 5: Not Including the Sforce-Limit-Info Header in Monitoring Design

**What the LLM generates:** API contract documentation that describes rate limits in text but does not include guidance on the `Sforce-Limit-Info` response header.

**Why it happens:** LLMs describe limits as static documentation rather than as runtime observability signals.

**The correct pattern:** The `Sforce-Limit-Info: api-usage=X/Y` header is present on every REST API response and provides real-time consumption visibility. Consumer teams must log this header and alert when X/Y exceeds a threshold (e.g., 80%). Documentation must include the header format and monitoring guidance.

**Detection hint:** API rate limit documentation that does not include the `Sforce-Limit-Info` header is missing the operational monitoring requirement.

---

## Anti-Pattern 6: Modelling the Salesforce Error Body as a Single Object

**What the LLM generates:** An OpenAPI error schema (or a partner-side DTO) shaped as `{ "message": string, "errorCode": string }`, and handler code that reads `response.errorCode`.

**Why it happens:** Most REST APIs return one error object per failure, so the LLM applies the majority shape. Salesforce returns a JSON **array** of error objects — the guide's own examples are `[{ "fields": ["Id"], "message": "...", "errorCode": "MALFORMED_ID" }]` and `[{ "message": "The requested resource does not exist", "errorCode": "NOT_FOUND" }]`.

**The correct pattern:** Type the error as an array of `{ message, errorCode, fields }` and make the handler iterate. See the `SalesforceErrors` schema in `references/worked-examples.md` § 2.

**Detection hint:** Any error schema whose `type` is `object` rather than `array`, or any handler that dereferences `errorCode` without indexing first. This bug survives UAT because most single-cause failures still parse if the client is lenient; it surfaces on the first multi-field validation failure.

---

## Anti-Pattern 7: Treating a 200 from a Batch Resource as "All Rows Saved"

**What the LLM generates:** Reconciliation logic — or a contract clause — whose success criterion is `if (response.status == 200) markAllDelivered()` for an sObject Collections or composite request.

**Why it happens:** For single-record REST calls the HTTP status genuinely is the outcome, and the LLM generalises. For sObject Collections it is not: if the request is well formed the API returns `200 OK`, and per-item outcomes live in the response, where each item carries a `success` flag and an `errors` array.

**The correct pattern:** Require per-row reconciliation in the contract — count `success: true` items against items sent — and record the `allOrNone` decision explicitly, because `allOrNone: true` converts silent partial loss into a whole-batch rollback, which is a business choice rather than a default.

**Detection hint:** Any batch integration whose monitoring dashboard tracks HTTP status codes and nothing else. Green for weeks, then a reconciliation gap nobody can date.

---

## Anti-Pattern 8: Documenting a Hardcoded Host Instead of the Named Credential

**What the LLM generates:** An outbound contract whose `endpoint` is `https://partner.example.com/v1/orders`, matching what the Apex looks like it calls.

**Why it happens:** The LLM resolves `callout:Northwind_OMS/v1/orders` to what it believes the URL is, because a concrete URL reads as more informative than a credential name.

**The correct pattern:** Document the `callout:<NamedCredential>/<path>` form as the contract endpoint and let the Named Credential record own the host. Apex resolves the host at runtime, so repointing the credential retargets every caller with no code diff and no failing test — a hardcoded host in the document is guaranteed to go stale silently.

**Detection hint:** An outbound contract that names a hostname but no Named Credential. Cross-check against `agents/integration-catalog-builder/AGENT.md`, which inventories the credential records that actually decide the host.
