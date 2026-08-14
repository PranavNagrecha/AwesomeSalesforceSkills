---
name: soql-object-limits-and-restrictions
description: "Use when a SOQL query fails or must be shaped around a specific object's own limits and restrictions — Attachment's 100,000-record ceiling, the mandatory filter fields on ContentDocumentLink / ContentHubItem / Vote, the required LIMIT clause on TopicAssignment / NewsFeed / UserProfileFeed (absent View All Data), the hard 200-row cap and ORDER BY HasAccess rule on UserRecordAccess, indexed-field-only filtering on big objects, the 4-join / 1,000-row-subquery caps on external objects, KnowledgeArticleVersion requiring dynamic SOQL, and RecentlyViewed's 90-day rolling window. NOT for generic SOQL governor limits — use apex/governor-limits. NOT for index and selectivity tuning — use data/soql-query-optimization. NOT for general SOQL syntax — use apex/soql-fundamentals."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
triggers:
  - "querying Attachment fails once results exceed 100,000 records"
  - "a ContentDocumentLink query throws an error demanding a filter on Id, ContentDocumentId, or LinkedEntityId"
  - "filtering a big object only works on the indexed fields, in order, with no gaps"
  - "figuring out how many joins a single SOQL query can make across external objects"
  - "a TopicAssignment or NewsFeed query fails unless I add a LIMIT clause"
tags:
  - soql
  - per-object-limits
  - big-objects
  - external-objects
  - content-document-link
  - userrecordaccess
inputs:
  - "A SOQL query (inline Apex, dynamic SOQL, or API) that targets Attachment, ContentDocumentLink, ContentHubItem, UserRecordAccess, RecentlyViewed, TopicAssignment, NewsFeed, UserProfileFeed, Vote, KnowledgeArticleVersion, a big object, or an external object"
  - "The running user's permission context — specifically whether they hold View All Data"
  - "Whether the query runs in user mode or system mode, and the expected result volume"
outputs:
  - "A compliant query that satisfies the target object's mandatory-filter, required-LIMIT, row-cap, or indexed-field constraint"
  - "A remediation plan for a query that fails a per-object SOQL restriction (rewrite, scope down, or migrate the object)"
  - "Guidance on which restriction applies and why View All Data is not the fix"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOQL Object Limits and Restrictions

This skill activates when a SOQL query fails — or has to be written defensively — because of a limit that belongs to the **object it targets**, not to the generic governor limits. Salesforce documents that "SOQL applies specific limits to objects and situations," and those per-object rules (hard row caps, mandatory filter fields, required `LIMIT` clauses, indexed-field-only filtering) sit on top of the normal query limits and fail queries that would otherwise be perfectly legal.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Identify the target object.** The restriction is keyed to the object in the `FROM` clause (and sometimes the field in `SELECT`). A query on `Account` has none of these; a query on `Attachment`, `ContentDocumentLink`, `UserRecordAccess`, a big object, or an external object may fail on a rule the object alone imposes.
- **Know the running user's permissions.** Several limits lift only when the user holds **View All Data** (the Attachment 100,000 cap, the `LIMIT` requirement on `TopicAssignment` / `NewsFeed` / `UserProfileFeed`). Whether your code runs in user mode or system mode changes what actually happens.
- **Separate these from the generic governor limits.** A query can be well inside the 100-queries / 50,000-rows-retrieved Apex governor limits and *still* fail on a per-object rule. Don't debug a per-object failure by chasing governor limits.
- **These are unversioned reference limits.** The docs do not stamp them GA/Beta, and the exact numbers can change between releases. Treat the values here as current-as-documented and re-check the SOQL and SOSL Reference before relying on an edge case.

---

## Core Concepts

### The four shapes of a per-object restriction

Every restriction on the page reduces to one of four shapes. Knowing which shape you are facing tells you how to fix it:

1. **Hard row cap** — the query fails or is capped past a fixed count. `Attachment` fails past **100,000** records; `UserRecordAccess` returns at most **200** records no matter what you filter on.
2. **Mandatory filter field** — the query is invalid unless it filters on a specific field. `ContentDocumentLink` must filter on one of `Id`, `ContentDocumentId`, or `LinkedEntityId`; `ContentHubItem` on `Id`, `ExternalId`, or `ContentHubRepositoryId`; `Vote` on `ParentId` (single ID), `Parent.Type` (single type), or `Id` (single ID or list).
3. **Required `LIMIT` absent a permission** — the query must carry a `LIMIT` unless the user has View All Data. `TopicAssignment` needs `LIMIT 1,100` or fewer; `NewsFeed` and `UserProfileFeed` need `LIMIT 1,000` or fewer.
4. **Restricted filter surface** — you cannot filter the object like a normal sObject. Big objects can filter **only** on their index fields, in index order, with no gaps; external objects cap joins and subqueries; `KnowledgeArticleVersion` cannot take an Apex bind variable and must be queried with dynamic SOQL.

### View All Data is the escape hatch — and the trap

Several caps and `LIMIT` requirements simply disappear when the running user holds View All Data. That makes it tempting to "fix" a failing query by granting the permission or moving the code to system mode. Resist it. View All Data is one of the broadest permissions in the platform; using it to make a query compile bypasses sharing for **every** object the transaction touches, not just the one that was failing. The correct fix is almost always to scope the query (add the filter, add the `LIMIT`) rather than to widen access.

### Big objects and external objects filter differently

Big objects are not stored like standard/custom objects, so a big-object SOQL query can filter **only on the fields in the object's index**, and only in the order they appear in the index with no gaps. The last field in the filter may use `=`, `<`, `>`, `<=`, `>=`, or `IN`; every earlier field must use `=`. Operators `!=`, `LIKE`, `NOT IN`, `EXCLUDES`, and `INCLUDES` are unsupported. External objects live in a remote system reached over OData, so a single query allows **up to 4 joins** across external objects and other types, subqueries fetch **up to 1,000 rows**, and aggregate functions/clauses (`AVG()`, `COUNT(fieldName)`, `HAVING`, `GROUP BY`, `MAX()`, `MIN()`, `SUM()`) are unsupported.

### RecentlyViewed is a rolling window, not a table

`RecentlyViewed` rows are retained for **90 days** and the object is periodically truncated down to about 200 records per object. It is a convenience view of recent activity, not a historical or audit dataset — never treat a `RecentlyViewed` query as a complete record of what a user has seen.

---

## Common Patterns

### Satisfy the mandatory filter (ContentDocumentLink / ContentHubItem / Vote)

**When to use:** any query against a file-linkage or vote object.

**How it works:** always include a `WHERE` clause on one of the object's allowed filter fields. For files attached to a record, filter `ContentDocumentLink` on `LinkedEntityId`; to find where a file is shared, filter on `ContentDocumentId`. Route the query through a selector so the constraint lives in one place.

**Why not the alternative:** a bare `SELECT ... FROM ContentDocumentLink` with no filter (or a filter on a different field) throws at runtime — there is no "return everything" mode for these objects.

### Keep Attachment under the ceiling with a bounded WHERE + LIMIT

**When to use:** querying attachments across many parent records.

**How it works:** filter to a bounded parent set (e.g. `WHERE ParentId IN :parentIds`) and add a `LIMIT` that keeps the result under 100,000; for large content workloads, migrate off `Attachment` to `ContentVersion` / `ContentDocument`, which are the modern file model.

**Why not the alternative:** granting View All Data to lift the cap trades a bounded query problem for an org-wide sharing hole; adding `OFFSET` does not help because the query fails before paging matters.

### Design the filter to match the big-object index

**When to use:** any query against a big object.

**How it works:** read the big object's index definition, then build the `WHERE` clause to cover the leading index fields with `=` and use a range operator (`<`, `>`, `<=`, `>=`, `IN`) only on the last field in the filter — never skip an index field. Avoid `LIKE`, `!=`, and `NOT IN` entirely.

**Why not the alternative:** treating a big object like a custom object (arbitrary fields, `LIKE`, out-of-order filters) produces a query that the platform rejects; there is no non-index path to the rows.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Query on `ContentDocumentLink` / `ContentHubItem` / `Vote` | Add the mandatory `WHERE` on an allowed field | The query is invalid without it — no unfiltered mode exists |
| `Attachment` result set could exceed 100,000 | Bounded `WHERE` + `LIMIT`, or migrate to `ContentVersion` | Query fails past the cap; migration is the durable fix |
| `TopicAssignment` / `NewsFeed` / `UserProfileFeed` query | Add `LIMIT` (1,100 / 1,000 / 1,000) | Required unless the user holds View All Data |
| Need more than 200 `UserRecordAccess` rows | Batch the IDs across multiple queries | 200 is a hard cap regardless of filter |
| `SELECT HasAccess ... FROM UserRecordAccess` | Add `ORDER BY HasAccess` | The object requires it when `HasAccess` is selected |
| Query on a big object | Filter index fields in order, `=` then one range op | Big objects filter only on indexed fields, no gaps |
| Query joins several external objects | Keep to ≤4 joins, subqueries ≤1,000 rows, no aggregates | External-object query caps are enforced by the connector |
| `KnowledgeArticleVersion` with a variable filter | Build dynamic SOQL, not an inline bind | Bind variables are not allowed on this object |
| A per-object limit is blocking you and View All Data would lift it | Scope the query instead of granting the permission | View All Data bypasses sharing org-wide, not just here |

---

## Recommended Workflow

1. **Locate the target object.** Read the `FROM` clause (and any subquery `FROM`s). If it is a standard/custom object with none of these names, this skill does not apply — check governor limits or selectivity instead.
2. **Classify the restriction.** Match the object to one of the four shapes: hard row cap, mandatory filter, required `LIMIT`, or restricted filter surface. The object table in the work template lists each one.
3. **Rewrite the query to comply.** Add the mandatory filter, add a bounded `LIMIT`, batch to stay under a row cap, or reshape the `WHERE` to the big-object index — *without* reaching for View All Data to make it pass.
4. **Centralize it in the selector layer.** Put the query in a selector that extends `templates/apex/BaseSelector.cls` so it runs `WITH USER_MODE` and the per-object constraint is written once and unit-tested.
5. **Test at the boundary and without elevated permissions.** Exercise the query with a dataset that approaches the cap, and — for permission-gated limits — run it as a user who does **not** hold View All Data (`System.runAs`).
6. **Run the checker before deploy.** `python3 scripts/check_soql_object_limits_and_restrictions.py --manifest-dir <path>` flags the missing-filter, missing-`LIMIT`, and bind-variable red flags statically.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every `ContentDocumentLink` / `ContentHubItem` / `Vote` query filters on an allowed field
- [ ] `Attachment` queries are bounded (filter + `LIMIT`) or the workload moved to `ContentVersion`
- [ ] `TopicAssignment` / `NewsFeed` / `UserProfileFeed` queries carry a `LIMIT` (or the View All Data dependency is documented and justified)
- [ ] `UserRecordAccess` usage stays within 200 rows and adds `ORDER BY HasAccess` when `HasAccess` is selected
- [ ] Big-object filters use only index fields, in order, with `=` on all but the last field
- [ ] External-object queries keep ≤4 joins and ≤1,000-row subqueries and avoid aggregate functions
- [ ] `KnowledgeArticleVersion` filters use dynamic SOQL, not inline bind variables
- [ ] No per-object failure was "fixed" by granting View All Data or switching to system mode

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The Attachment cap is a hard failure, not a truncation** — past 100,000 records the query errors out entirely; it does not silently return the first 100,000, and `OFFSET` cannot page around it. Add a filter + `LIMIT` or migrate to `ContentVersion`.
2. **UserRecordAccess is capped at 200 and demands an ORDER BY** — no filter raises the ceiling, and selecting `HasAccess` without `ORDER BY HasAccess` is invalid. Batch your IDs and always order by `HasAccess`.
3. **Big-object filters fail on gaps and on the wrong operator** — skipping an index field, or using `LIKE` / `!=` / `NOT IN`, produces a rejected query with no fallback path to the data.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Compliant SOQL query | A query rewritten to satisfy the object's mandatory filter, `LIMIT`, row cap, or index constraint |
| Selector method | The query centralized in a `BaseSelector` subclass, `WITH USER_MODE`, with the per-object rule encoded once |
| Checker report | Output of `check_soql_object_limits_and_restrictions.py` listing missing filters, missing `LIMIT`s, and bind-variable misuse |
| Remediation note | Which restriction applied, the fix chosen, and why View All Data was not used |

---

## Related Skills

- `apex/soql-fundamentals` — base SOQL syntax and structure; start there if the question is about writing a query at all, not an object-specific limit.
- `apex/governor-limits` and `apex/apex-limits-monitoring` — the generic per-transaction SOQL limits (query count, 50,000 rows retrieved) that these per-object rules sit on top of.
- `apex/apex-soql-relationship-queries` — relationship-query depth (child/parent join levels), a different family of limits from the external-object join cap.
- `apex/apex-dynamic-soql-binding-safety` — how to build the dynamic SOQL that `KnowledgeArticleVersion` requires without opening a SOQL-injection hole.
- `apex/apex-polymorphic-soql` — filtering on `Parent.Type`, relevant to the `Vote` object's allowed filters.
- `data/external-data-and-big-objects` and `integration/salesforce-connect-external-objects` — modelling big objects and external objects whose query surfaces this skill constrains.
- `data/soql-query-optimization` — selectivity and index tuning once the query is legal but slow.
