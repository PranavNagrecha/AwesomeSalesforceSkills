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

## Anti-Pattern 3: Asserting the wrong identity for connector steps

**What the LLM generates:** "The Flow runs as the Slack user, so their profile permissions apply", or the opposite, with no mention of the step's account setting.

**Why it happens:** Analogies to interactive OAuth apps. An earlier version of this file said the identity model was unknown.

**Correct pattern:**

```
Slack Help, Authenticate third-party accounts to use connector steps:
- The builder connects an account when adding the step.
- Default: people using the workflow can use the builder's account.
- "Whose account should be used for this step" > "The person using the workflow"
  makes each user authenticate, so their Salesforce permissions apply.
Coded workflows: credential_source "END_USER" (link trigger only) or "DEVELOPER".
```

**Detection hint:** Any claim about which Salesforce user runs the step that does not name the step's account setting.

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

---

## Anti-Pattern 6: Letting Slack Connect partners run steps on an internal account

**What the LLM generates:** "Share the workflow in the partner channel so suppliers can update their Salesforce records."

**Why it happens:** The model treats shared channels like internal ones.

**Correct pattern:** Slack Help says external people can only use workflows with connector steps that do not require them to authenticate, and admins control whether they can use such workflows at all. A step that runs on an internal account would therefore act with internal permissions on a partner's behalf. Use a Salesforce-side intake (for example an Experience Cloud form) for partners instead.

**Detection hint:** A Salesforce connector workflow intended for a Slack Connect channel with no identity or admin-setting review.

---

## Anti-Pattern 7: Building a flow for a single record update

**What the LLM generates:** An autolaunched flow whose only element is Update Records, called through Run a Flow.

**Why it happens:** The model reaches for Run a Flow by default.

**Correct pattern:** The Salesforce connector has Create a record, Read a record, Update a record, and Delete a record steps. Use them for single-record work and keep Run a Flow for logic that needs a flow.

**Detection hint:** A Run a Flow target whose flow contains one record element and no decisions.

