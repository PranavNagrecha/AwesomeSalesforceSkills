# Gotchas — Salesforce Object Queryability

Each entry is a platform behaviour, not advice: **What happens / When it occurs /
How to avoid**. Line references are into the plain-text extracts of the Summer '26
guides (`api_rest.txt`, `object_reference.txt`, `apexdev.txt`, `apexrefguide.txt`,
`salesforce_app_limits_cheatsheet.txt`).

---

## Gotcha 1: `INVALID_TYPE` covers four distinct root causes

**What happens.** Salesforce returns `INVALID_TYPE` for: object doesn't exist,
edition-gated object, namespace prefix missing, API version too old. The error
code alone tells you nothing.

**When it occurs.** On every failed `FROM` clause where the object name is not
resolvable in the running context, whatever the reason.

**How to avoid.** Always check the `/sobjects/` listing + managed-package list +
edition before declaring a mode. The listing answers three of the four in one call.

---

## Gotcha 2: Tooling API vs Data API is not interchangeable

**What happens.** Objects like `ApexClass`, `FlowDefinition`, `ValidationRule`,
`RoutingConfiguration` exist in Tooling API only. Querying them via
`/services/data/v62.0/query` returns `INVALID_TYPE`. Same query via
`/services/data/v62.0/tooling/query` succeeds. Conversely, `ObjectPermissions`,
`FieldPermissions`, `PermissionSetAssignment`, `GroupMember` live on the Data API.

**When it occurs.** Any probe that hard-codes one endpoint and iterates a mixed
list of objects.

**How to avoid.** Declare `endpoint: data` or `endpoint: tooling` per query in the
probe recipe and have the runner honour it, rather than retrying blindly.

> UNVERIFIED (2026-09-04): the Tooling API Developer Guide is not in the extracted
> corpus, so the Tooling-only membership of each object above is field-observed,
> not quoted. The REST guide grounds only the Data API surface
> (`api_rest.txt` L7533, L8139–L8155). Confirm any Tooling query shape against
> the live org's `/services/data/vXX.X/tooling/sobjects/` listing before relying on it.

---

## Gotcha 3: Empty result set is not a query failure

**What happens.** A query returning `{"totalSize": 0, "records": []}` is a
**successful** response with an HTTP 200. An empty list of PSG assignments means
"this user has no PSGs".

**When it occurs.** Whenever an agent treats falsiness of the record list as the
failure signal instead of the HTTP status.

**How to avoid.** Branch on status first, record count second. In Apex the same
trap has a sharper edge: assigning a zero-row query to a **singleton** sObject
variable raises `System.QueryException: List has no rows for assignment to
SObject`, while the identical query assigned to a `List<>` just yields an empty
list (Apex Developer Guide, *QueryException*, `apexdev.txt` L39914–L39930). The
exception is about the assignment target, not about queryability.

---

## Gotcha 4: Field-level `SECURITY_ENFORCED` rewrites errors (legacy clause — ≤ 66.0 only)

**What happens.** A query with `WITH SECURITY_ENFORCED` that hits a field the
running user can't see returns `INVALID_FIELD` for the field, not
`INSUFFICIENT_ACCESS_OR_READONLY`. Strips the security signal.

**When it occurs.** On any inherited query still carrying the clause.

**How to avoid.** Diagnose by rerunning without `SECURITY_ENFORCED` — if it
succeeds, the user is the problem, not the query. That diagnosis applies only to a
query you inherited. In Apex the gate is the **`apiVersion` in the class's
`.cls-meta.xml`**, not the org's release — a Summer '26 org runs a class pinned to
58.0 with the clause quite happily. At **67.0+** the clause is removed and the
class does not compile: `WITH SECURITY_ENFORCED is no longer supported, use WITH
USER_MODE instead`. At **57.0–66.0** it still compiles but is legacy — migrate to
`WITH USER_MODE`. At **≤ 56.0** it is the idiom available. So never write it into
a new query, and never read its presence as evidence a query is secure: a scanner
flags it — P0 at 67.0+, P2 tech debt at 57.0–66.0. Canonical table:
`agents/_shared/AGENT_CONTRACT.md` § *Apex security idiom by API version*.

---

## Gotcha 5: Managed-package objects are invisible until installed

**What happens.** If the package isn't installed in the org, `fin__Payment__c`
returns `INVALID_TYPE`. That's correct behaviour, not a bug.

**When it occurs.** Cross-org probes, sandbox refreshes that dropped a package,
and any query copied from a different customer's org.

**How to avoid.** Introspect `/sobjects/` for `^<namespace>__` prefixes to detect
which packages are installed before issuing managed-package queries.

---

## Gotcha 6: API version affects `SetupEntityAccess` shape

**What happens.** Older API versions return fewer `SetupEntityType` values. A
probe filtering on `FlowDefinition` via `SetupEntityAccess` on API v45 gets
`INVALID_FIELD` on the filter clause.

**When it occurs.** Whenever the client's pinned version predates the value.

**How to avoid.** Bump to the version the `/services/data/` listing reports as
newest, then re-run. The REST guide's own 409 description says the same thing from
the server side: "Check that the API version is compatible with the resource
you're requesting" (`api_rest.txt` L1152–L1153).

---

## Gotcha 7: `describe` calls are not free

**What happens.** `GET /sobjects/<name>/describe` costs one API call per describe.

**When it occurs.** Multi-probe agents that describe once per query rather than
once per sObject.

**How to avoid.** Cache one describe per sObject per run, and read `queryable`
straight out of the single Describe Global payload instead — it is already in
that response alongside `name` and `keyPrefix` (`api_rest.txt` L2412–L2447). Add
`If-Modified-Since` and the whole listing collapses to a `304 Not Modified` with
no body when nothing changed (`api_rest.txt` L8143–L8145). In SOAP, batching does
not rescue you either: `describeSObjects()` "is limited to a maximum of 100
objects returned" per call (`salesforce_app_limits_cheatsheet.txt` L968–L969).

---

## Gotcha 8: HTTP 500 is different from HTTP 400

**What happens.** 400 = your query is malformed or references something that
doesn't exist. 500 = "An error has occurred within Lightning Platform, so the
request couldn't be completed" (`api_rest.txt` L1183–L1184).

**When it occurs.** Transient platform errors during any call.

**How to avoid.** Don't classify a 500 as "not queryable" — it's "not queryable
right now". Retry with backoff; after 3 attempts, escalate. The neighbouring
codes deserve the same care: 503 means the server is down for maintenance or
overloaded, and 403 with `REQUEST_LIMIT_EXCEEDED` means the org's API allocation
is spent — an org-level condition that has nothing to do with the object
(`api_rest.txt` L1145–L1146, L1188–L1189).

---

## Gotcha 9: Long-running queries can be killed silently

**What happens.** A query that exceeds the transaction's CPU ceiling terminates
with a partial response or a 500. Looks like a malformed query but isn't.

**When it occurs.** Wide projections over large objects, or a probe loop that
fans out. The synchronous ceiling is 10,000 ms of CPU and 100 SOQL queries
issued; asynchronous doubles the queries to 200 and raises CPU to 60,000 ms
(`salesforce_app_limits_cheatsheet.txt` L53, L91).

**How to avoid.** Narrow the filter, chunk the query, or move the probe to an
asynchronous context — and cap the object list so one run stays inside 100
queries.

---

## Gotcha 10: `ORDER BY` on a non-indexed field fails on large objects

**What happens.** A query like `ORDER BY ModifiedDate` on an object with millions
of rows returns `QUERY_TIMEOUT` or gets rewritten by the platform. Looks like a
failure; is a limit.

**When it occurs.** LDV objects with no selective filter ahead of the sort.

**How to avoid.** Add `LIMIT` and put an indexed filter first. Sizing rule: a
single transaction can retrieve 50,000 rows total via SOQL, or 10,000 via
`Database.getQueryLocator` (`salesforce_app_limits_cheatsheet.txt` L55, L57).
Depth on selectivity lives in `data/soql-query-optimization`.

---

## Gotcha 11: Presence in Describe Global is not a promise of `query()`

**What happens.** An object can appear in the `/sobjects/` listing, carry a
`keyPrefix` and a describe URL, and still have no `query()` call — the Describe
Global entry reports it as `"queryable": false` (`api_rest.txt` L2430). A
top-level `SELECT ... FROM <object>` then fails, and an agent that only checked
"is the name in the listing?" concludes the object is missing or that permissions
are wrong.

**When it occurs.** On read-only related-list and aggregation objects. The Object
Reference states each object's *Supported Calls*, and for these the list is
`describeSObjects()` with no `query()`:

| Object | Documented Supported Calls | Line |
|---|---|---|
| `OpenActivity` | `describeSObjects()` | `object_reference.txt` L191459 |
| `NoteAndAttachment` | `describeSObjects()` | `object_reference.txt` L189272 |
| `AttachedContentDocument` | `describeSObjects()` | `object_reference.txt` L43163 |
| `OwnedContentDocument` | `describeSObjects()` | `object_reference.txt` L207199 |
| `FeedTrackedChange` | `describeSObjects()` | `object_reference.txt` L137140 |
| `FeedLike` | `create(), delete(), describeSObjects()` | `object_reference.txt` L136566 |

**How to avoid.** Read `queryable` from the Describe Global entry — never infer it
from the name being present. When it is `false`, the verdict is
`not-queryable-on-this-surface` and the remediation is a subquery from the parent
object, not a permission grant. `StandardObjectNameChangeEvent` is the extreme
case: "A change event isn't a Salesforce object — it doesn't support CRUD
operations or queries. It's included in the object reference so you can discover
which Salesforce objects support change events" (`object_reference.txt`
L5119–L5132).

---

## Gotcha 12: A misspelled object name produces two different error codes depending on the REST surface

**What happens.** Hit the sObject Rows / Basic Information path
(`/services/data/vXX.X/sobjects/Acount/`) with a misspelled name and the response
is HTTP 404 with `{"message":"The requested resource does not exist","errorCode":
"NOT_FOUND"}` — the REST guide's own worked example is "you try to create a record
using a misspelled object name" (`api_rest.txt` L1202–L1209). Put the same
misspelling in a SOQL `FROM` clause on the query resource and you get an HTTP 400
instead: "The request couldn't be understood, usually because the JSON or XML
body contains an error" (`api_rest.txt` L1140).

**When it occurs.** Any time a probe mixes resource-path access with query access
across the same object list — very common in agents that describe over
`/sobjects/<name>/` and then query over `/query/`.

**How to avoid.** Classify on the HTTP status line plus the Describe Global
result, not on the error code string. A handler that only recognises `INVALID_TYPE`
silently mis-classifies every 404 from the resource path as a network or routing
problem, and a handler that treats 404 as "object missing" mis-classifies a
sharing problem — the guide's own note on 404 is "Check the URI for errors, and
verify that there are no sharing issues" (`api_rest.txt` L1148).

---

## Gotcha 13: `Schema.getGlobalDescribe()` keys are namespace-prefixed, so a bare name misses

**What happens.** `gd.get('MyObject__c')` returns `null` inside namespace `NS1`
even though the object exists, because the key is `NS1__MyObject__c`. "Starting
with Apex saved using Salesforce API version 28.0, the keys in the map that
getGlobalDescribe returns are always prefixed with the namespace, if any, of the
code in which it is running" (`apexdev.txt` L11081–L11088).

**When it occurs.** Any describe-based existence check running inside a managed
package or a namespaced org, and any check that was written against an
unnamespaced dev org and then installed.

**How to avoid.** Match on suffix (`key.endsWithIgnoreCase('__' + name)`) as well
as on the exact key before concluding the object does not exist — that is the
difference between verdict `namespace-prefix-missing` and
`object-does-not-exist`. Two further behaviours of the same map: sObject names are
case insensitive (`apexdev.txt` L11076), and when the method is called from an
**installed managed package** it "returns sObject names and tokens for Chatter
sObjects, such as NewsFeed and UserProfileFeed, even if Chatter is not enabled in
the installing organization" (`apexdev.txt` L11090–L11092) — so a key in the map
is not by itself proof the feature is on.

---

## Gotcha 14: `DescribeSObjectResult.isAccessible()` changed answer at API 54.0 for custom settings and custom metadata

**What happens.** "In API version 54.0 and later, for custom settings and custom
metadata type objects, `DescribeSObjectResult.isAccessible()` returns false if the
user doesn't have permissions to access the queried objects. In API version 53.0
and earlier, the method returns true even if the user doesn't have the required
permissions" (`apexrefguide.txt` L192676–L192679).

**When it occurs.** A probe class whose `.cls-meta.xml` pins an `apiVersion` at or
below 53.0, running in a current org. The gate is the class's saved API version,
not the org's release.

**How to avoid.** Read the class's `apiVersion` before trusting an `isAccessible()`
pass on a custom setting or CMDT, and pin probe classes at the org's newest
version. On a low-pinned class the check reports access the running user does not
have, and the real failure surfaces later as a query error the classifier will
blame on the object.

---

## Gotcha 15: A field can be un-filterable while the object is perfectly queryable

**What happens.** `SELECT Id FROM UserLicense` succeeds and
`WHERE UsedLicenses > 0` fails on the same object: "This field isn't filterable in
API version 64.0 or later when using it in a WHERE clause in a SOQL query.
Instead, you have to process the data after fetching all the records"
(`object_reference.txt` L299685–L299686).

**When it occurs.** On any org at API 64.0 or later, for a licence-usage query
that worked unchanged for years — the object did not move, the field did not
disappear, only the filterability did.

**How to avoid.** Read the field's **Properties** line in the Object Reference —
`Filter`, `Group`, `Sort`, `Nillable`, `idLookup` are per-field capabilities, and
`Filter` missing means no `WHERE`. Verdict is `field-not-visible`, remediation is
"fetch and filter client-side", never "the object isn't queryable in this org".
The same object-level pattern applies to aggregates: `SetupAuditTrail` supports
`query(), retrieve()`, but "Aggregate queries aren't supported on this object. For
example, `SELECT count() FROM SetupAuditTrail` works but `SELECT count(Id) FROM
SetupAuditTrail` fails" (`object_reference.txt` L261553–L261554).

---

## Gotcha 16: `API_DISABLED_FOR_ORG` is an org verdict masquerading as an object verdict

**What happens.** Every API call fails identically, so the first object in the
probe list gets blamed. "API access is enabled by default in Enterprise,
Performance, Unlimited, and Developer Edition orgs. Professional Edition orgs can
add API access as an add-on... If you send an API request to an org without API
access, Salesforce returns a API_DISABLED_FOR_ORG error" (`api_rest.txt`
L409–L412).

**When it occurs.** Professional Edition orgs without the add-on, and any org
where the running user's profile lacks API Enabled — "To make any API call, a user
must have the API Enabled permission turned on in the user profile they're
assigned" (`api_rest.txt` L418–L419).

**How to avoid.** Make the org-level probe the first check in the verdict record
(`org_api_enabled`) and abort the whole run on failure rather than emitting one
per-object verdict per target. A run that reports six objects "not queryable in
this org" when the real answer is one org-level licence gap is the same
looks-complete-but-isn't failure this skill exists to prevent, multiplied.
