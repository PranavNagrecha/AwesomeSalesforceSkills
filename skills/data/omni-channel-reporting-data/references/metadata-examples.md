# Metadata Examples: Omni-Channel Reporting Data

A deployable custom report type with AgentWork as the base object, so supervisors can build historical reports that include `IsTransfer` (readable in reports, not through the API). Element names follow the Metadata API Developer Guide, Version 67.0, ReportType entry. The ReportType reference states that `baseObject` supports "all objects, including custom and external objects." Column `field` values use the lookup notation shown in that entry's sample (`Owner.IsActive`).

## File: `force-app/main/default/reportTypes/Omni_Agent_Work_History.reportType-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ReportType xmlns="http://soap.sforce.com/2006/04/metadata">
    <baseObject>AgentWork</baseObject>
    <category>other</category>
    <deployed>true</deployed>
    <description>Omni-Channel assignments, one row per AgentWork. Transfers create extra rows; use IsTransfer to split them. ActiveTime is tracked only for tab-based capacity.</description>
    <label>Omni Agent Work History</label>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Name</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>User.Name</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>ServiceChannel.MasterLabel</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>OriginalGroup.Name</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>Status</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>IsTransfer</field>
            <table>AgentWork</table>
        </columns>
        <masterLabel>Assignment</masterLabel>
    </sections>
    <sections>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>RequestDateTime</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>AssignedDateTime</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>AcceptDateTime</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>CloseDateTime</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>SpeedToAnswer</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>true</checkedByDefault>
            <field>HandleTime</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>ActiveTime</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>CapacityModel</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>CapacityWeight</field>
            <table>AgentWork</table>
        </columns>
        <columns>
            <checkedByDefault>false</checkedByDefault>
            <field>DeclineReason</field>
            <table>AgentWork</table>
        </columns>
        <masterLabel>Timing and Capacity</masterLabel>
    </sections>
</ReportType>
```

UNVERIFIED (2026-10-03): the `category` value `other` is a valid ReportTypeCategory enumeration value, but the Metadata API guide does not say which category Salesforce assigns to Omni-Channel objects. The lookup columns `User.Name`, `ServiceChannel.MasterLabel`, and `OriginalGroup.Name` use the relationship names listed in the AgentWork field entries (`User`, `ServiceChannel`, `OriginalGroup`); deploy to a sandbox first to confirm each lookup is exposed to report types. The polymorphic `WorkItem` relationship is left out on purpose: no fetched source confirms that report types can traverse it.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Omni_Agent_Work_History</members>
        <name>ReportType</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy and verify

1. Deploy to a sandbox: `sf project deploy start --manifest manifest/package.xml --target-org <sandbox-alias>`.
2. In Reports, create a report from "Omni Agent Work History." Filter by `ServiceChannel` for one channel at a time.
3. Group by `IsTransfer` and confirm the transferred rows match the number of `Status = Transferred` rows on the handed-off assignments.
4. Run the checker against the folder before committing: `python3 skills/data/omni-channel-reporting-data/scripts/check_omni_channel_reporting_data.py --manifest-dir force-app/main/default`.
