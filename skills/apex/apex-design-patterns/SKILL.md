---
name: apex-design-patterns
description: "Use when structuring Apex into service, selector, domain, factory, and dependency-injection layers for maintainability and testability. Triggers: 'service layer', 'selector pattern', 'domain layer', 'dependency injection', 'fat trigger/controller', 'unit of work', 'strategy pattern in Apex', 'Type.forName factory', 'static cache singleton', 'savepoint rollback in a service'. NOT for the fflib library — use apex/fflib-enterprise-patterns. NOT for splitting one class — use apex/apex-class-decomposition-pattern."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
tags:
  - service-layer
  - selector-pattern
  - domain-layer
  - dependency-injection
  - factory-pattern
  - unit-of-work
  - strategy-pattern
triggers:
  - "how should I structure Apex service classes"
  - "selector layer versus querying in service"
  - "domain layer pattern in Salesforce"
  - "dependency injection for Apex tests"
  - "fat trigger or controller needs refactor"
  - "split a fat trigger into handler service selector domain"
  - "make an Apex rule swappable with custom metadata"
  - "instantiate an Apex class by name with Type.forName"
  - "roll back everything a service did when one step fails"
  - "static cache keeps stale values in my trigger"
  - "abstract method requires at least one of global public protected"
  - "which sharing keyword goes on a service versus a selector"
inputs:
  - "current entry points such as trigger, controller, invocable, or REST"
  - "team size and expected codebase growth"
  - "testing pain points and dependency boundaries"
  - "the sObject and the business rules that must survive a 200-record save"
  - "which behaviours must be swappable per business unit, record type, or org"
outputs:
  - "Apex layering recommendation"
  - "review findings for coupling and responsibility issues"
  - "refactor pattern for service, selector, domain, or factory layers"
  - "a deployable handler / domain / service / selector / strategy set plus its bulk test class"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-09-16
---

Use this skill when Apex code needs structure that will survive more than one sprint. The goal is not to import a framework blindly. It is to separate orchestration, querying, business rules, and replaceable dependencies so triggers, controllers, and invocables stay thin and tests can isolate behavior.

The repo already owns the base classes. Do not re-implement them — extend them:
`templates/apex/TriggerHandler.cls`, `templates/apex/TriggerControl.cls`,
`templates/apex/BaseDomain.cls`, `templates/apex/BaseService.cls`,
`templates/apex/BaseSelector.cls`, `templates/apex/ApplicationLogger.cls`,
`templates/apex/SecurityUtils.cls`, `templates/apex/tests/TestDataFactory.cls`.
`references/code-examples.md` shows a concrete Case stack built on exactly those files.

## Before Starting

- What are the main entry points today: triggers, Aura/LWC controllers, invocables, REST resources, or schedulers?
- Which dependencies are hardest to test: SOQL, callouts, or global utility classes?
- Is the current pain duplicated business rules, query sprawl, or giant god-classes?

## Questions to Ask Before Configuring

Ask these before writing a class. Each one maps to a gotcha in `references/gotchas.md`; an agent that skips them produces a layer diagram that compiles and a transaction that misbehaves under Bulk API or a second save.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the largest batch this code will ever see — a UI save, a 200-row trigger chunk, or a Bulk API job?" | Static guards and static caches are reset across transactions but **not** across the trigger invocations of one Bulk API request (Apex Developer Guide L3789–3791) | The recursion-guard design, and whether the guard may be a `Boolean` at all |
| "Does any step of this workflow have to be undone if a later step fails?" | Only a service may open a savepoint, and each savepoint costs one of the 150 DML statements (L8691, L19554) | Whether you need `BaseService.beginTransaction()` at all, and where the try/catch boundary sits |
| "Which behaviours must differ per business unit, record type, or installed org?" | That is the strategy seam — a Custom Metadata row naming an Apex class, resolved with `Type.forName` (Apex Reference Guide L242008–242049) | The CMDT type, its rows, and the interface every implementation must satisfy |
| "Which of these classes is an entry point, and which is called by one?" | `inherited sharing` runs as `without sharing` only when called from an established `without sharing` context; at every entry point it runs `with sharing` (L4851–4860) | The sharing keyword per layer, written down rather than defaulted |
| "What API version will these classes be saved at?" | At 65.0+ an `abstract`/`override` method without an explicit access modifier fails to compile (L3359–3364); at 67.0+ an undeclared class runs `with sharing` and Apex runs in user context (L4961, L11744–11746) | The `apiVersion` in every `.cls-meta.xml`, chosen deliberately |
| "Who owns the field list this query returns, and does the caller need every field?" | One `selectEverything` method becomes the slowest query in the org and the hardest to security-review | Intent-named selector methods instead of one broad one |
| "Is this abstraction paying for itself today, or is it speculative?" | Apex has no DI container; every seam is hand-wired and hand-maintained | An explicit stop line — which collaborators get an interface and which stay concrete |

What a proper configuration adds over just writing the classes: the trigger is re-entrant-safe under Bulk API chunking, a failed step rolls the whole unit of work back instead of leaving half a transaction committed, per-org behaviour changes by deploying a Custom Metadata row rather than an Apex class, and every layer's sharing and access-modifier decision is written in the source rather than inherited by accident.

## Core Concepts

### Service Layer Owns Orchestration

Service classes coordinate work. They should decide sequence, call selectors, invoke domain logic, and manage transaction boundaries. They should not absorb every query, validation rule, and integration detail forever. When a service becomes the only place logic can live, it turns into a god-class quickly.

`templates/apex/BaseService.cls` fixes the contract: `beginTransaction()` / `rollbackTransaction(sp)` / `logAndRethrow(source, e)`. The service is the only layer allowed to call them.

### Selector Layer Centralizes Query Intent

Selectors are for query shape, field lists, and reusable retrieval patterns. They make security review, field list reuse, and query tuning easier because data access is not scattered across controllers, triggers, and utility methods. A selector is not just "any class with SOQL"; it should have a stable retrieval responsibility.

`templates/apex/BaseSelector.cls` is `abstract inherited sharing` and hands subclasses `userMode()` / `systemMode()`, so `AccessLevel.USER_MODE` is the default and a system-mode query is a visible, reviewable exception.

### Domain Layer Holds Object-Specific Rules

Domain logic is where object behavior and cross-field rules belong. If every trigger, flow-invocable method, and controller re-implements the same Account or Opportunity rules differently, domain logic is missing.

`templates/apex/BaseDomain.cls` carries the collection plus `oldMap`, and gives you `isChanged(record, field)` and `recordIds()`. Its contract is explicit: domains never issue SOQL, DML, or callouts.

### Unit Of Work Is A Savepoint With A Boundary

Apex has no separate transaction object. The unit of work is the Apex transaction itself, narrowed by `Database.setSavepoint()` and `Database.rollback(sp)`. Two platform facts shape the pattern:

- each savepoint you set counts against the DML **statement** limit of 150, and `Database.rollback` counts too (Apex Developer Guide L8691, L19554)
- static variables are **not** reverted by a rollback (L8692–8693), so a recursion guard or a cached value set before the failure survives it

So a savepoint belongs at one service method boundary, not around every DML.

### Singleton Means "Static, For One Transaction"

A static variable is static only within the scope of one Apex transaction and is reset across transaction boundaries (L3736–3738). That makes a static `Map` a perfect per-transaction cache and a poor cross-request cache. Two consequences the catalogue depends on:

- an Apex DML request that fires a trigger several times shares those statics across the invocations (L3738–3740) — which is what makes a recursion guard work
- each `execute()` of a Batch Apex job is a discrete transaction (L17099), so the singleton is rebuilt per chunk

### Strategy And Factory Are One Pattern On This Platform

`Type.forName(name)` returns the `System.Type` of a **public or global** class — never a private one (Apex Reference Guide L241920–241922) — and `newInstance()` creates an instance you cast to the interface (L242298–242327). Pair it with a Custom Metadata Type row holding the class name and you get behaviour that varies per org without an Apex deployment. Custom metadata records carry no SOQL-query limit inside a transaction (Apex Developer Guide L19614–19615), so the lookup is effectively free.

### Dependency Injection Creates Testable Boundaries

Apex has limited native DI ergonomics compared with other languages, but interfaces plus factories still help. The purpose is not abstraction for its own sake. It is to replace integrations, notification clients, or expensive collaborators in tests without branching on `Test.isRunningTest()`.

## Common Patterns

### Thin Entry Point To Service

**When to use:** Triggers, controllers, invocables, or REST resources are accumulating business logic.

**How it works:** Keep the entry point as an adapter only, then delegate to a service with explicit inputs. For triggers the adapter is one line — `new CaseTriggerHandler().run();` — because `templates/apex/TriggerHandler.cls` already owns dispatch, the depth counter, `skipOnce()`, and the `TriggerControl` kill switch.

**Why not the alternative:** Entry-point logic is hard to reuse and harder to review across many contexts.

### Service + Selector Pair

**When to use:** A business workflow reads complex record sets repeatedly.

**How it works:** Put orchestration in the service and field/query definitions in a selector.

### Interface + Factory For External Dependencies

**When to use:** A service depends on a notifier, API client, or expensive collaborator.

**How it works:** Define an interface, provide a production implementation, and use a factory or constructor injection for tests.

### Custom Metadata-Driven Strategy

**When to use:** The same step must behave differently per business unit, record type, or subscriber org, and you do not want a `switch` that grows a branch per customer.

**How it works:** One interface, one implementation class per variant, one `..._Strategy__mdt` row per variant naming the class. The factory reads the row, calls `Type.forName`, casts to the interface, and memoises the instance in a static map for the transaction. Worked end to end in `references/code-examples.md` § 5–6.

**Why not the alternative:** A hardcoded `if/else` ships an Apex deployment for every new variant; the CMDT row ships as data.

### Unit Of Work At The Service Boundary

**When to use:** One service method writes to more than one object and a partial write would be wrong.

**How it works:** `Savepoint sp = beginTransaction();` at the top of the public method, all DML inside the `try`, `rollbackTransaction(sp)` plus `logAndRethrow` in the `catch`. One savepoint per public method, never one per DML.

**Why not the alternative:** `Database.insert(records, false)` gives you partial success, which is a different requirement — use it when partial writes are acceptable, not as a substitute for rollback.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Trigger or controller contains queries, branching, and DML directly | Thin adapter + service layer | Cleaner review and reuse boundary |
| Same query field list appears in several classes | Selector layer | One place to tune and secure data access |
| Object-specific business rules repeat across entry points | Domain layer | Keeps behavior tied to the object's business rules |
| Tests rely on `Test.isRunningTest()` to skip dependencies | Interface + injected dependency | Better isolation without production branching |
| One method writes several objects and a partial write is unacceptable | Savepoint at the service method boundary | Rollback is a service responsibility; the DML statement cost is paid once |
| Some but not all rows may fail and that is acceptable | `Database.insert(rows, false)` and inspect `Database.SaveResult` | Partial success is not the same requirement as rollback |
| Behaviour must vary per business unit or subscriber org | Interface + CMDT row + `Type.forName` factory | New variants ship as data, not as an Apex deployment |
| The same value is recomputed many times in one save | Static map memoised in the class | Statics live exactly one transaction (L3736–3738) |
| The "cache" must survive past the transaction | Platform Cache or a Custom Setting, not a static | A static is reset at every transaction boundary |

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Answer the seven questions above first.** The batch-size answer decides the recursion guard, the rollback answer decides whether a savepoint exists at all, and the variability answer decides whether a strategy interface is justified. Write the answers into `templates/apex-design-patterns-template.md` before any class exists.
2. **Place every existing method into exactly one layer.** Use the Decision Guidance table. Anything that lands in two layers is the refactor; anything that lands in none is usually a utility that should be inlined or deleted.
3. **Extend the canonical bases, never fork them.** `TriggerHandler` for dispatch, `BaseDomain` for per-record rules, `BaseSelector` for every SOQL statement, `BaseService` for orchestration and the savepoint, `SecurityUtils` before DML on user-supplied rows. Copy the concrete shapes from `references/code-examples.md` § 1–4 rather than inventing new ones. Give every `override` an explicit `protected`/`public` modifier — API 65.0+ rejects it otherwise.
4. **Add the strategy seam only where question 3 said behaviour varies.** Build it as `references/code-examples.md` § 5–6 does: interface, `..._Strategy__mdt` row, `Type.forName` + `newInstance()` cast to the interface, memoised in a static map, with a named fallback when the row is missing or the class no longer exists.
5. **Write the test class against the three paths that break in production** — 200 records through the trigger, each strategy resolved from its CMDT row, and the rollback path proving the savepoint undid every object the service touched. Build fixtures with `templates/apex/tests/TestDataFactory.cls` and the 200-row shape in `templates/apex/tests/BulkTestPattern.cls`.
6. **Run this skill's checker over the source tree, then the tests:**
   `python3 skills/apex/apex-design-patterns/scripts/check_apex_design_patterns.py --manifest-dir force-app/main/default`
   then `sf apex run test --tests CaseEscalationServiceTest --result-format human --code-coverage --synchronous`.
7. **Record what you did not abstract and why.** The template has a row for it. An unwritten "we deliberately left `CaseSelector` concrete" is re-litigated in every later review.

---

## Review Checklist

- [ ] Entry points are adapters, not business-logic containers.
- [ ] Query logic is centralized where reuse or tuning matters.
- [ ] Object-specific rules are not duplicated across multiple services or triggers.
- [ ] Services do not absorb unrelated responsibilities forever.
- [ ] Test seams use interfaces/factories instead of `Test.isRunningTest()` hacks.
- [ ] Pattern usage is proportionate to the codebase size; abstraction is justified.
- [ ] Every class declares a sharing keyword explicitly, including inner classes.
- [ ] Every `abstract` and `override` method carries `protected`, `public`, or `global`.
- [ ] Exactly one savepoint per service method, and the `catch` rolls back before it logs.
- [ ] Every static mutable collection has a `@TestVisible` reset hook.
- [ ] Every class named by a `Type.forName` call is public (not inner, not private) and has a no-argument constructor.
- [ ] The test class covers 200 records, every strategy row, and the rollback path.

## Salesforce-Specific Gotchas

1. **A "service layer" can become a dumping ground fast** — if every concern lands there, the pattern has failed.
2. **Selector patterns still need secure query behavior** — sharing declarations do not enforce object- or field-level security at all (Apex Developer Guide L4926).
3. **Static helpers are not dependency injection** — they are harder to stub and usually push teams toward test-only branching.
4. **Patterns are not free** — for a tiny one-off class, excessive layering can be ceremony without payoff.
5. **A rollback does not undo your statics** — the recursion guard you set before the failure is still set (L8692–8693).
6. **Bulk API chunking resets governor limits but not statics** — a `Boolean hasRun` guard silently skips chunks 2..n of the same request (L3789–3791).
7. **`Type.forName` returns `null` for an inner or private class** — the failure surfaces as a null dereference at `newInstance()`, not as a compile error (Apex Reference Guide L241920–241922).

Full **What happens / When it occurs / How to avoid** treatment for these and five more is in `references/gotchas.md`.

## Output Artifacts

| Artifact | Description |
|---|---|
| Layering review | Findings on where orchestration, queries, and business rules are misplaced |
| Refactor map | Recommendation for service, selector, domain, factory, and interface boundaries |
| Pattern scaffold | Minimal Apex structure showing how to separate responsibilities cleanly |
| Deployable stack | Trigger + handler + domain + service + selector + strategy factory + CMDT + bulk test, with `-meta.xml` and `package.xml` |

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are about to write the classes — the full Case stack on the canonical bases, the CMDT strategy factory, the 200-record + rollback test, `-meta.xml`, `package.xml`, and the `sf` commands |
| `references/gotchas.md` | A layered design compiles but misbehaves — statics, savepoints, sharing modes, `Type.forName`, CMDT truncation, access modifiers |
| `references/examples.md` | You want the shorter before/after refactor narratives and the layer-ownership matrix |
| `references/llm-anti-patterns.md` | You are reviewing generated Apex and want the eight failure shapes with detection hints |
| `references/well-architected.md` | You are tagging findings by pillar or need the sourced claim behind a statement |

## Related Skills

- `apex/trigger-framework` — use when the immediate problem starts at the trigger boundary and needs handler structure first.
- `apex/test-class-standards` — use when better layering is mainly valuable because tests are currently brittle.
- `apex/apex-security-patterns` — use when selectors and services need explicit security posture, not just better structure.
- `apex/apex-mocking-and-stubs` — use when the interface seam exists and the question is how to double it in a test.
- `apex/fflib-enterprise-patterns` — use when the team has decided to adopt the fflib library rather than hand-roll these layers.
- `apex/apex-class-decomposition-pattern` — use when the unit of work is splitting one oversized class, not designing a layer stack.
- `apex/recursive-trigger-prevention` — use when the specific failure is re-entry, not layering.
- `apex/apex-cpu-and-heap-optimization` — use when the layered design is correct but the transaction is hitting CPU or heap.
