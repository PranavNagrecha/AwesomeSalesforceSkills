# Gotchas — Salesforce Object Queryability

## Gotcha 1: `INVALID_TYPE` covers four distinct root causes

Salesforce returns `INVALID_TYPE` for: object doesn't exist, edition-gated object, namespace prefix missing, API version too old. The error code alone tells you nothing. Always check `/sobjects/` listing + managed-package list + edition before declaring a mode.

---

## Gotcha 2: Tooling API vs Data API is not interchangeable

Objects like `ApexClass`, `FlowDefinition`, `ValidationRule`, `RoutingConfiguration` exist in Tooling API only. Querying them via `/services/data/v62.0/query` returns `INVALID_TYPE`. Same query via `/services/data/v62.0/tooling/query` succeeds.

Conversely, `ObjectPermissions`, `FieldPermissions`, `PermissionSetAssignment`, `GroupMember` live on the Data API. Tooling API rejects them.

---

## Gotcha 3: Empty result set ≠ query failure

A query returning `{"totalSize": 0, "records": []}` is a **successful** response. An empty list of PSG assignments means "this user has no PSGs" — not "PSG queries don't work." Collapsing these two states is the ExampleOrg incident.

---

## Gotcha 4: Field-level `SECURITY_ENFORCED` rewrites errors (legacy clause — ≤ 66.0 only)

A query with `WITH SECURITY_ENFORCED` that hits a field the running user can't see returns `INVALID_FIELD` for the field, not `INSUFFICIENT_ACCESS_OR_READONLY`. Strips the security signal. Diagnose by rerunning without `SECURITY_ENFORCED` — if it succeeds, the user is the problem, not the query.

That diagnosis applies only to a query you inherited. In Apex the gate is the **`apiVersion` in the class's `.cls-meta.xml`**, not the org's release — a Summer '26 org runs a class pinned to 58.0 with the clause quite happily. At **67.0+** the clause is removed and the class does not compile: `WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead`. At **57.0–66.0** it still compiles but is legacy — migrate to `WITH USER_MODE`. At **≤ 56.0** it is the idiom available. So never write it into a new query, and never read its presence as evidence a query is secure: a scanner flags it — P0 at 67.0+, P2 tech debt at 57.0–66.0. Canonical table: `agents/_shared/AGENT_CONTRACT.md` § *Apex security idiom by API version*.

---

## Gotcha 5: Managed-package objects are invisible until installed

If the package isn't installed in the org, `fin__Payment__c` returns `INVALID_TYPE`. That's correct behavior, not a bug. Your probe should introspect `/sobjects/` for `^<namespace>__` prefixes to detect which packages are installed before issuing managed-package queries.

---

## Gotcha 6: API version affects `SetupEntityAccess` shape

Older API versions return fewer `SetupEntityType` values. A probe querying for `FlowDefinition` via `SetupEntityAccess` on API v45 gets `INVALID_FIELD` on the filter clause. Bump to current (v62+).

---

## Gotcha 7: `describe` calls are not free

`GET /sobjects/<name>/describe` counts against API limits (1 call per describe). Caching is essential for multi-probe agents — one describe per sObject per run, not per query.

---

## Gotcha 8: HTTP 500 is different from HTTP 400

- 400 = your query is malformed or references something that doesn't exist.
- 500 = Salesforce internal error; retry with exponential backoff.

Agents should not classify a 500 as "not queryable." It's "not queryable right now" — a transient failure. After 3 retries with backoff, escalate.

---

## Gotcha 9: Long-running queries can be killed silently

A Tooling API query that exceeds the CPU governor limit (10s sync) terminates with a partial response or a 500. Looks like a malformed query but isn't. Fix: narrow the filter, chunk the query, or move to async.

---

## Gotcha 10: `ORDER BY` on non-indexed field fails on large objects

A query like `ORDER BY ModifiedDate` on an object with millions of rows returns `QUERY_TIMEOUT` or gets rewritten by the platform. Looks like a failure; is a limit. Add `LIMIT` + use indexed filter first.
