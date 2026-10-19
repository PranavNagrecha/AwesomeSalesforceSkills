---
name: apex-with-without-sharing-decision
description: "Choosing the sharing keyword on an Apex class: with sharing vs without sharing vs inherited sharing, how it flows through called methods, and when WITH USER_MODE overrides it. NOT for enforcing CRUD/FLS on the records themselves — use apex/apex-stripinaccessible-and-fls-enforcement. NOT for granting row access via __Share records — use apex/apex-managed-sharing."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "should this apex class be with sharing or without sharing"
  - "auraenabled controller running as system context unexpectedly"
  - "inherited sharing keyword apex when to use"
  - "without sharing utility called from with sharing controller"
  - "managed package class ignoring caller sharing rules"
  - "with user_mode vs with sharing class keyword difference"
  - "trigger handler default sharing behavior surprising users"
  - "why does a with system_mode query in a with sharing class still hide records"
tags:
  - apex
  - sharing
  - security
  - record-access
  - user-mode
  - controller
  - service-layer
inputs:
  - Apex class purpose (controller, service, batch, trigger handler, utility)
  - Caller context (LWC / Aura / REST / Batch / Trigger / Schedulable)
  - Whether the class needs to read or write records the running user cannot see
  - Presence of @AuraEnabled, @InvocableMethod, @RestResource annotations
  - Whether calls use SOQL/DML in WITH USER_MODE / WITH SYSTEM_MODE
outputs:
  - Recommended sharing keyword (with / without / inherited) with justification
  - Required `// reason:` comment text when without sharing is chosen
  - Per-query override plan using WITH USER_MODE where appropriate
  - Reviewer checklist confirming inherited-method risks are handled
dependencies: []
version: 1.1.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# Apex With / Without / Inherited Sharing Decision

Activate when an author is creating a new Apex class, refactoring one, or
reviewing a PR and the question is the narrow one: **what sharing keyword
goes on this class right now?** This is a code-author decision, distinct
from the org-level sharing-mechanism choice in
`standards/decision-trees/sharing-selection.md`.

---

## Before Starting

Gather this context before deciding:

- **Entry point.** Is the class invoked from an LWC `@AuraEnabled` method,
  a REST `@HttpGet`, a batch `Database.executeBatch`, a trigger handler,
  a Flow `@InvocableMethod`, or chained from another Apex class?
- **Record visibility intent.** Should the user see only what their
  sharing rules permit, or does the operation legitimately need to read
  and write records they cannot normally see (e.g., audit aggregation,
  approval routing, compliance scrubbing)?
- **Caller context.** If this class will be called from other Apex,
  remember that only an `inherited sharing` class — or a bare class
  pinned at API ≤ 66.0 — takes its mode from the caller. An explicit
  `with` / `without sharing` keyword holds whoever calls it: "the sharing
  mode of a method is determined by where the method is defined, not
  where it's called from" (Apex Developer Guide L4927).
- **Annotations on the class.** `@AuraEnabled`, `@RemoteAction`, and
  `@RestResource` classes are user-facing entry points and **must default
  to `with sharing`** unless you have a documented elevation reason.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| What `apiVersion` is in the class's `.cls-meta.xml`? | Both the bare-class sharing default and the default access mode flip at 67.0 (Gotchas 1, 3, 7) | The row of the version table every later answer is judged against |
| Which entry points reach this class — LWC/Aura, REST, Flow, batch, trigger, other Apex? | An `inherited sharing` class — or a bare one pinned at API ≤ 66.0 — takes its mode from whoever calls it (Gotchas 1, 3) | The full caller list, so no second path silently changes the mode |
| Must this operation return records the running user cannot see — which ones, and why? | Row elevation needs a `without sharing` class plus system mode at 67.0+; system mode alone in a `with sharing` class still filters rows (Gotcha 7) | A named record set and a `// reason:` sentence, scoped to one small helper |
| Is the elevation about rows (sharing) or about fields and objects (FLS/CRUD)? | System mode lifts only FLS and object checks; `WITH USER_MODE` adds FLS on top of sharing (Gotchas 6, 7) | The right tool per statement instead of a class flip |
| Is any number this class returns meant to be org-wide (`COUNT`, `SUM`, KPI tile)? | Aggregates obey the class keyword and the access mode, and under-count silently (Gotcha 4) | A decision, shown on the surface, between org-wide and per-user totals |
| Does the class call, or get called by, managed-package code? | Packaged code keeps its own keyword; the subscriber cannot tighten it (Gotcha 2) | A trust boundary where returned IDs are re-read through your own selector |
| Is this a trigger handler, and what does the trigger body itself query? | The trigger body's mode is version-split and independent of the handler keyword (Gotcha 5) | An explicit access mode on every trigger-body operation and an explicit handler keyword |

A proper configuration over "just add a keyword" leaves each class with
a keyword a reviewer can audit, keeps any row elevation inside one small
justified helper instead of a whole controller, and survives an
`apiVersion` bump without changing who sees what.

---

## Core Concepts

### The three keyword choices

`with sharing` / `without sharing` / `inherited sharing` differ on **whose** sharing rules apply to direct SOQL queries. Field-Level Security and CRUD are a separate enforcement concern (`WITH USER_MODE`, `Security.stripInaccessible`; `WITH SECURITY_ENFORCED` only on classes at API ≤ 66.0 — it is removed in 67.0 and does not compile there) and are **not** controlled by these keywords.

| Keyword | Sharing applied to direct SOQL | Default for what entry points | When to use |
|---|---|---|---|
| `with sharing` | Running user's sharing rules enforced; invisible records filtered out | `@AuraEnabled`, `@RemoteAction`, `@RestResource` (must default here) | Any user-facing entry point unless you have a documented elevation reason |
| `without sharing` | Running user's sharing rules ignored for this class's own **system-mode** queries — at API 67.0+ a query with no mode clause runs in user mode and still enforces sharing (Apex Developer Guide L11954-11961) | None — never a safe default | Audit aggregation, approval routing, compliance scrubbing — deliberate elevation only |
| `inherited sharing` | Adopts the **caller's** mode; **defaults to `with sharing`** when called directly from Lightning/REST/Aura | Reusable utilities, selectors, base service classes | Shared service/selector code that should respect whatever the entry point demanded |

`without sharing` is a record-visibility keyword, not a blanket system context. It does not turn off FLS or CRUD — and at API 67.0+ database operations enforce the running user's FLS and object permissions by default with no keyword at all, so an elevation that genuinely needs them off states it per statement (`WITH SYSTEM_MODE`, `AccessLevel.SYSTEM_MODE`).

### Sharing is inherited through method calls

A class that explicitly declares `with sharing` keeps its own mode no
matter who calls it. What a **bare** callee does depends on its own
`apiVersion` (see "Bare class behavior" below): at **API ≤ 66.0** the
outermost class on the call stack governs it, so a `with sharing`
controller makes the bare service run `with sharing` while a `without
sharing` controller makes the same service run `without sharing`. At
**API 67.0+** the bare callee no longer follows the caller down — it runs
`with sharing` on its own. Either way the callee's behavior is decided
somewhere other than its source, so always declare an explicit keyword on
shared service / selector layers.

### Where `inherited sharing` fits

Reusable utilities, selectors, and base service classes that should
respect whatever the entry point demanded. `inherited sharing` is the
explicit way to say "I do not want to override the caller's choice, but I
also do not want to be ambiguous about it." It also produces a safe
default (with sharing) when called from Lightning / REST entry points —
unlike a bare class with no keyword.

### Bare class (no keyword) behavior — version-gated

The bare-class default inverted in Summer '26. The gate is the
**`apiVersion` in the class's own `.cls-meta.xml`**, not the org's
release — a Summer '26 org runs a class pinned to 58.0 with the old
behavior.

- **API 67.0+** — a class with no keyword runs `with sharing`,
  regardless of who called it. The rule reaches across a call chain: once
  any class in the chain is saved at 67.0+, the chain from there runs
  `with sharing` — a bare 67.0 callee is not pulled down to `without
  sharing` by a `without sharing` caller.
- **API ≤ 66.0** — a bare class is **not** equivalent to `with sharing`;
  it ran effectively as `without sharing`, except when called from a
  Lightning context (`@AuraEnabled`, `@RemoteAction`), which has run it
  `with sharing` since API v34.

**Never ship a bare class at either version** — pick one of the three
keywords explicitly so reviewers can audit intent, and so an `apiVersion`
bump cannot silently flip a class that needs elevation into enforcing
sharing. Canonical version table:
[`agents/_shared/AGENT_CONTRACT.md`](../../../agents/_shared/AGENT_CONTRACT.md)
§ *Apex security idiom by API version*.

### Interaction with `WITH USER_MODE` and `WITH SYSTEM_MODE`

The two clauses are not mirror images.

- **User mode tightens everything.** `WITH USER_MODE` on a SOQL query
  (and `Database.queryWithBinds(..., AccessLevel.USER_MODE)`, plus DML
  overloads with `AccessLevel.USER_MODE`) enforces **sharing rules and
  FLS/CRUD** for that statement whatever the class keyword: "the
  operation always respects the user's sharing rules" (Apex Developer
  Guide L11959). A `without sharing` job can therefore run one
  user-scoped lookup without changing the rest of its behavior.
- **System mode loosens only FLS and object permissions.** For
  `WITH SYSTEM_MODE` / `AccessLevel.SYSTEM_MODE`, "the sharing keyword
  on the calling class determines whether the operation respects the
  user's record-level permissions" (Developer Guide L11960-11961);
  `AccessLevel.SYSTEM_MODE` is the mode where "object and field-level
  permissions of the current user are ignored, and the record sharing
  rules are controlled by the class sharing keywords" (Apex Reference
  Guide L199118-199119). Inside a `with sharing` class, a
  `WITH SYSTEM_MODE` query still returns only the rows the user can see.

So a per-statement clause can tighten sharing but cannot lift it. To
read rows outside the user's perimeter from a `with sharing` class, move
that one query into a small `without sharing` helper — an inner class
works, because "inner classes don't adopt the sharing mode of the
container class" (Developer Guide L4931) — and, at API 67.0+, give the
query `WITH SYSTEM_MODE` too, since without it the query runs in user
mode and enforces sharing anyway. Code: `references/examples.md`
Example 4.

### Always justify `without sharing`

Repo convention: any `without sharing` class must be preceded by a
`// reason:` comment explaining what user-invisible data is being
accessed and why the elevation is required. The checker enforces this.

---

## Common Patterns

### Pattern: AuraEnabled controller

**When to use:** any `@AuraEnabled` Apex class invoked from LWC / Aura.

**How it works:** declare `with sharing`. Let the user's record
visibility govern. If a single operation legitimately needs elevation
(e.g., loading a configuration record outside the user's perimeter),
factor that one query into a small `without sharing` helper (inner or
separate class) with a `// reason:` comment, and at API 67.0+ give the
query `WITH SYSTEM_MODE`. `WITH SYSTEM_MODE` on its own, left in the
`with sharing` controller, lifts FLS and object checks but not sharing.

**Why not the alternative:** `without sharing` on an `@AuraEnabled` class
is a frequent insecure-direct-object-reference vector — the LWC may pass
arbitrary IDs and the controller will return them all.

### Pattern: Domain / service / selector layer

**When to use:** classes called from other Apex, never directly by a
user-facing entry point.

**How it works:** declare `inherited sharing` so the entry point's
choice flows through. Document the assumption at the top of the class:
"caller-governed; ensure entry point declares with sharing for
user-scoped operations."

**Why not the alternative:** a bare class is ambiguous; an explicit
`with sharing` overrides legitimate batch / system contexts that need
elevation.

### Pattern: Batchable / Schedulable / Queueable system jobs

**When to use:** asynchronous jobs that operate across all records
regardless of user perimeter (data scrubs, aggregation, retention sweeps).

**How it works:** `without sharing` with a `// reason:` comment
explaining why system context is required. At API 67.0+ the keyword is
not enough on its own: a query with no mode clause runs in user mode and
enforces sharing, so the cross-perimeter queries also need
`WITH SYSTEM_MODE` (or `AccessLevel.SYSTEM_MODE`). Add a unit test that
asserts the job processes records the running user cannot see.

**Why not the alternative:** `with sharing` on a batch run by an
integration user can silently miss records and cause incomplete jobs.

---

## Decision Guidance

| Scenario | Keyword | Reason |
|---|---|---|
| `@AuraEnabled` controller for LWC | `with sharing` | User invoked it; respect their visibility |
| `@RestResource` exposed to a community / partner | `with sharing` | External caller authenticates as a user |
| Reusable selector / service / domain class | `inherited sharing` | Caller chooses; you remain neutral |
| Batch / Schedulable system job | `without sharing` + `// reason:` (+ `WITH SYSTEM_MODE` on its queries at API 67.0+) | Cross-perimeter aggregation; at 67.0+ an unqualified query runs in user mode and enforces sharing |
| Trigger handler | `without sharing` (typical) | A trigger always carries an implicit `without sharing` context, but its own SOQL and DML are version-split: user mode (running user's sharing, FLS, object permissions applied) at API 67.0+, system mode before 67.0. The handler's keyword governs only the handler's own queries |
| Site / guest user controller | `with sharing` (mandatory for guest) | Guest perimeter must not be elevated |
| Managed-package internal class | `without sharing` (Salesforce-enforced) | Subscriber's keyword cannot override package |
| One-off elevated read inside a `with sharing` class | keep the class `with sharing`; move that one query into a small `without sharing` helper (inner or separate class) with a `// reason:` comment, and give the query `WITH SYSTEM_MODE` at API 67.0+ | Minimum-blast-radius elevation. `WITH SYSTEM_MODE` left in the `with sharing` class lifts only FLS/CRUD — record sharing follows the class keyword (Developer Guide L11960-11961; Reference Guide L199118-199119) |
| One query in a `with sharing` class must read a field the user lacks FLS on, rows already visible | keep class `with sharing`, `WITH SYSTEM_MODE` on that query + `// reason:` | System mode lifts FLS/CRUD only, which is exactly the need |

---

## Recommended Workflow

When this skill activates, the agent runs these steps in order:

1. **Identify entry-point category** for every class in scope (controller, REST, batch, trigger handler, service, selector, utility, guest-user controller).
2. **Match category to the Decision Guidance table** above and propose the default keyword for each class.
3. **Trace inherited-sharing risk** — for any class without an explicit keyword, list every caller and confirm none of them are `without sharing` in a way that would silently elevate this code.
4. **Justify every `without sharing`** with a single-line `// reason:` comment immediately above the class declaration; reject the change if the reason is generic ("performance", "convenience").
5. **Plan per-query overrides** — if 90%+ of the class is one mode but one query needs the other, do not flip the class keyword. To tighten one query in a `without sharing` class, use `WITH USER_MODE`. To lift FLS/CRUD only, use `WITH SYSTEM_MODE`. To see rows outside the user's perimeter from a `with sharing` class, extract that query into a `without sharing` helper (plus `WITH SYSTEM_MODE` at 67.0+) — a mode clause cannot lift sharing.
6. **Run** `python3 skills/apex/apex-with-without-sharing-decision/scripts/check_apex_with_without_sharing_decision.py --manifest-dir <path>` to flag missing keywords on `@AuraEnabled` classes and unjustified `without sharing`.
7. **Add a Review Checklist citation** to the PR confirming the keyword choice was deliberate and the `// reason:` comment exists where required.

---

## Review Checklist

- [ ] Every class in scope has an explicit sharing keyword (no bare classes) — at API 67.0+ the bare default is `with sharing`, which is safe but hides intent and flips on an `apiVersion` change
- [ ] All `@AuraEnabled` and `@RestResource` classes are `with sharing`
- [ ] Every `without sharing` class has a `// reason:` comment above it
- [ ] Reusable service / selector classes use `inherited sharing`
- [ ] No `with sharing` class silently calls a `without sharing` helper that exposes user-invisible data back to the UI
- [ ] Per-query `WITH USER_MODE` / `WITH SYSTEM_MODE` used where the class default is wrong for one statement — and no `WITH SYSTEM_MODE` in a `with sharing` class is relied on to return rows the user cannot see (the checker WARNs on it)
- [ ] Trigger handlers explicitly declare `without sharing` (or `with sharing` if user-mode behavior is intended) — never bare
- [ ] Test class exists that proves the chosen keyword by running as a low-privilege user

---

## Salesforce-Specific Gotchas

1. **Sharing is inherited through method calls.** A `with sharing`
   controller that calls a `without sharing` helper runs that helper's
   own queries with the running user's sharing rules ignored — the
   explicit keyword wins over the caller at every API version. Reviewers
   must trace the call tree, not just the entry point.
2. **Managed-package classes always run `without sharing` regardless of
   subscriber.** When a subscriber org calls a managed-package
   `@AuraEnabled` class, the package's declared keyword is enforced; the
   subscriber cannot tighten it.
3. **A trigger's own queries and DML are version-split.** A `.trigger`
   file cannot carry a sharing keyword and always runs in an implicit
   `without sharing` context. At trigger API **67.0 and later**, SOQL,
   SOSL, DML and `Database` methods in the trigger body run in **user
   mode** unless system mode is stated; user mode overrides the implicit
   `without sharing`, so the running user's sharing, FLS and object
   permissions all apply. Before 67.0 they run in **system mode**. State
   the mode on every operation in a trigger (`WITH SYSTEM_MODE` only
   where the trigger genuinely needs all records) and delegate to a
   handler class that declares an explicit keyword.
   Source: Apex Developer Guide v67.0, *Using the with sharing, without
   sharing, and inherited sharing Keywords* (Implementation in Apex
   Triggers) — recorded in `skills/apex/soql-security/references/gotchas.md`
   Gotcha 6.
4. **Aggregate queries (`SUM`, `COUNT`, `AVG`) respect class sharing.**
   A `with sharing` class running `SELECT COUNT() FROM Opportunity` only
   counts opportunities the user can see — surprising for dashboards.
5. **`WITH USER_MODE` enforces FLS/CRUD too**, not just sharing. Adding
   it to a query inside a `without sharing` class can suddenly start
   throwing `QueryException` if the user lacks field-level read on a
   selected field.
6. **System mode is not `without sharing`.** `WITH SYSTEM_MODE` in a
   `with sharing` class drops FLS and object checks but keeps the row
   filter, so a "security fix" that adds it to reach hidden records
   changes nothing about which records come back. Details and the fix:
   `references/gotchas.md` Gotcha 7.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Keyword recommendation per class | Explicit `with` / `without` / `inherited sharing` choice with rationale |
| `// reason:` comment text | One-line justification for every `without sharing` class |
| Per-query override list | Statements that need `WITH USER_MODE` (tighten) or `WITH SYSTEM_MODE` (FLS/CRUD only), plus any query moved into a `without sharing` helper for row elevation |
| Test class scaffold | Runs the code as a minimum-permission user to prove keyword behavior |

---

## Related Skills

- `apex/apex-stripinaccessible-and-fls-enforcement` — sharing is record-level; FLS/CRUD is field/object-level. Both must be considered.
- `apex/apex-security-patterns` — controller-specific security review including sharing keyword and the version-gated access mode
- `apex/soql-security` — per-query `WITH USER_MODE` / `WITH SYSTEM_MODE` usage on SOQL
- `standards/decision-trees/sharing-selection.md` — org-level sharing mechanisms (OWD, role hierarchy, sharing rules) — read this when the question is broader than "what keyword goes on this class"
