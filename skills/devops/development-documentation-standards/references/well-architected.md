# Well-Architected Notes — Development Documentation Standards

## Relevant Pillars

- **Operational Excellence** — the primary pillar. Accurate, standardized in-source
  documentation and consistent naming are what make an org maintainable and hand-off-able.
  ApexDoc's own stated purpose is to *facilitate code collaboration and increase long-term
  code maintainability*, and its audience explicitly includes AI agents — so good docs are
  now an operational input to automated tooling, not just a courtesy to the next human. Because
  the compiler never enforces ApexDoc, operational maturity here means putting the enforcement
  somewhere it will actually run: code review and CI.
- **Security** — a lighter but real concern. Documentation should describe *that* a class runs
  `with`/`without sharing` and why, so reviewers understand the access posture — but doc
  comments must never embed secrets, credentials, or sensitive record data in `@example`
  blocks. Redact anything sensitive; a doc comment is shipped source.

## Architectural Tradeoffs

- **Coverage vs. noise.** Requiring ApexDoc on *every* surface can produce filler like
  `@param id The id`. Target public/global surfaces and the non-obvious parts of the contract
  (constraints, side effects, exceptions); let trivial private helpers carry a one-liner.
- **Convention adoption vs. house rules.** Adopting Salesforce's official naming conventions
  verbatim buys consistency with tooling, other teams, and new hires, at the cost of some
  existing local habits. Layer only genuinely org-specific additions on top.
- **Enforcement cost vs. drift.** A review gate plus a CI checker costs pipeline time but is
  the only thing that stops silent decay — the compiler will never catch a stale `@param`.

## Anti-Patterns

1. **Trusting the compiler** — assuming "it deployed" means the docs are accurate. ApexDoc is
   unenforced; wire a checker and a review gate instead.
2. **Inventing naming rules** — authoring a standard that contradicts the official Apex
   conventions, so code and tooling fight it. Adopt the prescribed conventions as the baseline.
3. **Scattered or absent standards** — per-developer documentation habits with no single
   agreed source. Keep one central design-standards document.

## Official Sources Used

- Apex Developer Guide — ApexDoc Introduction — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_doc_intro.htm
- Apex Developer Guide — ApexDoc Format (tag vocabulary, delimiters, compiler note) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_doc_format.htm
- Apex Developer Guide — ApexDoc Examples — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_doc_examples.htm
- Apex Developer Guide — Naming Conventions — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_naming_conventions.htm
- Salesforce Architects — Design Standards Template (org-wide naming + central documentation; architect.salesforce.com may 403 on direct fetch — verify in a browser) — https://architect.salesforce.com/resources/design-standards-template
