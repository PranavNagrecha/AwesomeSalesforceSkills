# File And Document Integration — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `file-and-document-integration`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- File direction: Upload into SF / Surface external files / Export from SF
- Maximum expected file size:
- Org file storage allocation and current usage:
- Virus scanning required: Yes / No
- Target record type for file linking:
- External system (if Files Connect or outbound):

## Approach

Which pattern applies:
- [ ] REST multipart upload (files > 20 MB or up to 2 GB)
- [ ] Base64 ContentVersion insert (files < 20 MB, simple integration)
- [ ] Files Connect configuration (read external files in SF)
- [ ] Virus scanning implementation (async Queueable callout)
- [ ] ContentDocumentLink wiring (link files to records)

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] ContentVersion is used for file creation — ContentDocument is never inserted directly
- [ ] Files over 28 MB use REST multipart upload, not base64 encoding
- [ ] ContentDocumentLink records have explicit ShareType (V, C, or I)
- [ ] FirstPublishLocationId is used where possible to avoid separate ContentDocumentLink insert
- [ ] Virus scanning is implemented via async callout if security policy requires it
- [ ] Named Credentials are used for external service callouts
- [ ] File storage consumption is estimated and compared against org allocation
- [ ] Files Connect uses correct Authentication Provider type for external system
- [ ] Error handling covers STORAGE_LIMIT_EXCEEDED, FILE_SIZE_LIMIT_EXCEEDED, and callout failures

## Notes

Record any deviations from the standard pattern and why.
