---
name: dynamic-sharing-recalculation
description: "Force or orchestrate sharing recalculation after bulk data loads, rule changes, or user/role reorgs so row access catches up with policy. NOT for designing new sharing rules — use sharing-selection tree — use data/sharing-recalculation-performance."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "after data load users cant see records"
  - "added sharing rule recalculation is still running"
  - "role hierarchy change access not updated"
  - "recalculate sharing apex"
tags:
  - sharing
  - recalculation
  - bulk
inputs:
  - "Which driving event triggered the drift"
  - "estimated record volume"
outputs:
  - "Recalc orchestration plan (defer rules, enable in batches, verify)"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Dynamic Sharing Recalculation

Sharing recalculation is the asynchronous platform process that rebuilds `__Share`
rows after something changes the inputs to the record-access model. It runs
without being asked, takes as long as it takes, and reports only through
**Setup → Background Jobs** and a completion email. In a small org it is
invisible. Above roughly a million rows, or a few hundred users, it becomes the
critical path of every migration and every reorg.

This skill covers the orchestration: when recalculation fires, how to suppress it
during a load, how to trigger it deliberately afterwards, and how to prove access
is correct before reopening the org.

It does **not** cover designing the sharing model itself. Read
[`standards/decision-trees/sharing-selection.md`](../../../standards/decision-trees/sharing-selection.md)
for that, and cite the branch that sent you here.

---

## Before Starting

1. **Name the driving event.** Recalculation is a consequence, never a cause.
   Which of these is happening: a bulk data load, an org-wide default change, a
   sharing rule add/edit/delete, a role hierarchy change, a territory change, a
   group membership change, or a mass owner reassignment? The answer determines
   both the blast radius and whether deferral is even the right tool.

2. **Confirm Defer Sharing Calculations is available in production.** The Security
   Guide's availability is conditional: "**If enabled in your org**, you can
   temporarily defer sharing rule calculations." Verify the Setup page renders,
   in production, before the plan depends on it. If it is absent, the enablement
   is a Salesforce Support case and a schedule dependency.

3. **Inventory Apex sharing recalculation classes.** "When sharing is
   recalculated, Salesforce also runs all Apex sharing recalculations." Walk the
   custom objects and check the **Apex Sharing Recalculation** related list.
   Their runtime belongs in the window estimate.

4. **Establish the verification set.** One representative user per persona, one
   record each must see and one each must not. Without this you have no exit
   criterion other than "the job finished," which is not the same thing.

---

## Core Concepts

### What fires recalculation automatically

From the Security Guide, sharing rule recalculation happens on its own after:

- adding or removing individual users from a group, role, or territory
- changing which role a particular role reports to
- changing which territory a particular territory is subordinate to
- adding or removing a group from within another group
- updating org-wide defaults or sharing rules

A role reorg is therefore not one recalculation. It is one per user move, unless
you defer.

### The Account family cascades

> "If sharing rules are recalculated for accounts, cases, contacts, or
> opportunities, sharing rules are also recalculated for the other three objects.
> This behavior occurs because cases, contacts, and opportunities are child objects
> of accounts."

Size the window for four objects when you touch any one of them. Conversely,
trigger recalculation on one to cover all four.

### Share locks

While a recalculation runs you cannot modify org-wide defaults for any object, and
while an OWD recalculation runs you cannot modify sharing rules. You *can* change
OWDs and sharing rules for unrelated objects. On the Account family the lock is
tighter: an OWD update on an account or its child objects disables further OWD and
sharing rule updates on all four.

### Deferral covers exactly two processes

**Setup → Defer Sharing Calculations** suspends:

- group membership calculation
- sharing rule calculation

It does **not** suspend Apex triggers that write `__Share` rows, Flows that change
ownership, or Apex sharing recalculation classes you invoke yourself. Those are
separate switches — see
[`templates/apex/TriggerControl.cls`](../../../templates/apex/TriggerControl.cls).

### Resume is not recalculate

> "After this work is completed, you must resume sharing rule calculations and
> manually initiate a full sharing rule recalculation to prevent errors."

And the ordering is forced: "The Recalculate button is disabled when group
membership or sharing rule calculations are deferred." Resume first, recalculate
second.

### Observability surface

| Signal | Where | What it tells you |
|---|---|---|
| Platform recalculation progress | Setup → Background Jobs | Subtypes `Account — Parent Access Grant`, `Account — Extra Parent Access Removal`, `Object — Access Cleanup` |
| Apex recalculation progress | Setup → Apex Jobs | Registered `Database.Batchable` sharing classes |
| Completion | Email notification | Sent when recalculation completes for all affected objects |
| History | Setup → View Setup Audit Trail | Recent sharing operations |
| Ground truth | `SELECT ... FROM UserRecordAccess` | Whether a specific user can read a specific record right now |

---

## Common Patterns

### Pattern A — initial load into a greenfield org

Sequence the model, per the LDV guide: users into roles → record data with owners →
public groups and queues → sharing rules **one at a time** → set the restrictive
OWD last. Optionally hold the OWD at Public Read/Write during the load "to avoid
sharing calculation overhead," accepting that no `__Share` row can be inserted
while it is there.

### Pattern B — repeated loads into a live org

Defer both calculations for the duration of the load campaign, resume, recalculate
manually, verify. One rebuild instead of N overlapping partial rebuilds. Full
runbook in [`references/examples.md`](references/examples.md), Example 2.

### Pattern C — role or territory reorg

Defer, apply the hierarchy change, resume, recalculate on Account (which covers
Case, Contact, and Opportunity), monitor Background Jobs, verify. Schedule for a
weekend: a 1,200-user reorg without deferral fires 1,200 recalculations.

### Pattern D — targeted repair

When a specific object's access is wrong and nothing is deferred, use
**Setup → Sharing Settings → [object] → Sharing Rules → Recalculate**. The guide
is explicit that this is a repair tool, not routine maintenance: "Manually
recalculate sharing rules only if updates have failed or record access isn't
working as expected."

---

## Decision Guidance

| Situation | Approach |
|---|---|
| Greenfield initial load | Sequence per LDV guide; optionally relax OWD during load |
| Repeated bulk loads into a live org over days | Defer both calculations for the campaign |
| One-off load of a few thousand rows | No deferral; run in a low-activity window |
| Role / territory reorg above ~100 users | Defer, change, resume, recalculate on Account |
| Adding many sharing rules | Add one at a time, letting each finish |
| Access wrong, nothing deferred, rules look correct | Check managed-package licence expiry on criteria fields, then manual recalculate |
| Access wrong for one user on one record | Not a recalculation problem — use `security/record-access-troubleshooting` |
| Custom object OWD change rejected | Apex references its `__Share` entries; the code must change first |

---

## Recommended Workflow

1. **Classify the driving event and compute the blast radius.** Include the
   Account four-object cascade, every object shared through the role hierarchy if
   roles are changing, and the runtime of every registered Apex sharing
   recalculation class.
2. **Verify Defer Sharing Calculations is available in production** and decide
   whether the freeze it imposes is cheaper than the backlog it prevents. Record
   the decision and the fallback.
3. **Capture the verification baseline** — the per-persona list of records that
   must and must not be visible — before anything changes.
4. **Suspend group membership and sharing rule calculation**, then execute the
   load or configuration change. Disable application triggers separately if Apex
   writes `__Share` rows.
5. **Resume both calculations, then manually recalculate** from Sharing Settings.
   These are two distinct steps in this order; the button is disabled while
   deferral is active.
6. **Monitor Background Jobs to empty and Apex Jobs to complete**, and wait for
   the completion email.
7. **Run the verification probe and assert both directions** — visible where
   expected, not visible where not — before reopening reports and list views.
   Close the change record only after this passes.

---

## Review Checklist

- [ ] Driving event named; blast radius includes the Account family cascade
- [ ] Apex sharing recalculation classes inventoried and timed
- [ ] Defer Sharing Calculations confirmed present in **production**
- [ ] Runbook has resume and recalculate as separate, ordered, signed-off steps
- [ ] Application triggers writing `__Share` rows disabled separately for the load
- [ ] Verification baseline captured before the change
- [ ] Exit gate is a per-user, per-record assertion — not job status
- [ ] Negative assertions included (users who must *not* see a record)
- [ ] Managed-package licence expiry checked for criteria-based rule fields
- [ ] Change record cannot be closed while deferral is still active

---

## Salesforce-Specific Gotchas

Full detail with quotes in [`references/gotchas.md`](references/gotchas.md).

1. **Defer Sharing Calculations may not exist in your org** and is not
   self-service. Verify in production at kickoff.
2. **Resume does not replay suppressed work.** The manual recalculation is
   mandatory and separate.
3. **The Recalculate button is disabled while deferral is active** — resume first.
4. **Recalculating Accounts recalculates Cases, Contacts, and Opportunities too.**
5. **Share locks block unrelated-looking changes** mid-recalculation.
6. **Criteria-based rules referencing expired managed-package fields are silently
   skipped**, with historical sharing preserved so the rule looks healthy.
7. **Apex sharing recalculation rides along** with every platform recalculation.
8. **Deferral does not stop your own Apex `__Share` DML.**
9. **A custom object's OWD cannot go private → public** if Apex references its
   sharing entries.
10. **`UserRecordAccess` ignores restriction rules**, so it over-reports access in
    orgs that use them.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Recalculation window plan | Driving event, affected objects (including cascades), estimated duration, freeze scope, and the fallback if deferral is unavailable |
| Deferral runbook | Timestamped steps with suspend / load / resume / recalculate / monitor / verify as distinct signed-off items |
| Verification baseline and result | Per-persona user × record matrix with expected and observed access, both positive and negative |
| Apex sharing inventory | Custom objects with registered `Database.Batchable` recalculation classes and their measured runtimes |

---

## Related Skills

- `security/apex-managed-sharing-patterns` — the `Database.Batchable` recalculation
  classes that ride along with every platform recalculation
- `security/record-access-troubleshooting` — diagnosing a single user's access to a
  single record, which is a different problem from a stale rebuild
- `data/bulk-api-and-large-data-loads` — the load itself, of which the
  recalculation window is one phase
