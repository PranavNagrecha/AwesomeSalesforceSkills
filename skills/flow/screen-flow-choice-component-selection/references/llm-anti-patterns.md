# LLM Anti-Patterns — Screen Flow Choice Component Selection

Common mistakes AI coding assistants make when generating or advising on Screen Flow choice
component selection. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Multi-Select Picklist, then wiring a Loop over it

**What the LLM generates:** "Use a Multi-Select Picklist so users can pick several, then Loop
over the selected values to create a record for each."

**Why it happens:** the model reasons about UI (multi-select control) and downstream processing
(iterate the selection) independently, and doesn't surface the documented incompatibility
between them.

**Correct pattern:**

```text
Need to iterate the selection in a Loop/Transform?
  → Do NOT use Checkbox Group, Multi-Select Picklist, or Choice Lookup.
  → Use a Data Table over a record collection; iterate its selectedRows output.
```

**Detection hint:** a `<loops>`/`<transforms>` element whose `collectionReference` /
`elementReference` names a `MultiSelectPicklist`, `MultiSelectCheckboxes`, or Choice Lookup
screen field.

---

## Anti-Pattern 2: Defaulting every "pick one" to a Picklist

**What the LLM generates:** a Picklist for a 3-option choice and a Picklist for a 300-option
choice alike, because "Picklist" is the most common single-select control in training data.

**Why it happens:** Picklist is the highest-frequency token for "choose one" and the model
doesn't reason about set size or scannability.

**Correct pattern:**

```text
Single-select, few options   → Radio Buttons / Radio Button Group (all visible)
Single-select, medium list   → Picklist (compact dropdown)
Single-select, large/search  → Choice Lookup (typeahead)
```

**Detection hint:** a Picklist backed by a choice set with dozens of `choiceReferences`, or a
Radio Buttons field with a very long static choice list.

---

## Anti-Pattern 3: Asserting a maturity level for Radio Button Group

**What the LLM generates:** "Radio Button Group is Generally Available as of Summer '26" or
"it's still Beta."

**Why it happens:** models pattern-fill maturity labels for any release-noted feature, defaulting
to "GA" or copying a "Beta" tag from a sibling feature.

**Correct pattern:** state that it was introduced in the Summer '26 release notes, that its
release-note title carries no "(Beta)"/"(Pilot)" qualifier (consistent with GA), and that the
docs don't print the literal phrase "Generally Available" — so no maturity level is asserted.

**Detection hint:** the strings "Generally Available", "GA", "Beta", or "Pilot" attached to
Radio Button Group without a release-notes citation.

---

## Anti-Pattern 4: Confusing the Choice resource with the component

**What the LLM generates:** "Use a Picklist Choice Set" as the answer to "which component should
I use," conflating the data source with the widget — or claiming a Record Choice Set must render
as a Picklist.

**Why it happens:** the names overlap ("picklist"), and the model treats resource and component
as one concept.

**Correct pattern:**

```text
Component (widget):  Picklist | Radio Buttons | Radio Button Group | Checkbox Group |
                     Multi-Select Picklist | Choice Lookup | Dependent Picklists | Data Table
Resource (data):     Choice | Record Choice Set | Picklist Choice Set  (or a field dependency)
```

**Detection hint:** an answer that names only a resource type when asked for a component, or
insists a given resource forces a specific widget.

---

## Anti-Pattern 5: Hand-building a dependent cascade instead of Dependent Picklists

**What the LLM generates:** two independent Picklists plus a Decision element or a reactive
formula to filter the second list by the first.

**Why it happens:** the model composes primitives it knows well (Picklist + Decision) rather than
reaching for the purpose-built Dependent Picklists component.

**Correct pattern:** if the org already has a field dependency for the two picklist fields, use a
Dependent Picklists component, which reads that dependency directly. Reserve hand-built cascades
for logic that has no field dependency behind it.

**Detection hint:** two Picklist fields where one's visibility/choices are gated by a Decision or
reactive formula on the other, over fields that have a Setup field dependency.

---

## Anti-Pattern 6: Putting rich text or angle-bracket labels in a Multi-Select Picklist

**What the LLM generates:** choice labels containing HTML/markup or `<...>` fragments feeding a
Multi-Select Picklist, expecting them to render.

**Why it happens:** the model assumes all choice components render labels identically and doesn't
know the Multi-Select Picklist limitation.

**Correct pattern:** the Multi-Select Picklist doesn't support rich text and hides text between
`<` and `>`; use a Checkbox Group for markup-bearing labels, or strip the markup.

**Detection hint:** a `MultiSelectPicklist` field whose choice labels contain `<`, `>`, or
rich-text markup.
