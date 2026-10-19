# Metadata Examples — Relationship Fields That Encode the Design Decision

Each file below sets the attributes that carry the decision, so a reviewer can see the choice in the diff instead of in Setup.

## Junction object: two master-detail legs

The Metadata API guide: a junction object has two master-detail relationships; one parent is primary (`relationshipOrder` 0) and the other secondary (1), and that choice affects delete behaviour, look and feel, and record ownership for the junction.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Enrollment__c/fields/Course__c.field-meta.xml (primary leg) -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Course__c</fullName>
    <label>Course</label>
    <type>MasterDetail</type>
    <referenceTo>Course__c</referenceTo>
    <relationshipName>Enrollments</relationshipName>
    <relationshipOrder>0</relationshipOrder>
    <reparentableMasterDetail>false</reparentableMasterDetail>
    <writeRequiresMasterRead>false</writeRequiresMasterRead>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Enrollment__c/fields/Student__c.field-meta.xml (secondary leg) -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Student__c</fullName>
    <label>Student</label>
    <type>MasterDetail</type>
    <referenceTo>Contact</referenceTo>
    <relationshipName>Course_Enrollments</relationshipName>
    <relationshipOrder>1</relationshipOrder>
    <reparentableMasterDetail>false</reparentableMasterDetail>
    <writeRequiresMasterRead>false</writeRequiresMasterRead>
</CustomField>
```

| Attribute | Value here | Why |
|---|---|---|
| `relationshipOrder` | 0 for Course, 1 for Student | Course is primary; the junction's owner and look and feel follow it |
| `reparentableMasterDetail` | false (the default) | An enrollment never moves to another course or student |
| `writeRequiresMasterRead` | false | Users need Read/Write on the master to create, edit, or delete enrollments; true would allow Read-only users |

A leg to Product2, Pricebook2, Lead, User, or the other never-master objects must be a `Lookup` instead, and that parent gets no native roll-up.

## Lookup that blocks parent deletion

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Service_Visit__c/fields/Asset__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Asset__c</fullName>
    <label>Asset</label>
    <type>Lookup</type>
    <referenceTo>Asset</referenceTo>
    <relationshipName>Service_Visits</relationshipName>
    <deleteConstraint>Restrict</deleteConstraint>
    <required>false</required>
</CustomField>
```

`Restrict` prevents deleting an Asset that still has visits; `SetNull` (the default) would clear the field and leave the visits orphaned.

## Integration key

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Course__c/fields/SIS_Course_Code__c.field-meta.xml -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>SIS_Course_Code__c</fullName>
    <label>SIS Course Code</label>
    <type>Text</type>
    <length>30</length>
    <externalId>true</externalId>
    <unique>true</unique>
    <caseSensitive>false</caseSensitive>
</CustomField>
```

External ID indexes the field and makes it the upsert key; Unique rejects duplicates; `caseSensitive` false means `CS-101` and `cs-101` are the same key.

Run `python3 skills/data/data-model-design-patterns/scripts/check_data_model.py --manifest-dir force-app/main/default` after adding fields like these.
