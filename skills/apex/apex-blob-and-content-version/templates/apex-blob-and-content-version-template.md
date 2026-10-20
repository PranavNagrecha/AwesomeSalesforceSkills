# Apex Blob And Content Version — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `apex-blob-and-content-version`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting and Questions to Ask Before Configuring sections of SKILL.md here.

- Largest file (binary MB) and files per transaction:
- Execution context and its heap ceiling: sync 10 MB / async 25 MB from Winter '27 (6 / 12 MB through Summer '26, or on a Winter '27 nonproduction org with `ApexSettings.enableEnforceSummer26ApexHeapLimit`):
- Byte source (LWC data URL, REST body, callout — callout responses stay capped at 6 MB sync / 12 MB async):
- Owning record (`FirstPublishLocationId`) and audience (`Visibility`, `ShareType`):
- New file or new version of an existing `ContentDocumentId`:

## Approach

Which pattern from SKILL.md applies, and why?

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Every ContentVersion insert sets `Title`, `PathOnClient`, and `VersionData`.
- [ ] Sharing is explicit: `FirstPublishLocationId` OR `ContentDocumentLink` with `ShareType` + `Visibility`.
- [ ] No loop holds more than one large `Blob` in scope at a time.
- [ ] LWC uploads over 4 MB binary are routed to `lightning-file-upload` or UI API, not a custom `@AuraEnabled`.
- [ ] Callout-sourced imports run in a Queueable with `Database.AllowsCallouts`, not sync Apex.
- [ ] Community-facing files use `Visibility = 'AllUsers'`.
- [ ] Base64 encoding is not round-tripped through `Blob.toString()`.
- [ ] Heap usage is tested with realistic file sizes, not trivial fixtures.

## Notes

Record any deviations from the standard pattern and why.
