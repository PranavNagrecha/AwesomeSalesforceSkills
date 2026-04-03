# Well-Architected Notes — Apex Design Patterns

## Relevant Pillars

### Scalability

Good layering prevents each new requirement from increasing coupling exponentially. Query centralization and reusable service boundaries make the codebase safer to expand.

Tag findings as Scalability when:
- the same logic is duplicated across many entry points
- query sprawl makes tuning and limit management harder
- one class becomes a central bottleneck for every change

### Reliability

Patterns improve reliability when business rules live in one place and dependencies are easier to isolate in tests.

Tag findings as Reliability when:
- duplicated rules can drift between trigger, Flow, and API paths
- tests cannot isolate integrations or collaborators
- entry points directly mutate data with no service boundary

### Operational Excellence

Operational Excellence improves when the structure is easy to review, easy to onboard into, and predictable under change.

Tag findings as Operational Excellence when:
- class responsibilities are ambiguous
- layer names are present but not meaningful
- refactors require touching too many unrelated classes

## Architectural Tradeoffs

- **More layers vs lower ceremony:** layering helps as codebases grow, but tiny features can be over-abstracted.
- **Centralized selectors vs tailored queries:** reuse is good until selector methods become bloated.
- **Interface seams vs simplicity:** inject dependencies when they create genuine test or substitution value.

## Anti-Patterns

1. **God service class** — orchestration, queries, validations, and integrations in one place.
2. **Pattern-by-name only** — class names imply design without actually enforcing boundaries.
3. **Test-only branching instead of DI** — `Test.isRunningTest()` hiding a missing seam.

## Official Sources Used

- Apex Developer Guide — class structure and language boundaries
- Salesforce Well-Architected Overview — scalability, reliability, and operational excellence framing
