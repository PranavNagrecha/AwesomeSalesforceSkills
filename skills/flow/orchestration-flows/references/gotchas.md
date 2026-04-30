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

---

## $Profile.Name Always Returns Automated Process In Background Steps

**What happens:** A background step that checks `$Profile.Name` silently evaluates against the Automated Process user — not the user who triggered the record change. Logic that worked correctly in a record-triggered flow (which ran in the triggering user's context) will always be false or skip entirely in an orchestration background step.

**When it occurs:** Migrating a record-triggered flow that uses `$Profile.Name` to restrict logic to specific user profiles (e.g., Community, Portal, or internal admin users) into an orchestration background step.

**How to avoid:** Replace `$Profile.Name` checks with a query chain inside the auto-launched flow: query the User record using the triggering record's `LastModifiedById`, then query that user's Profile, then check `Profile.Name`. This reconstructs the triggering user's profile from stored data rather than from runtime context, which is not available in async execution.

---

## Multi-Status Flows Must Be Split When Partially Migrating To Orchestration

**What happens:** A single async flow handles multiple record status values in one flow with internal decision routing. When one status path is moved into orchestration, the original flow is fully deactivated — and the remaining status paths stop working silently with no error surfaced.

**When it occurs:** Moving only one status path (e.g., Submitted) into orchestration while the original flow also handles other statuses (e.g., Withdrawn, Expired). The team deactivates the original assuming orchestration replaces it entirely.

**How to avoid:** Do not deactivate the original flow. Update its entry condition to exclude the status value now owned by the orchestration. The orchestration owns one path; the original flow continues to own the others. Document the split explicitly in both flow descriptions so the next developer does not re-deactivate the original.
