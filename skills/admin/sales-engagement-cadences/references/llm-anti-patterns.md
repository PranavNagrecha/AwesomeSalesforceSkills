# LLM Anti-Patterns — Sales Engagement Cadences

Common mistakes AI coding assistants make when generating or advising on Sales Engagement Cadences.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Sales Engagement Cadences With Marketing Cloud Journeys

**What the LLM generates:** Advice to "set up a journey in Sales Engagement" or instructions referencing Journey Builder, Automation Studio, or Marketing Cloud send definitions when the user is asking about Sales Engagement cadences.

**Why it happens:** Training data conflates Sales Engagement (rep-driven outbound sequences) with Marketing Cloud journeys (automated marketing campaigns) because both use "engagement" terminology and both involve email sequences.

**Correct pattern:**

```
Sales Engagement cadences are configured in:
  Setup > Sales Engagement > Cadences

They are NOT configured in Marketing Cloud, Journey Builder,
or Marketing Cloud Account Engagement (Pardot).

Sales Engagement targets Lead and Contact records in Sales Cloud.
Marketing Cloud targets Subscribers in a separate system.
```

**Detection hint:** Any mention of "Journey Builder," "Automation Studio," "Pardot," or "Marketing Cloud" in a response about Sales Engagement cadence setup is wrong.

---

## Anti-Pattern 2: Recommending Apex to Create or Manage Cadences Programmatically

**What the LLM generates:** Apex code using `SalesEngagementService` or `CadenceService` Apex classes, or DML on `SalesEngagementCadence__c` objects, to create or enroll leads in cadences.

**Why it happens:** LLMs default to code-first answers for automation tasks. There is limited official Apex API for cadence management; the LLM fills the gap with hallucinated class names or incorrectly applies Flow patterns to an Apex context.

**Correct pattern:**

```
Cadence enrollment is managed declaratively:
- Manual: Rep adds prospect via the Cadence related list or Work Queue
- Automated: Use Flow (Record-Triggered Flow with "Add to Cadence" action)
  available in Flow Builder as a standard action element

There is no supported public Apex API for cadence creation or enrollment.
Do not generate Apex DML against cadence objects.
```

**Detection hint:** Any code block containing `SalesEngagementService`, `CadenceService`, or DML/SOQL referencing `SalesEngagementCadence` or `CadenceEnrollment` objects is almost certainly hallucinated.

---

## Anti-Pattern 3: Treating the 500,000 Active Target Cap as the Only Limit

**What the LLM generates:** "Your org supports up to 500,000 active targets in Sales Engagement" — stated as the sole limit without mentioning the 150,000 active tracker limit.

**Why it happens:** The 500,000 cap is the most-cited limit in Salesforce documentation summaries. The 150,000 tracker limit is a secondary constraint that affects email engagement tracking, and LLMs trained on abbreviated source material miss it.

**Correct pattern:**

```
Sales Engagement has two separate org-wide limits:
1. Active target cap: 500,000 prospects enrolled across all active cadences
2. Active tracker limit: 150,000 email engagement trackers
   (governs open/click/reply signal tracking)

A high-volume org can hit the tracker limit (150,000) while still being
well under the target cap (500,000). Exceeding the tracker limit silently
disables engagement tracking for new enrollments.

Always check BOTH limits under Setup > Sales Engagement Settings > Usage.
```

**Detection hint:** Any limit discussion that mentions only one number ("500,000") without the tracker limit is incomplete.

---

## Anti-Pattern 4: Suggesting "High Velocity Sales" as the Current Product Name

**What the LLM generates:** Instructions referencing "High Velocity Sales" (HVS) as the product name, e.g., "Go to Setup > High Velocity Sales" or "enable High Velocity Sales in your org."

**Why it happens:** Sales Engagement was branded "High Velocity Sales" until Spring '21. LLMs trained on pre-rename documentation or community posts continue to use the old name and old Setup navigation paths, which no longer exist in current orgs.

**Correct pattern:**

```
Current product name: Sales Engagement
Current Setup path: Setup > Sales Engagement > Settings

"High Velocity Sales" is the legacy name (pre-Spring '21).
The Setup node "High Velocity Sales" does not exist in current orgs.
Any instructions using the old name should be treated as potentially outdated.
```

**Detection hint:** References to "High Velocity Sales" as a Setup menu path or product name in a current-release context signal stale documentation.

---

## Anti-Pattern 5: Assuming All Step Types Are Available Without Checking Prerequisites

**What the LLM generates:** Instructions to add a LinkedIn step or configure a dialer Call step without first checking edition and integration prerequisites.

**Why it happens:** The LLM describes Cadence Builder 2.0 step types as universally available because the documentation lists all five types without prominent edition-gating callouts. The LLM omits the prerequisite checks for LinkedIn (Sales Navigator required) and Call steps (dialer required).

**Correct pattern:**

```
Step type availability by prerequisite:

Email steps     -> Available in all editions with Sales Engagement enabled
Wait steps      -> Available in all editions with Sales Engagement enabled
Custom steps    -> Available in all editions with Sales Engagement enabled
Call steps      -> Require: built-in Salesforce dialer OR CTI integration configured
LinkedIn steps  -> Require: LinkedIn Sales Navigator integration enabled in Setup

Before advising on Call or LinkedIn steps, always confirm:
1. Is the dialer configured? (Setup > Sales Engagement > Dialer)
2. Is LinkedIn Sales Navigator enabled? (Setup > LinkedIn Sales Navigator)
```

**Detection hint:** Any instruction to add a Call or LinkedIn step without a prerequisite check on dialer or Sales Navigator configuration is incomplete.
