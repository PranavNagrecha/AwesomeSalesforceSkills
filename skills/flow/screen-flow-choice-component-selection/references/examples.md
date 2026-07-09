# Examples — Screen Flow Choice Component Selection

All snippets are illustrative Flow metadata (`*.flow-meta.xml`) fragments authored from the
official Flow screen-component references. Element and API names are placeholders — replace
with your own. The point of each example is the *selection decision*, not a full flow.

## Example 1: Single-select — size drives the widget

**Context:** a support screen flow asks the agent to pick one Case Reason. There are 6 reasons
today, but the "Product" flavor of the same screen must pick from ~300 products.

**Problem:** builders reflexively drop a Picklist for both. Six options in a dropdown hides
them behind a click; 300 options in Radio Buttons is an unscannable wall.

**Solution:** match the widget to the set size. Few options → Radio Buttons (or Radio Button
Group for a compact stacked layout). Large searchable set → Choice Lookup.

Radio Buttons for the short list, backed by a Picklist Choice Set on Case Reason:

```xml
<screens>
    <name>Pick_Case_Reason</name>
    <fields>
        <name>CaseReason</name>
        <fieldType>RadioButtons</fieldType>
        <dataType>String</dataType>
        <choiceReferences>Case_Reason_PicklistChoiceSet</choiceReferences>
        <isRequired>true</isRequired>
    </fields>
</screens>
```

Choice Lookup for the ~300-product set (a ComponentInstance-based screen field):

```xml
<fields>
    <name>ProductChoice</name>
    <fieldType>ComponentInstance</fieldType>
    <extensionName>flowruntime:choiceLookup</extensionName>
    <isRequired>true</isRequired>
</fields>
```

**Why it works:** Radio Buttons and Choice Lookup are both single-select, so the data contract
is identical — only the ergonomics differ. Choice Lookup "lets users search for and select one
option from a set of choices," which is exactly what a 300-item list needs.

---

## Example 2: Multi-select — decide iteration *before* the component

**Context:** an onboarding flow lets a user select several interest areas, then a downstream
Loop creates a child record per selection.

**Problem:** the builder chooses Multi-Select Picklist for the compact UI, adds a Loop over the
selection, and the Loop's collection reference won't accept it — Checkbox Group, Multi-Select
Picklist, and Choice Lookup are all incompatible with Loop and Transform elements.

**Solution (wrong then right):**

```xml
<!-- WRONG: a Loop cannot iterate a Multi-Select Picklist selection -->
<fields>
    <name>InterestAreas</name>
    <fieldType>MultiSelectPicklist</fieldType>
    <choiceReferences>Interest_Area_Choices</choiceReferences>
</fields>
<loops>
    <name>Create_Interest_Records</name>
    <collectionReference>InterestAreas</collectionReference>  <!-- invalid -->
</loops>
```

```xml
<!-- RIGHT: a Data Table returns a record collection the Loop can iterate -->
<fields>
    <name>InterestTable</name>
    <fieldType>ComponentInstance</fieldType>
    <extensionName>flowruntime:datatable</extensionName>
    <!-- input: a record collection of Interest_Area__c rows;
         output: selectedRows, itself a record collection -->
</fields>
<loops>
    <name>Create_Interest_Records</name>
    <collectionReference>InterestTable.selectedRows</collectionReference>  <!-- valid -->
</loops>
```

**Why it works:** the Data Table's selected-rows output is a genuine record collection, so a
Loop can walk it. When the requirement is "let the user pick several, then process each one,"
the record-selection lane (Data Table) is the compatible design — not a multi-select picklist.

---

## Example 3: Dependent Picklists over a hand-built cascade

**Context:** a screen collects Country, then State, where valid States depend on Country.

**Problem:** a builder wires two independent Picklists plus a Decision (or reactive formula) to
filter the second — re-implementing logic the org's field dependency already maintains.

**Solution:** define the Country → State field dependency in Setup, then use one Dependent
Picklists component that reads it:

```xml
<fields>
    <name>CountryState</name>
    <fieldType>ComponentInstance</fieldType>
    <extensionName>flowruntime:dependentPicklists</extensionName>
    <!-- reads the existing Country/State field dependency; no Choice resource needed -->
</fields>
```

**Why it works:** Dependent Picklists "displays picklists in a flow screen where the options for
one picklist depend on the selected value of another picklist using an existing field dependency
in your org." The controlling field must be a picklist (1 to fewer than 300 values) or a
checkbox. The cascade stays correct because it points at the org dependency, not a copy.

---

## Anti-Pattern: reaching for Multi-Select Picklist by default

**What practitioners do:** whenever "the user should be able to pick more than one," they drop a
Multi-Select Picklist, because it's the multi-select control they've seen most.

**What goes wrong:** two failure modes surface late. (1) If any label carries markup, the
Multi-Select Picklist "doesn't show text between the `<` and `>` characters," so choices render
blank. (2) If a Loop or Transform must process the selection, the component can't feed it, and
the screen has to be rebuilt around a Data Table.

**Correct approach:** decide two things before the component: does a label carry rich
text/markup (→ Checkbox Group), and must the selection be iterated downstream (→ Data Table over
a record collection)? Only when both answers are "no" is Multi-Select Picklist the compact,
correct pick. Checkbox Group is the safer multi-select default for small, markup-bearing lists.
