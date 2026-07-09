---
name: screen-flow-choice-component-selection
description: "Use when picking which Screen Flow component collects a choice from users — Picklist, Radio Buttons, Radio Button Group (Summer '26), Multi-Select Picklist, Checkbox Group, Choice Lookup, Dependent Picklists, or Data Table — and which Choice resource (Choice, Record Choice Set, Picklist Choice Set) populates it. Covers single- vs multi-select semantics, the Loop/Transform incompatibility of the multi-select components, and set-size/searchability tradeoffs. NOT for building the choice-set resource internals from records or picklist fields (use flow/flow-dynamic-choices), NOT the deep configuration of one component (see flow/screen-flow-radio-button-group, flow/flow-data-tables), and NOT general screen UX, navigation, or input validation (see flow/screen-flows, flow/flow-screen-input-validation-patterns)."
category: flow
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Operational Excellence
  - Performance
triggers:
  - "choosing the right choice component for a flow screen when users pick one option"
  - "deciding between Checkbox Group and Multi-Select Picklist for a multi-select flow screen"
  - "picking a screen component that scans well when a radio button list is too long"
  - "letting users search and select one value from a large set on a flow screen"
  - "figuring out why a multi-select picklist can't feed a Loop or Transform element"
tags:
  - screen-flows
  - choice-components
  - single-vs-multi-select
  - choice-resources
  - component-selection
inputs:
  - "The screen requirement: what you collect, single vs multiple selection, and where the choices come from (static list, filtered records, an existing picklist field, or a field dependency)"
  - "Expected size of the choice set and whether the selection must be iterated downstream in a Loop or Transform element"
  - "Target surface (desktop vs mobile) and any picklist field dependencies already defined in the org"
outputs:
  - "A recommended screen component (Picklist, Radio Buttons, Radio Button Group, Multi-Select Picklist, Checkbox Group, Choice Lookup, Dependent Picklists, or Data Table) with the reason"
  - "The matching Choice resource type (Choice, Record Choice Set, or Picklist Choice Set) or field dependency to populate it"
  - "Downstream-compatibility warnings (e.g. Loop/Transform incompatibility) and a fallback design"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# Screen Flow Choice Component Selection

This skill activates when a builder must pick *which* Screen Flow component presents a set of options — and which Choice resource feeds it. Salesforce ships at least seven choice-oriented screen components plus a record-selection Data Table, each with different single/multi-select semantics, downstream compatibility, and set-size ergonomics. Salesforce maintains a dedicated decision-guide article for exactly this call, and Flow Builder even lets you swap between choice components after the fact — evidence that builders regularly pick the wrong one. Use this skill to make the choice deliberately instead of reaching for a Picklist by reflex.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the selection cardinality.** With the Picklist and Radio Buttons (and Radio Button Group) components, users select **only one** choice. With the Multi-Select Picklist and Checkbox Group components, users can select **multiple** choices. This is the first fork in the decision and it constrains every other option.
- **Identify where the choices come from.** Three Choice resource types feed the components: a **Choice** (manually entered values), a **Record Choice Set** (a filtered set of records), or a **Picklist Choice Set** (values from an existing org picklist field). Dependent Picklists is different — it reuses an existing field dependency, not a Choice resource.
- **Ask whether the selection must be iterated.** The Checkbox Group, Choice Lookup, and Multi-Select Picklist components are **incompatible with Transform and Loop elements**. If a downstream Loop or Transform has to process each selected value, those three are off the table — model with a Data Table over a record collection instead.
- **Know the Radio Button Group maturity.** The Radio Button Group component was introduced in the **Summer '26** release notes. Its release-note title carries no "(Beta)" or "(Pilot)" qualifier (unlike sibling Beta features shipped the same season), which is consistent with GA — but the docs do **not** print the literal phrase "Generally Available" for it. Do not assert a maturity label the release notes don't state; confirm exact wording before promising GA behavior to a customer.

---

## Core Concepts

### The component catalog

Every choice-collection decision resolves to one row of this catalog. Cardinality and Loop/Transform compatibility are the two properties that most often force the choice:

| Component | Selection | Best when | Loop / Transform |
|---|---|---|---|
| Picklist (dropdown) | Single | Medium list; save vertical space | Compatible |
| Radio Buttons | Single | Short list; show all options at once | Compatible |
| Radio Button Group *(Summer '26)* | Single | Short list; compact stacked layout | Compatible |
| Choice Lookup | Single | Large list; user searches then picks one | **Incompatible** |
| Dependent Picklists | Single (chained) | Options depend on a prior picklist value | Compatible |
| Checkbox Group | Multiple | Few options; show all as checkboxes | **Incompatible** |
| Multi-Select Picklist | Multiple | Many options; compact multi-select | **Incompatible** |
| Data Table | Single or multiple **rows** | Select record(s) from a record collection | Collection output is Loop-friendly |

### Choice resources — what populates a component

A component is the *widget*; a Choice resource is the *data*. You mix and match:

- **Choice** — "Give users simple values to choose from." You enter each value manually (Yes/No, High/Medium/Low).
- **Record Choice Set** — "Present users with a filtered set of records to choose from" (e.g. products in a family, contacts on an account). Because it surfaces live records, it must respect the running user's record access and field-level security.
- **Picklist Choice Set** — "Present users with a set of values that are defined in an existing picklist." This reuses an org picklist field, so the flow tracks the field's values instead of a hand-maintained copy.

The same Record Choice Set can back a Picklist, Radio Buttons, or a Checkbox Group — the resource and the component are independent decisions. Dependent Picklists and Choice Lookup are the exceptions: Dependent Picklists reads an org field dependency directly, and Choice Lookup draws from a choice source you configure on the component.

### Single-select layout is a UX choice, not a behavior change

Picklist, Radio Buttons, and Radio Button Group are behaviorally identical — the user picks exactly one value. They differ only in layout. Radio Buttons render a vertical list where every option is visible; Radio Button Group "presents horizontally (desktop) or vertically (mobile devices) stacked choices that are compact and easier to scan" and "functions like the traditional Radio Buttons component where users select a single option at run time." A Picklist collapses the list into a dropdown to save space. Choice Lookup adds typeahead search for cases where even a dropdown is unwieldy. Because these are interchangeable at the data layer, Flow Builder lets you switch between choice components (the "Let Users Select Multiple Options" toggle also flips a single-select component to its multi-select equivalent) without rebuilding the screen.

---

## Common Patterns

### Right-size the single-select widget to the set size

**When to use:** the user picks exactly one value and you're deciding between Radio Buttons, Radio Button Group, Picklist, and Choice Lookup.

**How it works:** scale the widget to the number of options. A handful of options → Radio Buttons or Radio Button Group so every choice is visible at a glance (Radio Button Group when horizontal/compact scanning matters). A medium list → Picklist to reclaim vertical space. Dozens or hundreds of options → Choice Lookup, which "lets users search for and select one option from a set of choices on a flow screen" instead of forcing a scroll.

**Why not the alternative:** a Radio Buttons list of 40 options is unscannable and pushes the rest of the screen below the fold; a Picklist of 200 options is a scroll marathon. Matching widget to set size is the core of this skill.

### Choose the multi-select component by downstream needs, not looks

**When to use:** the user selects several values and you're deciding between Checkbox Group and Multi-Select Picklist.

**How it works:** if the choice set is small and you want every option visible, use Checkbox Group; if it's long and you want a compact control, use Multi-Select Picklist. But first check what happens to the selection: **all three multi-value components (Checkbox Group, Multi-Select Picklist, Choice Lookup) are incompatible with Loop and Transform elements.** If a later Loop or Transform must process each selected value, neither multi-select component works — restructure around a **Data Table** over a record collection, whose selected-rows output *is* a collection a Loop can iterate.

**Why not the alternative:** teams pick Multi-Select Picklist for the compact UI, wire a Loop to the selection, and only discover at build time that the Loop can't reference it. Deciding on iteration *before* the component avoids a rebuild.

### Reuse an existing field dependency instead of hand-building cascades

**When to use:** the value list for one picklist depends on the value chosen in another (Country → State, Product Family → Product).

**How it works:** the Dependent Picklists component "displays picklists in a flow screen where the options for one picklist depend on the selected value of another picklist using an existing field dependency in your org." Define the field dependency in Setup first, then drop the component on the screen — it reads the dependency automatically. The controlling field must be a picklist (with at least one and fewer than 300 values) or a checkbox on the same object.

**Why not the alternative:** simulating the cascade with two independent Picklists plus Decision elements or reactive formulas re-implements logic the platform already maintains, and drifts whenever the field dependency changes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Pick exactly one, short list (~2–7) | Radio Buttons or Radio Button Group | Every option visible; Radio Button Group stacks compactly (Summer '26) |
| Pick exactly one, medium list | Picklist (dropdown) | Compact; reclaims vertical screen space |
| Pick exactly one, large/searchable list | Choice Lookup | Typeahead search for one option among many |
| Options depend on a prior picklist value | Dependent Picklists | Reuses an existing org field dependency |
| Pick several, few options | Checkbox Group | Checkbox layout shows all options |
| Pick several, many options | Multi-Select Picklist | Compact multi-select control |
| Selection must feed a Loop or Transform | Data Table over a record collection — **not** Checkbox Group / Multi-Select Picklist / Choice Lookup | Those three are incompatible with Loop and Transform |
| Select one or more **records** (rows) | Data Table | Row selection with a Loop-friendly collection output |
| Choices are filtered records | Any component + Record Choice Set | Presents a filtered set of records (respect record/FLS access) |
| Choices mirror an existing picklist field | Any component + Picklist Choice Set | Tracks the field's values instead of a copy |
| Choices are a small fixed list | Any component + Choice resource | Manually entered values |
| Choices contain rich text or markup | Checkbox Group, not Multi-Select Picklist | Multi-Select Picklist doesn't support rich text and hides text between `<` and `>` |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Characterize the requirement** — confirm single vs multiple selection, where the choices originate (static list, filtered records, an existing picklist field, or a field dependency), the expected set size, and whether the selection must be iterated in a Loop or Transform.
2. **Pick the cardinality lane** — single-select (Picklist, Radio Buttons, Radio Button Group, Choice Lookup, Dependent Picklists), multi-select (Checkbox Group, Multi-Select Picklist), or record-row selection (Data Table).
3. **Choose the component within the lane** — apply the Decision Guidance table, weighting set size, scannability, search, dependency, and target surface (desktop vs mobile).
4. **Choose the Choice resource** — Choice, Record Choice Set, or Picklist Choice Set (or a field dependency for Dependent Picklists) to populate the component. Confirm a Record Choice Set exposes only records/fields the running user may see.
5. **Check downstream compatibility** — if a Loop or Transform must process the selection, reject Checkbox Group / Multi-Select Picklist / Choice Lookup and redesign around a Data Table + record collection.
6. **Validate on target surfaces** — verify layout on desktop and mobile, confirm no unstated maturity assumption for Radio Button Group, and run `scripts/check_screen_flow_choice_component_selection.py` against the flow metadata to catch Loop/Transform incompatibilities and oversized single-select lists.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Selection cardinality (single vs multiple) matches the chosen component
- [ ] Set size justifies the widget (Choice Lookup for large searchable lists, not a 200-item Picklist)
- [ ] No Loop or Transform element references a Checkbox Group, Multi-Select Picklist, or Choice Lookup selection
- [ ] The Choice resource type (Choice / Record Choice Set / Picklist Choice Set) or field dependency fits the source of the values
- [ ] A Record Choice Set surfaces only records and fields the running user is entitled to see
- [ ] Multi-Select Picklist is not used for rich-text or markup-bearing choices
- [ ] Any Radio Button Group claim avoids stating a maturity level the Summer '26 release notes don't state

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Multi-select components can't feed Loops or Transforms** — Checkbox Group, Multi-Select Picklist, and Choice Lookup are incompatible with Transform and Loop elements. You discover this only when you try to wire the Loop, after the screen is built. Decide on iteration first.
2. **Multi-Select Picklist silently swallows markup** — it doesn't support rich text and "doesn't show text between the `<` and `>` characters," so choice labels containing angle brackets render blank or truncated. Use Checkbox Group when labels carry markup.
3. **Dependent Picklists needs the dependency defined first** — the component reads an *existing* org field dependency; without one defined in Setup it has nothing to display. Also, hidden picklists inside a Dependent Picklists component aren't set to null on conditional visibility unless the whole component is hidden — unlike other screen inputs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Component + resource recommendation | The chosen screen component and the Choice resource (or field dependency) that populates it, with the reason |
| Downstream-compatibility note | Whether the selection can feed a Loop/Transform, and the Data Table fallback design if not |
| `templates/screen-flow-choice-component-selection-template.md` | A selection worksheet that walks the cardinality → source → size → iteration decision to a recommendation |
| `scripts/check_screen_flow_choice_component_selection.py` | Stdlib checker that flags multi-select components fed to Loop/Transform and oversized single-select choice lists in flow metadata |

---

## Related Skills

- `flow/flow-dynamic-choices` — build the Record Choice Set / Picklist Choice Set / dependent choice resources this skill selects a component for.
- `flow/flow-resource-patterns` — the full Choice / Record Choice Set / Picklist Choice Set resource model and where each lives in scope.
- `flow/screen-flow-radio-button-group` — deep configuration of the Summer '26 Radio Button Group component once this skill has selected it.
- `flow/flow-data-tables` — the Data Table row-selection mechanics used as the Loop-friendly fallback for multi-select scenarios.
- `flow/screen-flows` — general screen navigation, commit timing, and UX once the component is chosen.
