# Metadata and API Examples: Referral Management Health Cloud

Deployable and runnable artifacts for this skill. Each block names the file path it lives at. Narrative examples are in `references/examples.md`.

## Example 1: Searchable Provider Attribute, Referral Intake API, and Verification Query

**Context:** Care coordinators want to filter provider search by "accepting new patients", and a partner hospital will send referrals from its own system.

**Artifact 1: provider search mapping** (Metadata API type `CareProviderSearchConfig`, suffix `.careProviderSearchConfig`, folder `careProviderSearchConfigs`, API 48.0+, per the Agentforce Health Developer Guide).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/objects/HealthcareProvider/fields/Accepting_New_Patients__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Accepting_New_Patients__c</fullName>
    <defaultValue>false</defaultValue>
    <description>Source field for provider search: practitioner accepts new patients.</description>
    <label>Accepting New Patients</label>
    <type>Checkbox</type>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/objects/CareProviderSearchableField/fields/Accepting_New_Patients__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Accepting_New_Patients__c</fullName>
    <defaultValue>false</defaultValue>
    <description>Target field populated from HealthcareProvider.Accepting_New_Patients__c.</description>
    <label>Accepting New Patients</label>
    <type>Checkbox</type>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/careProviderSearchConfigs/Accepting_New_Patients.careProviderSearchConfig-meta.xml -->
<CareProviderSearchConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <sourceField>Accepting_New_Patients__c</sourceField>
    <targetField>Accepting_New_Patients__c</targetField>
    <mappedObject>HealthcareProvider</mappedObject>
    <isProtected>false</isProtected>
    <isActive>true</isActive>
    <masterLabel>Accepting New Patients</masterLabel>
</CareProviderSearchConfig>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>HealthcareProvider.Accepting_New_Patients__c</members>
        <members>CareProviderSearchableField.Accepting_New_Patients__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Accepting_New_Patients</members>
        <name>CareProviderSearchConfig</name>
    </types>
    <version>67.0</version>
</Package>
```

The guide's own sample deploys the same three members (two `CustomField` entries and one `CareProviderSearchConfig`). UNVERIFIED (2026-10-03): the `-meta.xml` file suffix under `force-app` follows the source-format convention for `.careProviderSearchConfig`; the guide states the suffix and folder for the Metadata API zip format.

**Artifact 2: referral intake call from the partner hospital** (`POST /services/data/v66.0/connect/health/referral-management/referrals`, API 59.0+). The API creates Account, ClinicalServiceRequest, and ClinicalServiceRequestDetail records.

```json
{
  "patient": {
    "fields": { "FirstName": "Joe", "LastName": "Clark", "Phone": "8015550189" }
  },
  "requester": { "id": "<HealthcareProvider id of the referring physician>" },
  "performers": [
    { "id": "<HealthcareProvider id, specialist 1>" },
    { "id": "<HealthcareProvider id, specialist 2>" }
  ],
  "referral": {
    "fields": { "Priority": "Routine", "Status": "Draft", "Type": "Plan" }
  },
  "referralDetails": [
    {
      "detailType": "Insurance",
      "detailRecordType": "Member Plan",
      "fields": { "Name": "Aetna PPO", "MemberNumber": "2345678" }
    }
  ],
  "referralNotes": "Cardiology consult for abnormal stress test.",
  "shouldUseHighConfidenceMatch": true
}
```

Rules from the REST Reference: `patient` and `referral` are required; at most five `performers`; a new patient is created from `patient.fields` unless high-confidence matching finds an existing record.

**Artifact 3: verification query for the coordinator queue**

```sql
SELECT Id, Name, Patient.Name, Requester.Name, Performer.Name,
       Status, IsAccepted, StatusReason, Priority, StartDate
FROM ClinicalServiceRequest
WHERE Status IN ('Draft', 'Active') AND IsAccepted = false
ORDER BY Priority, StartDate
```

UNVERIFIED (2026-10-03): the relationship names `Patient`, `Requester`, and `Performer` are assumed from the field names; the object reference read for this revision lists the fields and their targets but not the polymorphic relationship names. Remove the `.Name` columns if the query does not compile.

**Why it works:** The mapping makes the new attribute searchable without custom search code, the API gives the partner one documented intake path with duplicate matching, and the query uses only fields from the object reference.
