# Radio Button Group — Screen Component Worksheet

Fill this in before and while configuring a Radio Button Group on a Flow screen. It
forces the two decisions that cause the most rework — **single vs multiple** and the
**choice source** — and captures the wiring the checker validates.

> The component type, orientation, and *Let Users Select Multiple Options* setting are
> chosen in the Flow Builder screen editor. This worksheet records those choices and the
> stable metadata (choices ↔ references). Do not assert a GA/Beta/Pilot maturity the
> Summer '26 release notes don't state.

## 1. Fit check

- Flow API name:
- Flow type (must be a **Screen Flow** / Experience Cloud screen flow):
- Screen this lives on:
- Why a compact box layout here (space saved vs a radio list / picklist)?
- Option count (if 10+, reconsider vs a picklist):

## 2. Single vs multiple  ← decide before wiring downstream logic

| Question | Answer |
|---|---|
| Can a user legitimately pick more than one? | one / many |
| *Let Users Select Multiple Options* | OFF (single) / ON (multi) |
| Resulting output shape | single value / **collection** |
| Stored variable/field + its type | `{! }` (single-value / collection) |
| Downstream read operator | `Equals` / `Contains` + loop iteration |

## 3. Choice source

- Source kind: static Choice resource(s) / Picklist Choice Set / Record Choice Set / Collection Choice Set
- Stored Value data type (must match the stored variable in §2):
- If dynamic: filter criteria, and the **empty-result path** (what the user sees when zero options):

Static choices (one `<choices>` element per option — the stable metadata the component references):

```xml
<choices>
    <name>Choice_OptionA</name>
    <choiceText>Option A</choiceText>
    <dataType>String</dataType>
    <value>
        <stringValue>A</stringValue>
    </value>
</choices>
```

## 4. Component wiring (what the checker validates)

- Component references every intended choice via `choiceReferences` (no dangling names):
- Required / default state matches intent; any default is one of the referenced choices:
- Label is clear and describes the choice:

## 5. Review checklist

- [ ] Flow is a Screen Flow; component references ≥ 1 choice / dynamic choice set
- [ ] Single vs multi is deliberate; stored variable type matches the output shape
- [ ] Every downstream Decision/Assignment/formula/reactive ref reads the correct shape
- [ ] Dynamic source has an empty-result path
- [ ] Debugged on **both** desktop and mobile (horizontal vs vertical stacking)
- [ ] Label, required/default, focus order, and contrast reviewed for accessibility
- [ ] Ran `python3 scripts/check_screen_flow_radio_button_group.py --manifest-dir <path>` clean

## Notes

Record any deviation from the standard pattern and why:
