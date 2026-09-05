---
name: compound-field-patterns
description: "Compound fields (Name, Address, Geolocation): SOQL access rules, DML semantics, component access in Apex/LWC, reporting column behavior, formula field restrictions. NOT for creating a new custom field — use admin/custom-field-creation. NOT for formula syntax and functions — use admin/formula-fields. Trigger keywords: BillingAddress, MailingAddress, ShippingAddress, StateCode, CountryCode, GeocodeAccuracy, Location field type, displayLocationInDecimal, __Latitude__s, __Longitude__s, DISTANCE, GEOLOCATION, Custom Address Fields, AddressSettings, System.Address, System.Location, Person Account name."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
tags:
  - compound-fields
  - address
  - geolocation
  - name
  - soql
triggers:
  - "soql compound address field returns null in apex"
  - "how to update contact name first name last name via dml"
  - "geolocation latitude longitude component access"
  - "billing address compound field report column filter"
  - "person account name compound field behavior"
  - "apex serialize compound field to json"
  - "find nearest records within a radius using soql distance"
  - "sort soql query results by distance from a geolocation"
  - "data loader export fails when i select the address field"
  - "isblank on billingaddress will not save in a validation rule"
  - "custom geolocation field counts as three fields toward the limit"
  - "enable custom address fields on a custom object"
  - "location custom field metadata scale displaylocationindecimal"
  - "address field missing from the report filter picker"
  - "apex dot notation on billingaddress city does not compile"
  - "state and country picklists broke the integration writing billingstate"
inputs:
  - Fields in scope (Name, Address, Geolocation on standard or custom object)
  - Access context (SOQL, Apex DML, LWC wire, Report)
  - Custom Address or Geolocation field use case
outputs:
  - SOQL selection pattern (components vs compound)
  - DML/update pattern with component fields
  - LWC/UI-API access pattern
  - Reporting and filtering plan
dependencies: []
version: 1.3.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Compound Field Patterns

Activate when working with Salesforce compound fields — `Name`, `Address`, and `Geolocation` — in SOQL, Apex DML, LWC, or reports. Compound fields expose a single logical field (the compound) and N component fields (the parts). SOQL rules, DML behavior, and reporting differ in ways that trip up both humans and LLMs.

## Before Starting

- **Know the three compound field types.** Name (FirstName/LastName/Salutation), Address (Street/City/State/PostalCode/Country/Latitude/Longitude), Geolocation (Latitude/Longitude).
- **Compound in SELECT works; compound in WHERE does not.** You can `SELECT MailingAddress FROM Contact` but not `WHERE MailingAddress = ...`.
- **DML uses component fields.** `update new Contact(Id=x, MailingCity='SF')` — never assign the compound.
- **The compound value exists on three surfaces only.** "Compound fields are accessible only through SOAP API, REST API, and Apex. The compound versions of fields aren't accessible anywhere in the Salesforce user interface" (object_reference.txt L2913–L2914). Reports, Visualforce, formulas, Data Loader export and lookup filters all need components.
- **Confirm three org flags before writing anything**: State and Country/Territory Picklists (adds `-Code` components), Custom Address Fields (`CustomAddressFieldSettings.enableCustomAddressField`, irreversible once `true` — api_meta.txt L113903–L113909), and Person Accounts (changes what `Account.Name` accepts).

## Questions to Ask Before Configuring

Ask these before opening Object Manager or writing the first query; each answer changes the field names your code targets, and an assistant that skips them writes code that compiles and saves the wrong column.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Are State and Country/Territory Picklists enabled here — and in every sandbox on the deploy path?" | Decides whether writes target `BillingState` or `BillingStateCode`. `Address.getStateCode()` "returns the state code of this address if state and country/territory picklists are enabled in your organization. Otherwise, returns null" (apexrefguide.txt L199256–L199258) | The exact field list every integration, Flow, and load file must target (gotcha 1) |
| "Which surfaces read this field — Apex, a report filter, a formula, a Flow, Data Loader export?" | Only SOAP API, REST API, and Apex can see the compound value at all; every other surface needs components | The compound-vs-component decision per surface, from the matrix in `references/well-architected.md` (gotcha 7) |
| "Does the requirement need proximity — now, or plausibly next year?" | `DISTANCE`/`GEOLOCATION` work only against a `Location`-type compound. Two independent decimal fields never qualify, and converting later is a data migration plus a field-name breaking change | A `Location` field type chosen at creation, before any data lands |
| "Is Person Accounts enabled, and can one transaction touch both record types?" | `Account.Name` accepts a direct write on a business Account; on a Person Account it is "the concatenation of the FirstName, MiddleName, LastName, and Suffix of the associated person contact. You can't modify this value" (object_reference.txt L13262–L13266) | An `IsPersonAccount` partition in the bulk code instead of a mixed-batch failure (gotcha 3) |
| "Do we need an address on an object that has no standard one?" | Custom Address Fields is an org-wide enablement, and "Custom Address Fields can't be disabled. When `enableCustomAddressField` is set to `true`, you can't change the value to `false`" (api_meta.txt L113905–L113909) | A deliberate, reviewed, one-way enablement — or a decision to use five text fields instead (gotcha 8) |
| "How many custom fields are left on this object?" | "Custom geolocation fields count as three custom fields towards your organization's limits: one for latitude, one for longitude, and one for internal use" (object_reference.txt L2874–L2876) | The real field budget — see `admin/data-model-documentation` gotcha 7 for how to document it |
| "Is any validation rule or formula supposed to check 'the address is filled in'?" | "As of API version 20.0, validation rules can't have compound fields" (api_meta.txt L45369–L45370), and only `ISBLANK`, `ISCHANGED`, and `ISNULL` accept a compound at all | A component-level rule set instead of one rule that will not compile (gotcha 9) |

What a proper configuration adds over just reading and writing the field: every write lands on the column the org's flags actually make authoritative, proximity stays possible without a migration, and the rules and reports that need the address are expressed against components that exist on their surface.

## Core Concepts

### Name compound

Standard objects: `Name` is read-only compound; update `FirstName`, `LastName`, `Salutation`. Custom objects: `Name` is plain text unless defined as Person Name type.

### Address compound

On Account (`BillingAddress`, `ShippingAddress`), Contact (`MailingAddress`, `OtherAddress`), Lead, User. The `Address` type extends `Location`. Components, verbatim from the Object Reference field table (object_reference.txt L2684–L2726):

| Component | Type | Contact example |
|---|---|---|
| `Street` | textarea | `MailingStreet` |
| `City` | string | `MailingCity` |
| `State` | string | `MailingState` |
| `StateCode` | picklist | `MailingStateCode` — standard addresses only when state and country/territory picklists are enabled |
| `Country` | string | `MailingCountry` |
| `CountryCode` | picklist | `MailingCountryCode` — always available on Custom Address Fields, picklist-gated on standard ones |
| `PostalCode` | string | `MailingPostalCode` |
| `Latitude` / `Longitude` | double | `MailingLatitude` / `MailingLongitude` |
| `Accuracy` | picklist | `MailingGeocodeAccuracy` — standard address fields on standard objects only, populated only once geocoded |

Address compound fields are available in the SOAP and REST APIs in API version 30.0 and later.

### Geolocation compound

`CustomField` of `type` `Location` (not "Geolocation" — that spelling is not in the `FieldType` enum, api_meta.txt L45760). Components are addressed by appending `__Latitude__s` / `__Longitude__s` to the field name "instead of the usual '__c'" (object_reference.txt L2915–L2917). Geolocation compound fields are available in the SOAP and REST APIs in API version 26.0 and later; `Location` is not an available custom field type on external objects (api_meta.txt L43233–L43245).

### SOQL rules

```soql
-- Works: the compound in SELECT, through SOAP API, REST API, or Apex
SELECT Name, BillingAddress FROM Account

-- Fails: "Address fields can't be used in WHERE statements in SOQL"
SELECT Id FROM Account WHERE BillingAddress = :addr

-- Works: components
SELECT Id FROM Account WHERE BillingCity = 'SF' AND BillingStateCode = 'CA'

-- Works: the address compound used as a *location*, not as a filter value
SELECT Id, Name, BillingAddress FROM Account
WHERE DISTANCE(BillingAddress, GEOLOCATION(37.775,-122.418), 'mi') < 20
ORDER BY DISTANCE(BillingAddress, GEOLOCATION(37.775,-122.418), 'mi')
LIMIT 10
```

The last query is the guide's own sample (object_reference.txt L2836–L2841) and is the reason "no compound in WHERE" needs the qualifier: the compound is not *filterable*, but it is usable as a location operand inside `DISTANCE`. `DescribeFieldResult.isFilterable()` "erroneously returns true for address fields" (object_reference.txt L2950–L2951), so do not gate code on it.

### Apex DML

```apex
// Works — components
update new Contact(Id = cid, MailingCity = 'SF');

// Fails — "Compound fields are read-only. To update field values, modify the individual field components."
update new Contact(Id = cid, MailingAddress = new Address(...));

// Reading: assign the parent to a typed variable first. Dot notation
// straight through the parent field does not compile.
Address addr = acct.BillingAddress;   // System.Address
String city  = addr.city;             // == addr.getCity()
Location loc = acct.MyLocation__c;    // System.Location
Double lat   = loc.latitude;

// Writing a geolocation: the __Latitude__s / __Longitude__s components
w.Warehouse_Location__Latitude__s  = 37.775;
w.Warehouse_Location__Longitude__s = -122.418;
```

`Address` and `Location` are also standard object names. In Apex, "always use `Schema.Address` instead of `Address`" for the object and `System.Address` for the compound field type; the same disambiguation applies to `System.Location` vs `Schema.Location` (apexrefguide.txt L199187–L199190, L221921–L221924).

### LWC UI API

`@wire(getRecord)` returns compound and components; display via `{v.fields.MailingAddress.displayValue}` or each component individually.

## Common Patterns

### Pattern: Address update from form

Collect form fields, assign to component fields on a new SObject, DML. When State and Country/Territory Picklists are on, write the `-Code` component; see `references/metadata-examples.md` §5 for the load-file column list and `references/examples.md` Example 1 for the batch shape.

### Pattern: Geolocation proximity search

`DISTANCE(location1, location2, 'unit')` calculates the distance between two location values; `GEOLOCATION(latitude, longitude)` builds a location from coordinates and must be paired with `DISTANCE`. `DISTANCE()` is supported in `SELECT`, `WHERE`, and `ORDER BY` clauses; `GEOLOCATION()` is supported in `WHERE` and `ORDER BY` only. Neither is supported in `GROUP BY`. Use for store locators — see gotchas.md (Gotcha 6) for the four non-obvious query constraints and examples.md Example 2 for the working Apex pattern.

### Pattern: Compute distance in Apex when SOQL cannot

`DISTANCE`/`GEOLOCATION` need a query. When both points are already in memory — a user's browser coordinates against a record you already hold — `System.Location` exposes the same maths without a second query: `Location.newInstance(lat, lon)`, `loc1.getDistance(loc2, 'mi')`, and the static `Location.getDistance(a, b, unit)`, all documented as "an approximation of the haversine formula" (apexrefguide.txt L221955–L221962). Use these instead of hand-rolling trigonometry; use SOQL `DISTANCE` whenever the filtering or sorting can happen in the database.

### Pattern: Serialize compound to JSON

`JSON.serialize(contact.MailingAddress)` returns the compound object. Consuming code should use components, not the serialized blob as a key.

## Decision Guidance

| Task | Approach |
|---|---|
| Display full address | Select compound, render via UI API or concatenate components |
| Filter by city | Use component field (BillingCity) |
| Update name | Update FirstName/LastName, not Name |
| Proximity search | DISTANCE on Geolocation compound |
| Report with address columns | Use component columns — the compound value is not accessible in the UI at all |
| Export addresses with Data Loader | Select component fields; compound fields "cause error messages" on export |
| "Address is required" rule | Validation rule on components; compound fields are not allowed in validation rules |
| Distance rule in a workflow/approval/validation rule | `DISTANCE` formulas are supported there — the compound field on its own is not |

## Recommended Workflow

1. Fill `templates/compound-field-patterns-template.md`: the compound fields in scope, the three org flags (State and Country/Territory Picklists, Custom Address Fields, Person Accounts), and every surface that reads or writes the field. Answer the Questions table above into it.
2. Resolve compound-vs-component per surface against the matrix in `references/well-architected.md` → *Architectural Tradeoffs*. Anything outside SOAP API, REST API, and Apex resolves to components.
3. If a new field is needed, take the XML from `references/metadata-examples.md` §1 (`Location` field), §2 (`CustomAddressFieldSettings`) or §3 (`AddressSettings`) — not from `admin/custom-field-creation`, which covers the non-compound `CustomField` elements.
4. Write the SOQL, the Apex reads and writes, and the Data Loader column mapping from §4–§6 of the same file. Keep the location field first in every `DISTANCE` call and the unit a literal.
5. Run `python3 scripts/check_compound_field_patterns.py --manifest-dir force-app/main/default`. ERROR findings (compound in `WHERE`, compound DML assignment, `DISTANCE` without a unit) block the deploy; WARN and INFO findings need a written reason.
6. Deploy with `sf project deploy start --dry-run` first, then verify with the describe call and the SOQL in §8–§9 — confirm `MailingStateCode` is populated, not just `MailingState`.
7. Walk `references/gotchas.md` against the change before sign-off; each gotcha names the surface it breaks and the org flag that triggers it.

## Review Checklist

- [ ] No WHERE-clause filters on compound fields
- [ ] DML uses component fields only
- [ ] LWC rendering via UI API displayValue or explicit components
- [ ] Reports using compound columns where appropriate
- [ ] State & Country Picklists considered (adds -Code components)
- [ ] Person Account name semantics documented if Person Accounts enabled
- [ ] Proximity queries use DISTANCE in SOQL, or `System.Location.getDistance` when both points are already in memory — never hand-rolled trigonometry
- [ ] Validation rules and formulas reference components, not the compound (only `ISBLANK`, `ISCHANGED`, `ISNULL` accept a compound)
- [ ] Data Loader export mappings list components; no compound field is selected
- [ ] `Location` field XML carries `scale` and `displayLocationInDecimal`, and the object's field budget accounts for three fields per geolocation
- [ ] No `Address` / `Location` identifier ambiguity in Apex (`System.` vs `Schema.`)
- [ ] DISTANCE uses only `>` / `<` operators and a literal `'mi'`/`'km'` unit (location field before GEOLOCATION)

## Salesforce-Specific Gotchas

1. **State & Country Picklists change components.** Adds `BillingStateCode` / `BillingCountryCode` alongside text versions; DML requires the code if picklist is enabled.
2. **`Name` on standard objects cannot be DML-assigned.** Only on custom objects (where it's a plain text field anyway).
3. **Serialized compound in JSON integrations is not round-trippable.** Always map to components explicitly.
4. **`isFilterable()` lies about address fields.** The describe result reports `true`; SOQL rejects the filter. Do not build dynamic query builders on that flag.
5. **A custom geolocation field is three fields against the org limit**, one in the UI, and absent from Schema Builder and dashboards.

The full set with reproduction and avoidance steps is in `references/gotchas.md`.

## Output Artifacts

| Artifact | Description |
|---|---|
| Compound-access cheat sheet | Context × field-type matrix |
| DML update template | Component-assignment patterns |
| Geolocation query library | DISTANCE patterns |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing deployable metadata or queries: the `Location` `CustomField` XML with `scale` and `displayLocationInDecimal`, `CustomAddressFieldSettings`, `AddressSettings`, the SOQL set (compound, components, `DISTANCE`, `GEOLOCATION`), the Apex read/write patterns, the Data Loader column mapping, package.xml, retrieve/deploy, and the verification describe |
| `references/gotchas.md` | The field saved and something downstream is wrong — a null `-Code`, an empty report column, a query the parser refuses, a describe flag that lies, or a formula that will not compile. Eleven behaviours with guide line citations |
| `references/examples.md` | You want the scenarios end to end: a 30,000-record address batch under State and Country Picklists, a store-locator proximity query, and the compound-in-a-filter anti-pattern |
| `references/well-architected.md` | You are justifying the design — the pillar mapping, the surface-by-surface compound-vs-component matrix, the three field-shape tradeoffs, and the sources every claim rests on |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated compound-field code and need the six failure modes with detection hints |
| `templates/compound-field-patterns-template.md` | Workflow step 1 — the org-flag and surface inventory |
| `scripts/check_compound_field_patterns.py` | Workflow step 5, before every deploy that touches an address, name, or geolocation field |

---

## Related Skills

- `admin/custom-field-creation` — the non-compound `CustomField` elements, the `FieldType` enum, and general field design; it owns the CustomField XML this skill only extends
- `admin/data-model-documentation` — how to document a compound field that counts as three against the limit (its gotcha 7)
- `admin/validation-rules` — why `ISBLANK(BillingAddress)` will not save, and the component-level rules to write instead (its "Compound Fields Cannot Be Used in a Validation Rule at All")
- `admin/formula-fields` — formula syntax and which field types are addressable
- `data/soql-query-optimization` — selectivity and index behaviour for the component filters this skill sends you to
- `apex/soql-fundamentals` — SOQL query patterns
