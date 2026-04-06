# LLM Anti-Patterns — Orchestration Flows

Common mistakes AI coding assistants make when generating or advising on Flow Orchestration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Orchestration for simple sequential automation

**What the LLM generates:**

```
"Use Flow Orchestration to first create the Case, then assign it to
an agent, then send a notification."
```

**Why it happens:** LLMs suggest Orchestration for any multi-step process. But Orchestration is designed for long-running, multi-user processes with human handoffs. Simple sequential automation should use a standard autolaunched or record-triggered flow.

**Correct pattern:**

Use Orchestration only when:
- The process spans hours, days, or weeks
- Multiple users must complete steps in sequence or parallel
- Work items need assignment, reassignment, and monitoring

For the example above, a single record-triggered flow with sequential elements is sufficient.

**Detection hint:** Orchestration recommendation for a process that completes in a single transaction with no user handoffs.

---

## Anti-Pattern 2: Putting DML-heavy logic directly in orchestration steps instead of subflows

**What the LLM generates:**

```
Stage 1: Background Step
  [Get Records] --> [Loop] --> [Update Records] --> [Create Records]
```

**Why it happens:** LLMs build the logic directly in the orchestration step. Orchestration steps should delegate to autolaunched subflows that can be tested, reused, and maintained independently.

**Correct pattern:**

```
Stage 1: Background Step
  [Subflow: Process_Accounts_Subflow]

// The subflow contains the actual logic:
Process_Accounts_Subflow:
  [Get Records] --> [Loop] --> [Update Records] --> [Create Records]
```

Keep orchestration steps thin — they coordinate, subflows execute.

**Detection hint:** Orchestration background steps with more than 3-4 elements. Complex logic should be in a subflow.

---

## Anti-Pattern 3: Not designing for step failure and recovery

**What the LLM generates:**

```
Stage 1: Step 1 (Background) --> Stage 2: Step 2 (Interactive)
// No fault handling — if Step 1 fails, the orchestration is stuck
```

**Why it happens:** LLMs design the happy path. In Orchestration, a failed step can leave the entire process in a stuck state with no recovery path.

**Correct pattern:**

```
Stage 1: Step 1 (Background)
  Subflow: My_Process_Subflow (with fault connectors that log errors)
  On failure: Set status variable, route to recovery step

Stage 1: Recovery Step (Interactive)
  Assigned to: Admin
  Action: Review error, fix data, restart or skip
```

Design every background step with fault handling. Design recovery paths for interactive steps that may time out or be rejected.

**Detection hint:** Orchestration design with no mention of failure handling, recovery steps, or stuck-state resolution.

---

## Anti-Pattern 4: Using interactive steps without clear work item assignment

**What the LLM generates:**

```
Stage 1: Interactive Step
  Screen Flow: My_Approval_Screen
  // No assignee specified — who does this work item go to?
```

**Why it happens:** LLMs focus on the screen flow logic and forget that interactive steps create work items that must be assigned to specific users or queues.

**Correct pattern:**

```
Stage 1: Interactive Step
  Screen Flow: My_Approval_Screen
  Assigned to: {!ManagerUserId} (or a Queue)
  Due date: {!$Flow.CurrentDateTime} + 3 days
```

Every interactive step must specify:
- Who receives the work item
- When it is due
- What happens if it is not completed (timeout, reassignment)

**Detection hint:** Interactive orchestration step without an explicit assignee or due date.

---

## Anti-Pattern 5: Confusing parallel steps with concurrent stage execution

**What the LLM generates:**

```
"Run Stage 1 and Stage 2 in parallel to speed up the process."
```

**Why it happens:** LLMs confuse steps within a stage (which can run in parallel) with stages themselves (which always run sequentially). Stages execute in order; only steps within a single stage can be parallel.

**Correct pattern:**

```
Stage 1:
  Step A (Background) -- parallel with --> Step B (Background)
  Both must complete before Stage 2 starts

Stage 2:
  Step C (Interactive)
```

Steps within a stage run in parallel. Stages run sequentially — Stage 2 waits for all Stage 1 steps to complete.

**Detection hint:** Orchestration design describing stages running "in parallel" or "concurrently."

---

## Anti-Pattern 6: Not monitoring orchestration instances after deployment

**What the LLM generates:**

```
"Deploy the orchestration to production and it will handle the process automatically."
```

**Why it happens:** LLMs treat deployment as the finish line. Orchestrations are long-running and can pause, fail, or get stuck. Without monitoring, failed instances go unnoticed.

**Correct pattern:**

Set up monitoring:
1. Check Orchestration Run instances in Setup regularly
2. Create reports or dashboards on OrchestrationRunInstance and OrchestrationStepInstance
3. Set up alerts for stuck or failed instances (e.g., no progress in 48 hours)
4. Assign an admin or team to review and recover stuck orchestrations weekly

**Detection hint:** Orchestration advice that does not mention post-deployment monitoring, alerts, or instance review.
