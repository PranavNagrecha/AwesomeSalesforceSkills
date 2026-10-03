# Agentforce Multi Turn Patterns — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `agentforce-multi-turn-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Which pattern from SKILL.md applies (accumulating form fill, cross-subagent memory, clarify-or-assume, failure-bounded escalation)? Why?

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Every fact later turns need is a declared variable with type, default, and description
- [ ] Record IDs are typed string, not id
- [ ] Dependent variables reset when their source variable changes
- [ ] Owned variables reset when their subagent hands off
- [ ] Escalation route (Omni-Channel connection) exists before escalation is tested
- [ ] Sensitive action outputs use filter_from_agent
- [ ] Multi-turn test cases use conversationHistory

## Notes

Record any deviations from the standard pattern and why.
