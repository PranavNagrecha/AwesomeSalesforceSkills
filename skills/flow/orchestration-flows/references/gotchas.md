# Gotchas — Orchestration Flows

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Human Steps Need Queue Ownership, Not Just Page Design

**What happens:** The screen or work item is built, but nobody operationally owns the queue of pending tasks.

**When it occurs:** Teams focus on Flow canvas design and forget the support model for interactive steps.

**How to avoid:** Treat assignment, backlog management, and escalation as first-class requirements.

---

## Too Many Stages Hide The Real Milestones

**What happens:** Orchestration instances become hard to monitor because every tiny action is promoted to a stage.

**When it occurs:** Designers use stages as visual grouping rather than meaningful lifecycle markers.

**How to avoid:** Reserve stages for true milestones and keep step-level detail inside them.

---

## Background Automation Still Needs Fault And Retry Strategy

**What happens:** A background step fails and the team discovers too late that nobody designed recovery or retry expectations.

**When it occurs:** Designers assume orchestration visibility alone is enough.

**How to avoid:** Define step-level failure handling, ownership, and intervention procedures up front.
