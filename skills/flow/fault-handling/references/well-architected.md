# Flow Fault Handling — Well-Architected Mapping

## Reliability

- Fault connectors prevent silent or generic failures from reaching production unchanged.
- Logging and deliberate error routing make failed interviews diagnosable.
- User-safe and support-safe error paths reduce repeat failures during live operations.

## Scalability

- Bulk review of record-triggered paths reduces load-time rollback surprises.
- Explicit review of repeated reads and related-record fan-out keeps flow designs safer under volume.

## Operational Excellence

- Consistent error logging and notification create supportable automation.
- Review checklists turn Flow failure handling into a repeatable release discipline.

## Pillars Not Addressed

- **Security** - this skill focuses on failure behavior and observability, not access design.
- **User Experience** - UX matters for screen flows, but the main goal is predictable automation failure handling.

## Official Sources Used

- **Metadata API Developer Guide — `Flow`** (`api_meta.txt` L68065+) — which node types
  carry `faultConnector` (`FlowRecordCreate` L70965, `FlowRecordUpdate` L71283,
  `FlowRecordDelete` L71046, `FlowRecordLookup` L71120, `FlowActionCall` L68476,
  `FlowApexPluginCall` L69688, `FlowWait` L72993) and which do not (`FlowSubflow`
  L72625–L72660, `FlowAssignment` L69729, `FlowDecision` L70225, `FlowLoop` L70698,
  `FlowScreen` L71427). Also `FlowConnector` L70147 and the declarative sample flow
  L73205–L73607 that the XML in `references/metadata-examples.md` is shaped from.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Metadata API Developer Guide — `FlowCustomError` / `FlowCustomErrorMessage`**
  (`api_meta.txt` L70006–L70040) — the Custom Error element's purpose ("roll back a change
  that triggered a flow"), its `Required` `connector`, and `isFieldError` /
  `fieldSelection` choosing inline-on-field against page-level window. Backs gotcha 9 and
  flow 3 of `references/metadata-examples.md`.
- **Metadata API Developer Guide — `FlowRecordRollback`** (`api_meta.txt` L71253–L71256) —
  "Available only in screen flows", API 52.0 and later. Backs gotcha 3 and the
  `recordRollbacks` element in flow 1.
- **Metadata API Developer Guide — `FlowOrchestratedStage`** (`api_meta.txt` L70803) — the
  `faultConnector` field described as "Not used." Backs gotcha 2 and anti-pattern 7.
- **Metadata API Developer Guide — `FlowTest` and subtypes** (`api_meta.txt` L73960–L74457)
  — `FlowTestAssertion` / `FlowTestCondition` / `FlowTestParameter`, the `HasError`
  operator (API 64.0 and later, L74203), `testType` = `WithAssertion` (API 66.0 and later,
  L74041), and the guide's own sample plus its `<version>66.0</version>` manifest
  (L74341–L74457). Backs section 4 of `references/metadata-examples.md`.
- **Metadata API Developer Guide — `FlowSettings.enableFlowUseApexExceptionEmail`**
  (`api_meta.txt` L116961–L116972) — process and flow error emails go to the user who last
  modified the flow (`false`, the default) or to the Apex Exception Email addresses
  (`true`). Backs gotcha 6 and the Setup verification step.
- **Metadata API Developer Guide — `CustomObject.publishBehavior`** (`api_meta.txt`
  L42206–L42229) — `PublishImmediately` against `PublishAfterCommit`, API 46.0 and later.
  Backs gotcha 5 and anti-pattern 5: whether a fault-path notification survives rollback
  is a property of the event definition, not of the flow.
- **Apex Developer Guide — "Triggers and Order of Execution"** (`apexdev.txt`
  L15402–L15490) — before-save flows at step 3, custom validation rules at step 5,
  after-save flows at step 14, commit at step 19, email and async paths at step 20. Backs
  gotchas 3, 5 and 10, and every rollback-scope claim in this skill.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide — "InvocableMethod Considerations"** (`apexdev.txt` L5419–L5459)
  — the input parameter must be a list, and inputs and outputs must match on size and
  order for bulkified execution. Backs gotcha 11, which corrects the older "not list-safe"
  framing.
- **Apex Developer Guide — per-transaction governor limits** (`apexdev.txt` L19544,
  L19554) — 100 SOQL queries and 150 DML statements synchronously. Backs gotcha 12 and the
  bulk-safety arithmetic in `SKILL.md`.
- **Apex Developer Guide — "Unhandled Exception Emails"** (`apexdev.txt` L39598–L39601) —
  Apex Exception Email recipients "can also receive process or flow error emails". Backs
  the Setup half of gotcha 6.
- **Object Reference — `FlowInterviewLog` / `FlowInterviewLogEntry`**
  (`object_reference.txt` L140058, L140206) — both are defined as logs of a **screen flow**
  interview, API 49.0 and later. Backs gotcha 7 and the correction to the triage runbook in
  `SKILL.md`.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Lightning Web Components Developer Guide — "Configure the Javascript Class for a Flow
  Local Action"** (`lwc_guide.txt` L8839–L8840) and **"Cancel an Asynchronous Request in a
  Flow Local Action"** (L8863) — the flow "takes the… fault connector and sets the error
  message to `$Flow.FaultMessage`"; the default message text; local-action requests time
  out after 120 seconds by default. Backs gotcha 8 and the message-design table in
  `SKILL.md`.
  https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-js-actions.html
- **Custom Error Element** — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_custom_error.htm&type=5
  (retained from the previous revision; help.salesforce.com is not fetchable from this
  environment, so the behavioural claims above rest on `api_meta.txt` instead).
- **Customize What Happens When a Flow Fails (fault connectors)** —
  https://help.salesforce.com/s/articleView?id=sf.flow_build_logic_fault.htm&type=5
  (retained from the previous revision; same caveat).
- **Salesforce Well-Architected** — reliability and operational-quality framing for the
  pillar mapping above.
