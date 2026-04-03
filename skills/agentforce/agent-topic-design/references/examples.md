# Agent Topic Design — Examples

## Example 1: Topic As A Capability, Not A Department

**Context:** A service agent is being configured with topics called `Support`, `Sales`, and `Billing`.

**Problem:** These labels are too broad to tell the agent what job it is supposed to do, and user intents overlap immediately.

**Solution:**

```text
Replace broad labels with capability topics such as:
- Check order status
- Reschedule appointment
- Troubleshoot account access
```

**Why it works:** Each topic now has clearer activation signals, boundaries, and action needs.

---

## Example 2: Topic Selector For A Broad Domain

**Context:** The business wants the agent to support many product and service capabilities.

**Problem:** A flat topic list is becoming noisy and unreliable.

**Solution:**

```text
Use a topic selector to narrow the active candidate topic set,
then keep each selected topic small and capability-specific.
```

**Why it works:** The selector reduces topic competition before the final topic instructions are applied.

---

## Anti-Pattern: No Out-Of-Scope Rule

**What practitioners do:** Write a topic that only describes happy-path success behavior.

**What goes wrong:** The agent keeps trying to answer beyond its real boundary instead of escalating or refusing safely.

**Correct approach:** Include explicit out-of-scope, escalation, and handoff conditions in the topic design.
