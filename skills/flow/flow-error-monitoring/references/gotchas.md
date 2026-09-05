# Gotchas — Flow Error Monitoring

Twelve platform behaviours that decide whether a production flow failure becomes visible.
Line citations are into the extracted Summer '26 guides: `api_meta.txt` (Metadata API
Developer Guide), `object_reference.txt` (Object Reference), `apexdev.txt` (Apex Developer
Guide). Anything the guides do not state carries an inline UNVERIFIED marker.

---

## Gotcha 1: The default error-email recipient is the last person to *modify* the flow

**What happens:** Flow and process error emails go to one individual, and it is not the flow
owner, not an admin, and not whoever built it originally. The guide is explicit:
`enableFlowUseApexExceptionEmail` decides whether error emails go to "the user who last
modified the process or flow (`false`)" or "the addresses set on the Apex Exception Email
page in Setup (`true`)", and "by default, the value is `false`" (`api_meta.txt`
L116961–L116967).

**When it occurs:** Always, in any org that has never deployed a `Flow.settings` file. The
symptom appears when the last modifier leaves, changes teams, or filters the mail — the
failures continue and the org hears nothing.

**How to avoid:** Deploy `Flow.settings` with `enableFlowUseApexExceptionEmail` set to `true`
**and** an `apexEmailNotifications` file with the recipients. Setting the flag without the
recipient list points the email at an empty list. Both fences are in
`references/metadata-examples.md` §3 and §4; `flow/flow-governance` owns the policy decision
about which values the org standardises on.

---

## Gotcha 2: `FlowInterviewLog` is the screen-flow log, and zero rows proves nothing

**What happens:** A monitoring report built on `FlowInterviewLog` shows no errors for a
record-triggered flow that is failing every hour. The object "represents the logs of a
**screen flow** interview" (`object_reference.txt` L140059–L140060), as does
`FlowInterviewLogEntry` (L140206–L140208).

**When it occurs:** Any time the flow being monitored is record-triggered, scheduled or
autolaunched — which is most of a production portfolio.

**How to avoid:** Use `FlowInterview` for interview state across all flow types
(`object_reference.txt` L139861) and your own log object for error history. Reserve
`FlowInterviewLog` for the screen-flow slice, and remember its access is gated: "by default,
only users with the View All Data permission can access the logs for flows that are run by
other users" (L140068–L140070), opened up through `FlowInterviewLogOwnerSharingRule`.

> **UNVERIFIED (2026-09-05): `FlowInterviewLog` retention.** A widely repeated "14 days"
> figure does not appear in `object_reference.txt`, `api_meta.txt`, `apexdev.txt` or
> `api_rest.txt`. Do not design a trend report around any retention number you have not
> confirmed against your own org's oldest row.

---

## Gotcha 3: The fault-path Create Records can itself fault, and then nothing is logged

**What happens:** The fault route runs, the log write fails, and the flow ends with no record
anywhere. Nothing in the platform re-routes a fault raised on a fault path.

**When it occurs:** Most often on a required or restricted field. The canonical
`Application_Log__c` template ships `Severity__c` as `<required>true</required>` with a
`<restricted>true</restricted>` value set whose `fullName` values are `DEBUGL`, `INFOL`,
`WARN`, `ERROR`, `FATAL`
(`templates/apex/custom_objects/fields/Severity__c.field-meta.xml`). A flow that assigns
`'Error'` or `'CRITICAL'` writes an invalid restricted value and the insert fails.

**How to avoid:** Keep the sink's schema minimal and its picklists matched to what the flows
actually send; give `Message__c` room (`LongTextArea`, 32768) so a long fault string cannot
overflow it. `references/metadata-examples.md` §2 is the field set this skill assumes, and
the checker treats a log object with no `LongTextArea`/`TextArea` field as an ERROR.

---

## Gotcha 4: The log write is DML in the failing transaction, and so is the event that follows it

**What happens:** Each fault-path `recordCreates` consumes a DML statement in the same
transaction that is already in trouble. Adding a platform-event publish behind it consumes
another, and whether either survives depends on the event's `publishBehavior`:
`PublishAfterCommit` means "the event message is published only after a transaction commits
successfully. If the transaction fails, the event message isn't published";
`PublishImmediately` means it is "published when the publish call executes, regardless of
whether the transaction succeeds" (`api_meta.txt` L42206–L42227).

**When it occurs:** Bulk saves and data loads, where a single transaction can take the fault
path many times.

**How to avoid:** One sink per fault, not a chain. If the monitoring design must survive a
rollback, that is a `PublishImmediately` platform event, and `apex/debug-and-logging` owns
that design (`Log_Event__e`) — do not invent a second one here.

---

## Gotcha 5: Nothing in the metadata layer carries the alert

**What happens:** The report and the log object deploy cleanly, and no one is ever notified,
because the scheduled subscription that would have mailed the report is not part of the
deployment.

**When it occurs:** Every promotion between orgs, and every sandbox refresh.

**How to avoid:** Treat the subscription as manual configuration with an owner and a
checklist line, not as code. Page on a record-level trigger — a flow or an Apex trigger on
the error-log object — not on a report or dashboard.

> **UNVERIFIED (2026-09-05): report subscription and dashboard refresh cadence.**
> `api_meta.txt` has no metadata type for a report subscription, and states no dashboard
> refresh interval. Both are documented only on help.salesforce.com, which cannot be fetched.
> The negative — that they are not in the metadata layer — is what this gotcha rests on.

---

## Gotcha 6: `FlowVersionView` returns nothing at all unless you filter it

**What happens:** A version-drift audit written as `SELECT ... FROM FlowVersionView WHERE
Status = 'Active'` returns an empty result set and the org looks perfectly clean.

**When it occurs:** On the first attempt, every time. "A query must be filtered by
`DurableId` or `FlowDefinitionViewId` to get results" (`object_reference.txt`
L145295–L145296).

**How to avoid:** Drive the audit from `FlowDefinitionView`, which has no such restriction
(`object_reference.txt` L139268–L139274), using `IsOutOfDate` — "indicates whether the active
flow version is the latest version of the flow definition" (L139405–L139412) — then query
`FlowVersionView` per definition with `FlowDefinitionViewId`. Both queries are in
`references/metadata-examples.md` §5b.

---

## Gotcha 7: Your monitoring flow deploys to production inactive

**What happens:** The instrumented flow deploys successfully, the checker passes, and no
fault path ever runs because the flow is not active.

**When it occurs:** On the first production deploy of any org that has not changed the
default. `enableFlowDeployAsActiveEnabled`: "when the value is `false`, all processes and
flows are deployed as inactive… The default value is `false` for production orgs and is
`true` for non-production orgs such as scratch, sandbox, and developer orgs"
(`api_meta.txt` L116877–L116886). Turning it on has a cost the same paragraph states:
"deploying an active process or flow in a production org causes your Apex tests to run. If
Apex tests don't launch your org's required percentage of active processes and autolaunched
flows, the deployment is rolled back."

**How to avoid:** Make "is it active in the target org?" a verification step, not an
assumption — `SELECT ApiName, IsActive, IsOutOfDate FROM FlowDefinitionView WHERE ApiName =
'…'`. A monitoring deploy that reports success and leaves the flow inactive is the worst of
both outcomes: no coverage, and a false record of coverage.

---

## Gotcha 8: Deploying `apexEmailNotifications` deletes every recipient not in the file

**What happens:** A flow-side deploy silently removes the Apex on-call address from the org's
error-notification roster. "Deploying ApexEmailNotifications deletes all previous
notifications in the org" — the guide's own worked example shows `test1@example.com`
disappearing because it was absent from the deployed list (`api_meta.txt` L22458–L22466).

**When it occurs:** Any deploy that includes the file, from any team. There is no partial
update: the type "isn't supported in `destructiveChanges.xml`. To delete specific
ApexEmailNotification items, deploy a new ApexEmailNotifications without those items"
(L22468–L22470).

**How to avoid:** One version-controlled file, one owner, and a review rule that any change
to it is reviewed by both the flow and Apex sides. `apex/debug-and-logging` writes to the
same file.

---

## Gotcha 9: `Expired` is a valid interview status on one object and not the other

**What happens:** A paused-interview backlog query filtering `InterviewStatus = 'Expired'`
against `FlowInterview` fails or returns nothing, because the field is a **restricted**
picklist and `Expired` is not one of its values.

**When it occurs:** Whenever someone reads the two objects' status lists as interchangeable.
`FlowInterview.InterviewStatus` documents `Completed`, `Error`, `Paused`, `Running`,
`VersionPaused` (`object_reference.txt` L139956–L139971).
`FlowInterviewLog.InterviewStatus` documents those plus `Autosaved` (API 62.0+, L140158) and
`Expired` (API 62.0+, L140161).

**How to avoid:** Use `('Paused', 'VersionPaused', 'Error')` on `FlowInterview` and treat
`VersionPaused` as its own class of finding — "this flow version is paused. No more records
are processed until the flow is resumed" (L139968–L139970) usually means a version was
deactivated underneath live interviews, not that a flow failed.

---

## Gotcha 10: You can delete a paused interview but you cannot annotate one

**What happens:** A triage process that wants to mark interviews as "reviewed" has nowhere to
write. `FlowInterview`'s Supported Calls are `delete()`, `describeLayout()`,
`describeSObjects()`, `getDeleted()`, `getUpdated()`, `query()` and `retrieve()`
(`object_reference.txt` L139864–L139869) — no `create()`, no `update()` — even though the
`Error` field's own properties line reads `Create, Nillable, Update` (L139907–L139913).

**When it occurs:** As soon as the backlog is large enough to need state.

**How to avoid:** Keep triage state on your own record, keyed by `FlowInterview.Guid`, and
treat the interview itself as read-then-delete. Deletion is also permissioned: "to delete a
flow interview, you must have the 'Manage Flow' user permission. All other calls require the
'Run Flows' user permission or the Flow User field enabled on the user detail page"
(L139869–L139871) — so the ops role that clears the backlog needs Manage Flow, which is not a
small grant.

---

## Gotcha 11: `PauseLabel` is user-entered, so it is null for every scheduled path

**What happens:** A backlog report grouped by "why paused" is empty for the majority of rows.
`PauseLabel` holds "information about why the interview was paused. **This string is entered
by the user who paused the flow interview.** The label is Why Paused"
(`object_reference.txt` L140013–L140019).

**When it occurs:** Any interview paused by a scheduled path or a wait rather than by a
person clicking Pause on a screen — which is every record-triggered flow with a
`scheduledPaths` entry.

**How to avoid:** Group the backlog by `InterviewLabel` and `CurrentElement` — "the flow
element at which the interview is paused" (L139891) — and make `interviewLabel` carry the
record Id at design time (`api_meta.txt` L68156–L68160). `WasPausedFromScreen` tells you
which rows could have a `PauseLabel` at all.

---

## Gotcha 12: A `FlowTest` cannot assert on the log row it caused

**What happens:** A team writes a `FlowTest`, sees it pass, and believes the fault-path log
write is covered. It is not. `FlowTestPoint.elementApiName` has exactly two possible values,
`Start` and `Finish` (`api_meta.txt` L74141–L74148), and no `FlowTest` field queries records
created by the flow under test.

**When it occurs:** Every time the monitoring path is "tested" without an Apex wrapper.

**How to avoid:** Use `FlowTest` with the `HasError` operator (API 64.0 and later,
`api_meta.txt` L74203) to prove the *fault happened*, and an Apex test or a manual scratch-org
save to prove the *row was written*. Two artefacts, two claims.

---

## Gotcha 13: A subflow element has no `faultConnector`, so the parent cannot catch it there

**What happens:** A fault inside a called subflow does not route to a fault path on the
parent's Subflow element, because that element has none to route to. `FlowSubflow`'s field
table lists `connector`, `flowName`, `inputAssignments`, `outputAssignments` and
`storeOutputAutomatically` — and **no `faultConnector`** (`api_meta.txt` L72625–L72660).
Every other fault-capable node type has one: `FlowRecordCreate` (L70965),
`FlowRecordDelete` (L71046), `FlowRecordLookup` (L71120), `FlowRecordUpdate` (L71283),
`FlowActionCall` (L68476), `FlowApexPluginCall` (L69688), `FlowWait` (L72993).

**When it occurs:** Any portfolio that factors shared logic into subflows — which is the
portfolio most likely to have a monitoring convention in the first place.

**How to avoid:** Put the fault-path log write **inside** the subflow, on the failing element
itself, and let the subflow be responsible for its own sink. A monitoring convention that
only instruments top-level flows leaves every subflow silent. The checker reflects this: it
counts `subflows` as a connectable node but never as fault-capable.

> **UNVERIFIED (2026-09-05): what the parent flow does next.** Whether the parent halts,
> continues at the subflow's `connector`, or surfaces an unhandled fault is not stated in
> `api_meta.txt`, `apexdev.txt` or `object_reference.txt`. Test the exact combination you
> depend on rather than assuming propagation.

---

## Gotcha 14: One bulk save produces one interview per record, and one alert per interview

**What happens:** A 200-record data load that hits the same fault takes the fault path 200
times and sends 200 emails, burying the signal in the noise it just created.

**When it occurs:** Data loads, integration writes, and scheduled paths. Scheduled paths make
the batch size explicit: `FlowScheduledPath.maxBatchSize` is "the maximum number of scheduled
path interviews to execute in a single batch, from 1 to 200. Default is 200"
(`api_meta.txt` L71397–L71400).

**How to avoid:** Alert on the *log record*, not on the fault. The fault path writes a row
unconditionally; a separate scheduled or record-triggered flow on the log object applies the
threshold — "N rows for the same `Source__c` in M minutes" — and sends one message.
Inline `emailSimple` on the fault path is acceptable only where the flow is known to be
single-record. `flow/flow-error-notification-patterns` owns suppressing an already-noisy
channel; this skill's answer is to put the aggregation between the fault and the channel.
