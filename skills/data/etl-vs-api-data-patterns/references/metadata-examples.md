# Metadata Examples: ETL vs API Data Patterns

Upserts by external ID are how an ongoing pipeline reruns safely. Integration Patterns and Practices tells ETL jobs to use primary keys from both systems, and a Bulk API 2.0 upsert job names the field in `externalIdFieldName`.

## External ID field on Account

File: `force-app/main/default/objects/Account/fields/ERP_Customer_Id__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>ERP_Customer_Id__c</fullName>
    <caseSensitive>false</caseSensitive>
    <externalId>true</externalId>
    <label>ERP Customer Id</label>
    <length>40</length>
    <required>false</required>
    <type>Text</type>
    <unique>true</unique>
</CustomField>
```

`externalId` applies to AutoNumber, Email, Number, and Text fields, and an external ID field is indexed (Metadata API Developer Guide, CustomField).

package.xml member form:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.ERP_Customer_Id__c</members>
        <name>CustomField</name>
    </types>
    <version>67.0</version>
</Package>
```

