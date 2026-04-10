---
name: lead-nurture-journey-design
description: "Use this skill when designing or configuring lead nurture journeys in MCAE (Account Engagement / Pardot) Engagement Studio — including mapping content to funnel stages, defining behavioral trigger rules, building branching program paths, and establishing MQL handoff criteria. Covers funnel stage mapping (Awareness, Consideration, Decision), Engagement Studio program structure, rule-based branching on score/grade/activity, content inventory prerequisites, and program execution schedule. NOT for Journey Builder implementation in Marketing Cloud Engagement (MCE), NOT for Sales Engagement cadences in Sales Cloud, NOT for Einstein Lead Scoring configuration, NOT for initial MCAE Business Unit setup or CRM connector provisioning."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Scalability
triggers:
  - "How do I build a lead nurture program in MCAE Engagement Studio that branches based on email clicks and form fills"
  - "How do I map content to different funnel stages so that prospects receive awareness emails first and decision-stage offers later"
  - "My nurture emails are sending to everyone at the same pace regardless of prospect behavior — how do I add branching logic"
  - "How do I use behavioral triggers like page visits and score thresholds to move prospects between nurture tracks"
  - "How do I design an Engagement Studio program that hands off MQL-ready prospects to Sales automatically"
  - "What is the correct order of steps for setting up a lead nurture journey before I touch Engagement Studio"
tags:
  - mcae
  - pardot
  - account-engagement
  - engagement-studio
  - lead-nurture
  - nurture-journey
  - drip-program
  - behavioral-triggers
  - funnel-stages
  - mql
  - content-mapping
inputs:
  - "MCAE Business Unit provisioned and CRM connector active (see mcae-pardot-setup skill)"
  - "Documented content inventory: list of existing marketing assets mapped to buyer funnel stages (Awareness, Consideration, Decision)"
  - "Agreed MQL definition: score threshold and grade threshold that triggers sales handoff"
  - "Defined prospect entry criteria: list or segment that gates who enters the program"
  - "Agreed branching logic: which prospect behaviors (email click, form fill, page visit, score change) should change the path"
  - "Sales handoff SLA and notification preference (task creation, email alert, or CRM queue assignment)"
outputs:
  - "Engagement Studio program with stage-mapped email sends and rule-based branching"
  - "Funnel stage content map: table linking Awareness / Consideration / Decision assets to program steps"
  - "Documented program entry/exit criteria and suppression list policy"
  - "MQL handoff automation (notify user or assign to queue at score+grade threshold)"
  - "Program execution schedule and expected cadence documented"
  - "Decision record: chosen branching triggers, wait periods, and suppression rules with rationale"
dependencies:
  - mcae-pardot-setup
  - mcae-lead-scoring-and-grading
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Lead Nurture Journey Design

Use this skill to design and configure MCAE Engagement Studio lead nurture programs — from pre-program content inventory and funnel-stage mapping through behavioral trigger rules, branching path construction, and MQL handoff automation. It activates when a practitioner needs to build a multi-step nurture sequence that responds to prospect behavior rather than sending identical emails to all recipients on a fixed schedule.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm a content inventory exists before touching Engagement Studio.** The most common failure mode is opening Engagement Studio before knowing what emails to send at each stage. The program skeleton is meaningless without content mapped to Awareness, Consideration, and Decision stages. Require a documented content map as a prerequisite.
- **Confirm the MQL definition is agreed.** Score threshold and grade threshold must be signed off by Sales before the program is built. The program's exit trigger and handoff action depend entirely on this number.
- **Understand program execution frequency.** Engagement Studio programs run on a weekly cadence by default — they are not real-time. Steps with "Wait" timers are evaluated once per week. Prospects who take an action on Tuesday will not be re-evaluated until the next weekly run. If real-time response is required for a specific step, a separate Automation Rule or Completion Action must handle it outside the program.
- **Identify the entry list or dynamic list.** Programs require a prospect list as the entry source. Static lists allow bulk entry; dynamic lists continuously add prospects who meet criteria. Know which is correct before building.
- **Clarify suppression requirements.** Determine which prospects must be excluded: existing customers, competitors, already-MQL records, opted-out prospects. Suppression is configured at the program level and cannot be applied per step.

---

## Core Concepts

### 1. Funnel Stage Content Mapping

Before any Engagement Studio program is configured, existing content must be mapped to the three buyer funnel stages:

- **Awareness** — Educational content with no sales pressure. Goal: build trust and brand familiarity. Examples: blog posts, how-to guides, industry reports, educational webinar invitations.
- **Consideration** — Comparative content that helps the prospect evaluate solutions. Goal: establish differentiation. Examples: product comparison guides, case studies, ROI calculators, product-specific webinar invitations.
- **Decision** — Conversion-focused content targeting prospects close to purchase. Goal: remove friction from the buying decision. Examples: free trial offers, demo request CTAs, pricing pages, customer testimonials, sales call scheduling links.

A content inventory audit is mandatory before program construction. Every email send in the program must correspond to a specific asset at the correct stage. Sending Decision-stage content to an Awareness prospect destroys trust and increases unsubscribes. Sending Awareness content to a Decision-stage prospect stalls the pipeline.

### 2. Engagement Studio Program Structure

An Engagement Studio program is a visual canvas of sequential steps. The available step types are:

| Step Type | Purpose |
|---|---|
| **Wait** | Pause execution for a defined number of days before evaluating the next step |
| **Send Email** | Send a specific MCAE email template to the prospect |
| **Add to List** | Add the prospect to a static or dynamic list |
| **Remove from List** | Remove the prospect from a list (e.g., remove from a cold list when re-engaged) |
| **Notify User** | Send an internal email notification to a Salesforce user or group |
| **Change Prospect Field** | Update a field value on the prospect record (e.g., set "Nurture Stage" custom field) |
| **Create Task** | Create a Salesforce task assigned to a user or queue |
| **Add Tag** | Apply a tag to the prospect record for segmentation |

Steps are evaluated in sequence. **Rules** (conditional checks) create branching: a rule evaluates a condition and routes the prospect down a "Yes" path or a "No" path. Rules can check: prospect score, prospect grade, list membership, email open, email click, form submission, page view, custom field values.

The critical distinction between a simple drip sequence and a behavioral nurture program is the presence of **rule steps with branching**. Without rules, all prospects receive the same emails in the same order regardless of their behavior — equivalent to a time-based drip with no intelligence.

### 3. Behavioral Triggers and Branching

Behavioral triggers are the differentiating feature of Engagement Studio programs. Rather than advancing all prospects on a fixed timer, rules evaluate specific prospect behaviors and route each prospect accordingly.

Common trigger patterns:

- **Email click trigger:** After sending an email, add a Wait step, then a Rule: "Prospect clicked email X." Yes path → advance to next stage content. No path → send a re-engagement variation or hold.
- **Form submission trigger:** After sending a gated content offer, Rule: "Prospect submitted form Y." Yes path → advance to Consideration stage. No path → send a different Awareness asset.
- **Page visit trigger:** Rule: "Prospect visited [specific URL]." Yes path → escalate to Decision stage content. No path → continue Consideration track.
- **Score threshold trigger:** Rule: "Prospect score >= [MQL threshold]." Yes path → Notify User step + Create Task step for Sales. No path → continue nurture.
- **Grade trigger:** Rule: "Prospect grade >= B." Yes path → combine with score check for MQL handoff.

Wait periods between Send and Rule steps are critical. A Wait of at least 3–5 days after a Send Email step ensures the prospect has time to open and click before the rule evaluates. Evaluating a rule on the same day as the send captures near-zero engagement.

### 4. Program Execution Schedule and MQL Handoff

**Execution schedule:** Engagement Studio programs evaluate steps on a weekly cadence, not real-time. Each prospect advances through one "step evaluation" per program run. This means a 5-step program with 7-day Wait periods takes a minimum of 5 weeks to complete — but because of weekly evaluation, actual elapsed time may be longer. Design Wait periods with this in mind: a 3-day Wait configured in the program may behave as a 7-day wait in practice depending on when the weekly run occurs.

**Real-time actions:** For actions that must happen immediately (e.g., "Send confirmation email the moment a form is submitted"), use Completion Actions on the form, not Engagement Studio steps. Completion Actions fire immediately at activity time.

**MQL handoff in the program:** The program's Score threshold rule should trigger a "Notify User" or "Create Task" step at the point where the prospect crosses the MQL threshold. However, the definitive MQL routing should also be backed by a standalone Automation Rule outside the program, because:
1. The program runs weekly — a threshold crossed mid-week will not trigger until the next run.
2. Prospects who enter MQL status through channels outside the program (direct form fills, event registration) will not be covered by a program-only handoff.

---

## Common Patterns

### Pattern 1: Stage-Gated Nurture with Behavioral Advancement

**When to use:** B2B orgs with a multi-stage content library where prospects should advance from Awareness to Consideration to Decision based on demonstrated engagement, not elapsed time.

**How it works:**
1. Prospect enters program via an Awareness dynamic list (e.g., "Recently scored prospect, grade >= C, not yet MQL").
2. **Week 1:** Send Awareness email (educational guide). Wait 5 days.
3. **Rule:** Did prospect click the email? Yes → advance to Consideration track. No → send second Awareness asset.
4. **Week 3 (Consideration track):** Send Consideration email (case study). Wait 5 days.
5. **Rule:** Did prospect submit the case study form? Yes → advance to Decision track. No → send alternative Consideration asset.
6. **Decision track:** Send Decision email (demo request CTA). Wait 3 days.
7. **Rule:** Prospect score >= MQL threshold? Yes → Notify Sales user + Create Task. No → Add to "Long-term nurture" list and exit.

**Why not a simple drip:** A time-based drip sends the demo CTA to a prospect who never opened the first email, wasting a high-value conversion asset and signaling irrelevance to a cold prospect.

### Pattern 2: Re-engagement Program for Cold Prospects

**When to use:** Prospects in the database who have not engaged in 60+ days, have decayed scores, and need a targeted re-engagement sequence before being recycled or suppressed.

**How it works:**
1. Entry list: Dynamic list "Prospect score <= 20 AND last activity > 60 days ago AND opted in."
2. **Step 1:** Send re-engagement email: "We miss you — here's our latest [resource]." Wait 7 days.
3. **Rule:** Did prospect open or click? Yes → Remove from re-engagement list, add to standard nurture list, exit program. No → continue.
4. **Step 2:** Send final re-engagement with a stronger offer. Wait 7 days.
5. **Rule:** Any engagement? Yes → move to nurture. No → Change Prospect Field "Marketing Status" = "Dormant," add to suppression list, exit program.

**Why not suppress immediately:** Cold prospects occasionally re-engage with the right content. A two-step re-engagement sequence recovers a meaningful percentage before writing off the record.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to send emails on a fixed timer regardless of prospect behavior | Simple drip (list email, not Engagement Studio) | Engagement Studio overhead is unnecessary if no branching is required |
| Need to advance prospects based on email clicks or form fills | Engagement Studio with Rule steps after each Send | Rule-based branching is Engagement Studio's core differentiator |
| Need to send an immediate autoresponder after a form fill | Completion Action on the form, not a program step | Completion Actions are real-time; programs evaluate weekly |
| Need to hand off MQL-ready prospects to Sales from within the program | Notify User + Create Task steps triggered by Score rule | Also back this with a standalone Automation Rule for prospects who reach MQL outside the program |
| No content inventory exists yet | Stop — do not open Engagement Studio | Building a program without content mapping produces a skeleton that must be rebuilt; content map is mandatory first |
| Need to nurture multiple ICP segments with different content | Separate programs per segment, or a single program with grade-based branching early in the flow | Mixing segments in one undifferentiated program sends irrelevant content and inflates unsubscribes |
| Prospect behavior must trigger an instant sales alert | Standalone Automation Rule or Completion Action | Programs check weekly; use real-time automation for time-sensitive alerts |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Audit the content inventory.** Before any Engagement Studio configuration, produce a table mapping every available marketing asset (email, guide, webinar, case study, CTA page) to its funnel stage (Awareness, Consideration, Decision). Identify gaps — stages with no content must be filled before the program is built. Record the content map in the work template.

2. **Confirm the MQL definition and entry criteria.** Document the agreed score threshold and grade threshold for MQL handoff. Define the entry criteria for the program (e.g., "Prospect score >= 25, grade >= C, not already MQL, opted in"). Define the suppression list (existing customers, competitors, opted-out, already-MQL records). Get explicit sign-off from Sales and Marketing before proceeding.

3. **Design the program flow on paper before building.** Sketch the full branching tree: which email is sent at each stage, what rule follows each send, what each Yes/No branch does. Define Wait periods (minimum 3–5 days after each Send Email step). Identify where the MQL handoff step lives in the flow. This design document prevents rework inside Engagement Studio.

4. **Build the Engagement Studio program.** In MCAE > Engagement Studio, create a new program. Assign the entry list and suppression list. Add steps following the approved design: Send Email → Wait → Rule → branch. Use Change Prospect Field steps to track nurture stage progression (e.g., set a "Nurture Stage" field to "Awareness," "Consideration," "Decision"). Add the MQL handoff steps (Notify User, Create Task) at the score/grade rule branch.

5. **Configure the companion Automation Rule for MQL handoff.** Outside the program, create an Automation Rule that fires independently when Prospect Score >= [threshold] AND Grade >= [letter]. Set the action to assign to the Sales queue and notify the assigned user. This ensures prospects who cross MQL threshold through paths outside the program are also handed off without delay.

6. **Test with a seed prospect.** Create a test prospect record. Add it to the entry list. Step through each stage manually (submit forms, click tracked links) to confirm rule evaluations route correctly. Verify that the "Nurture Stage" field updates at each branch. Confirm that reaching the MQL rule triggers the Notify User and Create Task steps. Validate that the test prospect's score and grade appear on the synced Lead/Contact record in CRM.

7. **Activate and document.** Activate the program. Record the program name, entry list, suppression list, step count, expected cadence, and MQL handoff logic in the decision record. Share with Marketing and Sales so both teams understand when and how prospects enter, advance, and exit.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Content inventory audit is complete and every email send in the program maps to a documented asset at the correct funnel stage
- [ ] Entry list and suppression list are configured and reviewed for accuracy (no existing customers or opted-out records in entry list)
- [ ] Every Send Email step is followed by a Wait step of at least 3 days before the next Rule evaluation
- [ ] Rule steps use behavioral triggers (click, open, form submit, page visit) or score/grade conditions — not just time-based advancement
- [ ] MQL handoff is covered by both a program-internal Rule step and a standalone Automation Rule
- [ ] A "Change Prospect Field" or "Add Tag" step tracks nurture stage progression for reporting
- [ ] Program execution schedule is documented and stakeholders understand the weekly cadence (not real-time)
- [ ] Test prospect confirmed correct routing through at least one Yes branch and one No branch
- [ ] Score and grade values appear on the synced Lead/Contact record in CRM after program handoff
- [ ] Decision record is complete: entry criteria, suppression policy, branching logic, MQL threshold, and program cadence

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Programs evaluate on a weekly schedule, not in real time** — Engagement Studio programs process steps once per week. A prospect who clicks an email on Monday will not be evaluated by the rule that follows the send until the next weekly run. Teams expecting same-day follow-up are frequently surprised. The fix is to use Completion Actions or Automation Rules for any step that must fire within minutes or hours of a prospect action.

2. **A prospect can only be in one program at a time by default** — If a prospect is already active in Program A, adding them to Program B's entry list has no effect until they exit Program A. Overlapping programs silently drop the new entry. Design program exit criteria carefully (score threshold exit, end-of-program exit, manual removal) and document which program takes priority for each prospect segment.

3. **Rule steps check the condition at evaluation time, not at the time the triggering action occurred** — If a prospect clicked an email three weeks ago, and the rule evaluates this week, the rule still fires "Yes" — because the platform checks historical activity within the evaluation window. This can cause unexpected "Yes" branches for old behavior. Set explicit time windows in rule criteria where precision matters (e.g., "Clicked email within the last 7 days").

4. **Changing a program's steps while it is active can strand prospects mid-flow** — If you modify a running program (add, remove, or reorder steps), prospects currently waiting between steps may be re-evaluated against the new structure or skip steps entirely. Pause the program before editing, make changes, verify the prospect queue state, then reactivate.

5. **Prospects who exit the program do not automatically receive follow-on communication** — When a prospect exits (either by reaching the end, being removed from the entry list, or manually exited), no action fires. If the intended next action after exit is a Sales task or a CRM campaign assignment, that must be an explicit program step before the exit point or handled by a separate Automation Rule that fires on the exit condition.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Content inventory and funnel-stage map | Table of all marketing assets mapped to Awareness / Consideration / Decision stages, confirming no stage gaps |
| Engagement Studio program | Configured program with send, wait, rule, and action steps following the approved design |
| Program decision record | Documents entry list, suppression list, branching trigger logic, wait periods, MQL threshold, and execution cadence |
| Standalone MQL Automation Rule | Backs up the program-internal MQL handoff for prospects who cross threshold outside the program |
| Nurture stage field or tag convention | Custom field or tag scheme tracking which funnel stage each prospect has reached, enabling pipeline reporting |

---

## Related Skills

- admin/mcae-pardot-setup — Required prerequisite; Business Unit and CRM connector must be provisioned before Engagement Studio programs can be built
- admin/mcae-lead-scoring-and-grading — Required prerequisite; score and grade thresholds driving MQL handoff must be configured before the program's rule steps are meaningful
- admin/marketing-cloud-engagement-setup — Use instead if the org is on Marketing Cloud Engagement (MCE) and needs Journey Builder; this skill covers MCAE Engagement Studio only
