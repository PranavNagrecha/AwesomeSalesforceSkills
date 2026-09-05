---
name: custom-field-creation
description: "Use when creating a new custom field on any Salesforce object: choosing field type, setting API name, configuring Field-Level Security, adding to page layouts, and deploying. Triggers: 'add a field', 'new custom field', 'what field type should I use', 'FLS not working', 'field not showing on page layout'. NOT for creating the object itself - use admin/object-creation-and-design. NOT for formula field logic - use admin/formula-fields. NOT for picklist value set management - use admin/picklist-and-value-sets. Also covers: field-meta.xml, CustomField metadata, deleteConstraint, externalId, unique, precision and scale, relationshipOrder, writeRequiresMasterRead, fieldPermissions, package.xml for fields."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do I add a new field to a Salesforce object"
  - "add new custom field to object in Salesforce Setup"
  - "create a field on a standard or custom Salesforce object"
  - "what custom field type should I use for storing this data"
  - "field I created is not showing up for users on the page"
  - "FLS field-level security not working after adding new field"
  - "how do I deploy a custom field from sandbox to production"
  - "user cannot see a field I added to the page layout"
  - "what is the difference between text and text area field type"
  - "adding a new field to Account Contact Opportunity object"
  - "creating a new custom field on a Salesforce object"
  - "deploy failed because permissions for required fields cannot be deployed"
  - "upsert returns 300 the external id exists in more than one record"
  - "parent record was deleted and the lookup field went blank"
  - "wildcard star does not retrieve custom fields in package.xml"
  - "junction object records are owned by the wrong parent"
  - "user can see the parent record but cannot create child records"
  - "field history tracking fails to deploy on this object"
  - "number field is shorter than the length I set in setup"
  - "write the field-meta.xml for a lookup with a lookup filter"
  - "which permission set exposes this new field"
tags:
  - custom-fields
  - add-field
  - new-field
  - field-level-security
  - page-layout
  - metadata
  - admin
  - object-field
  - field-creation
inputs:
  - "Object name (standard or custom) where the field will be created"
  - "Business requirement describing what data the field stores"
  - "Who needs to see or edit the field (profiles or permission sets)"
  - "Whether the field is required or optional"
outputs:
  - "Field type recommendation with rationale"
  - "Step-by-step creation and configuration checklist"
  - "FLS and page layout configuration guidance"
  - "Deployment checklist for change set or SFDX"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Custom Field Creation

Use this skill when a practitioner needs to add a new custom field to any Salesforce object — from choosing the right field type through FLS configuration, page layout placement, and deployment to production. The skill covers all field types on both standard and custom objects.

---

## Before Starting

Gather this context before working on field creation:

| Context | What to confirm |
|---|---|
| Target object | Standard object (Account, Contact, Opportunity, Case, Lead) or custom object? |
| Data type | What kind of data is being stored? Text, number, date, a relationship to another object, a yes/no flag? |
| Cardinality | Is there a fixed set of valid values (use Picklist) or free-form text? |
| Who needs access | Which profiles or permission sets need read vs. edit access? |
| Required? | Does every record need this field? If yes, existing records and integrations must be able to provide the value. |
| Deployment target | Is this going to production? Change set or SFDX/sf CLI? |

The most common wrong assumption: creating a field is enough to make it visible to users. It is not. FLS and page layout must also be configured.

---

## Questions to Ask Before Configuring

Ask these before opening the field editor or writing the `field-meta.xml`. Each one maps to a gotcha in `references/gotchas.md`; skipping them yields a field that deploys and is still wrong.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who writes this value — a person, a nightly integration, or both?" | An integration-owned field almost always needs `externalId` plus `unique`; a person-owned one needs `inlineHelpText`. Non-unique external IDs fail upserts at runtime with HTTP 300 | The `externalId` / `unique` / `caseSensitive` triple, and whether help text is needed at all |
| "If the parent record is deleted, what should happen to this one?" | `deleteConstraint` defaults to `SetNull`, which silently blanks the lookup rather than blocking the delete | An explicit `Cascade` / `Restrict` / `SetNull` written into the XML |
| "Does anything need to know what this value used to be?" | `trackHistory` is the only durable record of a change, and it will not deploy unless the object has `enableHistory` | A `trackHistory` decision plus the object change in the same deploy |
| "Is the value one of a closed set, and can the API be allowed to add to it?" | An unrestricted picklist lets data loads write values no dashboard groups | `restricted` `true`, or a documented reason to leave it open — and a pointer to `admin/picklist-and-value-sets` if the set is shared |
| "Which permission set will grant this field, and is it in the same deploy?" | The field and its FLS are separate components; a field shipped without one is invisible. A `required` field cannot carry FLS metadata at all | The `permissionsets/*.permissionset-meta.xml` entry, or the decision to leave a required field implicit |
| "Do we already have a field that holds this?" | Field count per object is capped and dead fields are expensive to remove later | Either a reuse decision or a named reason the existing field will not do |
| "If this is a relationship, which side owns the record?" | On a junction, `relationshipOrder` decides ownership, sharing, and delete behaviour, and `reparentableMasterDetail` defaults to `false` | The primary/secondary assignment and whether children can be moved |

What a proper configuration adds over just creating the field: the field arrives with the permission set that exposes it, its delete and uniqueness behaviour is a written decision rather than a platform default, and the type is one you can still live with after the data lands.

---

## Core Concepts

### 1. Field Type Changes Are Allowed — and That Is the Danger

Most conversions are permitted: Text → Picklist, Number → Currency, and Picklist → Multi-Select Picklist all go through. The risk is not that Salesforce refuses, it is that stored values disappear. Salesforce's rule is to convert only custom fields that hold no data. Conversions documented as data-losing: to or from Date or Date/Time; to Number, Percent, or Currency from any other type; from Checkbox to any other type; to or from Multi-Select Picklist; from Text to Picklist; from Auto Number to any other type except Text; to Auto Number from any type except Text; and from Long Text Area to any type except Email, Phone, Text, Text Area, or URL.

A smaller set is blocked outright: Formula fields convert neither in nor out, Classic Encrypted Text converts neither in nor out, and no custom field referenced in Apex or on a Visualforce page can change type at all. Text ↔ Auto Number is the safe round trip, with Auto Number capped at 30 characters. Plan the type before clicking Save anyway — see `references/gotchas.md` Gotcha 6 for what a lossy conversion destroys beyond the field itself.

### 2. Three Separate Access Layers

Salesforce has three independent layers that must all be configured for a user to see and use a custom field:

1. **Field definition** — the field exists on the object (created in Object Manager).
2. **Field-Level Security (FLS)** — controls which profiles or permission sets can see (Read) or edit (Edit) the field. Newly created fields default to hidden for all profiles in Enterprise and Unlimited editions.
3. **Page layout** — controls whether the field appears on the record detail/edit page in the UI. FLS and page layout are independent: a field can be on a layout but hidden by FLS (user sees nothing), or accessible via FLS but not on any layout (accessible via API and reports, but not the UI record page).

All three must be configured. Missing any one of them is why users cannot see a new field.

### 3. API Name Rules and Permanence

The API name is permanent after save. Rules:
- Maximum 40 characters
- Alphanumeric characters and underscores only
- Must start with a letter
- Cannot end with an underscore
- Cannot contain consecutive underscores
- Salesforce appends `__c` automatically

Choose a clear, unambiguous name. "Billing_Region__c" is better than "BR__c". You cannot rename an API name after creation.

### 4. Platform Limits

| Edition | Custom Fields per Object |
|---------|--------------------------|
| Contact Manager, Group | 100 |
| Essentials | 100 |
| Professional | 100 |
| Enterprise | 500 |
| Performance, Unlimited | 800 |
| Developer | 500 |

Source for both tables: Salesforce Help — *Custom Field Allocations* and *Custom Field Types* (listed in `references/well-architected.md`). UNVERIFIED (2026-09-04): these per-edition and per-type figures are not present in the Summer '26 Salesforce Developer Limits and Allocations quick reference, and `help.salesforce.com` cannot be fetched here — confirm the ceiling for your org at Setup → Company Information before planning against it.

Key type-level limits:

| Field type | Limit |
|---|---|
| Text | Max 255 characters |
| Text Area | Max 255 characters (multi-line display) |
| Long Text Area | 256 to 131,072 characters (configurable) |
| Rich Text Area | Up to 131,072 characters |
| Number | Max 18 digits, max 17 decimal places |
| Classic Encrypted Text | Max 175 characters; cannot be used in formulas, reports, or workflow criteria |

---

## Field Type Decision Guide

| Data Need | Recommended Type | Notes |
|-----------|-----------------|-------|
| Short free-form text (name, code, ID) | Text | Max 255 chars. Can be marked as External ID or Unique. |
| Multi-line notes or descriptions | Long Text Area | Min 256 chars. Use instead of Text Area for longer content. |
| Rich text with formatting | Rich Text Area | Stores HTML; max 131,072 chars. |
| Fixed list of choices | Picklist | Consider Global Value Set if values are reused across objects. |
| Multiple selections from a list | Multi-Select Picklist | Stored as semicolon-delimited string; harder to filter in reports. |
| Whole number | Number (0 decimal places) | Use Currency for monetary amounts. |
| Money amount | Currency | Respects org currency settings; supports multi-currency. |
| Ratio or percentage | Percent | Stored as decimal, displayed with % symbol. |
| Yes/No boolean flag | Checkbox | Defaults to unchecked; cannot be set as Required. |
| Calendar date only | Date | No time component. |
| Date and time | Date/Time | Stored in UTC; displayed in user's timezone. |
| Email address | Email | Validates format; renders as email client link. |
| Phone number | Phone | Stores any format; add validation rule for specific format enforcement. |
| Web address | URL | Renders as clickable link; max 255 chars. |
| Auto-incrementing record number | Auto Number | Format defined at creation; cannot be changed after. |
| Relationship to another record (optional parent) | Lookup Relationship | Parent can be blank; no cascade delete; no roll-up summary. |
| Required parent relationship with cascade delete | Master-Detail Relationship | Parent required; delete cascades; enables Roll-Up Summary. |
| Computed read-only value | Formula | Not stored in DB; computed at runtime. |
| Aggregated value from child records | Roll-Up Summary | Only on Master-Detail parent objects; supports Count, Sum, Min, Max. |
| Geographic coordinates | Geolocation | Stores latitude and longitude; enables DISTANCE() formula. |

---

## Common Patterns

### Pattern 1: Build from Scratch — New Field for a Business Requirement

**When to use**: A stakeholder requests a new data capture point on any object.

**Steps:**

1. Navigate to Setup → Object Manager → [Object] → Fields & Relationships → New.
2. Select field type using the decision guide above. Click Next.
3. Enter **Field Label** (user-facing name). Salesforce auto-populates **Field Name** (API name) — review it. Add **Description** (internal notes for admins) and **Help Text** (shown to end users).
4. Configure type-specific options: Length (Text), Decimal Places (Number/Currency), Visible Lines (Long Text Area), picklist values.
5. On "Establish Field-Level Security": set Read and/or Edit per profile. Include every profile whose users need access.
6. On "Add to Page Layouts": select every layout where the field must appear.
7. Click Save.
8. Verify: use View as a target user or log in as a test user. Confirm the field is visible and editable.

### Pattern 2: Review / Troubleshoot — Field Not Visible to Users

**When to use**: A user reports they cannot see a field that was recently created.

**Diagnosis steps:**

1. Setup → Object Manager → [Object] → Fields & Relationships → [Field] → **Set Field-Level Security**.
   Confirm the user's profile (or relevant permission set) has at least Read access checked.
2. Setup → Object Manager → [Object] → **Page Layouts** → [Applicable layout].
   Confirm the field appears on the layout canvas (not just in the palette on the left, which means it is NOT on the layout).
3. If the org uses Lightning Record Pages with **Dynamic Forms**:
   Setup → App Builder → [Record page for this object] → check the Dynamic Form component.
   In Dynamic Forms, fields must be added to the form component individually — the page layout is not used for those fields.
4. Check the user's active record type and which layout is assigned to that record type for that profile.

### Pattern 3: Lookup vs. Master-Detail — Choosing the Right Relationship Type

**Lookup Relationship** — use when:
- The parent record is optional (child can exist without a parent)
- Deleting the parent should NOT delete child records
- Child records have their own ownership and sharing rules
- Roll-up summaries are not needed

**Master-Detail Relationship** — use when:
- Every child record must have a parent (field is always required)
- Deleting the parent should cascade-delete all children
- Roll-Up Summary fields are needed on the parent
- Child records should inherit the parent's sharing model

A Lookup can be converted to Master-Detail later only if no child records have a blank parent. Master-Detail cannot be converted to Lookup if the object has Roll-Up Summary fields using that relationship.

---


## Recommended Workflow

1. **Answer the seven questions above** and fill in `templates/custom-field-creation-template.md`. The answers decide `type`, `required`, `unique`, `deleteConstraint`, `restricted`, and which permission set ships with the field. Stop here if the answer to "do we already have a field that holds this?" is yes.
2. **Pick the `type` from the enum, not from the UI label.** `references/metadata-examples.md` lists every valid `FieldType` value and the four spellings LLMs get wrong (`MasterDetail`, `Url`, `Location`, `Summary`).
3. **Write the `.field-meta.xml`** at `objects/<Object>/fields/<Name>__c.field-meta.xml`, copying the closest of the eight worked examples in `references/metadata-examples.md` (§1 required text, §2 external ID, §3 number, §4 checkbox and date, §5 lookup with filter, §6 junction master-detail, §7 restricted picklist, §8 data classification).
4. **Write the `fieldPermissions` entry in the same change** — `references/metadata-examples.md` §9. Omit it only for `required` fields, which cannot carry FLS metadata. Add the `Layout` (or Dynamic Form) change to the same manifest.
5. **Build the `package.xml` by enumerating each `Object.Field__c`** (§10). `CustomField` accepts no wildcard; a `*` manifest ships nothing and does not error.
6. **Run the checker** over the source tree before deploying: `python3 scripts/check_custom_field_creation.py --manifest-dir force-app/main/default`. Resolve every WARN or justify it in the template's Notes section.
7. **Validate, deploy, verify** — `sf project deploy start --dry-run` first, then deploy, then confirm the shape the org actually has with the `sf sobject describe`, `FieldPermissions` SOQL, and `Schema.DescribeFieldResult` checks in `references/metadata-examples.md` §11–§12. Log in as a target user; a clean deploy is not evidence anyone can see the field.

---

## Review Checklist

Before marking field creation complete:

- [ ] Field type chosen intentionally — most conversions are allowed later, but the data-losing ones destroy stored values, and where data is lost every list view built on the field is deleted.
- [ ] API name reviewed: clear, unique, under 40 characters, no trailing underscores.
- [ ] Description and Help Text filled in — helps future admins and end users.
- [ ] FLS configured for all profiles or permission sets that need Read and/or Edit access.
- [ ] Field added to all relevant page layouts for the target user group.
- [ ] If Dynamic Forms are in use on any Lightning record page, field added to the Dynamic Form component.
- [ ] Required setting validated: if required, existing records and integrations can provide the value.
- [ ] Tested as a target user (View as user or dedicated test user in sandbox).
- [ ] Deployment artifact prepared: field + page layout(s) included in change set or SFDX retrieve manifest.
- [ ] Production deployment validated: field visible and editable for users in production.

---

## Salesforce-Specific Gotchas

1. **New fields are hidden for all profiles in Enterprise/Unlimited editions** — When you create a field in Enterprise or Unlimited, the default FLS is hidden (no access) for all profiles. If you click through the FLS screen without setting visibility, no user (other than System Administrators in some editions) can see the field. The field exists and stores data written via API, but the UI and reports show it as blank or invisible.

2. **Required fields break existing records and integrations** — Marking a field Required at the field definition level causes the Salesforce API to reject any DML (from UI, triggers, or integrations) that does not supply the field. If you convert an optional field to required after records already exist without values, bulk operations and integrations that do not explicitly set the field will start producing errors. Provide a default value or run a data update before making an existing field required.

3. **Dynamic Forms bypass classic page layouts for field display** — If a Lightning record page uses the Dynamic Forms feature in Lightning App Builder, fields on the classic page layout are NOT automatically shown. Dynamic Forms replaces the classic layout's field section with a custom field component. Adding a field to the classic page layout has no effect for users seeing the Dynamic Forms version of the page. The field must be added directly to the Dynamic Form component in App Builder.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field type recommendation | Which type to use and why, based on business requirement |
| Creation and configuration checklist | Step-by-step including FLS, layout, and Dynamic Forms |
| Deployment manifest note | Which metadata types to include: CustomField, Layout, PermissionSet (if FLS via perm sets) |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the `.field-meta.xml` for any field type, the `fieldPermissions` entry, the `package.xml`, the retrieve/deploy commands, or the post-deploy describe and FLS verification |
| `references/gotchas.md` | Fourteen platform behaviours that make a field wrong after it deploys — FLS retrieve rewrites, `deleteConstraint` defaults, non-unique external IDs, junction ownership, wildcard-free manifests, precision arithmetic |
| `references/examples.md` | Looking for a worked scenario end to end: picklist over text, date over text, master-detail over lookup, and the text-instead-of-picklist anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing a field an assistant generated, before it reaches a deploy |
| `references/well-architected.md` | Framing the design against Security, Operational Excellence, and Scalability, and for the full source list |
| `templates/custom-field-creation-template.md` | Documenting any field worth reviewing — field summary, type rationale, FLS matrix, layout placement, deployment checklist |

---

## Related Skills

- **admin/formula-fields**: Use when the value should be computed from other fields at read time rather than stored. Also owns the `formula` / `formulaTreatBlanksAs` XML.
- **admin/picklist-and-value-sets**: Use when managing picklist values, global value sets, restriction, or value deactivation. NOT for the picklist field's own definition, which is here.
- **admin/field-dependency-and-controlling**: Use when one picklist filters another; `controllingField` and `valueSettings` are designed there.
- **admin/lookup-and-relationship-design**: Use to choose between Lookup, Master-Detail, and a junction object before writing either relationship field.
- **admin/lookup-filter-cross-object-patterns**: Use when the requirement is to constrain which parent records a lookup offers, beyond the single filter shown here.
- **admin/compound-field-patterns**: Use for Address, Geolocation, and Name compound fields, whose component fields behave differently from ordinary custom fields.
- **admin/system-field-behavior-and-audit**: Use for field history retention, `trackHistory` querying, and system audit fields.
- **admin/permission-set-architecture**: Use when designing which permission sets exist and how FLS is grouped across users; this skill only ships the one `fieldPermissions` entry.
- **admin/object-creation-and-design**: Use when deciding whether a new custom object beats adding fields to an existing one.
