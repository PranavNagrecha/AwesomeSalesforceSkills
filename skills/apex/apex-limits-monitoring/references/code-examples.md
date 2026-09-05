# Code Examples — Apex Limits Monitoring

A deployable monitoring slice covering the three horizons this skill owns: `LimitGuard`
(in-transaction thresholds and degrade decisions), `OrgLimitsPoller` (a Schedulable that
turns `OrgLimits.getAll()` into `Limit_Snapshot__c` rows against `Limit_Threshold__mdt`),
the two metadata objects, a test class that proves both without mocking a System type,
and the CI query that catches per-test-method limit regressions.

## What This Builds

| Artifact | File | Why it exists |
|---|---|---|
| In-transaction guard | `LimitGuard.cls` | `nearCpu/nearSoql/nearHeap(pct)` booleans and one `snapshot()` string, so a degrade decision is one call instead of a subtraction repeated in ten classes |
| Org-wide poller | `OrgLimitsPoller.cls` | Schedulable; writes one `Limit_Snapshot__c` per limit per run and raises on threshold breach |
| Snapshot store | `Limit_Snapshot__c` + fields | The time series. Without a DateTime column there is no trend, only a "current" value you already had |
| Threshold config | `Limit_Threshold__mdt` + one record | Percent thresholds per limit name, deployable and reviewable — not literals in two classes |
| Alert sink | `LogService` (from `apex/debug-and-logging`) | Do not build a second logger. This skill decides *when* to log; that skill owns *how* |
| Test | `LimitGuardTest.cls` | Asserts guard thresholds against measured consumption and the poller row shape through an injection seam |
| Manifest | `package.xml` | Deploy order matters: object → fields → CMDT → CMDT record → classes |

## How To Read It

- `LimitGuard` never hardcodes a ceiling. Every threshold is a percentage of
  `Limits.getLimitX()`, because "there are two versions of every method: the first returns
  the amount of the resource that has been used while the second version contains the word
  limit and returns the total amount of the resource that is available" (Apex Reference
  Guide, Limits Class, `apexrefguide L220166–220170`) — and the ceiling that comes back
  differs by context (100 vs 200 SOQL, 10,000 vs 60,000 ms CPU; Apex Developer Guide,
  Per-Transaction Apex Limits, `apexdev L19544`, `L19579`).
- `snapshot()` deliberately emits the same `name=used/ceiling` shape that
  `LogService.limitsSnapshot()` emits in `apex/debug-and-logging`, so the two strings
  concatenate and one log query parses both. `LimitGuard` adds the meters `LogService`
  omits (SOSL, callouts, queueable jobs, email, future calls, query-locator rows).
- The poller uses an **injection seam**, not a mock, because `OrgLimits.getAll()` is a
  static method on a System type and the Apex Stub API can mock neither: "You can't mock
  the following Apex elements… Static methods (including future methods)… System types"
  (`apexdev L42205–42211`).
- Thresholds live in `Limit_Threshold__mdt` because they are read in more than one place
  and change without a code review. Custom metadata records are also exempt from the SOQL
  ceiling: "This limit doesn't apply to custom metadata types. In a single Apex transaction,
  custom metadata records can have unlimited SOQL queries" (`apexdev L19617–19618`), so the
  poller's config read costs nothing against the meter it is trying to protect.
- `OrgLimitsPoller` is a *thin* Schedulable — it delegates to a static `run()`. That is the
  shape `apex/apex-scheduled-jobs` prescribes and the Apex Developer Guide recommends:
  "Though it's possible to do additional processing in the `execute` method, we recommend
  that all processing take place in a separate class" (`apexdev L16621–16623`).
- The poller runs under **synchronous** governor limits. "Although scheduled Apex is an
  asynchronous feature, synchronous limits apply to scheduled Apex jobs" (`apexdev L19536`).
  That is why it guards its own DML with `LimitGuard` before inserting.

---

## `force-app/main/default/classes/LimitGuard.cls`

```apex
/**
 * LimitGuard — one place to ask "how close is this transaction to a ceiling?".
 *
 * Every answer is derived from the matching Limits.getLimitX() call at run time, so the
 * same code is correct in a trigger (100 SOQL / 6 MB heap / 10 s CPU) and in a Batch
 * execute (200 SOQL / 12 MB heap / 60 s CPU) without a branch.
 *   Apex Reference Guide, Limits Class: apexrefguide L220152-220176
 *   Apex Developer Guide, Per-Transaction Apex Limits: apexdev L19540-19580
 *
 * This class does NOT recover from a breach. System.LimitException cannot be caught, and
 * "when exceptions are uncatchable, catch blocks, as well as finally blocks if any, aren't
 * executed" (apexdev L39727-39728). Everything here runs BEFORE the expensive operation.
 *
 * Usage:
 *     if (LimitGuard.nearSoql(80)) {
 *         LogService.warn('OrderSync.enrich', 'degrading: ' + LimitGuard.snapshot());
 *         return partialResult;              // degrade, do not throw
 *     }
 *     List<Account> a = [SELECT Id FROM Account WHERE ...];
 */
public inherited sharing class LimitGuard {

    /** Default trip point. Override per call site; do not copy the number into a class. */
    public static final Integer DEFAULT_PCT = 80;

    /** One governor meter: consumed, ceiling, and the arithmetic nobody should retype. */
    public class Meter {
        public String name { get; private set; }
        public Long used { get; private set; }
        public Long ceiling { get; private set; }

        public Meter(String name, Long used, Long ceiling) {
            this.name = name;
            this.used = used == null ? 0 : used;
            this.ceiling = ceiling == null ? 0 : ceiling;
        }

        /** 0-100. Returns 0 when the platform reports no ceiling rather than dividing by zero. */
        public Integer pctUsed() {
            if (ceiling <= 0) {
                return 0;
            }
            return (Integer) ((used * 100) / ceiling);
        }

        public Long headroom() {
            return ceiling - used;
        }

        public String describe() {
            return name + '=' + used + '/' + ceiling;
        }
    }

    // ---------------------------------------------------------------- meters

    public static Meter cpu() {
        return new Meter('cpu', Limits.getCpuTime(), Limits.getLimitCpuTime());
    }

    public static Meter soql() {
        return new Meter('soql', Limits.getQueries(), Limits.getLimitQueries());
    }

    public static Meter heap() {
        return new Meter('heap', Limits.getHeapSize(), Limits.getLimitHeapSize());
    }

    public static Meter dml() {
        return new Meter('dml', Limits.getDmlStatements(), Limits.getLimitDmlStatements());
    }

    public static Meter dmlRows() {
        return new Meter('dmlRows', Limits.getDmlRows(), Limits.getLimitDmlRows());
    }

    public static Meter queryRows() {
        return new Meter('queryRows', Limits.getQueryRows(), Limits.getLimitQueryRows());
    }

    public static Meter callouts() {
        return new Meter('callouts', Limits.getCallouts(), Limits.getLimitCallouts());
    }

    public static Meter sosl() {
        return new Meter('sosl', Limits.getSoslQueries(), Limits.getLimitSoslQueries());
    }

    public static Meter queueableJobs() {
        return new Meter('queueable', Limits.getQueueableJobs(), Limits.getLimitQueueableJobs());
    }

    /** Every meter this class tracks, in a stable order. */
    public static List<Meter> allMeters() {
        return new List<Meter>{
            soql(), queryRows(), dml(), dmlRows(), cpu(), heap(),
            callouts(), sosl(), queueableJobs()
        };
    }

    // --------------------------------------------------------------- guards

    public static Boolean nearCpu(Integer pct) {
        return atOrAbove(cpu(), pct);
    }

    public static Boolean nearSoql(Integer pct) {
        return atOrAbove(soql(), pct);
    }

    public static Boolean nearHeap(Integer pct) {
        return atOrAbove(heap(), pct);
    }

    public static Boolean nearDml(Integer pct) {
        return atOrAbove(dml(), pct);
    }

    public static Boolean nearDmlRows(Integer pct) {
        return atOrAbove(dmlRows(), pct);
    }

    public static Boolean nearCallouts(Integer pct) {
        return atOrAbove(callouts(), pct);
    }

    /** True when ANY tracked meter has reached pct. Use before a fan-out, not in a loop. */
    public static Boolean nearAny(Integer pct) {
        for (Meter m : allMeters()) {
            if (atOrAbove(m, pct)) {
                return true;
            }
        }
        return false;
    }

    /** The meter closest to its ceiling — the thing to name in the log line. */
    public static Meter worst() {
        Meter leader = soql();
        for (Meter m : allMeters()) {
            if (m.pctUsed() > leader.pctUsed()) {
                leader = m;
            }
        }
        return leader;
    }

    /**
     * True when this many more of `unit` would not fit. Prefer this over nearX() when the
     * cost is known: needRoomFor('soql', 3) is exact where nearSoql(80) is a guess.
     */
    public static Boolean hasRoomFor(String meterName, Integer count) {
        for (Meter m : allMeters()) {
            if (m.name.equalsIgnoreCase(meterName)) {
                return m.headroom() >= (count == null ? 0 : count);
            }
        }
        throw new LimitGuardException('Unknown meter: ' + meterName);
    }

    // ------------------------------------------------------------- snapshot

    /**
     * Same `name=used/ceiling` shape LogService.limitsSnapshot() emits in
     * apex/debug-and-logging, so the two concatenate and one parser reads both.
     */
    public static String snapshot() {
        List<String> parts = new List<String>();
        for (Meter m : allMeters()) {
            parts.add(m.describe());
        }
        return String.join(parts, ';');
    }

    /** Machine-readable form for a Limit_Snapshot__c row or a test assertion. */
    public static Map<String, Integer> pctUsedByMeter() {
        Map<String, Integer> out = new Map<String, Integer>();
        for (Meter m : allMeters()) {
            out.put(m.name, m.pctUsed());
        }
        return out;
    }

    // ---------------------------------------------------------------- inner

    private static Boolean atOrAbove(Meter m, Integer pct) {
        Integer trip = (pct == null) ? DEFAULT_PCT : pct;
        if (trip < 0 || trip > 100) {
            throw new LimitGuardException('Threshold percent must be 0-100, got: ' + trip);
        }
        return m.pctUsed() >= trip;
    }

    public class LimitGuardException extends Exception {}
}
```

`force-app/main/default/classes/LimitGuard.cls-meta.xml` — identical in shape to
`templates/apex/ApplicationLogger.cls-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## `force-app/main/default/classes/OrgLimitsPoller.cls`

```apex
/**
 * OrgLimitsPoller — reads every org limit once per run, writes a Limit_Snapshot__c row per
 * limit, and raises through LogService when a limit passes its Limit_Threshold__mdt percent.
 *
 * Schedulable is deliberately thin: the interface method does nothing but call run().
 * (apexdev L16621-16623 — do the work in a separate class.) See apex/apex-scheduled-jobs
 * for cron expressions, System.abortJob, and the 100-scheduled-job ceiling (apexdev L16947).
 *
 * Two platform facts shape this class:
 *   1. Scheduled Apex gets SYNCHRONOUS governor limits (apexdev L19536), so 150 DML
 *      statements and 6 MB heap — hence the LimitGuard call before the insert.
 *   2. OrgLimit values "are updated asynchronously, in near-real-time"
 *      (apexrefguide L226215). These rows are a trend line, never a gate.
 */
public with sharing class OrgLimitsPoller implements Schedulable {

    /** A limit reading, decoupled from System.OrgLimit so tests can supply one. */
    public class Reading {
        public String name;
        public Integer value;
        public Integer maxValue;
        public Reading(String name, Integer value, Integer maxValue) {
            this.name = name;
            this.value = value;
            this.maxValue = maxValue;
        }
        public Integer pctUsed() {
            if (maxValue == null || maxValue <= 0) {
                return 0;
            }
            return (Integer) (((Long) value * 100) / maxValue);
        }
    }

    /**
     * Test seam. The Apex Stub API cannot mock OrgLimits: it is a System type and getAll()
     * is static, and both are on the "can't mock" list (apexdev L42205-42211). Injection is
     * the only way to assert the row shape without depending on the running org's usage.
     */
    @TestVisible
    private static List<Reading> injectedReadings;

    public void execute(SchedulableContext ctx) {
        run();
    }

    /** Returns the rows it inserted, so a caller (or a test) can assert on them. */
    public static List<Limit_Snapshot__c> run() {
        Datetime capturedAt = Datetime.now();
        String runId = System.Request.getCurrent().getRequestId();

        Map<String, Limit_Threshold__mdt> thresholds = activeThresholds();
        List<Limit_Snapshot__c> rows = new List<Limit_Snapshot__c>();
        List<String> breaches = new List<String>();

        for (Reading r : read()) {
            Limit_Threshold__mdt cfg = thresholds.get(r.name);
            if (cfg == null) {
                continue;                       // not configured = not monitored
            }
            Integer pct = r.pctUsed();
            String severity = classify(pct, cfg);
            rows.add(new Limit_Snapshot__c(
                Limit_Name__c = r.name,
                Consumed__c = r.value,
                Maximum__c = r.maxValue,
                Percent_Used__c = pct,
                Severity__c = severity,
                Captured_At__c = capturedAt,
                Poll_Run_Id__c = runId
            ));
            if (severity != 'OK') {
                breaches.add(severity + ' ' + r.name + ' ' + pct + '% (' + r.value + '/' + r.maxValue + ')');
            }
        }

        // Scheduled Apex runs under synchronous limits (apexdev L19536): one bulk insert,
        // and only if there is DML headroom left for it plus the logger's own flush.
        if (!rows.isEmpty() && LimitGuard.hasRoomFor('dml', 2)) {
            insert as user rows;
        } else if (!rows.isEmpty()) {
            LogService.warn('OrgLimitsPoller.run',
                'DML headroom exhausted; dropped ' + rows.size() + ' snapshot row(s). '
                + LimitGuard.snapshot());
        }

        if (!breaches.isEmpty()) {
            // One log line per run, not one per breach: alert volume is the thing that
            // kills an alert channel. The line carries every breach.
            LogService.warn('OrgLimitsPoller.run',
                breaches.size() + ' limit threshold breach(es): ' + String.join(breaches, ' | '));
        }
        LogService.flush();
        return rows;
    }

    /** Reads OrgLimits unless a test injected readings. */
    @TestVisible
    private static List<Reading> read() {
        if (injectedReadings != null) {
            return injectedReadings;
        }
        List<Reading> out = new List<Reading>();
        for (System.OrgLimit ol : OrgLimits.getAll()) {
            out.add(new Reading(ol.getName(), ol.getValue(), ol.getLimit()));
        }
        return out;
    }

    /**
     * Custom metadata reads do not count against the SOQL ceiling
     * (apexdev L19617-19618), so this is free even inside a limit-pressured transaction.
     */
    @TestVisible
    private static Map<String, Limit_Threshold__mdt> activeThresholds() {
        Map<String, Limit_Threshold__mdt> byName = new Map<String, Limit_Threshold__mdt>();
        for (Limit_Threshold__mdt t : Limit_Threshold__mdt.getAll().values()) {
            if (t.Is_Active__c == true && String.isNotBlank(t.Limit_Name__c)) {
                byName.put(t.Limit_Name__c, t);
            }
        }
        return byName;
    }

    @TestVisible
    private static String classify(Integer pct, Limit_Threshold__mdt cfg) {
        Decimal critical = cfg.Critical_Percent__c == null ? 90 : cfg.Critical_Percent__c;
        Decimal warning = cfg.Warning_Percent__c == null ? 70 : cfg.Warning_Percent__c;
        if (pct >= critical) {
            return 'CRITICAL';
        }
        if (pct >= warning) {
            return 'WARN';
        }
        return 'OK';
    }
}
```

Schedule it from anonymous Apex — the cron string and `System.schedule` signature are the
guide's own (`apexdev L16643`); hourly is a starting point, not a recommendation:

```apex
// Top of every hour. OrgLimit values lag by design (apexrefguide L226215), so polling
// faster than the refresh interval buys resolution the platform does not have.
System.schedule('OrgLimitsPoller hourly', '0 0 * * * ?', new OrgLimitsPoller());
```

---

## `force-app/main/default/objects/Limit_Snapshot__c/Limit_Snapshot__c.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Time series of org-limit consumption written by OrgLimitsPoller. One row per monitored limit per poll run. Trend data, not a gate: OrgLimit values update asynchronously in near-real-time.</description>
    <enableActivities>false</enableActivities>
    <enableHistory>false</enableHistory>
    <enableReports>true</enableReports>
    <label>Limit Snapshot</label>
    <pluralLabel>Limit Snapshots</pluralLabel>
    <nameField>
        <displayFormat>LIMSNAP-{0000000000}</displayFormat>
        <label>Snapshot Number</label>
        <type>AutoNumber</type>
    </nameField>
    <sharingModel>Private</sharingModel>
</CustomObject>
```

Fields, one file each under `objects/Limit_Snapshot__c/fields/`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Captured_At__c</fullName>
    <description>Poll timestamp. Without this column the object holds only a current value, which OrgLimits already gives you for free.</description>
    <externalId>false</externalId>
    <label>Captured At</label>
    <required>true</required>
    <type>DateTime</type>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Limit_Name__c</fullName>
    <description>OrgLimit.getName(), e.g. DailyApiRequests. Matches Limit_Threshold__mdt.Limit_Name__c.</description>
    <externalId>false</externalId>
    <label>Limit Name</label>
    <length>80</length>
    <required>true</required>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Consumed__c</fullName>
    <description>OrgLimit.getValue() - the usage value. Note the REST /limits resource returns Remaining instead, not consumed.</description>
    <externalId>false</externalId>
    <label>Consumed</label>
    <precision>18</precision>
    <scale>0</scale>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Maximum__c</fullName>
    <description>OrgLimit.getLimit() - the maximum allowed value at poll time. Stored per row because allocations change.</description>
    <externalId>false</externalId>
    <label>Maximum</label>
    <precision>18</precision>
    <scale>0</scale>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Percent_Used__c</fullName>
    <description>Stored, not a formula: Maximum__c changes between polls, so a formula would restate history every time the allocation moves.</description>
    <externalId>false</externalId>
    <label>Percent Used</label>
    <precision>5</precision>
    <scale>2</scale>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Severity__c</fullName>
    <description>Classification against Limit_Threshold__mdt at poll time.</description>
    <externalId>false</externalId>
    <label>Severity</label>
    <required>true</required>
    <type>Picklist</type>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>OK</fullName>
                <default>true</default>
                <label>OK</label>
            </value>
            <value>
                <fullName>WARN</fullName>
                <default>false</default>
                <label>Warning</label>
            </value>
            <value>
                <fullName>CRITICAL</fullName>
                <default>false</default>
                <label>Critical</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Poll_Run_Id__c</fullName>
    <description>System.Request.getCurrent().getRequestId() for the poll transaction. Groups one run's rows and joins to ApexLog.RequestIdentifier and to Event Monitoring REQUEST_ID.</description>
    <externalId>true</externalId>
    <label>Poll Run Id</label>
    <length>64</length>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

---

## `force-app/main/default/objects/Limit_Threshold__mdt/Limit_Threshold__mdt.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Per-limit alert thresholds read by OrgLimitsPoller. Custom metadata so the numbers are deployable and reviewable, and because CMDT reads do not consume the SOQL ceiling.</description>
    <label>Limit Threshold</label>
    <pluralLabel>Limit Thresholds</pluralLabel>
    <visibility>Public</visibility>
</CustomObject>
```

Fields under `objects/Limit_Threshold__mdt/fields/`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Limit_Name__c</fullName>
    <description>Exact OrgLimit.getName() key, e.g. DailyApiRequests, DataStorageMB, HourlyPublishedPlatformEvents. A typo here silently monitors nothing.</description>
    <externalId>false</externalId>
    <fieldManageability>DeveloperControlled</fieldManageability>
    <label>Limit Name</label>
    <length>80</length>
    <required>true</required>
    <type>Text</type>
    <unique>true</unique>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Warning_Percent__c</fullName>
    <externalId>false</externalId>
    <fieldManageability>DeveloperControlled</fieldManageability>
    <label>Warning Percent</label>
    <precision>3</precision>
    <scale>0</scale>
    <required>true</required>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Critical_Percent__c</fullName>
    <externalId>false</externalId>
    <fieldManageability>DeveloperControlled</fieldManageability>
    <label>Critical Percent</label>
    <precision>3</precision>
    <scale>0</scale>
    <required>true</required>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Is_Active__c</fullName>
    <description>Off switch that does not need a deploy of the poller. A limit with no active record is not polled.</description>
    <externalId>false</externalId>
    <fieldManageability>DeveloperControlled</fieldManageability>
    <label>Is Active</label>
    <type>Checkbox</type>
    <defaultValue>true</defaultValue>
</CustomField>
```

One record, `customMetadata/Limit_Threshold.DailyApiRequests.md-meta.xml` — the
`<values><field>/<value xsi:type="…">` shape is the Metadata API guide's own
(`api_meta L41595–41625`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>Daily API Requests</label>
    <protected>false</protected>
    <values>
        <field>Limit_Name__c</field>
        <value xsi:type="xsd:string">DailyApiRequests</value>
    </values>
    <values>
        <field>Warning_Percent__c</field>
        <value xsi:type="xsd:double">70</value>
    </values>
    <values>
        <field>Critical_Percent__c</field>
        <value xsi:type="xsd:double">90</value>
    </values>
    <values>
        <field>Is_Active__c</field>
        <value xsi:type="xsd:boolean">true</value>
    </values>
</CustomMetadata>
```

---

## `force-app/main/default/classes/LimitGuardTest.cls`

```apex
/**
 * Two things are asserted, and one is deliberately not.
 *
 * Asserted: that the guard flips from false to true when real consumption crosses the
 * percentage — measured, not stubbed. A test that asserts nearSoql(80) is false on an
 * empty transaction proves only that zero is less than eighty.
 *
 * Asserted: the poller's row shape, through the injection seam, because OrgLimits is a
 * System type with static methods and the Stub API can mock neither (apexdev L42205-42211).
 *
 * NOT asserted: that a LimitException is thrown and handled. It cannot be caught, and
 * catch and finally blocks both fail to run (apexdev L39727-39728). There is no assertion
 * to write. The regression net for real consumption is ApexTestResultLimits in CI, below.
 */
@IsTest
private class LimitGuardTest {

    @IsTest
    static void nearSoqlFlipsOnceTheCeilingIsApproached() {
        // startTest ADDS a limit context, it does not refresh one (apexdev L41442-41446),
        // so consumption measured inside the block starts from zero for these meters.
        Test.startTest();

        Assert.isFalse(LimitGuard.nearSoql(50),
            'A fresh limit context has issued no queries; ' + LimitGuard.snapshot());

        Integer ceiling = Limits.getLimitQueries();
        Integer target = (Integer) (ceiling * 0.55);
        for (Integer i = Limits.getQueries(); i < target; i++) {
            // A LIMIT 1 count query is the cheapest way to move the SOQL meter.
            Integer ignored = [SELECT COUNT() FROM Organization LIMIT 1];
        }

        Assert.isTrue(LimitGuard.nearSoql(50),
            'Past 50% of ' + ceiling + ' queries the guard must trip; ' + LimitGuard.snapshot());
        Assert.isFalse(LimitGuard.nearSoql(95),
            'Still well under 95%; ' + LimitGuard.snapshot());
        Test.stopTest();
    }

    @IsTest
    static void heapGuardTripsOnMeasuredAllocation() {
        Test.startTest();
        Assert.isFalse(LimitGuard.nearHeap(50), 'Nothing allocated yet: ' + LimitGuard.snapshot());

        Long ceiling = LimitGuard.heap().ceiling;
        List<String> ballast = new List<String>();
        while (Limits.getHeapSize() < (ceiling * 0.55)) {
            ballast.add('x'.repeat(100000));
        }

        Assert.isTrue(LimitGuard.nearHeap(50),
            'Heap past 50% of ' + ceiling + ' bytes: ' + LimitGuard.snapshot());
        Assert.isTrue(ballast.size() > 0, 'Ballast must be referenced or it may be collected');
        Test.stopTest();
    }

    @IsTest
    static void ceilingComesFromTheContextNotAConstant() {
        // The point of the class: no hardcoded 100 or 6000000 anywhere.
        Assert.areEqual(Limits.getLimitQueries(), (Integer) LimitGuard.soql().ceiling,
            'soql ceiling must be read from Limits.getLimitQueries()');
        Assert.areEqual(Limits.getLimitCpuTime(), (Integer) LimitGuard.cpu().ceiling,
            'cpu ceiling must be read from Limits.getLimitCpuTime()');
    }

    @IsTest
    static void percentOutOfRangeIsRejected() {
        try {
            LimitGuard.nearCpu(140);
            Assert.fail('A threshold of 140% should not be accepted');
        } catch (LimitGuard.LimitGuardException e) {
            Assert.isTrue(e.getMessage().contains('0-100'), 'Message must name the valid range');
        }
    }

    @IsTest
    static void snapshotCarriesEveryMeterAsNameEqualsUsedSlashCeiling() {
        String s = LimitGuard.snapshot();
        for (String meter : new List<String>{'soql', 'dml', 'cpu', 'heap', 'callouts', 'queueable'}) {
            Assert.isTrue(s.contains(meter + '='), meter + ' missing from snapshot: ' + s);
        }
        Assert.areEqual(9, s.split(';').size(), 'One segment per tracked meter: ' + s);
    }

    @IsTest
    static void pollerClassifiesAndShapesRowsFromInjectedReadings() {
        OrgLimitsPoller.injectedReadings = new List<OrgLimitsPoller.Reading>{
            new OrgLimitsPoller.Reading('DailyApiRequests', 9500, 10000),   // 95% -> CRITICAL
            new OrgLimitsPoller.Reading('DataStorageMB', 100, 1024),        // 9%  -> OK
            new OrgLimitsPoller.Reading('NotConfiguredLimit', 999, 1000)    // no CMDT -> skipped
        };

        Test.startTest();
        List<Limit_Snapshot__c> rows = OrgLimitsPoller.run();
        Test.stopTest();

        Map<String, Limit_Snapshot__c> byName = new Map<String, Limit_Snapshot__c>();
        for (Limit_Snapshot__c r : rows) {
            byName.put(r.Limit_Name__c, r);
        }
        Assert.isFalse(byName.containsKey('NotConfiguredLimit'),
            'A limit with no active Limit_Threshold__mdt record must not be written');

        Limit_Snapshot__c api = byName.get('DailyApiRequests');
        Assert.isNotNull(api, 'DailyApiRequests must be polled; ship the CMDT record with the class');
        Assert.areEqual('CRITICAL', api.Severity__c, '9500 of 10000 is past the 90% critical mark');
        Assert.areEqual(95, api.Percent_Used__c, 'Percent is stored, not recomputed at read time');
        Assert.areEqual(9500, api.Consumed__c, 'Consumed is getValue(), not remaining');
        Assert.areEqual(10000, api.Maximum__c, 'Maximum is getLimit() at poll time');
        Assert.isNotNull(api.Captured_At__c, 'Without the timestamp the object is not a time series');
        Assert.isNotNull(api.Poll_Run_Id__c, 'Run id joins the rows of one poll');
    }

    @IsTest
    static void readingHandlesAZeroCeilingWithoutDividingByZero() {
        OrgLimitsPoller.Reading r = new OrgLimitsPoller.Reading('Weird', 5, 0);
        Assert.areEqual(0, r.pctUsed(), 'A zero ceiling must report 0%, not throw');
    }
}
```

---

## `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Limit_Snapshot__c</members>
        <members>Limit_Threshold__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Limit_Snapshot__c.Captured_At__c</members>
        <members>Limit_Snapshot__c.Consumed__c</members>
        <members>Limit_Snapshot__c.Limit_Name__c</members>
        <members>Limit_Snapshot__c.Maximum__c</members>
        <members>Limit_Snapshot__c.Percent_Used__c</members>
        <members>Limit_Snapshot__c.Poll_Run_Id__c</members>
        <members>Limit_Snapshot__c.Severity__c</members>
        <members>Limit_Threshold__mdt.Critical_Percent__c</members>
        <members>Limit_Threshold__mdt.Is_Active__c</members>
        <members>Limit_Threshold__mdt.Limit_Name__c</members>
        <members>Limit_Threshold__mdt.Warning_Percent__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Limit_Threshold.DailyApiRequests</members>
        <name>CustomMetadata</name>
    </types>
    <types>
        <members>LimitGuard</members>
        <members>LimitGuardTest</members>
        <members>OrgLimitsPoller</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy Order

1. **`apex/debug-and-logging` first.** `OrgLimitsPoller` calls `LogService`, which delegates
   to `templates/apex/ApplicationLogger.cls` and needs `Application_Log__c`
   (`templates/apex/custom_objects/`) and `Logger_Setting__mdt` (`templates/apex/cmdt/`).
   Deploying the poller into an org without them fails compilation, not at run time.
2. `Limit_Snapshot__c` object + its seven fields, and `Limit_Threshold__mdt` + its four
   fields. Objects and fields go in one deploy; a field cannot precede its object.
3. The `Limit_Threshold` custom metadata **records**. A record cannot deploy before its
   type's fields exist. Creating them requires the Customize Application permission
   (`api_meta L41466–41467`).
4. `LimitGuard`, then `OrgLimitsPoller`, then `LimitGuardTest`.
5. Schedule the job **last**, from anonymous Apex. Do not schedule from a post-install
   script during the same deploy — a class with an active scheduled job cannot be updated
   through the UI (`apexdev L16598–16600`).

```bash
sf project deploy start \
  --source-dir force-app/main/default/objects/Limit_Snapshot__c \
  --source-dir force-app/main/default/objects/Limit_Threshold__mdt \
  --target-org myOrg

sf project deploy start --source-dir force-app/main/default/customMetadata --target-org myOrg

sf project deploy start --manifest manifest/package.xml --target-org myOrg

sf apex run test --tests LimitGuardTest --result-format human --wait 10 --target-org myOrg
```

Retrieve what is already there before you write over it:

```bash
sf project retrieve start --metadata "CustomObject:Limit_Snapshot__c" --target-org myOrg
```

## Verification

After the first scheduled run, one row per configured limit, newest first:

```soql
SELECT Limit_Name__c, Consumed__c, Maximum__c, Percent_Used__c,
       Severity__c, Captured_At__c, Poll_Run_Id__c
FROM   Limit_Snapshot__c
WHERE  Captured_At__c = LAST_N_HOURS:2
ORDER  BY Percent_Used__c DESC
```

The job itself is a `CronTrigger` row — `TimesTriggered` and `NextFireTime` are the guide's
own verification query (`apexdev L16667–16669`):

```soql
SELECT Id, CronJobDetail.Name, CronJobDetail.JobType, State,
       TimesTriggered, NextFireTime, PreviousFireTime
FROM   CronTrigger
WHERE  CronJobDetail.Name = 'OrgLimitsPoller hourly'
```

A trend query that answers "is this limit climbing?" rather than "what is it now?" — the
question the object exists for:

```soql
SELECT Limit_Name__c, Captured_At__c, Percent_Used__c
FROM   Limit_Snapshot__c
WHERE  Limit_Name__c = 'DailyApiRequests'
AND    Captured_At__c = LAST_N_DAYS:14
ORDER  BY Captured_At__c
```

## Post-Transaction Horizon: Catching Limit Regressions in CI

`ApexTestResultLimits` records what each test method consumed. It is available in API
version 37.0 and later, and "in API version 49.0 and later, users must have the View Setup
and Configuration permission to access this object" (Object Reference,
`object_reference L32558–32568`). Query it after a CI test run and fail the build when a
method's consumption jumps:

```bash
sf apex run test --test-level RunLocalTests --wait 30 --target-org ci --result-format json \
  > test-run.json

sf data query --target-org ci --result-format csv --query "
  SELECT ApexTestResult.ApexClass.Name, ApexTestResult.MethodName,
         LimitContext, Cpu, Soql, QueryRows, Dml, DmlRows, Callouts, Sosl,
         Email, AsyncCalls, MobilePush, LimitExceptions
  FROM   ApexTestResultLimits
  WHERE  ApexTestResult.ApexTestRunResultId = '\$RUN_ID'
  ORDER  BY Cpu DESC" > limits-current.csv

# Diff against the committed baseline; a method whose Cpu or Soql grew beyond the
# tolerance is a limit regression even though the test still passes.
python3 scripts/check_apex_limits_monitoring.py --manifest-dir force-app/main/default --strict
```

Three traps make this gate silently useless if you skip them, all from the same Usage
paragraph (`object_reference L32693–32702`):

- The object "captures the limits used **between the `Test.startTest()` and
  `Test.stopTest()` methods. If `startTest()` and `stopTest()` aren't called, limits usage
  isn't captured**." A test without the block reports nothing, and nothing looks like zero.
- "The associated test method must be run **asynchronously**." A synchronous run produces no
  rows, so `sf apex run test` must not be forced synchronous for the gate to have input.
- "Limits for asynchronous Apex operations (batch, scheduled, future, and queueable) that
  are called within test methods **aren't captured**", and "limits are captured only for the
  default namespace." Your Batch `execute` consumption never reaches this table.

There is no `Heap` column and no `PublishImmediateDml` column on `ApexTestResultLimits`
(`object_reference L32570–32690` lists the complete field set: `ApexTestResultId`,
`AsyncCalls`, `Callouts`, `Cpu`, `Dml`, `DmlRows`, `Email`, `LimitContext`,
`LimitExceptions`, `MobilePush`, `QueryRows`, `Soql`, `Sosl`). Heap regressions must be
caught by an assertion inside the test on `Limits.getHeapSize()`, not by this gate.

## Post-Mortem Horizon: What Survives an Uncatchable Breach

When `System.LimitException` fires, neither a `catch` nor a `finally` runs
(`apexdev L39727–39728`), so nothing in the failing transaction can log its own death.
Three surfaces record it from outside:

| Surface | What it gives you | Grounding |
|---|---|---|
| `BatchApexErrorEvent` | Record IDs in scope, exception type, message, stack trace — fired for "uncatchable Apex exceptions such as LimitExceptions". Requires `implements Database.RaisesPlatformEvents` | `apexdev L17853–17864` |
| Transaction Finalizer on a Queueable | `FinalizerContext.getResult()` returns `UNHANDLED_EXCEPTION`; the finalizer runs in its own transaction with its own limits | `apexdev L16296–16303`; see `apex/apex-transaction-finalizers` |
| `EventLogFile` `ApexUnexpectedException` | `EXCEPTION_CATEGORY` names the exact meter: `LimitException: CpuTime`, `LimitException: HeapSize`, `LimitException: Queries`, `LimitException: QueryRows`, `LimitException: DmlStatements`, `LimitException: Callouts` (API v57.0+) | `object_reference L114265–114290` |

The Event Monitoring query, once the log file is downloadable — `EventType` values and the
`LogFile` field are from the Object Reference (`object_reference L112511–112520`):

```soql
SELECT Id, EventType, LogDate, LogFileLength, LogFile
FROM   EventLogFile
WHERE  EventType IN ('ApexUnexpectedException', 'ApexExecution')
AND    LogDate = LAST_N_DAYS:7
ORDER  BY LogDate DESC
```
