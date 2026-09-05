# Standard Object Quirks — Work Template

Use this template when diagnosing or fixing unexpected behavior from Salesforce standard objects.

## Scope

**Skill:** `standard-object-quirks`

**Request summary:** (fill in what the user asked for)

**Standard objects involved:** (list all standard objects in play — Account, Contact, Lead, Task, Event, Case, CaseComment, etc.)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **PersonAccounts enabled?** Yes / No / Unknown — verify with `SELECT IsPersonAccount FROM Account LIMIT 1`
- **Which object do the existing triggers sit on?** Account / Contact / both / none — person-account
  DML fires **Account** triggers, not Contact triggers, so a Contact-side implementation is dead code
- **Validation and triggers for lead conversion enabled?** Yes / No / Unknown — before triggers on
  account, contact and opportunity fire during conversion only when this is on
- **Lead conversion in scope?** Yes / No — check if custom fields exist on Lead that need to survive conversion
- **Which Task statuses are flagged closed?** (list them) — `CompletedDateTime` follows the Closed
  status *category*, not the literal value `Completed`
- **Activity automation involved?** Yes / No — confirm whether Task/Event triggers or Flows are part of the issue
- **Event duration form used by the source system?** DurationInMinutes / EndDateTime / both / neither
- **CaseComment automation?** Yes / No — and does anything need to *edit* a saved comment?
  (that needs Modify All Records on Cases or Modify All Data)
- **Merge in scope?** Yes / No — if yes, how many duplicates per master, and which fields must survive?

## Quirk Identified

**Category:** (select one)
- [ ] Polymorphic lookup (WhoId/WhatId)
- [ ] Lead conversion field loss, or conversion triggers not firing
- [ ] PersonAccount — logic written on the wrong object (Contact instead of Account)
- [ ] PersonAccount — `Name` write, or `Schema.Account.<field>` token throwing
- [ ] Business↔person record-type conversion firing no trigger
- [ ] CaseComment trigger isolation, or the post-insert write lock
- [ ] Activity date field confusion (ActivityDate vs CompletedDateTime vs closed status category)
- [ ] Event duration contract (neither DurationInMinutes nor EndDateTime supplied)
- [ ] Merge — record cap, field survival, or MasterRecordId read too early
- [ ] Account deletion / Contact orphaning (UNVERIFIED behaviour — test in sandbox)
- [ ] Other: ___________

**Description of unexpected behavior:**

(Describe what the code or configuration does versus what was expected)

**Root cause:**

(Reference the specific platform behavior from SKILL.md Core Concepts or Gotchas, and cite the
guide line — e.g. "apexdev.txt L15521". A root cause without a source is a guess.)

**Was the original belief inverted?** Yes / No — if yes, record what was believed and what the
guide actually says, so the correction survives the next rewrite.

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
- [ ] Person-account logic lives in an **Account** trigger handler, not a Contact one
- [ ] No code assigns `Account.Name` on a person-account record
- [ ] Schema introspection uses string field names, not `Schema.Account.<field>` tokens
- [ ] Lead conversion logic captures unmapped custom fields before `convertLead`
- [ ] CaseComment-driven automation uses a CaseComment trigger, and never edits a saved comment
- [ ] Event creation sets **either** EndDateTime **or** DurationInMinutes (both only if they agree)
- [ ] Task completion filters use `CompletedDateTime`, not the literal `'Completed'`
- [ ] Merge passes at most three records and reads `MasterRecordId` in **after delete**
- [ ] `python3 scripts/check_standard_object_quirks.py --manifest-dir <src>` reports no errors
- [ ] Unit tests cover both sides of polymorphic lookups, and both account shapes
- [ ] Code comments explain the non-obvious platform behavior, with the source line

## Test Plan

| Test Scenario | Expected Result | Pass? |
|---|---|---|
| (e.g., Query Task with Contact WhoId) | (e.g., Returns Contact.Email via TYPEOF) | |
| (e.g., Query Task with Lead WhoId) | (e.g., Returns Lead.Company via TYPEOF) | |
| Insert a person account with **no Contact trigger deployed** | Account handler still ran — proves the dispatch object | |
| Insert Event with DurationInMinutes only, no EndDateTime | Insert succeeds (this is the valid form) | |
| Insert Event with neither field, IsAllDayEvent false | Insert fails — the only genuinely invalid shape | |
| Save a Task in a non-`Completed` closed status | `CompletedDateTime` populates; `IsClosed` is true | |
| Merge 3 losers into 1 master in one call | Fails or truncates — cap is master + 2 | |
| Read `MasterRecordId` in after delete after a merge | Winning record's Id present on every loser | |

## Notes

Record any deviations from the standard pattern and why.
