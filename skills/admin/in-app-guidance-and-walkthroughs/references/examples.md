# Examples — In-App Guidance and Walkthroughs

Three worked scenarios and one anti-pattern. Configuration below is expressed in the field names the
`Prompt` metadata actually uses, so it transfers straight into the XML shapes in
`references/metadata-examples.md` rather than into Setup-screen labels that do not survive a retrieve.

## Example 1: New Approval Process Walkthrough

**Context:** A sales ops team has added a new multi-stage approval field to the Opportunity record and changed the Submit for Approval quick action. Reps are skipping the new field because they don't know it exists.

**Problem:** A single email announcement produced no behavior change. Reps submitted opportunities with the approval status field blank, causing approval failures downstream.

**Solution:**

A three-step walkthrough. Step 1 carries the schedule and the audience gate; step 3 carries the action
button. Every step carries `stepNumber`, `versionNumber` of `1`, and its own `body`, `title`, and
`displayType`.

| Step | `displayType` | Anchor | `title` (≤36) | `body` |
|---|---|---|---|---|
| 1 | `Targeted` | Approval Status field | New: Approval Status required | Opportunities over $50K now need an Approval Status before submission. Pick a value here first. |
| 2 | `Targeted` | Submit for Approval action | Submit after setting status | Once Approval Status is set, submit from here. Deals missing status are auto-rejected. |
| 3 | `FloatingPanel` | — | You're all set | That's the whole change. The full renewal runbook is one click away. |

Step 1 also carries: `startDate` = go-live date, `timesToDisplay` = 1 (no `delayDays`, so it shows once),
`userAccess` = `SpecificPermissions`, and a `uiFormulaRule` criterion on the Sales Rep pilot custom
permission. Step 3 carries `shouldDisplayActionButton` = `true`, `actionButtonLabel` = "Open the runbook"
(≤25 chars), and `actionButtonLink`.

**Why it works:** Targeted prompts draw a visual line directly to the UI elements that changed, eliminating ambiguity about which field or button is relevant. Limiting to 3 steps keeps completion rates high.

**What to look at two weeks in.** The drop-off query from `references/metadata-examples.md` section 8
grouped by `StepNumber` and `LastResult` is the whole diagnosis. A healthy walkthrough concentrates on
`Finish`; a walkthrough with an anchor problem concentrates on one step:

```text
StepNumber  StepCount  LastResult    users
1           3          Finish          12
1           3          Dismiss          4
2           3          NoAction        61   <-- everyone stalls here
2           3          Dismiss         18
3           3          Finish            9

-- and, in the same window:
SELECT Type, StepNumber, COUNT(Id) FROM PromptError GROUP BY Type, StepNumber
Type                        StepNumber  count
ReferenceElementNotFound    2           79
```

79 `ReferenceElementNotFound` rows on step 2 says the Submit for Approval anchor moved — the quick action
was renamed in the same release. Step 2 is not "unpopular"; it is rendering as a context-free floating
card. Rebuild step 2 in targeting mode, retrieve, redeploy. The `StepNumber` correlation between the two
result sets is what distinguishes a broken anchor from genuinely bad copy, and neither query alone shows it.

---

## Example 2: Seasonal Release Feature Announcement with Video

**Context:** Salesforce Spring '25 released an enhanced Einstein Activity Capture summary panel. The admin wants users to discover the new panel without a live demo.

**Problem:** Users are ignoring the new panel because they don't know it exists. A docked prompt with a 90-second video would demonstrate the panel faster than any email or document.

**Solution:**

A single docked prompt, not a walkthrough — one step needs no `stepNumber` and consumes no walkthrough slot.

```text
displayType             DockedComposer      (the only type that accepts videoLink)
header                  New: Activity Summary Panel     (docked only, max 36 chars)
title                   New: Activity Summary           (max 36 chars)
body                    See every email, call, and meeting in one place. Watch the 90-second tour.
videoLink               <embed URL>         (max 1,000 chars; do NOT also set image or imageLink)
shouldIgnoreGlobalDelay false               (respect the org's global delay so the prompt
                                             does not compete with the initial page render)
userProfileAccess       SpecificProfiles
uiFormulaRule           {!ENCODED:{!ID:$User.Profile.Key}} EQUAL Standard
                        OR {!ENCODED:{!ID:$User.Profile.Key}} EQUAL custom_sales_manager
timesToDisplay          2
delayDays               7                   (a week between the two showings — DAYS, not seconds)
startDate               <release date>
endDate                 <release date + 30>
versionNumber           1
```

**Why it works:** Docked prompts support embedded video natively without requiring the user to leave Salesforce. Leaving `shouldIgnoreGlobalDelay` false keeps the prompt behind the org's global delay, which reduces immediate dismissal.

Two traps this shape avoids. `videoLink` and `image` cannot both be set, so there is no thumbnail here. And
the guide's own sample definition spells the element `<videolink>` in lowercase while the field table says
`videoLink` — copy the sample and the element does not match the field.

---

## Example 3: Recurring Compliance Reminder

**Context:** A compliance team needs users to acknowledge a quarterly data handling reminder. It must re-appear once per quarter even for users who have already seen it.

**Problem:** A one-time prompt is not sufficient — quarterly acknowledgment is a compliance requirement. The team initially set `timesToDisplay` to 1, which meant long-tenured users never saw the updated version.

**Solution:**

```text
displayType             FloatingPanel
displayPosition         TopCenter
title                   Q2 Data Handling Reminder       (max 36 chars)
body                    Review the updated data handling policy before opening customer records.
dismissButtonLabel      I Acknowledge                   (max 15 chars — "I have read and agree"
                                                         does not fit and fails on deploy)
shouldDisplayActionButton  true
actionButtonLabel       Read the policy                 (max 25 chars)
actionButtonLink        <policy URL>
timesToDisplay          1
startDate               first day of the quarter
endDate                 last day of the quarter
userAccess              SpecificPermissions
uiFormulaRule           {!$Permission.CustomPermission.Handles_Customer_Data} EQUAL true
versionNumber           1
```

Operational procedure: at quarter end, deploy a **new** `Prompt` with updated copy and a new quarter's
dates rather than republishing the old one. A new prompt means a new `PromptVersionId`, which means the
quarter's `PromptAction` rows are cleanly separable. Republishing the same prompt keeps the old rows and
keeps incrementing the same lifetime `TimesDisplayed` / `TimesDismissed` counters, so "did this quarter's
cohort acknowledge?" becomes a date-filtering exercise on every report.

The audience gate is worth noting: "all profiles that access customer records" is not a profile — it is a
cohort spanning several. Gating on a `Handles_Customer_Data` custom permission makes the compliance
population an explicit, auditable permission-set assignment rather than a list of profile names that drifts.

**Why it works:** A per-quarter prompt is the only native way to get a recurring acknowledgement with clean per-cycle evidence. It is operationally manual, and the manual step buys the audit trail.

---

## Anti-Pattern: Over-engineered Walkthrough with 8 Steps

**What practitioners do:** Map every field on a complex record layout to a targeted prompt step, producing an 8- or 10-step walkthrough covering an entire record form.

**What goes wrong:** Completion rates for walkthroughs beyond 5 steps drop sharply. Users dismiss the walkthrough at step 3 or 4 and never re-trigger it once `timesToDisplay` is exhausted. The walkthrough also holds its slot until someone sets `isPublished` to false. And every additional `Targeted` step is another `referenceElementContext` binding that a future layout change can degrade — an 8-step walkthrough carries roughly three times the anchor-maintenance surface of a 3-step one.

**Correct approach:** Identify the 3–5 highest-friction steps in the process and build the walkthrough around those. For complex multi-page processes, split into two shorter walkthroughs (one per phase), each using a slot. Prefer `FloatingPanel` for steps that explain rather than point — they carry no anchor dependency at all.
