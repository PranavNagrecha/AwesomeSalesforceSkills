# User Story Writing — Work Template

Use this when you are about to author or refine a Salesforce user story.
For the canonical story-shape (markdown + JSON), see `story-shape.md` in this folder.

## Scope

**Skill:** `user-story-writing-for-salesforce`

**Request summary:** (fill in what the user asked for — what is the requirement to be reshaped into a story?)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Was elicitation completed?** (yes / no — if no, route to `admin/requirements-gathering-for-sf` first)
- **Persona, in Salesforce terms:** (profile / permission set / role)
- **Object(s) involved:** (standard / custom)
- **Trigger event:** (record created, updated, manual button, scheduled, integration callback, etc.)
- **Available downstream agents in this chain:** (e.g. `object-designer`, `flow-builder`, `lwc-builder`, `permission-set-architect`)
- **Known constraints:** (volume, integration deps, sharing model, licensing)
- **Existing-story / duplicate check:** (which backlog query was run; results)

## Approach

Which pattern from SKILL.md applies?

- [ ] Reshape a vague requirement into a story
- [ ] Split an XL story
- [ ] Emit handoff JSON alongside markdown

Which split axis (if splitting)?

- [ ] By workflow steps
- [ ] By business rule
- [ ] By data variation
- [ ] By persona
- [ ] By happy path / sad path

## Draft

Use `story-shape.md` as the template. Paste the draft markdown story + handoff JSON here.

## Review Checklist (from SKILL.md)

- [ ] Persona is Salesforce-grounded (profile / permission set / role)
- [ ] `So That` names a concrete business outcome
- [ ] At least one Given-When-Then AC present
- [ ] At least one sad-path AC present
- [ ] Story body does not prescribe Flow / Apex / LWC choice
- [ ] Complexity is exactly one of S / M / L / XL
- [ ] No story committed at XL (XL split first)
- [ ] Handoff JSON present, valid, `recommended_agents[]` non-empty
- [ ] `dependencies[]` populated for any prerequisite stories
- [ ] `python3 scripts/check_invest.py <story.md>` exits 0

## Notes

Record any deviations from the canonical shape and why.
