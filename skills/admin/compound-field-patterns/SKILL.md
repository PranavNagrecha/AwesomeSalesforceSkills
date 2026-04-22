---
name: compound-field-patterns
description: "Compound fields (Name, Address, Geolocation): SOQL access rules, DML semantics, component access in Apex/LWC, reporting column behavior, formula field restrictions. NOT for general field design (use custom-field-creation). NOT for address validation services (use address-validation-integration)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Compound Field Patterns

Activate when working with Salesforce compound fields — `Name`, `Address`, and `Geolocation` — in SOQL, Apex DML, LWC, or reports. Compound fields expose a single logical field (the compound) and N component fields (the parts). SOQL rules, DML behavior, and reporting differ in ways that trip up both humans and LLMs.

## Before Starting

- **Know the three compound field types.** Name (FirstName/LastName/Salutation), Address (Street/City/State/PostalCode/Country/Latitude/Longitude), Geolocation (Latitude/Longitude).
- **Compound in SELECT works; compound in WHERE does not.** You can `SELECT MailingAddress FROM Contact` but not `WHERE MailingAddress = ...`.
- **DML uses component fields.** `update new Contact(Id=x, MailingCity='SF')` — never assign the compound.

## Core Concepts

### Name compound

Standard objects: `Name` is read-only compound; update `FirstName`, `LastName`, `Salutation`. Custom objects: `Name` is plain text unless defined as Person Name type.

### Address compound

On Account (`BillingAddress`, `ShippingAddress`), Contact (`MailingAddress`, `OtherAddress`), Lead, User. Components: `Street`, `City`, `State`, `PostalCode`, `Country`, `Latitude`, `Longitude`, plus StateCode/CountryCode when State & Country Picklists enabled.

### Geolocation compound

Custom field type combining `__latitude__s` and `__longitude__s`. SOQL `SELECT Location__c` returns a Location object; filter by components.

### SOQL rules

```
-- Works
SELECT BillingAddress FROM Account

-- Fails
SELECT Account WHERE BillingAddress = :addr
-- Use components:
SELECT Account WHERE BillingCity = 'SF' AND BillingState = 'CA'
```

### Apex DML

```
-- Works
update new Contact(Id = cid, MailingCity = 'SF');

-- Fails (compound is read-only for DML)
update new Contact(Id = cid, MailingAddress = new Address(...));
```

### LWC UI API

`@wire(getRecord)` returns compound and components; display via `{v.fields.MailingAddress.displayValue}` or each component individually.

## Common Patterns

### Pattern: Address update from form

Collect form fields, assign to component fields on new SObject, DML.

### Pattern: Geolocation proximity search

SOQL supports `DISTANCE(Location__c, GEOLOCATION(lat, lon), 'km')` in SELECT and ORDER BY. Use for store locators.

### Pattern: Serialize compound to JSON

`JSON.serialize(contact.MailingAddress)` returns the compound object. Consuming code should use components, not the serialized blob as a key.

## Decision Guidance

| Task | Approach |
|---|---|
| Display full address | Select compound, render via UI API or concatenate components |
| Filter by city | Use component field (BillingCity) |
| Update name | Update FirstName/LastName, not Name |
| Proximity search | DISTANCE on Geolocation compound |
| Report with address columns | Compound column works in Reports UI |

## Recommended Workflow

1. Identify whether the context is SELECT, WHERE, DML, LWC, or Report.
2. For SELECT and Reports: compound or components both work.
3. For WHERE and ORDER BY (except DISTANCE): use components.
4. For DML: always components, never the compound assignment.
5. For LWC: use UI API `displayValue` for rendering and component paths for editing.
6. For geolocation: use DISTANCE in SOQL for proximity; never compute haversine in Apex unless offline.
7. Document per-field compound behavior (Person Account names are especially quirky).

## Review Checklist

- [ ] No WHERE-clause filters on compound fields
- [ ] DML uses component fields only
- [ ] LWC rendering via UI API displayValue or explicit components
- [ ] Reports using compound columns where appropriate
- [ ] State & Country Picklists considered (adds -Code components)
- [ ] Person Account name semantics documented if Person Accounts enabled
- [ ] Proximity queries use DISTANCE, not manual math

## Salesforce-Specific Gotchas

1. **State & Country Picklists change components.** Adds `BillingStateCode` / `BillingCountryCode` alongside text versions; DML requires the code if picklist is enabled.
2. **`Name` on standard objects cannot be DML-assigned.** Only on custom objects (where it's a plain text field anyway).
3. **Serialized compound in JSON integrations is not round-trippable.** Always map to components explicitly.

## Output Artifacts

| Artifact | Description |
|---|---|
| Compound-access cheat sheet | Context × field-type matrix |
| DML update template | Component-assignment patterns |
| Geolocation query library | DISTANCE patterns |

## Related Skills

- `admin/custom-field-creation` — general field design
- `integration/address-validation-integration` — external address cleansing
- `apex/apex-soql-patterns` — SOQL query patterns
