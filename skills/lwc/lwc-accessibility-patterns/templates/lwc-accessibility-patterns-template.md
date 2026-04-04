# LWC Accessibility Patterns — Work Template

Use this template when implementing or reviewing ARIA attributes, keyboard navigation, live regions, focus management, or accessible data table structure in a Lightning Web Component.

## Scope

**Skill:** `lwc-accessibility-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before writing any code.

- **What ARIA pattern is needed?** (labeling / live region / custom widget role / table structure)
- **Does the component cross shadow boundaries?** (yes/no — if yes, IDREF attributes will not work)
- **Is this an AppExchange package?** (yes/no — if yes, WCAG 2.1 AA is a hard requirement)
- **Which interactive states need focus management?** (open / close / save / error)

## Accessibility Contract

Document the keyboard and ARIA contract before writing markup:

- **Keyboard entry point:** (which element receives initial focus)
- **Expected tab order:** (describe the sequence)
- **Focus target on open:** (element that should receive focus when this opens)
- **Focus target on validation error:** (first invalid field or error summary)
- **Focus target on close/dismiss:** (element that launched the overlay)
- **Live region needed?** (yes/no — what events should be announced)
- **Custom widget role?** (listbox / menu / grid / tabpanel / dialog / none)

## Pattern Selected

Which pattern from SKILL.md applies? Why?

- [ ] Live region for async announcements
- [ ] Custom listbox with Arrow key navigation
- [ ] Accessible data table with role="grid"
- [ ] div-as-button (last resort)
- [ ] Focus management via @api method
- [ ] aria-label / aria-labelledby labeling

## Implementation Checklist

Tick each item as you verify it in code and in manual testing:

- [ ] All ARIA IDREF values (`aria-controls`, `aria-owns`, `aria-activedescendant`) are in the same component template as the element they reference.
- [ ] Custom interactive elements have `role`, `tabindex="0"`, and `onkeydown` for Enter/Space.
- [ ] Custom listbox/menu implements Arrow, Home, End, Enter, Escape key handlers with `event.preventDefault()` on navigation keys.
- [ ] Live region (`aria-live`) is always present in DOM (not conditionally rendered); text is updated after async operation completes.
- [ ] Focus is explicitly placed after open, close, save, and error transitions.
- [ ] Custom data table uses `role="grid"`, `aria-rowcount`, `aria-colcount`, `role="row"`, `role="gridcell"` (or `lightning-datatable` is used).
- [ ] `aria-label` or `aria-labelledby` is present on every interactive control — not both on the same element.
- [ ] WCAG 2.1 AA criteria verified: 1.3.1, 2.1.1, 2.4.3, 4.1.2.
- [ ] Keyboard-only testing completed: Tab, Shift+Tab, Arrow keys, Enter, Space, Escape.
- [ ] Screen reader testing completed with VoiceOver or NVDA.

## Notes

Record any deviations from the standard pattern and why they were made. Note any platform constraints encountered (shadow DOM limitations, LWS restrictions, etc.).
