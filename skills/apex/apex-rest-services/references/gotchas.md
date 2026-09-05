# Gotchas — Apex REST Services

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `RestContext` Must Be Set In Tests

**What happens:** Unit tests call the REST method directly and hit null references.

**When it occurs:** `RestContext.request` and `RestContext.response` are not initialized in the test.

**How to avoid:** Create and assign both objects before invoking the REST method.

---

## Authentication Into Salesforce Does Not Finish The Security Job

**What happens:** A valid integration user can call the endpoint, but the resource class still overexposes or overupdates data.

**When it occurs:** Teams assume caller authentication removes the need for explicit sharing and CRUD/FLS review.

**How to avoid:** Declare sharing intentionally and secure data access paths explicitly.

---

## Always Returning `200` Makes Client Behavior Worse

**What happens:** Clients cannot distinguish validation failure, not-found, and server error cases.

**When it occurs:** Endpoints use one status code and one vague message shape for everything.

**How to avoid:** Define status codes and error bodies as part of the contract.

---

## Versioning Is Harder To Add Later

**What happens:** An endpoint initially ships without versioning, then incompatible changes become painful.

**When it occurs:** Teams optimize for speed and delay contract planning.

**How to avoid:** Version the endpoint deliberately from the beginning when external consumers will depend on it.

---

## A Wildcard Is Legal In The Middle Of A Path — And Two Overlapping Mappings Resolve By Save Order

**What happens:** Two `@RestResource` classes both answer a URL, and which one runs is decided by which class was saved first, not by which is more specific. Redeploying both in a different order silently swaps the endpoint's behaviour.

**When it occurs:** The wildcard rules are looser than most authors assume. "A wildcard (*) that appears in a path must be preceded by a forward slash (/). Additionally, unless the wildcard is the last character in the path, it must be followed by a forward slash (/)" (apexdev L6359–6361) — so `/cases/*/comments` is a legal mapping, not just `/cases/*`. Resolution then runs: "An exact match always wins. If no exact match is found, find all the patterns with wildcards that match, and then select the longest (by string length) of those. If no wildcard match is found, an HTTP response status code 404 is returned" (apexdev L6362–6364). The tie-break case is explicit: "The URL patterns `URLpattern` and `URLpattern/*` match the same URL. If one class has a urlMapping of `URLpattern` and another class has a urlMapping of `URLpattern/*`, a REST request for this URL pattern resolves to the class that was saved first" (apexdev L18589–18591).

**How to avoid:** Never ship `/x` and `/x/*` in the same org. Give each resource one mapping that no other class can also match, and treat the mapping string as a deployment-ordered dependency during a package split. `python3 scripts/check_apex_rest_services.py --manifest-dir force-app` reports duplicate and overlapping mappings across the source tree.

---

## `urlMapping` Is Case-Sensitive, So `/Cases/*` And `/cases/*` Are Different Endpoints

**What happens:** A client that capitalises the path gets `404 — The URL is unmapped in an existing @RestResource annotation` (apexdev L18688) even though the resource is deployed and active.

**When it occurs:** "The URL mapping is case-sensitive. For example, a URL mapping for `my_url` matches a REST resource containing `my_url` and not `My_Url`" (apexdev L6350–6351). The failure shows up when the integration is handed to a team whose HTTP client or gateway normalises casing differently from the one used in testing.

**How to avoid:** Fix a lowercase-with-hyphens convention for every mapping, publish the exact string in the contract document, and probe it in the deployment smoke test rather than relying on the client's own URL builder.

---

## Declaring Method Parameters Empties `RestRequest.requestBody`

**What happens:** A `@HttpPost` method takes typed parameters *and* reads `RestContext.request.requestBody` for logging or a checksum. `requestBody` is null, and the log line records nothing.

**When it occurs:** The two are mutually exclusive by design. "If the Apex method has no parameters, Apex REST copies the HTTP request body into the `RestRequest.requestBody` property. If the method has parameters, then Apex REST attempts to deserialize the data into those parameters and the data won't be deserialized into the `RestRequest.requestBody` property" (apexdev L18459–18461, restated at apexrefguide L228536–228538). Separately, "Methods annotated with `@HttpGet` or `@HttpDelete` must have no parameters. This is because GET and DELETE requests have no request body, so there's nothing to deserialize" (apexdev L18443–18444).

**How to avoid:** Pick one style per method and stay in it. A parameterless method plus `JSON.deserialize(req.requestBody.toString(), MyRequest.class)` keeps the raw body available for logging, replay, and idempotency keys; parameter-based deserialization gives that up.

---

## A Status Code Outside The Documented Table Is Converted To A 500

**What happens:** The endpoint sets `res.statusCode = 422` for a validation failure. The client receives `500` with the body `Invalid status code for HTTP response: 422`, and the carefully designed error envelope never arrives.

**When it occurs:** "If you set the `RestResponse.statusCode` property to a value that's not listed in the table, then an HTTP status of 500 is returned with the error message 'Invalid status code for HTTP response: nnn' where nnn is the invalid status code value" (apexrefguide L228768–228770). The accepted list is 200, 201, 202, 204, 206, 300, 301, 302, 304, 400, 401, 403, 404, 405, 406, 409, 410, 412, 413, 414, 415, 417, 500, 503 (apexrefguide L228772–228820). `422`, `429`, and `418` are all absent — and `429` is the one an author reaches for when adding rate limiting.

**How to avoid:** Use `400` for validation and `409` for a conflict. Carry the finer-grained reason in the envelope's `code` field, which is yours to define, rather than in the status line, which is not.

---

## Heap Exhaustion During Response Serialization Returns HTTP 200 With A Truncated Body

**What happens:** A collection endpoint returns a large result. The client sees `200 OK` and a body that is valid-looking JSON up to a point and then stops. Retry logic keyed on the status code never fires.

**When it occurs:** "If the heap limit is exceeded in the process of serialization, an HTTP 200 code is returned and the error `{"status":"some error occurred"}` is appended to the partial JSON response. Returning a collection of sObjects from a REST method involves buffering the JSON serialized form of each sObject. Heap and CPU limits may not be encountered until after the HTTP response header and initial data has started streaming back to the client" (apexdev L18474–18477). The header is already on the wire when the limit hits, so the platform cannot retract the `200`.

**How to avoid:** The guide names the fix in the same paragraph — "To gain control of the `statusCode` and the `responseBody`, use a `RestResponse` instead of directly returning sObjects" (apexdev L18477–18478). Return `void`, build the body yourself, cap the page size in the contract, and project onto a narrow DTO instead of returning sObjects. See `integration/rest-api-pagination-patterns` for the paging contract.

---

## Returning A Value Instead Of `void` Hands The Response Body To The Platform — And Drops Every Null Field

**What happens:** A method returns a wrapper object. The client's schema validation fails intermittently, because fields the client declares as required are simply absent from some responses.

**When it occurs:** Serialization is automatic and lossy on nulls. "An Apex method with a non-void return type has the return value serialized into `RestResponse.responseBody`. If the return type includes fields with null values, those fields aren't serialized into the response body" (apexdev L18463–18465; restated apexrefguide L228728–228734: "If the method returns void, then Apex REST returns the response in the `responseBody` property"). Returning an sObject also emits the platform's own `attributes` envelope with a hard-coded `/services/data/vNN.0/` URL — visible in the guide's own cURL walkthrough (apexdev L18818–18828).

**How to avoid:** For any endpoint with a published contract, return `void` and write `res.responseBody` explicitly. That is the only shape in which the status code, the headers, and the null-handling are all yours.

---

## Unhandled Exceptions Never Reach Your Error Envelope — They Become A Platform 400 Or 500

**What happens:** A `try/catch` around the business call is assumed to cover everything, so the endpoint is documented as "always returns our error envelope". Some failures arrive as a bare platform error body with no `code` field, and the client's parser throws.

**When it occurs:** Three failure classes are decided before or outside the method body. "`DELETE, GET, PATCH, POST, PUT` → `400` — An unhandled user exception occurred" and "→ `500` — An unhandled Apex exception occurred" (apexdev L18684, L18693). A cycle between user-defined types "generates an HTTP 400 status code error response" at run time (apexdev L18564–18565), and duplicate keys in the request data — `{"x":"value1","x":"value2"}` — also "results in an HTTP 400 status code error response" (apexdev L18607–18609). None of these run your `catch`.

**How to avoid:** Document the platform-generated statuses (`400`, `403`, `404`, `405`, `406`, `415`, `500`) as part of the contract alongside your own, and have the client treat a response with no `code` field as a transport-level error rather than an application one. Never let a `LimitException` be the thing you promised to catch — no `catch (Exception)` intercepts it.

---

## The Caller Needs Apex Class Access, And It Is Checked Only At The Entry Point

**What happens:** An integration user authenticates successfully, has full object permissions, and still gets `403` on every call. Or the inverse: a user is granted access to the resource class and thereby reaches a service class they were deliberately not granted.

**When it occurs:** "Class security applies to methods that are in Apex transaction entry points, such as: … Apex REST services" (apexdev L12325–12329), and the documented response is `403 — You don't have access to the specified Apex class` (apexdev L18686). The one-hop rule is explicit: "class A calls class B. User X has a profile that can access class A but not class B. User X can execute the code in class B, but only through class A" (apexdev L12323–12324).

**How to avoid:** Ship the permission set that grants Apex Class Access on the resource class in the same `package.xml` as the class. Grant the resource class only — the service class is reached through it by design, so adding it grants nothing and invites direct invocation from elsewhere.

---

## A Packaged Class's URL Grows A Namespace Segment, And The Namespaced Class Wins Any Collision

**What happens:** An endpoint that worked in the development org returns `404` after the code is packaged and installed, because every client is calling the un-namespaced path.

**When it occurs:** "When calling Apex REST methods that are contained in a managed package, you must include the managed package namespace in the REST call URL. For example, if the class is contained in a managed package namespace called `packageNamespace` and the Apex REST methods use a URL mapping of `/MyMethod/*`, the URL used via REST to call these methods would be of the form `https://instance.salesforce.com/services/apexrest/packageNamespace/MyMethod/`" (apexdev L18465–18470). The collision rule matters when a subscriber org has its own class on the same path: "In the case of a URL collision, the namespaced class is always used" (apexdev L6367–6369). A third documented `404` covers the case where the namespace itself is wrong: "The Apex class with the specified namespace couldn't be found" (apexdev L18693).

**How to avoid:** Decide packaging before publishing the contract. If the endpoint may ever ship in a managed package, publish the base URL as a client-side configuration value, not a constant.

---

## The Size Ceiling Is On The Whole Request, And The URL Has A Separate, Much Smaller One

**What happens:** A bulk POST that worked at 500 records fails at 5,000; or a GET with a long filter string starts returning `414`/`431` under a different load balancer.

**When it occurs:** Two independent caps apply. Body: "Calls to Apex REST classes count against the organization's API governor limits. All standard Apex governor limits apply to Apex REST classes. For example, the maximum request or response size is 6 MB for synchronous Apex or 12 MB for asynchronous Apex" (apexdev L18396–18397). URL and headers: "In each REST call, the allowed length for the combined URI and headers is 16,384 bytes. Requests exceeding this limit can return a `431 Request Header Fields Too Large` error at any time. For URIs exceeding this limit, requests can return a `414 URI Too Long` error at any time" — with the further advice that "for public-facing services, it's recommended to limit URI length to 2000 characters and headers to approximately 8000 bytes" (App Limits Cheat Sheet L693–700). A third ceiling is concurrency, not size: requests running 20 seconds or longer are capped at 25 in production and sandboxes, 5 in Developer Edition and trial orgs, and exceeding it returns `REQUEST_LIMIT_EXCEEDED` (App Limits Cheat Sheet L481–493).

**How to avoid:** Publish a maximum batch size in the contract and enforce it in the resource with a `413`. Keep filters in the POST body rather than the query string. Keep the p99 under 20 seconds, or move the work to an async pattern — see `integration/bulk-api-2-patterns`.

---

## `@ReadOnly` Buys A Million Rows And Costs You All DML

**What happens:** `@ReadOnly` is added to a heavy `@HttpGet` to escape the query-row limit; a later change adds an audit-log insert to the same method and fails at run time.

**When it occurs:** "The `@ReadOnly` annotation allows you to perform less restrictive queries against the Lightning Platform database by increasing the limit of the number of returned rows for a request to 1,000,000. All other limits still apply. The annotation blocks the following operations within the request: DML operations, calls to `System.schedule`, and enqueued asynchronous Apex jobs" (apexdev L6162–6164). It also requires the web service to be the top-level request (apexdev L6165–6166). From API version 49.0 it no longer needs `@RemoteAction` alongside it (apexdev L6176–6178).

**How to avoid:** Reserve `@ReadOnly` for genuinely read-only reporting endpoints, and put it in the class-level comment so the next author knows why an `insert` will not compile into that path. Do not add it to a resource that also logs to a custom object.
