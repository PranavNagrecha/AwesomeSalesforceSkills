# Examples — Sales Engagement Cadences

## Example 1: Setting Up a 7-Day SDR Outreach Cadence

**Context:** A new SDR team needs a structured outreach cadence for inbound leads. The goal is 6 touchpoints over 7 days combining email and calls, with a positive branch for replied leads and a negative branch for bounces.

**Problem:** Without a cadence, reps send emails and calls ad hoc. Some leads get 5 contacts in a day; others get none. There is no engagement signal routing, so a rep who calls a lead who already replied does not know the lead is warm.

**Solution:**

```
Cadence: Inbound-Lead-7Day
Target object: Lead

Main track:
  Step 1 — Email (Day 1)
    Template: Inbound-Welcome-Email
    Positive signal: Email replied -> jump to Positive track
    Negative signal: Email bounced -> jump to Negative track

  Step 2 — Wait (1 day)

  Step 3 — Call (Day 2)
    Script: Intro-Call-Script
    Positive signal: Call answered -> jump to Positive track

  Step 4 — Wait (2 days)

  Step 5 — Email (Day 4)
    Template: Inbound-Follow-Up-Email

  Step 6 — Wait (1 day)

  Step 7 — Call (Day 5)
    Script: Follow-Up-Call-Script

  Step 8 — Wait (2 days)

  Step 9 — Email (Day 7)
    Template: Inbound-Last-Attempt-Email

Positive track:
  Step 1 — Wait (1 day)
  Step 2 — Call (Day 2)
    Script: Warm-Lead-Call-Script

Negative track:
  Step 1 — Custom task: "Update Lead email address and re-enroll if valid"
```

**Why it works:** Branching ensures warm leads get a call, not another generic email. Bounced leads trigger a data quality task instead of more failed sends. The Wait steps enforce minimum delay so the sequence does not fire all touchpoints in one day.

---

## Example 2: Troubleshooting a Rep Reporting No Steps in Work Queue

**Context:** A rep has been assigned 20 leads enrolled in the "Inbound-Lead-7Day" cadence. After two days the rep reports seeing no steps in the Work Queue.

**Problem:** The rep cannot work their cadence and suspects the cadence is broken. The admin needs to diagnose without disrupting other reps using the same cadence.

**Solution:**

```
Diagnostic checklist (run in this order):

1. Verify permission set assignment:
   Setup > Users > [Rep Name] > Permission Set Assignments
   Confirm "Sales Engagement User" is present.
   If missing: assign it, have rep log out and back in.

2. Check prospect enrollment status:
   Open any of the 20 Lead records.
   Cadence related list: Status should be "Active".
   If Paused: check pause reason (engagement signal or manual pause).

3. Confirm step due dates:
   If Step 1 was a Wait step, the step may not be due yet.
   Review cadence step order; confirm no Wait step at position 1.

4. Confirm preceding step completion:
   If a prior step is marked Pending (not Complete),
   the queue will not advance.
   Check open tasks on the Lead record tied to the cadence.

5. Check org-wide active target count:
   Setup > Sales Engagement Settings > Usage
   Active target count vs. 500,000 cap.
   Active tracker count vs. 150,000 cap.

6. Confirm email field population:
   If Step 1 is an Email step and Lead.Email is blank,
   the step silently skips; queue appears empty
   until a non-email step is due.
```

**Why it works:** The diagnostic sequence eliminates the most common causes (permissions, enrollment status) before checking limits or field data. This avoids unnecessary cadence deactivation or escalation.

---

## Anti-Pattern: Building Cadences Before Creating Email Templates

**What practitioners do:** Admins open Cadence Builder and start adding Email steps, expecting to pick or create templates inline.

**What goes wrong:** Email steps require selecting an existing template. If no templates exist, the step cannot be saved. The cadence is saved in a broken state with incomplete steps. Activating a cadence with incomplete email steps causes those steps to silently fail at runtime.

**Correct approach:** Create all email templates and call scripts in Setup before opening Cadence Builder. Map each step in the cadence design to a specific template name and confirm each template exists and is accessible before building the step.
