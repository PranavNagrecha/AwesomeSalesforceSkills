# Examples — Orchestration Flows

## Example 1: Customer Onboarding Across Teams

**Context:** A new customer onboarding process requires account setup, legal review, and customer-success handoff over several days.

**Problem:** A standard flow cannot clearly represent which team owns the next action or how to monitor stalled work.

**Solution:**

```text
Stage 1: Background account setup
Stage 2: Interactive legal review work item
Stage 3: Background entitlement creation
Stage 4: Interactive customer-success kickoff work item
```

**Why it works:** The process milestones and ownership are explicit, and operations teams can see where instances are waiting.

---

## Example 2: Fulfillment With Human Exception Handling

**Context:** Most order fulfillment steps are automated, but high-value exceptions must be reviewed by operations.

**Problem:** The original design forces every order through a manual review path, creating backlog and hiding which orders are truly exceptional.

**Solution:**

```text
Background step: validate and enrich order
Decision: exception threshold met?
  No -> continue automated fulfillment
  Yes -> create interactive work item for operations review
```

**Why it works:** Human work is reserved for exception paths while the normal path stays automated.

---

## Anti-Pattern: Using Orchestration As A Bigger Canvas

**What practitioners do:** They move a normal synchronous process into Orchestration simply because the logic looks large.

**What goes wrong:** The team inherits stage, work-item, and monitoring overhead without getting value from the orchestration model.

**Correct approach:** Use Flow Orchestration only when the process genuinely spans time, teams, or asynchronous ownership transitions.
