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

## Gotcha 8: Orchestration metadata changes don't migrate in-flight orchestrations

**What happens.** Admin updates the orchestration definition (adds
a stage, removes a step, changes assignee logic). In-flight
orchestrations continue running against their original version.
The new behavior only applies to orchestrations started after the
deploy.

**When it occurs.** Iterating on orchestration design while
orchestrations are running.

**How to avoid.** Plan metadata changes during a quiet period when
no orchestrations are mid-flight. Or accept that mid-flight
orchestrations will continue with old behavior; document the
mismatch for support.

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
