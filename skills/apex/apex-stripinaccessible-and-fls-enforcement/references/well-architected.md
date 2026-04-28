# Well-Architected Notes — Apex stripInaccessible and FLS Enforcement

## Relevant Pillars

- **Security** — This skill exists primarily to satisfy the Security pillar's "Trusted" sub-principle: protect customer data by enforcing the running user's CRUD/FLS on every Apex DML and outbound payload, not just on Lightning UI surfaces. `with sharing` enforces record visibility but is silent about field-level access; `Security.stripInaccessible` (and `WITH USER_MODE`) closes that gap.
- **Reliability** — Secondary. Stripping rather than throwing keeps user-facing operations from cascading into hard failures when only a subset of fields is restricted. Pair with `getRemovedFields()` logging so silent strips remain observable.
- **Performance** — Minor. `stripInaccessible` evaluates FLS per field per record and contributes to sync CPU. For 10k+ row collections, batch or chunk the strip rather than running it inline in a synchronous controller.

## Architectural Tradeoffs

| Choice | Pro | Con |
|---|---|---|
| `Security.stripInaccessible` (REMOVE-and-continue) | Graceful — operation completes with restricted fields silently scrubbed | Silent by default; without `getRemovedFields` logging, privilege-escalation attempts are invisible |
| `WITH USER_MODE` (THROW-on-inaccessible) | Loud — caller gets `QueryException` and knows immediately | Hard fail can break partially-permissioned UIs that expect a degraded view |
| Proactive `Schema.SObjectField.isCreateable()` checks | Cheap, fail-fast at the entry point | Easy to miss a field; not authoritative — must still strip before DML as defense-in-depth |
| `WITH SECURITY_ENFORCED` (legacy) | Available pre-API 58 | Deprecated in spirit; USER_MODE supersedes it |

The deepest tradeoff is per-entry-point: choose strip-and-log for end-user operations where partial success is acceptable, USER_MODE for backend or admin tooling where any FLS violation is a bug.

## Anti-Patterns

1. **DML on the original list after stripping** — calling `Security.stripInaccessible(...)` and then `insert userSupplied;` instead of `insert decision.getRecords();`. The strip returns a new list; the original is untouched. This is the single most common bug in this domain and gives a false sense of security to anyone reading the code.
2. **Single strip pass over a relationship-bearing parent collection** — assuming `stripInaccessible(UPDATABLE, cases)` also enforces FLS on `case.Contact.*` or child collections. It does not. Strip child collections separately.
3. **Trusting tests that run under default system context** — without `System.runAs(restrictedUser)`, test code bypasses FLS entirely and the strip is a no-op. The test passes for the wrong reason and provides zero assurance.

## Official Sources Used

- Apex Developer Guide — Strip Fields That Are Inaccessible to the Current User — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security_stripinaccessible.htm
- Apex Developer Guide — Filter SOQL Queries Using WITH SECURITY_ENFORCED — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_with_security_enforced.htm
- Apex Developer Guide — Enforce User Mode for Database Operations — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_with_user_mode.htm
- Apex Reference Guide — Security Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_Security.htm
- Apex Reference Guide — SObjectAccessDecision — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_SObjectAccessDecision.htm
- Salesforce Well-Architected — Trusted (Security) — https://architect.salesforce.com/well-architected/trusted/secure
