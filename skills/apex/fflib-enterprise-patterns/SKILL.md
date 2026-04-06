---
name: fflib-enterprise-patterns
description: "Use when adopting or working with the fflib (Apex Enterprise Patterns) open-source library — UnitOfWork, SObjectDomain, SObjectSelector, and Service layer classes — in a Salesforce Apex codebase. Triggers: 'fflib', 'UnitOfWork', 'SObjectDomain', 'enterprise patterns apex'. NOT for general Apex layering guidance without the fflib library (see apex-design-patterns) or for Apex Mocks setup in isolation."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "how do I use fflib UnitOfWork to coordinate DML"
  - "setting up SObjectDomain for trigger logic with enterprise patterns"
  - "fflib selector layer for centralized SOQL with FLS enforcement"
  - "service layer pattern using fflib Application class"
  - "enterprise patterns library structure for large Apex codebase"
tags:
  - fflib
  - unit-of-work
  - domain-layer
  - selector-layer
  - service-layer
  - enterprise-patterns
  - separation-of-concerns
inputs:
  - "existing Apex entry points (triggers, controllers, invocables, REST resources)"
  - "whether fflib is already installed or being adopted for the first time"
  - "current pain points — scattered DML, duplicated queries, untestable dependencies"
outputs:
  - "fflib layer wiring recommendation with Application factory configuration"
  - "UnitOfWork usage pattern for transactional DML coordination"
  - "Domain, Selector, and Service class scaffolds following fflib conventions"
dependencies:
  - apex-design-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# fflib Enterprise Patterns

Use this skill when a project already uses or plans to adopt Andrew Fawcett's fflib (Apex Enterprise Patterns) open-source library. The library provides concrete base classes — `fflib_SObjectUnitOfWork`, `fflib_SObjectDomain`, `fflib_SObjectSelector`, and the `Application` factory — that implement the separation-of-concerns layering described in the apex-design-patterns skill. This skill focuses on the library-specific conventions, class hierarchies, and wiring that fflib imposes on top of those general patterns.

---

## Before Starting

Gather this context before working on anything involving fflib:

- Is the fflib-apex-common package already deployed to the org, or does it need to be installed? Check for the `fflib_SObjectUnitOfWork` class in the org metadata.
- Does the project already have an `Application.cls` factory class that registers Domain, Selector, and Service bindings? If not, one must be created before any layer classes work.
- What SObjects will participate in the UnitOfWork transaction? The SObject type registration order in UnitOfWork determines DML execution order and must respect parent-child relationships.

---

## Core Concepts

### Application Factory — The Wiring Hub

The `Application` class is a static factory that maps SObject types to their Domain, Selector, Service, and UnitOfWork implementations. Every fflib project needs exactly one `Application` class. It uses `fflib_Application.UnitOfWorkFactory`, `fflib_Application.DomainFactory`, `fflib_Application.SelectorFactory`, and `fflib_Application.ServiceFactory` to register concrete implementations. At runtime, callers ask `Application.UnitOfWork.newInstance()` or `Application.Selector.newInstance(Account.SObjectType)` rather than constructing classes directly. This indirection is what enables Apex Mocks to swap in test doubles.

### UnitOfWork — Transactional DML Coordinator

`fflib_SObjectUnitOfWork` collects all DML operations — inserts, updates, deletes, and relationship registrations — during a transaction and commits them in a single pass at the end. The SObject types passed to `newInstance(new List<SObjectType>{ Account.SObjectType, Contact.SObjectType })` define the DML execution order: parents before children. You register records with `registerNew`, `registerDirty`, `registerDeleted`, and use `registerRelationship` to wire lookup fields between uncommitted parent and child records without needing the parent Id in advance. The `commitWork()` call issues all DML in the registered order inside a single transaction savepoint.

### Domain Layer — SObject-Scoped Business Logic

Classes extending `fflib_SObjectDomain` encapsulate validation, field defaulting, and business rules for a single SObject. The base class provides `onBeforeInsert`, `onAfterInsert`, `onBeforeUpdate`, `onAfterUpdate`, `onBeforeDelete`, and `onAfterDelete` overrides. The trigger handler dispatches to these methods automatically when wired through `fflib_SObjectDomain.triggerHandler()`. Domain classes receive a `List<SObject>` in their constructor and must call `super(records)` or `super(records, sObjectType)`. Keep domain logic focused on the records in scope — cross-object orchestration belongs in the Service layer.

### Selector Layer — Centralized Query Access

Classes extending `fflib_SObjectSelector` define the field set, SObject type, default ordering, and optional `with sharing` / FLS enforcement for every query path against a given SObject. The base class requires overriding `getSObjectType()`, `getSObjectFieldList()`, and optionally `getOrderBy()`. The selector provides `selectById(Set<Id>)` out of the box and you add custom query methods (e.g., `selectByAccountId(Set<Id>)`) as needed. All queries flow through `newQueryFactory()`, which automatically includes the registered field list and enforces FLS when `isEnforcingFLS()` returns true. This guarantees field-list consistency and simplifies security review.

---

## Common Patterns

### Service-to-UnitOfWork Orchestration

**When to use:** Any service method that creates or updates records across multiple SObjects in a single logical operation.

**How it works:** The Service method obtains a UnitOfWork from `Application.UnitOfWork.newInstance()`, queries via Selectors, applies Domain logic, registers all DML against the UnitOfWork, then calls `uow.commitWork()` once at the end.

**Why not the alternative:** Scattering `insert` and `update` statements across helper methods leads to partial-commit failures, governor limit waste from multiple DML statements, and difficulty rolling back on error.

### Domain Trigger Dispatch

**When to use:** When an SObject has trigger logic and the project uses fflib.

**How it works:** Create a single trigger per SObject that calls `fflib_SObjectDomain.triggerHandler(AccountDomain.class)`. The Domain constructor accepts `List<SObject>` and the base class dispatches to the correct `onBefore*`/`onAfter*` override based on `Trigger.operationType`.

**Why not the alternative:** Manually branching on `Trigger.isBefore`, `Trigger.isInsert`, etc. inside the trigger file itself defeats the purpose of the library and prevents Apex Mocks from replacing domain logic in tests.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New project, small team, < 20 Apex classes | General layering patterns without fflib | fflib adds ceremony; overhead not justified at small scale |
| Existing large codebase with scattered DML and untestable triggers | Adopt fflib incrementally, one SObject domain at a time | UnitOfWork and Domain wiring pay off at scale; incremental adoption avoids big-bang risk |
| Need to mock Selectors and Services in unit tests | Use fflib with Apex Mocks | Application factory + ApexMocks enables stub injection without `Test.isRunningTest()` branches |
| Project already has a home-grown trigger framework | Evaluate migration cost vs. benefit before replacing with fflib Domain | Switching mid-project can be expensive; sometimes wrapping existing framework is more pragmatic |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working with fflib:

1. Confirm fflib-apex-common is deployed. Search the org metadata for `fflib_SObjectUnitOfWork.cls`. If absent, deploy the package from the official GitHub repository.
2. Locate or create the `Application.cls` factory. Verify that Domain, Selector, Service, and UnitOfWork factories are registered with the correct SObject type mappings.
3. For the SObject in scope, create or update the Domain class extending `fflib_SObjectDomain`. Wire the trigger to call `fflib_SObjectDomain.triggerHandler(YourDomain.class)`.
4. Create or update the Selector class extending `fflib_SObjectSelector`. Register the field list, SObject type, and any custom query methods. Ensure `isEnforcingFLS()` returns true unless there is a documented reason to skip FLS.
5. Implement the Service method. Obtain UnitOfWork from the Application factory, use Selectors for queries, apply Domain rules, register DML, and call `commitWork()` once.
6. Write tests using Apex Mocks to stub Selectors and Services via the Application factory. Verify Domain logic with real DML in focused integration tests.
7. Run the checker script (`check_fflib_enterprise_patterns.py`) against the project metadata to detect common structural issues like missing Application bindings or direct DML outside UnitOfWork.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Application.cls has factory registrations for every SObject used in the feature
- [ ] UnitOfWork SObject type list respects parent-before-child order
- [ ] Domain classes call `super(records)` or `super(records, sObjectType)` in the constructor
- [ ] Selector classes override `getSObjectType()`, `getSObjectFieldList()`, and enforce FLS
- [ ] Service methods obtain UnitOfWork from Application factory, not via `new fflib_SObjectUnitOfWork(...)`
- [ ] No direct DML (`insert`, `update`, `delete`) appears outside of UnitOfWork `commitWork()`
- [ ] Triggers contain only `fflib_SObjectDomain.triggerHandler(...)` — no inline logic

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **UnitOfWork SObject order determines DML order** — If you register Contact before Account, the UnitOfWork will attempt to insert Contacts before their parent Accounts exist, causing a `REQUIRED_FIELD_MISSING` error on the lookup field.
2. **Domain constructor must accept List<SObject>** — The trigger handler uses reflection to instantiate Domain classes. If your constructor signature does not match `(List<SObject>)` or `(List<YourSObject>)`, the handler throws a runtime exception with a confusing message.
3. **Selector FLS enforcement is opt-in** — `fflib_SObjectSelector` does not enforce FLS by default. You must override `isEnforcingFLS()` to return `true`. Forgetting this means queries silently return fields the running user should not see.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Application.cls | Central factory class registering all Domain, Selector, Service, and UnitOfWork bindings |
| Domain class | `fflib_SObjectDomain` subclass for each SObject with trigger logic |
| Selector class | `fflib_SObjectSelector` subclass for each SObject with centralized query methods |
| Service class | Stateless service methods that orchestrate Domain, Selector, and UnitOfWork |

---

## Related Skills

- apex-design-patterns — General Apex layering concepts that fflib implements; use when evaluating whether fflib is the right choice
- apex-mocking-and-stubs — Apex Mocks integration for test isolation when using fflib Application factory
- trigger-framework — Alternative trigger dispatch approaches; compare before adopting fflib Domain layer
- soql-security — FLS and CRUD enforcement patterns that complement Selector-layer security
