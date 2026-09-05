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

- **Apex Developer Guide — "Debug Event Types" `FLOW_*` table** (`apexdev.txt` L38714–L38911;
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf)
  — every event name, its "fields or information logged", its category and its minimum level:
  the `FLOW_ELEMENT_FAULT` (WARNING+) vs `FLOW_ELEMENT_ERROR` (ERROR+) distinction the whole
  method turns on, plus `FLOW_VALUE_ASSIGNMENT`, `FLOW_RULE_DETAIL`, `FLOW_LOOP_DETAIL`,
  `FLOW_SUBFLOW_DETAIL`, `FLOW_BULK_ELEMENT_*` and the `*_LIMIT_USAGE` limit list.

- **Apex Developer Guide — "Debug Log Categories", "Debug Log Levels", "Debug Log Limits",
  "Debug Log Order of Precedence"** (`apexdev.txt` L38113–L38126, L38341–L38403, L39542–L39560)
  — that the `Workflow` category "includes information for workflow rules, flows, and
  processes"; the eight cumulative levels; the 20 MB truncation that removes lines "from any
  location, not just the start"; the 1,000 MB ceilings that disable trace flags; the default
  `WORKFLOW: INFO`; and that `TraceFlag` and `DebugLevel` are Tooling API objects
  (L39543–L39546), which is why no capture artefact in this package is deployable metadata.

- **Object Reference — `FlowInterview`, `FlowInterviewLog`, `FlowInterviewLogEntry`,
  `FlowRecordRelation`, `ApexLog`** (`object_reference.txt` L31307–L31311, L139861–L140302,
  L143527–L143600; https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf)
  — the scope split this package is built around (`FlowInterview` covers any flow;
  `FlowInterviewLog` is documented as the **screen flow** log), `CurrentElement`, the
  queryable `Error` field from API 62.0, `InterviewLabel`, the `InterviewStatus` and
  `LogEntryType` picklists, and the 7-day / 24-hour `ApexLog.Location` retention split that is
  routinely misattributed to the Flow Interview Log.

- **Metadata API Developer Guide — `Flow`** (`api_meta.txt` L68065–L73220;
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — `interviewLabel`
  (L68156–L68160), `runInMode` and its three context values (L68374–L68390), `FlowVersionStatus`
  (L68416–L68424), the `faultConnector` field on `recordLookups` / `recordUpdates` /
  `recordCreates` (L70965, L71120, L71283), `doesRequireRecordChangedToMeetCriteria`
  (L71320–L71322), and `triggerType` / `recordTriggerType` (L72448–L72525).

- **Metadata API Developer Guide — `FlowTest` and `FlowDefinition`** (`api_meta.txt`
  L73920–L74400) — that `FlowTest` covers record-triggered, autolaunched and Data
  Cloud-triggered flows only (L73961–L73962), that test points exist only at `Start` and
  `Finish` (L74139–L74147), the `HasError` operator from API 64.0 (L74203), the `testType`
  requirement from API 66.0 (L74041–L74050), and that a deployed `flowDefinition`'s
  `activeVersionNumber` overrides the `status` in the flow files (L73929–L73931).

- **Metadata API Developer Guide — `FlowSettings`** (`api_meta.txt` L116817–L117080) —
  `enableFlowUseApexExceptionEmail` and its default of `false`, meaning flow error emails go
  to "the user who last modified the process or flow" (L116961–L116967), plus
  `enableFlowViaRestUsesUserCtxt` (L116968–L116972). `flow/flow-governance` owns this file;
  it is cited here only to explain a missing fault email.

- **Apex Reference Guide — `flowtesting` namespace** (`apexrefguide.txt` L158183–L158187) —
  that flow tests are run with `sf flow run test`, and that the guide documents none of that
  command's flags.

- Salesforce Well-Architected Overview — operational excellence and reliability framing for
  automation observability
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- **Help-only, not fetchable, marked UNVERIFIED wherever used:** Flow Builder's Debug window
  and its "Run as a different user", "Roll back changes after the debug run" and per-element
  "Show Details" options; the `$Flow.FaultMessage` global (which appears in none of the
  guides above); Process Automation Settings as a UI surface.
  https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5 —
  https://help.salesforce.com/s/articleView?id=sf.process_auto_settings.htm&type=5
