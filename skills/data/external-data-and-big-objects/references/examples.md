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

Aggregate daily averages into a summary custom object with a stateful Batch Apex job.

> This is where an Async SOQL `POST /services/data/vXX.0/async-queries/` job used to go, with a
> `targetObject` and `targetFieldMap` that materialised the aggregate for you. Async SOQL was
> **retired in Summer '23** and that endpoint no longer exists. Batch Apex replaces the job
> semantics but not the automatic write — the class below does its own aggregation and its own
> insert, because nothing does it on your behalf any more.

```apex
public class SensorDailyRollup implements Database.Batchable<SObject>, Database.Stateful {

    // key: DeviceId + '|' + yyyy-MM-dd
    private Map<String, Decimal> sumByKey   = new Map<String, Decimal>();
    private Map<String, Integer> countByKey = new Map<String, Integer>();

    private final Id      deviceId;
    private final DateTime windowStart;

    public SensorDailyRollup(Id deviceId, DateTime windowStart) {
        this.deviceId    = deviceId;
        this.windowStart = windowStart;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        // Composite index is (DeviceId__c, ReadingTime__c).
        // Leading field takes = only; the last filtered field may take a range operator.
        // Note there is no GROUP BY here - big object SOQL will not do the aggregation.
        return Database.getQueryLocator([
            SELECT DeviceId__c, ReadingTime__c, Temperature__c
            FROM SensorReading__b
            WHERE DeviceId__c = :deviceId AND ReadingTime__c >= :windowStart
        ]);
    }

    public void execute(Database.BatchableContext bc, List<SensorReading__b> scope) {
        for (SensorReading__b r : scope) {
            String key = r.DeviceId__c + '|' + String.valueOf(r.ReadingTime__c.date());
            sumByKey.put(key,   (sumByKey.get(key)   == null ? 0 : sumByKey.get(key))   + r.Temperature__c);
            countByKey.put(key, (countByKey.get(key) == null ? 0 : countByKey.get(key)) + 1);
        }
    }

    public void finish(Database.BatchableContext bc) {
        List<DailySensorSummary__c> rows = new List<DailySensorSummary__c>();
        for (String key : sumByKey.keySet()) {
            List<String> parts = key.split('\\|');
            rows.add(new DailySensorSummary__c(
                DeviceId__c            = parts[0],
                SummaryDate__c         = Date.valueOf(parts[1]),
                AverageTemperature__c  = sumByKey.get(key) / countByKey.get(key)
            ));
        }
        insert rows;
    }
}
```

**Why it works:** The `WHERE` clause is a gapless left-to-right prefix of the composite index — `DeviceId__c` with `=`, then a range on `ReadingTime__c` as the last filtered field — so the query is valid and the platform reads only the relevant partition. `Database.Stateful` carries the running sums across `execute()` chunks, and `finish()` performs the write that Async SOQL's `targetFieldMap` used to perform. On the write side, `Database.insertImmediate()` puts the raw readings in the Big Object storage tier, leaving standard org data storage untouched.

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

## Anti-Pattern: Routing Big Object Reads Through Async SOQL

**What practitioners do:** After creating a Big Object, a design document (or an AI assistant) specifies the read path as `POST /services/data/vXX.0/async-queries/` with a `targetObject`, polled until `Completed`. Sometimes it is framed as a correction — "standard SOQL doesn't scale on Big Objects, use Async SOQL."

**What goes wrong:** Async SOQL was **retired in Summer '23**. The endpoint returns 404. This is usually discovered *after* the archival write path is built and populated, because writes (`Database.insertImmediate`, Bulk API) work fine and nobody exercises the read until the first compliance query. At that point there is a Big Object holding hundreds of millions of records and no implemented way to read them.

The framing makes it worse: presented as the sophisticated alternative to the naive standard-SOQL approach, it survives code review precisely because it sounds like expertise.

**Correct approach:** Standard SOQL is the query mechanism for Big Objects, subject to the composite-index prefix rule. For result sets larger than one transaction, wrap it in Batch Apex over a `Database.QueryLocator`; for extraction out of the platform, use Bulk API query. Salesforce Help states it directly: "You must use the Bulk API or batch Apex to query or report on custom Big Objects."

**Detection hint:** `grep -rn 'async-queries\|AsyncQueryJob' .` — any hit is a dead endpoint. Also flag any Big Object design that names a `targetObject` / `targetFieldMap` for query results; that is the Async SOQL request shape, and no current API has an equivalent.
