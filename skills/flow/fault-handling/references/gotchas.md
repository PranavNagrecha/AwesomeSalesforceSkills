# Flow Fault Handling — Gotchas

Line citations are `grep -n` positions in the Summer '26 / v62-era plain-text extracts of
the Metadata API Developer Guide (`api_meta.txt`), Apex Developer Guide (`apexdev.txt`),
Object Reference (`object_reference.txt`) and Lightning Web Components Developer Guide
(`lwc_guide.txt`).

## 1. Subflow elements have no fault connector at all

**What happens.** You are told to "add a fault connector to every DML, Action and Subflow
element", you go looking for it on the Subflow, and it is not there. Generated XML that
emits `<faultConnector>` inside `<subflows>` fails to deploy.

**When it occurs.** Any time a parent flow calls a child flow and you try to handle the
child's failure at the call site.

**How to avoid.** `FlowSubflow`'s complete field list is `connector`, `flowName`,
`inputAssignments`, `outputAssignments`, `storeOutputAutomatically` (`api_meta.txt`
L72625–72660) — no `faultConnector`. Handle failure **inside** the child, on the child's
own fault-capable elements, and return the outcome to the parent through a
`FlowSubflowOutputAssignment` the parent branches on. See `flow/subflows-and-reusability`
for the contract shape; the fault-handling consequence is that the child owns its errors
and the parent reads a result, never an exception.

## 2. `faultConnector` on an orchestration stage exists in the schema and does nothing

**What happens.** `FlowOrchestratedStage` accepts a `faultConnector`. It deploys. It never
fires.

**When it occurs.** Orchestrations authored by hand or generated from a record-triggered
flow's shape.

**How to avoid.** The guide's description of that field is the single word "Not used."
(`api_meta.txt` L70803). Stage-level failure in an orchestration is handled by stage exit
conditions (`exitConditions`, `exitConditionLogic`) and by the fault paths inside the
flows the steps invoke — not by a connector on the stage.

## 3. `Roll Back Records` is screen-flow-only, and there is no autolaunched equivalent

**What happens.** You design a "log then roll back" fault path for a record-triggered or
autolaunched flow, and the element is not available.

**When it occurs.** Whenever the fault design was drafted against a screen flow and reused
for background automation.

**How to avoid.** `FlowRecordRollback` "Rolls back the current transaction and cancels its
pending record changes… **Available only in screen flows.**" (`api_meta.txt`
L71253–L71256, API 52.0 and later). In an autolaunched or record-triggered flow the
equivalent of "roll back" is *not handling the fault at all* — an unhandled fault ends the
interview and the transaction never reaches step 19, "Commits all DML operations to the
database" (`apexdev.txt` L15478). Rollback there is the default, not an element.

## 4. A fault path that writes a record can fault, and then nothing is left

**What happens.** The fault path logs to `Application_Log__c`, that Create fails too, and
now you have neither the business change nor the diagnostic.

**When it occurs.** Most often when the original failure was a governor limit. The DML and
SOQL budgets are per transaction — 150 DML statements and 100 SOQL queries synchronously
(`apexdev.txt` L19554, L19544) — and they do not refill for the error handler. It also
happens when the log object's own validation rules or FLS reject the write.

**How to avoid.** Give every DML element on a fault path its own `faultConnector`, and
make the last hop something that does not need the transaction to commit. Flow 2 in
`references/metadata-examples.md` routes the failing log write to a platform event for
exactly this reason.

## 5. The error notification your fault path sends is the first thing rollback destroys

**What happens.** The fault path sends an email alert, the transaction rolls back, and no
email arrives — so the failure is invisible on the very run that mattered.

**When it occurs.** Any fault path in a record-triggered or autolaunched flow that ends
without suppressing the failure.

**How to avoid.** Sending email is post-commit work: the save order commits all DML at
step 19 and only then "executes post-commit logic… Sending email" at step 20
(`apexdev.txt` L15478–L15487). A rolled-back transaction never reaches step 19. A platform
event does survive — but **only when the event's `publishBehavior` is
`PublishImmediately`**, which is "published when the publish call executes, regardless of
whether the transaction succeeds", against `PublishAfterCommit`, where "if the transaction
fails, the event message isn't published" (`api_meta.txt` L42206–L42229, API 46.0 and
later). The default when the field is omitted is `PublishImmediately`. `publishBehavior`
is a field on the *event definition* in `CustomObject` metadata, not a Flow setting — an
alert event someone marked `PublishAfterCommit` is silent in exactly the case you built it
for.

## 6. Flow error emails go to whoever last modified the flow, not to a monitored mailbox

**What happens.** A production flow fails nightly for weeks. Nobody sees it, because the
error emails are going to the consultant who last saved the flow.

**When it occurs.** By default, in every org, immediately after any release in which
someone edited the flow.

**How to avoid.** `FlowSettings.enableFlowUseApexExceptionEmail` decides the recipient:
`false` — the default — sends process and flow error emails to "the user who last modified
the process or flow"; `true` sends them to "the addresses set on the Apex Exception Email
page in Setup" (`api_meta.txt` L116961–L116972). It surfaces as *Send Process or Flow
Error Email to* on the Process Automation Settings page. Those Apex Exception Email
addresses "can also receive process or flow error emails" (`apexdev.txt` L39598–L39601).
Set it to `true`, point it at a distribution list, and re-check it after every deploy that
touches `FlowSettings`. Note that this is a different setting from `FlowStart.flowRunAsUser`
= `DefaultWorkflowUser`, which controls who the flow *runs as* (`api_meta.txt` L72404+).

## 7. `FlowInterviewLog` only logs screen flows — it is not where background faults land

**What happens.** A runbook says "check FlowInterviewLog for the failed interview". The
flow is autolaunched or record-triggered, and the query returns nothing, so the failure
looks like it never happened.

**When it occurs.** Triaging any non-screen flow.

**How to avoid.** `FlowInterviewLog` "Represents the logs of a **screen flow** interview"
and `FlowInterviewLogEntry` "Represents the log of a specific element that's executed by a
**screen flow** interview" (`object_reference.txt` L140058, L140206; both API 49.0 and
later). Neither carries the fault message — the parent's fields are `FlowDeveloperName`,
`FlowInterviewGuid`, `FlowLabel`, `FlowNamespace`, `FlowVersionNumber`, and the entry's
are element name/label, timestamps and `LogEntryType`. For background flows the evidence
is whatever your own fault path wrote, plus the error email. That asymmetry is the
argument for writing an `Application_Log__c` row rather than relying on the platform.

## 8. `$Flow.FaultMessage` is set *by taking the fault connector*, so it is empty everywhere else

**What happens.** An Assignment on the success path copies `{!$Flow.FaultMessage}` into a
log field "just in case", and every log row has a blank message.

**When it occurs.** When fault paths are merged into a shared tail that is also reachable
from a non-fault branch, or when a decision on the happy path tries to test whether an
error occurred.

**How to avoid.** The one place these sources state the mechanism is the local-action page
of the LWC guide: when the work fails "the flow takes the local action's fault connector
**and sets** the error message to `$Flow.FaultMessage`" (`lwc_guide.txt` L8839). Capture it
in the *first* element of the fault branch and pass that variable onward. Do not merge a
fault tail with a non-fault path unless every element after the merge reads the captured
variable, never the global. To ask "did an error happen" outside a fault branch, use the
`HasError` comparison operator instead (`api_meta.txt` L70087, API 64.0 and later).

## 9. Custom Error is not a fault handler — it is a rollback, and the metadata says its connector is required

**What happens.** Two separate surprises. First, an agent uses a Custom Error element as a
generic "show the user an error" device on a screen flow's fault path and the whole
transaction disappears. Second, hand-written `customErrors` XML with no `<connector>`
child does not match the documented schema.

**When it occurs.** Whenever Custom Error is treated as the declarative equivalent of a
catch block.

**How to avoid.** `FlowCustomError` "Defines a custom error element to **roll back** a
change that triggered a flow and inform the user exactly what caused the error"
(`api_meta.txt` L70006–L70007). Its `connector` field is marked `Required` (L70013), even
though Flow Builder draws the element as terminal. `isFieldError` is also `Required` and
picks the UI: `true` "displays inline on a field" (with `fieldSelection` naming it),
`false` "displays in a window on a record page", default `false` (L70034–L70040).
*UNVERIFIED (2026-09-05): the guide states no API-version floor and no flow-type
restriction for `FlowCustomError`; the "roll back a change that triggered a flow" wording
implies record-triggered use but does not exclude other types. Verify availability in your
org's Flow Builder before promising it in a screen flow.*

## 10. A before-save flow hands its values to validation rules it cannot catch

**What happens.** A before-save flow derives a field, a validation rule rejects the derived
value, and the save fails with an error the flow author cannot see a fault path for.

**When it occurs.** Every time a before-save flow writes to `$Record` and any validation
rule reads that field.

**How to avoid.** The order is fixed: record-triggered flows configured to run before the
save execute at step 3, before triggers at step 4, and "most system validation steps…
and any custom validation rules" at step 5 (`apexdev.txt` L15440–L15442). The flow finishes
before the rule runs, so there is nothing to attach a fault connector to. If the flow's own
logic can determine the value is invalid, block the save with a Custom Error element inside
the flow rather than letting a validation rule do it downstream — you control the message
and you keep the diagnosis in one place.

## 11. Invocable Apex cannot take a non-list input, so "not list-safe" is the wrong diagnosis

**What happens.** A review says "this invocable Apex takes a single input, so it fires once
per interview — change it to a list". The signature it describes does not compile.

**When it occurs.** In generated bulk-safety advice, and in older guidance carried forward.

**How to avoid.** "There can be at most one input parameter and its data type must be…
a list of a primitive data type… a list of an sObject type… a list of the generic sObject
type… a list of a user-defined type" (`apexdev.txt` L5432–L5438). Lists are mandatory. The
real bulk hazard is the *correspondence* rule: "For a correct bulkification implementation,
the Inputs and Outputs must match on both the size and the order… the i-th Output entry
must correspond to the i-th Input entry. Matching entries are required for data correctness
when your action is in bulkified execution, such as when an apex action is used in a record
trigger flow" (`apexdev.txt` L5456–L5459). An action that filters its inputs and returns a
shorter list silently hands interview *n* the result belonging to interview *n+k* — a data
corruption bug that no fault connector fires on, because nothing threw.

## 12. Shared transactions still share governor limits

**What happens.** A flow that works fine on UI edits fails under a data load, and the fault
message names a limit rather than a business rule.

**When it occurs.** When Apex, other flows and this flow run inside one save.

**How to avoid.** The synchronous transaction budget is 100 SOQL queries and 150 DML
statements (`apexdev.txt` L19544, L19554); asynchronously it is 200 SOQL and still 150 DML.
Those are transaction-wide, not per-flow. Count the SOQL and DML your flow issues per
interview, multiply by the expected batch cardinality, and subtract what the triggers on
the same object already spend. See `flow/flow-bulkification` for the counting method; the
fault-handling consequence is that a missing fault connector converts a limit breach on
one record into a rolled-back batch.
