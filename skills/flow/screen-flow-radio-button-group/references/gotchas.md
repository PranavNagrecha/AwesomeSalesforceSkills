# Gotchas — Screen Flow Radio Button Group

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The multi-select toggle silently changes the output type

**What happens:** you enable *Let Users Select Multiple Options* on a Radio Button Group and
downstream logic quietly breaks — Decisions never fire, an Assignment errors on save, or a
stored value reads as empty.

**When it occurs:** the moment single-select becomes multi-select, the component's output
goes from a single stored value to a **collection** (Checkbox Group behavior). Anything bound
to a single-value variable or read with `equals` no longer matches.

**How to avoid:** treat the toggle as a contract change. Retype the stored variable to a
collection, switch downstream Decisions/Assignments to `Contains` or loop iteration, and
re-test. If most consumers assume a scalar, keep it single-select.

---

## Gotcha 2: A dynamic choice set that returns zero options renders an empty group

**What happens:** the screen shows the label but no selectable boxes, and the user is stuck
with a required field they can't satisfy — with no "no options" message.

**When it occurs:** the component references a Record/Picklist/Collection Choice Set whose
source returns no rows (filter too tight, no matching records, empty collection).

**How to avoid:** add an explicit empty-state path — a Decision before the screen that routes
zero-result runs to a display-text screen, or a fallback that skips the choice entirely.

---

## Gotcha 3: The choice's Stored Value data type must match the target

**What happens:** the selection doesn't land in the variable, or an Assignment/Decision throws
a type error, even though the choice appears correct on screen.

**When it occurs:** a Choice's *Stored Value* (or a dynamic choice set's value field) is a
different data type than the variable/field the component stores into — e.g. a numeric stored
value fed into a Text variable, or a record Id stored where a picklist string is expected.

**How to avoid:** align the Choice Stored Value type with the target variable type up front,
and keep it consistent across every choice the component references.

---

## Gotcha 4: The compact layout is not automatically more accessible

**What happens:** an accessibility audit that passed on a traditional Radio Buttons screen now
flags the Radio Button Group for focus order or contrast on the selected box.

**When it occurs:** the responsive box layout stacks differently on desktop vs mobile and the
selected-state contrast or tab order wasn't verified. The base component's fieldset/legend
grouping helps, but it doesn't guarantee the surrounding layout meets WCAG 2.1 AA.

**How to avoid:** verify label, focus order, and contrast in the compact layout on both form
factors; don't assume the new component inherits a passing audit. See
`flow/screen-flow-accessibility`.

---

## Gotcha 5: Radio Buttons and Radio Button Group are different components

**What happens:** swapping a traditional Radio Buttons field for a Radio Button Group (or vice
versa) doesn't cleanly carry over default selection or references, and the flow renders
differently than expected on mobile.

**When it occurs:** you replace one component with the other mid-build and assume settings,
default value, and downstream wiring migrate automatically. The option source (choices) is
shared, but the component instance, its default-value setting, and its responsive rendering
are its own.

**How to avoid:** re-check the default/required state and the stored variable after swapping,
and debug the screen on **both desktop and a mobile form factor** to confirm the horizontal vs
vertical stacking behaves as intended.
