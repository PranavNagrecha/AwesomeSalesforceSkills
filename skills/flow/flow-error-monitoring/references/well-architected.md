# Well-Architected Notes — Flow Error Monitoring

## Relevant Pillars

- **Reliability** — an unmonitored fault path is indistinguishable from a flow that works.
  Both produce a silent org. Monitoring is what makes the difference observable, and
  observability is the precondition for every reliability claim downstream of it.
- **Operational Excellence** — a portfolio is run by a rota, not by inbox archaeology. The
  artefacts that make a rota possible are a single sink, a backlog query, a drift query and
  an owner per severity band.

## Architectural Tradeoffs

### Where the error lands first

| Surface | What it is grounded on | What it is good for | What it cannot do |
|---|---|---|---|
| Error email | `enableFlowUseApexExceptionEmail` + `ApexEmailNotifications` (`api_meta.txt` L116961, L22415) | Zero-build coverage on day one | Aggregate, filter, or survive the recipient leaving |
| `FlowInterview` | `object_reference.txt` L139861 | Live state: paused, failed, which element | No history — the row is the interview, not a log of it |
| `FlowInterviewLog` | `object_reference.txt` L140059 | Screen-flow interview history | Holds nothing for record-triggered, scheduled or autolaunched flows |
| Debug log `FLOW_*` events | `apexdev.txt` L38792, L38821 | Exact element and limit usage for one run | Prospective and short-lived; `flow/flow-debugging` owns it |
| Custom log object | `templates/apex/custom_objects/Application_Log__c` | History, trend, alerting, ownership | Only exists where a fault connector was actually wired |

Rule: the first four are given to you and cover no more than the first hour of an incident.
The fifth is the only one you control, and it is the only one a portfolio-level SLA can rest
on. Build it, then use the other four to explain what it recorded.

### One sink versus per-domain sinks

| One `Application_Log__c` | A log object per business domain |
|---|---|
| One query answers "what is failing in this org" | Each team owns its schema and its retention |
| Shares `Request_Id__c` correlation with Apex logging | Cross-domain root cause needs a join nobody wrote |
| Field-level security is the only tenancy control | Sharing is natural per object |

Rule: one sink until a real compliance boundary forces a second. Two sinks created for
convenience become two half-monitored portfolios.

### Inline notification versus threshold on the log

| Inline (alert per fault) | Threshold (alert per N faults in a window) |
|---|---|
| Fastest possible notification | Survives a 200-record bulk save without 200 messages |
| Adds an action call to a transaction already failing | Adds latency equal to the evaluation window |

Rule: inline only where the flow is provably single-record; otherwise the fault writes and a
separate flow on the log object decides whether anyone is woken.

## Anti-Patterns

1. **Setting `enableFlowUseApexExceptionEmail` to `true` with no `ApexEmailNotifications`
   file** — the email now goes to an empty list instead of one individual. Strictly worse.
2. **Building the trend report on `FlowInterviewLog`** — it is the screen-flow log; a
   record-triggered portfolio reports zero errors forever.
3. **Paging off a dashboard** — no refresh cadence is documented anywhere in the guides, and
   the subscription is not deployable metadata.
4. **A second log object beside `Application_Log__c`** — splits the correlation surface the
   Apex side already writes to.
5. **Monitoring only the flows someone remembered to instrument** — coverage is a checker
   output over the whole source tree, not a list maintained by hand.
6. **Treating a green deploy as coverage** — in production, flows deploy inactive by default.

## Official Sources Used

- Metadata API Developer Guide, `FlowSettings` (`api_meta.txt` L116817–L117090;
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — the
  error-email recipient rule (`enableFlowUseApexExceptionEmail`, L116961–L116967), paused
  interview resumability (`enableFlowInterviewSharingEnabled`, L116918–L116925), and the
  deploy-as-inactive default (`enableFlowDeployAsActiveEnabled`, L116877–L116886) behind
  gotchas 1 and 7 and the `Flow.settings` fence in `references/metadata-examples.md` §3.
- Metadata API Developer Guide, `ApexEmailNotifications` (`api_meta.txt` L22415–L22520) —
  that flow errors may use this type, the `email`-or-`user` exclusivity, and the
  replace-on-deploy behaviour behind gotcha 8 and §4 of `references/metadata-examples.md`.
- Metadata API Developer Guide, `Flow` (`api_meta.txt` L68065+) — `faultConnector` on
  `FlowRecordCreate`/`Update`/`Delete`/`Lookup`, `FlowActionCall`, `FlowApexPluginCall` and
  `FlowWait`; its absence on `FlowSubflow` (L72625–L72660, gotcha 13); `interviewLabel`
  (L68156–L68160); `scheduledPaths` and `maxBatchSize` (L71389–L71400, gotcha 14). Grounds
  the flow XML in §1.
- Metadata API Developer Guide, `FlowTest` (`api_meta.txt` L73960–L74400) — test points
  limited to `Start`/`Finish` (L74141–L74148) and the `HasError` operator (L74203). Grounds
  §7 and gotcha 12.
- Metadata API Developer Guide, `Report` (`api_meta.txt` L103868–L105770) — folder-qualified
  manifest members, `ReportFilterItem` operators (L104595–L104660), `ReportFormat` values
  (L104676–L104690) and the sample definitions the report XML in §6 is shaped from.
- Metadata API Developer Guide, `CustomObject` `publishBehavior` (`api_meta.txt`
  L42206–L42227) — `PublishAfterCommit` versus `PublishImmediately`, behind gotcha 4's claim
  about what survives a rollback.
- Object Reference, `FlowInterview` (`object_reference.txt` L139861–L140055;
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) —
  supported calls and the Manage Flow requirement (L139864–L139871), `InterviewStatus` values
  (L139956–L139971), `Error` (L139907–L139913), `CurrentElement` (L139891), `PauseLabel`
  (L140013–L140019). Grounds the backlog query in §5a and gotchas 9, 10 and 11.
- Object Reference, `FlowInterviewLog` / `FlowInterviewLogEntry` (`object_reference.txt`
  L140059–L140290) — the screen-flow scope, the View All Data access rule (L140068–L140070)
  and the extra `Autosaved`/`Expired` status values (L140158, L140161). Grounds gotchas 2
  and 9.
- Object Reference, `FlowDefinitionView` and `FlowVersionView` (`object_reference.txt`
  L139268–L139860, L144970–L145300) — `IsOutOfDate` (L139405–L139412) and the mandatory
  `DurableId`/`FlowDefinitionViewId` filter (L145295–L145296). Grounds the drift queries in
  §5b and gotcha 6.
- Apex Developer Guide, debug-log events (`apexdev.txt` L38792, L38821;
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf)
  — `FLOW_ELEMENT_FAULT` at Workflow WARNING and above, and
  `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE` at FINER and above. Cited only to mark the boundary
  with `flow/flow-debugging`, which owns log reading as a method.
- Repo templates — `templates/apex/custom_objects/Application_Log__c.object-meta.xml` and its
  `fields/` (the sink and its `required`, `restricted` `Severity__c` behind gotcha 3),
  `templates/flow/FaultPath_Template.md` (the `$Flow.FaultMessage` / `$Flow.InterviewGuid`
  convention this skill inherits and marks as unverified), and
  `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` (the flow shape in §1).
