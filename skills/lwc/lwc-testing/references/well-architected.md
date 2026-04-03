# Well-Architected Notes - Lwc Testing

## Relevant Pillars

### Reliability

Reliable components need reliable tests. Jest coverage for happy paths, error states, and interaction contracts catches regressions before they escape to users.

### Operational Excellence

A healthy Jest setup reduces change risk, accelerates refactoring, and makes LWC delivery repeatable in CI instead of dependent on manual browser checks.

### User Experience

Unit tests that verify loading, error, empty, and success states directly protect the user experience because those states are where regressions usually surface first.

## Architectural Tradeoffs

- **Fast isolated tests vs full environment realism:** Jest is intentionally isolated and fast. It should prove component behavior, while other test layers handle broader integration.
- **Behavioral assertions vs snapshots:** Snapshots are cheap to add, but they do not cover user flows well without targeted assertions.
- **More mocks vs more confidence:** Mocking adds setup cost, but it allows meaningful coverage of failure paths that are hard to reproduce manually.

## Anti-Patterns

1. **Render-only tests with no behavior assertions** - the component can still break for users while the suite remains green.
2. **Flaky async guesses** - arbitrary `setTimeout` use produces brittle tests and hides real rerender boundaries.
3. **No project-level Jest governance** - missing scripts, dependencies, or cleanup patterns make test adoption inconsistent across components.

## Official Sources Used

- Test Lightning Web Components - https://developer.salesforce.com/docs/platform/lwc/guide/testing.html
- Write Jest Tests for Lightning Web Components That Use the Wire Service - https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-wire-utility?-escaped-fragment-=.html
- Best Practices for Development with Lightning Web Components - https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
