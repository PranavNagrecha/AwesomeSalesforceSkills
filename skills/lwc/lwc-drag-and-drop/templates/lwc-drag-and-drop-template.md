# LWC Drag and Drop — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `lwc-drag-and-drop`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answers to the Before Starting questions from SKILL.md:

- Interaction shape (kanban, sortable list, file drop, tree reorder):
- Target devices — touch has no native HTML5 drag:
- Accessibility obligation, and the keyboard path that satisfies it:
- Custom MIME type for the payload, defined once:

## Approach

Native HTML5 drag, or a third-party library for touch and keyboard support — and why:

## Checklist

From the review checklist in SKILL.md, plus the failure modes in `references/gotchas.md`:

- [ ] `event.preventDefault()` in `dragover` (otherwise `drop` never fires)
- [ ] Visual state reset in `dragend`, not `drop`
- [ ] `dragenter`/`dragleave` handle child-element bubbling
- [ ] `setData('text/plain', ...)` set alongside any custom MIME
- [ ] Keyboard alternative present (arrow keys and/or a Move-to menu)
- [ ] Foreign drops rejected cleanly by checking the custom MIME

## Notes

Deviations from the standard pattern, and the reason for each:

