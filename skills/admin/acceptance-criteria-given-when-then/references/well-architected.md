# Well-Architected Notes — Acceptance Criteria Given/When/Then

## Relevant Pillars

- **Reliability** — A precise, paired AC block (every "should" has a "should not", every single-record path has a bulk path) is what catches the governor-limit and async-timing defects that turn a release into an outage. AC is the upstream artifact that determines whether reliability gets tested at all.
- **User Experience** — Behavior-driven AC keeps the contract focused on what the user can observe (a field value, a record state, an error message), not on UI chrome that changes between releases. UX outcomes are tested deterministically rather than by visual inspection.
- **Operational Excellence** — Given/When/Then is the canonical input shape for downstream agents (`agents/test-generator`, `agents/data-loader-pre-flight`, `agents/uat-test-case-designer`). When AC is in this shape, the whole test pipeline is automatable; when it is not, every handoff requires manual rework.

## Architectural Tradeoffs

- **Verbosity vs. precision** — Given/When/Then takes more lines than "the user can edit the record". The tradeoff is that it can be tested unambiguously. For a 1-line clarification fix, prefer a comment in the story; for any behavior that touches automation, sharing, or integration, the AC must be Given/When/Then.
- **Scenario Outlines vs. expanded Scenarios** — A Scenario Outline with an Examples table is denser but harder to scan. Use it when the same shape applies to 3+ data points; expand to discrete Scenarios when the shape genuinely diverges.
- **Synchronous vs. eventual Then** — A synchronous Then is easier to test but lies when the implementation is async. Always use `Then eventually within N seconds` for Queueable, Platform Event, batch, and integration-bound outcomes — even if the current implementation happens to commit synchronously.

## Anti-Patterns

1. **Compound AC with multiple Whens** — "When the user saves the record AND the manager approves AND the system sends an email." This is three Scenarios. Splitting them is what lets the team see exactly which behavior regressed.
2. **Happy-path-only AC** — Every Scenario without a paired negative-path Scenario is a half-finished AC block. Production defects almost always come from the missing deny-case, not the missing happy-case.
3. **AC that asserts implementation, not behavior** — "Given a Process Builder fires on Opportunity insert" couples the AC to the chosen automation tool. Replace with "Given an Opportunity is inserted" and let the design team pick Flow vs Apex via `standards/decision-trees/automation-selection.md`.

## Official Sources Used

- Salesforce Trailhead: Business Analyst Certification Preparation — https://trailhead.salesforce.com/credentials/businessanalyst — recommends if/then form for AC; this skill's Given/When/Then is the more rigorous extension.
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — anchors AC quality as a Reliability and Operational Excellence concern.
- Salesforce Trailhead: User Story Basics — https://trailhead.salesforce.com/content/learn/modules/user-story-basics — covers INVEST quality criteria; behavior-driven AC is what makes the "T" (Testable) checkable.
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm — required when an AC needs to reference a standard object's lifecycle (Opportunity StageName, Case Status, etc.).
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — required when AC mentions a permission set, validation rule, or sharing rule by metadata name.
