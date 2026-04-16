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
- Apex Developer Guide — governor execution limits, testing, transactions, and Apex behavior
- Apex Developer Guide — trigger and bulk request best practices
- Apex Developer Guide — naming conventions for Apex classes and methods
- Apex Developer Guide — code coverage best practices
- Secure Apex Classes (LWC guide) — component-facing Apex security when reviewing LWC-backed services
