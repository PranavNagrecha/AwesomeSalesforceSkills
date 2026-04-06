# Standard Object Quirks — Work Template

Use this template when diagnosing or fixing unexpected behavior from Salesforce standard objects.

## Scope

**Skill:** `standard-object-quirks`

**Request summary:** (fill in what the user asked for)

**Standard objects involved:** (list all standard objects in play — Account, Contact, Lead, Task, Event, Case, CaseComment, etc.)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **PersonAccounts enabled?** Yes / No / Unknown — verify with `SELECT IsPersonAccount FROM Account LIMIT 1`
- **Lead conversion in scope?** Yes / No — check if custom fields exist on Lead that need to survive conversion
- **Activity automation involved?** Yes / No — confirm whether Task/Event triggers or Flows are part of the issue
- **CaseComment automation?** Yes / No — confirm whether comment-driven Case updates are expected

## Quirk Identified

**Category:** (select one)
- [ ] Polymorphic lookup (WhoId/WhatId)
- [ ] Lead conversion field loss
- [ ] PersonAccount dual-nature
- [ ] CaseComment trigger isolation
- [ ] Activity date field confusion (ActivityDate vs CompletedDateTime)
- [ ] Account deletion / Contact orphaning
- [ ] Other: ___________

**Description of unexpected behavior:**

(Describe what the code or configuration does versus what was expected)

**Root cause:**

(Reference the specific platform behavior from SKILL.md Core Concepts or Gotchas)

## Corrective Pattern Applied

**Pattern used:** (reference the pattern name from SKILL.md Common Patterns)

**Code or configuration change:**

```apex
// Paste the corrected code here
```

**Why this fixes the issue:**

(Explain the key insight — what platform behavior does this pattern account for)

## Review Checklist

Copy from SKILL.md and check off as completed:

- [ ] All SOQL queries on Task/Event use TYPEOF or explicit type checks for WhoId/WhatId
- [ ] PersonAccount queries use Person-prefixed fields (PersonEmail, PersonMailingCity)
- [ ] Lead conversion logic accounts for unmapped custom fields
- [ ] CaseComment-driven automation uses a CaseComment trigger, not a Case trigger
- [ ] Event creation via Apex sets EndDateTime explicitly
- [ ] Unit tests cover both sides of polymorphic lookups
- [ ] Code comments explain the non-obvious platform behavior

## Test Plan

| Test Scenario | Expected Result | Pass? |
|---|---|---|
| (e.g., Query Task with Contact WhoId) | (e.g., Returns Contact.Email via TYPEOF) | |
| (e.g., Query Task with Lead WhoId) | (e.g., Returns Lead.Company via TYPEOF) | |
| (e.g., Create Event via Apex with EndDateTime) | (e.g., Insert succeeds without error) | |

## Notes

Record any deviations from the standard pattern and why.
