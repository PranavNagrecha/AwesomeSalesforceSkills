# Bulk API 2.0 Patterns — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `bulk-api-2-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from `SKILL.md` here.

- Setting / configuration: API version, auth mode, multipart vs staged upload
- Known constraints: object types, operation, daily volume estimates, external IDs available
- Failure modes to watch for: partial batch success, parent/child ordering, locator pagination bugs

## Approach

Which pattern from `SKILL.md` applies (hardened single job, ordered parent/child, query pagination worker)? Why?

## Checklist

Copy the review checklist from `SKILL.md` and tick items as you complete them.

- [ ] Non-multipart ingest includes explicit `UploadComplete` after final `PUT`
- [ ] Polling distinguishes `InProgress`, `JobComplete`, `Failed`, and `Aborted`
- [ ] Partial failures produce a scoped retry file
- [ ] Query extracts implement locator pagination without invented tokens
- [ ] Parent/child loads are sequenced with a hard gate on parent `JobComplete`
- [ ] Monitoring includes Salesforce job ID, state transitions, and row counters

## Notes

Record any deviations from the standard pattern and why (for example, multipart chosen for payload size, or extra quarantine delay after `Failed`).
