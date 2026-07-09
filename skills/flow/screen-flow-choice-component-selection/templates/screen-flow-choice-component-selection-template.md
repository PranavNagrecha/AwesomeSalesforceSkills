# Screen Flow Choice Component — Selection Worksheet

Fill this out per screen field that collects a choice. Answer the questions top to
bottom; each one narrows the component. Record the result in the Decision box.

**Skill:** `screen-flow-choice-component-selection`

**Screen field / label:** _______________________________________

---

## 1. Cardinality — how many values may the user select?

- [ ] Exactly **one** → single-select lane (Q2)
- [ ] **Several** → multi-select lane (Q3)
- [ ] One or more **records/rows** → **Data Table** (skip to Q5)

## 2. Single-select — how big is the list, and does it depend on another field?

- [ ] Options depend on a prior picklist value → **Dependent Picklists**
      (define the field dependency in Setup first; controlling field = picklist
      with 1 to <300 values, or a checkbox)
- [ ] Short list (~2–7), want all visible → **Radio Buttons** or **Radio Button Group**
      (Radio Button Group = Summer '26, compact stacked layout; single-select like Radio Buttons)
- [ ] Medium list, save space → **Picklist**
- [ ] Large / searchable list → **Choice Lookup** (typeahead)

## 3. Multi-select — do any labels carry markup?

- [ ] Labels contain rich text / `<...>` markup → **Checkbox Group**
      (Multi-Select Picklist hides text between `<` and `>`)
- [ ] Few options, want all visible → **Checkbox Group**
- [ ] Many options, want a compact control → **Multi-Select Picklist**

## 4. Iteration gate (multi-select and Choice Lookup only)

Must a downstream **Loop** or **Transform** process each selected value?

- [ ] **Yes** → Checkbox Group / Multi-Select Picklist / Choice Lookup are **incompatible**
      with Loop/Transform. Redesign around a **Data Table** over a record collection
      (its `selectedRows` output is a Loop-friendly collection).
- [ ] **No** → the multi-select component from Q3 stands.

## 5. Choice resource — what populates the component?

- [ ] Small fixed list of values → **Choice** (entered manually)
- [ ] Filtered set of records → **Record Choice Set**
      (confirm the running user may see those records/fields — FLS + record access)
- [ ] Values from an existing org picklist field → **Picklist Choice Set**
- [ ] (Dependent Picklists / Choice Lookup use a field dependency / configured source, not a Choice resource)

---

## Decision

| Field | Value |
|---|---|
| Selection cardinality | single / multiple / records |
| Chosen component | ____________________ |
| Choice resource / source | ____________________ |
| Feeds a Loop/Transform? | yes / no |
| If yes, redesigned as | Data Table + record collection / n.a. |
| Target surface(s) | desktop / mobile / both |

## Notes / caveats

- If you selected **Radio Button Group**, don't state a maturity level (GA/Beta/Pilot) the
  Summer '26 release notes don't state.
- Re-run `scripts/check_screen_flow_choice_component_selection.py --manifest-dir <path>`
  after building to catch Loop/Transform incompatibilities and oversized single-select lists.
