### Gotchas — Apex With / Without / Inherited Sharing Decision

Non-obvious Salesforce platform behaviors that cause real production
problems when choosing a sharing keyword.

## Gotcha 1: Sharing inherits through static method calls

**What happens:** `ServiceA.with sharing` calls `Util.doWork()` (no
keyword on `Util`). The query inside `doWork` runs `with sharing`.
Later, `BatchB.without sharing` calls the same `Util.doWork()` — and
the query now runs `without sharing`. The same line of code returns
different records depending on the caller.

**When it occurs:** any time a service / selector / utility class lacks
an explicit keyword and is called from multiple entry points.

**How to avoid:** declare `inherited sharing` explicitly on shared
utilities. Reviewers and the runtime then know the inheritance is
deliberate, and a future refactor cannot silently change semantics.

---

## Gotcha 2: Managed-package class always runs `without sharing` regardless of caller

**What happens:** A managed package's internal class declares (or
defaults to) `without sharing`. When a subscriber-org `with sharing`
class invokes it, the managed-package code still runs `without sharing`
inside the package's namespace. The subscriber cannot tighten it.

**When it occurs:** any time you integrate with an AppExchange package
or 1GP/2GP package you do not own.

**How to avoid:** assume packaged code runs unrestricted. Wrap returned
record IDs through your own `with sharing` selector before exposing
them to a UI. Treat the package boundary as a trust boundary.

---

## Gotcha 3: `@AuraEnabled` on a bare class is not implicitly `with sharing` in all contexts

**What happens:** A class with `@AuraEnabled` methods and no class-level
sharing keyword. Most LWC entry-point invocations run `with sharing`
since API v34. But if that same class is called from another `without
sharing` Apex class (e.g., a Queueable that re-uses the controller
method), it runs `without sharing`. Reviewers see "it's an AuraEnabled
controller" and assume safety; the second caller path breaks the
assumption.

**When it occurs:** controllers that are also re-used as utility
methods by background jobs.

**How to avoid:** always explicitly declare `with sharing` on
`@AuraEnabled` classes. Never rely on the implicit Lightning default.

---

## Gotcha 4: Aggregate queries respect class sharing — silent under-counts

**What happens:** A `with sharing` class runs
`SELECT COUNT() FROM Opportunity WHERE IsClosed = true`. The result
counts only opportunities the running user can see. A dashboard tile
backed by this query shows different numbers depending on who loads the
page — and is silently wrong for users with limited perimeter.

**When it occurs:** Apex-backed dashboard tiles, KPI controllers,
analytics surfaces, anywhere `SUM`/`COUNT`/`AVG` is used in a
sharing-enforced class.

**How to avoid:** for org-wide metrics, use a `without sharing` class
(with `// reason:` comment) or `WITH SYSTEM_MODE` on the aggregate
query. Document the elevation in the metric's surface so users know
they're seeing org-wide totals.

---

## Gotcha 5: Trigger handlers default to `without sharing`-like behavior if bare

**What happens:** A trigger handler class with no sharing keyword. The
trigger body itself runs in system context, so DML happens regardless.
But SOQL queries inside the handler — fetching related records, e.g.,
`SELECT Id FROM Account WHERE Id IN :triggerNew` — run without sharing
unless the handler explicitly declares `with sharing`. New records show
up that the actor would normally not be able to see, and downstream
logic (e.g., assignment rules driven by the handler) misbehaves.

**When it occurs:** trigger handlers written without explicit sharing
declaration; especially common in trigger-handler frameworks where the
base class is bare.

**How to avoid:** explicitly declare a keyword on every handler. Most
handlers want `without sharing` (system context for the trigger is
intentional), but the keyword must be deliberate and documented, not
defaulted.

---

## Gotcha 6: `WITH USER_MODE` enforces FLS/CRUD, not just sharing

**What happens:** A developer adds `WITH USER_MODE` to a query expecting
it to "make this query respect sharing." It does — and also begins
enforcing field-level security and object permissions. A query that
selects 12 fields suddenly throws `QueryException` because the user
lacks read on field 7.

**When it occurs:** retrofitting `WITH USER_MODE` onto legacy queries
inside a `without sharing` class without auditing the field list.

**How to avoid:** before adding `WITH USER_MODE`, run the query as the
target persona in a sandbox. Verify FLS coverage with
`Schema.describeSObjects(...)` or restrict the field list to ones in
the user's permission set. Treat `WITH USER_MODE` as a full
user-context query, not a sharing-only filter.
