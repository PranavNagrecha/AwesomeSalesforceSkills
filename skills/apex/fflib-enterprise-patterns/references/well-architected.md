# Well-Architected Notes — fflib Enterprise Patterns

## Relevant Pillars

- **Scalability** — UnitOfWork batches DML operations, reducing the number of DML statements consumed per transaction. Selector centralization means query optimization changes propagate to all callers. These properties let an fflib codebase grow to hundreds of Apex classes without proportional governor-limit pressure.

- **Reliability** — UnitOfWork wraps all DML in a single commit, providing implicit rollback on failure. Without it, partial commits leave data in an inconsistent state. Domain classes centralize validation, ensuring that business rules fire consistently regardless of the entry point (trigger, REST, invocable, LWC controller).

- **Operational Excellence** — Separation of concerns makes the codebase navigable. A developer looking for Opportunity queries checks the Selector; one looking for Opportunity validation checks the Domain; one looking for business workflows checks the Service. This reduces onboarding time and code-review friction. The Application factory provides a single registry of all layer bindings, which serves as a living architecture map.

## Architectural Tradeoffs

**Ceremony vs. payoff at scale.** fflib introduces four layer classes, a factory, and a UnitOfWork per feature area. For a 10-class project this is overhead. For a 200-class project with multiple teams, the ceremony prevents the coupling and duplication that cause deployment failures and regression bugs. Evaluate adoption based on projected codebase size and team count.

**Testability vs. runtime indirection.** The Application factory adds a level of indirection that can confuse developers unfamiliar with the pattern. However, it enables Apex Mocks to replace any layer in tests, which eliminates slow integration tests and reduces test execution time significantly.

**Incremental adoption vs. consistency.** You can adopt fflib one SObject at a time, but a half-adopted codebase has two query patterns, two DML patterns, and two trigger dispatch patterns. Document which SObjects are on fflib and which are not, and set a timeline for full migration.

**FLS enforcement location.** Selector-level FLS enforcement (via `isEnforcingFLS()`) is the fflib-recommended approach, but it only covers Selector queries. Ad-hoc SOQL outside Selectors falls outside it, and is then enforced only by whatever access mode its own class runs in. The tradeoff is discipline: if all queries go through Selectors, FLS is centralized. If developers write SOQL outside Selectors, enforce it with `WITH USER_MODE` on the read and `as user` on the DML — or `Security.stripInaccessible(AccessType, records).getRecords()` on writes where dropping the inaccessible fields beats throwing on the whole statement. Which idiom is available is gated by the class's `apiVersion` in its `.cls-meta.xml`, not by the org's release: at 67.0+ database operations already run in user mode by default and `WITH SECURITY_ENFORCED` no longer compiles (`WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead`); at 57.0–66.0 both compile and `WITH USER_MODE` is the one to write; only at ≤56.0 is `WITH SECURITY_ENFORCED` still the idiom (with `Security.stripInaccessible`, 48.0+, on writes — `as user` does not exist below 57.0), and there prefer raising the class's `apiVersion` over hardening it in place.

## Anti-Patterns

1. **God Service with no Domain layer** — Putting all validation, defaulting, and cross-field logic in the Service class instead of the Domain class. The Service becomes a monolith that is hard to test, hard to reuse, and tightly coupled to every SObject it touches. Domain classes should own record-level rules; Services coordinate across Domains.

2. **Bypassing the Application factory** — Directly constructing `new OpportunitiesSelector()` or `new AccountsDomain(records)` in production code instead of going through `Application.Selector.newInstance(...)`. This breaks Apex Mocks injection and means tests cannot isolate layers.

3. **Using UnitOfWork as a dumping ground** — Passing a single UnitOfWork through 10+ method calls across unrelated features in a single request. The UnitOfWork should scope to a single service operation. If two independent operations need to commit separately (e.g., one can fail without rolling back the other), they need separate UnitOfWork instances.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Secure Apex Classes (LWC Guide) — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security
- The WITH SECURITY_ENFORCED SOQL Clause Is Removed (Summer '26 / API 67.0) — https://help.salesforce.com/s/articleView?id=release-notes.rn_apex_removed_withSecurityEnforced.htm&type=5 — grounds the API-version gate on the FLS tradeoff note above
