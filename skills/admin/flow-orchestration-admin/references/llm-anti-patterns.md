# LLM Anti-Patterns — Flow Orchestration Admin

Common mistakes AI coding assistants make when configuring Flow Orchestration.

## Anti-Pattern 1: Using Approval Process for multi-actor parallel work

**What the LLM generates:** A standard Approval Process with multiple steps for what is clearly a multi-team parallel review.

**Why it happens:** Approval Process is well-documented and familiar; Flow Orchestration is newer.

**Correct pattern:**

```
Independent actors doing different work = Flow Orchestration Stage with
several Interactive Steps, each running its own screen flow. An Approval
Process step routes ONE approve-or-reject request to up to 25 approvers
(Unanimous or FirstResponse; api_meta 264 L25404-25414).
```

**Detection hint:** An Approval Process with three "unanimous required" steps that the business describes as "happening at the same time."

---

## Anti-Pattern 2: Heavy logic inside Evaluation Flows

**What the LLM generates:** A 15-element `EvaluationFlow` with SOQL, loops, and decision branches as the Stage's evaluation flow.

**Why it happens:** Evaluation Flows look like regular flows; the cost of running them repeatedly is not obvious. UNVERIFIED (2026-10-20): how often an evaluation flow is re-run is not stated on any corpus line; the flow's only read output is `isOrchestrationConditionMet` (api_meta 264 L70783-70787).

**Correct pattern:**

```
Evaluation Flow = one or two decisions returning a boolean. Pre-compute
context upstream (in a Background Step), then the Evaluation Flow just
reads a field and returns true/false.
```

**Detection hint:** An Evaluation Flow over ~5 elements or containing loops.

---

## Anti-Pattern 3: Interactive Step with no assignment

**What the LLM generates:** An Interactive Step that produces a Work Item but does not specify an assignee — "it will default to the current user."

**Why it happens:** The model does not realize Work Items need explicit assignment to surface on a user's list.

**Correct pattern:**

```
Every Interactive Step lists `assignees` - a User, Group, or Queue
(api_meta 264 L74763-74764, L74889-74894) - by value or by resource
reference. `assignees` is not marked Required, so the metadata deploys
without one. UNVERIFIED (2026-10-20): where an unassigned work item
surfaces in the UI.
```

**Detection hint:** A `stageSteps` entry with `<actionType>stepInteractive</actionType>` and no `<assignees>` element.

---

## Anti-Pattern 4: Rolling a long-wait via scheduled Apex

**What the LLM generates:** Suggests a scheduled Apex to poll an external system and advance the orchestration.

**Why it happens:** The model falls back on polling patterns from non-orchestration training data.

**Correct pattern:**

```
Publish FlowOrchestrationEvent from the external system on completion
(create(); OrchestrationInstanceId, StepInstanceId, StepStatus -
platform_events 264 L12625, L12662-12698). The event "notifies subscribers
that a paused instance of an orchestration is ready to be resumed"
(L12611-12613). No polling job to operate.
```

**Detection hint:** Scheduled Apex that advances orchestrations by updating records or invoking orchestration APIs.

---

## Anti-Pattern 5: Deleting orchestration metadata while instances are running

**What the LLM generates:** "Retire the old orchestration — delete the metadata, deploy the new one."

**Why it happens:** The model treats orchestration like any flow.

**Correct pattern:**

```
Drain in-flight instances first (either complete them, cancel them, or
migrate). Deploy the new orchestration alongside the old. Only delete
old metadata after the monitoring view confirms zero active instances.
```

**Detection hint:** A retirement plan that deletes Orchestration metadata on the same change window as go-live. UNVERIFIED (2026-10-20): the effect of deleting an orchestration with running instances is not in the corpus; draining first is the safe default.

---

## Anti-Pattern 6: Sending ops to Setup → Orchestration Runs

**What the LLM generates:** "Open Setup, search Orchestration Runs."

**Why it happens:** Paused Flow Interviews live in Setup, so the analogue is guessed.

**Correct pattern:**

```
/lightning/o/FlowOrchestrationInstance/list
```

That is the object list view. `/lightning/setup/OrchestrationRuns/home` is not a Setup node. UNVERIFIED (2026-10-20): both URLs are Help-only UI facts.

**Detection hint:** Any URL containing `setup/OrchestrationRuns`.

---

## Anti-Pattern 7: A "just click Resume" runbook that never names the run's status

**What the LLM generates:** "If the run is stuck, click Resume."

**Why it happens:** One control name covers more than one run state, so a single instruction looks complete.

**Correct pattern:** Name the state first — a run stalled on an unclaimed work item, a run that errored in a step, and a run paused waiting on something outside Salesforce are three different situations with three different operator actions, and only the last needs a manually published `FlowOrchestrationEvent` (the platform publishes one itself when an interactive step's screen flow completes, platform_events 264 L12614-12615). Read the exact resume semantics for each state off the Orchestration Runs detail view in the target org and write them down; do not state them from memory in a runbook someone will follow at 2am.

**Detection hint:** A single "resume" procedure that does not name the run's current status.
