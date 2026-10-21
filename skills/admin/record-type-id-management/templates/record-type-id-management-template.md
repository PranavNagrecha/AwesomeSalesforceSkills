# Record Type Id Management — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `record-type-id-management`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the `## Questions to Ask Before Configuring` table in SKILL.md here.

- Hard-coded `012…` literals found (file:line):
- Objects and record types in scope (DeveloperName per object):
- User-facing pickers that need `isAvailable()` / `isActive()` / `isMaster()` filtering:
- Lead / Opportunity / Solution / Case record types (need a bare `businessProcess`):

## Approach

Which reference point applies (Apex, Flow, formula, LWC) and which row of the SKILL.md Decision Guidance table resolves it.

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] No hard-coded record-type IDs remain in Apex, LWC, Flow, or metadata
- [ ] Central Apex utility used for ID resolution, with a null-guard
- [ ] LWC gets the Id from an Apex resolver, not a `getObjectInfo` developerName lookup
- [ ] `check_record_type_id_management.py --strict` passes on the changed metadata

## Notes

Record any deviations from the standard pattern and why.
