# Agent Topic Design — Examples

## Example 1: Subagent As A Capability, Not A Department

**Context:** A service agent is being configured with subagents (called topics before April 2026) named `Support`, `Sales`, and `Billing`.

**Problem:** These labels are too broad to tell the agent what job it is supposed to do, and user intents overlap immediately.

**Solution:**

```text
Replace broad labels with capability subagents such as:
- Check order status
- Reschedule appointment
- Troubleshoot account access
```

**Why it works:** Each subagent now has clearer activation signals, boundaries, and action needs.

---

## Example 2: Topic Selector For A Broad Domain

**Context:** The business wants the agent to support many product and service capabilities.

**Problem:** A flat subagent list is becoming noisy and unreliable.

**Solution:**

```text
Use a topic selector to narrow the active candidate subagent set,
then keep each selected subagent small and capability-specific.
```

**Why it works:** The selector reduces subagent competition before the final subagent instructions are applied.

---

## Anti-Pattern: No Out-Of-Scope Rule

**What practitioners do:** Write a subagent that only describes happy-path success behavior.

**What goes wrong:** The agent keeps trying to answer beyond its real boundary instead of escalating or refusing safely.

**Correct approach:** Include explicit out-of-scope, escalation, and handoff conditions in the subagent design.

---

## Example 3: Topic Metadata, Agent Script Router, and Routing Test

**Context:** The `Order_Returns` subagent for a retail service agent, designed with the instruction template from SKILL.md.

**Solution:** The complete `GenAiPlugin` XML, the equivalent Agent Script router and subagent, the `AiEvaluationDefinition` routing test, and the `package.xml` member form are in `references/metadata-examples.md`. The design maps onto metadata fields like this:

```text
Template section            GenAiPlugin field
What this subagent does  -> description (1-3 sentences; the classification signal)
When to activate         -> description + aiPluginUtterances
Does NOT do              -> description (exclusions) + scope ("You are not allowed to ...")
Handoff rules            -> canEscalate + an out-of-scope instruction
Actions available        -> genAiFunctions (no more than 15)
```

**Why it works:** Each section of the design has a home in deployable metadata, so the review artifact and the deployed topic cannot drift apart.
