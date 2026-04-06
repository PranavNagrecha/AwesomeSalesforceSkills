# Document Generation OmniStudio — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `document-generation-omnistudio`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- OmniStudio DocGen enabled: yes / no
- Server-side DocGen enabled (if needed): yes / no
- Generation mode: client-side (OmniScript) / server-side (Integration Procedure)
- Output format required: PDF / DOCX / PPTX
- Template token types needed: simple / repeating / conditional / image / rich text
- Data source objects:
- Estimated document volume: single / batch

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Pattern 1: Interactive Single-Document (client-side) — user reviews data before generating
- [ ] Pattern 2: Batch/Headless (server-side) — triggered without user interaction
- [ ] Pattern 3: Multi-Template Package — multiple documents generated and combined

## Artifact Checklist

| Artifact | Name | Status |
|---|---|---|
| Document Template (.docx/.pptx) | | pending / done |
| OmniDataTransform (Mapping) | | pending / done |
| Document Generation Setting | | pending / done |
| OmniScript or Integration Procedure | | pending / done |
| PDF Conversion Step (if needed) | | pending / done |

## Review Checklist

Copy from SKILL.md and tick items as you complete them.

- [ ] Document Template uploaded as ContentVersion with correct format
- [ ] All tokens in template have corresponding Data Mapper mappings
- [ ] OmniDataTransform output JSON matches template token paths (case-sensitive)
- [ ] Document Generation Setting links correct template, Data Mapper, and mode
- [ ] Image tokens used only in client-side mode and images under 2.5 MB
- [ ] Rich text tokens used only in client-side mode
- [ ] Repeating sections work with 0, 1, and many items
- [ ] Conditional sections render correctly for true and false conditions
- [ ] PDF conversion step included if PDF output required
- [ ] Generated document stored as ContentVersion on correct parent record
- [ ] Server-side DocGen setting enabled (if using server-side)

## Notes

Record any deviations from the standard pattern and why.
