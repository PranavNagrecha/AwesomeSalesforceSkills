# Gotchas — Flow Orchestration Admin

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: An Orchestration Has `processType` `Orchestrator` — Flow Inventories Filtering on `AutoLaunchedFlow` Miss Every One

**What happens:** Deployment gates, Flow inventory reports, and "how many active flows do we have" audits routinely filter on `ProcessType = 'AutoLaunchedFlow'` or `'Flow'`. Orchestrations are neither. Metadata API defines `Orchestrator` as its own process type — "An orchestration that organizes flows into groups of steps contained in a series of stages" (API version 53.0 and later). The audit returns a clean number that excludes the most business-critical automation in the org.

**When it occurs:** Any org-health scan, release checklist, or governance dashboard written before orchestrations were adopted. It also hits change-management tooling that decides what needs regression testing based on process type.

**How to avoid:** Enumerate process types explicitly rather than by exclusion, and include `Orchestrator` and `ApprovalWorkflow` in every flow inventory. When reviewing someone else's flow audit, check the filter before trusting the count — an orchestration that fails is a multi-user process stopping, not one record failing.

---

## Gotcha 2: `ApprovalWorkflow` and `Orchestrator` Are Different Process Types, Chosen Once

**What happens:** Two orchestration process types exist. `Orchestrator` is the general one; `ApprovalWorkflow` is "An orchestration that's used for an approval process" and is available in API version 63.0 and later. They are not interchangeable and `processType` is not something you flip on an existing flow — picking the wrong one means rebuilding the orchestration, re-testing every branch, and re-pointing anything that referenced it.

**When it occurs:** At the very first design decision, usually before anyone has read far enough to know both exist. Teams migrating off classic Approval Processes are the common casualty: they build a general `Orchestrator` because that is the type they had heard of, then discover the approval-shaped one after go-live.

**How to avoid:** Resolve the choice against `standards/decision-trees/automation-selection.md` before opening Flow Builder, and record which type was chosen and why. Also check the target org's API version — `ApprovalWorkflow` does not exist below 63.0, so a sandbox or scratch-org definition pinned lower cannot represent it and the retrieve comes back without it.

---

## Gotcha 3: The `ConnectApi.Orchestration` Overloads Are Version-Gated and Fail at Compile Time

**What happens:** Apex that reads orchestration state compiles in one org and refuses to compile in another. The three methods landed in different releases: `getOrchestrationInstanceCollection(String relatedRecordId)` in API 54.0, `getOrchestrationInstance(String instanceId)` in 63.0, and the two-argument `getOrchestrationInstanceCollection(String relatedRecordId, String relatedOrchestrationId)` in 66.0. The controlling value is the `apiVersion` in the class's own `.cls-meta.xml`, not the org's release — a Summer '26 org runs a class pinned to 58.0 quite happily, and that class cannot see the 63.0 or 66.0 methods.

**When it occurs:** Copying a monitoring or "show me my in-flight orchestrations" component between projects, or adding orchestration reads to an old utility class that nobody has re-versioned in three years.

**How to avoid:** Check the class's `apiVersion` before writing the call, and raise it deliberately rather than downgrading the code. On the two-argument overload the docs are explicit: "You must specify either relatedRecordId or relatedOrchestrationId" — passing both as null is a runtime failure, not a compile error, so it survives to production.

---

## Gotcha 4: Work Items Are Records, and Nothing Watches Them for You

**What happens:** An interactive step assigns work and then waits — indefinitely. `FlowOrchestrationWorkItem` "represents a work item associated with a run-time instance of an interactive step in a run-time instance of an orchestration" (API version 54.0 and later). It is a queryable record, which means an orchestration stalled on one distracted reviewer is fully visible in a report — and completely invisible to anyone who has not built that report. The Orchestrations UI shows what is running; it is not an SLA monitor and raises no alert.

**When it occurs:** Most painfully in parallel stages, where the stage advances only when every step in it completes. One unassigned or ignored work item holds the entire stage, and the other reviewers who finished promptly have no signal that anything is wrong.

**How to avoid:** Build the aging report before go-live, not after the first escalation: a list view or report over work items grouped by assignee and age, with an alert on anything past the stage's SLA. Because work items are records, ordinary reporting and notification tooling works on them — there is no orchestration-specific monitoring product to wait for. Pair it with a documented reassignment procedure so ops has an answer when the aging report fires.

---

## Gotcha 5: Invocable Apex Behind a Background Step Is Gated by Its Own Class API Version

**What happens:** A Background Step calls an autolaunched flow, which calls an invocable Apex method. On a Summer '26 org the deployment fails with `WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead`. The clause was removed in API 67.0, and the admin who built the orchestration has no visibility into the Apex three layers down.

**When it occurs:** During the deployment that raises a helper class's `apiVersion` to 67.0 — often an unrelated change that happens to touch the same class. It surfaces as "the orchestration deploy is broken" even though the orchestration metadata is fine.

**How to avoid:** Treat every invocable the orchestration reaches as part of the orchestration's deployable surface, and inventory their `apiVersion` values. From 67.0 the platform defaults SOQL, SOSL, DML, and `Database` methods to user mode, so the clause is not merely deprecated — it does not compile. On write paths that assemble records from step inputs, `Security.stripInaccessible(AccessType.CREATABLE, records)` returns an `SObjectAccessDecision`, and DML must run against `.getRecords()`; default user mode throws and fails the whole step instead, which for an orchestration means a stalled instance rather than a partial save. See `agents/_shared/AGENT_CONTRACT.md` § "Apex security idiom by API version" for the full version table.

---

## Gotcha 6: Orchestration Runs Is Not a Setup Node

**What happens:** Admins search Setup for "Orchestration Runs". Find returns nothing. `/lightning/setup/OrchestrationRuns/home` is **not a valid Setup node** — it 404s or dumps a generic Setup shell. Ops concludes they lack permission.

**When it occurs:** First-time monitoring, demo runbooks copied from a guess, anyone who analogises to "Paused Flow Interviews" in Setup.

**How to avoid:** Orchestration Runs is a **standard object list view**, not a Setup page:

```
/lightning/o/FlowOrchestrationInstance/list          the runs list
/lightning/r/FlowOrchestrationInstance/<id>/view     one run's detail
```

Grant object access to `FlowOrchestrationInstance` / `FlowOrchestrationStepInstance` / `FlowOrchestrationWorkItem`. "Manage Orchestration Runs" is a separate permission from "Manage Flow".

---

## Gotcha 7: Three Permissions, Not One

**What happens:** The person who can build the orchestration cannot Resume an errored run, or the reviewer cannot complete a Work Item. One profile change is expected to cover all three.

**When it occurs:** "Give them Manage Flow" as the entire ops model.

**How to avoid:** Treat them as three grants: **Manage Flow** (build), **Manage Orchestration Runs** (pause / resume / cancel the run), **Run Flows** (complete a work item). Confirm all three on the persona perm set before go-live.

---

## Gotcha 8: Nothing Polls — Publish a `FlowOrchestrationEvent`

**What happens:** A scheduled job or time-based flow "advances" the orchestration by flipping a field the stage-exit condition reads. It works until the schedule lags, double-fires, or the field is written by something else.

**When it occurs:** Waiting on an external system or a Salesforce field that changes outside the orchestration, and the author reaches for polling because that is the Flow Pause mental model.

**How to avoid:** Resume a paused run by publishing the platform event built for it. `FlowOrchestrationEvent` "notifies subscribers that a paused instance of an orchestration is ready to be resumed" and is available in API version 53.0 and later — a publish from Apex, Flow, or an external system is a single delivery with retry semantics, where a polling job is a schedule you now have to operate. Confirm the event's field API names against the Platform Events Developer Guide before wiring the publisher; do not infer them from the run or step objects.
