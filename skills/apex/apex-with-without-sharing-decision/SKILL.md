---
name: apex-with-without-sharing-decision
description: "Choosing the correct sharing keyword on an Apex class: with sharing vs without sharing vs inherited sharing, how the choice flows through called methods, and when WITH USER_MODE overrides class-level behavior. NOT for org-level sharing design (use standards/decision-trees/sharing-selection.md). NOT for FLS / CRUD enforcement (use apex-fls-crud-enforcement). NOT for Apex Managed Sharing (use apex-managed-sharing)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
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
  remember that `with`/`without sharing` is **inherited from the calling
  class** — your keyword may be irrelevant if a `without sharing` caller
  invokes you, unless you explicitly declare `with sharing`.
- **Annotations on the class.** `@AuraEnabled`, `@RemoteAction`, and
  `@RestResource` classes are user-facing entry points and **must default
  to `with sharing`** unless you have a documented elevation reason.

---

## Core Concepts

### The three keyword choices

- **`with sharing`** — the runtime enforces the running user's sharing
  rules on every SOQL query made directly inside this class. Records the
  user cannot see are filtered out of query results. Field-Level Security
  and CRUD are **not** automatically enforced — that is a separate concern
  (`Security.stripInaccessible`, `WITH SECURITY_ENFORCED`, or
  `WITH USER_MODE`).
- **`without sharing`** — sharing rules are **ignored** for queries in
  this class. The class runs in system context for record visibility.
  Use deliberately, never as a default.
- **`inherited sharing`** — the class adopts the sharing mode of the
  **caller**. If the entry point is `with sharing`, this class behaves
  the same way. If the entry point has no keyword, an `inherited sharing`
  class **defaults to `with sharing`** when called directly from
  Lightning, REST, or Aura entry points (this is the safe default for
  reusable utilities).

### Sharing is inherited through method calls

The sharing mode of the **outermost** class on the call stack governs the
queries inside any callees that did not declare a keyword themselves. A
class that explicitly declares `with sharing` keeps its own mode no
matter who calls it. The corollary: if you author a `with sharing`
controller that calls into a service class with no keyword, the service
runs `with sharing` — but if a different `without sharing` controller
calls the same service, the service runs `without sharing`. Always
declare an explicit keyword on shared service / selector layers.

### Where `inherited sharing` fits

Reusable utilities, selectors, and base service classes that should
respect whatever the entry point demanded. `inherited sharing` is the
explicit way to say "I do not want to override the caller's choice, but I
also do not want to be ambiguous about it." It also produces a safe
default (with sharing) when called from Lightning / REST entry points —
unlike a bare class with no keyword.

### Bare class (no keyword) behavior

A class with no sharing keyword is **not equivalent to `with sharing`**.
Historically it ran effectively as `without sharing`. Since API v34, when
called from a Lightning context (`@AuraEnabled`, `@RemoteAction`) it runs
as `with sharing`, but in many other contexts (called from a `without
sharing` class, anonymous Apex, some legacy entry points) it still runs
as `without sharing`. **Never ship a bare class** — always pick one of
the three keywords explicitly so reviewers can audit intent.

### Interaction with `WITH USER_MODE`

`WITH USER_MODE` on a SOQL query (and `Database.queryWithBinds(...,
AccessLevel.USER_MODE)`, plus DML overloads with `AccessLevel.USER_MODE`)
enforces **both sharing rules and FLS/CRUD** for that single statement,
regardless of the class-level keyword. This means a `without sharing`
class can run a single query in user mode without changing the rest of
its behavior — useful when 95% of a system-context job needs one
user-scoped lookup. Conversely, `WITH SYSTEM_MODE` on a query inside a
`with sharing` class elevates only that statement. Class keyword sets the
default; `WITH USER_MODE` / `WITH SYSTEM_MODE` is the per-statement
override.

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
factor it into a separate `without sharing` helper with a `// reason:`
comment, or use `WITH SYSTEM_MODE` on that one query.

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
explaining why system context is required. Add a unit test that asserts
the job processes records the running user cannot see.

**Why not the alternative:** `with sharing` on a batch run by an
integration user can silently miss records and cause incomplete jobs.

---

## Decision Guidance

| Scenario | Keyword | Reason |
|---|---|---|
| `@AuraEnabled` controller for LWC | `with sharing` | User invoked it; respect their visibility |
| `@RestResource` exposed to a community / partner | `with sharing` | External caller authenticates as a user |
| Reusable selector / service / domain class | `inherited sharing` | Caller chooses; you remain neutral |
| Batch / Schedulable system job | `without sharing` + `// reason:` | Cross-perimeter aggregation |
| Trigger handler | `without sharing` (typical) | Triggers run in system context already; explicit keyword removes ambiguity |
| Site / guest user controller | `with sharing` (mandatory for guest) | Guest perimeter must not be elevated |
| Managed-package internal class | `without sharing` (Salesforce-enforced) | Subscriber's keyword cannot override package |
| One-off elevated query inside a `with sharing` class | keep class `with sharing`, use `WITH SYSTEM_MODE` per-query | Minimum-blast-radius elevation |

---

## Recommended Workflow

When this skill activates, the agent runs these steps in order:

1. **Identify entry-point category** for every class in scope (controller, REST, batch, trigger handler, service, selector, utility, guest-user controller).
2. **Match category to the Decision Guidance table** above and propose the default keyword for each class.
3. **Trace inherited-sharing risk** — for any class without an explicit keyword, list every caller and confirm none of them are `without sharing` in a way that would silently elevate this code.
4. **Justify every `without sharing`** with a single-line `// reason:` comment immediately above the class declaration; reject the change if the reason is generic ("performance", "convenience").
5. **Plan per-query overrides** — if 90%+ of the class is one mode but one query needs the other, do not flip the class keyword; use `WITH USER_MODE` / `WITH SYSTEM_MODE` on that statement.
6. **Run** `python3 skills/apex/apex-with-without-sharing-decision/scripts/check_apex_with_without_sharing_decision.py --manifest-dir <path>` to flag missing keywords on `@AuraEnabled` classes and unjustified `without sharing`.
7. **Add a Review Checklist citation** to the PR confirming the keyword choice was deliberate and the `// reason:` comment exists where required.

---

## Review Checklist

- [ ] Every class in scope has an explicit sharing keyword (no bare classes)
- [ ] All `@AuraEnabled` and `@RestResource` classes are `with sharing`
- [ ] Every `without sharing` class has a `// reason:` comment above it
- [ ] Reusable service / selector classes use `inherited sharing`
- [ ] No `with sharing` class silently calls a `without sharing` helper that exposes user-invisible data back to the UI
- [ ] Per-query `WITH USER_MODE` / `WITH SYSTEM_MODE` used where the class default is wrong for one statement
- [ ] Trigger handlers explicitly declare `without sharing` (or `with sharing` if user-mode behavior is intended) — never bare
- [ ] Test class exists that proves the chosen keyword by running as a low-privilege user

---

## Salesforce-Specific Gotchas

1. **Sharing is inherited through method calls.** A `with sharing`
   controller that calls a `without sharing` helper executes that helper
   in system context — the helper's keyword wins for queries it makes
   itself. Reviewers must trace the call tree, not just the entry point.
2. **Managed-package classes always run `without sharing` regardless of
   subscriber.** When a subscriber org calls a managed-package
   `@AuraEnabled` class, the package's declared keyword is enforced; the
   subscriber cannot tighten it.
3. **Triggers run in system context** by default. The trigger body itself
   is system; the trigger handler class keyword determines what queries
   inside it do. Always declare an explicit keyword on the handler.
4. **Aggregate queries (`SUM`, `COUNT`, `AVG`) respect class sharing.**
   A `with sharing` class running `SELECT COUNT() FROM Opportunity` only
   counts opportunities the user can see — surprising for dashboards.
5. **`WITH USER_MODE` enforces FLS/CRUD too**, not just sharing. Adding
   it to a query inside a `without sharing` class can suddenly start
   throwing `QueryException` if the user lacks field-level read on a
   selected field.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Keyword recommendation per class | Explicit `with` / `without` / `inherited sharing` choice with rationale |
| `// reason:` comment text | One-line justification for every `without sharing` class |
| Per-query override list | Statements that need `WITH USER_MODE` / `WITH SYSTEM_MODE` |
| Test class scaffold | Runs the code as a minimum-permission user to prove keyword behavior |

---

## Related Skills

- `apex/apex-fls-crud-enforcement` — sharing is record-level; FLS/CRUD is field/object-level. Both must be considered.
- `apex/apex-aura-enabled-security` — controller-specific security review including sharing keyword
- `standards/decision-trees/sharing-selection.md` — org-level sharing mechanisms (OWD, role hierarchy, sharing rules) — read this when the question is broader than "what keyword goes on this class"
