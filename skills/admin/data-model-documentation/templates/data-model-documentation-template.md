# Data Model Documentation — Work Template

Use this template to produce a complete data model documentation package for a Salesforce org or a scoped set of objects.

---

## Scope

**Objects in scope:** (list each object API name)

**Requested format:** Field inventory / ER diagram / relationship map / data dictionary / all of the above

**Audience:** Developer / Business stakeholder / Integration partner / Audit/compliance

**Source:** Live org Setup access / Metadata API retrieve / Both

---

## Object Inventory

For each object in scope:

| Object Label | Object API Name | Type (Standard/Custom) | Description / Business Purpose |
|---|---|---|---|
| | | | |

---

## Field Inventory

Repeat this table per object, or use a combined table with an Object column.

**Object: `<ObjectName>`**

| Field Label | API Name | Type | Required | External ID | Description | Owner/Team | Notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Columns explained:
- **Type**: Text, Number, Date, Lookup(Object), Master-Detail(Object), Picklist, Formula, etc.
- **Required**: Yes / No
- **External ID**: Yes / No — marks fields used as integration keys
- **Description**: The field's documented purpose (from metadata Description property)
- **Owner/Team**: Which team or system uses this field
- **Notes**: Deprecated, in-use, being migrated, etc.

---

## Object Relationship Map

| Parent Object | Relationship Type | Child Object | Relationship Field API Name | Cascade Delete? |
|---|---|---|---|---|
| | Lookup | | | No |
| | Master-Detail | | | Yes |
| | Junction (via) | | | — |

**Polymorphic lookups (document separately):**

| Field | Parent Object | Valid Target Objects |
|---|---|---|
| Task.WhoId | Task | Contact, Lead |
| Task.WhatId | Task | Account, Opportunity, Case, Contract, ... |

---

## ER Diagram

*(Attach Schema Builder screenshot or draw.io export here)*

Annotations:
- Bold/thick lines = Master-Detail (cascade delete)
- Thin lines = Lookup (no cascade)
- Dashed lines = Polymorphic lookup (multiple valid targets)

---

## Documentation Debt — Fields With No Description

The following custom fields have empty Description values and require documentation:

| Object | Field API Name | Type | Assigned To |
|---|---|---|---|
| | | | |

---

## FLS Summary (if in scope)

For sensitive fields, document which permission sets grant access:

| Object | Field API Name | Read Access (Permission Sets) | Edit Access (Permission Sets) |
|---|---|---|---|
| | | | |

---

## Delivery Checklist

- [ ] All in-scope objects and their custom fields are in the field inventory
- [ ] Standard fields on standard objects noted from Object Reference (not from metadata retrieve)
- [ ] All relationship fields show parent object, relationship type, and cascade behavior
- [ ] Polymorphic lookups documented separately
- [ ] ER diagram attached and reviewed against the field inventory
- [ ] Documentation debt list produced and assigned
- [ ] FLS summary completed for any sensitive fields (if required by scope)
