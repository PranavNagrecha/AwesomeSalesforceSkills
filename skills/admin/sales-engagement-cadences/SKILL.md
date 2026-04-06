---
name: sales-engagement-cadences
description: "Use when setting up, configuring, or troubleshooting Salesforce Sales Engagement (formerly High Velocity Sales) cadences, call scripts, email templates, work queue, or rep assignment. Triggers: 'cadence builder', 'HVS cadence', 'work queue steps', 'sales engagement setup', 'sequence steps not appearing', 'cadence not sending email', 'Sales Engagement permission set'. NOT for Marketing Cloud campaigns, Marketing Cloud Account Engagement (Pardot) journeys, or custom Apex email services."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Scalability
triggers:
  - "cadence steps not showing up in rep's work queue"
  - "how do I set up Sales Engagement cadences in my org"
  - "reps can't add prospects to cadence or call isn't logging"
  - "email in cadence not sending or wrong template used"
  - "Sales Engagement High Velocity Sales setup permission set dialer"
tags:
  - sales-engagement
  - cadences
  - high-velocity-sales
  - work-queue
  - call-scripts
  - email-templates
  - cadence-builder
inputs:
  - "Sales Cloud edition (Unlimited, Enterprise, Professional) and whether Sales Engagement add-on is provisioned"
  - "Current Sales Engagement feature flag status (Setup > Sales Engagement Settings)"
  - "Permission sets assigned to reps and managers"
  - "Desired cadence structure: step types (Email, Call, LinkedIn, Custom), branching tracks, step delays"
  - "Email templates and call scripts to be used in cadence steps"
outputs:
  - "Cadence configuration guidance and step design"
  - "Permission set assignment plan for reps and managers"
  - "Work Queue troubleshooting findings"
  - "Email template and call script integration guidance"
  - "Org limit assessment (active targets, tracker limits)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

You are a Salesforce Admin expert in Sales Engagement cadence setup, configuration, and troubleshooting. Your goal is to ensure reps have a working, well-structured cadence experience with correct permissions, templates, and work queue visibility — without hitting org limits or creating unmaintainable step sprawl.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first. Only ask for information not covered there.

Gather if not available:

- Is Sales Engagement (formerly High Velocity Sales) enabled under Setup > Sales Engagement Settings? Bundled with Sales Cloud Unlimited; add-on required for Professional/Enterprise.
- Which permission sets are currently assigned to reps and managers? Reps need "Sales Engagement User" and managers need "Sales Engagement Manager."
- What step types are needed (Email, Call, LinkedIn, Wait, Custom)? Does the cadence require branching (main, positive, negative tracks)?
- Are email templates and call scripts already created, or do they need to be built as part of this work?
- What are the target objects — Leads, Contacts, or both? Are Person Accounts in scope?
- Is the built-in dialer configured? Outbound calls require dialer setup before Call steps work.
- Are org limits a concern? Org-wide active target cap is 500,000 records; active tracker limit is 150,000. Large deployments must plan against these.

---

## Core Concepts

### Cadence Builder 2.0

Sales Engagement uses Cadence Builder 2.0 — a drag-and-drop interface at Setup > Sales Engagement > Cadences. Each cadence is a multi-step sequence with up to three branching tracks:

- **Main track** — default path for all prospects
- **Positive track** — triggered by a positive engagement signal (e.g., email reply, call answered)
- **Negative track** — triggered by a negative signal (e.g., email bounced, call declined)

Track branching is signal-driven. The signals that trigger branch transitions are configured per-step and depend on the step type (Email vs. Call steps surface different signal options). Custom steps do not generate automatic engagement signals.

### Step Types and Their Constraints

Five step types are available:

| Step Type | What It Does | Key Constraint |
|-----------|-------------|---------------|
| Email | Sends a templated email to the prospect | Template must target the prospect's email field; HTML templates require Classic Email Builder |
| Call | Surfaces a call task with optional call script | Requires built-in Salesforce dialer or CTI; call logging must be configured |
| LinkedIn | Creates a LinkedIn outreach task | Requires LinkedIn Sales Navigator integration enabled |
| Wait | Introduces a delay (hours or days) between steps | Minimum delay is 1 hour |
| Custom | Creates a generic task for any rep action | No automatic engagement signal; branching must be manually triggered |

### Work Queue and Rep Experience

The Work Queue (available in the Sales Console app or via the Work Queue component on record pages) surfaces all due cadence steps for a rep's assigned prospects. Reps complete steps directly from the queue; completion logs activity automatically.

The Work Queue is also embeddable in Outlook and Gmail via the Salesforce Inbox integration. Steps only appear in the queue when they are due — future steps are not surfaced early. If a step appears stuck, check whether the preceding step was completed or whether the prospect was paused by the system due to an engagement signal.

---

## Common Patterns

### Pattern: Standard New-Hire Outreach Cadence

**When to use:** A sales team wants a consistent multi-step outreach sequence for new leads — typically Email → Wait → Call → Wait → Email → Call across 10–14 days.

**How it works:**
1. Create email templates in Setup > Classic Email Templates or Lightning Email Templates depending on cadence step requirements.
2. Create call scripts in Setup > Sales Engagement > Call Scripts.
3. Open Cadence Builder, create a new cadence, name it, and set the target object (Lead or Contact).
4. Add steps in order: Email (Day 1) → Wait (2 days) → Call with script (Day 3) → Wait (2 days) → Email (Day 5) → Call (Day 7).
5. Configure positive track: if a prospect replies to the first email, branch to a lighter follow-up track with 1 Call step.
6. Configure negative track: if email bounces, branch to a task for the rep to update contact info.
7. Activate the cadence and assign it to reps via permission and cadence visibility settings.

**Why not ad hoc tasks:** Unstructured manual tasks have no sequence enforcement, no engagement signal routing, and no visibility in the Work Queue. Reps skip steps inconsistently.

### Pattern: Troubleshooting Missing Work Queue Steps

**When to use:** Reps report that expected cadence steps are not appearing in their Work Queue.

**How it works:**
1. Confirm the rep has the "Sales Engagement User" permission set assigned.
2. Confirm the prospect record is actively enrolled in the cadence and not paused — check the Cadence related list on the Lead or Contact record.
3. Confirm the current step is due. Steps only surface when their delay has elapsed.
4. Check whether the preceding step was completed. If a prior step is incomplete, subsequent steps do not advance.
5. Check whether the prospect has exceeded the per-rep active target assignment or the org-wide limit.
6. If email steps are missing, confirm the prospect has a valid email address populated; Sales Engagement skips email steps silently if the target email field is blank.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Repeatable outbound sequence for SDR team | Cadence with Email + Call + Wait steps | Enforces sequence discipline, surfaces steps automatically |
| Personalized outreach with rep discretion | Cadence with Custom steps and clear call scripts | Keeps structure without locking message; rep adapts content |
| Large-scale drip to 100k+ records | Validate against org limits before deploy; consider Marketing Cloud | Org active target cap is 500,000 but tracker limit is 150,000 |
| Follow-up after a meeting | Single-track cadence with 2–3 steps only | Simpler is better; branching adds overhead not warranted for short sequences |
| LinkedIn outreach steps needed | Enable LinkedIn Sales Navigator integration first | LinkedIn steps will not work without the integration |
| Rep uses Gmail or Outlook | Configure Salesforce Inbox for Work Queue embedding | Reps can complete steps without switching to Salesforce |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Confirm feature enablement and licensing** — Verify Sales Engagement is enabled under Setup > Sales Engagement Settings. Confirm the org edition (Unlimited includes it; Professional/Enterprise require add-on). Check that dialer is configured if Call steps are required.
2. **Assign permission sets** — Assign "Sales Engagement User" to all reps who will use the Work Queue. Assign "Sales Engagement Manager" to team leads who create and manage cadences. Do not skip this; no permission set means no Work Queue access.
3. **Build supporting assets** — Create email templates and call scripts before building cadences. Cadence Builder references these; building them first avoids dead steps.
4. **Design and activate cadences** — Open Cadence Builder, create cadences for each outreach motion, add steps in the correct order, configure branching tracks, and activate. Test with a sandbox prospect record before activating for the full team.
5. **Validate rep experience** — Log in as a test rep, enroll a prospect in the cadence, confirm steps appear in the Work Queue at the expected times, and complete a step to verify activity logging.
6. **Monitor org limits** — After initial deployment, review active target counts against the 500,000 org-wide cap and 150,000 tracker limit. Build a cadence governance process so stale cadences and completed prospects are removed regularly.
7. **Document and train** — Update cadence names and descriptions to reflect the intended sales motion. Train reps on Work Queue completion discipline — cadences only advance when steps are marked complete.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Sales Engagement is enabled in Setup and the correct license or add-on is provisioned
- [ ] "Sales Engagement User" permission set is assigned to all reps; "Sales Engagement Manager" to team leads
- [ ] All email templates referenced in cadence steps exist and render correctly with valid merge fields
- [ ] All call scripts referenced in Call steps exist and reflect current messaging
- [ ] Cadence branching tracks (positive, negative) are configured where engagement signal routing is needed
- [ ] Cadences are activated and a test prospect has been enrolled and stepped through the Work Queue
- [ ] Org-wide active target count and tracker limit have been reviewed against current and projected volume
- [ ] LinkedIn Sales Navigator integration is enabled if LinkedIn steps are used

---

## Salesforce-Specific Gotchas

1. **Email steps silently skip if the target email field is blank** — If a Lead or Contact has no email address, Sales Engagement skips the email step without notifying the rep or logging a failure. The prospect silently advances or stalls with no visible error in the Work Queue. Always validate that prospects have populated email fields before enrolling them in email-heavy cadences.

2. **Classic vs. Lightning Email Template compatibility** — Cadence email steps support both Classic HTML email templates and Lightning Email Templates, but they are not interchangeable within the same step. Using a Lightning Email Template in an older cadence built for Classic templates can cause render failures. Audit template type consistency when migrating or cloning cadences.

3. **Dialer must be configured before Call steps surface correctly** — If the built-in Salesforce dialer or a connected CTI is not configured, Call steps appear in the Work Queue but clicking them does not initiate a call. Reps see the step but cannot complete it properly. Set up the dialer under Setup > Sales Engagement > Dialer before creating Call steps.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Cadence configuration guidance | Step sequence design, branching track logic, and activation checklist |
| Permission set assignment plan | Which permission sets to assign and to whom, based on role (rep vs. manager) |
| Work Queue troubleshooting findings | Root cause and resolution path for missing or stuck queue steps |
| Email template and call script integration notes | Template type compatibility, merge field recommendations, and script structure |
| Org limit assessment | Current vs. limit comparison for active targets and trackers |

---

## Related Skills

- **admin/email-templates-and-alerts** — Use when the email templates referenced in cadence steps have design, merge-field, or sender identity issues. NOT for cadence step configuration itself.
- **admin/lead-management-and-conversion** — Use when the Lead lifecycle intersects with cadence enrollment decisions. NOT for cadence builder configuration.
- **admin/connected-apps-and-auth** — Use when the Salesforce Inbox or dialer integration requires OAuth or connected app setup. NOT for cadence step design.
