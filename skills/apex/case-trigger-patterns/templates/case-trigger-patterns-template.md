# Case Trigger Patterns — Work Template

Use this template when working on Case trigger tasks in this domain.

## Scope

**Skill:** `case-trigger-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before writing any code:

- **Assignment rules active?** Yes / No — rule Id if specific rule needed: ___
- **Entitlements enabled?** Yes / No — coverage model: Account-wide / Contact-specific (EntitlementContact)
- **Merge handling in scope?** Yes / No
- **Milestone completion at case close required?** Yes / No
- **Existing CaseTrigger in the org?** Yes / No — if Yes, handler class name: ___
- **Trigger framework in use?** Yes / No — framework name: ___

## Patterns Selected

Which of the four patterns apply? (check all that apply)

- [ ] Pattern 1 — Assignment rule invocation via `Database.DmlOptions`
- [ ] Pattern 2 — Entitlement auto-association in Before Insert
- [ ] Pattern 3 — Merge delete handling with `MasterRecordId` check
- [ ] Pattern 4 — Milestone completion on case close

## Implementation Plan

For each selected pattern, describe the class and method to add or modify:

| Pattern | File | Method | New or Extend? |
|---|---|---|---|
| Assignment rules | `CaseService.cls` or handler | `insertCasesWithRouting()` | |
| Entitlement association | `CaseTriggerHandler.cls` | `associateEntitlements()` | |
| Merge handling | `CaseTriggerHandler.cls` | `onBeforeDelete()` | |
| Milestone completion | `CaseTriggerHandler.cls` | `completeMilestonesOnClose()` | |

## Checklist

Copy and complete before marking work done:

- [ ] All Case DML requiring assignment rules uses `Database.insert()`/`Database.update()` with `Database.DmlOptions` — not the `insert`/`update` keyword
- [ ] Entitlement association runs in `Before Insert` context (not After Insert) to avoid extra DML
- [ ] Merge delete handler checks `MasterRecordId` on `Trigger.old` records, not `Trigger.new`
- [ ] Milestone completion sets `CaseMilestone.CompletionDate`, not `CaseMilestone.IsCompleted`
- [ ] No second `CaseTrigger` created — logic added to existing handler
- [ ] All handler methods are bulkified (no SOQL or DML inside loops)
- [ ] Test class covers all selected patterns with positive and guard-condition assertions
- [ ] `python3 scripts/skill_sync.py --skill skills/apex/case-trigger-patterns` passes

## Notes

Record any deviations from the standard pattern and why:

(empty)
