# LLM Anti-Patterns — Screen Flow Radio Button Group

Common mistakes AI coding assistants make when generating or advising on the Screen Flow
Radio Button Group component. These patterns help the consuming agent self-check its output.

## Anti-Pattern 1: Asserting a GA/Beta status or the wrong release

**What the LLM generates:** "the Radio Button Group, generally available since Spring '25…"
or a confident "this Beta component…" — a maturity label and/or a release the sources don't
support.

**Why it happens:** models pattern-fill maturity phrasing and default to familiar release
names; the actual release notes carry a feature *title* but no Beta/Pilot stamp.

**Correct pattern:**

```
Radio Button Group is a Summer '26 screen-component addition. The release notes do not
label it Beta or Pilot — do not assert a GA/Beta/Pilot maturity the notes don't state.
```

**Detection hint:** any "Generally Available"/"Beta"/"Pilot" claim, or a release other than
Summer '26, without a release-notes citation.

---

## Anti-Pattern 2: Assuming multi-select still returns a single value

**What the LLM generates:** turns on *Let Users Select Multiple Options* but keeps the
selection in a single-value variable and reads it with an `equals` Decision.

**Why it happens:** the model treats the toggle as cosmetic and doesn't surface that the
output shape changes from a scalar to a collection.

**Correct pattern:**

```
Multi-select → store into a COLLECTION variable; branch with Contains / loop iteration.
Single-select → single-value variable; equals is fine.
```

**Detection hint:** *Let Users Select Multiple Options = ON* alongside a single-value stored
variable or an `equals` check on the selection.

---

## Anti-Pattern 3: Hallucinating the metadata serialization

**What the LLM generates:** a made-up `<fieldType>RadioButtonGroup</fieldType>` (or a
specific orientation/componentName enum) presented as verified metadata for the new component.

**Why it happens:** the model fills the gap with a plausible-looking enum rather than admitting
the exact serialization isn't in the fetched sources.

**Correct pattern:**

```xml
<!-- Wire the component to its options via choiceReferences (the shared, verifiable part).
     Choose the component type / orientation / multi-select setting in the Flow Builder
     screen editor rather than inventing a metadata enum you can't cite. -->
<fields>
    <name>MyChoiceField</name>
    <choiceReferences>My_Choice_A</choiceReferences>
    <choiceReferences>My_Choice_B</choiceReferences>
    <dataType>String</dataType>
    <fieldText>Pick one</fieldText>
</fields>
```

**Detection hint:** a confidently-stated new `<fieldType>`/enum value with no source, especially
one the release notes never name.

---

## Anti-Pattern 4: Hard-coding options instead of using choices

**What the LLM generates:** option labels baked into the component (or a formula) rather than a
Choice resource / dynamic choice set, and no handling for an empty option list.

**Why it happens:** hard-coded lists are the shortest path and dominate generic UI examples.

**Correct pattern:**

```
Static options  → one Choice resource per option (Choice Label + Stored Value).
Data-driven     → Picklist / Record / Collection Choice Set, WITH an empty-state path.
```

**Detection hint:** option text embedded in the component with no `Choice` resource, or a
dynamic source with no zero-result branch.

---

## Anti-Pattern 5: Confusing it with an orientation setting on Radio Buttons

**What the LLM generates:** "just set the existing Radio Buttons component's orientation to
horizontal" — treating the compact layout as a property of the old component rather than a
distinct Radio Button Group component.

**Why it happens:** the model generalizes "horizontal radio buttons" to a CSS/orientation toggle
it has seen elsewhere.

**Correct pattern:** describe Radio Button Group as its own component with responsive box layout
(horizontal desktop / vertical mobile) and the *Let Users Select Multiple Options* setting; the
traditional Radio Buttons component remains a separate, single-column control.

**Detection hint:** advice to "change orientation to horizontal" on Radio Buttons, or wording
that implies the two are the same component with a flag.

---

## Anti-Pattern 6: Claiming it works in any flow type

**What the LLM generates:** guidance to add a Radio Button Group (or its Choice resource) to a
record-triggered, scheduled, or autolaunched flow.

**Why it happens:** the model treats screen components as universally available across flow types.

**Correct pattern:** state that the component — and the Choice resource it depends on — exists
only in **Screen Flows**; there's no screen to render it on in a headless flow.

**Detection hint:** a Choice resource or screen component referenced from a non-screen flow
(`RecordBeforeSave`/`RecordAfterSave`/`Scheduled`/autolaunched) `processType`.
