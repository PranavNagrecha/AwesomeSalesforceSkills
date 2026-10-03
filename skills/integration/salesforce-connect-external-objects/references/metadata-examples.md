# Metadata Examples: OData 4.0 External Object With Apex Access and a Stubbed Test

A deployable Salesforce Connect slice: an OData 4.0 external data source behind a named credential, an external object with an indirect lookup to Account, an Apex service that reads in user mode and writes through the asynchronous path, and a test that mocks the external query with a SOQL stub. Element names come from the Metadata API Developer Guide, Version 67.0 (ExternalDataSource, CustomObject, CustomField); Apex behavior from the Apex Developer Guide, Version 67.0 (Salesforce Connect chapter).

## File: `force-app/main/default/dataSources/ERP_OData.dataSource-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalDataSource xmlns="http://soap.sforce.com/2006/04/metadata">
    <customConfiguration>{"inlineCountEnabled":"true","pagination":"SERVER","noIdMapping":"false","requestCompression":"false","compatibility":"DEFAULT","format":"JSON","timeout":"120","searchEnabled":"true"}</customConfiguration>
    <endpoint>callout:ERP_OData/odata/v4</endpoint>
    <isWritable>true</isWritable>
    <label>ERP OData</label>
    <principalType>Anonymous</principalType>
    <protocol>NoAuthentication</protocol>
    <type>OData4</type>
</ExternalDataSource>
```

- `inlineCountEnabled` is Request Row Counts: required for `COUNT()` and for batch Apex with a query locator.
- `pagination` `SERVER` is Server Driven Pagination: the source sets page sizes, which avoids skipped or doubled records in long batch jobs.
- `endpoint` may be a named credential URL: "A named credential URL contains the scheme callout:, the name of the named credential, and an optional path."
- `isWritable` enables create, update, and delete; omit it for read-only access.

UNVERIFIED (2026-10-03): that `principalType` `Anonymous` with `protocol` `NoAuthentication` is the right pairing when authentication is delegated to the named credential, and that `format` accepts `JSON` for OData 4.0 (the guide's sample shows `ATOM`), are not stated in the fetched guide. Configure the data source once in Setup and retrieve it to confirm.

## File: `force-app/main/default/objects/SalesOrder__x/SalesOrder__x.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>ERP sales orders, virtualized through Salesforce Connect</description>
    <externalDataSource>ERP_OData</externalDataSource>
    <externalIndexAvailable>false</externalIndexAvailable>
    <externalName>SalesOrders</externalName>
    <label>Sales Order</label>
    <pluralLabel>Sales Orders</pluralLabel>
</CustomObject>
```

`externalDataSource` and `externalName` are "Required and available for external objects only." External object names end in `__x`.

## File: `force-app/main/default/objects/SalesOrder__x/fields/Status__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Status__c</fullName>
    <externalDeveloperName>Status</externalDeveloperName>
    <externalId>false</externalId>
    <isFilteringDisabled>false</isFilteringDisabled>
    <isNameField>false</isNameField>
    <isSortingDisabled>false</isSortingDisabled>
    <label>Status</label>
    <length>40</length>
    <required>false</required>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

## File: `force-app/main/default/objects/SalesOrder__x/fields/Amount__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Amount__c</fullName>
    <externalDeveloperName>Amount</externalDeveloperName>
    <externalId>false</externalId>
    <isFilteringDisabled>false</isFilteringDisabled>
    <isNameField>false</isNameField>
    <isSortingDisabled>false</isSortingDisabled>
    <label>Amount</label>
    <precision>16</precision>
    <required>false</required>
    <scale>2</scale>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

## File: `force-app/main/default/objects/Account/fields/ERP_Customer_Number__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>ERP_Customer_Number__c</fullName>
    <externalId>true</externalId>
    <label>ERP Customer Number</label>
    <length>20</length>
    <required>false</required>
    <type>Text</type>
    <unique>true</unique>
</CustomField>
```

## File: `force-app/main/default/objects/SalesOrder__x/fields/CustomerNumber__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>CustomerNumber__c</fullName>
    <externalDeveloperName>CustomerNumber</externalDeveloperName>
    <externalId>false</externalId>
    <isFilteringDisabled>false</isFilteringDisabled>
    <isNameField>false</isNameField>
    <isSortingDisabled>false</isSortingDisabled>
    <label>Customer</label>
    <length>20</length>
    <referenceTargetField>ERP_Customer_Number__c</referenceTargetField>
    <referenceTo>Account</referenceTo>
    <relationshipLabel>Sales Orders</relationshipLabel>
    <relationshipName>Sales_Orders</relationshipName>
    <required>false</required>
    <type>IndirectLookup</type>
    <unique>false</unique>
</CustomField>
```

An indirect lookup links a child external object to a parent standard or custom object. `referenceTargetField` names the parent field to match, and that field "must have both externalId and unique set to true", which is why `ERP_Customer_Number__c` is defined that way. UNVERIFIED (2026-10-03): whether `length` is required on an `IndirectLookup` field; the guide's `ExternalLookup` sample sets it.

## File: `force-app/main/default/classes/SalesOrderService.cls`

```apex
public with sharing class SalesOrderService {
    public static List<SalesOrder__x> openOrdersFor(String customerNumber) {
        // WITH clauses are not supported on external objects, so user mode is
        // passed as the AccessLevel argument instead of WITH USER_MODE.
        Map<String, Object> binds = new Map<String, Object>{ 'customer' => customerNumber };
        return Database.queryWithBinds(
            'SELECT Id, ExternalId, Status__c, Amount__c FROM SalesOrder__x '
                + 'WHERE CustomerNumber__c = :customer AND Status__c = \'Open\' LIMIT 200',
            binds,
            AccessLevel.USER_MODE
        );
    }

    // External objects do not accept plain insert; the write is queued.
    public static String submit(String customerNumber, Decimal amount) {
        SalesOrder__x order = new SalesOrder__x(
            CustomerNumber__c = customerNumber,
            Amount__c = amount,
            Status__c = 'Submitted'
        );
        Database.SaveResult sr = Database.insertAsync(order);
        return Database.getAsyncLocator(sr);
    }
}
```

## File: `force-app/main/default/classes/SalesOrderServiceTest.cls`

```apex
@IsTest
private class SalesOrderServiceTest {
    private class OpenOrderStub extends SoqlStubProvider {
        public override List<SObject> handleSoqlQuery(
            SObjectType sobjectType, String rawQuery, Map<String, Object> binds
        ) {
            Assert.areEqual('C-1001', binds.get('customer'), 'The bind value reaches the stub');
            return new List<SObject>{
                Test.createStubQueryRow(sobjectType, new Map<String, Object>{
                    'Status__c' => 'Open',
                    'Amount__c' => 250.00
                })
            };
        }
    }

    @IsTest
    static void returnsOpenOrdersFromTheStub() {
        Test.createSoqlStub(SalesOrder__x.SObjectType, new OpenOrderStub());
        Test.startTest();
        List<SalesOrder__x> rows = SalesOrderService.openOrdersFor('C-1001');
        Test.stopTest();
        Assert.areEqual(1, rows.size(), 'One stubbed order');
        Assert.areEqual('Open', rows[0].Status__c, 'Stubbed field value');
    }
}
```

The stub follows the Apex Developer Guide's Mock SOQL Tests for External Objects pattern: extend `System.SoqlStubProvider`, build rows with `Test.createStubQueryRow`, and register with `Test.createSoqlStub`. SOQL, SOSL, and callouts are not allowed inside a stub, and governor limits apply to stubbed rows. The asynchronous write path is not exercised by this test. UNVERIFIED (2026-10-03): how `Database.insertAsync` behaves for external objects inside a test method is not stated in the fetched guide.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ERP_OData</members>
        <name>ExternalDataSource</name>
    </types>
    <types>
        <members>SalesOrder__x</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Account.ERP_Customer_Number__c</members>
        <members>SalesOrder__x.Amount__c</members>
        <members>SalesOrder__x.CustomerNumber__c</members>
        <members>SalesOrder__x.Status__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>SalesOrderService</members>
        <members>SalesOrderServiceTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

The `ERP_OData` named credential and its external credential must exist before this deploys; see `integration/named-credentials-setup`.

## Verify

```bash
python3 skills/integration/salesforce-connect-external-objects/scripts/check_salesforce_connect_external_objects.py --manifest-dir force-app/main/default
```
