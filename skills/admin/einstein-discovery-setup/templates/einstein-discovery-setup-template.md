# Einstein Discovery Setup — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `einstein-discovery-setup`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **CRM Analytics license confirmed?** Yes / No (check Setup > Company Information > Licenses)
- **Target object:** (e.g., Opportunity, Lead, Case, Contact)
- **Outcome variable and type:** (e.g., IsClosed — binary, or Amount — numeric/regression)
- **Analysis mode required:** Insights only / Insights and Predictions (writeback required?)
- **Existing writeback fields on target object:** (count — max allowed is 3)
- **Profiles/permission sets that need to see prediction scores:** (for FLS assignment)
- **Model refresh schedule needed?** Yes / No — if yes, frequency: ___

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] End-to-End Story Deployment with Writeback (new story + writeback field + page layout)
- [ ] Model Refresh Activation After Scheduled Retraining (existing story, post-refresh steps)
- [ ] Other: ___

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] CRM Analytics license confirmed in Setup > Company Information > Licenses
- [ ] Story created in Analytics Studio using the three-step wizard (not Setup menu)
- [ ] Leakage fields excluded from explanatory variables in Step 3 of the wizard
- [ ] "Insights and Predictions" selected (not "Insights only") if writeback scoring is required
- [ ] Prediction definition created and status is Enabled (1OR prefix ID: ___)
- [ ] Writeback field FLS assigned to relevant profiles and permission sets
- [ ] Writeback field added to page layout(s) where scores should appear
- [ ] Initial bulk scoring job triggered and writeback field values verified on sample records
- [ ] Model refresh schedule configured and documented
- [ ] Post-refresh activation step documented in admin runbook
- [ ] Writeback field count on target object confirmed to be 3 or fewer

## Story Configuration Summary

| Setting | Value |
|---|---|
| Target object | |
| Outcome variable | |
| Outcome type | Binary / Numeric |
| Analysis mode | Insights only / Insights and Predictions |
| Explanatory variables included | (list key fields) |
| Leakage fields excluded | (list excluded fields and reason) |
| Prediction definition ID (1OR) | |
| Writeback field API name | |
| Writeback field FLS assigned to | (list profiles/permission sets) |
| Model refresh schedule | |

## Notes

Record any deviations from the standard pattern and why.
