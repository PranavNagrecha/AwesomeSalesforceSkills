# Metadata Examples: Roll Up Summary Alternatives

## Example A: Native roll-up on master-detail

**Context:** `Invoice_Line__c` is the detail in a master-detail relationship to `Invoice__c`. The invoice needs the total of non-cancelled lines.

**File:** `force-app/main/default/objects/Invoice__c/fields/Total_Amount__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Total_Amount__c</fullName>
    <label>Total Amount</label>
    <summarizedField>Invoice_Line__c.Amount__c</summarizedField>
    <summaryFilterItems>
        <field>Invoice_Line__c.Is_Cancelled__c</field>
        <operation>equals</operation>
        <value>false</value>
    </summaryFilterItems>
    <summaryForeignKey>Invoice_Line__c.Invoice__c</summaryForeignKey>
    <summaryOperation>sum</summaryOperation>
    <type>Summary</type>
</CustomField>
```

package.xml member: `Invoice__c.Total_Amount__c` under `<name>CustomField</name>`.

**Why it works:** `summarizedField`, `summaryFilterItems`, `summaryForeignKey` (the master-detail field on the child), and `summaryOperation` are the CustomField properties in the Metadata API Developer Guide (262). UNVERIFIED (2026-10-03): the guide lists the operation values as Count, Min, Max, Sum; this file uses the lowercase form seen in retrieved metadata. Retrieve one existing roll-up from your org to confirm the case before deploying.
