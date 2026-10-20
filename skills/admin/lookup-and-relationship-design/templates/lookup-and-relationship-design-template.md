# Lookup And Relationship Design — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `lookup-and-relationship-design`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md: ownership, delete behaviour, junction primary, deepest read path, automation users, orphan rows, polymorphic need.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Name the relationship type from the Decision Guidance table and the pattern that applies (master-detail for true parent-child, lookup + `Restrict`, or lookup + rollup alternative), with the answer that decided it.

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Ownership semantics documented and match the chosen type
- [ ] `deleteConstraint` (or cascade) set explicitly
- [ ] Relationship count under 40 on the custom object; read paths within five levels
- [ ] Two master-details: `relationshipOrder` names the intended primary

## Notes

Record any deviation from the chosen pattern, who approved it, and why.
