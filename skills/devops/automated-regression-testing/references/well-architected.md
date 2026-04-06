# Well-Architected Notes — Automated Regression Testing

## Relevant Pillars

- **Reliability** — Automated regression testing is the primary mechanism for detecting platform regressions before they impact users. Without automated suites running against pre-release sandboxes, teams discover breakage only after Salesforce GA cutover — when the blast radius is maximum. A well-maintained regression suite converts release risk into a scheduled, measurable activity.

- **Operational Excellence** — Regression suites integrated into CI/CD pipelines enforce consistent quality gates without manual intervention. Page Object Model architecture reduces maintenance cost per release cycle. JUnit XML output enables trend analysis across releases, making regression velocity visible to engineering leadership.

- **Adaptability** — Salesforce ships three major releases per year, each potentially changing component DOM structures, API behaviors, and UI patterns. A regression suite built on proper abstraction layers (UTAM page objects, Provar metadata connections) adapts to these changes through localized page object updates rather than wholesale test rewrites. Teams without this adaptability accumulate automation debt that eventually makes the suite unmaintainable.

## Architectural Tradeoffs

**UTAM (open-source) vs Provar (commercial):** UTAM is free and Salesforce-maintained, but requires manual page object creation for custom components and Java/JavaScript expertise. Provar auto-generates locators from org metadata and offers a lower-code IDE, but carries license cost and vendor lock-in. The tradeoff is development velocity and skill requirements vs budget and flexibility.

**Headless vs headed execution:** Headless Chrome is faster and CI-friendly but cannot catch visual regressions (layout shifts, overlapping elements, CSS breakage). Headed execution with screenshot capture catches visual issues but is slower and requires display infrastructure. The pragmatic middle ground is headless for CI with periodic headed runs that capture screenshots for visual diff review.

**Test data isolation vs shared data:** Isolated test data (created and torn down per test) is reliable but slow, especially in Salesforce where DML operations count against governor limits and sandbox data volumes affect test duration. Shared seeded datasets are faster but create inter-test dependencies and order-sensitive failures. The recommended approach is per-suite setup with API-based data creation (bypassing UI) and per-test teardown of only the records that test modified.

## Anti-Patterns

1. **Screenshot-only regression testing** — Teams that rely solely on visual screenshot comparison (pixel diffing) without functional assertions. Salesforce UI changes cosmetically with every release (spacing, font rendering, icon updates) causing massive false positives that train the team to ignore alerts. Functional assertions on element state, text content, and record outcomes must be the primary regression signal, with visual checks as a supplement.

2. **Recording-based test generation without abstraction** — Using Selenium IDE or similar record-and-playback tools to generate tests directly. The recorded selectors are absolute paths through the current DOM structure, which Salesforce changes frequently. Without a page object layer, every recorded test becomes a maintenance liability after one release cycle.

3. **Testing only in production-copy sandboxes** — Running regression suites exclusively against full-copy sandboxes that mirror production data. This couples tests to production data state, makes tests non-deterministic (data changes between refreshes), and prevents pre-release testing (full-copy sandboxes cannot be pre-release). Regression suites should target partial or developer sandboxes with controlled test data, or scratch orgs with deterministic shape definitions.

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing for reliability and adaptability pillars
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- UTAM Developer Guide — page object model framework for Shadow DOM traversal and LWC testing
  https://utam.dev/guide/introduction
- Salesforce DX Developer Guide — scratch org configuration, sandbox management, CLI-based testing workflows
  https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce Developers Blog — UTAM adoption patterns, Shadow DOM testing strategies
  https://developer.salesforce.com/blogs
- Lightning Web Components Developer Guide — Shadow DOM behavior, Locker Service, Lightning Web Security
  https://developer.salesforce.com/docs/platform/lwc/guide
