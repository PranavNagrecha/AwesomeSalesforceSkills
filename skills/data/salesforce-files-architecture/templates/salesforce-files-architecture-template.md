# Salesforce Files Architecture — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `salesforce-files-architecture`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Name the storage choice from SKILL.md Recommended Workflow step 2 (per-record ContentVersion + ContentDocumentLink, Library file, or Files Connect) and the `ShareType` / `Visibility` pair chosen for it.

## Checklist

Tick each Recommended Workflow step from SKILL.md as you complete it.

- [ ] Legacy `Attachment` count checked and a migration planned if non-zero
- [ ] Object choice made for the use case
- [ ] Sharing model planned (`ShareType`, `Visibility`)
- [ ] File storage budget forecast
- [ ] Apex inserts follow ContentVersion → ContentDocumentId → ContentDocumentLink
- [ ] "Files on this record" queries go through `ContentDocumentLink`
- [ ] Files above the 2 GB ceiling routed to external storage

## Notes

Record any deviations from the standard pattern and why.
