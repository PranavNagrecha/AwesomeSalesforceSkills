# Well-Architected Notes — Salesforce Debug Log Analysis

## Relevant Pillars

### Operational Excellence

Debug-log forensics is how an operations team recovers from opaque production incidents. The ability to read, classify, and explain a log in structured terms is a core Operational Excellence capability.

Tag findings as Operational Excellence when:
- the organization lacks a repeatable workflow for log analysis
- debug logs are captured only reactively, after users report incidents
- analysts blame the first trigger they see rather than classifying the writing mechanism
- managed-package traces are treated as unanalyzable rather than documented with known signatures
- post-incident reports do not explicitly state what the log could not prove

### Reliability

Log analysis is the feedback loop that makes the platform reliable over time. Misreading a log leads to the wrong fix, which makes the next incident worse.

Tag findings as Reliability when:
- the root cause pointed to by hasty log analysis is contradicted by subsequent incidents
- flip-flop fields recur because the actual writing mechanism was never identified
- governor-limit hits are "solved" by raising buffer sizes rather than fixing the underlying cascade
- async failures are retried without root-cause attribution

## Architectural Tradeoffs

- **Broad trace levels vs targeted trace levels:** `APEX_CODE,FINEST + WORKFLOW,FINER` captures everything but hits the 20 MB cap in seconds; `APEX_CODE,FINE + WORKFLOW,INFO` captures less but lets the log cover the full cascade. Default to the minimum level that still shows the event type you need.
- **Single-log analysis vs multi-log correlation:** one log is easier to read but rarely shows the real cause of async or cross-transaction issues. A cross-log timeline is more work but reveals retry loops, time-based actions, and concurrent writers.
- **Forensic analysis vs live debugging:** Apex Replay Debugger steps through a captured log interactively; `/mnt/user-data/uploads` + grep/Python is faster for triaging a stack of logs. Pick the tool that matches the question.
- **Fix the symptom vs fix the cascade:** stopping one flow or trigger often just moves the problem. Identify *why* the cascade happens (bulk load pattern, legacy automation, recursion) and fix that level.

## Anti-Patterns

1. **Blaming the first trigger logged** — it is almost never the writer. Classify the mechanism (Apex direct, Flow assignment, rollup, formula) before accusing any component.
2. **Treating managed-package internals as debuggable** — code inside `ENTERING_MANAGED_PKG` is deliberately opaque. Use known package signatures from `managed-packages.md` and route unresolved behavior to the package vendor.
3. **Drawing conclusions from a truncated log** — a log at exactly 20 MB with no `EXECUTION_FINISHED` is truncated. Analyzing it as if complete leads to wrong conclusions about which events ran last.
4. **Ignoring `What the log cannot tell you`** — every report should explicitly list the questions the log cannot answer, with concrete next steps (impersonate user, query CronTrigger, open field metadata). Silence on limits is dishonest.
5. **Loading all references up-front** — the reference folder has 12+ category guides. Preloading them wastes attention. Classify the question first (Step 3) and load only the matching reference.
6. **Summing `DML_BEGIN.Rows`** — those values are per-statement, not cumulative, and bulk operations log multiple statements. Use `TESTING_LIMITS` or `LIMIT_USAGE_FOR_NS` for governor-limit accounting.

## Official Sources Used

- Apex Developer Guide — [Debug Log](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_debugging_debug_log.htm), [Log Event Reference](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_log_events_reference.htm)
- Apex Reference Guide — [System.Limits](https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_limits.htm)
- Salesforce Developer Guide — [Order of Execution](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm)
- Salesforce Architects — [Well-Architected: Trusted > Resilient](https://architect.salesforce.com/well-architected/trusted/resilient), [Well-Architected: Adaptable > Composable](https://architect.salesforce.com/well-architected/adaptable/composable)
