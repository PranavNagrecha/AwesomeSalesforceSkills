---
name: data-classification-labels
description: "Classify Salesforce fields by data sensitivity and compliance category using the four built-in classification attributes (SecurityClassification, ComplianceGroup, BusinessOwnerId, BusinessStatus). Covers Metadata API deployment, Tooling API querying, and Einstein Data Detect recommendations. NOT for data masking, Shield Platform Encryption, or runtime access control enforcement."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do I mark fields as PII or HIPAA sensitive in Salesforce"
  - "set SecurityClassification or ComplianceGroup on custom and standard fields"
  - "audit which Salesforce fields are classified as Confidential or Restricted"
  - "use Einstein Data Detect to automatically classify fields with sensitive data"
  - "deploy data sensitivity labels across objects using Metadata API"
  - "query field classification metadata with Tooling API FieldDefinition"
tags:
  - data-classification
  - security-classification
  - compliance
  - pii
  - shield
  - field-metadata
inputs:
  - "List of objects and fields requiring classification review or labeling"
  - "Applicable compliance frameworks (HIPAA, PCI, PII, GDPR, CCPA, COPPA)"
  - "Desired SecurityClassification levels per field or object category"
  - "Shield license status (required for Einstein Data Detect auto-classification)"
outputs:
  - "CustomField metadata XML snippets with classification attributes populated"
  - "Tooling API SOQL queries for auditing field classification across the org"
  - "Classification inventory table mapping objects and fields to sensitivity labels"
  - "Einstein Data Detect guidance for auto-populating ComplianceGroup recommendations"
  - "Deployment checklist for promoting classification metadata via Metadata API"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Data Classification Labels

This skill activates when a practitioner needs to classify Salesforce fields by data sensitivity or compliance category — setting `SecurityClassification`, `ComplianceGroup`, `BusinessOwnerId`, or `BusinessStatus` on custom or standard fields. It also covers querying field classification via the Tooling API, using Einstein Data Detect to generate recommendations, and deploying classification metadata via the Metadata API. This skill does NOT cover data masking (a Shield Platform Encryption concern) or runtime enforcement — classification is metadata-only and does not restrict access or encrypt field values.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Classification is metadata-only:** Setting `SecurityClassification = Restricted` on a field does not restrict who can read or write that field. It does not trigger encryption, masking, or any platform enforcement. Field-Level Security (FLS) and sharing rules govern actual access. Classification is an informational label for governance, audit, and discoverability purposes only.
- **Einstein Data Detect requires Shield:** The auto-classification feature that scans field names and sample data to recommend `ComplianceGroup` values requires a Salesforce Shield license. Without Shield, classification must be set manually through Setup or Metadata API.
- **ComplianceGroup cannot be updated via Tooling API:** This is a known platform gap. While `SecurityClassification`, `BusinessOwnerId`, and `BusinessStatus` are all updatable through the Tooling API, `ComplianceGroup` must be set through the Metadata API or the Setup UI.
- **API version requirement:** Classification attributes on `CustomField` metadata are available from API v46.0 (Summer '19) onwards. Deployments using an older API version will silently ignore these attributes.

---

## Core Concepts

### The Four Classification Attributes

Every Salesforce field — custom or standard — carries four classification attributes as part of its metadata. These are informational labels; they carry no platform enforcement.

| Attribute | Valid Values | Purpose |
|---|---|---|
| `SecurityClassification` | `Public`, `Internal`, `Confidential`, `Restricted`, `MissionCritical` | Sensitivity tier of the data the field holds |
| `ComplianceGroup` | `HIPAA`, `PCI`, `PII`, `GDPR`, `CCPA`, `COPPA` (multi-value) | Compliance frameworks the field falls under |
| `BusinessOwnerId` | User Id (lookup) | Person accountable for this field's data |
| `BusinessStatus` | `Active`, `Deprecated`, `Inactive` | Lifecycle state of the field |

All four attributes are optional. Fields with no classification set are simply unclassified — the platform does not default or infer them.

`ComplianceGroup` is multi-value in the UI but is represented as a semicolon-delimited string in metadata XML. When deploying via Metadata API, list each applicable framework as a separate `<complianceGroup>` element.

### Metadata API Deployment

Classification attributes are properties of the `CustomField` metadata type. They are included in `.field-meta.xml` files in SFDX format or within `CustomObject` XML in the Metadata API format. Deployment is supported from API v46.0.

Example SFDX field metadata for a custom field with classification:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>SSN__c</fullName>
    <label>Social Security Number</label>
    <type>EncryptedText</type>
    <length>20</length>
    <securityClassification>Restricted</securityClassification>
    <complianceGroup>PII</complianceGroup>
    <complianceGroup>HIPAA</complianceGroup>
    <businessStatus>Active</businessStatus>
</CustomField>
```

Standard fields (e.g., `Contact.Email`) can also be classified. To classify a standard field, create a `.field-meta.xml` file for it in your SFDX project — the platform merges the classification attributes into the existing standard field definition on deploy.

### Tooling API Querying

The `FieldDefinition` object in the Tooling API exposes classification attributes for all fields on an object, including standard fields. This is the primary mechanism for auditing current classification state across an org.

```soql
SELECT QualifiedApiName, SecurityClassification, ComplianceGroup,
       BusinessOwnerId, BusinessStatus
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName = 'Contact'
ORDER BY QualifiedApiName
```

To audit unclassified fields across multiple objects:

```soql
SELECT QualifiedApiName, EntityDefinition.QualifiedApiName
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName IN ('Contact', 'Account', 'Lead')
  AND SecurityClassification = null
ORDER BY EntityDefinition.QualifiedApiName, QualifiedApiName
```

**Known platform gap:** `ComplianceGroup` values are not reliably updatable via the Tooling API `FieldDefinition` object. Read queries work; write operations targeting `ComplianceGroup` may silently fail. Use Metadata API or Setup UI to set `ComplianceGroup`.

### Einstein Data Detect

Einstein Data Detect (requires Salesforce Shield) scans field names and, with appropriate permission, sample data to generate `ComplianceGroup` recommendations. It populates a recommendation interface in Setup > Data Classification where admins can accept, reject, or modify suggestions.

Data Detect does not auto-apply classifications — a human must review and accept each recommendation. It surfaces fields that likely contain PII, HIPAA-regulated data, or payment card information based on naming patterns (e.g., fields containing "SSN", "CreditCard", "DateOfBirth" in their names).

Data Detect does not classify `SecurityClassification` — that value must always be set manually.

---

## Common Patterns

### Pattern: Bulk-Classify Fields via Metadata API Deployment

**When to use:** An org has a large number of custom fields requiring consistent classification labels as part of a compliance initiative. Manual UI classification of hundreds of fields is error-prone and not repeatable.

**How it works:**

1. Run a Tooling API query to export current classification state for all target fields (use `FieldDefinition` as shown above). Export to CSV for a baseline.
2. Identify fields requiring classification change based on your compliance framework.
3. For each target SFDX field file, add `<securityClassification>`, `<complianceGroup>`, and `<businessStatus>` elements.
4. For standard fields, create stub `.field-meta.xml` files containing only the classification attributes (the platform merges these on deploy — do not copy the full field definition).
5. Deploy via `sf project deploy start` or Metadata API `deploy` call at API v46.0+.
6. Validate post-deploy using the Tooling API query above. Compare against the pre-deploy baseline.

**Why not use the UI:** The Setup > Data Classification UI is suitable for small-scale reviews but does not support bulk updates, version control, or automated deployment as part of a DevOps pipeline. Metadata API deployment enables classification to be treated as code.

### Pattern: Compliance Audit Report via Tooling API

**When to use:** A compliance team or security reviewer needs a full inventory of classified and unclassified fields across the org to assess coverage and identify gaps.

**How it works:**

Query `FieldDefinition` across all high-priority objects and export results. For each object, produce a table showing field name, classification, compliance groups, business owner, and status. Flag fields where `SecurityClassification` is null or `ComplianceGroup` does not include a required framework (e.g., all PII fields must include `PII`).

```soql
SELECT QualifiedApiName,
       EntityDefinition.QualifiedApiName,
       SecurityClassification,
       ComplianceGroup,
       BusinessOwnerId,
       BusinessStatus
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName IN (
    'Contact', 'Lead', 'Account', 'Opportunity', 'Case', 'User'
)
ORDER BY EntityDefinition.QualifiedApiName, QualifiedApiName
```

Run this query via Workbench, Salesforce CLI (`sf data query --use-tooling-api`), or an external audit tool. Export to CSV for review.

**Why not use Setup reports:** Setup > Data Classification provides a field-by-field UI but does not export to a structured format suitable for compliance documentation.

### Pattern: Einstein Data Detect for Initial Classification Discovery

**When to use:** Onboarding an existing org with hundreds of custom fields into a compliance classification program. The starting state is that most fields are unclassified and the team needs to identify candidates for PII, HIPAA, or PCI labeling quickly.

**How it works:**

1. Confirm Shield license is active.
2. Navigate to Setup > Data Classification and enable Einstein Data Detect.
3. Run a scan — Data Detect will analyze field names across the org and surface recommendations organized by object.
4. Review each recommendation: accept (apply the ComplianceGroup label), modify, or reject.
5. After bulk review, export the final classification state via Tooling API to confirm all intended labels were persisted.
6. Pull the accepted classifications into source control via `sf project retrieve start` targeting the classified fields.

**Why not skip this step:** Starting classification from scratch on a large org without Data Detect typically results in missed fields. Data Detect's pattern matching catches fields with non-obvious names (e.g., a field called `Member_ID__c` that a manual reviewer might not flag as PII).

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Setting classification on new custom fields | Add classification XML to `.field-meta.xml` in SFDX and deploy | Keeps classification in source control alongside field definition |
| Classifying standard fields (e.g., Contact.Email) | Create stub `.field-meta.xml` with only classification attributes; deploy | Platform merges classification into standard field metadata on deploy |
| Bulk-classifying an existing org | Tooling API audit + Metadata API bulk deploy | UI is not scalable for more than ~20 fields |
| Setting ComplianceGroup on any field | Metadata API or Setup UI — NOT Tooling API | Tooling API write for ComplianceGroup is a known platform gap |
| Discovering which fields contain PII without reviewing all fields manually | Einstein Data Detect (requires Shield) | Pattern-matches field names and sample data to surface candidates |
| Need runtime enforcement — block access to Restricted fields | Use FLS, Permission Sets, and Sharing Rules | Classification labels have no enforcement semantics; FLS is the control |
| Confirming classification state post-deployment | Tooling API FieldDefinition query | Provides a queryable snapshot of current classification metadata |
| Proving compliance classification in an audit | Export Tooling API FieldDefinition results for target objects | Auditors need structured, exportable evidence — not Setup UI screenshots |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on field classification:

1. **Audit current state** — Run a Tooling API `FieldDefinition` query against all target objects to baseline which fields are classified, what values are set, and which are unclassified.
2. **Map fields to compliance frameworks** — Cross-reference the field inventory against applicable regulations (HIPAA, PCI, GDPR, CCPA, PII) to determine required `ComplianceGroup` values and appropriate `SecurityClassification` tiers.
3. **Update metadata files** — Add `<securityClassification>`, `<complianceGroup>`, and `<businessStatus>` elements to each target `.field-meta.xml` file. For standard fields, create stub metadata files containing only classification attributes.
4. **Deploy via Metadata API** — Run `sf project deploy start` (or equivalent) targeting the modified field metadata files. Confirm the API version is 46.0 or later.
5. **Validate post-deployment** — Re-run the Tooling API audit query and compare results against the expected classification plan. Confirm no fields were missed and no unexpected values were applied.
6. **Retrieve into source control** — If any classifications were applied through Setup or Einstein Data Detect, retrieve those field definitions back into the SFDX project to keep source control and org state in sync.
7. **Document business owners** — Set `BusinessOwnerId` on fields with `Restricted` or `MissionCritical` classification to establish accountability for sensitive data governance.

---

## Review Checklist

Run through these before marking classification work complete:

- [ ] Tooling API baseline query run before making changes; exported for audit trail
- [ ] All fields with PII, HIPAA, PCI, GDPR, or CCPA data have matching `ComplianceGroup` values
- [ ] `SecurityClassification` is set on all fields in scope — none left null
- [ ] `ComplianceGroup` was set via Metadata API or UI (not Tooling API write)
- [ ] `BusinessStatus` is set to `Active` for all in-use fields (not left unset)
- [ ] `BusinessOwnerId` is set for fields classified `Restricted` or `MissionCritical`
- [ ] Classification attributes verified post-deployment via Tooling API query
- [ ] Standard field stubs (if created) deployed without overwriting non-classification attributes
- [ ] Source control reflects final org state — retrieved after any UI or Data Detect changes
- [ ] Compliance team or data steward reviewed final classification inventory

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Classification has zero runtime enforcement** — Setting `SecurityClassification = Restricted` on a field does not prevent any user from reading or writing it. It does not trigger encryption, masking, row-level security, or any data access change. Practitioners who expect a "Restricted" label to restrict access will be surprised. Actual field access is governed entirely by FLS and Permission Sets.

2. **ComplianceGroup cannot be set via Tooling API writes** — The `FieldDefinition` object in the Tooling API supports read queries for `ComplianceGroup` but attempting to update it via a Tooling API `PATCH` or `update()` call does not persist the change. This is a documented platform limitation. The only supported write paths for `ComplianceGroup` are the Metadata API `CustomField` type or the Setup > Data Classification UI.

3. **Standard field classification requires stub metadata files** — To classify `Contact.Email` or `Account.Phone`, you cannot simply modify the standard object definition. You must create a `.field-meta.xml` stub in your SFDX project (e.g., `objects/Contact/fields/Email.field-meta.xml`) containing only the classification elements. The platform merges these on deploy. Deploying a full standard field definition with all standard attributes will cause a deploy error.

4. **Einstein Data Detect does not populate SecurityClassification** — Data Detect only generates `ComplianceGroup` recommendations. `SecurityClassification` is never auto-populated by any platform feature and must always be set manually by a human decision-maker. Teams that run Data Detect and assume all fields are "fully classified" will have incomplete classification records.

5. **Deploys at API v45.0 or lower silently drop classification attributes** — If a deployment uses an API version older than 46.0, the `securityClassification`, `complianceGroup`, `businessOwnerId`, and `businessStatus` elements in field metadata are ignored without error. The deploy succeeds but the classification attributes are not applied. Always verify `apiVersion` in `sfdx-project.json` and the deploy command.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field classification inventory | Tabular export from Tooling API FieldDefinition showing all fields with current and target classification values |
| Classified `.field-meta.xml` files | Updated SFDX field metadata files containing securityClassification, complianceGroup, businessStatus elements |
| Tooling API audit queries | Parameterized SOQL queries for auditing unclassified fields or fields missing a required ComplianceGroup value |
| Classification deployment checklist | Step-by-step record of which fields were classified, when, by whom, and against which compliance framework |

---

## Related Skills

- `security/field-audit-trail` — Shield Field Audit Trail for long-term retention of field change history. Complement to classification: classify sensitive fields AND audit changes to them.
- `security/guest-user-security` — Covers FLS and access controls for guest users. Classification labels are informational; actual access enforcement uses FLS (covered here).
- `data/data-quality-and-governance` — Broader data governance: validation rules, duplicate management, GDPR erasure. Classification is one layer of a governance program.
- `security/gdpr-data-privacy` — GDPR-specific guidance including data subject rights and erasure. Fields classified with ComplianceGroup=GDPR feed into the erasure and portability processes covered there.
