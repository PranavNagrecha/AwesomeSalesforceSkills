---
name: apex-class-decomposition-pattern
description: "When and how to split an Apex class into Domain / Service / Selector layers using this repo's lightweight base classes (BaseDomain, BaseService, BaseSelector). Covers splitting signals, ordering of extraction, and naming conventions. NOT for full fflib migration — see fflib-enterprise-patterns. NOT for trigger framework choice — see trigger-framework."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Scalability
tags:
  - apex
  - decomposition
  - domain
  - service
  - selector
  - architecture
  - refactoring
triggers:
  - "when to split apex class into service and selector"
  - "monolithic apex class refactor into domain service selector"
  - "trigger handler with embedded soql needs splitting"
  - "service class grew its own soql queries"
  - "how to apply enterprise patterns lightweight without fflib"
inputs:
  - Existing Apex class or trigger handler under review
  - SObject(s) the class operates on
  - Approximate line count and responsibility mix
  - Whether SOQL, DML, callouts, and per-record validation coexist
outputs:
  - Per-role split plan (Domain / Service / Selector)
  - New class names following the `<X>Domain`, `<X>Service`, `<X>Selector` convention
  - Extraction ordering (Selector first, then Service, then Domain)
  - Pointers to the matching base class under `templates/apex/`
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Apex Class Decomposition Pattern

Activate this skill when an Apex class has grown past the point where one class can comfortably hold all its responsibilities, when a trigger handler embeds SOQL, or when a service class has started issuing its own queries. The goal is the lightweight enterprise pattern this repo standardises on: a clear split into **Trigger handler → Domain → Service → Selector**, anchored by the canonical base classes in `templates/apex/`.

This is NOT a full fflib migration (no Application factory, Unit of Work, or interface registries) — see `apex/fflib-enterprise-patterns` for that. It is also NOT a trigger framework selection skill — see `apex/trigger-framework` for choosing between TriggerHandler styles.

## The four roles

| Role | Responsibility | Must NOT do |
|---|---|---|
| Trigger handler | Event dispatch — route `before insert` / `after update` / etc. to a Domain or Service method | Hold business logic, run SOQL, do DML |
| Domain (`<X>Domain extends BaseDomain`) | Per-record validation and field derivation against a homogeneous `Trigger.new` collection | SOQL, DML, callouts |
| Service (`<X>Service extends BaseService`) | Orchestration, transactions (savepoints), DML, platform events, callouts | Issue SOQL directly (always go through a Selector) |
| Selector (`<X>Selector extends BaseSelector`) | All SOQL for a given SObject, named by intent (`selectActiveByOwner(...)`) | DML, business rules, mutating state |

The base classes already encode the safety rails: `BaseService` exposes `beginTransaction`/`rollbackTransaction`/`logAndRethrow`, `BaseSelector` defaults to `AccessLevel.USER_MODE`, and `BaseDomain` operates over `List<SObject>` plus optional `oldMap` only.

## Splitting signals

Split when **any** of these are true:

- The class is over **400 lines** and trending upward.
- A single class issues SOQL, performs DML, validates per-record state, AND orchestrates cross-object work.
- The same SObject is queried from **3+ classes** with copy-pasted SOQL — Selector overdue.
- Business logic lives directly inside a `trigger` body or inside a handler that also runs SOQL.
- Test setup is dominated by mocking unrelated concerns (signals tangled responsibilities).
- A "Manager" / "Util" / "Helper" suffix appears and the class touches more than two SObjects.

## Extension and naming rules

- `AccountsDomain extends BaseDomain` — always plural SObject + `Domain`.
- `AccountMergeService extends BaseService` — verb phrase + `Service`; one service = one cohesive use case.
- `AccountsSelector extends BaseSelector` — plural SObject + `Selector`, one Selector per SObject.
- Trigger handlers stay in their own `<X>TriggerHandler` class and own only the dispatch table.
- Cross-Service calls go through interfaces, not concrete types, so dependencies stay testable.

## When NOT to split

- Throwaway one-off utilities (data fix scripts, one-time migrations).
- Prototypes still in flux where the responsibilities have not yet stabilised.
- Sub-100-line classes with a single responsibility — splitting just adds ceremony.
- Pure invocable wrappers around a single Service call.

## Ordering of split (lowest risk first)

1. **Extract the Selector first.** SOQL has the cleanest seam: move every `[SELECT ...]` to `<X>Selector` methods named by intent. No behaviour change, easiest to verify.
2. **Extract the Service next.** Move orchestration, DML, and savepoint handling into a `<X>Service` that calls the new Selector. Use `BaseService.beginTransaction()` / `logAndRethrow()`.
3. **Extract the Domain last.** Pull per-record validation and field derivation into `<X>Domain` operating on `Trigger.new` (and `Trigger.oldMap` when needed).

Reversing this order risks moving logic before its data dependencies are clear.

## Stateful vs stateless

All three layers are **stateless across invocations**:

- Selectors take arguments, return query results, hold no caches.
- Services receive a request object (or arguments) per call and return a response — no instance fields holding mid-flight state.
- Domains hold the records they were constructed with for the duration of one trigger context only — they are not reused across transactions.

State that must persist belongs in a Custom Setting / CMDT / Platform Cache, not on a Service or Selector instance.

## Anti-pattern: the "Manager" class

A class named `AccountManager` that opens savepoints, runs SOQL, validates per-record fields, and updates Contacts is doing all four roles at once. It is unbulkable, untestable in isolation, and a magnet for further bloat. Split immediately along the four-role boundary above.

## Recommended Workflow

1. Inventory the target class — count lines, list SObjects touched, mark every `[SELECT`, every DML statement, every per-record loop with validation, and every callout.
2. Classify each block by role (Trigger dispatch / Domain / Service / Selector) and confirm the split is justified by the signals above; if not, stop.
3. Extract the Selector first — create `<X>Selector extends BaseSelector` with intent-named methods, replace inline SOQL with calls to it, run tests.
4. Extract the Service next — create `<X>Service extends BaseService`, move DML/orchestration/savepoint handling, ensure SOQL only flows through the Selector.
5. Extract the Domain last — create `<X>Domain extends BaseDomain`, move per-record validation and derivation, ensure no SOQL/DML leaks in.
6. Wire the trigger handler to dispatch to Domain (for `before` validation/derivation) and Service (for `after` orchestration); keep the handler logic-free.
7. Re-run the project test suite; run `scripts/check_apex_class_decomposition_pattern.py` to confirm no Selector mutates and no handler still embeds SOQL.

## Review Checklist

- [ ] Every `[SELECT` lives in a `<X>Selector` method named by intent
- [ ] No DML inside any class extending `BaseSelector`
- [ ] No SOQL/DML/callouts inside any class extending `BaseDomain`
- [ ] Trigger handler delegates only — no business rules in the handler body
- [ ] Service classes use `BaseService.beginTransaction()` for transactional work
- [ ] No "Manager" / "Util" class still bundling all four roles
- [ ] Cross-Service calls go through interfaces, not concrete classes
- [ ] All three layers remain stateless across invocations

## Output Artifacts

| Artifact | Description |
|---|---|
| Split plan | Mapping from old class blocks to new Domain / Service / Selector classes |
| New class shells | `<X>Domain`, `<X>Service`, `<X>Selector` files extending the canonical base classes |
| Updated trigger handler | Dispatch-only handler routing to the new layers |
| Decomposition checker run | `scripts/check_apex_class_decomposition_pattern.py` clean exit |

## Related Skills

- `apex/trigger-framework` — choosing the trigger handler style
- `apex/fflib-enterprise-patterns` — full-fat enterprise pattern (Application, UoW, mocks)
- `apex/apex-savepoint-and-rollback` — transaction boundaries inside a Service
- `apex/apex-test-data-factory` — testing strategy after decomposition
