# Apex Schema Describe — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `apex-schema-describe`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask table in SKILL.md here.

- Call site (once per request / inside a loop):
- Object and field names known at compile time, or runtime strings:
- Namespace of the running code and of the target objects:

## Approach

Which pattern from SKILL.md applies (A cached field map, B stripInaccessible, C dynamic creation), and why.

## Checklist

- [ ] No `Schema.getGlobalDescribe()` inside loops.
- [ ] Per-type field map cached in a transaction-scoped `static` when used in hot paths.
- [ ] Bulk DML uses `Security.stripInaccessible`.
- [ ] Picklist code does not expect inactive values (`getPicklistValues()` returns active only).
- [ ] Record types looked up by DeveloperName.
- [ ] `check_apex_schema_describe.py --manifest-dir <src>` run; findings resolved or explained.

## Notes

Record any deviation from the standard pattern and why.
