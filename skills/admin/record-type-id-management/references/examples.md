# Examples — Record Type Id Management

## Example 1: Replacing hard-coded record-type IDs with a cached resolver

**Context:** A five-year-old org has `012` string literals scattered across trigger handlers, batch classes, and an `@AuraEnabled` controller. The record types were deployed into a new org, which generated its own Ids (an Id is "unique within your org's data", obj 264 L2290), and the nightly batch is failing there.

**Problem:** Record-type Ids are org-specific. The literal that resolved in the source org resolves to nothing in the new org, so branch conditions silently fall through instead of erroring — the batch "succeeds" while stamping the wrong record type on 40,000 rows.

**Solution:**

```apex
/**
 * RecordTypes — DeveloperName -> Id resolution with a transaction-local cache.
 * Fails loudly when a DeveloperName is not deployed, so a bad reference is a
 * deployment error rather than a silent null.
 */
public with sharing class RecordTypes {

    private static final Map<String, Id> CACHE = new Map<String, Id>();

    public static Id idFor(Schema.SObjectType token, String developerName) {
        String key = String.valueOf(token) + '.' + developerName;
        if (CACHE.containsKey(key)) {
            return CACHE.get(key);
        }
        Schema.RecordTypeInfo rti = token.getDescribe()
            .getRecordTypeInfosByDeveloperName()
            .get(developerName);
        if (rti == null) {
            throw new IllegalArgumentException(
                'No record type ' + developerName + ' on ' + token);
        }
        CACHE.put(key, rti.getRecordTypeId());
        return CACHE.get(key);
    }

    /** Only record types the running user may actually select. */
    public static List<Schema.RecordTypeInfo> selectableFor(Schema.SObjectType token) {
        List<Schema.RecordTypeInfo> out = new List<Schema.RecordTypeInfo>();
        for (Schema.RecordTypeInfo rti : token.getDescribe().getRecordTypeInfos()) {
            if (rti.isAvailable() && rti.isActive() && !rti.isMaster()) {
                out.add(rti);
            }
        }
        return out;
    }
}
```

Call sites become `RecordTypes.idFor(Account.SObjectType, 'Business_Account')`.

**Why it works:** The Id is derived at runtime from the DeveloperName, the API name the deploy carries as the component's `fullName` (api_meta 264 L47382; obj 264 L246998). `selectableFor` applies the filters the describe maps do not apply for you — `isAvailable()`, documented as "Returns true if this record type is available to the current user" (apexref 262 L193867), and `isActive()` — because `getRecordTypeInfos*` includes record types the running user cannot access (apexref 262 L192544).

---

## Example 2: Record-type metadata and matching declarative references

**Context:** A new `Bulk_Orders` record type on Opportunity, deployed via source format, referenced from a validation rule.

**Problem:** Hand-authored `RecordType` files commonly object-prefix the `businessProcess` value, and validation rules commonly compare `RecordTypeId` to a literal — the first breaks the deploy, the second breaks in any org with a different Id.

**Solution:**

`force-app/main/default/objects/Opportunity/recordTypes/Bulk_Orders.recordType-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<RecordType xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Bulk_Orders</fullName>
    <active>true</active>
    <businessProcess>Bulk Sales Process</businessProcess>
    <description>High-volume reseller orders. Skips the discount approval path.</description>
    <label>Bulk Orders</label>
    <picklistValues>
        <picklist>StageName</picklist>
        <values>
            <fullName>Qualification</fullName>
            <default>true</default>
        </values>
        <values>
            <fullName>Negotiation</fullName>
            <default>false</default>
        </values>
    </picklistValues>
</RecordType>
```

The matching validation rule, in `objects/Opportunity/validationRules/Bulk_Orders_Require_Quantity.validationRule-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Bulk_Orders_Require_Quantity</fullName>
    <active>true</active>
    <errorConditionFormula>AND(
  $RecordType.DeveloperName = &quot;Bulk_Orders&quot;,
  ISBLANK(Quantity__c)
)</errorConditionFormula>
    <errorDisplayField>Quantity__c</errorDisplayField>
    <errorMessage>Bulk orders require a quantity.</errorMessage>
</ValidationRule>
```

And the `package.xml` member — the one place the object prefix *is* required:

```xml
<types>
    <members>Opportunity.Bulk_Orders</members>
    <name>RecordType</name>
</types>
```

**Why it works:** `businessProcess` is the bare process name, as the guide requires for Opportunity record types ("As the record type is already defined within the object, don't prefix the object name", api_meta 264 L47367-47373), and the `package.xml` member is object-qualified, as in the guide's sample `<members>Opportunity.Test_Record_Type</members>` (api_meta 264 L97295). The bare `<fullName>Bulk_Orders</fullName>` matches the guide's declarative sample, where a record type defined inside its object carries `<fullName>My_First_Recordtype</fullName>` (api_meta 264 L47474); the guide's Java API sample, by contrast, sets an object-qualified `fullName` (`ExpenseReport__c.Edit`, api_meta 264 L47429). The validation rule compares `$RecordType.DeveloperName` (UNVERIFIED, Help-only merge field) to a string, so it carries no Id; a `RecordTypeId = "012..."` comparison would not survive an org with a different Id. Retrieve the record type from an org rather than hand-authoring the `picklistValues` block: the encoding Salesforce uses for picklist `fullName` values inside record-type metadata is not documented on this page, and guessing it is how multi-word picklist entries turn into deploy failures.

---

## Anti-Pattern: `[SELECT Id FROM RecordType WHERE Name = '...']` inside a loop

**What practitioners do:** Resolve the record type with a SOQL query against the `RecordType` object, usually filtered on `Name`, often inside a `for` loop over trigger records.

**What goes wrong:** Two failures at once. The query counts against the 100 SOQL queries per synchronous transaction (apexdev 264 L19747), so a loop over a 200-record trigger exceeds it. And `Name` is the record type's UI label (obj 264 L247039); when the filter matches no row, assigning the result to a single sObject throws a QueryException, "List has no rows for assignment to SObject" (apexdev 264 L40308-40312). UNVERIFIED (2026-10-21): that a `Name` filter matches the translated label for users in another language.

**Correct approach:** Resolve through `Schema` describe, which is a method call rather than a SOQL query, and key on DeveloperName. If you genuinely need the `RecordType` sObject (for example to read a custom description into a UI), query it once outside the loop into a `Map<String, RecordType>` keyed by `DeveloperName`, and filter `WHERE SobjectType = 'Account' AND IsActive = true`.
