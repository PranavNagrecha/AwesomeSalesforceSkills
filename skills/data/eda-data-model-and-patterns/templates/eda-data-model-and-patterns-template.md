# EDA Data Model and Patterns — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `eda-data-model-and-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answers to the Before Starting questions from SKILL.md:

- EDA package version installed, and whether it has been customised:
- Account record types in use, by developer name (`Academic_Program`, `HH_Account`, ...):
- Affiliation Mapping rows present in this environment (they are custom-setting data, not metadata):
- TDTM handlers that must stay active during this work:

## Approach

Which pattern from SKILL.md applies (Affiliation, Relationship, Course Connection, multi-campus), and why the alternatives were rejected:

## Checklist

From the review checklist in SKILL.md, plus the failure modes in `references/gotchas.md`:

- [ ] API names taken from Object Manager, not from labels (`hed__Course_Enrollment__c`, not Course Connection)
- [ ] Namespace prefix confirmed per field — four Primary Affiliation fields on Contact are unprefixed
- [ ] Affiliation Mapping rows verified in the target environment
- [ ] TDTM bypass, if used, scoped to the load user and restored with an assertion
- [ ] Reference dataset exercises every role and relationship variant

## Notes

Deviations from the standard pattern, and the reason for each:

