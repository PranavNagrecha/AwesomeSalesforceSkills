# Worked Example — A Null-Inclusive Custom Index Request, End to End

## 1. Evidence gathered

| Item | Value |
|---|---|
| Org | Production org ID (15 characters) |
| Object | `Service_Request__c`, 3,200,000 rows including Recycle Bin rows (`SELECT COUNT() FROM Service_Request__c ALL ROWS` in Apex) |
| Query | `SELECT Id FROM Service_Request__c WHERE Assigned_Team__c = null AND Status__c = 'New'` (runs every 2 minutes from a scheduled assignment job) |
| Plan (before) | `leadingOperationType: TableScan`, `relativeCost` 2.4, note "Not considering filter for optimization because unindexed" on `Status__c` |
| Counts | `Assigned_Team__c = null`: 41,000; `Status__c = 'New'`: 52,000; both: 38,000 |
| Threshold (custom index, 3.2M rows) | 10% × 1,000,000 + 5% × 2,200,000 = 210,000 |

Both filters are far under 210,000, so a custom index would be used. `Assigned_Team__c` is a lookup, which is indexed, but index tables exclude null rows by default, so the null filter cannot use it.

## 2. What to ask for

| Option | Choice | Reason |
|---|---|---|
| Null-inclusive index on `Assigned_Team__c` | Ask | The selective filter is the null comparison |
| Custom index on `Status__c` | Ask as fallback | 52,000 rows, under threshold; a picklist can't be made External ID |
| Two-column index | Not needed | No sort requirement |

## 3. Case text

```text
Subject: Null-inclusive custom index request — Service_Request__c.Assigned_Team__c

Object: Service_Request__c (about 3.2M rows including deleted rows)
Query (literal values):
  SELECT Id FROM Service_Request__c WHERE Assigned_Team__c = null AND Status__c = 'New'
Frequency: every 2 minutes (scheduled assignment job); blocks first-response SLA when slow
Plan: TableScan, relativeCost 2.4 (REST explain output attached)
Distribution: Assigned_Team__c = null -> 41,000 rows; Status__c = 'New' -> 52,000 rows
Request: null-inclusive index on Assigned_Team__c.
Fallback: custom index on Status__c.
Testing: we will validate in production and in a sandbox created after the index exists.
```

## 4. After Support confirms

If Support asks you to keep the definition in source control, the `CustomIndex` component records the null setting (file name illustrative):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomIndex xmlns="http://soap.sforce.com/2006/04/metadata">
    <allowNullValues>true</allowNullValues>
</CustomIndex>
```

Then capture the plan again. Expected: `leadingOperationType: Index` with `fields` containing `Assigned_Team__c`, `relativeCost` under 1.0. Re-check the day after any large load, because optimizer statistics are gathered nightly.
