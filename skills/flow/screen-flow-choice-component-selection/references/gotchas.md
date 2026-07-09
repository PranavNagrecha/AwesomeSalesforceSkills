# Gotchas — Screen Flow Choice Component Selection

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Multi-select components can't feed a Loop or Transform

**What happens:** you build a screen with a Multi-Select Picklist (or Checkbox Group, or Choice
Lookup), add a Loop or Transform to process each selected value, and the element won't accept
the selection as its collection input.

**When it occurs:** the Checkbox Group, Choice Lookup, and Multi-Select Picklist components are
incompatible with Transform and Loop elements. The incompatibility isn't visible while you're
laying out the screen — it surfaces only when you wire the downstream element.

**How to avoid:** decide whether the selection must be iterated *before* choosing the component.
If it must, use a Data Table over a record collection — its selected-rows output is a genuine
collection a Loop can walk. Reserve the multi-select components for cases where the combined
selection is stored or evaluated as a whole, not iterated.

---

## Gotcha 2: Multi-Select Picklist silently drops markup between angle brackets

**What happens:** a choice label like `Priority <High>` or any rich-text/HTML fragment renders
blank or truncated in a Multi-Select Picklist, with no error at design time.

**When it occurs:** rich text isn't supported in the Multi-Select Picklist component, and the
component doesn't show text between the `<` and `>` characters. Labels sourced from a field or a
formula that happens to contain angle brackets hit this quietly.

**How to avoid:** use Checkbox Group when choice labels carry markup or angle brackets, or strip
the markup from the label. Preview the screen with representative data before shipping.

---

## Gotcha 3: Dependent Picklists depends on setup you may not have done

**What happens:** you drop a Dependent Picklists component and it shows nothing, or the second
picklist never filters.

**When it occurs:** the component reads an *existing* field dependency in the org — it does not
create one. Without a field dependency defined in Setup for the two picklist fields, there's
nothing to display. The controlling field must be a picklist (with at least one and fewer than
300 values) or a checkbox on the same object.

**How to avoid:** define the field dependency in Setup first, confirm the controlling field
meets the picklist/checkbox constraint, then add the component. Also note a null-handling
quirk: screen input values are set to null when hidden by conditional visibility, but hidden
picklists inside a Dependent Picklists component aren't nulled unless the *entire* component is
hidden.

---

## Gotcha 4: Radio Button Group is new — don't overstate its maturity

**What happens:** an assistant or a design doc labels the Radio Button Group component "GA since
Summer '26" or "Beta," and a reviewer can't confirm the claim against the docs.

**When it occurs:** Radio Button Group was introduced in the Summer '26 release notes. Its
release-note title carries no "(Beta)" or "(Pilot)" qualifier — unlike sibling Beta features
released the same season — which is consistent with GA, but the docs do not print the literal
phrase "Generally Available" for it.

**How to avoid:** describe it as introduced in Summer '26 and behaviorally equivalent to Radio
Buttons, without asserting a maturity label the release notes don't state. If a customer needs a
guaranteed maturity commitment, confirm the current wording in the live release notes.

---

## Gotcha 5: The component and the Choice resource are separate decisions

**What happens:** a builder assumes "Picklist Choice Set" means the values must render as a
Picklist, or that switching from Radio Buttons to a Checkbox Group requires rebuilding the
underlying data.

**When it occurs:** the Choice resource (Choice, Record Choice Set, Picklist Choice Set) is the
data source; the component is the widget. The same Record Choice Set can back a Picklist, Radio
Buttons, or a Checkbox Group. Flow Builder even lets you switch between choice components (and
the "Let Users Select Multiple Options" toggle flips a single-select component to its
multi-select equivalent) without re-authoring the resource.

**How to avoid:** treat "which resource populates the choices" and "which component displays
them" as two independent picks. Changing the widget rarely requires changing the resource — but
switching single-select to multi-select does change downstream compatibility (see Gotcha 1).
