# Metadata Examples: HIPAA Workflow Design

A deployable worked example of the HIPAA design patterns in `SKILL.md`: a patient intake object whose PHI fields are tagged in metadata, tracked for history where the platform allows it, kept beyond 18 months with a Field Audit Trail policy, encrypted where Shield is licensed, and exposed field by field through role permission sets.

Grounding: Metadata API Developer Guide, CustomField `complianceGroup`, `securityClassification`, `encryptionScheme`, `trackHistory` (`api_meta L43334-43345`, `L43387-43396`, `L43614-43622`, `L43675-43682`), CustomObject `enableHistory` (`api_meta L42040`), HistoryRetentionPolicy (`api_meta L44074-44125`), PermissionSet (`api_meta L94772-94840`); Salesforce Security Guide, Field Audit Trail and untrackable fields (`salesforce_security_impl_guide L4823-4906`).

Licence gate: `historyRetentionPolicy` needs Field Audit Trail and the `RetainFieldHistory` permission; `encryptionScheme` needs Shield Platform Encryption with an active tenant secret. Both are marked optional below so the core example deploys in any org.

## 1. The object, with history and a retention policy

`force-app/main/default/objects/Patient_Intake__c/Patient_Intake__c.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Intake details captured before the first clinical encounter. Contains PHI.</description>
    <enableHistory>true</enableHistory>
    <historyRetentionPolicy>
        <archiveAfterMonths>18</archiveAfterMonths>
        <archiveRetentionYears>7</archiveRetentionYears>
        <description>Keep intake field history; archive after 18 months; review for deletion after 7 years</description>
    </historyRetentionPolicy>
    <label>Patient Intake</label>
    <nameField>
        <displayFormat>INT-{0000000}</displayFormat>
        <label>Intake Number</label>
        <type>AutoNumber</type>
    </nameField>
    <pluralLabel>Patient Intakes</pluralLabel>
    <sharingModel>Private</sharingModel>
</CustomObject>
```

| Element | Notes |
|---|---|
| `sharingModel` `Private` | Minimum necessary starts with no default record access |
| `enableHistory` | Required before any field can set `trackHistory` |
| `historyRetentionPolicy` | Optional; needs Field Audit Trail and `RetainFieldHistory`. `archiveAfterMonths` is 1 to 18 (default 18). `archiveRetentionYears` is only a reminder; nothing is deleted automatically |

UNVERIFIED (2026-10-03): the CustomObject field table marks `historyRetentionPolicy` "Reserved for future use" while the HistoryRetentionPolicy entry shows it inside `CustomObject`; deploy to a sandbox with Field Audit Trail first, then retrieve to confirm the policy is present. Remove the element in orgs without Field Audit Trail.

## 2. PHI fields, tagged and tracked

`force-app/main/default/objects/Patient_Intake__c/fields/Medical_Record_Number__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Medical_Record_Number__c</fullName>
    <complianceGroup>HIPAA</complianceGroup>
    <externalId>false</externalId>
    <label>Medical Record Number</label>
    <length>40</length>
    <required>false</required>
    <securityClassification>Restricted</securityClassification>
    <trackHistory>true</trackHistory>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

`force-app/main/default/objects/Patient_Intake__c/fields/Intake_Notes__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Intake_Notes__c</fullName>
    <complianceGroup>HIPAA</complianceGroup>
    <label>Intake Notes</label>
    <length>32768</length>
    <securityClassification>Restricted</securityClassification>
    <type>LongTextArea</type>
    <visibleLines>6</visibleLines>
</CustomField>
```

`Intake_Notes__c` has no `trackHistory`: long text fields cannot be history-tracked. Its audit evidence must come from somewhere else (for example, a versioned child record per edit), and the design must say so.

### Optional: encryption where Shield is licensed

Add this element to `Medical_Record_Number__c` only in orgs with Shield Platform Encryption and an active tenant secret:

```xml
<!-- excerpt: add inside the Medical_Record_Number__c CustomField element -->
<encryptionScheme>ProbabilisticEncryption</encryptionScheme>
```

Valid values are `CaseInsensitiveDeterministicEncryption`, `CaseSensitiveDeterministicEncryption`, `None`, and `ProbabilisticEncryption`. Enable encryption before this field's history is archived; archived history is not encrypted retroactively (`gotchas.md` gotcha 4).

## 3. Field-level access per role

`force-app/main/default/permissionsets/Patient_Intake_Front_Desk.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Front desk: create intakes and see the MRN; no access to intake notes</description>
    <fieldPermissions>
        <editable>true</editable>
        <field>Patient_Intake__c.Medical_Record_Number__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>false</editable>
        <field>Patient_Intake__c.Intake_Notes__c</field>
        <readable>false</readable>
    </fieldPermissions>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Patient Intake Front Desk</label>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Patient_Intake__c</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</PermissionSet>
```

`force-app/main/default/permissionsets/Patient_Intake_Clinician.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Clinicians: read MRN, read and edit intake notes on records shared with them</description>
    <fieldPermissions>
        <editable>false</editable>
        <field>Patient_Intake__c.Medical_Record_Number__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Patient_Intake__c.Intake_Notes__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Patient Intake Clinician</label>
    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Patient_Intake__c</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
</PermissionSet>
```

Neither permission set grants View All or Modify All, so record access still comes from sharing on the Private object.

## 4. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Patient_Intake__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Patient_Intake__c.Intake_Notes__c</members>
        <members>Patient_Intake__c.Medical_Record_Number__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Patient_Intake_Clinician</members>
        <members>Patient_Intake_Front_Desk</members>
        <name>PermissionSet</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy order

1. `CustomObject` (with or without the retention policy, per licence).
2. `CustomField` (add `encryptionScheme` only where Shield is active).
3. `PermissionSet`, then assign by role.

## Verification

- Edit the MRN on a test record: a history row appears; editing intake notes produces none, which matches the documented limit.
- With Field Audit Trail, retrieve `CustomObject:Patient_Intake__c` and confirm the custom retention policy is returned (the default policy is not returned on retrieve).
- A front desk user can see the MRN but not the notes; a clinician sees both on records shared with them.
- Search the repository for fields under the object without `complianceGroup` (see `examples.md` Example 3).
