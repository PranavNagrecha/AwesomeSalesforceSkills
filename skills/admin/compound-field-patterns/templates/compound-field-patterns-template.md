# Compound Field Patterns — Work Template

Fill this in before writing any query, Apex, load file, or field metadata. Workflow step 1 in
`SKILL.md`. Every row here changes which column name your code must use.

## Scope

**Skill:** `compound-field-patterns`

**Request summary:** (what was asked, in one line)

**Object(s) and compound field(s) in scope:**

| Object | Compound field | Kind (Name / Address / Geolocation) | Standard or custom |
|---|---|---|---|
| | | | |

## Org flags — check all three before anything else

| Flag | On? | How you checked | What it changes |
|---|---|---|---|
| State and Country/Territory Picklists | | `sf sobject describe --sobject Account` — is `BillingStateCode` present? | Writes target `StateCode` / `CountryCode`, not the text fields |
| Custom Address Fields (`enableCustomAddressField`) | | `sf project retrieve start --metadata "Settings:CustomAddressField"` | `Address` becomes a valid custom field type — and cannot be turned off again |
| Person Accounts | | Is `Account.IsPersonAccount` queryable? | `Account.Name` becomes a read-only concatenation on person records |

## Surfaces that touch this field

Tick every one that applies; anything outside SOAP API, REST API, and Apex resolves to components.

- [ ] SOQL `SELECT`
- [ ] SOQL `WHERE` / `ORDER BY` (filter value, or `DISTANCE` location operand?)
- [ ] Apex read
- [ ] Apex DML
- [ ] LWC / UI API
- [ ] Report column or filter
- [ ] Formula field
- [ ] Validation rule
- [ ] Flow
- [ ] Data Loader / Bulk API
- [ ] Outbound integration payload
- [ ] Lookup filter

**Resulting field list** (the exact API names every surface above must use):

## Answers to the Questions table in SKILL.md

| Question | Answer | Consequence for this build |
|---|---|---|
| Picklists enabled, everywhere on the deploy path? | | |
| Which surfaces read or write it? | | |
| Is proximity needed now or plausibly later? | | |
| Person Accounts, and can one transaction see both types? | | |
| Address needed on an object with no standard one? | | |
| Custom-field budget left on the object? | | |
| Any "address is filled in" rule or formula? | | |

## Approach

**Which pattern from `SKILL.md` → Common Patterns applies, and why:**

**Which `references/metadata-examples.md` section the metadata comes from:**

**Deviations from the standard pattern, and the reason:**

## Checklist

Copy the Review Checklist from `SKILL.md` and tick as you go.

- [ ] No WHERE-clause filters on compound fields (`DISTANCE` operand use is fine)
- [ ] DML uses component fields only
- [ ] LWC rendering via UI API `displayValue` or explicit components
- [ ] Report columns and filters use components
- [ ] State and Country/Territory Picklists accounted for (`-Code` components)
- [ ] Person Account name semantics documented if Person Accounts enabled
- [ ] Proximity uses SOQL `DISTANCE`, or `System.Location.getDistance` for in-memory points
- [ ] `DISTANCE` uses `>` / `<` only, a literal `'mi'` / `'km'`, location field first
- [ ] Validation rules and formulas reference components
- [ ] Data Loader mappings list components; no compound selected
- [ ] `Location` field XML carries `scale` and `displayLocationInDecimal`; field budget accounts for three
- [ ] Apex declares `System.Address` / `System.Location`, never bare `Address` / `Location`
- [ ] `python3 scripts/check_compound_field_patterns.py --manifest-dir <dir>` run; zero ERRORs, every WARN/INFO explained

## Checker findings and dispositions

| Finding | Severity | Disposition |
|---|---|---|
| | | |

## Notes
