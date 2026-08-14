# Gotchas — Flow Orchestration Patterns

Non-obvious Flow Orchestration behaviors that bite real multi-stage
processes.

---

## Gotcha 1: No direct cancel UI for in-flight orchestrations

**What happens.** Admin needs to terminate an orchestration that's
been running for days. Looks for a Cancel button. Doesn't exist.

**When it occurs.** Source record created in error, business
process abandoned mid-flight, employee terminated mid-onboarding.

**How to avoid.** Design the cancel pathway in from the start.
Pattern: a `Cancelled__c` flag on the source record + every
step / evaluation flow checks the flag and short-circuits. The
orchestration drains cleanly through remaining stages.

---

## Gotcha 2: Formula-derived assignee returning null = stuck step

**What happens.** Formula evaluates to null (no manager, inactive
user, lookup field blank). Work Item is created without an
assignee. Nobody can open it. Orchestration is stuck.

**When it occurs.** Formulas like `Owner.ManagerId` against records
whose owner has no manager. Records imported from sandbox where
some User references didn't migrate.

**How to avoid.** Fallback logic in the formula that resolves to a
default-approver group or queue. Test the formula's null case
explicitly before deployment.

---

## Gotcha 3: Modifying a screen-flow definition referenced by in-flight Work Items

**What happens.** A screen flow used as an interactive step is
modified — added input variables, renamed fields, reordered
screens. When a user opens an in-flight Work Item created against
the previous version, the resume can produce confused UI or fail
outright.

**When it occurs.** Long-running orchestrations + active flow
development.

**How to avoid.** Treat screen flows used by orchestrations as
contracts. Schema changes (input variables, output variables) need
backwards-compatible migrations, not in-place edits. Or accept that
in-flight Work Items may need admin intervention after a flow
upgrade.

---

## Gotcha 4: Inactive user as assignee — Work Item is created but unopenable

**What happens.** Step assigned to a specific user; that user is
later deactivated. Work Item exists, assigned to the deactivated
user, can't be opened. Orchestration stuck.

**When it occurs.** Long-running orchestrations spanning user
turnover.

**How to avoid.**
- Prefer queue-based assignment over specific-user assignment for
  any step that might span weeks.
- Add a periodic "stuck Work Item" report that flags items assigned
  to inactive users for admin reassignment.

---

## Gotcha 5: Stages run sequentially; steps within a stage run in parallel

**What happens.** Admin builds an orchestration with three steps in
stage 1 expecting them to run in order. Steps run in parallel,
producing race conditions or out-of-order side effects.

**When it occurs.** Inferring sequencing from visual top-to-bottom
order in the orchestration designer.

**How to avoid.** If steps must run in a specific order, put them
in separate stages. Within-stage parallelism is the default and
intentional.

---

## Gotcha 6: Background-step errors don't surface to users

**What happens.** A background step (autolaunched flow) faults.
The orchestration considers the step "completed" and moves on. No
user is notified. The downstream effect (the integration call that
didn't fire, the field that wasn't updated) is invisible.

**When it occurs.** Default fault handling in background-step flows.

**How to avoid.** Apply `flow/flow-error-notification-patterns` to
every background step. Fault paths must publish to
`Flow_Error_Event__e` or insert into `Flow_Error_Log__c`. Admin
notification cadence catches these errors before they accumulate.

---

## Gotcha 7: Evaluation flows that throw exceptions hold the orchestration

**What happens.** Stage-exit evaluation flow has an unhandled fault
on a Get Records or Action call. The orchestration doesn't
transition to the next stage; it holds at the exit. Admin doesn't
know it's held unless they check.

**When it occurs.** Evaluation flows that do DML or callouts
without fault paths.

**How to avoid.** Evaluation flows should be defensive — wrap
critical elements in fault paths that return a sensible default
(usually true to let the stage complete, or false to hold pending
admin review).

---

## Gotcha 8: Do not print "in-flight runs stay on the starting version" as platform law

**What happens.** Help, release notes, Trailhead, and the Object
Reference do not state that a running orchestration continues on
the version it started on. `FlowOrchestrationInstance.FlowDefinitionVersionName`
exists and can be **null for every run in an org**, so it cannot
prove which version a run is executing.

**When it occurs.** Someone wants a slide-ready sentence after a
deploy that changed Decision rules while a run was sitting in an
earlier stage.

**How to avoid.** Treat version pinning as **unobserved until you
test it in the target org**. One org has shown a four-day-old run
finish on the **old** Decision rules after a newer version was
activated — that is a method ("start a run, activate a version that
changes a Decision, complete the waiting work item, see which
rules fired"), not a platform guarantee. Do not tell a customer
their in-flight deals "survive deployments" unless you have run
that test on their org. If you must change an orchestration that
has open runs, document the mismatch for support either way.

---

## Gotcha 9: Work Items don't appear in Salesforce mobile by default

**What happens.** Users on mobile don't see assigned Work Items in
the standard mobile UI. Adoption suffers when the workflow assumes
mobile users will pick up items quickly.

**When it occurs.** Service / field / mobile-first user populations.

**How to avoid.** Configure the Lightning Page that displays Work
Items, ensure it's added to the mobile experience. Test on the
target user's actual device. Or push interactive-step notifications
to a separate channel (email with deep link, Slack DM, push
notification via custom Apex action).

---

## Gotcha 10: Evaluation-flow output must be named exactly `isOrchestrationConditionMet`

**What happens.** The evaluation flow returns a Boolean under any
other variable name. The orchestration **discards it silently**.
The stage never exits, or always exits, and nothing in the debug
log says "wrong output name".

**When it occurs.** Authoring an autolaunched flow that "returns a
boolean" without reading the evaluation-flow contract.

**How to avoid.** The output variable name is a reserved contract,
not a style choice. Name it `isOrchestrationConditionMet`. Help:
[Considerations for Evaluation Flows](https://help.salesforce.com/s/articleView?id=platform.orchestrator_considerations_evaluation_flows.htm&type=5).

---

## Gotcha 11: Dotted step-output references are rejected

**What happens.** A later step or condition writes
`Evaluate_Deal_Risk.financeReviewRequired`. Deploy (or the
expression builder) fails with `"Evaluate_Deal_Risk.financeReviewRequired"
element doesn't exist`.

**When it occurs.** Treating a background step like a Flow element
whose outputs are in scope for later elements.

**How to avoid.** Capture the step output into an **orchestration
variable** with `<assignToReference>` first, then read the
variable. A dotted `StepName.output` path is not a legal
orchestration reference.

---

## Gotcha 12: ERROR-resume and SUSPEND-resume are different operations

**What happens.** An admin treats "Resume" as one button. Salesforce's
own *"Resume errored orchestration run?"* dialog says: the errored
step **restarts**, not-started steps run, and steps **completed
before the error are not run again**. Suspend-resume is a different
path: suspended steps are **discontinued**; a background step
restarts and an interactive step gets a **replacement** work item.

**When it occurs.** Mixing an error screenshot with suspend-resume
speaker notes, or telling ops "just hit Resume" without saying
which pause state the run is in.

**How to avoid.** Teach two runbooks. Error-resume: fix the called
flow or the frozen assignee, then Resume — completed work stands.
Suspend-resume: expect discontinued steps and new work items, not
a continuation of the paused ones. Do not print suspend-resume
rules on an error-resume slide.

---

## Gotcha 13: Recoverable errors have a 14-day window and a short list

**What happens.** A run sits in Error. Ops assumes they can Resume
whenever. Recoverable errors can be resumed **within 14 days**, and
only for two cases: the flow a step called errored, **or** the step
has a frozen or inactive assignee. Everything else is
non-recoverable: an error outside the called flows, an error in a
MuleSoft step's action, or an **assignee reference that does not
resolve**. The last one is the trap — `$Record.OwnerId` can deploy
clean and then kill the run with **Debug and no Resume**. Observed
failure signature: the *preceding* stage is marked Discontinued,
the target stage instance is **never created**.

**When it occurs.** Formula or `elementReference` assignees;
deactivated users; MuleSoft steps; anything that fails outside the
called autolaunched/screen flow.

**How to avoid.** Prefer queue or literal-username assignees that
exist and are active at deploy time. Treat unresolved
`elementReference` assignees as **non-recoverable** until proven
otherwise in that org. Help: [Orchestration Run](https://help.salesforce.com/s/articleView?id=platform.orchestrator_orchestration_run.htm&type=5).
Summer '24 release notes (recoverable within 14 days).

---

## Gotcha 14: Interactive steps need `ActionInput__RecordId`, not just `$Record`

**What happens.** Deploy fails with `field integrity exception:
unknown (A context record is required for interactive steps.)`
even though the orchestration is record-triggered and `$Record` is
in scope.

**When it occurs.** Every interactive step that does not pass the
reserved input. Being record-triggered is **not** sufficient —
`$Record` is trigger context, not work-item context.

**How to avoid.** On every `InteractiveStep`, set:

```xml
<inputParameters>
    <name>ActionInput__RecordId</name>
    <value>
        <elementReference>$Record.Id</elementReference>
    </value>
</inputParameters>
```

That reserved name populates `FlowOrchestrationWorkItem.RelatedRecordId`
(UI label: Context Record ID) so the Work Guide can pin the item to
the record. Other names (`ContextRecordId`, `relatedRecordId`) are
rejected. Do **not** add it to background steps. Observed on API
67.0; not a documented Metadata field — test the deploy in the
target org.

---

## Gotcha 15: Interactive assignees are usernames, not User Ids

**What happens.** `<stringValue>005…</stringValue>` fails deploy:
*"The assigned user 005… doesn't exist or is inactive."* A
username string deploys. Salesforce resolves the username **at
deploy time** and checks `IsActive`. A 15- or 18-character User Id
is rejected. `$Record.Owner.ManagerId` can deploy clean and throw
`Invalid Resource reference` at **run time**.

**When it occurs.** Copying Ids from a query into the XML; using
two-level owner.manager traversal; porting an orchestration
between orgs (usernames are org-specific).

**How to avoid.** Assign a queue, or a literal username that is
active in **this** org. Do not generalise "two-level traversal is
unsupported" — Salesforce publishes no such limit; say what the
org did and test yours. A deactivated demo/service user breaks the
next deploy, not just the next run.

---

## Gotcha 16: A stage that exits early discontinues its own open steps

**What happens.** Stage-exit logic fires while an interactive step
in that stage is still open. The work item is **discontinued** and
**vanishes with no notification** to the assignee.

**When it occurs.** Evaluation-flow or record-condition exits that
do not wait for every in-stage step; "or" exits on a wait stage;
anyone still holding a Work Item when the stage is allowed to
finish.

**How to avoid.** If humans must be told the work is gone, notify
them yourself — the platform will not. Design stage-exit so it
cannot fire while a required interactive step is still In Progress,
or accept silent discontinue as the product behaviour. Object
Reference: `FlowOrchestrationStepInstance` status values.
