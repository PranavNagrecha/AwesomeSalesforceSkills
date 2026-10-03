# Metadata and API Examples: Program Processes in Source Control and the Transaction Feed

Two artifacts a loyalty implementation keeps under version control: the `LoyaltyProgramSetup` file that holds a program's processes, and the request an external system sends to the Transaction Journals Execution resource. Field names come from the Metadata API Developer Guide, Version 67.0 (LoyaltyProgramSetup) and the Loyalty Management Developer Guide pages Transaction Journals Execution and Eligible Promotions List (POST), fetched 2026-10-03.

## Step 1: Retrieve the program first

The `label` in a `LoyaltyProgramSetup` file is the program name, and "if a loyalty program or referral program with the specified name doesn't exist, a new LoyaltyProgram record is created." Retrieve before editing so the name is exact.

### Manifest: `manifest/loyalty-retrieve.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>SkyRewards</members>
        <name>LoyaltyProgramSetup</name>
    </types>
    <version>67.0</version>
</Package>
```

```bash
sf project retrieve start --manifest manifest/loyalty-retrieve.xml --target-org <sandbox alias>
```

The guide's note: "To retrieve metadata specific to any loyalty program, mention the loyalty program name in the <members> tag."

## Step 2: A program process in source control

### File: `force-app/main/default/loyaltyProgramSetups/SkyRewards.loyaltyProgramSetup-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LoyaltyProgramSetup xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>SkyRewards</label>
    <programProcesses>
        <executionType>RealTime</executionType>
        <journalType>Accrual</journalType>
        <parameters>
            <dataType>Numeric</dataType>
            <decimalPlaces>0</decimalPlaces>
            <isCollection>false</isCollection>
            <isInput>false</isInput>
            <isOutput>false</isOutput>
            <parameterName>VoucherValue</parameterName>
            <parameterType>Constant</parameterType>
            <value>50</value>
        </parameters>
        <processName>High Value Booking Voucher</processName>
        <processType>TransactionJournal</processType>
        <rules>
            <isProcessEligibilityRule>false</isProcessEligibilityRule>
            <actions>
                <actionName>Issue High Value Voucher</actionName>
                <actionParameters>
                    <operator>Equals</operator>
                    <parameterName>VoucherDefinitionName</parameterName>
                    <sequenceNumber>1</sequenceNumber>
                    <value>Voucher for High Value Bookings</value>
                    <valueType>Literal</valueType>
                </actionParameters>
                <actionParameters>
                    <operator>Equals</operator>
                    <parameterName>VoucherFaceValue</parameterName>
                    <sequenceNumber>2</sequenceNumber>
                    <value>{!VoucherValue}</value>
                </actionParameters>
                <actionType>IssueVoucher</actionType>
            </actions>
            <conditions>
                <conditionCriteria>1</conditionCriteria>
                <conditionFilterCriteria>
                    <operator>GreaterThanOrEquals</operator>
                    <sequence>1</sequence>
                    <sourceFieldName>TransactionJournal.TransactionAmount</sourceFieldName>
                    <value>500</value>
                    <valueType>Literal</valueType>
                </conditionFilterCriteria>
                <conditionName>Booking At Least 500</conditionName>
                <conditionType>Condition</conditionType>
            </conditions>
            <ruleName>Voucher for Bookings of 500 or More</ruleName>
            <startDate>2026-10-01</startDate>
            <status>Draft</status>
            <stepMappings>
                <associatedStep>Booking At Least 500</associatedStep>
                <sequence>1</sequence>
            </stepMappings>
            <stepMappings>
                <associatedStep>Issue High Value Voucher</associatedStep>
                <parentStep>Booking At Least 500</parentStep>
                <sequence>1</sequence>
            </stepMappings>
        </rules>
        <status>Draft</status>
    </programProcesses>
</LoyaltyProgramSetup>
```

Field notes from the Metadata API guide:

| Element | Values and rules |
|---|---|
| `executionType` | `Batch`, `BatchAndRealTime`, `RealTime` |
| `journalType` | `Accrual` or `Redemption` for loyalty programs |
| `processType` | Required; the record type processed |
| `actionType` | Includes `CreditPoints`, `DebitPoints`, `IssueVoucher`, `ChangeMemberTier`, `GetMemberTier`, `RunProgramProcess`, `Crud` |
| `status` | `Active`, `Draft`, `Inactive`; "Only active program processes can process transaction journals." |

This file adapts the guide's own `IssueVoucher` sample, keeps the process in `Draft`, and changes names and the threshold. It deploys the process without activating it; activate after review. UNVERIFIED (2026-10-03): the guide describes `processType` as `TransactionJournal` for referral programs, but its loyalty sample uses `Transaction Journal` with a space; use whatever value the Step 1 retrieve returns. The voucher definition named in `VoucherDefinitionName` must already exist.

### Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>SkyRewards</members>
        <name>LoyaltyProgramSetup</name>
    </types>
    <version>67.0</version>
</Package>
```

The type requires one of the B2C - Loyalty, B2C - Loyalty Plus, Loyalty Management - Growth, Loyalty Management - Advanced, or Referral Marketing licenses.

## Step 3: Feed transactions from the external system

### Optional first call: Eligible Promotions List

When promotion limits matter, call `POST /services/data/v67.0/global-promotions-management/eligible-promotions` (API 60.0+) first. It needs Context Definitions, the Context Rule Library, Global Promotions Management, and the Track Member Progress for Engagement Trails Using Promotion Party Usage setting, and it excludes promotions whose limit is reached. Pass its result as `appliedPromotions` below; "Promotion limits aren't enforced if appliedPromotions is omitted."

### Request: Transaction Journals Execution

```http
POST /services/data/v67.0/connect/realtime/loyalty/programs/SkyRewards HTTP/1.1
Host: MyDomainName.my.salesforce.com
Authorization: Bearer <access token for a user with the Loyalty Management permission set>
Content-Type: application/json
```

```json
{
  "transactionJournals": [
    {
      "ActivityDate": "2026-10-03T12:45:19Z",
      "JournalDate": "2026-10-03T00:45:19Z",
      "ExternalTransactionNumber": "BK-20261003-0001",
      "JournalTypeId": "<Journal Type Id for Accrual>",
      "LoyaltyProgramId": "<Loyalty Program Id>",
      "MemberId": "<Loyalty Program Member Id>",
      "TransactionAmount": "620",
      "Origin": "Bangalore",
      "Destination": "Hyderabad",
      "Status": "Pending"
    }
  ]
}
```

This mirrors the guide's airline example (`Origin`, `Destination`, `ExternalTransactionNumber`, `Status` `Pending`). Each journal's applicable program process applies eligible rules and actions, then creates the transaction journal. Since API 55.0 the body can instead carry `{"transactionJournals": [{"Id": "<existing journal Id>"}]}` to process journals already in the org.

## Verify

```bash
python3 skills/integration/loyalty-management-setup/scripts/check_loyalty_management_setup.py --manifest-dir force-app/main/default
```
