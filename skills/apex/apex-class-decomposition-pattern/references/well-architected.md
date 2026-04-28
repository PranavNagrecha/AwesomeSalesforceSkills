# Well-Architected Notes — Apex Class Decomposition Pattern

This skill maps primarily to **Operational Excellence** and **Scalability** in the Salesforce Well-Architected framework. It also strongly supports the cross-cutting maintainability concern that runs through every pillar (modular, resilient, adaptable code).

## Relevant Pillars

- **Operational Excellence** — the pattern produces systems that are observable, recoverable, and predictable in production:
  - *Observable* — `BaseService.logAndRethrow(source, e)` produces consistently formatted error logs (via `ApplicationLogger`). Because all Service entry points use the same helper, log mining is uniform across the org.
  - *Manageable* — savepoint/rollback handling is centralised in `BaseService.beginTransaction()` / `rollbackTransaction()`. There is exactly one place to audit transaction boundaries, not dozens of ad-hoc try/catch blocks.
  - *Compliant* — `BaseSelector.userMode()` defaults every query to `AccessLevel.USER_MODE`, enforcing CRUD/FLS/sharing automatically. System-mode access requires an explicit, reviewed override.
- **Scalability** — the pattern keeps the codebase scalable as team size and feature count grow:
  - *Modular* — each class has one reason to change. A new SOQL filter touches only the Selector. A new validation rule touches only the Domain. A new orchestration step touches only the Service.
  - *Bulk-safe by construction* — `BaseDomain` constructors take a `List<SObject>`, so per-record APIs are structurally discouraged; bulk handling is the default shape.
  - *Resilient* — bugs are contained. A bad query in `AccountsSelector` cannot accidentally rewrite Account state because Selectors do not perform DML. A faulty per-record rule in `AccountsDomain` cannot break unrelated callouts because Domains do not call out.
  - *Adaptable* — replacing the persistence layer (e.g., adding a Selector that reads from Salesforce Connect) requires changing one class. Adding a new use case is a new Service, not edits to an existing one.

## Concrete maintainability wins

| Before split | After split |
|---|---|
| 600-line class with intertwined SOQL, DML, validation | Four classes ≤ ~150 lines each, single responsibility |
| Same SOQL copy-pasted in 3 places | One Selector method called 3 times |
| Per-record validation requires DML setup to test | Domain method tested with `new AccountsDomain(records).validate(...)` — no DML |

## Architectural Tradeoffs

- **More files.** Splitting a 100-line utility into four classes adds ceremony without improving anything — see "When NOT to split" in `SKILL.md`.
- **Indirection cost.** A new contributor reading the code must hop through three classes to follow one use case. This is paid back at the second or third use case.
- **Naming discipline required.** `AccountsDomain` vs `AccountDomain` vs `Accounts` matters; drift breaks searchability. Suffixes are load-bearing.
- **No fflib safety net.** This lightweight pattern omits Application factory, Unit of Work, and the mocking framework. If your team needs those, plan a migration to `apex/fflib-enterprise-patterns` rather than half-implementing them.

## Anti-Patterns

1. **The "Manager" class** — `AccountManager` opens savepoints, runs SOQL, validates per-record fields, and updates Contacts. It is unbulkable, untestable in isolation, and a magnet for further bloat. Split along the four-role boundary.
2. **SOQL in a Service "for convenience"** — every `[SELECT` belongs in a Selector even if the method body is one line. The "small" exception multiplies into eight inline queries six months later.
3. **Per-record validation routed through the Service** — per-record rules live in the Domain, not in a Service that grows a per-record API surface for other callers to misuse.
4. **Empty Domain/Service/Selector trios scaffolded "just in case"** — empty shells are noise that pollutes search and slows IDE indexing. Create the layer when a real query / orchestration / validation needs a home.

## Official Sources Used

- **Salesforce Architects — Apex Enterprise Patterns**: <https://architect.salesforce.com/decision-guides/trigger-framework> and the Apex Enterprise Patterns trail (<https://trailhead.salesforce.com/content/learn/trails/build_apex_enterprise_patterns>) — the canonical articulation of the Domain / Service / Selector separation that this lightweight pattern derives from.
- **Salesforce Well-Architected Framework — Maintainability pillar**: <https://architect.salesforce.com/well-architected/adaptable/resilient> and related Maintainability pages — defines modular, resilient, adaptable as the maintainability sub-attributes referenced above.
- **Salesforce Well-Architected Framework — Operational Excellence**: <https://architect.salesforce.com/well-architected/trusted/secure> and the Trusted pillar pages — frame the observability and compliance benefits.
- **Apex Developer Guide — `WITH USER_MODE` / `AccessLevel.USER_MODE`**: <https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_with_user_mode.htm> — the security default `BaseSelector.userMode()` returns.
- **Apex Developer Guide — `Database.Savepoint`**: <https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_methods_system_database.htm> — semantics behind `BaseService.beginTransaction()`.
- **Repo template `templates/apex/README.md`** (and the base classes `BaseService.cls`, `BaseDomain.cls`, `BaseSelector.cls`) — the canonical local definition of the four-role split this skill instructs agents to apply.
