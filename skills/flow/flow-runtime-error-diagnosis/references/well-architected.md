# Well-Architected Notes — Flow Runtime Error Diagnosis

## Relevant Pillars

- **Reliability** — Unhandled Flow errors that expose raw error messages to users or fail silently on certain records degrade org reliability. Adding fault path handlers and null checks makes flows resilient to edge cases and prevents transient data conditions from causing hard failures.
- **Operational Excellence** — Fault notification emails routed to an admin inbox, structured error handling, and systematic debug workflows keep flows observable and maintainable. Knowing which element failed and why, within minutes of a production error, is a core operational capability.

## Architectural Tradeoffs

**Fault paths on every DML element vs. selective fault paths:** Adding fault paths to all Get Records, Create, Update, and Delete elements is the safer architectural default. The overhead is low and ensures no runtime error ever surfaces as a raw platform message to users. The tradeoff is additional flow complexity — mitigate by routing all fault paths to a shared fault screen with a `{!$Flow.FaultMessage}` display.

**Null checks after every Get Records vs. only where needed:** Defensive null checks after every Get Records element are the correct default when the variable is used downstream in formulas or decisions. In high-volume record-triggered flows, every extra Decision element adds a small execution overhead — prioritize null checks where the variable drives logic rather than where it is only written to a field.

**Fix root cause vs. add fault path:** A fault path is not a substitute for fixing the underlying error. Fault paths are a safety net for unhandled edge cases. If a specific error is reproducible and understood, the correct fix is to eliminate the error condition (null check, fix field reference, move elements out of loops). Fault paths should handle genuinely unexpected failures.

## Anti-Patterns

1. **No fault path on any element** — All flow errors bubble up as raw platform messages to users. Add fault paths to at least all DML elements.
2. **Routing fault path back to a retry loop** — Fault paths cannot retry a failed DML. Retry loops create infinite execution risk. Use fault paths for graceful failure only.
3. **Not configuring fault email routing** — Fault emails going to the flow's last modifier are silently lost when that user leaves. Always configure org-level fault email routing.

## Official Sources Used

- Salesforce Help — Flow Error Handling — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_fault.htm
- Salesforce Help — Troubleshoot Your Flows — https://help.salesforce.com/s/articleView?id=sf.flow_troubleshoot.htm
- Salesforce Help — Debug a Flow in Flow Builder — https://help.salesforce.com/s/articleView?id=sf.flow_test_debug.htm
- Salesforce Help — Process Automation Settings — https://help.salesforce.com/s/articleView?id=sf.process_automation_settings.htm
- Apex Developer Guide — Execution Governors and Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
