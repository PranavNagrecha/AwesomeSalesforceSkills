# Well-Architected Notes — Apex Mocking And Stubs

## Relevant Pillars

### Reliability

Reliable Apex tests require realistic control over dependencies and failure paths. Good mocks and stubs improve behavioral confidence, not just deployment coverage.

Tag findings as Reliability when:
- failure scenarios are not mockable or untested
- production code hides missing seams with test-only branching
- tests depend on real external behavior accidentally

### Operational Excellence

Mocking infrastructure improves maintainability when it is focused and consistent across the team.

Tag findings as Operational Excellence when:
- mock classes are duplicated inconsistently
- fixture management is unclear
- there is no agreed pattern for collaborator seams

## Architectural Tradeoffs

- **Transport mock vs collaborator stub:** one validates HTTP behavior; the other validates orchestration around internal dependencies.
- **Inline mock classes vs reusable fixtures:** reuse helps until the mock framework becomes harder to understand than the tests.
- **Static resource fixtures vs inline JSON:** static resources keep tests cleaner for large payloads but require fixture maintenance discipline.

## Anti-Patterns

1. **`Test.isRunningTest()` as a seam substitute** — hides a structural problem.
2. **Only happy-path mocks** — undercuts confidence in failure handling.
3. **Mocking framework overbuild** — tests become harder to reason about than the production code.

## Official Sources Used

- Apex Developer Guide — `Test.setMock` and HTTP callout testing
- Apex Developer Guide — Stub API and `StubProvider`
- Apex Reference Guide — `Test` class behavior
