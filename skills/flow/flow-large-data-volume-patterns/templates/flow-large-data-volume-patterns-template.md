# Flow Large Data Volume Patterns — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `flow-large-data-volume-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Which pattern from SKILL.md applies? Why?

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Each `Get Records` has a documented worst-case row count.
- [ ] No synchronous path depends on unbounded related retrieval.
- [ ] Combined SOQL row usage leaves headroom for co-resident automation.
- [ ] Volume tested with production-like related counts where feasible.

## Notes

Record any deviations from the standard pattern and why.
