# Well-Architected Notes — Flow Debugging

## Relevant Pillars

- **Operational Excellence** — Debuggable flows are operationally maintainable flows. Element naming, fault paths with logged diagnostics, and Flow Test Suite coverage are the principal operational investments. A flow that fails silently in production with no error path and no Interview Log context is an operational liability.
- **Reliability** — Flows that are not designed to surface their own failure modes will eventually cause hard-to-diagnose production incidents. Fault emails are a minimum signal; a custom error log object provides durable diagnostics that survive the 7-day Interview Log retention window.
- **Security** — Debug runs that execute as the current admin user mask permission-related failures that affect standard users. The "Run As" option must be used deliberately to test record access and FLS under real user profiles.

## Architectural Tradeoffs

**Invest in naming and test coverage up front vs. debug reactively.**
Flows with descriptive element labels, documented decision rationale, and a basic Flow Test Suite are faster to diagnose by an order of magnitude compared to flows with generated names like `Decision_4` and no test assertions. The investment during authoring is small; the diagnostic savings during incidents are large.

**Custom error logs vs. relying on fault emails alone.**
Fault emails are sent to a single admin address and are not queryable. If an org processes thousands of records per day, fault emails become noise. A custom `Flow_Error_Log__c` object with fields for flow name, element, error message, record ID, and timestamp provides structured, queryable, durable diagnostics. The tradeoff is an additional object and maintenance overhead, but it is the correct choice for any flow that runs in a mission-critical transaction path.

**Flow Test Suite vs. manual regression testing.**
Manual debug runs verify a single scenario at a time and leave no audit trail. Flow Test Suite assertions are repeatable, auditable, and can be re-run by anyone. For flows that have more than two decision paths or that run on records owned by different user profiles, automated test coverage is not optional — it is the only way to catch regressions before they reach production.

## Anti-Patterns

1. **Debugging without reproducing the exact triggering conditions** — Running debug with default or empty variable values produces a trace that does not correspond to the real failure. The practitioner confirms the flow "works" on a different data path than the one that failed. Always match variable and field values to the actual failing scenario before interpreting debug output.

2. **Relying on fault emails as the sole error signal for high-volume flows** — Fault emails go to a single admin inbox, have no retention beyond the email itself, and cannot be queried. For flows processing significant record volumes, this means error patterns are invisible until someone manually reviews an inbox. Build a fault path that writes to a queryable custom object for any flow in a production transaction path.

3. **Activating new flow versions during peak usage without checking paused interviews** — Activating a new version immediately invalidates in-progress paused screen flow interviews. Doing this during business hours on a screen flow used for multi-step data entry will force users to restart their work with no warning. Always check Setup > Paused Flow Interviews before activating a new version.

## Official Sources Used

- Flow Builder (Salesforce Help) — debug mode, debug options, entry conditions, and Flow Test Suite
  https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5

- Flow Reference (Salesforce Help) — flow element behavior, fault paths, system variables including `$Flow.FaultMessage`
  https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5

- Salesforce Well-Architected Overview — operational excellence, reliability, and quality framing for automation design
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Process Automation Settings (Salesforce Help) — Send Flow Error Email configuration
  https://help.salesforce.com/s/articleView?id=sf.process_auto_settings.htm&type=5
