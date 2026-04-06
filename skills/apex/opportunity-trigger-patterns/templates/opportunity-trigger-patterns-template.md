# Opportunity Trigger Patterns — Work Template

Use this template when working on Opportunity trigger tasks.

## Scope

**Skill:** `opportunity-trigger-patterns`

**Request summary:** (fill in what the user asked for)

**Automation type(s) in scope:**
- [ ] Stage-change detection
- [ ] Account rollup
- [ ] OpportunityTeamMember sync
- [ ] OpportunitySplit redistribution
- [ ] Other: ___

## Context Gathered

Record answers to the Before Starting questions from SKILL.md:

- **Trigger framework in use:** (FFLIB / Kevin O'Hara / custom / none)
- **Opportunity Splits enabled:** yes / no
- **Split types in org:** Revenue / Overlay / custom (list names)
- **Opportunity Teams enabled:** yes / no
- **Existing trigger on Opportunity:** yes / no — name: ___
- **Existing trigger on OpportunityTeamMember:** yes / no — name: ___
- **Maximum expected batch size:** ___
- **AccountId can change on updates:** yes / no (affects rollup pattern)

## Trigger Events Required

Check all that apply:

- [ ] before insert
- [ ] before update
- [ ] after insert
- [ ] after update
- [ ] after delete
- [ ] after undelete
- [ ] (OpportunityTeamMember) after insert
- [ ] (OpportunityTeamMember) after delete

## Approach

Which pattern from SKILL.md applies? Why?

- Pattern selected: ___
- Reason: ___
- Trigger context: before / after (circle one per automation type)

## Split Percentage Arithmetic (if applicable)

- Split type: Revenue / Overlay
- Member count (expected): ___
- Base share formula: `100 / count = ___`
- Remainder formula: `100 - (base * count) = ___`
- Remainder assigned to: first / last / owner record (circle one)
- Sum verified: `(base * (count - 1)) + (base + remainder) = 100`

## Checklist

Copy the Review Checklist from SKILL.md and tick items as you complete them:

- [ ] `Trigger.oldMap` is only accessed in update/delete contexts — never in insert
- [ ] No SOQL queries or DML statements inside loops
- [ ] Revenue split percentages verified to sum to 100 before DML
- [ ] OpportunitySplit DML placed in after-insert or after-update only, never before
- [ ] Account rollup collects AccountIds from both old and new maps to handle reparenting
- [ ] Stage-change detection explicitly compares old.StageName != new.StageName
- [ ] Trigger framework activation bypass guard present and tested
- [ ] Test class covers 200-record batch, stage-change-only subset, and no-change-subset

## Notes

Record any deviations from the standard pattern and why.
