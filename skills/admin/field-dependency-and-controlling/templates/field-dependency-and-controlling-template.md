# Field Dependency Worksheet

One worksheet per dependent picklist. Fill it in before writing XML — the matrix table below is the single
artifact that the field file, the validation rule, and the record-type entries are all derived from, and the
one thing a reviewer can check without an org.

## 1. Scope

| | |
|---|---|
| Object | `Warranty_Claim__c` |
| Controlling field (API name) | `Product_Family__c` |
| Controlling field type | Picklist / Checkbox |
| Dependent field (API name) | `Product_Line__c` |
| Does the dependent field also control another field? | Yes → name it: `Component__c` / No |
| Value source | Local `valueSetDefinition` / Global value set `<name>__gvs` |
| Record types on this object | `Hardware`, `Software`, or "none" |
| Request / ticket | |

## 2. Answers to the questions in SKILL.md

| Question | Answer | Consequence for this build |
|---|---|---|
| Which paths write both fields? | e.g. record page, nightly Data Loader, order-intake integration | Validation rule required: yes / no |
| Picklist or checkbox controller? | | Matrix keys are value `fullName`s / `checked` and `unchecked` |
| Does anything need un-mapping? | | Setup ticket needed: yes / no — a deploy cannot do it |
| Which profiles see the controlling field? | | Profiles needing an FLS fix or a fallback: |
| Which record types offer which dependent values? | | `RecordType.picklistValues` edits needed: |
| How deep is the chain? | | Deploy order and clear-on-change logic: |
| What about existing bad rows? | | Count from the verification SOQL: ____ ; plan: backfill / report / stage the rule inactive |

## 3. The matrix

Tick every enabled pair. A blank column is a controlling value that renders an empty dependent picklist —
confirm that is intentional. A blank row is a dependent value nobody can ever select.

| Dependent value \ Controlling value | Computers | Mobile | Peripherals |
|---|---|---|---|
| `Laptops` | x | | |
| `Desktops` | x | | |
| `Handsets` | | x | |
| `Tablets` | | x | |
| `Accessories` | x | x | x |

Pair count (ticks): ______  — compare this number against the Setup Field Dependencies grid after deploy, and
against the count the checker prints.

For a **checkbox** controller the table has exactly two columns, headed `checked` and `unchecked`.

## 4. Record-type availability

Only for objects with record types. A value must be ticked here *and* in §3 to be selectable.

| Value | Hardware | Software |
|---|---|---|
| `Product_Family__c` → `Computers` | x | |
| `Product_Family__c` → `Mobile` | x | |
| `Product_Family__c` → `Peripherals` | | x |
| `Product_Line__c` → `Laptops` | x | |
| `Product_Line__c` → `Accessories` | x | x |

## 5. Enforcement off the browser

| | |
|---|---|
| Validation rule name | `Product_Line_Matches_Family` |
| Or before-save automation | |
| Ships active from day one? | Yes / No — if No, the date it is switched on |
| Existing rows that would fail it | ____ (run the SOQL in `references/metadata-examples.md` §9) |

## 6. Build record

- [ ] Matrix table above signed off by the requester
- [ ] Controlling field retrieved, not hand-written
- [ ] Dependent field file authored from `references/metadata-examples.md` §2 / §3 / §4
- [ ] Checkbox controllers use `checked` / `unchecked`
- [ ] `RecordType.picklistValues` updated for every record type in §4
- [ ] Validation rule authored and referenced from §5
- [ ] `python3 skills/admin/field-dependency-and-controlling/scripts/check_field_dependency_and_controlling.py --manifest-dir force-app/main/default` exits 0
- [ ] `sf project deploy validate --manifest manifest/package.xml` clean against production
- [ ] Deployed in the order in `references/metadata-examples.md` §8
- [ ] Apex assertion of `isDependentPicklist()` / `getController()` added (`references/examples.md` Example 3)
- [ ] Invalid-combination insert rejected in a test
- [ ] Setup Field Dependencies grid pair count matches §3
- [ ] Any un-mapping done in Setup and re-retrieved into source

## 7. Deviations

Record anything that departs from the patterns in SKILL.md and why — a controlling value that deliberately
enables nothing, a chain deeper than two levels, a UI-only decision with no validation rule, a GVS-backed
field in the matrix. State who accepted the risk.

| Deviation | Reason | Accepted by |
|---|---|---|
| | | |
