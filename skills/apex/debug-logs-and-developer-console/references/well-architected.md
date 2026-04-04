# Well-Architected Notes — Debug Logs And Developer Console

## Relevant Pillars

- **Operational Excellence** — Debug logs and the Developer Console are the primary instruments for diagnosing Apex behavior during development and targeted troubleshooting. Effective use of trace flags, appropriate log levels, and familiarity with log output format reduces mean time to diagnose issues and supports a more predictable release cycle.

- **Reliability** — Misusing debug tooling (leaving high-verbosity trace flags active, over-relying on anonymous Apex for data fixes without testing) introduces risk. Anonymous Apex that is not wrapped in a try/catch or verified in a transaction can leave records in a partial state. Knowing the limits of each tool prevents reliability incidents introduced during debugging itself.

## Architectural Tradeoffs

**Debug verbosity vs. log completeness:** Higher verbosity captures more detail but increases log file size and truncation risk. For most Apex debugging, ApexCode = DEBUG is sufficient. Reserve FINEST for the Apex Replay Debugger and checkpoint-based heap inspection, and only for the specific code path under investigation.

**Developer Console vs. VS Code + sf CLI:** The Developer Console is browser-native and requires no local tooling — good for quick queries, anonymous Apex, and log review. VS Code with the Salesforce Extension Pack offers the Apex Replay Debugger and is better for structured step-through debugging. Use the Developer Console for speed and VS Code for precision.

**Trace flag scope: User vs. Class vs. Automated Process:** User-scoped trace flags capture all Apex executed by a user, which can produce noisy logs. Class-scoped flags narrow output to a specific class regardless of who triggers it. Automated Process flags are required for background jobs. Choosing the narrowest scope reduces log noise and truncation risk.

## Anti-Patterns

1. **Leaving FINEST trace flags active across long sessions** — High-verbosity logs for a user fill the 50-log retention limit quickly and push out older logs that may still be needed. Always set a short trace window and delete the flag when done.

2. **Using anonymous Apex in production for data fixes without sandbox validation** — Anonymous Apex cannot be rolled back easily if it produces unintended results. Always test the script in a sandbox with representative data, verify the output count, and ensure the fix is idempotent before running in production.

3. **Relying on the Developer Console as the primary IDE** — The Developer Console does not support version control, source format alignment, or deployment validation. It is a diagnostic and quick-edit tool, not a full development environment. Use VS Code with Salesforce Extensions for code authoring; use the Developer Console for inspection and ad-hoc queries.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm — debug logs, trace flags, anonymous Apex behavior, log levels
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm — `System.debug` method signatures and `LoggingLevel` enum
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — operational excellence and reliability framing
