# LLM Anti-Patterns — Flow Orchestration Admin

Common mistakes AI coding assistants make when configuring Flow Orchestration.

## Anti-Pattern 1: Using Approval Process for multi-actor parallel work

**What the LLM generates:** A standard Approval Process with multiple steps for what is clearly a multi-team parallel review.

**Why it happens:** Approval Process is well-documented and familiar; Flow Orchestration is newer.

**Correct pattern:**

```
Parallel steps with independent actors = Flow Orchestration Stage with
multiple parallel Interactive Steps. Approval Process steps run in series
and cannot branch.
```

**Detection hint:** An Approval Process with three "unanimous required" steps that the business describes as "happening at the same time."

---

## Anti-Pattern 2: Heavy logic inside Evaluation Flows

**What the LLM generates:** A 15-element autolaunched flow with SOQL, loops, and decision branches as the Stage's evaluation flow.

**Why it happens:** Evaluation Flows look like regular flows; the cost of running them repeatedly is not obvious.

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
Every Interactive Step assigns to a specific user, queue, or evaluated
field. Unassigned work items get lost in the global list; users never
see them.
```

**Detection hint:** A Flow Orchestration metadata XML with an Interactive Step missing assignee fields.

---

## Anti-Pattern 4: Rolling a long-wait via scheduled Apex

**What the LLM generates:** Suggests a scheduled Apex to poll an external system and advance the orchestration.

**Why it happens:** The model falls back on polling patterns from non-orchestration training data.

**Correct pattern:**

```
Use a Platform Event from the external system. The Background Step waits
on the event. The external system publishes on completion; orchestration
resumes. No polling, lower cost, tighter coupling to the real event.
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

**Detection hint:** A retirement plan that deletes Orchestration metadata on the same change window as go-live.

---

## Anti-Pattern 6: Sending ops to Setup → Orchestration Runs

**What the LLM generates:** "Open Setup, search Orchestration Runs."

**Why it happens:** Paused Flow Interviews live in Setup, so the analogue is guessed.

**Correct pattern:**

```
/lightning/o/FlowOrchestrationInstance/list
```

That is the object list view. `/lightning/setup/OrchestrationRuns/home` is not a Setup node.

**Detection hint:** Any URL containing `setup/OrchestrationRuns`.

---

## Anti-Pattern 7: A "just click Resume" runbook that never names the run's status

**What the LLM generates:** "If the run is stuck, click Resume."

**Why it happens:** One control name covers more than one run state, so a single instruction looks complete.

**Correct pattern:** Name the state first — a run stalled on an unclaimed work item, a run that errored in a step, and a run paused waiting on something outside Salesforce are three different situations with three different operator actions, and only the last is resumed by publishing a `FlowOrchestrationEvent`. Read the exact resume semantics for each state off the Orchestration Runs detail view in the target org and write them down; do not state them from memory in a runbook someone will follow at 2am.

**Detection hint:** A single "resume" procedure that does not name the run's current status.
