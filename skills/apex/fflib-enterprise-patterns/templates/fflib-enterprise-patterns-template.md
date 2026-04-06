# fflib Enterprise Patterns — Work Template

Use this template when working on tasks involving the fflib (Apex Enterprise Patterns) library.

## Scope

**Skill:** `fflib-enterprise-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Is fflib-apex-common deployed to the org?
- Does an Application.cls factory exist? Which SObject types are registered?
- What SObjects are in scope for this task?
- Are there existing Domain, Selector, or Service classes for these SObjects?

## Approach

Which fflib pattern applies?

- [ ] New Domain class (trigger logic, validation, field defaulting)
- [ ] New Selector class (centralized SOQL, FLS enforcement)
- [ ] New Service method (cross-object orchestration via UnitOfWork)
- [ ] UnitOfWork wiring for transactional DML
- [ ] Apex Mocks test isolation for existing fflib layer
- [ ] Incremental migration of existing code to fflib layers

## Application Factory Checklist

For every SObject touched by this task, verify:

- [ ] Domain registered in `Application.DomainFactory`
- [ ] Selector registered in `Application.SelectorFactory`
- [ ] Service registered in `Application.ServiceFactory` (if applicable)
- [ ] UnitOfWork SObject type list includes this SObject in correct parent-child order

## Review Checklist

Copy from SKILL.md and tick items as you complete them:

- [ ] Application.cls has factory registrations for every SObject used in the feature
- [ ] UnitOfWork SObject type list respects parent-before-child order
- [ ] Domain classes call `super(records)` or `super(records, sObjectType)` in the constructor
- [ ] Selector classes override `getSObjectType()`, `getSObjectFieldList()`, and enforce FLS
- [ ] Service methods obtain UnitOfWork from Application factory
- [ ] No direct DML outside of UnitOfWork `commitWork()`
- [ ] Triggers contain only `fflib_SObjectDomain.triggerHandler(...)` — no inline logic

## Notes

Record any deviations from the standard pattern and why.
