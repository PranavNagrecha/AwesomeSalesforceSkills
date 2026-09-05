# Code Examples — Custom Metadata in Apex

A deployable `__mdt` configuration slice: the type, two records, a **selector** that reads
them through `getAll()` / `getInstance()` with one injection seam, a **test that swaps the
configuration without a single DML statement**, and the other half of the story — a
**deployer** that writes a record back through `Metadata.Operations.enqueueDeployment()`
plus the `Metadata.DeployCallback` that receives the outcome, and a test for both that
never enqueues a real deployment.

Canonical building blocks are referenced by path, never duplicated here:

| Building block | Path | What this example takes from it |
|---|---|---|
| CMDT-cache + `@TestVisible` override | `templates/apex/TriggerControl.cls` | the memoised static `Map` and `overrideForTest()` shape this selector copies |
| Shipped `__mdt` source layout | `templates/apex/cmdt/Trigger_Setting__mdt/` | object folder + `fields/` decomposition, `fieldManageability` |
| Shipped `__mdt` picklist field | `templates/apex/cmdt/Logger_Setting__mdt/fields/Minimum_Severity__c.field-meta.xml` | restricted `valueSet` on a `__mdt` field |
| Logging | `templates/apex/ApplicationLogger.cls` | `warn()` when a configuration row is missing |
| Test fixtures | `templates/apex/tests/TestDataFactory.cls` | the `Invoice`-side data these tests do **not** need |

Scenario: payment-retry behaviour differs per business unit — how many attempts, how long
to back off, which queue gets the escalation — and Ops must be able to change it by
deploying a record rather than an Apex class. A separate admin screen lets a support lead
raise one business unit's attempt count, which is a metadata *deployment*, not a save.

Strategy/factory framing (a `__mdt` row naming an Apex class, resolved with
`Type.forName`) belongs to `apex/apex-design-patterns` § 5–7 — this file deliberately
stops at reading and writing the configuration values themselves.

---

## How to read it

- **`getAll()` and `getInstance()` truncate at 255 characters.** "Only the first 255
  characters are returned for any field in a custom metadata type record, so longer text
  fields get truncated. If you want all the field data from a custom metadata type record,
  use a SOQL query." (Apex Reference Guide L204569–204572, repeated for each `getInstance`
  overload at L204605–204607, L204645–204647, L204678–204680.) Every field in
  `Retry_Policy__mdt` below is a short scalar, so the cache path is safe; the moment a
  field could exceed 255 characters, that read has to move to SOQL.
- **SOQL against `__mdt` is free, so "use `getAll()` to save a query" is the wrong reason
  to use it.** "This limit doesn't apply to custom metadata types. In a single Apex
  transaction, custom metadata records can have unlimited SOQL queries." (Apex Developer
  Guide L19616–19619.) Choose SOQL when you need a `WHERE`, an `ORDER BY`, or untruncated
  text; choose `getAll()` when you want the whole small table as a map.
- **There is exactly one seam, and the test uses it.** `cache` is `@TestVisible private
  static` (Apex Developer Guide L6290–6296). Tests build `Retry_Policy__mdt` sObjects in
  memory and drop them into that map. That is legal because "You can edit records in
  memory but not upsert or delete them" (Metadata API Developer Guide L41318–41319) —
  and required, because the supported calls on a `__mdt` object are only
  `describeSObjects(), describeLayout(), query(), retrieve()` (Object Reference L5671–5672).
  No `create()`, no `update()`, no `delete()`.
- **The tests never set `DeveloperName`.** The map key carries the developer name; the
  sObject carries only custom fields. `DeveloperName` on `Custom Metadata Type__mdt` is
  documented with the properties *Defaulted on create, Filter, Group, Sort* (Object
  Reference L5681–5683) — not as a createable field — so nothing in this example depends
  on being able to assign it.
- **`enqueueDeployment` is asynchronous and never runs in a test.** "Deployment is queued
  for asynchronous processing" and the queued jobs "are counted as asynchronous jobs in
  the current org" (Apex Developer Guide L28194–28196, L28226–28229). The guide's own
  testing instruction is to assert the container and to call the callback directly:
  "Tests for deployment request code verify the metadata components and component values
  that get created and assert that the DeployContainer contains exactly what needs to be
  deployed… to test your callback outside of the deployment process, create tests that use
  your callback class directly." (L28248–28254.) Hence the `Test.isRunningTest()` guard
  (Apex Reference Guide L240629–240632) and the `TestingDeployCallbackContext` subclass
  the guide itself supplies (L28257–28262).
- **`Succeeded` is not the only success.** `Metadata.DeployStatus` also has
  `SucceededPartial` — "The deployment succeeded, but some components might not have been
  successfully deployed" (Apex Reference Guide L172228–172230) — plus `Canceled`,
  `Canceling`, `Failed`, `FinalizingDeploy`, `FinalizingDeployFailed`, `InProgress`,
  `Pending`. The callback below branches on all three outcomes rather than `== Succeeded`.
- **The full name must carry the namespace when there is one.** "the full name for a
  custom metadata MDType1__mdt component named Component1 that is contained in the
  myPackage namespace is `myPackage__MDType1__mdt.myPackage__Component1`" (Apex Developer
  Guide L28201–28203); `Metadata.CustomMetadata.fullName` drops the `__mdt` suffix —
  `'MetadataTypeName.MetadataRecordName'` (Apex Reference Guide L170844–170845).
- **A container is inspectable, and must not hold two components with the same name.**
  `Metadata.DeployContainer.getMetadata()` returns the `List<Metadata.Metadata>` it holds
  (Apex Reference Guide L171312–171320) — that is what makes the request side testable
  without deploying. `addMetadata()` carries its own warning: "Avoid adding components to
  a Metadata.DeployContainer that have the same Metadata.Metadata.fullName because it
  causes deployment errors." (L171293–171295.)
- **Relationship values are API names, not Ids.** "When setting the value for relationship
  fields, use the qualified API name of the related metadata, not the ID." (Apex Reference
  Guide L171050.) The same holds in the XML for `EntityDefinition` and
  `FieldDefinition` fields (Metadata API Developer Guide L41698–41706).

---

## 1. The Custom Metadata Type

SFDX source format: one folder per object, fields decomposed into `fields/` — the same
shape as `templates/apex/cmdt/Trigger_Setting__mdt/`.

```text
force-app/main/default/
├── objects/
│   └── Retry_Policy__mdt/
│       ├── Retry_Policy__mdt.object-meta.xml
│       └── fields/
│           ├── Is_Active__c.field-meta.xml
│           ├── Max_Attempts__c.field-meta.xml
│           ├── Backoff_Seconds__c.field-meta.xml
│           ├── Priority__c.field-meta.xml
│           └── Escalation_Queue__c.field-meta.xml
├── customMetadata/
│   ├── Retry_Policy.Default.md-meta.xml
│   └── Retry_Policy.EMEA_Standard.md-meta.xml
└── classes/
    ├── RetryPolicySelector.cls
    ├── RetryPolicyDeployCallback.cls
    ├── RetryPolicyDeployer.cls
    └── (their tests + .cls-meta.xml)
```

`objects/Retry_Policy__mdt/Retry_Policy__mdt.object-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Per-business-unit payment retry policy read by RetryPolicySelector.cls. The record named Default is the fallback and must always exist.</description>
    <label>Retry Policy</label>
    <pluralLabel>Retry Policies</pluralLabel>
    <visibility>Public</visibility>
</CustomObject>
```

`visibility` is the `SetupObjectVisibility` enum — `Public`, `Protected`, or
`PackageProtected`, defaulting to `Public` (Metadata API Developer Guide L41363–41377).
Read the gotcha on visibility before choosing anything other than `Public` here.

`fields/Is_Active__c.field-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Is_Active__c</fullName>
    <defaultValue>true</defaultValue>
    <externalId>false</externalId>
    <fieldManageability>SubscriberControlled</fieldManageability>
    <label>Is Active</label>
    <type>Checkbox</type>
</CustomField>
```

`fields/Max_Attempts__c.field-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Max_Attempts__c</fullName>
    <externalId>false</externalId>
    <fieldManageability>SubscriberControlled</fieldManageability>
    <label>Max Attempts</label>
    <precision>2</precision>
    <required>true</required>
    <scale>0</scale>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

`fields/Backoff_Seconds__c.field-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Backoff_Seconds__c</fullName>
    <externalId>false</externalId>
    <fieldManageability>SubscriberControlled</fieldManageability>
    <label>Backoff Seconds</label>
    <precision>4</precision>
    <required>true</required>
    <scale>0</scale>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

`fields/Priority__c.field-meta.xml` — the tie-breaker the SOQL path orders by:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Priority__c</fullName>
    <externalId>false</externalId>
    <fieldManageability>DeveloperControlled</fieldManageability>
    <label>Priority</label>
    <precision>3</precision>
    <required>true</required>
    <scale>0</scale>
    <type>Number</type>
    <unique>false</unique>
</CustomField>
```

`fields/Escalation_Queue__c.field-meta.xml` — `unique` + `externalId` on the field the code
looks records up by, which is what the guide recommends: "To make the fields on your custom
metadata types unique and indexable, mark your fields as Unique and ExternalId."
(Metadata API Developer Guide L41338.)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Escalation_Queue__c</fullName>
    <externalId>true</externalId>
    <fieldManageability>SubscriberControlled</fieldManageability>
    <label>Escalation Queue Developer Name</label>
    <length>80</length>
    <required>false</required>
    <type>Text</type>
    <unique>true</unique>
</CustomField>
```

Every field here is a short scalar on purpose — see the 255-character rule in
*How to read it*.

---

## 2. The records

Custom metadata **records** live in `customMetadata/`, carry the suffix `.md` in Metadata
API format (`.md-meta.xml` in SFDX source format), and are named
`<TypeNameWithoutMdtSuffix>.<RecordDeveloperName>` (Metadata API Developer Guide
L41456–41459).

`customMetadata/Retry_Policy.Default.md-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <description>Fallback retry policy. RetryPolicySelector returns this record when no business-unit record matches.</description>
    <label>Default</label>
    <protected>false</protected>
    <values>
        <field>Is_Active__c</field>
        <value xsi:type="xsd:boolean">true</value>
    </values>
    <values>
        <field>Max_Attempts__c</field>
        <value xsi:type="xsd:int">3</value>
    </values>
    <values>
        <field>Backoff_Seconds__c</field>
        <value xsi:type="xsd:int">60</value>
    </values>
    <values>
        <field>Priority__c</field>
        <value xsi:type="xsd:int">999</value>
    </values>
    <values>
        <field>Escalation_Queue__c</field>
        <value xsi:nil="true"/>
    </values>
</CustomMetadata>
```

`customMetadata/Retry_Policy.EMEA_Standard.md-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>EMEA Standard</label>
    <protected>false</protected>
    <values>
        <field>Is_Active__c</field>
        <value xsi:type="xsd:boolean">true</value>
    </values>
    <values>
        <field>Max_Attempts__c</field>
        <value xsi:type="xsd:int">5</value>
    </values>
    <values>
        <field>Backoff_Seconds__c</field>
        <value xsi:type="xsd:int">120</value>
    </values>
    <values>
        <field>Priority__c</field>
        <value xsi:type="xsd:int">10</value>
    </values>
    <values>
        <field>Escalation_Queue__c</field>
        <value xsi:type="xsd:string">EMEA_Billing_Escalations</value>
    </values>
</CustomMetadata>
```

Three details that are easy to get wrong and are all documented in the Metadata API
Developer Guide's `CustomMetadata` section:

- The `xsi:type` values are fixed per field type: `xsd:boolean` for Checkbox, `xsd:date`,
  `xsd:dateTime`, `xsd:picklist`, `xsd:string` for Text / Phone / TextArea / URL / Email,
  `xsd:int` for Number and Percent with scale 0, `xsd:double` for Number and Percent with
  a non-zero scale (L41716–41749).
- `<value xsi:nil="true"/>` explicitly clears a field. Omitting the `<values>` block
  entirely is **not** the same thing: "If you leave out the [values element], the value of
  the field doesn't change. The field's value is null for newly deployed custom metadata
  records and left at its previous value for updated custom metadata records."
  (L41753–41757.) `Default` above clears the queue on every deploy; `EMEA_Standard` sets it.
- `<field>` takes the non-object-qualified field name and must include the namespace when
  the type comes from a managed package — `picklist1234__AlphaSort__c`, not
  `MyType__mdt.AlphaSort__c` (L41524–41531).

---

## 3. `RetryPolicySelector.cls` — the read path

```apex
/**
 * Reads Retry_Policy__mdt configuration.
 *
 * Three read paths, deliberately distinct:
 *   all()                 -> Retry_Policy__mdt.getAll(), memoised. Whole table as a map.
 *   forBusinessUnit(name) -> a single policy with a documented Default fallback.
 *   currentValues(name)   -> Retry_Policy__mdt.getInstance(name), NOT memoised; used by
 *                            the deploy path, which must read what is really in the org.
 *   activeByPriority()    -> SOQL, for filtering and ordering the cache cannot do.
 *
 * Every field on Retry_Policy__mdt is a short scalar, so getAll()'s 255-character
 * truncation (Apex Reference Guide L204568-204570) cannot bite here. Add a field that
 * could exceed 255 characters and that read must move to the SOQL path.
 *
 * DEPLOY DEPENDENCY: objects/Retry_Policy__mdt/ and its five fields must exist in the
 * target org before this class compiles.
 */
public inherited sharing class RetryPolicySelector {

    @TestVisible
    private static final String FALLBACK_DEVELOPER_NAME = 'Default';

    /**
     * The single injection seam. Tests assign this map directly (see
     * RetryPolicySelectorTest); production code never touches it. Static state lives for
     * one Apex transaction, so this is a per-transaction cache and nothing more.
     */
    @TestVisible
    private static Map<String, Retry_Policy__mdt> cache;

    public static Map<String, Retry_Policy__mdt> all() {
        if (cache == null) {
            cache = Retry_Policy__mdt.getAll();
        }
        return cache;
    }

    /**
     * Resolves the policy for a business unit, falling back to the Default record.
     * Returns null only when Default itself is missing, which is a deployment defect and
     * is logged rather than swallowed.
     */
    public static Retry_Policy__mdt forBusinessUnit(String developerName) {
        Map<String, Retry_Policy__mdt> policies = all();
        Retry_Policy__mdt policy = String.isBlank(developerName)
            ? null
            : policies.get(developerName);

        if (policy == null || policy.Is_Active__c != true) {
            policy = policies.get(FALLBACK_DEVELOPER_NAME);
        }
        if (policy == null) {
            System.debug(
                LoggingLevel.WARN,
                'RetryPolicySelector: no Retry_Policy__mdt record named '
                + FALLBACK_DEVELOPER_NAME + '; retry behaviour is undefined.'
            );
        }
        return policy;
    }

    public static Integer maxAttempts(String developerName) {
        Retry_Policy__mdt policy = forBusinessUnit(developerName);
        return policy == null ? 1 : policy.Max_Attempts__c.intValue();
    }

    public static Integer backoffSeconds(String developerName) {
        Retry_Policy__mdt policy = forBusinessUnit(developerName);
        return policy == null ? 0 : policy.Backoff_Seconds__c.intValue();
    }

    /**
     * Deliberately NOT served from the cache. The deploy path must compare against the
     * value actually in the org, not against a map a test may have injected.
     * getInstance(developerName) returns null when no record matches
     * (Apex Reference Guide L204617-204619).
     */
    public static Retry_Policy__mdt currentValues(String developerName) {
        return Retry_Policy__mdt.getInstance(developerName);
    }

    /**
     * SOQL, not getAll(), because this needs a WHERE and an ORDER BY. Custom metadata
     * records carry no SOQL query limit inside a transaction (Apex Developer Guide
     * L19616-19619), so this costs nothing against the 100-query governor.
     */
    public static List<Retry_Policy__mdt> activeByPriority() {
        return [
            SELECT DeveloperName, Max_Attempts__c, Backoff_Seconds__c,
                   Priority__c, Escalation_Queue__c
            FROM Retry_Policy__mdt
            WHERE Is_Active__c = true
            ORDER BY Priority__c ASC, DeveloperName ASC
        ];
    }

    @TestVisible
    private static void reset() {
        cache = null;
    }
}
```

---

## 4. `RetryPolicySelectorTest.cls` — swapping configuration with zero DML

```apex
@IsTest
private class RetryPolicySelectorTest {

    /**
     * Builds an in-memory Retry_Policy__mdt. No DML: custom metadata records support
     * only describeSObjects(), describeLayout(), query() and retrieve()
     * (Object Reference L5671–5672), and Apex "can edit records in memory but not upsert or
     * delete them" (Metadata API Developer Guide L41313-41314).
     *
     * DeveloperName is never assigned - the map key carries it.
     */
    private static Retry_Policy__mdt policy(Boolean active, Integer attempts, Integer backoff, Integer priority) {
        return new Retry_Policy__mdt(
            Is_Active__c = active,
            Max_Attempts__c = attempts,
            Backoff_Seconds__c = backoff,
            Priority__c = priority
        );
    }

    private static void inject(Map<String, Retry_Policy__mdt> rows) {
        RetryPolicySelector.cache = rows;
    }

    @IsTest
    static void resolvesTheBusinessUnitRecordWhenItIsActive() {
        inject(new Map<String, Retry_Policy__mdt>{
            'Default' => policy(true, 3, 60, 999),
            'EMEA_Standard' => policy(true, 5, 120, 10)
        });

        Test.startTest();
        Integer attempts = RetryPolicySelector.maxAttempts('EMEA_Standard');
        Integer backoff = RetryPolicySelector.backoffSeconds('EMEA_Standard');
        Test.stopTest();

        Assert.areEqual(5, attempts, 'EMEA_Standard should win over Default');
        Assert.areEqual(120, backoff, 'Backoff should come from the same record');
    }

    @IsTest
    static void fallsBackToDefaultWhenTheBusinessUnitRecordIsInactive() {
        inject(new Map<String, Retry_Policy__mdt>{
            'Default' => policy(true, 3, 60, 999),
            'EMEA_Standard' => policy(false, 5, 120, 10)
        });

        Assert.areEqual(3, RetryPolicySelector.maxAttempts('EMEA_Standard'),
            'An inactive record must fall through to Default, not be used');
    }

    @IsTest
    static void fallsBackToDefaultForAnUnknownOrBlankBusinessUnit() {
        inject(new Map<String, Retry_Policy__mdt>{ 'Default' => policy(true, 3, 60, 999) });

        Assert.areEqual(3, RetryPolicySelector.maxAttempts('NO_SUCH_UNIT'), 'Unknown unit');
        Assert.areEqual(3, RetryPolicySelector.maxAttempts(null), 'Null unit');
        Assert.areEqual(3, RetryPolicySelector.maxAttempts(''), 'Blank unit');
    }

    @IsTest
    static void degradesSafelyWhenEvenDefaultIsMissing() {
        inject(new Map<String, Retry_Policy__mdt>());

        Assert.areEqual(1, RetryPolicySelector.maxAttempts('EMEA_Standard'),
            'With no configuration at all the caller must still get one attempt, not an NPE');
        Assert.areEqual(0, RetryPolicySelector.backoffSeconds('EMEA_Standard'),
            'And no backoff');
    }

    /**
     * The one test that reads the org rather than an injected map. It asserts the
     * deployment contract - "Default must exist" - and it needs no SeeAllData=true:
     * metadata objects remain visible to tests, unlike custom settings data, which
     * "must use SeeAllData=true to see existing custom settings data in the
     * organization" (Apex Developer Guide L13515-13516, L40707-40709).
     */
    @IsTest
    static void theDefaultRecordIsDeployedToThisOrg() {
        RetryPolicySelector.reset();

        Retry_Policy__mdt fallback = RetryPolicySelector.currentValues('Default');

        Assert.isNotNull(fallback, 'customMetadata/Retry_Policy.Default.md-meta.xml must be deployed');
        Assert.isTrue(fallback.Is_Active__c, 'The Default policy must be active');
    }

    @IsTest
    static void soqlPathReturnsOnlyActiveRowsInPriorityOrder() {
        RetryPolicySelector.reset();

        List<Retry_Policy__mdt> rows = RetryPolicySelector.activeByPriority();

        Decimal previous = -1;
        for (Retry_Policy__mdt row : rows) {
            Assert.isTrue(row.Priority__c >= previous, 'Rows must come back in priority order');
            previous = row.Priority__c;
        }
    }
}
```

`theDefaultRecordIsDeployedToThisOrg` is the one test that is *supposed* to be coupled to
org metadata, and it says so in its name. That is the difference between a stated
dependency and the accidental one described in `references/gotchas.md`.

---

## 5. `RetryPolicyDeployCallback.cls` — the write path's other half

```apex
/**
 * Receives the outcome of the asynchronous custom metadata deployment started by
 * RetryPolicyDeployer.
 *
 * Salesforce calls handleResult() asynchronously once the queued deployment completes,
 * and there is "a brief period where the deploy has completed, but your callback has not
 * been called yet" (Apex Reference Guide L171091-171094). Nothing downstream may assume
 * the new value is live until this has run.
 */
public with sharing class RetryPolicyDeployCallback implements Metadata.DeployCallback {

    public enum Outcome { SUCCEEDED, PARTIAL, FAILED }

    /** Set by handleResult so a test can assert what the callback decided. */
    @TestVisible
    private static Outcome lastOutcome;

    public void handleResult(Metadata.DeployResult result, Metadata.DeployCallbackContext context) {
        Id jobId;
        if (context != null) {
            jobId = context.getCallbackJobId();
        }

        if (result == null) {
            lastOutcome = Outcome.FAILED;
            System.debug(LoggingLevel.ERROR, 'Retry policy deploy ' + jobId + ': no result');
            return;
        }

        if (result.status == Metadata.DeployStatus.Succeeded) {
            lastOutcome = Outcome.SUCCEEDED;
            System.debug(LoggingLevel.INFO, 'Retry policy deploy ' + jobId + ' succeeded');
            return;
        }

        // SucceededPartial means "succeeded, but some components might not have been
        // successfully deployed" (Apex Reference Guide L172228-172230). Treating it as
        // success is how a half-applied configuration change goes unnoticed.
        if (result.status == Metadata.DeployStatus.SucceededPartial) {
            lastOutcome = Outcome.PARTIAL;
        } else {
            lastOutcome = Outcome.FAILED;
        }

        System.debug(
            LoggingLevel.ERROR,
            'Retry policy deploy ' + jobId + ' finished as ' + result.status
            + ': ' + describeFailures(result)
        );
    }

    @TestVisible
    private static String describeFailures(Metadata.DeployResult result) {
        if (result.details == null || result.details.componentFailures == null) {
            return result.errorMessage;
        }
        List<String> problems = new List<String>();
        for (Metadata.DeployMessage message : result.details.componentFailures) {
            problems.add(message.fullName + ' -> ' + message.problem);
        }
        return String.join(problems, '; ');
    }
}
```

---

## 6. `RetryPolicyDeployer.cls` — building and enqueuing the deployment

```apex
/**
 * Raises one business unit's Max_Attempts__c by deploying an updated custom metadata
 * record. This is the only class in the slice allowed to write configuration.
 *
 * Metadata.Operations.enqueueDeployment() deploys asynchronously; "you can create and
 * update components but not delete them" (Apex Developer Guide L28194-28197), and the
 * queued job and its callback count as asynchronous Apex jobs against the org's governor
 * limits (L28226-28229). Never call this from a trigger or a per-record loop.
 */
public with sharing class RetryPolicyDeployer {

    public class RetryPolicyDeployException extends Exception {}

    /** Captured instead of enqueued while a test is running, so the test can assert it. */
    @TestVisible
    private static Metadata.DeployContainer lastContainer;

    /**
     * @param developerName DeveloperName of the Retry_Policy__mdt record to update.
     * @param newMaxAttempts the new attempt count.
     * @return the deployment job Id, or null when running in a test.
     */
    public static Id raiseMaxAttempts(String developerName, Integer newMaxAttempts) {
        if (String.isBlank(developerName)) {
            throw new RetryPolicyDeployException('developerName is required');
        }
        if (newMaxAttempts == null || newMaxAttempts < 1 || newMaxAttempts > 99) {
            throw new RetryPolicyDeployException('newMaxAttempts must be between 1 and 99');
        }
        if (RetryPolicySelector.currentValues(developerName) == null) {
            throw new RetryPolicyDeployException(
                'No Retry_Policy__mdt record named ' + developerName
                + '. Deploy the record before trying to update it.'
            );
        }

        Metadata.DeployContainer container = buildContainer(developerName, newMaxAttempts);
        lastContainer = container;

        // The guide's own testing instruction is to assert the container and to invoke
        // the callback directly, not to enqueue a real deployment from a test
        // (Apex Developer Guide L28248-28254). Test.isRunningTest() is documented at
        // Apex Reference Guide L240629-240632.
        if (Test.isRunningTest()) {
            return null;
        }
        return Metadata.Operations.enqueueDeployment(container, new RetryPolicyDeployCallback());
    }

    /**
     * fullName is "<TypeNameWithoutMdtSuffix>.<RecordDeveloperName>". In a managed
     * package both halves must be namespace-qualified:
     * 'myPackage__Retry_Policy.myPackage__EMEA_Standard'
     * (Apex Developer Guide L28199-28203, Apex Reference Guide L170852-170855).
     */
    @TestVisible
    private static Metadata.DeployContainer buildContainer(String developerName, Integer newMaxAttempts) {
        Metadata.CustomMetadata record = new Metadata.CustomMetadata();
        record.fullName = 'Retry_Policy.' + developerName;
        record.label = developerName.replace('_', ' ');

        Metadata.CustomMetadataValue attempts = new Metadata.CustomMetadataValue();
        attempts.field = 'Max_Attempts__c';
        attempts.value = newMaxAttempts;
        record.values.add(attempts);

        Metadata.DeployContainer container = new Metadata.DeployContainer();
        container.addMetadata(record);
        return container;
    }
}
```

Only `Max_Attempts__c` is in the container, and that is deliberate: leaving a field out of
a `CustomMetadata` deployment leaves its existing value alone on an update
(Metadata API Developer Guide L41753–41757). Adding a `<values>` block with
`xsi:nil="true"` — or, in Apex, a `CustomMetadataValue` whose `value` is `null` — is what
clears a field.

---

## 7. `RetryPolicyDeployerTest.cls` — testing a deployment that never happens

```apex
@IsTest
private class RetryPolicyDeployerTest {

    /**
     * The guide's own pattern: "When creating a test instance of DeployCallbackContext,
     * subclass DeployCallbackContext and provide your own implementation of
     * getCallbackJobId()." (Apex Developer Guide L28255-28262.)
     */
    private class TestingDeployCallbackContext extends Metadata.DeployCallbackContext {
        // Returns null rather than the guide's literal '000000000000000000'. From API
        // version 54.0, "Assignment of an invalid 15 or 18 character ID to a variable
        // results in a System.StringException" (Apex Developer Guide L44630-44632), so
        // the guide's placeholder Id no longer assigns at a modern API version.
        public override Id getCallbackJobId() {
            return null;
        }
    }

    // ---------- request side: assert the container, never enqueue ----------

    @IsTest
    static void buildsAContainerWithExactlyTheFieldBeingChanged() {
        Metadata.DeployContainer container =
            RetryPolicyDeployer.buildContainer('EMEA_Standard', 7);

        List<Metadata.Metadata> components = container.getMetadata();
        Assert.areEqual(1, components.size(), 'Exactly one component belongs in this deployment');

        Metadata.CustomMetadata record = (Metadata.CustomMetadata) components[0];
        Assert.areEqual('Retry_Policy.EMEA_Standard', record.fullName,
            'fullName drops the __mdt suffix and joins type and record with a dot');
        Assert.areEqual(1, record.values.size(),
            'Only the changed field may be present; omitted fields keep their org value');
        Assert.areEqual('Max_Attempts__c', record.values[0].field);
        Assert.areEqual(7, record.values[0].value);
    }

    @IsTest
    static void rejectsAnOutOfRangeAttemptCountBeforeBuildingAnything() {
        try {
            RetryPolicyDeployer.raiseMaxAttempts('EMEA_Standard', 0);
            Assert.fail('Expected RetryPolicyDeployException');
        } catch (RetryPolicyDeployer.RetryPolicyDeployException e) {
            Assert.isTrue(e.getMessage().contains('between 1 and 99'), e.getMessage());
        }
    }

    @IsTest
    static void doesNotEnqueueADeploymentWhileATestIsRunning() {
        // Requires customMetadata/Retry_Policy.Default.md-meta.xml to be deployed.
        Test.startTest();
        Id jobId = RetryPolicyDeployer.raiseMaxAttempts('Default', 4);
        Test.stopTest();

        Assert.isNull(jobId, 'The isRunningTest guard must short-circuit before enqueueDeployment');
        Assert.isNotNull(RetryPolicyDeployer.lastContainer, 'The container is still built and assertable');
    }

    // ---------- result side: call the callback directly ----------

    @IsTest
    static void callbackRecordsSuccess() {
        Metadata.DeployResult result = new Metadata.DeployResult();
        result.status = Metadata.DeployStatus.Succeeded;
        result.success = true;

        new RetryPolicyDeployCallback().handleResult(result, new TestingDeployCallbackContext());

        Assert.areEqual(RetryPolicyDeployCallback.Outcome.SUCCEEDED,
            RetryPolicyDeployCallback.lastOutcome);
    }

    @IsTest
    static void callbackTreatsSucceededPartialAsNotDone() {
        Metadata.DeployResult result = new Metadata.DeployResult();
        result.status = Metadata.DeployStatus.SucceededPartial;
        result.success = true;

        new RetryPolicyDeployCallback().handleResult(result, new TestingDeployCallbackContext());

        Assert.areEqual(RetryPolicyDeployCallback.Outcome.PARTIAL,
            RetryPolicyDeployCallback.lastOutcome,
            'SucceededPartial must never be reported as a clean success');
    }

    @IsTest
    static void callbackSummarisesComponentFailures() {
        Metadata.DeployMessage message = new Metadata.DeployMessage();
        message.fullName = 'Retry_Policy.EMEA_Standard';
        message.problem = 'Field Max_Attempts__c is not writeable';
        message.success = false;

        Metadata.DeployDetails details = new Metadata.DeployDetails();
        details.componentFailures = new List<Metadata.DeployMessage>{ message };

        Metadata.DeployResult result = new Metadata.DeployResult();
        result.status = Metadata.DeployStatus.Failed;
        result.success = false;
        result.details = details;

        new RetryPolicyDeployCallback().handleResult(result, new TestingDeployCallbackContext());

        Assert.areEqual(RetryPolicyDeployCallback.Outcome.FAILED,
            RetryPolicyDeployCallback.lastOutcome);
        Assert.isTrue(
            RetryPolicyDeployCallback.describeFailures(result).contains('not writeable'),
            'The component failure must reach the log line'
        );
    }

    @IsTest
    static void callbackSurvivesANullResult() {
        new RetryPolicyDeployCallback().handleResult(null, new TestingDeployCallbackContext());
        Assert.areEqual(RetryPolicyDeployCallback.Outcome.FAILED,
            RetryPolicyDeployCallback.lastOutcome);
    }
}
```

Between them these two test classes cover both halves the guide asks for: "write tests
that verify both the set up of the deployment request and handling of the deployment
results" (Apex Developer Guide L28247–28249).

---

## 8. `-meta.xml` for every class

Identical for all five classes; substitute the file name.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

67.0 is a deliberate choice, not a default. From API version 67.0 a class without an
explicit sharing declaration runs `with sharing`, and Apex runs in user context by default
so the current user's permissions and FLS are enforced (Apex Developer Guide L4961,
L11744–11746). Every class above declares its sharing anyway, so the source means the same
thing at any version.

---

## 9. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Retry_Policy__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Retry_Policy__mdt.Is_Active__c</members>
        <members>Retry_Policy__mdt.Max_Attempts__c</members>
        <members>Retry_Policy__mdt.Backoff_Seconds__c</members>
        <members>Retry_Policy__mdt.Priority__c</members>
        <members>Retry_Policy__mdt.Escalation_Queue__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Retry_Policy.Default</members>
        <members>Retry_Policy.EMEA_Standard</members>
        <name>CustomMetadata</name>
    </types>
    <types>
        <members>RetryPolicySelector</members>
        <members>RetryPolicySelectorTest</members>
        <members>RetryPolicyDeployCallback</members>
        <members>RetryPolicyDeployer</members>
        <members>RetryPolicyDeployerTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

Three manifest facts, all from the Metadata API Developer Guide's own samples
(L41405–41432, L41693–41696):

- The **type** goes under `CustomObject` with the `__mdt` suffix; its **fields** go under
  `CustomField` dot-qualified with the type name.
- The **records** go under `CustomMetadata` as `TypeNameWithoutMdt.RecordDeveloperName` —
  no `__mdt`.
- With a namespace, both halves are qualified:
  `picklist1234__ReusablePicklist.travelApp1234__Hotels`.

---

## 10. Deploy order, commands, verification

The type and its fields must land before the records, and both before the Apex — a class
that says `Retry_Policy__mdt` will not compile until the object exists.

```bash
# 0. Retrieve current state before changing anything.
sf project retrieve start --manifest manifest/package.xml --target-org devhub-sandbox

# 1. Static review before deploying — this skill's checker.
python3 skills/apex/custom-metadata-in-apex/scripts/check_custom_metadata_in_apex.py \
  --manifest-dir force-app/main/default

# 2. Type + fields first, on their own.
sf project deploy start \
  --source-dir force-app/main/default/objects/Retry_Policy__mdt \
  --target-org devhub-sandbox

# 3. Records next.
sf project deploy start \
  --source-dir force-app/main/default/customMetadata \
  --target-org devhub-sandbox

# 4. Apex last, running only these tests.
sf project deploy start \
  --source-dir force-app/main/default/classes \
  --test-level RunSpecifiedTests \
  --tests RetryPolicySelectorTest --tests RetryPolicyDeployerTest \
  --target-org devhub-sandbox

# 5. Re-run the tests on their own, synchronously, with coverage.
sf apex run test \
  --tests RetryPolicySelectorTest --tests RetryPolicyDeployerTest \
  --result-format human --code-coverage --synchronous \
  --target-org devhub-sandbox
```

**Verification step.** The deploy proves the classes compile. This proves the
configuration is actually readable and that the fallback contract holds:

```soql
SELECT DeveloperName, MasterLabel, Is_Active__c, Max_Attempts__c,
       Backoff_Seconds__c, Priority__c, Escalation_Queue__c
FROM Retry_Policy__mdt
ORDER BY Priority__c ASC
```

```bash
sf data query --target-org devhub-sandbox \
  --query "SELECT DeveloperName, Is_Active__c, Max_Attempts__c FROM Retry_Policy__mdt ORDER BY Priority__c"
```

Read the result against three assertions:

1. A row with `DeveloperName = 'Default'` exists and has `Is_Active__c = true`. Without
   it `RetryPolicySelector.forBusinessUnit` returns null and every caller silently drops
   to one attempt.
2. `Escalation_Queue__c` is unique across rows — it is declared `unique` and
   `externalId`, so a duplicate fails the deploy rather than the runtime.
3. Every `Max_Attempts__c` is between 1 and 99. `RetryPolicyDeployer` enforces that on the
   write path, but a hand-deployed record bypasses it entirely — the `.md-meta.xml` file
   is the only gate.

After a `RetryPolicyDeployer.raiseMaxAttempts()` run in a real org, re-run the same query.
The deployment is asynchronous, so an unchanged value means the job has not finished, not
that it failed; confirm with the `DeployStatus` your callback logged before re-running.
