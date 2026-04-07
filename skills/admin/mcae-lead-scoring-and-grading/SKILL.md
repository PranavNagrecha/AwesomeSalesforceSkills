---
name: mcae-lead-scoring-and-grading
description: "Use this skill when configuring MCAE (Account Engagement / Pardot) lead scoring models, grading profiles, score decay rules, or automation rules that fire on score/grade thresholds. Covers: scoring point values per activity, score decay for inactivity, Profiles for fit grading, combined MQL definitions (Score + Grade), and automation rules vs completion actions. NOT for Einstein Lead Scoring (Sales Cloud), not for Marketing Cloud Engagement journey scoring, not for Salesforce native lead scoring without Account Engagement."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "How do I set up lead scoring in Pardot or MCAE so that form fills and email clicks raise the score"
  - "How do I configure score decay in Account Engagement to reduce scores for inactive prospects"
  - "How do I use Profiles to grade prospects by job title, industry, and company size in MCAE"
  - "How do I create an automation rule to assign a lead to Sales when score reaches 100 and grade is B or above"
  - "What is the difference between a completion action and an automation rule for score-based lead routing"
tags:
  - mcae
  - pardot
  - account-engagement
  - lead-scoring
  - lead-grading
  - profiles
  - automation-rules
  - score-decay
  - mql
inputs:
  - "MCAE / Account Engagement org access (Business Unit configured)"
  - "List of activities to score (form fills, email clicks, page views, custom redirects, etc.) with agreed point values"
  - "Agreed MQL threshold: minimum score and minimum grade (e.g., score >= 100 AND grade >= B)"
  - "Ideal Customer Profile (ICP) criteria: job titles, industries, company sizes, geographies that indicate fit"
  - "Sales handoff SLA and assignment routing rules (queue or user)"
outputs:
  - "Configured MCAE scoring rules (default scoring category point values per activity type)"
  - "Score decay rules (decay period in days and point reduction per cycle)"
  - "One or more Profiles with positive/negative criteria for letter-grade assignment"
  - "Automation rules triggering alerts, field updates, or assignments at score/grade thresholds"
  - "Score and grade synced to Salesforce Lead/Contact fields for CRM-side reporting"
  - "Decision record documenting MQL definition, decay settings, and profile criteria rationale"
dependencies:
  - mcae-pardot-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# MCAE Lead Scoring and Grading

Use this skill to configure the MCAE (Account Engagement / Pardot) behavioral scoring model and fit-based grading system. It activates when a practitioner needs to set up or tune scoring rules, score decay, Profiles, automation rules tied to score/grade thresholds, or define the combined MQL trigger for sales handoff.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm MCAE Business Unit is provisioned.** Scoring and grading configuration lives inside the MCAE app, not in Salesforce Setup. Ensure the user has the Marketing role (or admin) in the MCAE Business Unit.
- **Confirm the sync field mapping is enabled.** MCAE score and grade are written to the `Score` (integer) and `Rating` or a custom field on Lead/Contact only when the CRM sync is active and the field mapping is configured. If the sync is off, CRM-side reporting on score/grade is impossible.
- **Clarify whether a default scoring model or custom scoring model is in use.** MCAE ships with a default scoring model that assigns fixed points to standard activities (e.g., form fill = 50, email click = 5, page view = 1). Custom scoring can override these globally or per-asset. Know which mode the org is starting from.
- **Establish the MQL definition up-front.** The most common production mistake is building scoring in isolation without agreeing what score+grade combination triggers handoff. Get alignment from Sales before configuring thresholds.
- **Score is a non-negative integer; grade is a letter A++ through F.** These are two separate dimensions. Automation rules can filter on either or both.

---

## Core Concepts

### 1. Scoring — Behavioral Engagement Dimension

Scoring measures how much a prospect has engaged with your marketing assets. It is a cumulative integer starting at 0. Points are added when a prospect performs a trackable activity and can be removed (deducted) for negative signals such as unsubscribing or opting out.

Default activity point values (configurable in MCAE > Admin > Scoring):

| Activity | Default Points |
|---|---|
| Form fill (submission) | +50 |
| Form fill (error) | +5 |
| Email link click | +5 |
| Email open | +1 |
| Page view (tracked) | +1 |
| Custom redirect click | +5 |
| File download | +5 |
| Webinar registration | +10 |
| Unsubscribe | -50 |
| Hard bounce | -75 |

Points are configurable globally under **Admin > Scoring**. Per-asset overrides are also possible (e.g., a high-intent pricing page can award more points than a generic blog visit). Custom activities and page view scoring require the MCAE tracking code (JavaScript snippet) on the web property.

Score is only meaningful in context of the prospect's activity recency — which is why decay rules exist.

### 2. Score Decay — Time-Based Score Reduction

Score decay automatically reduces a prospect's score over time to ensure that old engagement does not keep a prospect at MQL indefinitely. Decay rules are configured in **Admin > Scoring > Decay Scoring**.

Key behaviors:
- Decay fires on a periodic basis (not real-time); the platform checks for decay-eligible prospects on a scheduled cadence.
- A typical rule: "-10 points after 30 days of inactivity." Multiple decay rules can stack (e.g., -10 at 30 days AND -20 at 60 days).
- Decay does not reduce score below 0.
- Decay does not trigger completion actions or automation rules. It silently reduces the score.
- If a prospect re-engages (new activity), new points are added normally on top of the decayed score.

### 3. Grading — Fit Dimension via Profiles

Grading is an independent dimension from scoring. It measures how well a prospect matches your Ideal Customer Profile (ICP). Grade is a letter (A++ through F) assigned by matching the prospect's field values against a **Profile**.

A Profile contains criteria — each criterion specifies a field value match and a positive or negative grade point adjustment. MCAE converts the cumulative grade points into a letter grade. Criteria examples:

- Job Title contains "VP" → +20 grade points
- Job Title contains "Intern" → -20 grade points
- Industry = "Technology" → +10 grade points
- Annual Revenue > 10,000,000 → +10 grade points
- Country not in {US, CA, UK} → -10 grade points

Each prospect is matched against exactly one Profile (the matching profile is selected based on the prospect's field values; only one profile can be the "default"). Profile criteria are evaluated whenever the prospect's fields update or the prospect is synced.

The letter grade map (approximate): 100 = A++, 85 = A+, 70 = A, 55 = B+, 40 = B, 25 = C, etc. Exact thresholds are fixed by the platform.

### 4. Automation Rules vs. Completion Actions

These are two distinct mechanisms for triggering score/grade-based actions. Confusing them is a common source of missed leads or duplicate actions.

**Automation Rules** (Admin > Automation > Automation Rules):
- Evaluate ALL prospects in the database continuously in near-real-time.
- Can be retroactive: when a rule is activated, it evaluates every existing prospect who matches the criteria, not just future ones.
- Ideal for threshold-based routing: "Score >= 100 AND Grade >= B → Assign to Sales queue."
- Rules can be set to repeat (fire every time criteria are met after a reset) or fire once per prospect.
- Use Automation Rules for durable, ongoing logic.

**Completion Actions** (on forms, emails, files, custom redirects):
- Fire once, immediately after a specific activity occurs (e.g., after a form is submitted).
- Not retroactive. They only fire on the single event that triggered them.
- Ideal for immediate responses: "After form fill → Send autoresponder email" or "After form fill → Add to list."
- Do not use completion actions for score threshold routing — they fire on the activity event, not on the resulting score.

---

## Common Patterns

### Pattern 1: Combined MQL Definition (Score + Grade Gate)

**When to use:** Most B2B orgs should use both dimensions to qualify leads. Score alone misses low-fit contacts who happen to be very active; grade alone misses high-fit contacts who haven't engaged yet.

**How it works:**
1. Define the MQL threshold collaboratively with Sales: typically "Score >= 100 AND Grade >= B."
2. Build one Automation Rule with two criteria: `Prospect Score >= 100` AND `Prospect Grade is B or better`.
3. Set the action to: Assign to [Sales Queue or User] + Notify assigned user + Add to "MQL" list.
4. Set the rule to "repeat" only after the prospect's score drops below threshold (use score reset on recycle to prevent infinite reassignments).

**Why not Score alone:** Without a grade gate, marketing-active but low-fit prospects (competitors, students, wrong geography) flood the Sales queue with noise.

### Pattern 2: Score Decay to Reflect Recency

**When to use:** Any org where prospects accumulate score from old campaigns and remain MQL-eligible indefinitely even after going dark.

**How it works:**
1. Go to Admin > Scoring > Decay Scoring.
2. Add a rule: Reduce score by 10 points after 30 days of inactivity.
3. Optionally add a second rule: Reduce score by 20 points after 60 days of inactivity (stacks with first rule).
4. Audit the MQL threshold — if decay is in place, the threshold should reflect expected score ranges for recently active prospects.

**Why not rely on list management alone:** Manual list cleanup is error-prone and creates data quality debt. Decay is automated and keeps scores reflective of actual recency without admin intervention.

### Pattern 3: Profile Criteria for Multi-Segment Grading

**When to use:** Orgs with multiple ICP segments (e.g., SMB vs. Enterprise, Healthcare vs. Technology) where fit criteria differ by segment.

**How it works:**
1. Create a separate Profile for each ICP segment (e.g., "Enterprise Technology" and "SMB Healthcare").
2. Add matching criteria to each profile. Use the default Profile as a catch-all for prospects that don't match any segment-specific profile.
3. The profile with the most matching criteria for a given prospect is automatically selected.
4. Grade thresholds in the MQL automation rule apply across all profiles — the letter grade is normalized regardless of which profile was used.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to route a prospect to Sales when they hit a score+grade threshold | Automation Rule with score AND grade criteria | Automation rules evaluate continuously; completion actions fire only on a single event |
| Need to send an immediate follow-up email after a form fill | Completion Action on the form | Real-time, event-scoped; no need to evaluate the whole database |
| Prospects are staying MQL-eligible from old campaigns | Score Decay rules (30-day and 60-day) | Automated recency signaling without manual cleanup |
| Multiple ICP segments with different fit criteria | Multiple Profiles with segment-specific criteria | One Profile per segment; platform selects best match per prospect |
| Sales complains about low-quality leads in queue | Add or tighten grade gate in MQL automation rule | Grade filters out high-engagement, low-fit contacts |
| Admin wants to manually promote a prospect to MQL | Manual score/grade override in MCAE prospect record | Override blocks automatic re-scoring; document the override reason |
| Custom web activity (e.g., pricing page) should score higher | Per-asset score override on the specific page/form | Global score rules still apply to all other assets |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm prerequisites.** Verify that the MCAE Business Unit is connected to the Salesforce CRM and that the Score and Grade fields are mapped in the connector field mapping. Without this, score/grade changes never reach Lead/Contact records.

2. **Document the MQL definition.** Before touching any configuration, capture the agreed score threshold and grade threshold in writing (e.g., "Score >= 100 AND Grade >= B"). Get explicit sign-off from Sales. Record this in the work template.

3. **Configure global scoring rules.** Go to MCAE Admin > Scoring. Review and adjust the default point values for each activity type to reflect the org's priorities. Document the final point table. Add per-asset score overrides for high-intent assets (e.g., pricing page, demo request form).

4. **Set up score decay.** Go to Admin > Scoring > Decay Scoring. Configure at minimum one decay rule (e.g., -10 points after 30 days of inactivity). Add a second rule for 60 days if the sales cycle is long. Verify that the MQL threshold is still achievable with decay in place.

5. **Build Profiles for grading.** Go to Admin > Profiles. Create a profile for each ICP segment. Add positive criteria for strong fit signals (job title, industry, company size) and negative criteria for disqualifying signals (competitors, wrong geography, student roles). Set one Profile as the default catch-all.

6. **Create the MQL Automation Rule.** Go to Automation > Automation Rules. Create a rule with criteria: Score >= [threshold] AND Grade >= [letter]. Set the action: Assign to [Sales queue], notify [Sales user or group], add to [MQL Salesforce Campaign or list]. Set the rule to "repeat" and decide the reset logic (e.g., reset if prospect score drops below threshold).

7. **Test and validate.** Create a test prospect. Simulate activities (form fill, page view, email click) and confirm score increments correctly. Verify decay fires on schedule. Check that the automation rule fires when threshold is crossed and that Score and Grade appear on the synced Lead/Contact record in CRM.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Score and Grade fields are mapped in the MCAE CRM connector field mapping
- [ ] Global scoring point values are documented and approved by Marketing
- [ ] At least one score decay rule is active (decay period and point reduction documented)
- [ ] At least one Profile exists with both positive and negative criteria for each major ICP segment
- [ ] MQL Automation Rule is active with both score AND grade criteria
- [ ] Automation Rule action assigns to the correct queue or user and sends a notification
- [ ] Automation Rule repeat/reset behavior is explicitly configured (not left at default without review)
- [ ] Test prospect confirms score increments, decay fires, grade updates, and automation rule triggers
- [ ] Score and Grade values appear on Lead/Contact records in CRM after sync
- [ ] Manual override behavior is documented and communicated to admin team

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Manual override blocks automatic re-scoring** — When an admin manually overrides a prospect's score or grade in the MCAE UI, MCAE marks that record as manually overridden and stops updating it automatically. Future activities do not change the score. This is a silent block — there is no UI indicator visible to other admins. Teams discover the problem when a re-engaged prospect never moves through scoring. Fix: document the override policy and review override records regularly.

2. **Automation Rules are retroactive by default** — When you activate a new Automation Rule, MCAE immediately evaluates all existing prospects against the rule criteria, not just new prospects going forward. If your rule assigns leads to Sales, activating it can flood the Sales queue with thousands of existing prospects at once. Fix: before activating a threshold-based rule on an existing database, filter by a "date created after X" criterion or run the rule in a lower-impact test segment first.

3. **Score decay does not trigger Automation Rules** — Score decay silently reduces scores without firing completion actions or re-evaluating automation rules. If a prospect was above your MQL threshold and decay drops them below it, no rule fires to notify Sales or remove the prospect from the MQL list. You must build a separate recycling rule to handle score-drop scenarios, or rely on periodic CRM-side reporting.

4. **Prospect score and grade sync is one-way (MCAE → CRM) by default** — Score and Grade flow from MCAE to the Lead/Contact fields in Salesforce. If a CRM workflow or flow overwrites the Score field on the Lead record, that change is not reflected back in MCAE. This creates divergence between MCAE score and CRM-visible score. Fix: protect the Score and Grade fields on Lead/Contact with field-level security or validation rules to prevent non-MCAE writes.

5. **Profile matching is based on the best-fit profile, not an explicit assignment** — MCAE automatically selects the profile for each prospect based on how many criteria match. If a prospect matches criteria from multiple profiles equally, the behavior is non-deterministic. Avoid overlapping criteria across profiles. Always have one clearly designated default profile as a catch-all.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Scoring point table | Documented list of activity types and their configured point values (filled in the work template) |
| Score decay rules | Active decay rules with period and point-reduction values |
| Profile definitions | One profile per ICP segment listing all positive and negative criteria |
| MQL Automation Rule | Active rule with score+grade criteria and assignment/notification actions |
| CRM field mapping confirmation | Evidence that Score and Grade fields are mapped in the MCAE connector |
| MQL definition document | Signed-off record of the score threshold, grade threshold, and reset logic |

---

## Related Skills

- admin/lead-scoring-requirements — Use first to gather and document scoring requirements before configuring MCAE; this skill covers requirements gathering, not MCAE-specific configuration
- admin/mcae-pardot-setup — Required prerequisite for Business Unit provisioning and CRM connector setup before scoring can be configured
- admin/marketing-cloud-connect — Relevant if the org also uses Marketing Cloud Engagement alongside MCAE
