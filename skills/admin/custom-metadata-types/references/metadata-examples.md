# Metadata Examples — Custom Metadata Types

Deployable shapes for a Custom Metadata Type, its fields, and its records. Element names, enum values, and the skeletons come from the Metadata API Developer Guide (v62 PDF, `Custom Metadata Types (CustomObject)`, `CustomMetadata`, `CustomMetadataValue` sections, pp. 745–752); the worked example below extends the guide's `ReusablePicklist` sample into a realistic routing-threshold type. Validate the result with:

```bash
python3 skills/admin/custom-metadata-types/scripts/check_custom_metadata_types.py --manifest-dir force-app/main/default
```

## Where the files live

| Component | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| The type | `CustomObject`, member `Routing_Rule__mdt` | `objects/Routing_Rule__mdt/Routing_Rule__mdt.object-meta.xml` | 31.0+ |
| A field on the type | `CustomField`, member `Routing_Rule__mdt.Threshold__c` | `objects/Routing_Rule__mdt/fields/Threshold__c.field-meta.xml` | 31.0+ |
| A record | `CustomMetadata`, member `Routing_Rule.EMEA_High` | `customMetadata/Routing_Rule.EMEA_High.md-meta.xml` | 31.0+ |

The type is a `CustomObject` with an `__mdt` suffix instead of `__c`, stored in the `objects` folder; its field names keep the `__c` suffix and must be dot-qualified with the type name in package.xml. Records have the suffix `.md`, live in `customMetadata`, and — unlike the type — carry **no** double-underscore suffix: the record file name is `<TypeNameWithout__mdt>.<RecordDeveloperName>`. Both `CustomObject` and `CustomMetadata` accept the `*` wildcard in package.xml.

## How to read the example

- **`visibility` is on the type, `protected` is on the record.** They are different switches with different blast radii — see `references/gotchas.md`.
- **`visibility` has exactly three values**: `Public` (default), `Protected`, `PackageProtected` (47.0+). Nothing else validates.
- **Every `<values>` block needs `<field>` and `<value>`.** `<field>` is the non-object-qualified field name including `__c` and, for a managed-package type, the namespace — the type name is *not* part of it.
- **`xsi:type` on `<value>` must match the field's type**, from the guide's table: `xsd:boolean` → Checkbox, `xsd:string` → Text / Phone / TextArea / URL / Email, `xsd:int` → Number or Percent with scale 0, `xsd:double` → Number or Percent with scale ≠ 0, `xsd:date` → Date, `xsd:dateTime` → Date/Time, `xsd:picklist` → Picklist. The attribute may be omitted entirely (`<value>true</value>`).
- **Omitting a `<values>` block is not the same as clearing it.** A missing block leaves the field at its previous value on an update and null on a first deploy; `<value xsi:nil="true"/>` is the only way to explicitly clear a field.
- **A Number field with scale 0 reads back as a double.** The guide states that a UI value of `1234567` is returned as `1234567.0` through the API, so Apex should use `Integer.valueOf()` rather than assuming an integer type.
- **Fields on a CMT can carry `fieldManageability`** (`Locked`, `DeveloperControlled`, `SubscriberControlled`) — this element is valid only on custom metadata type fields, and it decides who may change the value after a managed release.

## The type: `Routing_Rule__mdt`

Source format (DX) keeps type-level elements in the `.object-meta.xml` and each field in its own file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Routing Rule</label>
    <pluralLabel>Routing Rules</pluralLabel>
    <description>Score thresholds and target queues for Case routing. Deployed with the release; not edited in production.</description>
    <visibility>Public</visibility>
</CustomObject>
```

Metadata API format (a retrieved `.object` file, or the shape the guide's own sample uses) nests the fields in the same file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <fields>
        <fullName>Threshold__c</fullName>
        <externalId>false</externalId>
        <label>Score Threshold</label>
        <precision>3</precision>
        <scale>0</scale>
        <required>false</required>
        <type>Number</type>
        <unique>false</unique>
    </fields>
    <label>Routing Rule</label>
    <pluralLabel>Routing Rules</pluralLabel>
    <visibility>Public</visibility>
</CustomObject>
```

`description` on the type accepts a maximum of 1,000 characters.

## Field 1 — Number

`objects/Routing_Rule__mdt/fields/Threshold__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Threshold__c</fullName>
    <externalId>false</externalId>
    <label>Score Threshold</label>
    <precision>3</precision>
    <scale>0</scale>
    <required>false</required>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

## Field 2 — Text, subscriber-editable

`objects/Routing_Rule__mdt/fields/Queue_Developer_Name__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Queue_Developer_Name__c</fullName>
    <externalId>false</externalId>
    <label>Queue Developer Name</label>
    <length>40</length>
    <required>true</required>
    <type>Text</type>
    <unique>false</unique>
    <fieldManageability>SubscriberControlled</fieldManageability>
</CustomField>
```

The value is a queue **developer name**, not a queue Id. Ids differ per org; developer names survive a deploy.

Mark a field `<unique>true</unique>` and `<externalId>true</externalId>` when it needs to be indexable — the guide states this is how you make custom metadata type fields unique and indexable.

## Field 3 — Metadata Relationship to `EntityDefinition`

`objects/Routing_Rule__mdt/fields/Target_Object__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Target_Object__c</fullName>
    <externalId>false</externalId>
    <label>Target Object</label>
    <referenceTo>EntityDefinition</referenceTo>
    <relationshipLabel>Routing Rules</relationshipLabel>
    <relationshipName>Routing_Rules</relationshipName>
    <required>false</required>
    <type>MetadataRelationship</type>
</CustomField>
```

UNVERIFIED (2026-09-04): the Metadata API guide documents `MetadataRelationship` as a valid `FieldType` and documents `referenceTo`, `relationshipLabel`, and `relationshipName` as `CustomField` elements, but it publishes no complete sample of a `MetadataRelationship` field definition. The exact required element set above is inferred from the standard lookup-field shape — retrieve one from an org before trusting it.

What *is* documented is the value side: a record's `EntityDefinition` field holds the **qualified API name** of the entity, and a `FieldDefinition` field holds the qualified API name of the field it points to. A `FieldDefinition` (or entity particle) relationship additionally requires `metadataRelationshipControllingField`, naming the entity-definition field that determines which object's fields are selectable. Manageability is coupled: if the entity-definition field is subscriber-controlled the field-definition field must also be subscriber-controlled; if it is upgradeable the field-definition field must be upgradeable or subscriber-controlled.

## Record 1 — `customMetadata/Routing_Rule.EMEA_High.md-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>EMEA High Priority</label>
    <description>Cases scoring 80 or above in EMEA go to the EMEA escalation queue.</description>
    <protected>false</protected>
    <values>
        <field>Threshold__c</field>
        <value xsi:type="xsd:int">80</value>
    </values>
    <values>
        <field>Queue_Developer_Name__c</field>
        <value xsi:type="xsd:string">EMEA_Escalation_Queue</value>
    </values>
    <values>
        <field>Target_Object__c</field>
        <value xsi:type="xsd:string">Case</value>
    </values>
</CustomMetadata>
```

## Record 2 — `customMetadata/Routing_Rule.EMEA_Default.md-meta.xml`

The second record deliberately clears `Threshold__c` with `xsi:nil` rather than omitting the block, so a redeploy over an edited org resets it:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>EMEA Default</label>
    <protected>false</protected>
    <values>
        <field>Threshold__c</field>
        <value xsi:nil="true"/>
    </values>
    <values>
        <field>Queue_Developer_Name__c</field>
        <value xsi:type="xsd:string">EMEA_Standard_Queue</value>
    </values>
    <values>
        <field>Target_Object__c</field>
        <value xsi:type="xsd:string">Case</value>
    </values>
</CustomMetadata>
```

`description` on a record also accepts a maximum of 1,000 characters. `label` is what the packaging UI shows; records are not otherwise visible in Setup as ordinary records.

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Routing_Rule__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Routing_Rule__mdt.Threshold__c</members>
        <members>Routing_Rule__mdt.Queue_Developer_Name__c</members>
        <members>Routing_Rule__mdt.Target_Object__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Routing_Rule.EMEA_High</members>
        <members>Routing_Rule.EMEA_Default</members>
        <name>CustomMetadata</name>
    </types>
    <version>62.0</version>
</Package>
```

Note the asymmetry the guide calls out explicitly: `CustomObject` and `CustomField` members carry `__mdt`, `CustomMetadata` members do not. With a namespace `acme`, the type becomes `acme__Routing_Rule__mdt`, the field value in a record's `<field>` becomes `acme__Threshold__c`, and the record member becomes `acme__Routing_Rule.EMEA_High`. A subscriber viewing a record whose *record* also came from a second package sees both namespaces: `acme__Routing_Rule.other__EMEA_High`.

To pull every record instead of listing them:

```xml
<types>
    <members>*</members>
    <name>CustomMetadata</name>
</types>
```

## Retrieve and deploy

```bash
# Retrieve the type, its fields, and every record
sf project retrieve start \
  --metadata "CustomObject:Routing_Rule__mdt" \
  --metadata "CustomMetadata" \
  --target-org devhub-sandbox

# Validate without committing (check-only), running no tests
sf project deploy validate \
  --manifest manifest/package.xml \
  --target-org prod

# Deploy
sf project deploy start \
  --manifest manifest/package.xml \
  --target-org prod
```

Deploy the type and its fields **before or with** the records: a record whose `<field>` names a field that does not yet exist in the target org fails the deploy. A single manifest containing all three types handles the ordering for you.

## Verify

Confirm the records landed and the values are typed as expected. `DeveloperName`, `MasterLabel`, `Label`, `QualifiedApiName`, `NamespacePrefix`, and `isProtected` are standard fields on every `__mdt` object.

```sql
SELECT DeveloperName, MasterLabel, QualifiedApiName, isProtected,
       Threshold__c, Queue_Developer_Name__c, Target_Object__c
FROM Routing_Rule__mdt
ORDER BY DeveloperName
```

Expect `Threshold__c` to come back as `80.0` for `EMEA_High` (scale-0 Number fields are returned as doubles) and `null` for `EMEA_Default`.

Then confirm the runtime access path an agent or Flow will actually use.

```apex
// Cached accessor — no SOQL, but every field is truncated to 255 characters
Routing_Rule__mdt rule = Routing_Rule__mdt.getInstance('EMEA_High');
System.assertEquals('EMEA_Escalation_Queue', rule.Queue_Developer_Name__c);

// All records, keyed by DeveloperName
Map<String, Routing_Rule__mdt> all = Routing_Rule__mdt.getAll();

// SOQL — returns untruncated field values, and custom metadata records
// can have unlimited SOQL queries in a single Apex transaction
List<Routing_Rule__mdt> rules = [
    SELECT DeveloperName, Threshold__c, Queue_Developer_Name__c
    FROM Routing_Rule__mdt
    WHERE Threshold__c != null
    ORDER BY Threshold__c DESC
];
```

In Flow, read the same records with a **Get Records** element on `Routing_Rule__mdt` filtered on `DeveloperName`, and give it a decision branch for the no-record case — `getInstance` returns `null` for an unmatched name and Get Records returns nothing, so both consumers need a fallback. In a formula field or validation rule the path is `$CustomMetadata.Routing_Rule__mdt.EMEA_High.Threshold__c` (validation rules have supported custom metadata types since API version 40.0).

Do not expect the records to browse like ordinary records. The Metadata API guide states that custom metadata types "are visible only through the recently used objects list on the Lightning Platform Home Page and in the packaging user interface", and that custom metadata records "are currently visible only through the packaging user interface". UNVERIFIED (2026-09-04): the **Setup → Custom Metadata Types → Manage Records** path that admins use in practice is a Setup UI affordance not described in these PDFs. If a query returns nothing after a successful deploy, check the profile or permission-set custom metadata type access before assuming the deploy lied — see `references/gotchas.md`.
