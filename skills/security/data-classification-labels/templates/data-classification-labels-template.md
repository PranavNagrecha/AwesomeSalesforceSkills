# Data Classification Labels — Work Template

Use this template when working on a data classification task.

## Scope

**Skill:** `security/data-classification-labels`

**Request summary:** (fill in what the user asked for)

**Target objects and fields:**

| Object | Field(s) | Custom or Standard |
|---|---|---|
| (e.g., Contact) | (e.g., Email, Phone) | Standard |
| (e.g., Patient__c) | (e.g., Date_of_Birth__c) | Custom |

## Context Gathered

- **Org has Shield license:** Yes / No / Unknown (required for Einstein Data Detect only)
- **Applicable compliance frameworks:** (e.g., HIPAA, PCI, GDPR, PII)
- **API version in sfdx-project.json:** (must be 46.0+)
- **Fields already classified:** (from Tooling API audit query — paste summary)
- **Known constraints:** (e.g., ComplianceGroup must use Metadata API, not Tooling API)

## Pre-Work: Tooling API Baseline Query

Run this before making any changes. Replace object names as needed.

```soql
SELECT QualifiedApiName,
       EntityDefinition.QualifiedApiName,
       SecurityClassification,
       ComplianceGroup,
       BusinessOwnerId,
       BusinessStatus
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName IN ('Contact', 'Lead', 'Account')
ORDER BY EntityDefinition.QualifiedApiName, QualifiedApiName
```

**Baseline results summary:** (paste field count, unclassified count)

## Classification Plan

| Object | Field | SecurityClassification | ComplianceGroup | BusinessStatus | BusinessOwner |
|---|---|---|---|---|---|
| Contact | Email | Confidential | PII | Active | (User Id) |
| Contact | SSN__c | Restricted | PII; HIPAA | Active | (User Id) |

## Approach

**Pattern from SKILL.md:** (which pattern applies — bulk Metadata API deploy, Tooling API audit, Data Detect, or combination)

**ComplianceGroup write path:** Metadata API or Setup UI (NOT Tooling API)

## Metadata Snippets

### Custom field with classification (add to existing `.field-meta.xml`):

```xml
<securityClassification>Restricted</securityClassification>
<complianceGroup>PII</complianceGroup>
<complianceGroup>HIPAA</complianceGroup>
<businessStatus>Active</businessStatus>
```

### Standard field classification stub (create new `.field-meta.xml`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Email</fullName>
    <securityClassification>Confidential</securityClassification>
    <complianceGroup>PII</complianceGroup>
    <businessStatus>Active</businessStatus>
</CustomField>
```

## Checklist

Copy from SKILL.md and tick as you complete each item:

- [ ] Tooling API baseline query run; pre-deploy state exported
- [ ] All target fields mapped to compliance framework
- [ ] Classification XML added to custom field metadata files
- [ ] Standard field stubs created (classification attributes only — no intrinsic field attributes)
- [ ] ComplianceGroup set via Metadata API or UI — not Tooling API write
- [ ] `sfdx-project.json` sourceApiVersion confirmed at 46.0 or later
- [ ] Deploy executed and completed without errors
- [ ] Post-deploy Tooling API validation run; results match classification plan
- [ ] Source control updated — no untracked classification changes remain in Setup
- [ ] BusinessOwnerId set for all Restricted and MissionCritical fields

## Post-Deploy Validation Query

```soql
SELECT QualifiedApiName, SecurityClassification, ComplianceGroup, BusinessStatus
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName IN ('Contact')
  AND QualifiedApiName IN ('Email', 'SSN__c')
```

**Expected result:** (fill in expected values from classification plan)

**Actual result:** (paste post-deploy output)

## Notes

(Record any deviations from the standard pattern and why.)
