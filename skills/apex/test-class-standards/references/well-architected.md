# Well-Architected Notes — Test Class Standards

## Relevant Pillars

### Reliability

Reliable Salesforce delivery depends on tests that catch functional regressions before deployment. Weak tests allow defects into production even when code coverage is technically acceptable.

Tag findings as Reliability when:
- negative paths are untested
- bulk-sensitive logic has only single-record tests
- async or callout behaviors are not asserted correctly

### Operational Excellence

Operational Excellence improves when the test suite is deterministic, maintainable, and easy to extend. Factories, `@testSetup`, and explicit mocks reduce noise and make failures actionable.

Tag findings as Operational Excellence when:
- test setup is duplicated or inconsistent
- `SeeAllData=true` creates environment-specific fragility
- tests are difficult to diagnose because they do not clearly express intent

## Architectural Tradeoffs

- **Factory reuse vs test-local readability:** shared factories reduce duplication, but each test still needs clear local intent.
- **Broad fixtures vs focused setup:** a large baseline fixture is convenient until it obscures what a test actually depends on.
- **Coverage speed vs behavioral depth:** shallow tests run quickly but miss the failure modes that matter in Salesforce deployments.

## Anti-Patterns

1. **Coverage-only testing** — line execution without behavior verification.
2. **Org-data-dependent tests** — `SeeAllData=true` as a shortcut instead of isolated setup.
3. **Unmocked integration tests** — attempting real callouts or avoiding meaningful callout assertions altogether.

## Official Sources Used

- Apex Developer Guide — testing patterns, isolation guidance, and utility class usage
- Apex Reference Guide — `Test`, `HttpCalloutMock`, and related testing APIs
- Salesforce Well-Architected Overview — reliability and operational excellence framing
