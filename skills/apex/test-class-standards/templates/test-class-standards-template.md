# Apex Test Blueprint

## Test Scope

| Item | Value |
|---|---|
| Class under test | |
| Entry point | Trigger / Service / Controller / Queueable / Batch / REST |
| Main behavior under test | |
| Negative scenario required | |
| Bulk scenario required | |
| Callout involved | Yes / No |

## Shared Setup

- `@testSetup` needed? Yes / No
- Factory methods required:
  - `Account`
  - `User`
  - `Custom metadata or settings access`
  - Other:

## Test Methods To Include

- [ ] Positive path
- [ ] Negative path with specific expected exception or validation outcome
- [ ] Bulk path
- [ ] Security or `runAs` path if access matters
- [ ] Callout mock path if integration is involved
- [ ] Async path with `Test.startTest()` / `Test.stopTest()` if applicable

## Assertion Checklist

- [ ] Assert on changed field values
- [ ] Assert on created or prevented related records
- [ ] Assert on explicit exception type or message when relevant
- [ ] Assert after `Test.stopTest()` for async work
- [ ] Avoid `System.assert(true)` and vague count-only assertions
