# Examples — Data Classification Labels

## Example 1: Classifying PII Fields on Contact via Metadata API

**Context:** A healthcare technology company is implementing a HIPAA compliance program. Their Salesforce org has a custom `Patient__c` object and uses standard `Contact` fields to store patient data. A compliance audit identified that no fields have `SecurityClassification` or `ComplianceGroup` set. The team needs to classify all PII and HIPAA-regulated fields and deploy the labels as part of their CI/CD pipeline.

**Problem:** The compliance team manually reviewing Setup > Data Classification discovered 340 unclassified fields. Classifying them field-by-field in the UI is error-prone, leaves no audit trail in source control, and will be overwritten by any future metadata deploy that omits the classification attributes.

**Solution:**

Step 1 — Baseline with Tooling API to identify target fields:

```soql
SELECT QualifiedApiName, EntityDefinition.QualifiedApiName,
       SecurityClassification, ComplianceGroup
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName IN ('Contact', 'Patient__c')
  AND SecurityClassification = null
ORDER BY EntityDefinition.QualifiedApiName, QualifiedApiName
```

Step 2 — Add classification attributes to the custom field's `.field-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Date_of_Birth__c</fullName>
    <label>Date of Birth</label>
    <type>Date</type>
    <securityClassification>Restricted</securityClassification>
    <complianceGroup>PII</complianceGroup>
    <complianceGroup>HIPAA</complianceGroup>
    <businessStatus>Active</businessStatus>
</CustomField>
```

Step 3 — For standard `Contact.Email`, create a stub metadata file (do NOT copy the full standard field definition):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Email</fullName>
    <securityClassification>Confidential</securityClassification>
    <complianceGroup>PII</complianceGroup>
    <businessStatus>Active</businessStatus>
</CustomField>
```

Step 4 — Deploy and validate:

```bash
sf project deploy start --metadata "CustomField:Contact.Email,CustomField:Patient__c.Date_of_Birth__c"
```

Post-deploy Tooling API validation:

```soql
SELECT QualifiedApiName, SecurityClassification, ComplianceGroup
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName IN ('Contact', 'Patient__c')
  AND QualifiedApiName IN ('Email', 'Date_of_Birth__c')
```

**Why it works:** Metadata API deployment persists classification attributes in source control alongside the field definition, making classification a reproducible, version-controlled artifact. The stub file approach for standard fields allows classification to be set without overwriting any standard field behavior.

---

## Example 2: Auditing Unclassified Fields Across Multiple Objects

**Context:** A financial services org is preparing for a PCI DSS assessment. The security team needs to demonstrate that all fields storing cardholder data are labeled with `ComplianceGroup = PCI` and `SecurityClassification` of at least `Confidential`. The org has 15 custom objects related to payment processing.

**Problem:** There is no built-in Salesforce report that surfaces field-level classification metadata. The Setup UI shows one object at a time and cannot be exported to a structured format for auditors.

**Solution:**

Run a multi-object Tooling API query via Salesforce CLI:

```bash
sf data query \
  --query "SELECT QualifiedApiName, EntityDefinition.QualifiedApiName, SecurityClassification, ComplianceGroup, BusinessStatus FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName IN ('Payment__c','Transaction__c','CardHolder__c','PaymentMethod__c') ORDER BY EntityDefinition.QualifiedApiName, QualifiedApiName" \
  --use-tooling-api \
  --result-format csv \
  > field_classification_audit.csv
```

Then identify gaps — fields where `ComplianceGroup` does not include `PCI` or `SecurityClassification` is below `Confidential`:

```soql
SELECT QualifiedApiName, EntityDefinition.QualifiedApiName,
       SecurityClassification, ComplianceGroup
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName IN (
    'Payment__c', 'Transaction__c', 'CardHolder__c', 'PaymentMethod__c'
)
AND (SecurityClassification = null
     OR SecurityClassification = 'Public'
     OR SecurityClassification = 'Internal')
ORDER BY EntityDefinition.QualifiedApiName
```

Deliver the exported CSV to the auditors as the classification evidence, and the gap query results as the remediation backlog.

**Why it works:** Tooling API `FieldDefinition` exposes classification metadata for both standard and custom fields in a queryable, exportable format. It is the only mechanism for producing a structured classification inventory across an org at scale. The gap query identifies exactly which fields need remediation without manual review of 15 object Setup pages.

---

## Anti-Pattern: Relying on SecurityClassification to Restrict Field Access

**What practitioners do:** A team classifies a field as `SecurityClassification = Restricted` assuming that users without a "Restricted" permission level will no longer be able to see the field. They do not update Field-Level Security.

**What goes wrong:** The field remains visible to every profile that previously had access to it. `SecurityClassification` is a metadata label with no enforcement semantics. No platform mechanism reads the classification label and adjusts field visibility, encryption, or record access. The field is just as accessible as it was before — the label is purely informational.

**Correct approach:** Classification labels document governance intent but do not implement it. To actually restrict field access:
- Use Field-Level Security (FLS) to remove read/edit access on restricted profiles and permission sets.
- For encryption at rest, configure Shield Platform Encryption on the field (separate from classification).
- For masking in UI/API responses, evaluate Shield Data Mask or custom masking logic.

Classification and FLS are separate concerns and must both be configured intentionally.
