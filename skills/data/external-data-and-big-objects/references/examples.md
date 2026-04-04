# Examples — External Data and Big Objects

## Example 1: Inserting IoT Sensor Readings into a Big Object

**Context:** A manufacturing org collects telemetry events from 5,000 connected devices. Each device emits a reading every 30 seconds, producing roughly 14 million records per day. The data must be retained for 7 years for regulatory compliance. Standard custom objects would exhaust data storage within weeks.

**Problem:** Developers initially inserted records into a custom object `SensorReading__c`. Within 60 days, the org consumed 90% of data storage and nightly batch reports began timing out because unrelated SOQL queries were competing for the same storage tier.

**Solution:**

Define the Big Object with a composite index on `(DeviceId__c, ReadingTime__c)` — the two fields always used together in queries:

```xml
<!-- SensorReading__b.object-meta.xml (simplified) -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
  <label>Sensor Reading</label>
  <pluralLabel>Sensor Readings</pluralLabel>
  <deploymentStatus>Deployed</deploymentStatus>
  <indexes>
    <fullName>SensorReadingIndex</fullName>
    <label>Sensor Reading Index</label>
    <fields>
      <name>DeviceId__c</name>
      <sortDirection>ASC</sortDirection>
    </fields>
    <fields>
      <name>ReadingTime__c</name>
      <sortDirection>DESC</sortDirection>
    </fields>
  </indexes>
</CustomObject>
```

Insert records using `Database.insertImmediate()` in the platform event subscriber:

```apex
trigger SensorEventTrigger on SensorEvent__e (after insert) {
    List<Database.SaveResult> results = new List<Database.SaveResult>();
    for (SensorEvent__e evt : Trigger.new) {
        SensorReading__b reading = new SensorReading__b(
            DeviceId__c   = evt.DeviceId__c,
            ReadingTime__c = evt.CreatedDate,
            Temperature__c = evt.Temperature__c,
            Humidity__c    = evt.Humidity__c
        );
        results.add(Database.insertImmediate(reading));
    }
    for (Database.SaveResult sr : results) {
        if (!sr.isSuccess()) {
            for (Database.Error e : sr.getErrors()) {
                // Log to a custom error object or platform event
                System.debug(LoggingLevel.ERROR, 'Big Object insert failed: ' + e.getMessage());
            }
        }
    }
}
```

Submit an Async SOQL job to aggregate daily averages into a summary custom object:

```http
POST /services/data/v62.0/async-queries/
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "SELECT DeviceId__c, DAY_ONLY(ReadingTime__c) dayDate, AVG(Temperature__c) avgTemp FROM SensorReading__b WHERE ReadingTime__c >= 2025-01-01T00:00:00Z GROUP BY DeviceId__c, DAY_ONLY(ReadingTime__c)",
  "operation": "insert",
  "targetObject": "DailySensorSummary__c",
  "targetFieldMap": {
    "DeviceId__c": "DeviceId__c",
    "dayDate": "SummaryDate__c",
    "avgTemp": "AverageTemperature__c"
  },
  "cleanupJobRef": "0vY..."
}
```

**Why it works:** The composite index covers the two filter columns in query order, so Async SOQL can locate the correct partition without a full scan. The `Database.insertImmediate()` pattern offloads storage to the Big Object tier, leaving standard org storage untouched.

---

## Example 2: External Object Lookup for ERP Order Status

**Context:** A commerce org needs to display live order status from an SAP system on the Order record page. Order status changes frequently; copying it into Salesforce via nightly batch would always be 12-24 hours stale. The SAP system exposes an OData 4.0 endpoint.

**Problem:** The initial design replicated SAP orders into a custom object via nightly ETL. Customer service reps were making decisions based on stale data, causing incorrect refund processing.

**Solution:**

Configure the external data source in Setup pointing to the SAP OData endpoint, then define the External Object:

```xml
<!-- SAPOrder__x.object-meta.xml (simplified) -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
  <label>SAP Order</label>
  <pluralLabel>SAP Orders</pluralLabel>
  <externalDataSource>SAP_ERP</externalDataSource>
  <externalName>Orders</externalName>
  <fields>
    <fullName>OrderNumber__c</fullName>
    <externalName>OrderNumber</externalName>
    <label>Order Number</label>
    <type>Text</type>
    <length>50</length>
  </fields>
  <fields>
    <fullName>Status__c</fullName>
    <externalName>Status</externalName>
    <label>Status</label>
    <type>Text</type>
    <length>50</length>
  </fields>
</CustomObject>
```

Query in Apex for a single record lookup (acceptable callout cost):

```apex
// Safe: single record lookup on an indexed External Object field
List<SAPOrder__x> orders = [
    SELECT OrderNumber__c, Status__c
    FROM SAPOrder__x
    WHERE ExternalId = :sfOrderId
    LIMIT 1
];
if (!orders.isEmpty()) {
    currentStatus = orders[0].Status__c;
}
```

**Why it works:** External Objects proxy the read directly to SAP at query time, returning always-current data. Because this is a single-record lookup (not a bulk scan), the single callout cost is acceptable and stays well within the 100-callout per-transaction limit.

---

## Anti-Pattern: Querying a Big Object with Standard SOQL in Production

**What practitioners do:** After creating a Big Object, developers write a standard SOQL query like `SELECT Id, EventTime__c FROM EventLog__b WHERE UserId__c = :uid` in Apex and execute it synchronously.

**What goes wrong:** Standard SOQL against a Big Object works only for very small datasets (roughly hundreds of records in a sandbox). At production scale, queries return zero results silently, time out, or return partial data. There is no error — the query simply does not traverse the storage tier correctly for large volumes. Teams waste days debugging data pipelines before realising the mechanism is wrong.

**Correct approach:** Use the Async SOQL REST API (`POST /services/data/vXX.0/async-queries/`) to submit the query as a background job. Poll for job completion, then read results from the designated target object. Never rely on synchronous SOQL for Big Object queries in production orgs.
