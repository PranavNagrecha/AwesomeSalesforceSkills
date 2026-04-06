# Examples — In-App Guidance and Walkthroughs

## Example 1: New Approval Process Walkthrough

**Context:** A sales ops team has added a new multi-stage approval field to the Opportunity record and changed the Submit for Approval quick action. Reps are skipping the new field because they don't know it exists.

**Problem:** A single email announcement produced no behavior change. Reps submitted opportunities with the approval status field blank, causing approval failures downstream.

**Solution:**

Create a targeted walkthrough with 3 steps:

```
Step 1 (Targeted prompt — anchored to "Approval Status" field):
  Title: "New: Approval Status required"
  Body: "Opportunities over $50K now require an Approval Status before submission.
         Select a value from this picklist before clicking Submit for Approval."
  Action button: "Got it"

Step 2 (Targeted prompt — anchored to "Submit for Approval" quick action button):
  Title: "Submit after setting status"
  Body: "Once Approval Status is set, click here to submit.
         Deals missing status will be auto-rejected."
  Action button: "Next"

Step 3 (Floating prompt):
  Title: "You're all set"
  Body: "Complete the walkthrough confirmation email or message goes here."
  Action button: "Done"
```

Audience: Sales Rep profile
Frequency: Once per user
Start date: Day of go-live

**Why it works:** Targeted prompts draw a visual line directly to the UI elements that changed, eliminating ambiguity about which field or button is relevant. Limiting to 3 steps keeps completion rates high.

---

## Example 2: Seasonal Release Feature Announcement with Video

**Context:** Salesforce Spring '25 released an enhanced Einstein Activity Capture summary panel. The admin wants users to discover the new panel without a live demo.

**Problem:** Users are ignoring the new panel because they don't know it exists. A docked prompt with a 90-second video would demonstrate the panel faster than any email or document.

**Solution:**

Create a single docked prompt (not a walkthrough):

```
Type: Docked
Page: Record home — any Contact or Lead record
Title: "New: Activity Summary Panel"
Body: "See all emails, calls, and meetings in one place. Watch the 90-second overview."
Video URL: [internal YouTube or hosted video URL]
Audience: Sales Rep profile, Sales Manager profile
Frequency: Once per user
Page-load delay: 3 seconds
Start date: Day of release
End date: 30 days after release
```

**Why it works:** Docked prompts support embedded video natively without requiring the user to leave Salesforce. The 3-second page-load delay prevents the prompt from competing with the initial page render, which reduces immediate dismissal rates.

---

## Example 3: Recurring Compliance Reminder

**Context:** A compliance team needs users to acknowledge a quarterly data handling reminder. It must re-appear once per quarter even for users who have already seen it.

**Problem:** A one-time prompt is not sufficient — quarterly acknowledgment is a compliance requirement. The team initially set frequency to "Once" which meant long-tenured users never saw the updated version.

**Solution:**

```
Type: Floating prompt
Title: "Q2 Data Handling Reminder"
Body: "Please review our updated data handling policy before accessing customer records.
       [Link to policy document]"
Action button: "I Acknowledge"
Frequency: Once per user (deactivate and republish quarterly with updated copy — each republish resets the "Once" counter for all users)
Audience: All profiles that access customer records
Start date: First day of each quarter
End date: Last day of the quarter
```

Operational procedure: The admin deactivates the prompt at quarter end and creates a new prompt with updated copy at the start of the next quarter. Each new publication resets the display state.

**Why it works:** The "republish to reset" pattern is the only native way to achieve recurring acknowledgment without a Sales Enablement license. It is operationally manual but fully within the free tier.

---

## Anti-Pattern: Over-engineered Walkthrough with 8 Steps

**What practitioners do:** Map every field on a complex record layout to a targeted prompt step, producing an 8- or 10-step walkthrough covering an entire record form.

**What goes wrong:** Completion rates for walkthroughs beyond 5 steps drop sharply. Users dismiss the walkthrough at step 3 or 4 and never re-trigger it (if frequency is set to "Once"). The walkthrough also consumes one of the 3 free-tier slots indefinitely.

**Correct approach:** Identify the 3–5 highest-friction steps in the process and build the walkthrough around those. For complex multi-page processes, consider splitting into two separate shorter walkthroughs (one per phase), each using a slot.
