# Gotchas — SOQL USING SCOPE Clause

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: USING SCOPE is a filter, not a security boundary

**What happens:** a query with `USING SCOPE mine` is treated as record-level security, so it
ships without any FLS/CRUD/sharing enforcement and leaks fields the user shouldn't read — or is
assumed to hide records that were actually shared to the user (it doesn't).

**When it occurs:** the query runs in a `without sharing` (or system-mode) context, or a reviewer
reads the scope keyword as an access control.

**How to avoid:** treat scope and security as orthogonal. Keep `USING SCOPE` for the audience
filter and add `WITH USER_MODE` (Summer '23+) or `with sharing` + `SecurityUtils` CRUD/FLS checks
for enforcement.

---

## Gotcha 2: "The running user" is not always the end user

**What happens:** a query that works interactively returns zero (or someone else's) rows when it
runs in a scheduled job, batch, `@future`, Queueable, or trigger-driven automation.

**When it occurs:** `mine`, `my_territory`, and `my_team_territory` resolve against whoever is
running the query. In async/system execution that principal can be the Automated Process user or
the user who enqueued the job — not the person you designed the feature for.

**How to avoid:** decide explicitly who "the running user" is in each context. If you need a
*specific* user's records in automation, filter by `OwnerId`/relationship instead of relying on
`mine`, or run the work in the correct user context.

---

## Gotcha 3: Wrong enumeration — Metadata API filterScope leaks into SOQL

**What happens:** a scope like `Queue`, `AssignedToMe`, `SalesTeam`, or PascalCase `Everything`
throws a SOQL error, or an LLM/tool copies a list-view value into a query.

**When it occurs:** the author confuses the SOQL `filterScope` (`delegated`, `everything`, `mine`,
`mine_and_my_groups`, `my_territory`, `my_team_territory`, `scopingRule`, `team`) with the
Metadata API `ListView.filterScope` enum, which is a *different* set (it adds `Queue`,
`AssignedToMe`, `MineAndMyGroups`, `SalesTeam`, PascalCase casing, etc.).

**How to avoid:** use only the eight documented SOQL values in SOQL. `Queue`, `AssignedToMe`, and
`SalesTeam` do not exist as SOQL scopes — they belong to list-view metadata.

---

## Gotcha 4: mine_and_my_groups only works on ProcessInstanceWorkItem

**What happens:** `USING SCOPE mine_and_my_groups` on an object like Case or Lead is invalid.

**When it occurs:** the author generalizes the "me and my queues" behavior beyond approvals.

**How to avoid:** restrict `mine_and_my_groups` to `ProcessInstanceWorkItem` (the documented sole
object). For queue-owned records on other objects, filter on `Owner.Type`/queue membership.

---

## Gotcha 5: Object- and edition-specific scope support

**What happens:** `team`, `my_territory`, `my_team_territory`, or `scopingRule` throws on an object
or org that doesn't support it.

**When it occurs:** the object doesn't expose that scope, territory management isn't enabled, no
scoping rule is active, or (for the Scoping Rules SOQL operator) the org isn't a Lightning
Experience Performance/Unlimited Edition.

**How to avoid:** discover supported scopes per object — "call describeSObject() for SOAP API or
sObject Describe for REST API to determine scopes supported by an object" — and verify the
prerequisite (territory management on, an active scoping rule, correct edition) before shipping.

---

## Gotcha 6: Clause misplacement is a hard SOQL error

**What happens:** `SELECT ... FROM Account WHERE IsDeleted = false USING SCOPE mine` fails to
compile.

**When it occurs:** the author places `USING SCOPE` after `WHERE` (SQL habit) or before `FROM`.

**How to avoid:** follow the grammar exactly — `SELECT fieldList FROM objectType USING SCOPE
filterScope WHERE conditionExpression`. The clause is always after `FROM` and before `WHERE`.

---

## Gotcha 7: Scoping rules demand EVERYTHING in nested SELECTs too

**What happens:** a scoping-rule SOQL operator with `USING SCOPE EVERYTHING` on the outer query
but not on a nested subquery is rejected, or an author uses `mine`/omits the scope entirely.

**When it occurs:** authoring the SOQL operator inside a scoping rule's record criteria.

**How to avoid:** put `USING SCOPE EVERYTHING` on every `SELECT`, including nested subqueries — it
"is the only valid scope clause syntax for scoping rules." Remember the operator supports only
`$User.Id` (no other `$User` fields) and no dynamic queries.
