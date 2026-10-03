# Gotchas — REST API Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. "REST guide" means the REST API Developer Guide, Version 67.0 (api_rest.pdf). "Limits" means the Salesforce Developer Limits and Allocations Quick Reference, release 262.

## Gotcha 1: Outer HTTP 200 Does Not Mean All Composite Subrequests Succeeded

**What happens:** A POST to `/composite/` or `/composite/batch/` returns HTTP 200 for the outer response envelope even when individual subrequests failed with 4xx status codes. Integrations that stop at the outer status code silently discard errors and may assume records were written when they were not.

**When it occurs:** Any time you use the Composite or Composite Batch resources and do not iterate over `compositeResponse` entries to inspect per-subrequest `httpStatusCode`.

**How to avoid:** Always iterate over every entry in `compositeResponse` and treat any `httpStatusCode` ≥ 400 as an error requiring handling. Log the `referenceId`, status, and body. When `allOrNone: true` is set, a single 4xx subrequest triggers a full rollback — but you still need to read the response to identify which subrequest triggered the rollback.


**Source:** REST guide, Composite (response bodies and HTTP statuses of subrequests returned in a single response body) and Batch Request Body (`haltOnError`: top-level 200 with `hasErrors` true).
---

## Gotcha 2: `nextRecordsUrl` Is a Path, Not a Full URL

**What happens:** The `nextRecordsUrl` value returned in paginated SOQL query responses is a relative path (e.g., `/services/data/v63.0/query/01gXXX-2000`), not a complete URL. Clients that use this value as-is (without prepending the instance hostname) get a connection error or an incorrect request to the wrong host. Clients that try to reconstruct a query locator URL from scratch get a 404.

**When it occurs:** Whenever a SOQL query returns `"done": false`, which happens for any result set with more records than the batch size (default 2,000).

**How to avoid:** Always prepend the org's instance URL (e.g., `https://myorg.salesforce.com`) to `nextRecordsUrl` before issuing the next GET. Store the instance URL at authentication time from the OAuth token response (`instance_url` field) and reuse it for the duration of the pagination loop. Never reconstruct the query locator manually.


**Source:** REST guide, Query and Query More Results (`nextRecordsUrl` returned as `/services/data/v67.0/query/01gD0000002HU6KIAW-2000` and requested against `https://MyDomainName.my.salesforce.com`).
---

## Gotcha 3: Retired API Versions Return 410, After at Least a Year of Notice

**What happens:** An integration pinned to an old version starts failing with `410 GONE` on every call.

**When it occurs:** "Salesforce is committed to supporting each API version for a minimum of 3 years from the date of first release," and "notifies customers who use an API version scheduled for deprecation at least 1 year before support for the version ends." Versions 7.0 through 20.0 were retired as of Summer '22 and 21.0 through 30.0 as of Summer '25. "If you request any resource or use an operation from a retired API version, REST API returns the 410:GONE error code." An earlier version of this file said calls fail "with no runtime warning"; the advance notice and the 410 code are documented.

**How to avoid:** Keep the version in configuration, watch for retirement notices, and use the API Total Usage event type to find callers on old versions. Upgrade on a schedule rather than at the deadline.

**Source:** REST guide, API End-of-Life Policy.

---

## Gotcha 4: Concurrent Long-Running Request Limit Is Independent of the Daily Allocation

**What happens:** Exports and polling jobs start failing while the daily allocation is far from used.

**When it occurs:** Production orgs and sandboxes allow 25 concurrent inbound requests that run 20 seconds or longer; Developer Edition and trial orgs allow 5. "If the number of long running requests exceeds the limit, the API returns a REQUEST_LIMIT_EXCEEDED exception code." There is no limit on concurrent requests shorter than 20 seconds. Separately, REST and SOAP calls time out after 10 minutes (queries follow the SOQL limits), and for Composite resources the timeout applies to the whole composite request.

**How to avoid:** Cap parallel long-running calls per org, keep queries selective, split large composite requests, and prefer Change Data Capture or Platform Events over tight polling loops.

**Source:** Limits, API Request Limits and Allocations (Concurrent API Request Limits; API Timeout Limits).

---

## Gotcha 5: Exceeding the Request Limit Returns 403 `REQUEST_LIMIT_EXCEEDED`, Not 429

**What happens:** A client written for generic APIs waits for HTTP 429 and a `Retry-After` header, never sees them, and treats the 403 as a permissions problem.

**When it occurs:** The REST guide's status code table lists 403 with the note "If the error code is REQUEST_LIMIT_EXCEEDED, you've exceeded API request limits in your org." The table has no 429, and the guide does not describe a `Retry-After` header for REST API. An earlier version of this file said Salesforce returns 429 with `Retry-After`; no fetched Salesforce source supports that. Every REST response carries `Sforce-Limit-Info: api-usage=used/limit`.

**How to avoid:** Branch on the `errorCode` in a 403 body. On `REQUEST_LIMIT_EXCEEDED`, back off with jitter and alert; track `Sforce-Limit-Info` and `GET /limits/` to slow down before the limit. Allocations are org-wide, not per user, and calls with the DebuggingHeader have a separate 1,000-call allocation.

**Source:** REST guide, Status Codes and Error Responses; Limit Info Header. Limits, Total API Request Allocations.

---

## Gotcha 6: PATCH on a Non-Existent Record ID Returns 404, Not an Upsert

**What happens:** `PATCH /sobjects/{SObject}/{id}` updates a record if it exists. If the provided Salesforce record ID does not exist (deleted, wrong ID), the API returns HTTP 404. This surprises integrations that expect PATCH to behave as upsert.

**When it occurs:** When an integration caches Salesforce IDs and uses them for PATCH updates without validating that the records still exist. Common after org refreshes, data cleanup scripts, or record merges.

**How to avoid:** Use External ID upsert (`PATCH /sobjects/{SObject}/{ExternalIdField}/{value}`) when the create-or-update semantic is required. If using Salesforce IDs directly, add 404 handling that falls back to a POST create or re-queries for the current ID.


**Source:** REST guide, Status Codes and Error Responses (404: the requested resource could not be found); Insert or Update (Upsert) a Record Using an External ID.
---

## Gotcha 7: Composite Allows Only Five Collection or Query Subrequests

**What happens:** A composite request with 25 subrequests is rejected because ten of them are queries.

**When it occurs:** "You can have up to 25 subrequests in a single call. Up to 5 of these subrequests can be sObject Collections or query operations, including Query and QueryAll requests." Composite graphs raise the overall subrequest limit to 500.

**How to avoid:** Count collection and query subrequests separately from the 25 total, or use a composite graph for larger dependent sets.

**Source:** REST guide, Composite (Send Multiple Requests Using Composite, Note) and the composite examples note that composite graphs raise the limit to 500.

---

## Gotcha 8: Upsert Returns 300 When the External ID Matches Twice

**What happens:** An upsert neither creates nor updates, and the response is a list of records with status 300.

**When it occurs:** "If the external ID is matched multiple times, then a 300 error is reported, and the record isn't created or updated." In API 46.0 and later, a successful update returns 200 with `"created": false` and a create returns 201 with `"created": true`; in 45.0 and earlier an update returns 204 with no body.

**How to avoid:** Make the External ID field unique, handle 300 as a data-quality alert, and read `created` instead of the status code alone. Use `?updateOnly=true` when the integration must never create.

**Source:** REST guide, Insert or Update (Upsert) a Record Using an External ID.

---

## Gotcha 9: sObject Tree Fires Automation Per Level, Not Per Tree

**What happens:** A trigger that expects to see an Account and its Contacts in one transaction context sees all root Accounts first and all Contacts later.

**When it occurs:** "Triggers, processes, and workflow rules fire separately" for all root records across the trees, then all second-level records of the same type, then each further level. The request holds up to 200 records, up to five levels, and up to five record types; one failure fails the whole request.

**How to avoid:** Write triggers that do not assume parents and children arrive together, and validate records before sending large trees.

**Source:** REST guide, sObject Tree.

---

## Gotcha 10: The Requested Batch Size Is a Hint

**What happens:** A client that sets `batchSize=2000` and counts on exactly 2,000 rows per page miscalculates offsets.

**When it occurs:** The `Sforce-Query-Options` header's batch size defaults to 2,000, with a minimum of 200 and a maximum of 2,000, and "there is no guarantee that the requested batch size is the actual batch size." The query response "can include fewer records than the limit ... based on the size and complexity of records queried."

**How to avoid:** Always follow `nextRecordsUrl` until `done` is true and never compute pages from the batch size.

**Source:** REST guide, Query Options Header; Query.

