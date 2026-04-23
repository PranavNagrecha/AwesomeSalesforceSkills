---
name: screen-flow-accessibility
description: "Use when building Screen Flows that must meet accessibility standards (WCAG 2.1 AA, Salesforce accessibility guidelines). Covers keyboard navigation, focus order, labels, error messaging, color contrast, and screen reader compatibility. Does NOT cover LWC a11y (see lwc-accessibility) or general record-page a11y."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Security
triggers:
  - "accessible screen flow"
  - "wcag for salesforce flow"
  - "keyboard navigation screen flow"
  - "screen reader friendly flow"
  - "flow accessibility audit"
tags:
  - flow
  - screen-flow
  - accessibility
  - wcag
  - a11y
inputs:
  - Screen Flow under design or review
  - Users' assistive technology profile (if known)
  - Legal / procurement accessibility requirements
outputs:
  - Accessibility audit of the flow
  - Remediation list mapped to WCAG 2.1 success criteria
  - Updated screens with accessible labels, grouping, and error handling
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Screen Flow Accessibility

## Purpose

Screen Flows are a common way to ship end-user experiences fast, but the
default Flow Builder output often fails accessibility checks: unlabeled radio
groups, help text hidden from screen readers, validation errors that do not
announce, and custom LWCs dropped into screens without focus management. This
skill gives a deterministic checklist to design and audit Screen Flows
against WCAG 2.1 AA and Salesforce accessibility expectations.

## When To Use

- Designing any Screen Flow that faces an external user or a broad internal
  audience.
- Procurement or legal is asking for a VPAT / accessibility attestation.
- Users on assistive tech (screen readers, switch control, keyboard-only)
  report problems.
- Replacing a Visualforce or legacy JS page with a Screen Flow — accessibility
  debts typically transfer.

## Recommended Workflow

1. **Inventory screens.** For each screen, list the components, labels, and
   where dynamic content appears.
2. **Label everything.** Every input, picklist, radio group, and section has
   a visible or programmatic label. Help text is associated, not orphaned.
3. **Design focus order.** Tab order should match visual order. After a
   validation error, focus moves to the first invalid field or an error
   summary.
4. **Announce errors.** Use a consistent error summary block at the top of
   the screen, ARIA-live for dynamic errors, and inline field-level messages.
5. **Check color and contrast.** Do not rely on color alone to indicate
   required fields, errors, or status.
6. **Test keyboard-only.** Walk the entire flow with Tab/Shift-Tab/Enter/Space
   — no mouse. Anything that requires a mouse fails.
7. **Test with a screen reader.** NVDA + Firefox or VoiceOver + Safari are the
   baseline. Note missed announcements, skipped labels, and trap points.

## Component-Level Checklist

| Component | Watch For |
|---|---|
| Display Text | Semantic HTML only; avoid decorative images; alt text if meaningful |
| Radio / Picklist | Group label, not just per-option labels |
| Checkbox group | Fieldset + legend equivalent |
| Custom LWC on screen | Must expose labels, handle focus, implement ARIA |
| File Upload | Accessible label, error messaging, progress feedback |
| Section / Row | Do not rely on visual-only grouping |

## Error Handling Pattern

- On validation failure, render an error summary at the top with a link to each
  invalid field.
- Move focus to the summary, not silently to the first field.
- Inline error text uses ARIA `aria-describedby` linkage, not just red color.
- Do NOT flash-and-hide — persistent errors give assistive tech time to
  announce.

## Focus And Keyboard

- First focusable element on each screen receives focus on load.
- Tab order follows visual order.
- No custom JS steals focus without restoring it.
- Esc / Enter behave predictably (Enter submits, Esc does not destroy
  progress).

## Color Contrast

- 4.5:1 for normal text, 3:1 for large text and UI icons.
- Required markers and error states use text + icon, not just color.
- Avoid "green = good, red = bad" as the only signal.

## Screen Reader Hygiene

- Hidden decorative content uses `aria-hidden="true"`.
- Live regions announce asynchronous updates.
- Tables have headers; lists are marked up as lists.
- Heading levels are hierarchical.

## Anti-Patterns (see references/llm-anti-patterns.md)

- Putting all labels in placeholder text.
- Red asterisk as the only "required" signal.
- Silent validation where errors appear visually but are not announced.
- Drop-in custom LWCs that never ran an a11y audit.
- "We'll do accessibility at the end."

## Official Sources Used

- Salesforce Accessibility — https://help.salesforce.com/s/articleView?id=sf.accessibility_overview.htm
- Flow Builder Screen Components — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen.htm
- WCAG 2.1 — https://www.w3.org/TR/WCAG21/
- Salesforce Lightning Design System Accessibility — https://www.lightningdesignsystem.com/accessibility/overview/
