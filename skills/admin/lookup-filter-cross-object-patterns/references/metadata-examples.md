# Metadata Examples — Lookup Filter Cross Object Patterns

A lookup filter has no file of its own. It is the `lookupFilter` element of the lookup field's
`CustomField` component: "the metadata associated with a lookup filter is now represented by the
lookupFilter field in the CustomField component" (api_meta.txt:44513–44514). The standalone
`NamedFilter` type that used to hold it was removed in API version 30.0 (api_meta.txt:43860–43862,
44529–44530).

For every other element of a `CustomField` — `type`, `referenceTo`, `deleteConstraint`,
`relationshipName`, history tracking, compliance metadata — read
`admin/custom-field-creation` → `references/metadata-examples.md`. Nothing below repeats it.

## Where the file lives

| Form | Path | Root element |
|---|---|---|
| DX source format | `objects/Case/fields/ContactId.field-meta.xml` | `CustomField` |
| Metadata API zip | `objects/Case.object` — each field is a `<fields>` entry | `CustomObject` |

Standard fields carry filters exactly like custom ones; the DX file is named for the standard field
API name (`ContactId`, not `ContactId__c`). `LookupFilter` "isn't supported on the article type
object" (api_meta.txt:43500).

## The `$Source` prefix

Every `valueField` below uses the `$Source.` prefix to name a value on the record being edited.

> UNVERIFIED (2026-09-04): the Metadata API Developer Guide defines `valueField` only by purpose —
> it "specifies if the final column in the filter contains a field or a field value"
> (api_meta.txt:43922–43924) — and never documents the `$Source.` grammar or its traversal depth.
> The nearest documented relative is the removed `NamedFilter` type's `sourceObject` field, "the
> object that contains the lookup field that uses this lookup filter. Set this field if the lookup
> filter references fields on the source object" (api_meta.txt:44580–44583). Before shipping a
> hand-written filter, build one equivalent filter in a sandbox through Setup, retrieve it, and copy
> the literal `valueField` string the platform emits.

---

## 1. Required cross-object filter: Case contact must be on the case's account

`objects/Case/fields/ContactId.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>ContactId</fullName>
    <lookupFilter>
        <active>true</active>
        <description>Support reps must pick a contact who belongs to the account already on the case. Prevents a case being shared with a contact from an unrelated account.</description>
        <errorMessage>Choose a contact who belongs to the account on this case. If the right person is missing, add them to the account first.</errorMessage>
        <filterItems>
            <field>Contact.AccountId</field>
            <operation>equals</operation>
            <valueField>$Source.AccountId</valueField>
        </filterItems>
        <infoMessage>Only contacts on this case's account are shown.</infoMessage>
        <isOptional>false</isOptional>
    </lookupFilter>
</CustomField>
```

How to read it:

- `active` and `isOptional` are both "Required" booleans (api_meta.txt:43865–43866, 43890–43891).
  `active` `false` keeps the definition in source while switching it off; `isOptional` `false` is what
  makes the filter enforcing rather than advisory.
- The left side, `Contact.AccountId`, is a field on the object the lookup points *at*. The right
  side is a `valueField`, not a `value` — that is the difference between a cross-object filter and a
  static one.
- Never set both `value` and `valueField` on one item. `valueField` decides "if the final column in
  the filter contains a field or a field value" (api_meta.txt:43922–43924); supplying both leaves the
  comparison ambiguous.
- `errorMessage` is what the user reads when the save is rejected; `infoMessage` is what they read on
  the page describing "why certain items are excluded in the lookup filter"
  (api_meta.txt:43886–43888). A required filter with no `errorMessage` fails silently from the user's
  point of view.
- This file is a fragment of the field, not the whole field. A real `ContactId.field-meta.xml` also
  carries the elements `admin/custom-field-creation` documents.

---

## 2. Optional filter that explains itself

`objects/Opportunity/fields/Account_Manager__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Account_Manager__c</fullName>
    <label>Account Manager</label>
    <lookupFilter>
        <active>true</active>
        <description>Advisory only during the territory rollout. Shows in-region active users first but does not block an out-of-region assignment.</description>
        <filterItems>
            <field>User.IsActive</field>
            <operation>equals</operation>
            <value>true</value>
        </filterItems>
        <filterItems>
            <field>User.Region__c</field>
            <operation>equals</operation>
            <valueField>$Source.Region__c</valueField>
        </filterItems>
        <booleanFilter>1 AND 2</booleanFilter>
        <infoMessage>Showing active users in this opportunity's region. Clear the filter in the lookup dialog if you need someone outside the region.</infoMessage>
        <isOptional>true</isOptional>
    </lookupFilter>
    <referenceTo>User</referenceTo>
    <relationshipLabel>Managed Opportunities</relationshipLabel>
    <relationshipName>Managed_Opportunities</relationshipName>
    <type>Lookup</type>
</CustomField>
```

How to read it:

- `isOptional` `true` is the whole difference from §1. There is no `errorMessage` because nothing is
  rejected — an optional filter has no failure to report.
- `infoMessage` is doing the real work here. Without it, the user sees a shortened list and no
  explanation, which reads as a broken picker.
- The first item compares against a literal (`value`), the second against a field on the source
  record (`valueField`). One filter can mix both freely.

---

## 3. Filter on the target's status and record type

`objects/Contract__c/fields/Billing_Account__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Billing_Account__c</fullName>
    <label>Billing Account</label>
    <lookupFilter>
        <active>true</active>
        <description>Only a customer-record-type account that is not on billing hold can be invoiced.</description>
        <errorMessage>This account is either not a Customer account or is on billing hold, so it cannot be the billing account for a contract.</errorMessage>
        <filterItems>
            <field>Account.RecordType.DeveloperName</field>
            <operation>equals</operation>
            <value>Customer</value>
        </filterItems>
        <filterItems>
            <field>Account.Billing_Hold__c</field>
            <operation>notEqual</operation>
            <value>true</value>
        </filterItems>
        <booleanFilter>1 AND 2</booleanFilter>
        <isOptional>false</isOptional>
    </lookupFilter>
    <referenceTo>Account</referenceTo>
    <type>Lookup</type>
</CustomField>
```

How to read it:

- Both items compare a target field against a literal, so this is a *static* filter — no `$Source`
  anywhere. Static filters are the ones most safely hand-written, because they depend on nothing
  outside the target object.
- UNVERIFIED (2026-09-04): `Account.RecordType.DeveloperName` as a filter `field` is not documented
  in the Metadata API Developer Guide's `FilterItem` table (api_meta.txt:43897–43924), which says only
  that `field` "represents the field specified in the filter". If a deploy rejects it, replace it with
  a checkbox or formula field on the target object that resolves the record type, and filter on that
  instead. `admin/formula-fields` covers the flattening field.
- `notEqual` against `true` and `equals` against `false` are not the same on a nullable field. Both
  operations are in the enum (api_meta.txt:43903–43916); pick the one that matches how the field is
  populated.

---

## 4. Dependent lookup driven by a field on the same record

`objects/Work_Request__c/fields/Territory__c.field-meta.xml` — the source record's own
`Region__c` decides which territories are selectable, which is the lookup equivalent of a
controlling picklist.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Territory__c</fullName>
    <label>Territory</label>
    <lookupFilter>
        <active>true</active>
        <description>Territory choices depend on the Region field on this same record. Changing Region invalidates a previously chosen Territory.</description>
        <errorMessage>This territory is not in the region selected on this record. Change Region first, or pick a territory inside it.</errorMessage>
        <filterItems>
            <field>Territory__c.Region__c</field>
            <operation>equals</operation>
            <valueField>$Source.Region__c</valueField>
        </filterItems>
        <infoMessage>Territories are limited to the region on this record.</infoMessage>
        <isOptional>false</isOptional>
    </lookupFilter>
    <referenceTo>Territory__c</referenceTo>
    <type>Lookup</type>
</CustomField>
```

How to read it:

- This is a *same-record* dependency, not a cross-object one: the constraining value lives on the
  record being edited, so `valueField` needs no traversal at all.
- It is not the same mechanism as a dependent picklist. A dependent picklist uses
  `controllingField` on the `valueSet` and is covered by `admin/field-dependency-and-controlling`;
  a dependent lookup is an ordinary `filterItem` whose right-hand side happens to be a field on the
  same record.
- When the controlling field is a picklist on a standard object, the stored value may not be the
  label. The Object Reference documents exactly this for Field Service: "To create a dependent lookup
  filter with ServiceResource.ResourceType, use only the first letter of the picklist value, for
  example T for Technician" (object_reference.txt:259743–259744). Check the stored value, not the
  label, for any standard restricted picklist.

---

## 5. Three conditions under one `booleanFilter`

`objects/Project__c/fields/Reviewer__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Reviewer__c</fullName>
    <label>Reviewer</label>
    <lookupFilter>
        <active>true</active>
        <booleanFilter>1 AND (2 OR 3)</booleanFilter>
        <description>Reviewer must be active, and either in the project's business unit or flagged as a global reviewer. Item 3 is the deliberate exemption, since LookupFilter has no bypass element.</description>
        <errorMessage>Pick an active reviewer from this project's business unit, or one approved to review globally.</errorMessage>
        <filterItems>
            <field>User.IsActive</field>
            <operation>equals</operation>
            <value>true</value>
        </filterItems>
        <filterItems>
            <field>User.Business_Unit__c</field>
            <operation>equals</operation>
            <valueField>$Source.Business_Unit__c</valueField>
        </filterItems>
        <filterItems>
            <field>User.Global_Reviewer__c</field>
            <operation>equals</operation>
            <value>true</value>
        </filterItems>
        <infoMessage>Active reviewers in this business unit, plus anyone approved to review globally.</infoMessage>
        <isOptional>false</isOptional>
    </lookupFilter>
    <referenceTo>User</referenceTo>
    <type>Lookup</type>
</CustomField>
```

How to read it:

- `booleanFilter` "specifies advanced filter conditions" (api_meta.txt:43868) and numbers the
  `filterItems` **positionally, in document order**. `1 AND (2 OR 3)` binds to whichever items sit in
  positions 1, 2, and 3 of this file — rename nothing, reorder nothing, without rewriting the string.
- The cap is "up to 10 FilterItems per lookup filter" (api_meta.txt:43883–43884). A design that wants
  an eleventh condition needs a formula field on the target that collapses two of them.
- Item 3 is how an exemption is expressed. `LookupFilter` has seven fields and none of them is a
  bypass (api_meta.txt:43864–43891), so "let the migration user through" has to be a real filter
  condition that survives code review.

---

## 6. Translating the messages

`errorMessage` and `infoMessage` are English strings inside the field. Their translations live in a
different component: `CustomObjectTranslation` carries a `lookupFilter` of type
`LookupFilterTranslation`, whose two fields are `errorMessage` and `informationalMessage`
(api_meta.txt:46011–46014, 46075–46087).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Case-fr.objectTranslation-meta.xml — excerpt: the fields entry for ContactId only -->
<CustomObjectTranslation xmlns="http://soap.sforce.com/2006/04/metadata">
    <fields>
        <name>ContactId</name>
        <lookupFilter>
            <errorMessage>Choisissez un contact appartenant au compte de ce ticket.</errorMessage>
            <informationalMessage>Seuls les contacts du compte de ce ticket sont affichés.</informationalMessage>
        </lookupFilter>
    </fields>
</CustomObjectTranslation>
```

How to read it:

- The translation element is named `informationalMessage`, not `infoMessage`. The two components use
  different names for the same string (api_meta.txt:43886, 46083).
- `name` here is "the name of the field relative to the custom object; for example, MyField__c"
  (api_meta.txt:46016–46017) — bare, not object-qualified.
- Deploying the field without the object translation leaves non-English users reading the English
  message. Add the `CustomObjectTranslation` members to the same `package.xml`.

---

## 7. Finding records that already violate the filter

Run this **before** setting `isOptional` to `false`. A required filter constrains what can be saved
next; it does not go back and re-check what is already stored.

```sql
-- Cases whose contact belongs to a different account than the case itself.
-- Non-zero result = a backfill task, not a rounding error.
SELECT COUNT()
FROM Case
WHERE ContactId != NULL
  AND AccountId != NULL
  AND Contact.AccountId != AccountId
```

```sql
-- The same rows, listed, for the backfill file. Add LIMIT and ORDER BY Id
-- and page with Id > :lastId on a large object.
SELECT Id, CaseNumber, AccountId, ContactId, Contact.AccountId, Contact.Name
FROM Case
WHERE ContactId != NULL
  AND AccountId != NULL
  AND Contact.AccountId != AccountId
ORDER BY Id
```

Feed the second query's output to the load path in `data/data-loader-and-tools`. If the object is
large enough that the count itself times out, `data/soql-query-optimization` covers the selective
filter and index work.

---

## 8. Verifying the deployed filter from Apex

```apex
// Verification only - run in Anonymous Apex or a scratch-org test.
Schema.DescribeFieldResult f = Case.ContactId.getDescribe();
System.debug('Field: '        + f.getName());
System.debug('Points at: '    + f.getReferenceTo());
System.debug('Relationship: ' + f.getRelationshipName());

// UNVERIFIED (2026-09-04): getFilteredLookupInfo() and Schema.FilteredLookupInfo
// (isOptionalFilter / isDependent / getControllingFields) do not appear anywhere in the
// fetched Apex Reference Guide's DescribeFieldResult method list (apexrefguide.txt:190542-190740),
// so this block may not compile on your API version. If it does not, delete it and verify the
// filter by retrieving the field metadata (section 9) instead - that check is grounded and exact.
Schema.FilteredLookupInfo info = f.getFilteredLookupInfo();
if (info != null) {
    System.debug('Optional filter: ' + info.isOptionalFilter());
    System.debug('Dependent: '       + info.isDependent());
    System.debug('Controlled by: '   + info.getControllingFields());
}
```

The grounded methods above — `getReferenceTo()` "returns a list of Schema.sObjectType objects for the
parent objects of this field" and `getRelationshipName()` "returns the name of the child-to-parent
relationship" (apexrefguide.txt:190586–190590) — confirm the lookup's target, which is what the left
side of every `filterItem` must name. They do not report the filter itself.

---

## 9. `package.xml`, retrieve, and deploy

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case.ContactId</members>
        <members>Opportunity.Account_Manager__c</members>
        <members>Project__c.Reviewer__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Case-fr</members>
        <name>CustomObjectTranslation</name>
    </types>
    <version>62.0</version>
</Package>
```

`CustomField` members are object-qualified (`Case.ContactId`). The `CustomField` type "doesn't
support the wildcard character * (asterisk) in the package.xml manifest file"
(api_meta.txt:43983–43985), so every field is listed by name.

```bash
# Pull the field (and its filter) out of a sandbox that already has one working,
# so you can copy the literal valueField syntax the platform emits.
sf project retrieve start \
  --metadata "CustomField:Case.ContactId" \
  --target-org my-sandbox

# Whole-package round trip
sf project retrieve start --manifest manifest/package.xml --target-org my-sandbox

# Validate without committing, running the tests the org requires
sf project deploy start \
  --manifest manifest/package.xml \
  --target-org my-sandbox \
  --dry-run

# Deploy for real
sf project deploy start \
  --manifest manifest/package.xml \
  --target-org my-sandbox
```

Verification, in this order:

1. `sf project deploy start --dry-run` returns success — the filter is syntactically valid and every
   field it names exists in the target org.
2. Run the §7 count query. It must be zero before you set `isOptional` to `false`.
3. Open the record in the UI **as a non-admin user on a real profile** and click into the lookup.
   The list must be narrowed and the `infoMessage` must be visible. An empty list means a field in the
   filter is not readable by that profile, not that no records qualify — see `references/gotchas.md`.
4. Save an intentionally invalid value through the API or Data Loader and confirm the `errorMessage`
   text comes back.
5. `python3 skills/admin/lookup-filter-cross-object-patterns/scripts/check_lookup_filter_cross_object_patterns.py --manifest-dir force-app/main/default`
   returns no findings.
