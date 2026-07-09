# Examples — Screen Flow Radio Button Group

All snippets below are illustrative scaffolding authored from the official Summer '26
release notes and the Flow Choice-resource / base-component references. The **Choice**
metadata is the stable, verifiable part you wire the component to; the component type,
orientation, and *Let Users Select Multiple Options* setting are chosen in the Flow
Builder screen editor. Replace API names, labels, and values with your own. Do not
assert a GA/Beta/Pilot status the release notes don't state.

## Example 1: Compact single-select on a dense screen

**Context:** an intake Screen Flow already collects name, email, and a description. It
also needs a "Preferred Contact Method" choice (Email / Phone / Text). A vertical Radio
Buttons list pushes the description field below the fold.

**Problem:** three visible, mutually exclusive options are worth showing at once, but the
traditional single-column radio list costs three vertical slots on an already-tall screen.

**Solution:**

Author one static **Choice** resource per option. In flow metadata each is a `<choices>`
element with a label (`choiceText`) and a stored `value`:

```xml
<!-- One static Choice resource; repeat for Phone and Text -->
<choices>
    <name>Choice_ContactEmail</name>
    <choiceText>Email</choiceText>
    <dataType>String</dataType>
    <value>
        <stringValue>Email</stringValue>
    </value>
</choices>
```

Add the **Radio Button Group** component to the screen, leave *Let Users Select Multiple
Options* off, and reference the three choices. The selection is stored into a single-value
text variable. In metadata the wiring that matters is the field's `choiceReferences` — the
same list all choice components use:

```xml
<!-- Choice-based screen field: references the three Choice resources.
     Component type / orientation is set in the screen editor. -->
<fields>
    <name>PreferredContactMethod</name>
    <choiceReferences>Choice_ContactEmail</choiceReferences>
    <choiceReferences>Choice_ContactPhone</choiceReferences>
    <choiceReferences>Choice_ContactText</choiceReferences>
    <dataType>String</dataType>
    <fieldText>Preferred Contact Method</fieldText>
    <isRequired>true</isRequired>
</fields>
```

**Why it works:** the boxes stack horizontally on desktop and collapse to a vertical stack
on mobile automatically, so all three options stay visible without the vertical cost of a
radio list — the release notes' stated purpose. Because it's single-select, the stored
value is one string, so a downstream `equals` Decision reads it directly.

---

## Example 2: Multi-select via the toggle (collection output)

**Context:** the same flow later asks "Which topics are you interested in?" where a user
may pick several.

**Problem:** the moment more than one selection is allowed, the output stops being a single
value. A Decision or Assignment written for one value silently mishandles a collection.

**Solution:**

Turn on *Let Users Select Multiple Options*. The component now behaves as a Checkbox Group
and outputs a **collection** of stored values — model the target as a text collection, and
read it with a contains-style check instead of `equals`:

```text
Screen component:  Radio Button Group  →  Let Users Select Multiple Options = ON
Stored into:       {!SelectedTopics}   (Text COLLECTION variable, not a single Text)

Downstream Decision "Interested in Billing?":
    Resource:  {!SelectedTopics}
    Operator:  Contains          ← not "Equals"
    Value:     "Billing"
```

If you must branch on multiple members, iterate the collection in a Loop and set a boolean,
rather than chaining `equals` conditions that assume a scalar.

**Why it works:** multi-select maps onto the base checkbox-group contract, whose value is an
array of the selected stored values. Matching the variable type (collection) and the operator
(`Contains` / iteration) to that shape is the whole game — the layout is unchanged; only the
data shape is.

---

## Example 3: Data-driven options from a Record Choice Set (with empty state)

**Context:** the options should be the current user's active Cases, not a hard-coded list.

**Problem:** hard-coding option labels drifts from the data, and a dynamic source that
returns zero rows renders an empty group that strands the user.

**Solution:**

Build a **Record Choice Set** (a dynamic choice) that queries the records, then reference it
from the Radio Button Group exactly as you'd reference static choices. Guard the empty case
before the screen:

```text
1. Get Records (or Record Choice Set filter):  Case WHERE Status != 'Closed' AND OwnerId = {!$User.Id}
2. Decision "Any open cases?":
       {!OpenCases} Is Null = false   →  show the screen with the Radio Button Group
       default (no open cases)        →  show a display-text screen: "You have no open cases."
3. Screen field references the Record Choice Set:
```

```xml
<fields>
    <name>SelectCase</name>
    <choiceReferences>OpenCasesChoiceSet</choiceReferences>  <!-- dynamicChoiceSet name -->
    <dataType>String</dataType>
    <fieldText>Select a case</fieldText>
    <isRequired>true</isRequired>
</fields>
```

**Why it works:** the component only references choices — it doesn't care whether they're
static or dynamic — so the Record Choice Set slots in unchanged. The explicit empty-state
Decision keeps a zero-row query from producing a dead-end screen. Sourcing and filtering the
choice set itself is covered by `flow/flow-dynamic-choices`.

---

## Anti-Pattern: flipping to multi-select without retyping the output

**What practitioners do:** enable *Let Users Select Multiple Options* on an existing
single-select Radio Button Group to "let people pick more than one," and leave the stored
variable and downstream logic untouched.

**What goes wrong:** the component now emits a collection, but the selection is still bound
to a single-value variable and read by `equals` Decisions. Depending on the path this shows
up as an empty value, a type mismatch at save time, or branches that never fire — and often
none of it surfaces at design time.

**Correct approach:** treat single↔multi as a contract change. Retype the stored variable to
a collection, switch downstream Decisions/Assignments to `Contains` or loop iteration, and
re-test on both desktop and mobile. If most consumers assume a scalar, keep the component
single-select and model the rare multi-pick case explicitly instead.
