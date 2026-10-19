# Metadata Examples — Feature Flags via Custom Metadata

## The `Feature_Flag__mdt` type (Metadata API `.object` form)

The Metadata API represents a custom metadata type as a `CustomObject` with the `__mdt` suffix in the `objects` folder. This single-file form follows the guide's `ReusablePicklistOption__mdt` sample; in an SFDX source project the same definition is split into `objects/Feature_Flag__mdt/Feature_Flag__mdt.object-meta.xml` plus one `fields/<Name>.field-meta.xml` per field.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- objects/Feature_Flag__mdt.object -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <fields>
        <fullName>Is_Enabled__c</fullName>
        <defaultValue>false</defaultValue>
        <externalId>false</externalId>
        <label>Is Enabled</label>
        <type>Checkbox</type>
    </fields>
    <fields>
        <fullName>Percent_Rollout__c</fullName>
        <externalId>false</externalId>
        <label>Percent Rollout</label>
        <precision>4</precision>
        <scale>1</scale>
        <required>false</required>
        <type>Number</type>
        <unique>false</unique>
    </fields>
    <label>Feature Flag</label>
    <pluralLabel>Feature Flags</pluralLabel>
    <visibility>Public</visibility>
</CustomObject>
```

`visibility` accepts `Public` (default), `Protected`, and `PackageProtected`. A flag shipped in a managed package that subscribers must not read is `Protected`; an unpackaged org flag stays `Public`.

## Manifest entries

Records are listed by `<TypeNameWithoutSuffix>.<RecordName>`; a wildcard retrieves every record:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Feature_Flag__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Feature_Flag.NewDiscountEngine</members>
        <name>CustomMetadata</name>
    </types>
    <version>67.0</version>
</Package>
```

## Test override in the accessor

Tests cannot insert `Feature_Flag__mdt` rows, so the accessor takes an in-memory override that only tests set:

```apex
public with sharing class FeatureFlags {
    @TestVisible
    private static Map<String, Boolean> overrides = new Map<String, Boolean>();

    public static Boolean isEnabled(String flagName) {
        if (overrides.containsKey(flagName)) {
            return overrides.get(flagName);
        }
        Feature_Flag__mdt flag = Feature_Flag__mdt.getInstance(flagName);
        return flag != null && flag.Is_Enabled__c == true;   // rollout bucket omitted here; see examples.md
    }
}

@IsTest
private class DiscountEngine_Test {
    @IsTest
    static void newEngineRunsWhenFlagOn() {
        FeatureFlags.overrides.put('NewDiscountEngine', true);
        Opportunity opp = new Opportunity(Name = 'T', StageName = 'Prospecting', CloseDate = Date.today(), Amount = 100);
        Decimal price = new DiscountEngine().calculate(opp);
        Assert.isNotNull(price, 'new engine path should return a price');
    }
}
```
