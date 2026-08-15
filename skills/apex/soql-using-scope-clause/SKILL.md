---
name: soql-using-scope-clause
description: "Use when writing or reviewing a SOQL query (in Apex, a selector, or via the API) that must return only a subset of records defined by ownership, team, territory, delegation, or an active scoping rule — through the optional USING SCOPE filterScope clause (mine, everything, team, delegated, my_territory, my_team_territory, mine_and_my_groups, scopingRule) placed after FROM and before WHERE. Also covers the mandatory USING SCOPE EVERYTHING requirement for the Scoping Rules SOQL operator. NOT for plain SELECT / WHERE / ORDER BY syntax — use apex/soql-fundamentals. NOT for WITH USER_MODE or CRUD/FLS enforcement — use apex/soql-security. NOT for the with sharing / without sharing choice — use apex/apex-with-without-sharing-decision. NOT the Metadata API ListView filterScope enum (different casing and value set), and NOT for authoring scoping rules beyond their SOQL-operator criteria."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
triggers:
  - "limit a SOQL query to records owned by the running user without hardcoding an OwnerId filter"
  - "return only my records or my team's records from an Apex query"
  - "figure out where USING SCOPE goes in a SELECT statement — before or after WHERE"
  - "query only delegated tasks or records in the running user's territory"
  - "fix an error from USING SCOPE EVERYTHING inside a scoping rule's SOQL operator"
tags:
  - soql
  - using-scope
  - filterscope
  - query-scope
  - scoping-rules
inputs:
  - "The SOQL query or selector method to scope, and the sObject it targets"
  - "The desired audience filter: owned-by-me, my team, my territory, delegated, queues, or a scoping rule"
  - "The execution context (interactive user vs. async/scheduled/system) so 'the running user' is unambiguous"
outputs:
  - "A correctly positioned USING SCOPE clause (after FROM, before WHERE) using a valid filterScope value"
  - "A describe-backed confirmation that the target object supports the chosen scope"
  - "Guidance on pairing the scope with WITH USER_MODE / with sharing so the query is also secure"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# SOQL USING SCOPE Clause

This skill activates when a query needs to return records for a specific audience — the running user, their team, their territory, their queues, or an active scoping rule — using the optional `USING SCOPE filterScope` clause instead of a hand-written `OwnerId`/relationship filter. It also covers the one place the clause is *mandatory*: the `USING SCOPE EVERYTHING` requirement of the Scoping Rules SOQL operator.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the object supports the scope you want.** Supported scopes vary per object. The docs are explicit: "To get a list of scopes supported by an object, call describeSObject() for SOAP API or sObject Describe for REST API." Do not assume `team` or `my_territory` exists on an arbitrary object.
- **Know it is a filter, not a security boundary.** `USING SCOPE mine` limits *which rows* come back by ownership; it does **not** enforce CRUD, FLS, or sharing. Pair it with `WITH USER_MODE` (Summer '23+) or a `with sharing` + `SecurityUtils` edge check.
- **Pin down "the running user."** `mine`, `my_territory`, and `my_team_territory` resolve against the user *running the query*. In a scheduled job, batch, `@future`, or trigger-driven automation that may be the Automated Process user or the enqueuing user — not the end user you pictured.
- **Check prerequisites.** Territory scopes require territory management enabled; `scopingRule` requires an admin to have activated at least one scoping rule on the object; `mine_and_my_groups` applies only to `ProcessInstanceWorkItem`.
- **Know the API floor and maturity.** The clause is "Available in API version 32.0 and later." The docs give **no** GA/Beta/Pilot label for the clause itself — treat it as a standard SOQL language feature and do not assert a maturity level. The related Scoping Rules SOQL-operator feature is edition-gated (see Core Concepts).

---

## Core Concepts

### What the clause does and where it goes

"The optional USING SCOPE clause of a SOQL query returns records within a specified scope." Its position in the `SELECT` grammar is fixed — immediately after `FROM`, before `WHERE`:

```
SELECT fieldList [subquery][...]
FROM objectType[,...]
    [USING SCOPE filterScope]
[WHERE conditionExpression]
```

Getting this order wrong is a compile-time SOQL error, not a silent no-op.

### The filterScope enumeration

There are eight documented values. Each has object- or edition-specific constraints:

| filterScope | Returns | Constraint |
|---|---|---|
| `delegated` | Records delegated to another user for action (e.g. delegated Tasks) | — |
| `everything` | All (accessible) records | Effectively a no-op filter on most objects; **mandatory** for the Scoping Rules SOQL operator |
| `mine` | Records owned by the user running the query | — |
| `mine_and_my_groups` | Records assigned to the running user and the user's queues | **Only** the `ProcessInstanceWorkItem` object |
| `my_territory` | Records in the running user's territory | Territory management must be enabled |
| `my_team_territory` | Records in the territory of the running user's team | Territory management must be enabled |
| `scopingRule` | Records matching the applicable scoping rule | An admin must have activated at least one scoping rule on the object |
| `team` | Records assigned to a team, such as an Account team | Object must support teams |

### It is a data filter, not sharing enforcement

`USING SCOPE mine` narrows results to rows the running user owns, but it does nothing about field-level or object-level access. A query with `USING SCOPE mine` running in `without sharing` still returns owned rows; a query with no scope but `WITH USER_MODE` still enforces security. They are orthogonal — use both when you need "my rows, safely."

### USING SCOPE EVERYTHING and scoping rules

The Scoping Rules feature lets a query be embedded in a rule's record criteria via the SOQL operator. There the clause is not optional: "The SELECT statement, including nested SELECT statements, must include USING SCOPE EVERYTHING. USING SCOPE EVERYTHING is the only valid scope clause syntax for scoping rules." That feature is GA and edition-gated — "Available in: Lightning Experience in Performance and Unlimited Editions." It also does not support `$User` syntax except `$User.Id`, and dynamic queries inside the operator are unsupported.

---

## Common Patterns

### "My records" list without a hardcoded OwnerId filter

**When to use:** a controller, selector, or list view logic needs the running user's own rows.

**How it works:** put `USING SCOPE mine` after `FROM`; add `WITH USER_MODE` so security is enforced too.

```apex
List<Case> myOpen = [
    SELECT Id, CaseNumber, Subject, Status
    FROM Case
    USING SCOPE mine
    WHERE IsClosed = false
    WITH USER_MODE
    ORDER BY CreatedDate DESC
];
```

**Why not the alternative:** `WHERE OwnerId = :UserInfo.getUserId()` only matches direct ownership and misses platform semantics (e.g. delegated/queue cases); the scope keyword is the maintained, describe-backed path.

### Territory- or team-scoped selector method

**When to use:** reporting or automation that must respect the running user's territory or account team, in the Selector layer.

**How it works:** query through a selector so all SOQL stays in one place; keep `USING SCOPE` in the query string and pass user mode as the `AccessLevel`. See `templates/apex/BaseSelector.cls` for the base class this extends.

**Why not the alternative:** rebuilding territory/team membership in a `WHERE` clause duplicates platform data and drifts the moment assignments change.

### Scoping-rule record criteria (EVERYTHING everywhere)

**When to use:** authoring the SOQL operator inside a scoping rule's criteria.

**How it works:** every `SELECT`, including nested subqueries, carries `USING SCOPE EVERYTHING`; no other scope value is legal there.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need the running user's own rows | `USING SCOPE mine` + `WITH USER_MODE` | Ownership filter plus real security enforcement |
| Need approval items awaiting me or my queues | `USING SCOPE mine_and_my_groups` on `ProcessInstanceWorkItem` | The only object this scope supports |
| Need territory-scoped rows | `USING SCOPE my_territory` / `my_team_territory` | Requires territory management; avoids reinventing membership |
| Writing the SOQL operator in a scoping rule | `USING SCOPE EVERYTHING` on every SELECT | It is the *only* valid scope there, nested subqueries included |
| Unsure whether an object supports a scope | Call `describeSObject()` / sObject Describe first | Supported scopes are object-specific and must be discovered |
| Trying to enforce record-level security | Do **not** rely on `USING SCOPE` | It is a filter, not sharing/FLS — use `WITH USER_MODE` + `with sharing` |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Clarify the audience and context.** Which subset (mine / team / territory / delegated / queues / scoping rule), and who is "the running user" in this execution context (interactive vs. async/system)?
2. **Confirm object support.** Verify the target object exposes the chosen scope via `describeSObject()` / sObject Describe (and that any prerequisite — territory management, an active scoping rule — is in place).
3. **Place the clause correctly.** Insert `USING SCOPE <value>` after `FROM` and before `WHERE`; use the exact lowercase value (`everything`, `mine`, …), not a Metadata API casing.
4. **Add security separately.** Because scope is not enforcement, add `WITH USER_MODE` (or run `with sharing` + `SecurityUtils` CRUD/FLS checks) so the query is both scoped and secure.
5. **Handle the scoping-rule case explicitly.** If the query lives in a scoping rule's SOQL operator, force `USING SCOPE EVERYTHING` on the outer and every nested `SELECT`.
6. **Lint and test.** Run `scripts/check_soql_using_scope_clause.py` over the source tree, then test with a non-admin user (and, for async paths, assert results under the actual running user) to confirm the scope behaves as intended.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `USING SCOPE` appears after `FROM` and before `WHERE`
- [ ] The scope value is one of the eight documented values, in SOQL (lowercase) casing — not a Metadata API `filterScope` value like `Queue` or `AssignedToMe`
- [ ] The target object was confirmed (via describe) to support the chosen scope, and any prerequisite is enabled
- [ ] `mine_and_my_groups` is used only on `ProcessInstanceWorkItem`
- [ ] The query also enforces security (`WITH USER_MODE` or `with sharing` + CRUD/FLS) — scope alone is not enough
- [ ] "The running user" is the intended principal in this context (checked for async/scheduled/system execution)
- [ ] Any scoping-rule SOQL operator uses `USING SCOPE EVERYTHING` on every SELECT, nested subqueries included

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Scope is not security** — `USING SCOPE mine` filters by ownership but grants no FLS/CRUD/sharing enforcement. A reviewer who reads it as a security control will ship an over-permissive query. Add `WITH USER_MODE`.
2. **"The running user" shifts in async/system contexts** — `mine`/territory scopes resolve against whoever runs the query. In a scheduled job or batch that is often the Automated Process or enqueuing user, so the query silently returns the wrong person's (often zero) rows.
3. **Wrong enum entirely** — the Metadata API `ListView.filterScope` (`Everything`, `Mine`, `Queue`, `AssignedToMe`, `SalesTeam`, …) looks similar but is a *different* enumeration with different casing and extra values; `Queue`/`AssignedToMe`/`SalesTeam` are not valid SOQL scopes.

See `references/gotchas.md` for the full set and `references/llm-anti-patterns.md` for AI-assistant-specific mistakes.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Scoped SOQL query / selector method | A query with a correctly positioned, valid `USING SCOPE` clause paired with user-mode security |
| Describe confirmation note | Evidence that the target object supports the chosen scope (and prerequisites are met) |
| `scripts/check_soql_using_scope_clause.py` output | Lint findings: invalid/misordered/miscased scope usage across `.cls`/`.trigger`/`.soql` files |
| `templates/soql-using-scope-clause-template.md` | A planning + reference sheet (clause position, full scope table, checklist) |

---

## Related Skills

- `apex/soql-fundamentals` — base SELECT grammar and clause ordering this clause slots into.
- `apex/soql-security` — `WITH USER_MODE` / CRUD / FLS enforcement, the security layer `USING SCOPE` does *not* provide.
- `apex/apex-with-without-sharing-decision` — record-level sharing enforcement; distinct from ownership scoping.
- `apex/apex-dynamic-soql-binding-safety` — building dynamic query strings safely when the scope is chosen at runtime.
- `apex/territory-api-and-assignment` — territory management prerequisites for the `my_territory` / `my_team_territory` scopes.
