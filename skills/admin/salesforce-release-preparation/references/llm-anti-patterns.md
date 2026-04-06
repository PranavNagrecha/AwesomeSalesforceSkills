# LLM Anti-Patterns — Salesforce Release Preparation

Common mistakes AI coding assistants make when generating or advising on Salesforce Release Preparation. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Citing a Generic Upgrade Date Instead of Instance-Specific Date

**What the LLM generates:** "Your production org will be upgraded on February 8, 2025" — using the first date in the published release calendar as if it applies universally.

**Why it happens:** LLMs trained on community blog posts and Salesforce announcements see the first headline date for a release and generalize it. The instance-specific variation in upgrade scheduling is less prominent in training data than the release announcement date.

**Correct pattern:**

```
The production upgrade date depends on your org's Salesforce instance (e.g., NA1, NA100, EU15).
Look up your specific instance at trust.salesforce.com under Planned Maintenance, or check
Setup > Release Updates in your org for the instance-specific date.
```

**Detection hint:** Any response that states a specific upgrade date without asking for or referencing the org's Salesforce instance should be treated as suspect.

---

## Anti-Pattern 2: Recommending Toggling Off a Release Update as a Long-Term Solution

**What the LLM generates:** "You can disable this Release Update in Setup > Release Updates to avoid the breaking change."

**Why it happens:** LLMs see the toggle UI described in documentation and in community posts where admins temporarily turn off updates to investigate issues. The enforcement deadline concept — after which the toggle is removed — is less prominently represented in training data, so LLMs miss the temporal constraint.

**Correct pattern:**

```
Toggling off a Release Update is a temporary measure for testing purposes only.
Every Release Update has an enforcement date after which Salesforce permanently
enforces the behavior and removes the toggle. Use the toggle to buy time for
sandbox testing and fix deployment, not as a permanent workaround.
Check the enforcement date in Setup > Release Updates before planning any workaround.
```

**Detection hint:** Any advice to "disable the Release Update" without mentioning the enforcement date and a plan to fix the underlying issue before that date is incomplete.

---

## Anti-Pattern 3: Treating Release Notes as Purely Informational

**What the LLM generates:** "Review the release notes to stay informed about new features. Here is a summary of what's new in Summer '25."

**Why it happens:** LLMs default to a feature-briefing framing because most public content about release notes is written as "what's new" marketing copy. The operational triage purpose — finding items that require admin action, developer remediation, or stakeholder communication — is less dominant in training data.

**Correct pattern:**

```
Release notes are not just a feature catalog. They are the primary input for:
- Identifying Release Updates with enforcement deadlines requiring sandbox testing
- Finding End User behavior changes that need stakeholder communication
- Catching API version deprecations or Flow behavior changes that affect existing automations
- Identifying Requires Setup items with activation deadlines

Apply the Feature Impact filter (Admin, Developer, End User, Requires Setup) and
cross-filter by active feature areas to produce an action-oriented triage list.
```

**Detection hint:** A release notes summary that lists new features without identifying items requiring action, assigning owners, or flagging enforcement dates is using the wrong framing.

---

## Anti-Pattern 4: Assuming Sandbox Preview is Always Available for All Sandbox Types

**What the LLM generates:** "Simply enroll your Full Sandbox in Sandbox Preview to test the release early."

**Why it happens:** LLMs have seen general statements about Sandbox Preview without absorbing the per-release eligibility constraints. Salesforce publishes which sandbox types are eligible for each release cycle, and not all types qualify every time.

**Correct pattern:**

```
Sandbox Preview eligibility varies by release cycle and sandbox type.
Before enrolling, check the current release's Sandbox Preview Instructions
(Salesforce Knowledge Article 000391927) to confirm which sandbox types
are eligible for the specific release you are preparing for.
Developer and Developer Pro sandboxes are most commonly eligible.
Full and Partial Copy sandboxes may have different eligibility rules per cycle.
```

**Detection hint:** Any enrollment recommendation that does not reference checking the eligibility criteria in the release-specific Sandbox Preview article should be verified.

---

## Anti-Pattern 5: Recommending Release Notes Review Without Mentioning the Triage Framework

**What the LLM generates:** "Go through the release notes and make a list of anything that might affect your org."

**Why it happens:** The LLM knows release notes should be read but defaults to an informal approach because the systematic triage methodology — Feature Impact filter, feature area cross-filter, item ownership assignment — requires domain knowledge about how Salesforce structures its release notes UI and documentation.

**Correct pattern:**

```
Unfiltered release notes review is insufficient for orgs with multiple feature areas.
Use this triage framework:
1. Apply the Feature Impact filter: Admin, Developer, End User, Requires Setup.
2. Apply a secondary filter for your active product areas (Sales Cloud, Service Cloud, etc.).
3. For each item in the filtered list, classify it: action required, decision required, or informational.
4. Assign an owner and a sandbox test date for every action-required item.
5. Move all End User items to the stakeholder communication brief.
This reduces a 300+ item document to a 20–40 item action list for most orgs.
```

**Detection hint:** Any release preparation recommendation that does not include filtering mechanics and item ownership assignment is likely to produce incomplete coverage.

---

## Anti-Pattern 6: Skipping Stakeholder Communication in the Release Preparation Plan

**What the LLM generates:** A release preparation checklist that covers Release Updates, sandbox testing, and upgrade date confirmation, but omits stakeholder communication about end-user-visible changes.

**Why it happens:** LLMs trained on technical documentation produce technically complete plans. Stakeholder communication is an organizational process, not a platform configuration, so it is less prominent in technical reference sources.

**Correct pattern:**

```
Every release preparation plan must include a stakeholder communication step.
For each End User impact item in the triaged release notes:
- Write a plain-language description of what changes for users
- Confirm whether the change is on by default or requires admin activation
- Include the production upgrade date
- Assign communication owner and send-by date (at least one week before production upgrade)
Missing this step means users encounter unexplained behavior changes in production.
```

**Detection hint:** A release readiness checklist that has no communication or notification step is incomplete regardless of how complete the technical steps are.
