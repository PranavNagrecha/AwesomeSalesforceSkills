# Code Examples — Apex Design Patterns

A complete, deployable pattern stack for one object: a trigger that is one line, a
handler that only dispatches, a **domain** that only mutates in-memory records, a
**selector** that owns every SOQL statement, a **service** that owns the unit of work,
and a **Custom Metadata-driven strategy factory** that swaps behaviour without an Apex
deployment. Then the test class that proves all three risky paths — 200 records, every
strategy row, and the rollback.

The canonical base classes are referenced by path, never duplicated:

| Building block | Path | What this example takes from it |
|---|---|---|
| Trigger dispatch | `templates/apex/TriggerHandler.cls` | `run()`, `dispatch()`, the per-handler depth counter, `skipOnce()` |
| Kill switch | `templates/apex/TriggerControl.cls` | `Trigger_Setting__mdt` activation, `TriggerControl_BypassAll` |
| Domain base | `templates/apex/BaseDomain.cls` | `records` / `oldMap`, `isChanged()`, `recordIds()` |
| Service base | `templates/apex/BaseService.cls` | `beginTransaction()`, `rollbackTransaction()`, `logAndRethrow()`, `ServiceException` |
| Selector base | `templates/apex/BaseSelector.cls` | `userMode()` default, `assertNotNull()`, `SelectorException` |
| Logging | `templates/apex/ApplicationLogger.cls` | `warn()` / `error()` into `Application_Log__c` |
| CRUD + FLS | `templates/apex/SecurityUtils.cls` | `stripInaccessibleForUpdate/Insert` at the DML edge |
| Test fixtures | `templates/apex/tests/TestDataFactory.cls` | `createAccounts`, `createCases` |
| Bulk shape | `templates/apex/tests/BulkTestPattern.cls` | the 200-record assertion shape |
| CMDT for `TriggerControl` | `templates/apex/cmdt/Trigger_Setting__mdt/` | deploy this before `TriggerControl.cls` compiles |

Scenario: when a Case's `Status` moves to `Escalated`, mark it escalated, raise its
priority, and create a follow-up Task — and do it differently depending on
`Case.Origin`, with the per-origin behaviour configured as data.

---

## How to read it

- **The trigger is one line.** Everything the trigger body would normally hold — context
  branching, the recursion guard, the kill switch — is already in `TriggerHandler.run()`.
  Re-implementing it in `CaseTrigger` is the single most common way this pattern is
  broken.
- **Every `override` carries `protected`.** In API version 65.0 and later an `abstract`
  or `override` method without `protected`, `public`, or `global` fails to compile with
  *"Abstract methods require at least one of the following: global, public, protected"*
  (Apex Developer Guide L3359–3364). The base class methods are `protected virtual`, so
  the subclass must say `protected override`.
- **Inside a class, `Trigger.new` is typed `List<SObject>`.** The downcasts
  `(List<Case>) Trigger.new` and `(Map<Id, Case>) Trigger.oldMap` in the handler are load
  bearing; the domain constructor then upcasts `List<Case>` to `BaseDomain`'s
  `List<SObject>`, exactly as `BaseDomain.cls`'s own header example does. For the
  `oldMap` the example copies key-by-key rather than relying on map covariance — one loop
  is cheaper than a compile-time surprise.
- **Sharing is declared on every class, including the inner ones.** Inner classes do not
  adopt the container's sharing mode (L4931–4932). `CaseSelector` is `inherited sharing`
  because it is never an entry point; the service and handler are `with sharing`. Note
  that at API 67.0+ an undeclared class runs `with sharing` anyway (L4961) and Apex runs
  in user context by default (L11744–11746) — declare it anyway so the source says what
  it means at any API version.
- **`with sharing` is not CRUD/FLS.** Sharing declarations do not enforce object-level
  access or field-level security (L4925–4926). That is why the selector queries
  `userMode()` and the service pipes both DML lists through `SecurityUtils`.
- **The savepoint sits at the public service method, not around each DML.** Every
  `Database.setSavepoint()` and `Database.rollback()` costs one of the 150 DML
  *statements* per transaction (L8691, L19554) — though neither counts against the DML
  *row* limit at API 60.0 and later (L8695–8696).
- **`rollbackTransaction(sp)` runs before `logAndRethrow(...)`.** `ApplicationLogger`
  inserts an `Application_Log__c` row; if you log inside the `try` the rollback deletes
  your own audit trail, because a rollback discards every DML statement issued after the
  savepoint (L8682–8684).
- **The strategy is resolved by name, so the class must be reachable by name.**
  `Type.forName` retrieves the type of **public and global** classes only — not private
  ones, even when the context user has access (Apex Reference Guide L241920–241922) — and
  `newInstance()` takes no arguments (L242303), so the class needs an accessible
  no-argument constructor. `PhoneCaseEscalationStrategy` therefore declares no
  constructor at all and gets the implicit public no-argument one.
- **The factory always has a fallback.** A `Case_Escalation_Strategy__mdt` row can name a
  class that was renamed or deleted; `Type.forName` then returns `null`, and an
  unguarded `newInstance()` on it is a null dereference at run time, not a deploy-time
  error.
- **The CMDT lookup is free but truncated.** Custom metadata records have no SOQL query
  limit inside a transaction (Apex Developer Guide L19614–19615), but `getAll()` returns
  only the first 255 characters of any field (Apex Reference Guide L204568–204572). An
  Apex class name fits; a long JSON config blob would not.

---

## 1. The trigger and the handler

```apex
trigger CaseTrigger on Case (before insert, before update, after insert, after update) {
    new CaseTriggerHandler().run();
}
```

```apex
/**
 * Adapter only. No SOQL, no DML, no business rules.
 * Dispatch, the recursion depth counter, skipOnce() and the TriggerControl
 * kill switch all live in templates/apex/TriggerHandler.cls.
 */
public with sharing class CaseTriggerHandler extends TriggerHandler {

    // `protected override` is mandatory from API 65.0 (Apex Developer Guide L3359-3364).
    protected override void beforeInsert() {
        domain().applyIntakeDefaults();
    }

    protected override void beforeUpdate() {
        domain().rejectEscalationWithoutSubject();
    }

    protected override void afterUpdate() {
        Set<Id> needEscalation = domain().idsNewlyMarkedEscalated();
        if (!needEscalation.isEmpty()) {
            new CaseEscalationService().escalate(needEscalation);
        }
    }

    /**
     * Trigger.new is typed List<SObject> when read from a class rather than
     * from the trigger body, so the downcast is required.
     */
    private CaseDomain domain() {
        return new CaseDomain(
            (List<Case>) Trigger.new,
            Trigger.oldMap == null ? null : (Map<Id, Case>) Trigger.oldMap
        );
    }
}
```

---

## 2. The domain — in-memory rules only, bulk-safe by construction

```apex
/**
 * Extends templates/apex/BaseDomain.cls.
 *
 * Contract inherited from the base class: a domain NEVER issues SOQL, DML, or a
 * callout, and every method must be safe for a 200-record collection. Everything
 * here is a single pass over `records` with no per-record query.
 */
public with sharing class CaseDomain extends BaseDomain {

    @TestVisible private static final String STATUS_ESCALATED = 'Escalated';
    @TestVisible private static final String DEFAULT_ORIGIN   = 'Web';
    @TestVisible private static final String DEFAULT_PRIORITY = 'Medium';

    public CaseDomain(List<Case> records) {
        super(records);
    }

    public CaseDomain(List<Case> records, Map<Id, Case> oldMap) {
        super(records, asSObjectMap(oldMap));
    }

    /** before insert — one pass, no query. */
    public void applyIntakeDefaults() {
        for (Case theCase : cases()) {
            if (String.isBlank(theCase.Origin))   { theCase.Origin = DEFAULT_ORIGIN; }
            if (String.isBlank(theCase.Priority)) { theCase.Priority = DEFAULT_PRIORITY; }
        }
    }

    /** before update — addError marks the individual row, leaving the rest of the batch to save. */
    public void rejectEscalationWithoutSubject() {
        for (Case theCase : cases()) {
            if (!becameEscalated(theCase)) { continue; }
            if (String.isBlank(theCase.Subject)) {
                // Record-level addError, not theCase.Subject.addError(...): the field
                // variant dereferences the value, which is null here. The guide's own
                // field example uses safe navigation for exactly that reason
                // (Apex Developer Guide L2495-2499).
                theCase.addError('Give the case a subject before escalating it.');
            }
        }
    }

    /** after update — the only thing the handler hands to the service. */
    public Set<Id> idsNewlyMarkedEscalated() {
        Set<Id> ids = new Set<Id>();
        for (Case theCase : cases()) {
            if (becameEscalated(theCase) && theCase.IsEscalated != true) {
                ids.add(theCase.Id);
            }
        }
        return ids;
    }

    private Boolean becameEscalated(Case theCase) {
        // isChanged() comes from BaseDomain and reads oldMap; it returns false on insert.
        return STATUS_ESCALATED.equalsIgnoreCase(theCase.Status)
            && isChanged(theCase, Case.Status);
    }

    private List<Case> cases() {
        return (List<Case>) records;
    }

    /**
     * BaseDomain stores Map<Id, SObject>. Copying key-by-key is unambiguous at
     * compile time; do not rely on map covariance here.
     */
    private static Map<Id, SObject> asSObjectMap(Map<Id, Case> source) {
        Map<Id, SObject> out = new Map<Id, SObject>();
        if (source == null) { return out; }
        for (Id key : source.keySet()) {
            out.put(key, source.get(key));
        }
        return out;
    }
}
```

---

## 3. The selector — the only class in the stack allowed to say `SELECT`

```apex
/**
 * Extends templates/apex/BaseSelector.cls, which is `abstract inherited sharing`
 * and supplies userMode() / systemMode() / assertNotNull().
 *
 * One named field list, one method per retrieval intent. There is deliberately
 * no selectAll() and no selectEverything().
 */
public inherited sharing class CaseSelector extends BaseSelector {

    @TestVisible
    private static final String BASE_FIELDS =
        'Id, CaseNumber, AccountId, ContactId, Subject, Status, Priority, ' +
        'Origin, Reason, IsEscalated, IsClosed, OwnerId';

    /** Rows the escalation service may act on. Already-escalated rows are excluded here,
     *  which is what makes a second pass through the trigger a no-op. */
    public List<Case> selectEscalatableByIds(Set<Id> caseIds) {
        assertNotNull(caseIds, 'caseIds');
        return (List<Case>) Database.queryWithBinds(
            'SELECT ' + BASE_FIELDS + ' FROM Case ' +
            'WHERE Id IN :caseIds AND IsClosed = false AND IsEscalated = false ' +
            'ORDER BY CreatedDate ASC',
            new Map<String, Object>{ 'caseIds' => caseIds },
            userMode()
        );
    }

    /** A different intent, so a different method — not an extra optional argument. */
    public List<Case> selectOpenByAccountIds(Set<Id> accountIds) {
        assertNotNull(accountIds, 'accountIds');
        return (List<Case>) Database.queryWithBinds(
            'SELECT ' + BASE_FIELDS + ' FROM Case ' +
            'WHERE AccountId IN :accountIds AND IsClosed = false ' +
            'ORDER BY Priority, CreatedDate ASC',
            new Map<String, Object>{ 'accountIds' => accountIds },
            userMode()
        );
    }
}
```

---

## 4. The service — one savepoint, one unit of work

```apex
/**
 * Extends templates/apex/BaseService.cls.
 *
 * Owns: sequence, transaction boundary, DML, security enforcement, logging.
 * Owns nothing else — no queries of its own, no per-record business rules.
 */
public with sharing class CaseEscalationService extends BaseService {

    private final CaseSelector selector;
    private final CaseEscalationStrategyFactory strategies;

    /** Production entry point. Wires the real collaborators. */
    public CaseEscalationService() {
        this(new CaseSelector(), new CaseEscalationStrategyFactory());
    }

    /** Injection seam. No Test.isRunningTest() anywhere in this class. */
    @TestVisible
    private CaseEscalationService(CaseSelector selector, CaseEscalationStrategyFactory strategies) {
        this.selector = selector;
        this.strategies = strategies;
    }

    public void escalate(Set<Id> caseIds) {
        if (caseIds == null || caseIds.isEmpty()) { return; }

        Savepoint sp = beginTransaction();
        try {
            List<Case> cases = selector.selectEscalatableByIds(caseIds);
            if (cases.isEmpty()) { return; }

            List<Case> toUpdate  = new List<Case>();
            List<Task> followUps = new List<Task>();

            for (Case theCase : cases) {
                // One strategy lookup per row, but the factory memoises per origin,
                // so N rows of the same origin cost one Type.forName call.
                Task followUp = strategies.forOrigin(theCase.Origin).escalate(theCase);
                toUpdate.add(theCase);
                if (followUp != null) { followUps.add(followUp); }
            }

            // The update re-enters CaseTrigger; skipOnce() consumes exactly one
            // invocation (templates/apex/TriggerHandler.cls). The selector's
            // IsEscalated = false filter is the belt to that pair of braces.
            TriggerHandler.skipOnce('CaseTriggerHandler');
            update SecurityUtils.stripInaccessibleForUpdate(toUpdate);

            if (!followUps.isEmpty()) {
                insert SecurityUtils.stripInaccessibleForInsert(followUps);
            }
            commitTransaction();
        } catch (Exception e) {
            // Order matters: roll back FIRST. ApplicationLogger inserts a row, and
            // a rollback discards every DML issued after the savepoint
            // (Apex Developer Guide L8682-8684) — including the log row.
            rollbackTransaction(sp);
            logAndRethrow('CaseEscalationService.escalate', e);
        }
    }
}
```

---

## 5. The strategy interface and its implementations

```apex
/**
 * Interface methods need no access modifier — they are always public or global
 * depending on the interface's own visibility (Apex Developer Guide L4173-4175).
 *
 * Implementations MUST be public top-level classes with an accessible no-argument
 * constructor, because CaseEscalationStrategyFactory reaches them through
 * Type.forName(...).newInstance().
 */
public interface ICaseEscalationStrategy {
    /**
     * Mutates the in-memory Case and returns a follow-up Task, or null for none.
     * Implementations MUST NOT query, perform DML, or call out.
     */
    Task escalate(Case theCase);
}
```

```apex
public with sharing class PhoneCaseEscalationStrategy implements ICaseEscalationStrategy {

    // No constructor is declared, so the implicit public no-argument constructor
    // exists and Type.newInstance() can reach it. Adding a constructor with
    // arguments here would remove it (Apex Developer Guide L3582-3584).

    public Task escalate(Case theCase) {
        theCase.IsEscalated = true;
        theCase.Priority    = 'High';
        return new Task(
            WhatId       = theCase.Id,
            OwnerId      = UserInfo.getUserId(),   // never theCase.OwnerId: a queue cannot own a Task
            Subject      = 'Call back escalated case ' + theCase.CaseNumber + ': ' + theCase.Subject,
            Status       = 'Not Started',
            Priority     = 'High',
            ActivityDate = Date.today()
        );
    }
}
```

```apex
public with sharing class WebCaseEscalationStrategy implements ICaseEscalationStrategy {
    public Task escalate(Case theCase) {
        theCase.IsEscalated = true;
        theCase.Priority    = 'High';
        return new Task(
            WhatId       = theCase.Id,
            OwnerId      = UserInfo.getUserId(),
            Subject      = 'Email escalated case ' + theCase.CaseNumber,
            Status       = 'Not Started',
            Priority     = 'Normal',
            ActivityDate = Date.today().addDays(1)
        );
    }
}
```

```apex
/**
 * The fallback. The factory returns this when no Custom Metadata row matches the
 * origin, when the named class does not resolve, or when it resolves to something
 * that does not implement the interface.
 */
public with sharing class DefaultCaseEscalationStrategy implements ICaseEscalationStrategy {
    public Task escalate(Case theCase) {
        theCase.IsEscalated = true;
        theCase.Priority    = 'High';
        return null;
    }
}
```

---

## 6. The factory — Custom Metadata + `Type.forName`, memoised for the transaction

```apex
/**
 * Reads Case_Escalation_Strategy__mdt and instantiates the named Apex class.
 *
 * Two static caches, both with a reset hook:
 *   classNameByOrigin  — the CMDT rows, read once per transaction
 *   instanceByOrigin   — one strategy object per origin, so Type.forName is called
 *                        at most once per origin per transaction
 *
 * Statics live exactly one Apex transaction and are reset across transaction
 * boundaries (Apex Developer Guide L3736-3738), so this is a per-transaction
 * cache and never a cross-request one.
 */
public with sharing class CaseEscalationStrategyFactory {

    @TestVisible private static final String DEFAULT_CLASS = 'DefaultCaseEscalationStrategy';

    @TestVisible private static Map<String, ICaseEscalationStrategy> instanceByOrigin =
        new Map<String, ICaseEscalationStrategy>();
    @TestVisible private static Map<String, String> classNameByOrigin;

    public ICaseEscalationStrategy forOrigin(String origin) {
        String key = String.isBlank(origin) ? '' : origin.toLowerCase();
        if (instanceByOrigin.containsKey(key)) {
            return instanceByOrigin.get(key);
        }
        ICaseEscalationStrategy strategy = build(classNameFor(key));
        instanceByOrigin.put(key, strategy);
        return strategy;
    }

    private ICaseEscalationStrategy build(String className) {
        // Type.forName resolves public and global classes only, never private ones,
        // and returns null when nothing matches (Apex Reference Guide L241920-241922,
        // L242076-242082). A call can also cause the class to be compiled (L241925).
        Type resolved = Type.forName(className);
        if (resolved == null) {
            ApplicationLogger.warn(
                'CaseEscalationStrategyFactory',
                'No public Apex class named "' + className + '"; using ' + DEFAULT_CLASS
            );
            return new DefaultCaseEscalationStrategy();
        }

        // newInstance() takes no arguments (Apex Reference Guide L242303), so the
        // class must expose an accessible no-argument constructor.
        Object instance = resolved.newInstance();
        if (!(instance instanceof ICaseEscalationStrategy)) {
            ApplicationLogger.warn(
                'CaseEscalationStrategyFactory',
                className + ' does not implement ICaseEscalationStrategy; using ' + DEFAULT_CLASS
            );
            return new DefaultCaseEscalationStrategy();
        }
        return (ICaseEscalationStrategy) instance;
    }

    private String classNameFor(String key) {
        Map<String, String> byOrigin = classNames();
        return byOrigin.containsKey(key) ? byOrigin.get(key) : DEFAULT_CLASS;
    }

    /**
     * getAll() returns only the first 255 characters of any field
     * (Apex Reference Guide L204568-204572). An Apex class name fits comfortably;
     * a long configuration blob would be silently truncated, so do not put one here.
     * Custom metadata records carry no SOQL query limit in a transaction
     * (Apex Developer Guide L19614-19615), so this read is effectively free.
     */
    @TestVisible
    private static Map<String, String> classNames() {
        if (classNameByOrigin != null) { return classNameByOrigin; }
        classNameByOrigin = new Map<String, String>();
        for (Case_Escalation_Strategy__mdt row : Case_Escalation_Strategy__mdt.getAll().values()) {
            if (row.Is_Active__c != true) { continue; }
            if (String.isBlank(row.Case_Origin__c) || String.isBlank(row.Apex_Class__c)) { continue; }
            classNameByOrigin.put(row.Case_Origin__c.toLowerCase(), row.Apex_Class__c);
        }
        return classNameByOrigin;
    }

    /**
     * Reset hook. Mandatory for any static mutable collection: a rollback does NOT
     * revert statics (Apex Developer Guide L8692-8693), and a test that sets one
     * would otherwise leak into the next assertion inside the same transaction.
     */
    @TestVisible
    private static void reset() {
        instanceByOrigin = new Map<String, ICaseEscalationStrategy>();
        classNameByOrigin = null;
    }
}
```

---

## 7. The Custom Metadata Type and its rows

`force-app/main/default/objects/Case_Escalation_Strategy__mdt/Case_Escalation_Strategy__mdt.object-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Maps a Case Origin to the Apex class implementing ICaseEscalationStrategy. A missing or inactive row falls back to DefaultCaseEscalationStrategy.</description>
    <label>Case Escalation Strategy</label>
    <pluralLabel>Case Escalation Strategies</pluralLabel>
    <visibility>Public</visibility>
</CustomObject>
```

`.../fields/Case_Origin__c.field-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Case_Origin__c</fullName>
    <externalId>false</externalId>
    <fieldManageability>DeveloperControlled</fieldManageability>
    <label>Case Origin</label>
    <length>40</length>
    <required>true</required>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

`.../fields/Apex_Class__c.field-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Apex_Class__c</fullName>
    <description>Public top-level Apex class implementing ICaseEscalationStrategy. Must have an accessible no-argument constructor.</description>
    <externalId>false</externalId>
    <fieldManageability>DeveloperControlled</fieldManageability>
    <label>Apex Class</label>
    <length>255</length>
    <required>true</required>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

`.../fields/Is_Active__c.field-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Is_Active__c</fullName>
    <defaultValue>true</defaultValue>
    <externalId>false</externalId>
    <fieldManageability>DeveloperControlled</fieldManageability>
    <label>Is Active</label>
    <type>Checkbox</type>
</CustomField>
```

Records go in the `customMetadata` folder with a `.md` suffix, named
`<TypeNameWithoutMdt>.<RecordName>.md` (Metadata API Developer Guide L41455–41460).
`force-app/main/default/customMetadata/Case_Escalation_Strategy.Phone.md-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>Phone</label>
    <protected>false</protected>
    <values>
        <field>Case_Origin__c</field>
        <value xsi:type="xsd:string">Phone</value>
    </values>
    <values>
        <field>Apex_Class__c</field>
        <value xsi:type="xsd:string">PhoneCaseEscalationStrategy</value>
    </values>
    <values>
        <field>Is_Active__c</field>
        <value xsi:type="xsd:boolean">true</value>
    </values>
</CustomMetadata>
```

`.../customMetadata/Case_Escalation_Strategy.Web.md-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>Web</label>
    <protected>false</protected>
    <values>
        <field>Case_Origin__c</field>
        <value xsi:type="xsd:string">Web</value>
    </values>
    <values>
        <field>Apex_Class__c</field>
        <value xsi:type="xsd:string">WebCaseEscalationStrategy</value>
    </values>
    <values>
        <field>Is_Active__c</field>
        <value xsi:type="xsd:boolean">true</value>
    </values>
</CustomMetadata>
```

---

## 8. The test class — 200 records, every strategy, and the rollback

```apex
/**
 * Three paths, because these are the three that break in production:
 *   1. 200 records through the real trigger (bulk safety)
 *   2. every Custom Metadata row resolving to its class, plus the fallback
 *   3. the rollback path — a failure in the second DML undoing the first
 *
 * Fixtures come from templates/apex/tests/TestDataFactory.cls; the 200-record
 * shape follows templates/apex/tests/BulkTestPattern.cls.
 */
@IsTest
private class CaseEscalationServiceTest {

    private static final Integer BULK_SIZE = 200;

    @TestSetup
    static void makeData() {
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        insert accounts;

        List<Case> cases = TestDataFactory.createCases(
            BULK_SIZE,
            accounts[0].Id,
            new Map<String, Object>{
                'Origin'   => 'Phone',
                'Status'   => 'New',
                'Priority' => 'Medium'
            }
        );
        insert cases;
    }

    @IsTest
    static void escalates_two_hundred_cases_in_one_trigger_pass() {
        List<Case> cases = [SELECT Id, Status FROM Case];
        Assert.areEqual(BULK_SIZE, cases.size(), 'Fixture did not create the full batch.');
        for (Case theCase : cases) {
            theCase.Status = 'Escalated';
        }

        Test.startTest();
        // If any layer had SOQL or DML inside a loop, this single statement would
        // exceed the 100 SOQL / 150 DML statement limits (Apex Developer Guide
        // L19544, L19554) and the test would fail with a LimitException.
        update cases;
        Test.stopTest();

        Assert.areEqual(
            BULK_SIZE,
            [SELECT COUNT() FROM Case WHERE IsEscalated = true],
            'Every case in the batch should have been escalated.'
        );
        Assert.areEqual(
            BULK_SIZE,
            [SELECT COUNT() FROM Task WHERE Subject LIKE 'Call back escalated case%'],
            'Phone origin should produce exactly one follow-up Task per case.'
        );
        Assert.areEqual(
            0,
            [SELECT COUNT() FROM Case WHERE IsEscalated = true AND Priority != 'High'],
            'The strategy must raise priority on every escalated case.'
        );
    }

    @IsTest
    static void factory_resolves_one_strategy_per_custom_metadata_row() {
        CaseEscalationStrategyFactory factory = new CaseEscalationStrategyFactory();
        CaseEscalationStrategyFactory.reset();

        Test.startTest();
        ICaseEscalationStrategy phone    = factory.forOrigin('Phone');
        ICaseEscalationStrategy web      = factory.forOrigin('Web');
        ICaseEscalationStrategy unknown  = factory.forOrigin('Carrier Pigeon');
        ICaseEscalationStrategy blank    = factory.forOrigin(null);
        Test.stopTest();

        Assert.isInstanceOfType(phone, PhoneCaseEscalationStrategy.class,
            'The Phone CMDT row should resolve to PhoneCaseEscalationStrategy.');
        Assert.isInstanceOfType(web, WebCaseEscalationStrategy.class,
            'The Web CMDT row should resolve to WebCaseEscalationStrategy.');
        Assert.isInstanceOfType(unknown, DefaultCaseEscalationStrategy.class,
            'An origin with no row must fall back, not throw.');
        Assert.isInstanceOfType(blank, DefaultCaseEscalationStrategy.class,
            'A blank origin must fall back, not throw.');
    }

    @IsTest
    static void factory_falls_back_when_the_named_class_no_longer_exists() {
        CaseEscalationStrategyFactory.reset();
        // Simulate a CMDT row left pointing at a renamed class. Type.forName returns
        // null for a name that resolves to nothing (Apex Reference Guide L242076-242082);
        // without the guard in build() this would be a null dereference at run time.
        CaseEscalationStrategyFactory.classNameByOrigin =
            new Map<String, String>{ 'phone' => 'ClassThatWasRenamedLastRelease' };

        Test.startTest();
        ICaseEscalationStrategy resolved = new CaseEscalationStrategyFactory().forOrigin('Phone');
        Test.stopTest();

        Assert.isInstanceOfType(resolved, DefaultCaseEscalationStrategy.class,
            'A dangling class name must degrade to the default, not throw.');
    }

    @IsTest
    static void rollback_undoes_every_object_the_service_touched() {
        Case target = [SELECT Id, Subject, Status, IsEscalated FROM Case LIMIT 1];

        // Force the SECOND DML to fail. Task.Subject is limited to 255 characters
        // (Object Reference, Task.Subject), and PhoneCaseEscalationStrategy prefixes
        // the case subject, so a 250-character subject overflows it.
        target.Subject = 'x'.repeat(250);
        TriggerHandler.skipOnce('CaseTriggerHandler');
        update target;

        Boolean threw = false;
        Test.startTest();
        try {
            new CaseEscalationService().escalate(new Set<Id>{ target.Id });
            Assert.fail('The Task insert should have failed on subject length.');
        } catch (BaseService.ServiceException e) {
            threw = true;
        }
        Test.stopTest();

        Assert.isTrue(threw, 'The service must rethrow as ServiceException, not swallow.');

        Case after = [SELECT Id, IsEscalated, Priority FROM Case WHERE Id = :target.Id];
        Assert.areEqual(false, after.IsEscalated,
            'The Case update must have been rolled back with the failed Task insert.');
        Assert.areEqual(0, [SELECT COUNT() FROM Task WHERE WhatId = :target.Id],
            'No follow-up Task should survive the rollback.');

        // The other half of the same rule: statics are NOT reverted by a rollback
        // (Apex Developer Guide L8692-8693). The strategy the factory resolved before
        // the failure is still cached, which is exactly why every static mutable
        // collection in this stack has a reset() hook.
        Assert.isNotNull(CaseEscalationStrategyFactory.instanceByOrigin.get('phone'),
            'A rollback does not clear a static cache; the reset hook is what does.');
    }
}
```

---

## 9. `-meta.xml` for every class and the trigger

Each `.cls` needs a sibling `<Name>.cls-meta.xml`; `apiVersion` and `status` are the
`ApexClass` metadata fields (Metadata API Developer Guide L22212–22245). The value below
matches the repo templates (`templates/apex/BaseService.cls-meta.xml`) and is the version
at which classes without a sharing declaration run `with sharing` and Apex runs in user
context by default (Apex Developer Guide L4961, L11744–11746).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

`CaseTrigger.trigger-meta.xml` — note that `Inactive` is a valid `status` for
`ApexTrigger` but not for `ApexClass` (Metadata API Developer Guide L22277–22278):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexTrigger>
```

---

## 10. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Escalation_Strategy__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Case_Escalation_Strategy__mdt.Apex_Class__c</members>
        <members>Case_Escalation_Strategy__mdt.Case_Origin__c</members>
        <members>Case_Escalation_Strategy__mdt.Is_Active__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Case_Escalation_Strategy.Phone</members>
        <members>Case_Escalation_Strategy.Web</members>
        <name>CustomMetadata</name>
    </types>
    <types>
        <members>CaseDomain</members>
        <members>CaseEscalationService</members>
        <members>CaseEscalationServiceTest</members>
        <members>CaseEscalationStrategyFactory</members>
        <members>CaseSelector</members>
        <members>CaseTriggerHandler</members>
        <members>DefaultCaseEscalationStrategy</members>
        <members>ICaseEscalationStrategy</members>
        <members>PhoneCaseEscalationStrategy</members>
        <members>WebCaseEscalationStrategy</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>CaseTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <version>67.0</version>
</Package>
```

The base classes (`TriggerHandler`, `TriggerControl`, `BaseDomain`, `BaseService`,
`BaseSelector`, `ApplicationLogger`, `SecurityUtils`) and
`Trigger_Setting__mdt` / `Logger_Setting__mdt` / `Application_Log__c` are deployed once
from `templates/apex/` and are deliberately not repeated in this manifest.

---

## 11. Deploy, run the checker, run the tests

```bash
# 0. Retrieve current state before changing anything.
sf project retrieve start --manifest manifest/package.xml --target-org devhub-sandbox

# 1. Static review before deploying — this skill's checker.
python3 skills/apex/apex-design-patterns/scripts/check_apex_design_patterns.py \
  --manifest-dir force-app/main/default

# 2. Deploy the base classes and their CMDT first (once per org).
sf project deploy start --source-dir templates/apex --target-org devhub-sandbox

# 3. Deploy this stack and run only its tests.
sf project deploy start \
  --manifest manifest/package.xml \
  --test-level RunSpecifiedTests \
  --tests CaseEscalationServiceTest \
  --target-org devhub-sandbox

# 4. Run the tests on their own, synchronously, with coverage.
sf apex run test \
  --tests CaseEscalationServiceTest \
  --result-format human --code-coverage --synchronous \
  --target-org devhub-sandbox
```

**Verification step.** The deploy proves the classes compile; this proves the strategy
seam is actually data-driven. Confirm every class named by a Custom Metadata row exists
and is valid in the org:

```soql
SELECT Name, ApiVersion, Status, IsValid
FROM ApexClass
WHERE Name IN ('PhoneCaseEscalationStrategy', 'WebCaseEscalationStrategy', 'DefaultCaseEscalationStrategy')
```

```bash
# Every active row must name a class that the query above returned.
sf data query --target-org devhub-sandbox \
  --query "SELECT Case_Origin__c, Apex_Class__c, Is_Active__c FROM Case_Escalation_Strategy__mdt WHERE Is_Active__c = true"
```

A row whose `Apex_Class__c` is missing from the `ApexClass` result is the dangling-name
case: the factory will log a warning and silently fall back to
`DefaultCaseEscalationStrategy` in production. That is a deliberate degrade, not a pass —
fix the row.
