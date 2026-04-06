# Salesforce Surveys — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `salesforce-surveys`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Feedback Management tier (Base / Starter / Growth):
- Current response count (`SELECT COUNT() FROM SurveyResponse`):
- Audience: internal (authenticated) / external (guest user):
- Experience Cloud site name (if external):
- Question types needed:
- Branching required (yes/no):

## Approach

Which pattern from SKILL.md applies?

- [ ] Post-Case Survey via Email Invitation
- [ ] Internal Employee Pulse Survey
- [ ] Other (describe):

## Checklist

- [ ] Feedback Management tier confirmed and response cap is sufficient
- [ ] Guest User Profile has Read and Create on survey objects (if external)
- [ ] Field-level security on guest user profile covers all referenced fields
- [ ] Branching logic tested with each possible answer path
- [ ] SurveyInvitation records correctly associated to source records
- [ ] Survey tested from an unauthenticated browser session (for external)
- [ ] NPS scoring verified: Detractor (0-6), Passive (7-8), Promoter (9-10)

## Notes

Record any deviations from the standard pattern and why.
