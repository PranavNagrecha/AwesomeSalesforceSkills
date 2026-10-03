# Metadata Examples: CPQ Guided Selling

A deployable worked example: a "Deployment Model" guided selling question backed by a Product2 field and its Process Input mirror, plus an Enhanced-mode product search plugin that hides low-inventory products when the rep asks for urgent shipment.

Grounding: Salesforce CPQ Plugins Developer Guide, `SBQQ.ProductSearchPlugin` guided selling and product search interfaces (`cpq_plugins L1003-1640`); Salesforce CPQ Developer Guide, quote model (`cpq_developer_guide L950-975`); Metadata API Developer Guide, CustomField and ApexClass. The guided selling record fields (Quote Process, Process Input) are not deployable metadata and their API names are help-only, so they appear only as a Setup procedure with UNVERIFIED markers.

Licence gate: requires the Salesforce CPQ managed package (`SBQQ` namespace). The package has no new feature development; see `gotchas.md` gotcha 1.

## 1. Product2 classification and inventory fields

`force-app/main/default/objects/Product2/fields/Deployment_Model__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Deployment_Model__c</fullName>
    <label>Deployment Model</label>
    <required>false</required>
    <type>Picklist</type>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Cloud</fullName>
                <default>false</default>
                <label>Cloud</label>
            </value>
            <value>
                <fullName>On_Premises</fullName>
                <default>false</default>
                <label>On Premises</label>
            </value>
            <value>
                <fullName>Hybrid</fullName>
                <default>false</default>
                <label>Hybrid</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

`force-app/main/default/objects/Product2/fields/Inventory_Level__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Inventory_Level__c</fullName>
    <label>Inventory Level</label>
    <precision>10</precision>
    <required>false</required>
    <scale>0</scale>
    <type>Number</type>
</CustomField>
```

## 2. The mirror field on Process Input

`force-app/main/default/objects/SBQQ__ProcessInput__c/fields/Deployment_Model__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Deployment_Model__c</fullName>
    <label>Deployment Model</label>
    <required>false</required>
    <type>Picklist</type>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Cloud</fullName>
                <default>false</default>
                <label>Cloud</label>
            </value>
            <value>
                <fullName>On_Premises</fullName>
                <default>false</default>
                <label>On Premises</label>
            </value>
            <value>
                <fullName>Hybrid</fullName>
                <default>false</default>
                <label>Hybrid</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

Same API name, same type, same values as the Product2 field. UNVERIFIED (2026-10-03): the requirement for this mirror field is documented only on help.salesforce.com (`gotchas.md` gotcha 2). Grant field-level security on it to every permission set that runs the wizard.

## 3. Enhanced-mode product search plugin

`force-app/main/default/classes/UrgentShipmentSearchPlugin.cls`

```apex
/**
 * Guided selling plugin in Enhanced mode: CPQ keeps its own query and this class
 * appends one WHERE fragment when the rep answers "Yes" to "Urgent Shipment".
 * Method signatures follow the Salesforce CPQ Plugins Developer Guide.
 */
global with sharing class UrgentShipmentSearchPlugin implements SBQQ.ProductSearchPlugin {

    private static final String URGENT_FILTER = 'AND Product2.Inventory_Level__c > 3';

    global UrgentShipmentSearchPlugin() {}

    // ---------- Guided selling interface ----------

    global Boolean isInputHidden(SObject quote, String fieldName) {
        return false;
    }

    global String getInputDefaultValue(SObject quote, String fieldName) {
        return null;
    }

    global Boolean isSuggestCustom(SObject quote, Map<String, Object> fieldValuesMap) {
        return false; // Enhanced: CPQ calls getAdditionalSuggestFilters, not suggest
    }

    global String getAdditionalSuggestFilters(SObject quote, Map<String, Object> fieldValuesMap) {
        Object urgent = firstValue(fieldValuesMap, new List<String>{ 'Urgent Shipment', 'Urgent_Shipment__c' });
        // Static fragment only; no rep-entered text is concatenated into SOQL.
        return 'Yes'.equals(urgent) ? URGENT_FILTER : null;
    }

    global List<PricebookEntry> suggest(SObject quote, Map<String, Object> fieldValuesMap) {
        // Only runs if isSuggestCustom returns true. Kept bind-safe for that case.
        Id pricebookId = (Id) quote.get('SBQQ__Pricebook__c');
        Object model = fieldValuesMap.get('Deployment_Model__c');
        Set<String> fields = new Set<String>{ 'Id', 'UnitPrice', 'Pricebook2Id', 'Product2Id', 'Product2.Id' };
        for (Schema.FieldSetMember m : SObjectType.Product2.fieldSets.SBQQ__SearchResults.getFields()) {
            fields.add('Product2.' + m.getFieldPath());
        }
        String soql = 'SELECT ' + String.join(new List<String>(fields), ', ')
            + ' FROM PricebookEntry WHERE Pricebook2Id = :pricebookId AND IsActive = true'
            + (model == null ? '' : ' AND Product2.Deployment_Model__c = :model');
        return Database.queryWithBinds(
            soql,
            new Map<String, Object>{ 'pricebookId' => pricebookId, 'model' => model },
            AccessLevel.USER_MODE
        );
    }

    // ---------- Product search interface (not used by this design) ----------

    global Boolean isFilterHidden(SObject quote, String fieldName) {
        return false;
    }

    global String getFilterDefaultValue(SObject quote, String fieldName) {
        return null;
    }

    global Boolean isSearchCustom(SObject quote, Map<String, Object> fieldValuesMap) {
        return false;
    }

    global String getAdditionalSearchFilters(SObject quote, Map<String, Object> fieldValuesMap) {
        return null;
    }

    global List<PricebookEntry> search(SObject quote, Map<String, Object> fieldValuesMap) {
        return null; // not called while isSearchCustom returns false
    }

    private static Object firstValue(Map<String, Object> values, List<String> keys) {
        if (values == null) {
            return null;
        }
        for (String key : keys) {
            if (values.containsKey(key)) {
                return values.get(key);
            }
        }
        return null;
    }
}
```

`force-app/main/default/classes/UrgentShipmentSearchPlugin.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

Why both lookup keys: the guide describes the map key as "a Product2 API name", but its own `getAdditionalSuggestFilters` example reads the key `'Urgent Shipment'`. UNVERIFIED (2026-10-03): which key form CPQ sends for a question that does not map to a Product2 field; the helper accepts either. UNVERIFIED (2026-10-03): the guide's example classes each show one half of the interface; this class implements both halves so it compiles if the interface declares all ten methods. Compile it in a sandbox with CPQ installed.

## 4. Test class

`force-app/main/default/classes/UrgentShipmentSearchPluginTest.cls`

```apex
@IsTest
private class UrgentShipmentSearchPluginTest {

    @IsTest
    static void appendsInventoryFilterOnlyForUrgentShipments() {
        UrgentShipmentSearchPlugin plugin = new UrgentShipmentSearchPlugin();
        SObject quote = new SBQQ__Quote__c();

        System.assertEquals(false, plugin.isSuggestCustom(quote, new Map<String, Object>()));
        System.assertEquals('AND Product2.Inventory_Level__c > 3',
            plugin.getAdditionalSuggestFilters(quote, new Map<String, Object>{ 'Urgent Shipment' => 'Yes' }));
        System.assertEquals(null,
            plugin.getAdditionalSuggestFilters(quote, new Map<String, Object>{ 'Urgent Shipment' => 'No' }));
        System.assertEquals(false, plugin.isInputHidden(quote, 'Urgent Shipment'));
        System.assertEquals(null, plugin.getInputDefaultValue(quote, 'Urgent Shipment'));
    }

    @IsTest
    static void suggestReturnsEntriesFromTheQuotePricebookOnly() {
        Product2 cloud = new Product2(Name = 'Edge Gateway', IsActive = true, Deployment_Model__c = 'Cloud');
        Product2 onPrem = new Product2(Name = 'Rack Server', IsActive = true, Deployment_Model__c = 'On_Premises');
        insert new List<Product2>{ cloud, onPrem };
        Id standardPb = Test.getStandardPricebookId();
        insert new List<PricebookEntry>{
            new PricebookEntry(Pricebook2Id = standardPb, Product2Id = cloud.Id, UnitPrice = 100, IsActive = true),
            new PricebookEntry(Pricebook2Id = standardPb, Product2Id = onPrem.Id, UnitPrice = 200, IsActive = true)
        };
        SObject quote = new SBQQ__Quote__c();
        quote.put('SBQQ__Pricebook__c', standardPb);

        List<PricebookEntry> result = new UrgentShipmentSearchPlugin()
            .suggest(quote, new Map<String, Object>{ 'Deployment_Model__c' => 'Cloud' });

        System.assertEquals(1, result.size());
        System.assertEquals(cloud.Id, result[0].Product2Id);
    }

    @IsTest
    static void productSearchHalfIsInert() {
        UrgentShipmentSearchPlugin plugin = new UrgentShipmentSearchPlugin();
        SObject quote = new SBQQ__Quote__c();
        System.assertEquals(false, plugin.isSearchCustom(quote, new Map<String, Object>()));
        System.assertEquals(false, plugin.isFilterHidden(quote, 'Family'));
        System.assertEquals(null, plugin.getFilterDefaultValue(quote, 'Family'));
        System.assertEquals(null, plugin.getAdditionalSearchFilters(quote, new Map<String, Object>()));
        System.assertEquals(null, plugin.search(quote, new Map<String, Object>()));
    }
}
```

`force-app/main/default/classes/UrgentShipmentSearchPluginTest.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

## 5. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>UrgentShipmentSearchPlugin</members>
        <members>UrgentShipmentSearchPluginTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Product2.Deployment_Model__c</members>
        <members>Product2.Inventory_Level__c</members>
        <members>SBQQ__ProcessInput__c.Deployment_Model__c</members>
        <name>CustomField</name>
    </types>
    <version>67.0</version>
</Package>
```

## 6. Records and settings (Setup procedure, not metadata)

Quote Process and Process Input records are data. Create them in a sandbox and move them with a data tool.

1. App Launcher, then Quote Processes, then New. Name it "Hardware Guided Selling" and enable guided selling on it. UNVERIFIED (2026-10-03): the checkbox API name (`SBQQ__GuidedProductSelection__c` in earlier versions of this skill) is help-only.
2. On the quote process, add two Process Inputs: "Deployment Model" filtering Product2 field `Deployment_Model__c` with an equals operator, and "Urgent Shipment" with Yes and No values for the plugin to read. UNVERIFIED (2026-10-03): Process Input field names and operator values are help-only.
3. Setup, then Installed Packages, then Salesforce CPQ, then Configure, then the Plugins tab: enter `UrgentShipmentSearchPlugin` as the product search plugin. UNVERIFIED (2026-10-03): the field label on the Plugins tab is not named in the plugins guide for this plugin.
4. Make the quote process the default, or set it on test quotes (`SBQQ__Quote__c.SBQQ__QuoteProcessId__c`).

## Deploy order

1. `CustomField` on Product2, then the mirror on `SBQQ__ProcessInput__c`.
2. `ApexClass` (plugin and test). Run `UrgentShipmentSearchPluginTest`.
3. Records and plugin registration (section 6).

## Verification

- Answer "Cloud" with "Urgent Shipment" = "No": only Cloud products appear.
- Answer "Cloud" with "Urgent Shipment" = "Yes": only Cloud products with `Inventory_Level__c` above 3 appear.
- Remove field-level security on the mirror field in a sandbox and confirm the question stops filtering, so support staff recognize the symptom.
