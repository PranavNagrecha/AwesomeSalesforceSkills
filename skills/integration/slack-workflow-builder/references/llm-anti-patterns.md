# LLM Anti-Patterns — Slack Workflow Builder

Common mistakes AI coding assistants make when generating or advising on Slack Workflow Builder.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating any activated Flow as a valid “Run a Flow” target

**What the LLM generates:** “Select your existing **Closed Won automation** flow in the Slack **Run a Flow** step and map the Opportunity Id.”

**Why it happens:** Training data collapses “Flow” into one object; the assistant assumes any active flow in the org is invocable from Slack.

**Correct pattern:**

```
Create or reuse an **autolaunched** flow with the needed inputs. Record-triggered and screen flows are not valid targets for Slack Workflow Builder’s Run a Flow connector step. Point Slack only at that autolaunched entry point.
```

**Detection hint:** If the answer references **record-triggered**, **before save**, **screen**, or **user interview** together with **Run a Flow** inside **Slack Workflow Builder**, stop and correct the process type.

---

## Anti-Pattern 2: Confusing Slack Workflow Builder with Flow Core Actions

**What the LLM generates:** “Add **Send Slack Message** inside Slack Workflow Builder to notify the channel.”

**Why it happens:** Both surfaces mention Slack and Flow; the model maps “notify Slack” to the best-known Salesforce action name.

**Correct pattern:**

```
**Send Slack Message** is a Salesforce **Flow Core Action** used **inside Salesforce Flow**, not a Salesforce connector action authored in Slack. In Workflow Builder, use Slack’s own messaging steps for Slack-native posts, and use **Run a Flow** when Salesforce must execute logic.
```

**Detection hint:** Keywords **Core Action**, **Flow Builder**, **Send Slack Message** paired with **Workflow Builder** step names without distinguishing product surface.

---

## Anti-Pattern 3: Assuming the clicking user’s Salesforce session executes the Flow

**What the LLM generates:** “The Flow runs **as the Slack user**, so their profile permissions apply.”

**Why it happens:** Analogies to interactive OAuth apps; partially true for some Slack apps but dangerous to assert for managed connector behavior without verifying current product docs.

**Correct pattern:**

```
Treat Salesforce side effects as **integration context**: verify in official Salesforce for Slack documentation which identity and permission model applies to connector steps for your release. Never invent CRUD semantics from analogy.
```

**Detection hint:** Absolute claims about **running user**, **impersonation**, or **FLS** for connector steps without citing current help.

---

## Anti-Pattern 4: Putting callout-heavy or long-running logic in Slack-triggered flows

**What the LLM generates:** A single autolaunched flow that performs multiple **HTTP callouts**, heavy SOQL, and Slack messaging for every emoji reaction.

**Why it happens:** One-shot “just automate it” solutions ignore **governor limits**, **async** ceilings, and user experience.

**Correct pattern:**

```
Keep Slack-invoked flows **short and idempotent**. Push heavy work to **Queueable**, **Platform Events**, or **asynchronous Salesforce paths**; throttle noisy triggers at the Slack workflow level (filters, branches, rate limits where available).
```

**Detection hint:** Emoji, **shortcut**, or **message** triggers combined with **bulkified** or **callout** language without any throttling or async handoff.

---

## Anti-Pattern 5: Ignoring channel data exposure

**What the LLM generates:** “Return the full **Case** description and SSN custom field to a Slack message for visibility.”

**Why it happens:** The model optimizes for functional completeness over **data minimization**.

**Correct pattern:**

```
Return only fields required for the Slack outcome; prefer **IDs** and **non-sensitive labels**; use **private channels** or **DM workflows** when needed; align with org policies for Slack record previews and Workflow Builder outputs.
```

**Detection hint:** Flow outputs that include **PII**, **financial**, or **health** field names routed to **public** channels without governance language.
