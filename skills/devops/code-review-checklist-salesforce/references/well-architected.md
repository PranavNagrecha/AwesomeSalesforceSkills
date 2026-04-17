# Well-Architected Notes — Code Review Checklist Salesforce

## Relevant Pillars

- **Security** — Code review is where implicit `without sharing`, missing FLS enforcement, and unsafe dynamic SOQL are caught before ship. Tying findings to explicit sharing and access patterns keeps reviews objective.
- **Performance** — Governor-efficient code reduces latency, queue backlog, and surprise production failures under real batch sizes.
- **Scalability** — Bulk-safe patterns are the difference between a feature that works for pilot data and one that survives enterprise row volumes.
- **Reliability** — Meaningful tests and clear error handling reduce escaped defects and shorten incident response.
- **Operational Excellence** — Repeatable checklists and PR artifacts make reviews teachable and auditable across teams and releases.

## Architectural Tradeoffs

Strict user-mode SOQL everywhere improves safety but can increase `FlsException` noise if UX does not surface field access errors — reviewers should confirm the UI handles those failures. Partial success DML improves throughput for integrations but complicates transactional semantics; the checklist should flag whether the business really needs per-row success. Thin triggers with indirection add files and indirection cost but simplify testing and governor reasoning versus monolithic trigger bodies.

## Anti-Patterns

1. **Coverage-driven tests** — High percentage with no assertions; replace with behavior-focused cases.
2. **“Works on my sample” bulk** — Only testing with small lists; require 200-row paths for trigger code.
3. **Undocumented system mode** — Elevated access without comment in code or PR; treat as blocking until rationale and scope are documented.

## Official Sources Used

- Salesforce Well-Architected Overview — quality framing for what “done” means beyond syntax
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Apex Developer Guide — Running Apex within Governor Execution Limits
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_limits_tips.htm
- Apex Developer Guide — Trigger and Bulk Request Best Practices
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_bestpract.htm
- Apex Developer Guide — Naming Conventions
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_naming_conventions.htm
- Apex Developer Guide — Code Coverage Best Practices
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_code_coverage_best_pract.htm
- Secure Apex Classes (LWC guide) — component-facing Apex security when reviewing LWC-backed services
  https://developer.salesforce.com/docs/component-library/documentation/en/lwc/security_apex
