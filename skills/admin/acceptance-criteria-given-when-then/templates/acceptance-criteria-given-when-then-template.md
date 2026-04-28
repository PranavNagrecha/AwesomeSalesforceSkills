# Acceptance Criteria — Given/When/Then Work Template

Use this template when activating the `acceptance-criteria-given-when-then`
skill on a new or existing user story.

## Scope

**Skill:** `acceptance-criteria-given-when-then`

**Request summary:** (fill in what the user asked for — typically "write
behavior-driven AC for story X")

**Story under work:** (paste the As a / I want / So that wrapper)

## Context Gathered

Record answers to the Before Starting questions from `SKILL.md`:

- **Persona / profile / PSG:**
- **Target object(s):**
- **Sharing-relevant? OWD?** (Private / Public RO / Public RW / Controlled by Parent)
- **Single-record or bulk path expected?**
- **Async / callout / integration boundary?**
- **Known constraints (governor limits, integration peer system, license tier):**

## Approach

Which patterns from `SKILL.md` apply?

- [ ] Background block with named users + PSGs (always when sharing-relevant)
- [ ] Happy-path Scenario(s)
- [ ] Paired negative-path Scenario(s)
- [ ] Scenario Outline with Examples (when 3+ parameterized cases)
- [ ] Bulk Scenario (when trigger / flow / validation)
- [ ] `Then eventually` async Scenario (when callout / Queueable / PE / batch)

## Output

Use `templates/ac-template.md` (sibling file) as the canonical skeleton.
Paste the filled-in AC block into the user story body, then run:

```bash
python3 scripts/check_ac_format.py <story.md>
```

## Checklist

Copy the Review Checklist from `SKILL.md` and tick items as you complete
them. Do not hand off to `agents/test-generator` until all items are
ticked.

- [ ] Every Scenario has exactly one Given, one When, one Then
- [ ] Every happy-path has a paired negative-path
- [ ] Every Scenario names the running user by PSG / profile
- [ ] Record ownership / lifecycle precondition is explicit
- [ ] No UI-chrome language
- [ ] Bulk Scenario present (when applicable)
- [ ] Async outcomes use "eventually within N seconds"
- [ ] Validation-error messages are exact strings (or marked `# TBD`)
- [ ] Integration expectations name the named credential

## Notes

Record any deviations from the standard pattern and why.
