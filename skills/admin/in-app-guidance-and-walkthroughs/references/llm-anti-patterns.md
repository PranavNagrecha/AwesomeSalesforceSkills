# LLM Anti-Patterns — In-App Guidance and Walkthroughs

Common mistakes AI coding assistants make when generating or advising on In-App Guidance configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Role-Based or Permission-Set Audience Targeting

**What the LLM generates:** "Set the audience to users with the Sales Manager role" or "Target users who have the 'Manage In-App Guidance' permission set."

**Why it happens:** LLMs generalize from Salesforce's broader access control model (profiles, roles, permission sets) and assume all three targeting axes are available in every UI. Training data may include older Salesforce documentation or community posts predating Spring '25 that speculated about future targeting options.

**Correct pattern:**

```
In-App Guidance audience targeting supports profiles only as of Spring '25.
Audience configuration: select one or more profiles from the Profile picker.
Roles, territories, permission sets, and behavioral conditions are not supported natively.
```

**Detection hint:** Any response that mentions "role," "territory," "permission set," or "behavior-based" in the context of In-App Guidance audience targeting is incorrect.

---

## Anti-Pattern 2: Treating the 3-Walkthrough Limit as a Total Creation Limit

**What the LLM generates:** "You can only create 3 walkthroughs total in Salesforce." or "You've used all 3 walkthroughs — you must delete them to create more."

**Why it happens:** LLMs conflate "active" with "total." The limit is on simultaneously active walkthroughs, not on the total number ever created or currently existing in the org.

**Correct pattern:**

```
The free tier allows 3 active walkthroughs at one time.
Deactivating a walkthrough frees its slot immediately.
Previously deactivated walkthroughs remain in Setup > In-App Guidance and can be reactivated.
AppExchange managed-package prompts do not count against this limit.
```

**Detection hint:** Any response that says "delete" instead of "deactivate" when addressing the limit, or that says "3 total" instead of "3 active."

---

## Anti-Pattern 3: Claiming In-App Guidance Works in Experience Cloud

**What the LLM generates:** "Deploy this prompt to your Experience Cloud site to guide partner users through the process."

**Why it happens:** LLMs associate "Salesforce" broadly and assume Lightning Experience features extend to all Salesforce-hosted surfaces. Experience Cloud is a Salesforce product, so the inference seems reasonable but is wrong.

**Correct pattern:**

```
In-App Guidance prompts and walkthroughs are Lightning Experience-only.
They do not render in Salesforce Classic or in Experience Cloud sites (partner portals, customer portals, digital experience sites).
For Experience Cloud guidance needs, use custom LWC components or Flow-triggered in-app notifications.
```

**Detection hint:** Any response that mentions deploying In-App Guidance to Experience Cloud, portals, or community sites.

---

## Anti-Pattern 4: Suggesting More Than 5 Steps per Walkthrough Without Flagging Completion Risk

**What the LLM generates:** A 7- or 8-step walkthrough plan that maps every field on a complex record layout to a targeted prompt step, presented without caveats about completion rates.

**Why it happens:** When asked to "cover all fields in this process," LLMs optimize for completeness. The Salesforce-specific completion rate threshold (5 steps) is not general knowledge that LLMs reliably internalize.

**Correct pattern:**

```
Salesforce recommends a maximum of 5 steps per walkthrough for acceptable completion rates.
For processes with more than 5 distinct guidance points, split into two separate walkthroughs
(each covering one phase of the process), or reduce to the 3–5 highest-friction steps only.
```

**Detection hint:** Any walkthrough design with more than 5 steps presented without a completion-rate warning.

---

## Anti-Pattern 5: Omitting the Anchor Maintenance Risk for Targeted Prompts

**What the LLM generates:** A targeted prompt configuration that anchors to a specific field or button, with no mention of what happens if that UI element is later removed.

**Why it happens:** LLMs present configuration steps without operational lifecycle context. The silent failure mode (no error surfaced when anchor is removed) is a platform-specific operational detail not commonly documented in general Salesforce tutorials.

**Correct pattern:**

```
When configuring a targeted prompt, document the anchor element explicitly:
- Record the field API name or button label in the prompt's Description field
- Add the anchor element to your deployment checklist as a dependency
- After any page layout change, audit all targeted prompts to confirm anchors still exist
If the anchor element is removed, the targeted prompt will silently stop rendering.
No error or alert is generated for the admin.
```

**Detection hint:** Any targeted prompt recommendation that does not mention anchor maintenance, layout dependencies, or the silent failure mode.

---

## Anti-Pattern 6: Conflating PromptAction Analytics with Real-Time Behavioral Data

**What the LLM generates:** "Use In-App Guidance analytics to see which users have not started the process yet" or "Track user behavior in real time with PromptAction."

**Why it happens:** LLMs over-extend the analytics capability of PromptAction. The object records interaction events (dismissed, completed) but does not track what users do after leaving the prompt, nor does it update in real time in the reporting layer.

**Correct pattern:**

```
PromptAction records prompt interaction events: whether a user dismissed or completed each step.
It does NOT track what users do after the prompt (e.g., whether they actually completed the process).
It is NOT a real-time behavioral signal — use standard Salesforce Reports for process completion metrics.
For full adoption measurement, combine PromptAction data (did they see the prompt?)
with process object data (did the field get populated? was the record submitted?).
```

**Detection hint:** Any response that uses PromptAction as a proxy for process completion or task execution behavior downstream of the prompt.
