---
name: custom-field-creation
description: "Use when creating a new custom field on any Salesforce object: choosing field type, setting API name, configuring Field-Level Security, adding to page layouts, and deploying. Triggers: 'add a field', 'new custom field', 'what field type should I use', 'FLS not working', 'field not showing on page layout'. NOT for formula field logic (use formula-fields skill), picklist value set management (use picklist-and-value-sets skill), or object creation decisions (use object-creation-and-design skill)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---

# Custom Field Creation

Use this skill when a practitioner needs to add a new custom field to any Salesforce object — from choosing the right field type through FLS configuration, page layout placement, and deployment to production. The skill covers all field types on both standard and custom objects.

---

## Before Starting

Gather this context before working on field creation:

- **Target object**: Standard object (Account, Contact, Opportunity, Case, Lead) or custom object?
- **Data type**: What kind of data is being stored? Text, number, date, a relationship to another object, a yes/no flag?
- **Cardinality**: Is there a fixed set of valid values (use Picklist) or free-form text?
- **Who needs access**: Which profiles or permission sets need read vs. edit access?
- **Required?**: Does every record need this field? If yes, existing records and integrations must be able to provide the value.
- **Deployment target**: Is this going to production? Change set or SFDX/sf CLI?

The most common wrong assumption: creating a field is enough to make it visible to users. It is not. FLS and page layout must also be configured.

---

## Core Concepts

### 1. Field Type Is Permanent (Mostly)

Once you save a custom field, the field type cannot be changed for most types. Text cannot become a Picklist. Number cannot become Currency. The exceptions Salesforce permits are: Text ↔ Text Area, Auto Number ↔ Text, and certain picklist conversions. Plan the field type before clicking Save — changing it later requires creating a new field, migrating data, and retiring the old field.

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

Key type-level limits:
- **Text**: max 255 characters
- **Text Area**: max 255 characters (multi-line display)
- **Long Text Area**: 256 to 131,072 characters (configurable)
- **Rich Text Area**: up to 131,072 characters
- **Number**: max 18 digits, max 17 decimal places
- **Classic Encrypted Text**: max 175 characters; cannot be used in formulas, reports, or workflow criteria

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Before marking field creation complete:

- [ ] Field type chosen intentionally — type cannot be changed for most types after save.
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

## Related Skills

- `formula-fields` — use when the field value should be computed from other fields (read-only, not stored)
- `picklist-and-value-sets` — use when managing picklist values, global value sets, or controlling/dependent picklists after field creation
- `object-creation-and-design` — use when deciding whether to create a new custom object vs. adding fields to an existing one
- `permission-set-architecture` — use when designing the FLS and access model across many users, profiles, and permission sets
