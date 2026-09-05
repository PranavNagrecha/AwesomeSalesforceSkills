# LLM Anti-Patterns — In-App Guidance and Walkthroughs

Common mistakes AI coding assistants make when generating or advising on In-App Guidance configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Role-, Territory-, or Field-Based Audience Targeting

**What the LLM generates:** "Set the audience to users with the Sales Manager role", "target the EMEA territory", or "show it only to users whose Opportunity count is zero."

**Why it happens:** LLMs generalize from Salesforce's broader access-control model and assume every axis in it — role, territory, queue, record data — is available to every targeting UI. The narrower failure is the mirror image: some training data flattens this to "profiles only", which is also wrong and loses the option that actually solves cohort targeting.

**Correct pattern:**

```
uiFormulaRule leftValue accepts exactly three expression forms:
  {!$Permission.CustomPermission.<name>}     rightValue: true
  {!$Permission.StandardPermission.<name>}   rightValue: true
  {!ENCODED:{!ID:$User.Profile.Key}}         rightValue: <profile name>

operator accepts only EQUAL. Permission expressions work on app, Home,
and record pages only. Roles, territories, queues, and record field values
are not expressible. For a cohort that is not a profile, create a custom
permission, grant it via a permission set, and gate on it.
```

**Detection hint:** Any response that mentions "role", "territory", or a record field in the context of In-App Guidance targeting — and equally, any response that claims profiles are the only option.

---

## Anti-Pattern 2: Treating the 3-Walkthrough Limit as a Total Creation Limit

**What the LLM generates:** "You can only create 3 walkthroughs total in Salesforce." or "You've used all 3 walkthroughs — you must delete them to create more."

**Why it happens:** LLMs conflate "active" with "total." The limit is on simultaneously active walkthroughs, not on the total number ever created or currently existing in the org.

**Correct pattern:**

```
The free tier allows 3 active walkthroughs at one time.
  (UNVERIFIED 2026-09-04: figure rests on the Salesforce Help "Limits for
   In-App Guidance" article, which cannot be fetched; the v62 Metadata API
   guide states no cap. Confirm against the org's own Setup page.)
Deactivating a walkthrough frees its slot immediately.
Previously deactivated walkthroughs remain in Setup > In-App Guidance and can be reactivated.
AppExchange managed-package prompts do not count against this limit.
```

**Detection hint:** Any response that says "delete" instead of "deactivate" when addressing the limit, or that says "3 total" instead of "3 active."

---

## Anti-Pattern 3: Getting the Experience Cloud Answer Wrong in Both Directions

**What the LLM generates:** "Deploy this prompt to your Experience Cloud site to guide partner users through the process" — asserted flatly, for any page, with no verification step.

**Why it happens:** LLMs associate "Salesforce" broadly and assume Lightning Experience features extend to all Salesforce-hosted surfaces. Experience Cloud is a Salesforce product, so the inference seems reasonable but is wrong.

**Why the naive correction is also wrong:** "In-App Guidance is Lightning Experience only" is the reflex fix and it overshoots. Both official guides say prompts are added "in Lightning Experience pages or apps or in supported Experience Cloud site pages". The real constraints are that Classic is excluded outright, and that Experience Cloud support is limited to *supported* pages, which the Metadata API guide does not enumerate.

**Correct pattern:**

```
In-App Guidance does not render in Salesforce Classic.
It does render in supported Experience Cloud site pages (Metadata API Developer
Guide, Prompt > Special Access Rules; Object Reference, PromptAction).
Which pages are "supported" is not enumerated in either guide — prove it in a
sandbox site before committing a partner-facing rollout.
PromptError.Type NoAccessToApp / NoAccessToPage is the signal that a step
landed somewhere part of the audience cannot reach.
```

**Detection hint:** Any response that states In-App Guidance is Lightning-Experience-only without qualification, and any response that promises Experience Cloud support for a specific page type without saying it must be verified.

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

**Why it happens:** LLMs present configuration steps without operational lifecycle context. The degradation mode is a platform-specific detail not commonly documented in general Salesforce tutorials — and the version LLMs do repeat ("it silently stops rendering") is itself wrong in two ways, which is worse than saying nothing.

**Correct pattern:**

```
When the anchored element moves or is removed, the targeted prompt does NOT
stop rendering. Per the Object Reference (PromptError.Type):
  "The target element has moved or is no longer on your page. Targeted prompts
   attached to unavailable elements convert to floating prompts."
A PromptError row is written with Type = ReferenceElementNotFound. Nothing
notifies the admin, so the row must be queried:
  SELECT Type, StepNumber, COUNT(Id) FROM PromptError GROUP BY Type, StepNumber

So, when configuring a targeted prompt:
- Record the field API name or button label in the prompt's description field
- Add the anchor to the release's dependency list
- Run the PromptError query in the post-deploy check of any release that
  touches the page layout or Lightning page, not in a quarterly audit
```

**Detection hint:** Any targeted prompt recommendation that does not mention anchor maintenance or layout dependencies — and any response that says the prompt "silently stops rendering" or that "no record of the failure exists".

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
