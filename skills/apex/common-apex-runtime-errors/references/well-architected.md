# Well-Architected Notes — Common Apex Runtime Errors

## Relevant Pillars

- **Reliability** — Runtime exceptions that are not anticipated and handled correctly cause transaction rollbacks, silent data loss (in async contexts), and cascading failures in downstream processes. Applying null guards, SOQL-safe patterns, and per-row DML error handling directly improves transaction reliability. The `LimitException` gotcha is a Reliability concern: limits are platform-enforced ceilings that must be avoided proactively.

- **Operational Excellence** — Diagnosing runtime exceptions requires readable debug logs and actionable error messages. Logging per-row `DmlException` details, surfacing the original cause of a `NullPointerException` rather than the secondary field-access line, and using `Limits.*` instrumentation are all Operational Excellence practices. They reduce mean time to diagnosis and enable non-specialist responders to triage issues from logs alone.

- **Security** — Indirectly relevant: when a query runs in user mode — explicit `WITH USER_MODE`, or any SOQL in a class whose `apiVersion` is 67.0+, where user mode is the default — a field the running user cannot read raises `QueryException`. That flavour of `QueryException` is an access-control signal, not an infrastructure fault and not the row-count cause this skill covers elsewhere; treating it as infrastructure causes security regressions when developers suppress the exception instead of fixing field permissions. The same signal arrives via the legacy `WITH SECURITY_ENFORCED` clause in classes pinned at 66.0 or below; the gate is the `apiVersion` in the class's `.cls-meta.xml`, not the org's release, so a Summer '26 org still compiles that clause in a class pinned to 58.0. At 67.0+ it does not compile at all — the compiler emits `WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead`, which is a build failure rather than a runtime error and so falls outside this skill. See `soql-security` skill, and `agents/_shared/AGENT_CONTRACT.md` § "Apex security idiom by API version" for the full version table.

- **Performance** — `LimitException` is the runtime signal of a performance failure. CPU limit breaches and SOQL limit breaches are both governor enforcement of performance constraints. The patterns in this skill (bulkification, pre-query Limits checks) are the reactive counterpart to the proactive patterns in `governor-limits`.

## Architectural Tradeoffs

**allOrNone=true vs. allOrNone=false for DML**

Using `allOrNone=true` (the default `insert records;` form) gives atomic all-or-nothing behavior: if one record fails, everything rolls back. This is correct for business processes where partial success is worse than total failure (e.g. financial transactions). Using `allOrNone=false` via `Database.insert(records, false)` allows partial success and requires the caller to inspect `SaveResult` records and take compensating action. The wrong choice here causes either data inconsistency (partial success when atomicity was required) or unnecessary data loss (total rollback when partial success was acceptable).

**Null guards vs. query result guarantees**

Adding null guards and `isEmpty()` checks on every SOQL result adds defensive boilerplate. The alternative — designing data models and access patterns that make null results structurally impossible (e.g. foreign key constraints, required field rules, guaranteed record existence in setup data) — reduces the need for per-call guards. Both approaches are valid. The skill covers defensive per-call patterns; data model design is covered by architect-domain skills.

## Anti-Patterns

1. **Catching LimitException as a recovery strategy** — Code that wraps SOQL or DML in a try/catch with `catch (LimitException e)` expecting to log and continue is dead code. The exception is uncatchable. Orgs that deploy this pattern have no actual limit protection in place and will experience unhandled transaction failures under bulk load. The correct pattern is upstream prevention with `Limits.*` checks and architectural bulkification.

2. **Swallowing DmlException without per-row inspection** — Catching `DmlException` and logging only `e.getMessage()` discards the per-row error details available via `getDmlMessage(i)`, `getDmlIndex(i)`, and `getDmlFields(i)`. Post-incident forensics become impossible because the log does not identify which records failed or why. Always extract and log per-row details.

3. **Scalar SOQL in reusable utility methods** — A utility method that performs a scalar SOQL assignment and returns the SObject is a reliability trap. Every caller inherits the `NullPointerException` or `QueryException` risk. Utility methods that query by ID or other non-guaranteed keys should return `null` or `Optional`-pattern results (using a wrapper) and document that null is a valid return.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Apex Built-In Exceptions — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_exception_builtin.htm
- Exception Class and Built-In Exceptions (Apex Reference) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_exception_methods.htm — authoritative list of built-in exception types; `MixedDmlException` does not appear in it (mixed DML raises `DmlException` with status code `MIXED_DML_OPERATION`)
- SOAP API Developer Guide — StatusCode enumeration — https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_concepts_core_data_objects.htm — confirms `MIXED_DML_OPERATION` is a real status code
- sObjects That Cannot Be Used Together in DML Operations (mixed DML / setup objects) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_non_mix_sobjects.htm
- MIXED_DML_OPERATION error (Help) — https://help.salesforce.com/s/articleView?id=000382600&language=en_US&type=1
- "Unable to lock row - Record currently unavailable" error (Help) — https://help.salesforce.com/s/articleView?id=000387767&language=en_US&type=1
- Apex Governor Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- The WITH SECURITY_ENFORCED SOQL Clause Is Removed (Summer '26 / API 67.0) — https://help.salesforce.com/s/articleView?id=release-notes.rn_apex_removed_withSecurityEnforced.htm&type=5 — grounds the version qualifier on the Security pillar note above
- Apex Exception Statements — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_exception_statements.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
