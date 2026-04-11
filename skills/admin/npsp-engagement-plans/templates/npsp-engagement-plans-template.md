# NPSP Engagement Plans — Work Template

Use this template when configuring, applying, or troubleshooting NPSP Engagement Plans.

## Scope

**Skill:** `npsp-engagement-plans`

**Request summary:** (Describe what the stakeholder asked for — e.g., "Build a major donor stewardship engagement plan template with 30/60/90 day tasks and apply it automatically when a gift closes above $10,000.")

---

## Context Gathered

Answer these before building anything:

- **Target object(s):** (Account / Contact / Opportunity / Campaign / Case / Recurring Donation / Custom Object)
- **Custom object extra steps needed?** (Activities enabled? Lookup field added to npsp__Engagement_Plan__c?)
- **Stewardship cadence:** (Number of tasks, day offsets, subjects, assigned-to users or queues, parent-child dependencies)
- **Non-Task actions needed?** (Email sends, field updates, Chatter posts — these require a separate Flow)
- **Template migration plan:** (Manual recreation in production? Data Loader export/import? Document reference?)
- **In-flight plans impacted by this change?** (Are there existing npsp__Engagement_Plan__c instances that need to be deleted and reapplied?)

---

## Template Design

Fill this in before building the template record.

**Template Name:** ____________________________________

**Target Object:** ____________________________________

**Skip Weekends:** Yes / No

**Description:** ____________________________________

| # | Subject | Days Offset | Type | Priority | Assigned To | Parent Task # |
|---|---------|-------------|------|----------|-------------|---------------|
| 1 | | | | | | (none) |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |

Add rows as needed.

---

## Approach

**Which pattern applies?**

- [ ] Major donor stewardship cadence (Opportunity-based, Flow-applied)
- [ ] Campaign post-event stewardship (Campaign-based, manual or Flow-applied)
- [ ] Contact onboarding cadence (Contact-based)
- [ ] Custom object stewardship (requires Activities enabled + lookup field on npsp__Engagement_Plan__c)
- [ ] Other: ____________________________________

**Flow automation needed?**

- [ ] Yes — Record-Triggered Flow to auto-apply the template (document trigger criteria below)
- [ ] No — Templates will be applied manually by users

**Trigger criteria for Flow (if applicable):**
- Object: ____________________________________
- Entry criteria: ____________________________________
- Timing: After Save / Scheduled Path

**Non-Task actions needed (separate Flow)?**

- [ ] Yes — document actions below
- [ ] No

Non-Task actions: ____________________________________

---

## Build Checklist

- [ ] Template `npsp__Engagement_Plan_Template__c` record created with correct name and target object
- [ ] All `npsp__Engagement_Plan_Task__c` records added with accurate subjects, day offsets, types, and assignees
- [ ] Parent-child task dependencies configured (if applicable)
- [ ] Auto-Update Child Due Date behavior tested: parent marked Complete → child tasks recalculate (date edit alone does NOT trigger recalculation)
- [ ] Plan applied to a test record; correct number of Task records created
- [ ] Task due dates verified against the template offset values
- [ ] Flow fault path added (if automated application via Flow)
- [ ] Non-Task actions implemented in a separate Flow (if required)
- [ ] Template definition documented in external reference (spreadsheet/wiki) for migration
- [ ] Template migration plan confirmed for production deployment (Data Loader or manual recreation)
- [ ] Team informed that template changes do not update existing in-flight plan instances

---

## Migration Notes

**Source org:** ____________________________________

**Target org:** ____________________________________

**Migration method:** Data Loader / Manual recreation / REST API script

**Template IDs to export (from source org):**

| Template Name | npsp__Engagement_Plan_Template__c Id |
|---------------|--------------------------------------|
| | |

---

## Notes

Record any deviations from the standard pattern, decisions made, and open questions.

- 
- 
