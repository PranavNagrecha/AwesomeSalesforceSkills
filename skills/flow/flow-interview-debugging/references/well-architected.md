# Well-Architected Notes — Flow Interview Debugging

## Relevant Pillars

- **Reliability** — an unobserved failure is indistinguishable from success
  until a customer notices. Fault paths that write durable log rows convert
  silent data loss into a countable, alertable event.
- **Operational Excellence** — the interview GUID printed in the flow error
  email joins to the same GUID on the log row, which is what turns "a flow
  failed somewhere last week" into a specific interview, version, record, and
  running user.
- **Security** — flow error emails carry the data involved in the interview,
  including user-entered data. Routing them to a broad alias widens the audience
  for that payload, so the recipient list is a security decision, not just an
  ops one.

## Architectural Tradeoffs

- **Log-and-continue vs abort:** continuing past a fault keeps the interview
  alive and produces a partial commit; aborting (Custom Error in a
  record-triggered flow, Roll Back Records in a screen flow) preserves
  consistency and costs the user a retry. Choose per fault path against whether
  the business outcome survives the step failing — a blanket policy is wrong in
  one direction or the other.
- **One shared fault-handler subflow vs per-element handlers:** a shared subflow
  is far less to maintain but cannot know which element called it, so the caller
  has to pass the element name as a literal at every call site. Per-element
  handlers duplicate structure but keep the attribution local. Both are
  defensible; an unattributed shared handler is not.
- **Custom log object vs error email only:** the email arrives instantly and
  needs no build; the log object is queryable, reportable, and alertable at a
  threshold. Production flows need both — the email as the interrupt, the object
  as the record of rate and trend.
- **Debugger fidelity vs iteration speed:** roll-back-on debug runs are fast and
  leave no residue but skip commit and everything after it. Roll-back-off runs
  are the only ones that exercise downstream automation and cost cleanup. Use
  the first while wiring, the second before shipping.

## Hygiene

- Error email recipient is set to Apex Exception Email Recipients, and that list
  is a managed alias rather than an individual.
- Every DML, Action, and Subflow element in a production flow has a fault
  connector.
- Every fault handler writes `$Flow.FaultMessage`, `$Flow.InterviewGuid`, the
  literal element name, the record Id, and the running user.
- `Interview_Guid__c` on the log object is an indexed External ID.
- The async and scheduled branches are verified in the Setup → Time-Based
  Workflow queue, not in the debugger.
- The Paused And Failed Flow Interviews page is reviewed on a cadence — since
  Spring '24 there is no platform cap on how many accumulate.

## Related

- `flow/fault-handling` — the fault-path patterns themselves.
- `flow/flow-runtime-error-diagnosis` — reading a specific runtime error.
- `flow/flow-bulkification` — when the diagnosis lands on a governor limit.
- `flow/flow-versioning-strategy` — when the failing version is not the version
  in Flow Builder.
- `standards/decision-trees/automation-selection.md` — when the honest answer to
  a repeatedly failing flow is that the work belongs in Apex.

## Official Sources Used

- Select Flow and Process Error Email Recipients — Process Automation Settings; *User Who Last Modified the Process or Flow* vs *Apex Exception Email Recipients*; error emails include the data involved in the interview — https://help.salesforce.com/s/articleView?id=sf.flow_troubleshoot_error_email.htm&type=5
- Customize What Happens When a Flow Fails — fault connectors and `{!$Flow.FaultMessage}` — https://help.salesforce.com/s/articleView?id=platform.flow_build_logic_fault.htm&type=5
- Flow Resource: $Flow Global Variables — `$Flow.FaultMessage`, `$Flow.InterviewGuid` — https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources_system_variables.htm&type=5
- Custom Error Element — record-triggered flows; displays a message and rolls back the transaction — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_custom_error.htm&type=5
- Test or Troubleshoot Flows with the Flow Builder Debugger — https://help.salesforce.com/s/articleView?id=platform.flow_test_debug.htm&type=5
- Scheduled Paths — queued entries appear on the Time-Based Workflow page in Setup — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_trigger_scheduled_path.htm&type=5
- Monitoring and Managing Paused and Failed Flow Interviews — https://help.salesforce.com/s/articleView?id=platform.automate_ala_monitor.htm&type=5
- Per-Transaction Apex Governor Limits — 100/200 SOQL, 150 DML, 50,000 query rows, 10,000 DML rows, 10,000 ms / 60,000 ms CPU, 6 MB / 12 MB heap — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Flow and Process Run-Time Changes in API Version 57.0 — removal of the 2,000 executed-elements limit — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_versioned_updates.htm&release=242&type=5
- Have Unlimited Paused and Waiting Flows (Spring '24) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_mgmt_remove_paused_interview_limit.htm&release=248&type=5
- Salesforce Well-Architected — Resilient — https://architect.salesforce.com/docs/architect/well-architected/resilient/resilient
