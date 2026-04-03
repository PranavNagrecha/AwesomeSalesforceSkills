# Custom Field Creation — Output Template

Use this template to document a custom field being created. Fill in each section before submitting the field for admin review or including it in a deployment.

---

## Field Summary

| Property | Value |
|----------|-------|
| **Object** | (e.g., Account, Opportunity, Case, My_Custom_Object__c) |
| **Field Label** | (user-facing name shown in the UI) |
| **Field API Name** | (e.g., Sales_Region__c — includes __c suffix) |
| **Field Type** | (Text / Picklist / Number / Date / Lookup / Master-Detail / etc.) |
| **Required** | Yes / No |
| **Unique** | Yes / No |
| **External ID** | Yes / No |

---

## Business Requirement

**What data does this field store?**
(One sentence describing what the field captures and why it exists.)

**Who enters or uses this data?**
(Which user roles, integrations, or automated processes write to this field.)

**How is this data used downstream?**
(Reports, flows, validation rules, Apex, integrations that read this field.)

---

## Field Type Rationale

**Why this field type was chosen:**
(Reference the decision guide in SKILL.md. E.g., "Picklist chosen because values are a fixed set of regions; enforces data consistency without validation rules.")

**Alternatives considered:**
(E.g., "Text was rejected because inconsistent user input would break report filters.")

---

## Field-Level Security (FLS)

| Profile / Permission Set | Read | Edit |
|--------------------------|------|------|
| (Profile or Perm Set name) | Yes / No | Yes / No |
| (Profile or Perm Set name) | Yes / No | Yes / No |
| (Profile or Perm Set name) | Yes / No | Yes / No |

---

## Page Layout Placement

| Page Layout | Section | Position |
|-------------|---------|----------|
| (Layout name) | (Section name, e.g., "Field Details") | (e.g., Left column, Row 3) |
| (Layout name) | (Section name) | |

**Dynamic Forms pages affected:**
(List any Lightning record pages using Dynamic Forms where the field must also be added to the Dynamic Form component.)

---

## Picklist Values (if applicable)

| API Value | Label | Default? |
|-----------|-------|----------|
| | | |
| | | |

**Global Value Set used?** Yes / No — (If yes, name of the Global Value Set)

---

## Deployment Checklist

- [ ] Field definition (`CustomField` metadata) included in change set or SFDX manifest.
- [ ] Page layout(s) (`Layout` metadata) included in the same deployment.
- [ ] Permission set FLS settings included if FLS is managed via Permission Sets.
- [ ] Deployment tested in a lower sandbox first (verify field visible to test user).
- [ ] Production deployment validated: field visible and editable for target users.

---

## Notes

(Any deviations from the standard creation process, known limitations, or follow-up actions.)
