# Metadata Examples — Custom Field Creation

Every custom field is one `CustomField` component. The Metadata API Developer Guide defines it as
"the metadata associated with a field. Use this metadata type to create, update, or delete custom
field definitions on standard, custom, and external objects or standard field definitions on
standard objects" (api_meta.txt:43204–43206).

Formula fields are also `CustomField` components but their design decisions are different — read
`admin/formula-fields` → `references/metadata-examples.md` for the `formula` /
`formulaTreatBlanksAs` pair. Nothing below repeats it.

## Where the file lives

| Form | Path | Root element |
|---|---|---|
| DX source format | `objects/Account/fields/Contract_Number__c.field-meta.xml` | `CustomField` |
| Metadata API zip | `objects/Account.object` — each field is a `<fields>` entry | `CustomObject` |

The guide documents the embedded form — "Custom fields are user-defined fields and are part of the
custom object or standard object definition" (api_meta.txt:43248–43249) — and its own sample
definition shows `<fields>` inside `<CustomObject>` (api_meta.txt:43934–43975). `sf project
retrieve start` decomposes each field into its own `.field-meta.xml` rooted at `<CustomField>`.
Element names and ordering are identical in both forms.

`fullName` is object-qualified everywhere except inside a decomposed file. The guide's examples:
`MyCustomObject__c.MyCustomField__c`, `Account.MyAcctCustomField__c`, `Account.Phone`
(api_meta.txt:43222–43229). Inside `Contract_Number__c.field-meta.xml` the `fullName` is the bare
`Contract_Number__c`, matching the file name.

## The elements this skill cares about

| Element | Type | What the guide says | Line |
|---|---|---|---|
| `type` | `FieldType` enum | The field type; enum values are listed under Metadata Field Types | 43695–43700 |
| `label` | string | "Label for the field." | 43478 |
| `description` | string | "Description of the field." | 43360 |
| `inlineHelpText` | string | "Represents the content of field-level help." | 43455–43456 |
| `required` | boolean | "Indicates whether the field requires a value on creation (true) or not (false)." | 43598–43600 |
| `unique` | boolean | "Indicates whether the field is unique (true) or not (false)." | 43702 |
| `caseSensitive` | boolean | "Indicates whether the field is case-sensitive (true) or not (false)." | 43328–43333 |
| `externalId` | boolean | "Returned only if the custom field data type is AutoNumber, Email, Number, or Text." | 43402–43405 |
| `length` | int | "Length of the field." | 43481 |
| `precision` / `scale` | int | "Precision is the number of digits in a number… scale is the number of digits to the right of the decimal point." | 43563–43566, 43610–43612 |
| `defaultValue` | string | "If specified, represents the default value of the field." | 43346 |
| `visibleLines` | int | "Indicates the number of lines displayed for the field." | 43723 |
| `referenceTo` | string | "Indicates a reference this field has to another object." | 43574 |
| `relationshipName` / `relationshipLabel` | string | The one-to-many relationship API name and its label | 43576–43581 |
| `deleteConstraint` | `DeleteConstraint` enum | `Cascade`, `Restrict`, `SetNull` — "`SetNull`… is the default." | 43348–43356 |
| `lookupFilter` | `LookupFilter` | Filter definition; "up to 10 FilterItems per lookup filter" | 43483–43492, 43860–43893 |
| `relationshipOrder` | int | Junction primary (`0`) / secondary (`1`); "0 is always the value for objects that aren't junction objects" | 43582–43592 |
| `reparentableMasterDetail` | boolean | "Indicates whether the child records… can be reparented… The default value is false." | 43593–43597 |
| `writeRequiresMasterRead` | boolean | `true` = Read on the primary is enough to create/edit/delete children; `false` is the default and more restrictive | 43725–43742 |
| `valueSet` | `ValueSet` | Picklist values; `restricted`, `valueSetDefinition`, `valueSetName` | 43704–43715, 45843–45856 |
| `trackHistory` | boolean | Needs `enableHistory` `true` on the object | 43675–43683 |
| `trackFeedHistory` | boolean | Needs `enableFeeds` `true` on the object | 43668–43674 |
| `trackTrending` | boolean | "An object is enabled for historical trending if this attribute is true for at least one field." | 43684–43692 |
| `securityClassification` | picklist | `Public`, `Internal`, `Confidential`, `Restricted`, `MissionCritical` (v45.0+) | 43614–43622 |
| `complianceGroup` | multipicklist | `CCPA`, `COPPA`, `GDPR`, `HIPAA`, `PCI`, `PII` (v47.0+) | 43334–43345 |
| `businessStatus` | picklist | `Active`, `DeprecateCandidate`, `Hidden` (v45.0+) | 43313–43320 |
| `encryptionScheme` | enum | Shield, not Classic: `CaseInsensitiveDeterministicEncryption`, `CaseSensitiveDeterministicEncryption`, `None`, `ProbabilisticEncryption` (v44.0+) | 43387–43401 |

`FieldType` valid values, verbatim from Metadata Field Types (api_meta.txt:45718–45765):
`Address`, `AutoNumber`, `Lookup`, `MasterDetail`, `MetadataRelationship`, `Checkbox`, `Currency`,
`Date`, `DateTime`, `Email`, `EncryptedText`, `ExternalLookup`, `IndirectLookup`, `Number`,
`Percent`, `Phone`, `Picklist`, `MultiselectPicklist`, `Summary`, `Text`, `TextArea`,
`LongTextArea`, `Url`, `Hierarchy`, `File`, `Html`, `Location`, `Time`, `Array`, `Integer`, `Long`.
Note the spellings an LLM gets wrong: it is `MasterDetail`, not `Master-Detail`; `Url`, not `URL`;
`Location`, not `Geolocation`; `Summary`, not `RollUpSummary`; `MultiselectPicklist`, not
`MultiPicklist`.

---

## 1. Required text field with description and help text

`objects/Contract__c/fields/Contract_Number__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Contract_Number__c</fullName>
    <description>Customer-facing contract number printed on the signed PDF. Owner: Revenue Ops. Populated by the CLM integration on activation; never edited by hand.</description>
    <externalId>false</externalId>
    <inlineHelpText>The number that appears on the signed contract PDF, top right. If blank, the contract has not been activated in the CLM system yet.</inlineHelpText>
    <label>Contract Number</label>
    <length>40</length>
    <required>true</required>
    <trackFeedHistory>false</trackFeedHistory>
    <trackHistory>true</trackHistory>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

How to read it:

- `required` `true` is a database constraint, not a layout setting. The guide's wording is "requires
  a value on creation" (api_meta.txt:43598–43600) — every DML path pays it, including Data Loader,
  Bulk API 2.0, Flow, and Apex.
- `required` `true` also removes this field from permission-set deployability: "In API version 30.0
  and later, permissions for required fields can't be retrieved or deployed"
  (api_meta.txt:95020–95021). Do not write a `fieldPermissions` entry for it — see §9.
- `description` is for admins; `inlineHelpText` is "the content of field-level help"
  (api_meta.txt:43455–43456) and is what the end user sees behind the "i" icon. They are different
  audiences and both are worth writing. The skill's checker warns when either is missing.
- `trackHistory` `true` deploys only if the object already has `enableHistory` `true`
  (api_meta.txt:43678–43680). Deploy the object change first or in the same package.

---

## 2. External ID text field — `unique` and `caseSensitive` set deliberately

`objects/Account/fields/ERP_Account_Code__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>ERP_Account_Code__c</fullName>
    <caseSensitive>true</caseSensitive>
    <description>Primary key from SAP. Upsert target for the nightly account sync (Bulk API 2.0 externalIdFieldName). Unique + case sensitive because SAP issues ACME01 and acme01 as distinct customers.</description>
    <externalId>true</externalId>
    <inlineHelpText>SAP customer code. Do not edit; the nightly sync owns this value.</inlineHelpText>
    <label>ERP Account Code</label>
    <length>18</length>
    <required>false</required>
    <trackFeedHistory>false</trackFeedHistory>
    <trackHistory>false</trackHistory>
    <type>Text</type>
    <unique>true</unique>
</CustomField>
```

How to read it:

- `externalId` and `unique` are two independent booleans and the pairing is the whole point.
  `externalId` `true` alone makes the field an upsert key without making the key unique. When the
  key matches more than one record, REST upsert returns "300 — The value returned when an external
  ID exists in more than one record" and "the record isn't created or updated"
  (api_rest.txt:1134–1135, 2963–2966). `unique` `true` is what prevents the org from ever reaching
  that state.
- `externalId` is only meaningful on four types: it "is returned only if the custom field data type
  is AutoNumber, Email, Number, or Text" (api_meta.txt:43402–43405).
- Setting `externalId` indexes the field: "A custom field is indexed if its External ID field is
  selected" (api_asynch.txt:1509–1510). That is also what makes
  `Parent__r.ERP_Account_Code__c` legal as a Bulk API CSV column header
  (api_asynch.txt:1503–1522) — a lookup can be resolved on load without an Id.
- `caseSensitive` `true` means `ACME01` and `acme01` are two different keys. Set it `false` when the
  source system is case-insensitive, or the sync creates duplicates the moment someone re-keys a
  code in a different case.

---

## 3. Number field — `precision` and `scale` are one decision, not two

`objects/Contract__c/fields/Annual_Value__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Annual_Value__c</fullName>
    <description>Contract value in the contract currency, excluding tax. Sourced from CLM. Precision 18 / scale 2 to match the SAP amount column.</description>
    <externalId>false</externalId>
    <inlineHelpText>Annual contract value excluding tax, in the contract currency.</inlineHelpText>
    <label>Annual Value</label>
    <precision>18</precision>
    <required>false</required>
    <scale>2</scale>
    <trackFeedHistory>false</trackFeedHistory>
    <trackHistory>false</trackHistory>
    <trackTrending>false</trackTrending>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

How to read it:

- The guide defines them together: "Precision is the number of digits in a number. For example, the
  number 256.99 has a precision value of 5" (api_meta.txt:43563–43566) and "Scale is the number of
  digits to the right of the decimal point… the number 256.99 has a scale of 2"
  (api_meta.txt:43610–43612). Precision is the **total**, so `precision` 18 / `scale` 2 means 16
  digits left of the point, not 18.
- The Setup UI asks the question the other way round — Length (left of the point) and Decimal
  Places — so a field created in Setup as "16, 2" is `precision` 18 / `scale` 2 in metadata. An LLM
  that transcribes the Setup numbers into the XML silently shrinks the field.
- A `Number` field is "internally represented as a field of type double. Setting the scale of the
  Number field to 0 gives you a double that behaves like an int" (api_meta.txt:45766–45768).

---

## 4. Checkbox with a default, and a Date field — both in the packaged `CustomObject` form

`objects/Contract__c.object` (Metadata API zip form; the same two `<fields>` blocks are what DX
decomposes into two `.field-meta.xml` files)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: only the two <fields> entries this section discusses are shown. -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <fields>
        <fullName>Auto_Renew__c</fullName>
        <defaultValue>false</defaultValue>
        <description>Set true when the contract renews without a signature. Drives the 90-day renewal Flow.</description>
        <externalId>false</externalId>
        <inlineHelpText>Check this box if the contract renews automatically at term end.</inlineHelpText>
        <label>Auto Renew</label>
        <trackFeedHistory>false</trackFeedHistory>
        <trackHistory>true</trackHistory>
        <type>Checkbox</type>
    </fields>
    <fields>
        <fullName>Contract_Expiry_Date__c</fullName>
        <description>Last day of the current term. Renewal outreach Flow fires 30 days before this date.</description>
        <externalId>false</externalId>
        <inlineHelpText>Last day the contract is in force. Renewal outreach starts 30 days before this date.</inlineHelpText>
        <label>Contract Expiry Date</label>
        <required>false</required>
        <trackFeedHistory>false</trackFeedHistory>
        <trackHistory>true</trackHistory>
        <type>Date</type>
    </fields>
</CustomObject>
```

How to read it:

- A `Checkbox` has no `required` element. It always has a value, so `defaultValue` is what decides
  which one — "If specified, represents the default value of the field" (api_meta.txt:43346). Omit
  `defaultValue` and you are deploying whichever default the platform picks rather than a decision
  you made. Write `false` explicitly when unchecked is the intent.
- A `Checkbox` `defaultValue` is the literal `true` or `false`, not a formula string.
- `Date` has no time component and no `precision`/`scale`. Choose `Date` over `DateTime` when the
  business fact is a calendar day; `DateTime` is stored in UTC and will render as the previous or
  next day for users in other time zones.
- Both fields carry `trackHistory` `true`. Field history is the only durable record of who changed a
  renewal flag — see `admin/system-field-behavior-and-audit` for retention and query patterns.

---

## 5. Lookup relationship with `deleteConstraint` and a `lookupFilter`

`objects/Contract__c/fields/Billing_Contact__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Billing_Contact__c</fullName>
    <deleteConstraint>Restrict</deleteConstraint>
    <description>Contact who receives the invoice. Restrict, not SetNull: an invoice run with a blank billing contact fails silently downstream, so deleting the Contact must be blocked instead.</description>
    <externalId>false</externalId>
    <inlineHelpText>Contact who receives invoices for this contract. Must be a contact on the same account.</inlineHelpText>
    <label>Billing Contact</label>
    <lookupFilter>
        <active>true</active>
        <booleanFilter>1 AND 2</booleanFilter>
        <errorMessage>Choose a contact on this contract's account who has not opted out of email.</errorMessage>
        <filterItems>
            <field>Contact.AccountId</field>
            <operation>equals</operation>
            <valueField>$Source.Account__c</valueField>
        </filterItems>
        <filterItems>
            <field>Contact.HasOptedOutOfEmail</field>
            <operation>equals</operation>
            <value>false</value>
        </filterItems>
        <infoMessage>Only contacts on this account who accept email are shown.</infoMessage>
        <isOptional>false</isOptional>
    </lookupFilter>
    <referenceTo>Contact</referenceTo>
    <relationshipLabel>Billing Contracts</relationshipLabel>
    <relationshipName>Billing_Contracts</relationshipName>
    <required>false</required>
    <trackFeedHistory>false</trackFeedHistory>
    <trackHistory>false</trackHistory>
    <type>Lookup</type>
</CustomField>
```

> UNVERIFIED (2026-09-04): the guide documents `valueField` only by purpose, not its syntax. The `$Source.` form above matches `admin/lookup-filter-cross-object-patterns`, which owns lookup filters; retrieve a working filter from your org and copy its exact form before deploying.

How to read it:

- `deleteConstraint` is the element most field XML omits, and omitting it is a decision. The three
  values, verbatim (api_meta.txt:43348–43356): `Cascade` — "Deletes the lookup record as well as
  associated lookup fields"; `Restrict` — "Prevents the record from being deleted if it's in a
  lookup relationship"; `SetNull` — "This value is the default. If the lookup record is deleted, the
  lookup field is cleared." A silent `SetNull` is how a parent delete quietly blanks a field that
  automation depends on.
- `referenceTo` names the parent object (api_meta.txt:43574). `relationshipName` is what child
  records are called from the parent side and is what a subquery uses:
  `SELECT Id, (SELECT Id FROM Billing_Contracts__r) FROM Contact`. Metadata carries it without the
  `__r`; SOQL adds it.
- `lookupFilter` inlines the whole filter. `active` and `isOptional` are both required booleans, and
  `filterItems` allows "up to 10 FilterItems per lookup filter" (api_meta.txt:43883–43884).
- `value` and `valueField` are alternatives, not both: `valueField` "specifies if the final column
  in the filter contains a field or a field value" (api_meta.txt:43922–43924). The first filter item
  above compares two fields; the second compares a field to a literal.
- `isOptional` `false` makes the filter mandatory — users cannot clear it in the lookup dialog. For
  the design decision behind optional vs required filters and cross-object criteria, read
  `admin/lookup-filter-cross-object-patterns`; it is not repeated here.
- `FilterOperation` enum values (api_meta.txt:43903–43916): `equals`, `notEqual`, `lessThan`,
  `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`,
  `includes`, `excludes`, `within`.

---

## 6. Master-detail on a junction object

`objects/Contract_Product__c/fields/Contract__c.field-meta.xml` — the **primary** master of a
junction object joining `Contract__c` and `Product2`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Contract__c</fullName>
    <description>Primary master. Junction row inherits Contract ownership, sharing, and look and feel. Reparenting allowed so a mis-keyed line can be moved without a delete/recreate cycle.</description>
    <externalId>false</externalId>
    <inlineHelpText>The contract this product line belongs to. Changing it moves the line, and its ownership, to the new contract.</inlineHelpText>
    <label>Contract</label>
    <referenceTo>Contract__c</referenceTo>
    <relationshipLabel>Contract Products</relationshipLabel>
    <relationshipName>Contract_Products</relationshipName>
    <relationshipOrder>0</relationshipOrder>
    <reparentableMasterDetail>true</reparentableMasterDetail>
    <trackFeedHistory>false</trackFeedHistory>
    <trackHistory>false</trackHistory>
    <type>MasterDetail</type>
    <writeRequiresMasterRead>false</writeRequiresMasterRead>
</CustomField>
```

The second master, `objects/Contract_Product__c/fields/Product__c.field-meta.xml`, is identical in
shape with `<relationshipOrder>1</relationshipOrder>` and `<referenceTo>Product2</referenceTo>`.

How to read it:

- `relationshipOrder` only matters on junction objects: "A junction object has two master-detail
  relationships… Junction objects must define one parent object as primary (0), the other as
  secondary (1). The definition of primary or secondary affects delete behavior and inheritance of
  look and feel, and record ownership for junction objects. 0 or 1 are the only valid values, and 0
  is always the value for objects that aren't junction objects" (api_meta.txt:43582–43592). A
  junction with `0` on both fields, or `0` on neither, is a deploy error waiting to happen — and if
  it deploys, ownership follows the wrong parent.
- There is no `required` element on a `MasterDetail` field. The parent is structurally mandatory.
- `reparentableMasterDetail` "indicates whether the child records in a master-detail relationship on
  a custom object can be reparented to different parent records. The default value is false"
  (api_meta.txt:43593–43597). Leaving it at the default means a mis-keyed parent can only be fixed
  by deleting and recreating the child, which loses its Id, its history, and anything pointing at it.
- `writeRequiresMasterRead` `false` is the documented default and the more restrictive setting:
  `true` "allows users with Read access to the primary record permission to create, edit, or delete
  child records… `false` allows users with Read/Write access… and is the default value"
  (api_meta.txt:43725–43742). On a junction, "the most restrictive access from the two parents is
  enforced" (api_meta.txt:43738–43742), so setting `true` on one field alone changes nothing.
- Relationship choice — Lookup vs Master-Detail vs junction, and when to convert — belongs to
  `admin/lookup-and-relationship-design`. This file only shows the XML shape.

---

## 7. Restricted picklist with an inline value set

`objects/Contract__c/fields/Renewal_Risk__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Renewal_Risk__c</fullName>
    <description>Renewal risk band set by the CSM at each QBR. Restricted so the API cannot introduce a fourth value that dashboards do not group.</description>
    <externalId>false</externalId>
    <inlineHelpText>Your assessment of renewal risk as of the most recent QBR.</inlineHelpText>
    <label>Renewal Risk</label>
    <required>false</required>
    <trackFeedHistory>false</trackFeedHistory>
    <trackHistory>true</trackHistory>
    <type>Picklist</type>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Low</fullName>
                <default>true</default>
                <label>Low</label>
            </value>
            <value>
                <fullName>Medium</fullName>
                <default>false</default>
                <label>Medium</label>
            </value>
            <value>
                <fullName>High</fullName>
                <default>false</default>
                <label>High</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

How to read it:

- `restricted` is "whether the picklist's values are limited to only the values defined by a
  Salesforce admin" (api_meta.txt:45847–45849). Unrestricted is the permissive state: the API and
  data loads can write values that are not in the set. The guide's gloss on the equivalent flag is
  explicit — with a restricted picklist "only an admin can add or change values; users can't load or
  remove values through the API" (api_meta.txt:44696–44699).
- `sorted` `false` keeps the business order (`Low`, `Medium`, `High`). `true` alphabetises in the UI
  (api_meta.txt:45864–45866), which for a risk band is wrong: `High`, `Low`, `Medium`.
- Each `value` is a `CustomValue`. `default` is required, `label` "defaults to the API name" if
  omitted, and `isActive` defaults to `true` (api_meta.txt:47513–47529). `fullName` is the API value
  that reports, Flows, and Apex compare against — the `label` can change later, `fullName` should not.
- **Use a global value set instead** when the same values appear on more than one object. Then
  `valueSet` carries `valueSetName` (the global set's `masterLabel`) rather than a
  `valueSetDefinition`, and "a ValueSet component has either a valueSetDefinition or a valueName
  specified, but never both" (api_meta.txt:43710–43713). Global value sets, dependent picklists, and
  value deactivation are `admin/picklist-and-value-sets` and
  `admin/field-dependency-and-controlling`; do not design them from this file.

---

## 8. Data-classification elements — set them at creation, not in a later cleanup

Any of the examples above can carry these three. They are metadata-only and cost nothing to deploy.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: the classification elements only, shown on the Account external-ID field from §2. -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>ERP_Account_Code__c</fullName>
    <businessStatus>Active</businessStatus>
    <complianceGroup>PII</complianceGroup>
    <label>ERP Account Code</label>
    <securityClassification>Internal</securityClassification>
    <type>Text</type>
</CustomField>
```

- `securityClassification` — `Public`, `Internal`, `Confidential`, `Restricted`, `MissionCritical`
  (api_meta.txt:43614–43622, v45.0+).
- `complianceGroup` — `CCPA`, `COPPA`, `GDPR`, `HIPAA`, `PCI`, `PII` (api_meta.txt:43334–43345,
  v47.0+). It is a multipicklist, so several `<complianceGroup>` semantics apply per the API version
  in use.
- `businessStatus` — `Active`, `DeprecateCandidate`, `Hidden` (api_meta.txt:43313–43320, v45.0+).
  `DeprecateCandidate` is the honest way to mark a field on its way out without deleting it.

---

## 9. The permission set that actually exposes the field

Creating the field grants nobody access. FLS lives in a `PermissionSet` (or `Profile`) component,
deployed alongside.

`permissionsets/Contract_Manager.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: only the fieldPermissions entries for the fields created above. -->
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Contract Manager</label>
    <fieldPermissions>
        <editable>false</editable>
        <field>Account.ERP_Account_Code__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Contract__c.Renewal_Risk__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Contract__c.Annual_Value__c</field>
        <readable>true</readable>
    </fieldPermissions>
</PermissionSet>
```

How to read it:

- `field` is "the API name of the field (such as `Warehouse__c.Description__c`)" — always
  object-qualified (api_meta.txt:95043–95047). `editable` is required; `readable` is not, but
  `editable` `true` with `readable` `false` is a nonsense state — write both.
- `Contract_Number__c` from §1 is deliberately **absent**: it is `required` `true`, and "in API
  version 30.0 and later, permissions for required fields can't be retrieved or deployed"
  (api_meta.txt:95020–95021). Including it fails the deploy; the platform grants access to required
  fields implicitly.
- Retrieving the field rewrites this file whether you meant it to or not: "Retrieving a component of
  this metadata type in a project makes the component appear in any Profile and PermissionSet
  components that are retrieved in the same package" (api_meta.txt:43251–43252). Diff permission
  sets after every field retrieve.
- `viewAllFields` on an `objectPermissions` entry suppresses the individual rows: "If the View All
  Fields object permission is enabled for an object in the permission set, the individual fields
  aren't returned under fieldPermissions" (api_meta.txt:95027–95029). An empty `fieldPermissions`
  list is therefore not proof that nobody can read the field.
- Permission set *design* — which sets exist, how they group, muting — is
  `admin/permission-set-architecture`.

---

## 10. `package.xml` — `CustomField` has no wildcard

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.ERP_Account_Code__c</members>
        <members>Contract__c.Annual_Value__c</members>
        <members>Contract__c.Auto_Renew__c</members>
        <members>Contract__c.Billing_Contact__c</members>
        <members>Contract__c.Contract_Expiry_Date__c</members>
        <members>Contract__c.Contract_Number__c</members>
        <members>Contract__c.Renewal_Risk__c</members>
        <members>Contract_Product__c.Contract__c</members>
        <members>Contract_Product__c.Product__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Contract_Manager</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Contract__c-Contract Layout</members>
        <name>Layout</name>
    </types>
    <version>62.0</version>
</Package>
```

- Every member is `Object.Field__c`, matching the guide's manifest example
  (api_meta.txt:43261–43266).
- `<members>*</members>` does not work here: "This metadata type doesn't support the wildcard
  character `*` (asterisk) in the package.xml manifest file" (api_meta.txt:43983–43985). To get
  every field on an object, request the `CustomObject` instead — "when you retrieve a custom or
  standard object, you return everything associated with the object, except for standard fields that
  aren't customizable" (api_meta.txt:43256–43257).
- The `PermissionSet` and `Layout` entries are not optional extras. A field deployed without them
  exists and is invisible.

---

## 11. Retrieve and deploy

```bash
# Retrieve the fields plus the permission set that grants them, into the DX project.
# CustomField has no wildcard, so name each field.
sf project retrieve start \
  --metadata "CustomField:Contract__c.Renewal_Risk__c" \
  --metadata "CustomField:Account.ERP_Account_Code__c" \
  --metadata "PermissionSet:Contract_Manager" \
  --target-org my-sandbox

# Or retrieve the whole object when you want every field on it.
sf project retrieve start --metadata "CustomObject:Contract__c" --target-org my-sandbox

# Validate against production without saving anything. --dry-run is the gate before any prod deploy.
sf project deploy start \
  --source-dir force-app/main/default/objects/Contract__c \
  --source-dir force-app/main/default/permissionsets/Contract_Manager.permissionset-meta.xml \
  --dry-run \
  --target-org production

# Deploy for real once the dry run is clean.
sf project deploy start \
  --source-dir force-app/main/default/objects/Contract__c \
  --source-dir force-app/main/default/permissionsets/Contract_Manager.permissionset-meta.xml \
  --target-org production
```

Flag spellings verified against `sf project retrieve start --help`, `sf project deploy start
--help`, and `sf sobject describe --help` on `@salesforce/cli` 2.149.9 (2026-09-04). `--target-org`
is required unless the `target-org` config variable is set.

After the retrieve, `git diff` the permission sets before committing — the retrieve rewrote them
(§9).

---

## 12. Verification

Confirm what the org actually has, not what you think you deployed.

```bash
# Field shape as the platform sees it: type, length, precision/scale, unique, externalId, defaults.
sf sobject describe --sobject Account --target-org my-sandbox --json \
  | jq '.result.fields[] | select(.name == "ERP_Account_Code__c")
        | {name, type, length, precision, scale, unique, externalId, caseSensitive, nillable, createable, updateable, inlineHelpText}'
```

The `jq` path assumes the CLI wraps its payload under `.result`, which is the shape
`sf ... --json` emits. UNVERIFIED (2026-09-04): the exact envelope key was not confirmed against a
live org in this session — if the filter returns nothing, drop `.result` and use `.fields[]`.

`FieldDefinition` is a Tooling API object and is **not** in the Object Reference, so there is no
plain SOQL query that lists field metadata from a standard session. Use the describe above, or add
`--use-tooling-api` to `sf sobject describe` for Tooling objects. What SOQL *can* verify is that the
FLS deploy worked, because `FieldPermissions` is a queryable setup object:

```sql
SELECT Parent.Label, Field, PermissionsRead, PermissionsEdit
FROM FieldPermissions
WHERE SobjectType = 'Contract__c'
  AND Field = 'Contract__c.Renewal_Risk__c'
```

An empty result means no permission set grants the field — which is exactly the state a field is in
the moment after it is created. UNVERIFIED (2026-09-04): `FieldPermissions` is not documented in the
extracted Object Reference text; the query shape follows the `PermissionSetFieldPermissions`
metadata subtype (api_meta.txt:95019–95047). Run it in a sandbox before relying on it in a runbook.

In Apex, `Schema.DescribeFieldResult` answers the same questions and is the check to embed in a
post-deploy script:

```apex
Schema.DescribeFieldResult dfr = Account.ERP_Account_Code__c.getDescribe();

System.debug('type       : ' + dfr.getType());          // Schema.DisplayType
System.debug('length     : ' + dfr.getLength());        // max size in Unicode characters
System.debug('unique     : ' + dfr.isUnique());         // true if the value must be unique
System.debug('externalId : ' + dfr.isExternalID());     // true if used as an external ID
System.debug('caseSens.  : ' + dfr.isCaseSensitive());  // true if ACME01 != acme01
System.debug('helpText   : ' + dfr.getInlineHelpText());

// FLS as the RUNNING user sees it - this is the assertion that catches a missing permission set.
System.assert(dfr.isAccessible(), 'Running user has no FLS read on ERP_Account_Code__c');
```

Method names and semantics from the Apex Reference Guide, *DescribeFieldResult Class*
(apexrefguide.txt:190513–191460): `getLength()` "returns the maximum size of the field… in Unicode
characters (not bytes)" (190806–190811), `isAccessible()` "returns true if the current user can see
this field" (191030–191035), `isUnique()` (191422–191427), `isExternalID()` (191211–191216),
`isCaseSensitive()` (191108–191113), `getInlineHelpText()` (190764–190769).

Then run the skill's checker over the source tree:

```bash
python3 skills/admin/custom-field-creation/scripts/check_custom_field_creation.py \
  --manifest-dir force-app/main/default
```

---

## Sources

- Metadata API Developer Guide — *CustomField*, *LookupFilter*, *FilterItem*, *ValueSet*,
  *CustomValue*, *PermissionSetFieldPermissions*, *Metadata Field Types*:
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- REST API Developer Guide — upsert by external ID, HTTP 300 on multiple matches:
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Bulk API 2.0 Developer Guide — external ID indexing and relationship CSV headers:
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf
- Apex Reference Guide — *DescribeFieldResult Class*:
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexrefguide.pdf
