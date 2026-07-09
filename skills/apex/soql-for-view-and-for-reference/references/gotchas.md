# Gotchas — SOQL FOR VIEW and FOR REFERENCE

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: A read clause that quietly writes data

**What happens:** a code reviewer sees `SELECT ... FOR VIEW` and treats it as a harmless query,
but it performs DML side-effects — it updates `LastViewedDate` on each retrieved record and
inserts a `RecentlyViewed` row per record.

**When it occurs:** any time either clause runs. It matters most when the query sits in code that
is not obviously user-facing (a shared selector method reused by a batch job, for example), where
nobody expects a "read" to change state.

**How to avoid:** treat the clause as a deliberate write. Only place it on queries issued from a
genuine user-facing view/reference path, and keep it out of shared selector methods that batch or
async code also calls. If a method needs both a plain and a "mark viewed" variant, make them
separate methods.

---

## Gotcha 2: Misuse corrupts Recent Items and search auto-complete

**What happens:** records the user never opened start appearing in their Recent Items list and in
global-search auto-complete, making both surfaces noisy and untrustworthy.

**When it occurs:** the clause is applied to records that will *not* actually be viewed by the
logged-in user — an unbounded query, a list the user only scrolled past, or code running as a
batch/scheduled/integration user. The docs are explicit: use the clauses "only when you are sure
that the retrieved records will definitely be viewed by the logged-in user, else the clause
incorrectly updates the usage information for the records."

**How to avoid:** bound every query that carries the clause to the specific record(s) the user is
viewing (`WHERE Id = :id` / `WHERE Id IN :ids` + `LIMIT`), and never add the clause in
non-user-facing execution contexts.

---

## Gotcha 3: `No such column 'LastViewedDate'` on a custom object

**What happens:** the exact same query that works on a standard object throws
`System.QueryException: No such column 'LastViewedDate'` (or `LastReferencedDate`) on a custom
object, and by extension the `FOR VIEW` / `FOR REFERENCE` clauses fail against it.

**When it occurs:** the custom object has no custom tab. The recency fields are provisioned as
part of the object's tab definition and simply do not exist until a tab is created.

**How to avoid:** create a custom tab for the object (Setup → Tabs → Custom Object Tabs → New).
The tab does not need to be visible in the navigation bar — its existence alone activates the
fields. After that, the fields are queryable and the clauses work.

---

## Gotcha 4: `RecentlyViewed` ages out and truncates — it is not an audit trail

**What happens:** a record that was correctly marked viewed disappears from Recent Items later,
or a report built on `RecentlyViewed` shows far fewer rows than expected.

**When it occurs:** `RecentlyViewed` is deliberately ephemeral — "RecentlyViewed data is retained
for 90 days, after which it is removed on a periodic basis," and it "is periodically truncated
down to 200 records per object." A record drops out once it is older than 90 days or falls
outside the newest 200 rows for its object.

**How to avoid:** never treat `RecentlyViewed`, `LastViewedDate`, or `LastReferencedDate` as a
durable history or compliance record. If you need a permanent view/access log, capture it in your
own object (or use field history / event monitoring), not this recency data.

---

## Gotcha 5: Trying to update both recency fields from one query

**What happens:** a developer reads "use the FOR VIEW clause in conjunction with the FOR REFERENCE
clause" and writes a single query with both clauses, expecting `LastViewedDate` and
`LastReferencedDate` to update together — but the reference never shows a combined single-query
example, and the `SELECT` grammar lists them as an alternation `{FOR VIEW | FOR REFERENCE}`.

**When it occurs:** whenever someone assumes the two trailing clauses compose like independent
options in the same statement.

**How to avoid:** pick the one clause that matches the real interaction (a full view →
`FOR VIEW`; a reference → `FOR REFERENCE`). Treat "update both fields from one query" as
under-documented and do not ship a combined syntax the reference does not print. A full view
already implies a reference for most UX purposes, so a single `FOR VIEW` is usually sufficient.
