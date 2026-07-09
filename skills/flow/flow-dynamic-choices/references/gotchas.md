# Gotchas — Flow Dynamic Choices

## Gotcha 1: Sharing mismatch

**What happens:** User sees choices they can't open.

**When it occurs:** System context overrides sharing.

**How to avoid:** Match flow context to expected visibility.


---

## Gotcha 2: Empty state not handled

**What happens:** User sees empty dropdown; stuck.

**When it occurs:** Filter yields 0 rows.

**How to avoid:** Decision element after the Get → branch to message.


---

## Gotcha 3: Inactive picklist values

**What happens:** Historical values invisible.

**When it occurs:** Historical records display.

**How to avoid:** Mix Record Choice Set with active flag, or show inactive as read-only.


---

## Gotcha 4: Visual Picker choice with no icon

**What happens:** The choice shows up but not as an icon tile — the visual cue you wanted is missing.

**When it occurs:** A Choice resource is fed to a Visual Picker component without an icon attached. The icon is what makes it render as a tile.

**How to avoid:** Attach an icon to every Choice resource before pointing a Visual Picker at it. If choices legitimately have no icon, use a Picklist or Radio Buttons component instead of a Visual Picker.


---

## Gotcha 5: Choice Lookup display cap hides distant options

**What happens:** A user can't reach a record that exists in the underlying set.

**When it occurs:** Choice Lookup renders 20 options initially, loads 100 more each scroll, and caps at 1,020 displayed choices (reapplying a filter resets to 20). An unfiltered set larger than that leaves records unreachable by scrolling.

**How to avoid:** Filter the Record or Collection Choice Set down to a workable size and rely on the component's typeahead search rather than the scroll cap.


---

## Gotcha 6: Multi-select Choice Lookup needs a collection output and Lightning runtime

**What happens:** Selections are lost, or the component doesn't work at all.

**When it occurs:** "Let Users Select Multiple Options" = Yes lets users pick up to 25 choices, but the output has to go to a collection variable, and multi-select Choice Lookup isn't supported in Classic runtime for flows.

**How to avoid:** Wire the multi-select output to a collection and run the flow in Lightning runtime. With a single-select Choice Lookup over a record choice set, only the last record the user selects is stored — expected for single-select, but a trap if you assumed the component held several.

