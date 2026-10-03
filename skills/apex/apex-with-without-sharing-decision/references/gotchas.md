### Gotchas — Apex With / Without / Inherited Sharing Decision

Non-obvious Salesforce platform behaviors that cause real production
problems when choosing a sharing keyword.

## Gotcha 1: Sharing inherits through static method calls

**What happens:** at **API ≤ 66.0** — `ServiceA.with sharing` calls
`Util.doWork()` (no keyword on `Util`). The query inside `doWork` runs
`with sharing`. Later, `BatchB.without sharing` calls the same
`Util.doWork()` — and the query now runs `without sharing`. The same line
of code returns different records depending on the caller. At **API
67.0+** a bare `Util` stops following the caller and runs `with sharing`
in both paths, which silently breaks `BatchB` instead: the surprise moves
from the controller path to the batch path, it does not go away.

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

**What happens:** version-gated on the `apiVersion` in the class's own
`.cls-meta.xml`, not the org's release. At **API 67.0+** a bare class
runs `with sharing` and this gotcha is closed. At **API ≤ 66.0** a class
with `@AuraEnabled` methods and no class-level keyword runs `with
sharing` for most LWC entry-point invocations (since API v34) — but if
that same class is called from another `without sharing` Apex class
(e.g., a Queueable that re-uses the controller method), it runs `without
sharing`. Reviewers see "it's an AuraEnabled controller" and assume
safety; the second caller path breaks the assumption.

**When it occurs:** controllers that are also re-used as utility
methods by background jobs.

**How to avoid:** always explicitly declare `with sharing` on
`@AuraEnabled` classes. Never rely on the implicit Lightning default, and
never rely on the 67.0+ default either — an `apiVersion` change moves it.

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

## Gotcha 5: The trigger body's own query and DML mode is version-gated, and so is a bare handler's

**What happens:** A trigger handler class with no sharing keyword, called
from a trigger. A trigger itself cannot declare a sharing keyword and
always runs in an implicit `without sharing` context, but its own
database operations are version-split. At trigger **API 67.0+**, SOQL,
SOSL, DML and `Database` methods in the trigger body run in **user mode**
unless system mode is stated, and user mode overrides the implicit
`without sharing` — the running user's sharing, FLS and object
permissions apply, so a trigger saved at 67.0 can suddenly see fewer
related records or throw on a field the user cannot read. Before 67.0 the
same operations run in **system mode**. The handler keyword does not
change the trigger body's own operations; what it governs is the
handler's own SOQL, and that default inverted at 67.0 too. At
**API ≤ 66.0**, `SELECT Id FROM Account WHERE Id IN :triggerNew` in a
bare handler ran without sharing: records showed up that the actor could
not normally see, and downstream logic (e.g., assignment rules driven by
the handler) misbehaved. At **API 67.0+** the same bare handler runs
`with sharing` — the opposite surprise, where a handler that needs
cross-perimeter reads silently starts filtering them.

**When it occurs:** trigger handlers written without explicit sharing
declaration; especially common in trigger-handler frameworks where the
base class is bare.

**How to avoid:** explicitly declare a keyword on every handler, and
state an access mode on every database operation in the trigger body
itself (`WITH SYSTEM_MODE` / `AccessLevel.SYSTEM_MODE` only where all
records are genuinely needed). Most handlers want `without sharing`, but
the keyword must be deliberate and documented, not defaulted. Do not
assume "triggers are system mode" on a class or trigger saved at 67.0+.

**Source:** Apex Developer Guide v67.0, *Using the with sharing, without
sharing, and inherited sharing Keywords* (Implementation in Apex
Triggers): "Triggers always run implicitly in a without sharing context",
and database operations in trigger bodies "run in user mode unless system
mode is explicitly specified. User mode overrides the trigger's without
sharing context and effectively enforces a with sharing context in the
trigger body." Also recorded in
`skills/apex/soql-security/references/gotchas.md` Gotcha 6.

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
