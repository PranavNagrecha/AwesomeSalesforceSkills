# Gotchas — SOQL Object Limits and Restrictions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Attachment cap fails hard — it does not truncate or paginate

**What happens:** a query on `Attachment` that would return more than 100,000 records errors out
entirely. It does not return the first 100,000 rows, and adding `OFFSET` does not let you page
around it because the failure happens before paging applies.

**When it occurs:** any org with a large volume of attachments in the query's scope, especially
an unbounded `SELECT ... FROM Attachment` in a batch or scheduled job that "worked in the sandbox."

**How to avoid:** bound the `WHERE` (e.g. `ParentId IN :ids`) and add an explicit `LIMIT` under
100,000, or migrate the workload to `ContentVersion` / `ContentDocument`. Do not lift the cap by
granting View All Data.

---

## Gotcha 2: UserRecordAccess caps at 200 and requires ORDER BY HasAccess

**What happens:** a `UserRecordAccess` query never returns more than 200 records, and selecting
`HasAccess` without `ORDER BY HasAccess` throws a query-compilation error.

**When it occurs:** bulk access checks — building a list of "records the user can edit" for more
than 200 candidate records, or copying a `SELECT HasAccess ...` snippet without the ordering.

**How to avoid:** chunk the candidate IDs into batches of 200 and issue one query per batch;
always add `ORDER BY HasAccess` whenever `HasAccess` is in the `SELECT`.

---

## Gotcha 3: Big-object filters reject gaps and non-equality operators

**What happens:** a big-object query is rejected even though the fields exist, because the filter
skips an index field, filters them out of index order, or uses an unsupported operator.

**When it occurs:** treating a big object like a custom object — filtering on a non-index field,
using `LIKE` / `!=` / `NOT IN` / `EXCLUDES` / `INCLUDES`, or using a range operator on a field
that is not the last one in the filter.

**How to avoid:** filter the index fields in their defined order with no gaps, use `=` on every
field except the last, and reserve `<`, `>`, `<=`, `>=`, `IN` for that last field only.

---

## Gotcha 4: KnowledgeArticleVersion rejects inline bind variables

**What happens:** an inline SOQL query like `[SELECT Id FROM KnowledgeArticleVersion WHERE
Title LIKE :term]` fails; the object does not accept Apex bind variables in a static query.

**When it occurs:** any parameterized `KnowledgeArticleVersion` query written as inline Apex SOQL
rather than dynamic SOQL.

**How to avoid:** build the query as a string and run it with `Database.queryWithBinds`
(or `Database.query`), passing the bound values through the binds map and escaping any user
input with `String.escapeSingleQuotes` to stay injection-safe.

---

## Gotcha 5: View All Data silently lifts several limits — masking a security hole

**What happens:** a query that failed on the `Attachment` cap or a required `LIMIT`
(`TopicAssignment`, `NewsFeed`, `UserProfileFeed`) suddenly "works" after the running user is
granted View All Data or the code is moved to system mode.

**When it occurs:** a well-meaning fix for a failing query, or reusing a system-mode context
where the limit simply does not apply. The query passes review because it now runs.

**How to avoid:** treat a limit that lifts under View All Data as a signal to *scope the query*,
not to widen access. View All Data bypasses sharing for the whole transaction, not just the
object that was failing — keep the query in `WITH USER_MODE` and add the filter or `LIMIT` instead.

---

## Gotcha 6: RecentlyViewed is a 90-day rolling window, not a history table

**What happens:** a query on `RecentlyViewed` returns fewer records than expected, or older
entries are simply gone.

**When it occurs:** treating `RecentlyViewed` as a durable log of everything a user has opened.
Rows are retained for only 90 days and the object is periodically truncated to about 200 records
per object.

**How to avoid:** use `RecentlyViewed` for recent-activity UX only; if you need a durable audit
of views, capture it yourself (e.g. a custom object or event) rather than querying `RecentlyViewed`.
