---
name: screen-flow-accessibility
description: "Screen Flow accessibility — WCAG 2.2 AA, labels, keyboard, error announcements. Triggers: accessible Screen Flow, Flow WCAG, screen reader Flow. NOT for LWC component a11y inside screens — use lwc/lwc-accessibility."
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
  - Remediation list mapped to WCAG 2.2 success criteria
  - Updated screens with accessible labels, grouping, and error handling
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-20
---

# Screen Flow Accessibility

## Purpose

Screen Flows are a fast way to ship an end-user experience, and the default
Flow Builder output routinely fails accessibility checks: requiredness typed as
an asterisk instead of set as a property, instructions hidden behind a help
icon, validation implemented as flow logic so errors detach from their fields,
multi-column layouts whose tab order does not match reading order, and custom
components dropped in with no audit of their own.

The recurring root cause is doing accessibility work in CSS and prose when the
platform had a property for it. Almost every fix in this skill is a metadata
change, not a design change.

**The standard is WCAG 2.2 Level AA.** Salesforce states that Lightning
Experience follows Section 508 of the Rehabilitation Act and WCAG 2.2 Level AA to
the extent possible. Auditing against 2.1 — still the default in most
accessibility guidance — misses six criteria that apply directly to Screen
Flows.

UNVERIFIED (2026-10-20): the corpus holds no WCAG text and no Salesforce accessibility statement (both live on W3C and Help pages outside it), so every criterion number, the 24×24 px figure, the contrast ratios, the 4.1.1 removal and the "Lightning Experience follows WCAG 2.2 AA" quote in this package come from those sources, not from a corpus line. The Flow metadata claims below are grounded in api_meta 264.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which accessibility standard and level is the procurement or legal target? | 2.1 and 2.2 differ by six criteria (Gotcha 1). | WCAG 2.2 AA, or a named deviation. |
| Which containers will the flow run in: Lightning Experience, Experience Cloud, both? | A pass in one container does not carry to the other (Gotcha 8). | A container list for the audit plan. |
| Which fields are inputs that can carry `validationRule`, and which are choice or component fields? | `validationRule` is limited to InputField, LargeTextArea and PasswordField (Gotcha 4). | A per-field plan for attaching errors. |
| Does any field state requiredness with an asterisk or guidance in `helpText`? | These are the two most common metadata-level failures (Gotchas 2 and 3). | A list of fields to move to `isRequired` and Display Text. |
| Are there multi-column sections or conditional reveals? | Reading order and reveals are the author's decisions (Gotchas 5 and 6). | Fields reordered and reveals placed after their triggers. |
| Does any screen contain a `ComponentInstance`? | A custom LWC is a separate audit scope (Gotcha 7). | A named owner and an `lwc/lwc-accessibility` review. |
| Is `allowPause` wanted, and how long are the screens? | Pause adds a footer control when the org setting is on, and long screens lengthen every traversal (Gotchas 9 and 10). | A per-screen `allowPause` decision and a screen-split plan. |

A proper configuration adds metadata-level fixes, a per-container manual audit and an explicit scope for custom components, which a scanner-only pass does not.

## Recommended Workflow

1. **Set the target to WCAG 2.2 AA and list the delta (W3C text, UNVERIFIED 2026-10-20).** Six criteria are new
   at A/AA: 2.4.11 Focus Not Obscured (Minimum, AA), 2.5.7 Dragging Movements
   (AA), 2.5.8 Target Size (Minimum, AA) at 24×24 CSS pixels, 3.2.6 Consistent
   Help (A), 3.3.7 Redundant Entry (A), and 3.3.8 Accessible Authentication
   (Minimum, AA). Note that 4.1.1 Parsing was removed in 2.2.
2. **Move semantics out of prose into properties.** `isRequired` for
   requiredness (never an asterisk in `fieldText`; not supported for DisplayText
   or boolean input fields, api_meta 264 L74482-74484); `validationRule` with an
   `errorMessage` so the message attaches to its field (supported for InputField,
   LargeTextArea and PasswordField only, api_meta 264 L74550-74552); `fieldText` as a visible
   label, never a placeholder.
3. **Fix the reading order in metadata.** Multi-column screens use
   `RegionContainer` and `Region`, and DOM order follows metadata order, not the
   visual grid. Author first column then second, and verify by tabbing.
4. **Make conditional content discoverable.** A field with a `visibilityRule`
   sits immediately after its trigger; the trigger's label states the outcome.
   Test at a narrow viewport, where a reveal can push the focused element under
   a sticky footer.
5. **Rewrite error messages as instructions.** "Enter a postal code in the format
   A1A 1A1," not "Invalid." The wording is the accessibility fix.
6. **Scope every `ComponentInstance` separately.** A custom LWC inherits none of
   the screen's accessibility. Its internals belong to `lwc/lwc-accessibility`;
   refuse to sign off a screen containing an unaudited one.
7. **Run the audit manually, in every container the flow is published to.** One
   keyboard pass and one screen reader pass, in Lightning Experience *and* in
   Experience Cloud if it ships there. Automated scans are a floor, not a
   sign-off.

## What the Platform Gives You, and What It Does Not

| Requirement | Platform property | If you skip it |
|---|---|---|
| Required field | `isRequired` (not for DisplayText or boolean input, L74482-74484) | An asterisk in the label carries no semantics (screen reader "star" announcement: UNVERIFIED 2026-10-20) |
| Field-attached error | `validationRule` + `errorMessage` (InputField, LargeTextArea, PasswordField only, L74550-74552) | A Display Text error block is unassociated and easy to miss |
| Visible label | `fieldText` | A placeholder disappears on typing and has low contrast by design |
| Reading order | Order of `<fields>` within `Region` (UNVERIFIED 2026-10-20: that DOM and tab order follow metadata order is observed behaviour, not documented) | Tab order follows metadata, not layout |
| Conditional content | `visibilityRule` | — but adjacency to the trigger is your decision, not the platform's |
| Supplementary info | `helpText` | — it "appears if the end user clicks the help icon" (api_meta 264 L74449-74450); do not put essentials there |

Nothing on this list is an ARIA attribute, because (UNVERIFIED 2026-10-20: the metadata types expose no such property, but the corpus does not state the negative) a Screen Flow author cannot
set arbitrary attributes on standard components. ARIA advice applies inside a
custom LWC and nowhere else on the screen.

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

- Field-level errors use the field's own `validationRule` with an
  `errorMessage` ("the error message to display when formulaExpression is false",
  api_meta 264 L73389-73390). That is what attaches the message to the field so it is
  announced in context. `validationRule` is supported only on InputField,
  LargeTextArea and PasswordField (api_meta 264 L74550-74552); radio, dropdown,
  multi-select and component fields have none, so use `isRequired` and a Display Text
  message for them.
- The `errorMessage` is a string you write. Write it as an instruction — "Enter a
  postal code in the format A1A 1A1" — not as a verdict.
- Reserve a screen-level Display Text summary for cross-field rules that have no
  single field to attach to. It supplements field-level validation; it does not
  replace it.
- A summary with links that move focus to each invalid field requires a custom
  LWC to implement, which turns a declarative screen into a component audit.
  Weigh that before proposing it.

## Focus And Keyboard

- Tab order follows metadata order within `Region` elements (UNVERIFIED 2026-10-20: observed, not documented), which is what you
  control. Verify by tabbing through with no mouse and writing down the stops.
- Every interactive control must be reachable by Tab / Shift-Tab. Anything
  reachable only by mouse is a failure with no exceptions.
- Radio groups: arrow keys move within the group, Tab exits it (UNVERIFIED 2026-10-20: browser behaviour, not in the corpus).
- The focus indicator must remain visible and unobscured by the flow footer, a
  modal, or a sticky site header — WCAG 2.2's 2.4.11. Test at a narrow viewport,
  where conditional reveals push content around.
- Long screens have no skip mechanism (UNVERIFIED 2026-10-20: the negative is not in the corpus). Screen length is an accessibility
  parameter, not just a layout one. `showFooter` and `showHeader` default to true; hiding them means you must supply navigation and help text in components (api_meta 264 L74235-74240, L74252-74257).

## Color Contrast

- 4.5:1 for normal text, 3:1 for large text and UI components (WCAG values, UNVERIFIED 2026-10-20).
- Colour is never the sole signal (WCAG 1.4.1). Requiredness comes from
  `isRequired`; error state comes from `validationRule` text. Styling then
  reinforces something that already exists rather than carrying it.
- Contrast must be checked against the container the flow actually renders in.
  Brand colours on an Experience Cloud site can fail where the Lightning
  Experience background passed.

## Content Hygiene Inside Display Text

UNVERIFIED (2026-10-20): the metadata describes `fieldText` only as the "field label that is displayed on the screen" supporting merge fields (api_meta 264 L74401-74402); that a Display Text field takes rich-text markup is observed behaviour. Where it does, it can carry markup nobody
reviewed as content:

- Images that convey information need alt text; decorative ones need empty alt.
- Heading levels descend by one — no jumping from `h2` to `h4`.
- Link text describes the destination. "Read the refund policy," not "click
  here."

Read the markup, not the rendered preview.

## Anti-Patterns (see `references/llm-anti-patterns.md`)

- Auditing against WCAG 2.1 when the target is 2.2.
- Prescribing ARIA attributes on standard screen components, which the author
  cannot set.
- Asterisk-in-the-label instead of `isRequired`.
- An error summary built in flow logic instead of `validationRule`.
- Treating `helpText` as a description when it renders behind an interaction.
- Auditing only in Lightning Experience.
- An automated scan as the sign-off.

## Related

- `lwc/lwc-accessibility` — everything inside a `ComponentInstance` field.
- `flow/flow-screen-input-validation-patterns` — validation design in depth.
- `flow/flow-screen-lwc-components` — building and wiring screen components.
- `flow/screen-flow-choice-component-selection` — radio group vs picklist vs
  checkbox group, which is partly an accessibility decision.
- `flow/pause-elements-and-wait-events` — what `allowPause` creates downstream.

## Official Sources Used

- Accessibility Standards (Salesforce) — Section 508 and WCAG 2.2 Level AA — https://help.salesforce.com/s/articleView?id=sf.accessibility_overview.htm&type=5
- Product Accessibility Status (VPATs / Conformance Reports) — https://www.salesforce.com/company/legal/508_accessibility/
- What's New in WCAG 2.2 (W3C) — https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- WCAG 2.2 (W3C Recommendation) — https://www.w3.org/TR/WCAG22/
- Flow metadata type — `FlowScreen` and `FlowScreenField` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Salesforce Lightning Design System Accessibility — https://www.lightningdesignsystem.com/accessibility/overview/

The full annotated list is in `references/well-architected.md`.
