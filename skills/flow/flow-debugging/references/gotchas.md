# Gotchas — Flow Debugging

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Every claim carries the guide and line range it rests on, or an UNVERIFIED marker beside it.

## Gotcha 1: Debug Mode Commits Real DML in After-Save Flows Unless "Rollback" Is Checked

**What happens:** A practitioner uses Flow Builder Debug mode to test an after-save record-triggered flow in a sandbox. The flow includes a Create Records element that creates a related Task. After a few debug runs, the sandbox has dozens of orphaned Task records — each debug run committed real DML to the org.

**When it occurs:** Any debug run on an after-save record-triggered flow where the **"Roll back changes after the debug run"** checkbox is left unchecked. Before-save flows do not commit DML at the before-save boundary, but after-save flows run in a real transaction.

**How to avoid:** Always check **"Roll back changes after the debug run"** in the Debug modal when working with after-save flows that contain DML, unless you specifically need to verify committed data. Treat this as the default safe setting for all debug runs.

**UNVERIFIED (2026-09-05): the Debug window and its rollback checkbox are documented only
on help.salesforce.com, which cannot be fetched.** Neither the option nor its behaviour
appears in `api_meta.txt`, `apexdev.txt` or `object_reference.txt`. Confirm in the org
before running debug against data you care about — and prefer the log-capture path in
`references/metadata-examples.md` §3 when the data matters, because a captured log has no
write side effects at all.

---

## Gotcha 2: `FlowInterviewLog` Is the Screen-Flow Log — a Record-Triggered Flow Leaves Nothing In It

**What happens:** A support ticket describes a record-triggered flow failure. The practitioner navigates to the Flow Interview Log, or queries `FlowInterviewLog`, and finds nothing. The absence is read as "the flow never ran", and the next hour is spent on entry conditions that were fine.

**When it occurs:** Every time. `FlowInterviewLog` "represents the logs of a **screen flow** interview" (`object_reference.txt` L140059–L140060) and `FlowInterviewLogEntry` "represents the log of a specific element that's executed by a **screen flow** interview" (L140207–L140208). A record-triggered, autolaunched or scheduled flow is structurally out of scope. Access is also gated: "by default, only users with the View All Data permission can access the logs for flows that are run by other users" (L140068–L140070), so a delegated admin can get zero rows on a screen flow too.

The commonly quoted "7-day Flow Interview Log retention" is a different object's number. **No retention period for `FlowInterviewLog` is stated anywhere in the Object Reference.** Seven days is the retention of `ApexLog` records whose `Location` is `Monitoring` — "these types of logs are maintained for seven days or until a user deletes them", against 24 hours for `SystemLog` (`object_reference.txt` L31308–L31311; the same split appears at `apexdev.txt` L38118).

**How to avoid:** For anything that is not a screen flow, query `FlowInterview` instead — it "represents a flow interview. A flow interview is a running instance of a flow" (`object_reference.txt` L139861), with no flow-type qualifier. Filter on `InterviewStatus` and read `Error` and `CurrentElement`. Queries in `references/metadata-examples.md` §4b.

---

## Gotcha 3: "Run As" Debug Does Not Simulate All Sharing Behaviors

**What happens:** A practitioner uses Debug > Run as a specific user to test whether a flow works for a standard user. The debug session completes without error, but the same user reports a failure in production.

**When it occurs:** The flow's own `runInMode` can make the running user irrelevant. `FlowRunInMode` has three values (`api_meta.txt` L68374–L68390): `DefaultMode` — "how the flow is launched determines whether the flow runs in user context or in system context"; `SystemModeWithSharing` — "the flow respects org-wide default settings, role hierarchies, sharing rules, manual sharing, teams, and territories. The flow **doesn't respect object permissions, field-level access, or other permissions of the running user**"; `SystemModeWithoutSharing` — "the flow can access all data" (API 49.0+). Under either system mode, a Run As debug cannot reproduce a permission failure, because the flow is not consulting those permissions.

Beyond that, `enableFlowViaRestUsesUserCtxt` decides "whether a flow that runs via REST API uses the running user's profile and permission sets to determine the object permissions and field-level access of the flow" (`api_meta.txt` L116968–L116972) — so the same flow can enforce different access depending on how it was invoked.

**How to avoid:** Read `runInMode` on the flow before interpreting any Run As result. If it is `SystemModeWithoutSharing`, a Run As debug proves nothing about access and the failure is elsewhere. If the flow is invoked over REST, check `enableFlowViaRestUsesUserCtxt` too. **UNVERIFIED (2026-09-05): the Run As option itself is help-only and not in the corpus.**

---

## Gotcha 4: Activating a New Flow Version Changes the Fate of In-Progress Interviews

**What happens:** A screen flow is used for a multi-step wizard that users leave and resume later. A developer activates a new version mid-day. Users who had paused interviews find their sessions no longer behave as before.

**When it occurs:** On activation. The platform records this state explicitly: `FlowInterview.InterviewStatus` includes `VersionPaused` — "this flow version is paused. No more records are processed until the flow is resumed" — available in API version 60.0 and later (`object_reference.txt` L139961–L139975). `FlowInterviewLog.InterviewStatus` adds `Expired` on top of that, API 62.0 and later (L140157–L140166). So paused interviews on a superseded version are not silently deleted; they enter a distinguishable state you can query for.

**How to avoid:** Before activating, query for interviews that will be affected, and use `interviewLabel` to make them identifiable:

```soql
SELECT Id, InterviewLabel, CurrentElement, InterviewStatus, OwnerId, CreatedDate
FROM FlowInterview
WHERE InterviewStatus IN ('Paused', 'VersionPaused')
ORDER BY CreatedDate
```

**UNVERIFIED (2026-09-05): the exact user-visible consequence of activation for an already-paused interview — resumable on the old version, forced restart, or silently invalidated — is not stated in the Object Reference or the Metadata API guide.** The `VersionPaused` and `Expired` status values are grounded; the user experience behind them is not. `flow/flow-governance` owns the activation-window policy; test the resume path in a sandbox before an activation that matters.

---

## Gotcha 5: `FlowTest` Components Do Not Run Themselves on Deployment

**What happens:** A developer builds thorough flow tests in a sandbox, all pass, deploys, and assumes production behaviour is verified. It was not — nothing ran the tests in the destination org.

**When it occurs:** On every deployment. `FlowTest` is positioned as a pre-activation check: "**before you activate** a record-triggered, autolaunched, or Data Cloud-triggered flow, you can test it to verify its expected results and identify flow run-time failures" (`api_meta.txt` L73961–L73962). Nothing in the Metadata API guide states that a deployment executes them, and there is no `FlowTest` analogue of the Apex test-run coverage gate.

**How to avoid:** Run them explicitly after deploying — the `flowtesting` namespace "provides dynamically generated Apex classes for flow tests that are created in Flow Builder… You can run flow tests with the Salesforce CLI command `sf flow run test`" (`apexrefguide.txt` L158183–L158187). Gate on the observed exit code. **UNVERIFIED (2026-09-05): the corpus documents none of that command's flags or its exit-code behaviour** — "for more details about the command, use the Salesforce CLI `--help` flag" (L158186–L158187).

Note the coverage ceiling this implies: test points can only be placed at `Start` and `Finish` (`api_meta.txt` L74139–L74147), so no `FlowTest` can assert mid-flow. It tells you the flow failed, not where.

---

## Gotcha 6: `Workflow` at `ERROR` Silently Drops Every `FLOW_ELEMENT_FAULT`

**What happens:** An admin investigating a flow error sets the `Workflow` debug log category to `ERROR` — the level whose name matches the problem — reproduces the failure, and gets a log with no flow lines in it. The conclusion drawn is that the flow is not involved.

**When it occurs:** Whenever the flow has fault connectors, which is to say whenever it was built properly. The two failure events log at different floors: `FLOW_ELEMENT_FAULT` is "message, element type, and element name (fault path taken)" at **Workflow / WARNING and above** (`apexdev.txt` L38792), while `FLOW_ELEMENT_ERROR` is "message, element type, and element name (flow runtime exception)" at **Workflow / ERROR and above** (L38777). Levels are listed "from lowest to highest… NONE, ERROR, WARN, INFO, DEBUG, FINE, FINER, FINEST" and "the level is cumulative, that is, if you select FINE, the log also includes all events logged at the DEBUG, INFO, WARN, and ERROR levels" (L38389–L38403). Cumulation runs upward only: `ERROR` does not include `WARN`.

The consequence is exactly inverted from intuition. A badly built flow with no fault paths is *visible* at `ERROR`. A well-built flow with fault paths everywhere is *invisible* at `ERROR`.

**How to avoid:** Never set `Workflow` below `FINER` for a debugging session. `FINER` is also the floor for `FLOW_VALUE_ASSIGNMENT`, `FLOW_RULE_DETAIL`, `FLOW_LOOP_DETAIL` and every `*_LIMIT_USAGE` event, so there is no reason to pick anything lower. The full level matrix is in `references/metadata-examples.md` §3.

---

## Gotcha 7: The Default `Workflow` Level Logs Zero Element Events

**What happens:** A practitioner opens the Developer Console, reproduces the failure, opens the log, and sees `FLOW_START_INTERVIEW_BEGIN` and `FLOW_START_INTERVIEW_END` and nothing between them. The flow appears to have started and finished without doing anything.

**When it occurs:** Whenever no trace flag with a raised `Workflow` level is in effect. With no active trace flags the defaults are "DB: INFO, APEX_CODE: DEBUG, APEX_PROFILING: INFO, **WORKFLOW: INFO**, VALIDATION: INFO, CALLOUT: INFO, VISUALFORCE: INFO, SYSTEM: DEBUG" (`apexdev.txt` L39553–L39560). At `INFO` the interview-level events fire (`FLOW_START_INTERVIEW_BEGIN` / `_END`, `FLOW_CREATE_INTERVIEW_*`, `FLOW_INTERVIEW_PAUSED` / `_RESUMED`, all INFO+) but `FLOW_ELEMENT_BEGIN` and `FLOW_ELEMENT_END` are FINE+ (`apexdev.txt` L38768, L38774) and every `*_DETAIL` and `*_LIMIT_USAGE` event is FINER+.

**How to avoid:** Read the log header before reading the log. It contains "the log category and level used to generate the log", printed as a semicolon-delimited string such as `APEX_CODE,DEBUG;…;WORKFLOW,INFO` (`apexdev.txt` L38143–L38149). If it says `WORKFLOW,INFO`, your trace flag did not take effect — check the order of precedence, in which "trace flags override all other logging logic" (L39542–L39546), and confirm the flag is on the *saving* user, not on you.

---

## Gotcha 8: A Truncated Log Loses Lines From the Middle, Not the Top

**What happens:** A practitioner captures a log for a bulk save, greps for `FLOW_ELEMENT_BEGIN`, and finds the sequence jumps from one element to another with a gap. The missing element is investigated as if it never executed.

**When it occurs:** Above 20 MB. "Each debug log must be 20 MB or smaller. Debug logs that are larger than 20 MB are reduced in size by removing older log lines, such as log lines for earlier `System.debug` statements. **The log lines can be removed from any location, not just the start of the debug log**" (`apexdev.txt` L38115–L38118). There is no in-band marker at the point of loss, so a truncated log reads as a complete log with a smaller story in it. Setting the `Apex Code` category to `FINEST` makes this far more likely — the guide's own warning is that before a deployment you should "verify that the Apex Code log level isn't set to FINEST. Otherwise, the deployment is likely to take longer than expected" (L38405–L38407).

**How to avoid:** Two defences. Set every category except `Workflow` to `NONE` so Apex and database lines cannot crowd out flow lines. And check the size before trusting the content:

```soql
SELECT Id, Operation, Location, Status, LogLength, DurationMilliseconds, StartTime
FROM ApexLog
WHERE StartTime = LAST_N_DAYS:1
ORDER BY LogLength DESC
```

A `LogLength` at or near 20,971,520 means the log was repaired and you cannot reason from absence.

---

## Gotcha 9: The Flow Error Email Goes to Whoever Last Saved the Flow

**What happens:** A flow has been failing in production for weeks. Nobody saw an email. The admin concludes error emails are switched off, and builds a custom logging path to replace a mechanism that was working the whole time.

**When it occurs:** On any org that has not changed the default. `enableFlowUseApexExceptionEmail` "indicates whether process and flow error emails are sent to: the user who last modified the process or flow (`false`), the addresses set on the Apex Exception Email page in Setup (`true`). **By default, the value is `false`.** Corresponds to the *Send Process or Flow Error Email to* field on the Process Automation Settings page in Setup" (`api_meta.txt` L116961–L116967). The last person to save the flow is frequently a departed consultant, a partner user, or an admin who touched it once during a migration.

**How to avoid:** Before building anything, ask who last modified the flow and check that person's inbox — the diagnostic you need may already exist. Then decide deliberately whether to flip the setting. It is org-wide and affects every flow, so `flow/flow-governance` owns that call; `flow/flow-error-monitoring` owns what to do once the emails are landing somewhere useful.

---

## Gotcha 10: A Deployed `flowDefinition` Overrides the `status` Inside Your Flow Files

**What happens:** A developer deploys version 4 of a flow with `<status>Active</status>`, watches the deploy succeed, and then spends a day debugging behaviour that does not match the XML they are reading. Version 3 is what is running.

**When it occurs:** Whenever a `flowDefinition` component is in the deployment. "If you deploy with flow definitions, the active version numbers in the flow definitions override the status fields in the flows. For example, the active version number in the flow definition is version 3, and the latest version of the flow is version 4 with the status field as `Active`. After you deploy your flow, the active version is version 3" (`api_meta.txt` L73929–L73931). The guide itself recommends against the pattern: "in API version 44.0, we recommend upgrading your flows to flow metadata file names without version numbers and discontinue using the `FlowDefinition` object to activate or deactivate a flow" (L73926–L73928).

**How to avoid:** Before reading a single element, establish which version is executing, and search the repo for a `flowDefinitions/` entry for this flow. If one exists, its `activeVersionNumber` is the answer, not the `status` in the flow file. `FlowVersionStatus` values are `Active`, `Draft` ("in the UI, this status appears as Inactive"), `Obsolete`, `InvalidDraft`, `UnderReview` (`api_meta.txt` L68416–L68424) — note that two distinct statuses both display as "Inactive" in the UI, so the UI alone does not tell you which one you have.

---

## Gotcha 11: Generating Too Much Log Volume Disables Your Trace Flags Mid-Investigation

**What happens:** A practitioner sets a trace flag on an integration user to catch an intermittent flow failure, leaves it on over a weekend to catch the next occurrence, and returns to find no logs, no trace flag, and an inability to create a new one.

**When it occurs:** At two separate ceilings. "If you generate more than 1,000 MB of debug logs in a 15-minute window, your trace flags are disabled. We send an email to the users who last modified the trace flags, informing them that they can re-enable the trace flag in 15 minutes." And: "when your org accumulates more than 1,000 MB of debug logs, we prevent users in the org from adding or editing trace flags. To add or edit trace flags so that you can generate more logs after you reach the limit, delete some debug logs" (`apexdev.txt` L38119–L38126). The guide adds a warning that goes further than lost logs: "if the debug log trace flag is enabled on a frequently accessed Apex class or for a user executing requests often, **the request can result in failure**, regardless of the time window and the size of the debug logs" (L38122–L38123).

**How to avoid:** Scope the flag to one user and one short window with a real `ExpirationDate`, never org-wide and never open-ended. Set every category except `Workflow` to `NONE`. If the intermittent case genuinely needs a long window, catch it with a fault path that writes a durable log record instead — that is `flow/fault-handling`'s job and it costs no debug-log volume. Delete the flag when you are done; a forgotten flag is how the next investigation discovers it cannot capture anything.

---

## Gotcha 12: `FLOW_START_INTERVIEWS_BEGIN` Fires Once for the Whole DML, Not Once Per Record

**What happens:** A practitioner reads a log from a 200-record data load, counts one `FLOW_START_INTERVIEWS_BEGIN`, and concludes the flow ran for one record. Or the reverse: sees limit-usage numbers far above what one record could produce and treats them as a leak.

**When it occurs:** On every bulk save into a record-triggered flow. The guide's field list for `FLOW_START_INTERVIEWS_BEGIN` and `FLOW_START_INTERVIEWS_END` is "Requests" (`apexdev.txt` L38856, L38859) — the request count for the whole DML. The per-record events are the singular ones, `FLOW_START_INTERVIEW_BEGIN` / `_END`, "interview ID and flow name" (L38850, L38853). Bulk processing is reported separately again by `FLOW_BULK_ELEMENT_BEGIN` ("interview ID and element type", FINE+), `FLOW_BULK_ELEMENT_DETAIL` ("interview ID, element type, element name, number of records", FINER+) and `FLOW_BULK_ELEMENT_END` ("…number of records, and execution time", FINE+) (L38721–L38729). And `FLOW_BULK_ELEMENT_NOT_SUPPORTED` names the "operation, element name, and entity name that doesn't support bulk operations" at INFO+ (L38746) — that event appearing in a log is a bulkification finding on its own.

**How to avoid:** Read counts, not occurrences. `FLOW_BULK_ELEMENT_DETAIL`'s record count is the number to reason about; the `*_LIMIT_USAGE` events are per transaction, not per record, and each "displays the usage for one of these limits: SOQL queries, SOQL query rows, SOSL queries, DML statements, DML rows, CPU time in ms, heap size in bytes, callouts, email invocations, future calls, jobs in queue, push notifications" (L38795–L38808). If usage climbs once per `FLOW_ELEMENT_BEGIN` for the same element, that is a per-record query and the fix belongs to `flow/flow-bulkification`.
