# Examples — Apex Schema Describe

## Example 1 — Per-record describe in a trigger

**Wrong code.**

```apex
for (Account a : Trigger.new) {
    Schema.DescribeFieldResult dfr = Schema.getGlobalDescribe()
        .get('Account').getDescribe().fields.getMap().get('Name').getDescribe();
    if (!dfr.isAccessible()) continue;
    a.Name = a.Name?.toUpperCase();
}
```

**Why wrong.** `getGlobalDescribe()` + nested `getDescribe()` runs
PER record. 200-record batch = 200 global describes.

**Right code.**

```apex
private static final Boolean NAME_ACCESSIBLE = Account.Name.getDescribe().isAccessible();

for (Account a : Trigger.new) {
    if (NAME_ACCESSIBLE) {
        a.Name = a.Name?.toUpperCase();
    }
}
```

`static final` runs once at class load.

---

## Example 2 — Bulk FLS strip

**Wrong code.**

```apex
for (Account a : records) {
    if (Account.SSN__c.getDescribe().isUpdateable()) {
        // populate a.SSN__c
    }
}
update records;
```

**Right code.**

```apex
SObjectAccessDecision dec = Security.stripInaccessible(
    AccessType.UPDATABLE, records
);
update dec.getRecords();
```

Bulk-safe; honors FLS without explicit per-field checks.

---

## Example 3 — Dynamic SObject creation by name

```apex
public static SObject createByName(String apiName) {
    Schema.SObjectType t = Schema.getGlobalDescribe().get(apiName);
    if (t == null) throw new IllegalArgumentException(apiName);
    return t.newSObject();
}
```

NOT `Type.forName(apiName)` — that returns `System.Type`, not an
SObject.

---

## Example 4 — Active picklist values only

```apex
public static List<String> activeIndustryValues() {
    List<String> out = new List<String>();
    for (Schema.PicklistEntry pe : Account.Industry.getDescribe().getPicklistValues()) {
        if (pe.isActive()) out.add(pe.getValue());
    }
    return out;
}
```

`getValue()` is the API name, `getLabel()` is the display string.

---

## Example 5 — RecordType by DeveloperName

```apex
Schema.DescribeSObjectResult ds = Account.SObjectType.getDescribe();
Map<String, Schema.RecordTypeInfo> byDevName = ds.getRecordTypeInfosByDeveloperName();
Id partnerRtId = byDevName.get('Partner_Account')?.getRecordTypeId();
```

Use `byDeveloperName` (stable across orgs), not `byName` (label,
which can be renamed).
