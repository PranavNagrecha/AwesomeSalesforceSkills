---
name: screen-flow-radio-button-group
description: "Use when adding or configuring the Summer '26 Radio Button Group screen component in a Screen Flow — the compact choice input that lays options out as horizontal boxes on desktop and vertical boxes on mobile, single-select by default with a 'Let Users Select Multiple Options' setting that makes it behave as a Checkbox Group. Covers choosing it over traditional Radio Buttons / Picklist / Checkbox Group, wiring its options to a Choice resource or dynamic choice set, and the single-value-vs-collection output contract. NOT for picking which choice component to use — use flow/screen-flow-choice-component-selection. NOT for building the Record / Picklist Choice Set behind it — use flow/flow-dynamic-choices."
category: flow
salesforce-version: "Summer '26+"
well-architected-pillars:
  - User Experience
  - Reliability
triggers:
  - "make my screen flow radio buttons take up less vertical space"
  - "lay out flow choices as compact horizontal boxes instead of a long single-column list"
  - "add a radio button group to a screen flow"
  - "let users pick multiple options from a radio button group in a flow"
  - "choose between radio buttons, a picklist, and the new radio button group on a flow screen"
tags:
  - screen-flow-radio-button-group
  - flow
  - screen-flow
  - choice-components
  - summer-26
inputs:
  - "The Screen Flow (or Experience Cloud screen flow) and the screen that needs a compact single- or multi-select choice input"
  - "The options and their source: a static Choice resource, or a Picklist / Record / Collection dynamic choice set"
  - "Whether users select one option (radio) or several ('Let Users Select Multiple Options')"
  - "The variable/field the selection is stored into, and its data type (single value vs collection)"
outputs:
  - "A configured Radio Button Group screen component wired to its choices"
  - "A single-select vs multi-select decision with the matching stored-value data type"
  - "A validation, reactivity, and accessibility checklist for the choice screen"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# Screen Flow Radio Button Group

This skill activates when a practitioner wants to use the **Radio Button Group** screen component introduced in Summer '26 — the compact choice input that renders options as boxes stacked horizontally on desktop and vertically on mobile, saving vertical space over the traditional single-column Radio Buttons list. It covers when to pick it, how its options are sourced from a Choice resource, and the single-value-vs-collection contract that the *Let Users Select Multiple Options* setting changes.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the release.** Radio Button Group ships in **Summer '26** for both Flow (the Automate release-notes pillar) and Experience Cloud screen flows. The release notes do **not** stamp it Beta or Pilot — treat it as a standard Summer '26 screen-component addition and do not assert a GA/Beta/Pilot maturity the release notes don't state.
- **Know it's a Screen-Flow-only component.** Like the other choice inputs it draws its options from a **Choice** resource, which is available only in Screen Flows. It has no meaning in a record-triggered, scheduled, or autolaunched flow.
- **Decide single vs multiple up front.** The component is single-select by default. Turning on *Let Users Select Multiple Options* switches it to multi-select and it behaves and labels as a **Checkbox Group**. That decision changes the *data type of the output* (a single value vs a collection), so make it before you wire downstream logic — not after.
- **The most common wrong assumption:** that this is a new orientation toggle on a component you already know, so existing single-value references "just work" if you enable multi-select. They don't — the output shape changes.

---

## Core Concepts

### The component: a compact, responsive choice input

Radio Button Group presents the same options a Radio Buttons component would, but as compact boxes rather than a vertical list of labelled bullets. The layout is **responsive**: boxes stack **horizontally on desktop** and **vertically on mobile devices**. The stated purpose in the release notes is to reduce scrolling and screen real estate compared with traditional radio buttons, checkbox groups, or picklists — useful on dense screens or when a choice sits alongside other fields.

Under the platform, grouped radio selection works the way the base `lightning-radio-group` component does: it renders radio `<input>` elements that share one `name` attribute, so selecting one option deselects any previously selected option in the group. That shared-name grouping is what guarantees the single-selection default; it is not something you configure per option.

### Options come from the Choice resource family

The component does not invent its own option list. It consumes **choices** — the same resource family used by Checkbox Group, Radio Buttons, Picklist, Multi-Select Picklist, and Dependent Picklist. Two kinds exist:

- **Static choices** — a fixed `Choice` resource with a *Choice Label* (what the user sees) and a *Stored Value* (what the flow keeps). Hand-authored, one per option.
- **Dynamic choice sets** — a *Picklist Choice Set* (from field metadata), *Record Choice Set* (from a SOQL query), or *Collection Choice Set* (from a variable). One resource yields many options at runtime.

Because the option list is a resource, the Radio Button Group's job is to *reference* choices, not define them. Sourcing and filtering those choices is the province of `flow/flow-dynamic-choices`.

### The single-value vs collection output contract

This is the concept that causes the most rework. In single-select mode the component stores **one** Stored Value into a single-value variable or field. When *Let Users Select Multiple Options* is on, it stores **many** values — a **collection** — exactly like a Checkbox Group. Any Assignment, Decision, formula, or reactive reference built against a single value will not read a collection correctly. Flip the setting and you must revisit every downstream consumer and the type of the variable the selection lands in.

---

## Common Patterns

### Compact single-select on a dense screen

**When to use:** a screen already has several fields and a short list of mutually exclusive options (a rating, a plan tier, a shipping speed) that a full-height radio list would push below the fold.

**How it works:** add the Radio Button Group component to the screen, leave *Let Users Select Multiple Options* off, and point it at a static Choice resource or a Picklist Choice Set. The boxes lay out horizontally on desktop and collapse to a vertical stack on mobile automatically — no separate mobile layout to maintain.

**Why not the alternative:** a traditional Radio Buttons component is functionally identical but consumes a vertical slot per option; a Picklist hides the options behind a click. When the option count is small and you want the choices *visible* without the vertical cost, the group layout wins.

### Multi-select via the toggle (Checkbox Group behavior)

**When to use:** users may legitimately pick more than one option (interests, add-ons, applicable reasons).

**How it works:** enable *Let Users Select Multiple Options*. The component now behaves as a Checkbox Group and outputs a **collection** of Stored Values. Store it into a collection variable (or a multi-select-capable field), and update every downstream Decision/Assignment to iterate or contains-check rather than equals-check.

**Why not the alternative:** forcing multiple selections through a single-select control (or approximating it with several boolean fields) breaks the responsive layout and complicates validation. The toggle is the supported multi-select path — just budget for the output-shape change.

### Data-driven options via a dynamic choice set

**When to use:** the options are not static — active picklist values, records that match a filter, or an in-memory collection.

**How it works:** build a Picklist/Record/Collection Choice Set (see `flow/flow-dynamic-choices`), then reference it from the Radio Button Group. Always handle the **empty-result** case: a group bound to a dynamic choice set that returns zero options renders nothing and can strand the user.

**Why not the alternative:** hard-coding options that mirror configuration (picklist values, active products) drifts the moment an admin edits the source and forces a flow redeploy to stay correct.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Short list of mutually exclusive options, screen is space-constrained | Radio Button Group, single-select | Compact boxes keep choices visible without the vertical cost of a radio list |
| Same options but plenty of vertical room / accessibility-first audience | Traditional Radio Buttons component | Single-column list is the most familiar, longest-tested layout for screen readers |
| Many options (10+) where showing all at once is noise | Picklist / Dropdown | A dropdown collapses a long list; a box grid of 15 options is its own scrolling problem |
| Users may pick more than one | Radio Button Group with *Let Users Select Multiple Options* on (or a Checkbox Group) | Both yield a collection; the group just does it in the compact layout |
| Options come from records or picklist metadata | Any of the above bound to a **dynamic choice set** | Component choice is orthogonal to the option *source* — see `flow/flow-dynamic-choices` |
| You need a bespoke widget (cards with images, cross-field validation) | An LWC screen component | Choice components render text labels; rich UI belongs in `flow/flow-screen-lwc-components` |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm fit and release.** Verify the target is a Screen Flow (or Experience Cloud screen flow) on Summer '26+ and that the choice is a good fit for a compact box layout (few, mutually exclusive or multi-select options). If it isn't a screen flow, stop — the component doesn't apply.
2. **Decide single vs multiple.** Choose single-select or *Let Users Select Multiple Options* now, and note the resulting output shape (single value vs collection). This decision drives the variable type in step 4.
3. **Build or reuse the choices.** Author a static Choice resource per option, or wire a Picklist/Record/Collection Choice Set. Ensure each choice's *Stored Value* data type matches what downstream logic expects, and plan an empty-state path for dynamic sources.
4. **Add and configure the component.** Drop the Radio Button Group on the screen, reference the choices, set the label, and store the selection into a variable/field whose type matches step 2 (a single-value variable for single-select, a collection for multi-select).
5. **Wire and test downstream logic.** Update Decisions/Assignments/formulas and any reactive references to read the correct shape (`equals` for single value, iterate/`contains` for a collection). Debug the flow on **both desktop and a mobile form factor** to confirm the responsive layout and selection behavior.
6. **Review accessibility and validation.** Confirm the component has a clear label, that required/default behavior matches intent, and that contrast and focus order hold in the compact layout (see `flow/screen-flow-accessibility`). Run the skill's checker against the flow metadata before shipping.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The flow is a Screen Flow / Experience Cloud screen flow, and the component references at least one choice or dynamic choice set
- [ ] Single-select vs *Let Users Select Multiple Options* is a deliberate decision, documented, and matches the option semantics
- [ ] The stored variable/field type matches the output shape (single value for single-select, collection for multi-select)
- [ ] Every downstream Decision/Assignment/formula/reactive reference reads the correct shape after any single↔multi change
- [ ] Dynamic choice sources have an empty-result path so a zero-option group can't strand the user
- [ ] The screen was debugged on **both** desktop and mobile form factors (horizontal vs vertical stacking)
- [ ] Label, required/default state, focus order, and contrast were reviewed for accessibility
- [ ] No GA/Beta/Pilot maturity was asserted beyond "Summer '26 screen-component addition"

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The multi-select toggle silently changes the output type** — turning on *Let Users Select Multiple Options* converts the selection from a single value to a collection. Downstream `equals` checks, single-value assignments, and reactive references built for one value stop matching, usually with no design-time error. Revisit every consumer when you flip it.
2. **A dynamic choice set that returns zero options renders an empty group** — the component shows nothing selectable and there's no built-in "no options" message. Users can stall on the screen. Add an explicit empty-state (a Decision before the screen, or a display-text fallback).
3. **Compact boxes are not automatically more accessible than a radio list** — the responsive box layout can affect focus order and needs sufficient contrast on the selected state. Don't assume the new layout passes an accessibility audit just because the base component uses a fieldset/legend; verify it (see `flow/screen-flow-accessibility`).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Radio Button Group component | A screen component referencing its choices, with the single/multi setting chosen and the selection stored into a correctly-typed variable/field |
| Choice source | A static Choice resource per option, or a Picklist/Record/Collection dynamic choice set with an empty-state path |
| Single-vs-multi decision note | A one-line record of single-select vs *Let Users Select Multiple Options* and the resulting output shape, so downstream logic is built to match |
| Choice-integrity check output | The result of `scripts/check_screen_flow_radio_button_group.py` over the flow metadata (dangling / empty / single-option choice references) |

---

## Related Skills

- `flow/screen-flow-choice-component-selection` — the cross-component decision (Radio Buttons vs Checkbox Group vs Picklist vs Radio Button Group vs LWC) when you're choosing *which* choice input to use, not configuring this one.
- `flow/flow-dynamic-choices` — build the Picklist/Record/Collection Choice Sets this component references, including dependent choices and empty-result handling.
- `flow/flow-reactive-screen-components` — drive downstream components from this one's selection via `{!Component.value}`; mind that the value is a collection in multi-select mode.
- `flow/screen-flow-accessibility` — audit the compact layout for labels, focus order, and contrast against WCAG 2.1 AA.
- `flow/flow-screen-lwc-components` — the alternative when a choice needs rich UI (cards, images, cross-field validation) beyond text-labelled boxes.
