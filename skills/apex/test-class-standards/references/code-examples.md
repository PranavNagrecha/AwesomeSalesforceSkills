# Code Examples — Test Class Standards

A complete, deploy-shaped test package for an object model that does not exist
in any other skill in this repo: **Asset renewal**. Everything below is one
coherent artifact set — service, async callout, test class, metadata and
manifest — so it can be copied into a build step without stitching.

The shared test classes are referenced by relative path and shipped alongside
the test, per the provenance rule in `agents/apex-builder/AGENT.md` Step 6: a
test that names a canonical template class must deploy that class in the same
set, or the deploy fails with `Variable does not exist: TestDataFactory`.

## Object Model Under Test

| Field | Type | Role in the test |
|---|---|---|
| `Asset.UsageEndDate` | Date (standard) | Drives the 30-day renewal window |
| `Asset.Renewal_Status__c` | Picklist — Not Started / Pending / Renewed / Failed | The outcome every assertion reads |
| `Asset.Renewal_Quote_Number__c` | Text(32) | Written back from the callout response body |
| `Asset.AccountId` | Lookup (standard) | Parent seeded by `TestDataFactory.createAccounts` |
| Permission set `Asset_Renewal_Manager` | — | The access the `System.runAs` user is minted with |

## Template Classes This Package Ships

| Template (relative path) | Used for |
|---|---|
| `templates/apex/tests/TestDataFactory.cls` | Bulk parent Accounts with an overrides map |
| `templates/apex/tests/TestRecordBuilder.cls` | Assets, which the factory does not cover |
| `templates/apex/tests/TestUserFactory.cls` | The permission-set user for `System.runAs` |
| `templates/apex/tests/MockHttpResponseGenerator.cls` | The `HttpCalloutMock` for success and 503 paths |

Copy each one verbatim, with its `-meta.xml`, into the same class directory.
Do not fork the bodies; a forked copy stops matching `diff` against the
canonical template and the provenance check in review will reject it.

## 1. Service Under Test

```apex
/**
 * AssetRenewalService — flags Assets whose entitlement lapses inside the
 * renewal window and hands the batch to the renewal API.
 *
 * Object model assumed by this service:
 *   Asset.UsageEndDate              standard Date
 *   Asset.Renewal_Status__c         picklist: Not Started / Pending / Renewed / Failed
 *   Asset.Renewal_Quote_Number__c   text(32)
 */
public with sharing class AssetRenewalService {

    public class RenewalException extends Exception {}

    @TestVisible
    private static final Integer RENEWAL_WINDOW_DAYS = 30;

    public static List<Asset> queueRenewals(List<Asset> assets) {
        if (assets == null || assets.isEmpty()) {
            throw new RenewalException('queueRenewals requires at least one Asset');
        }
        Date cutoff = Date.today().addDays(RENEWAL_WINDOW_DAYS);
        List<Asset> due = new List<Asset>();
        Set<Id> dueIds = new Set<Id>();
        for (Asset record : assets) {
            if (record.UsageEndDate != null && record.UsageEndDate <= cutoff) {
                record.Renewal_Status__c = 'Pending';
                due.add(record);
                dueIds.add(record.Id);
            }
        }
        if (due.isEmpty()) {
            return due;
        }
        update as user due;
        System.enqueueJob(new AssetRenewalCalloutQueueable(dueIds));
        return due;
    }
}
```

## 2. Async Callout Worker

```apex
/**
 * AssetRenewalCalloutQueueable — posts a due-renewal batch to the renewal API
 * and writes the returned quote number back onto each Asset.
 */
public with sharing class AssetRenewalCalloutQueueable implements Queueable, Database.AllowsCallouts {

    private final Set<Id> assetIds;

    public AssetRenewalCalloutQueueable(Set<Id> assetIds) {
        this.assetIds = assetIds;
    }

    public void execute(QueueableContext context) {
        List<Asset> assets = [
            SELECT Id, Name, Renewal_Status__c, Renewal_Quote_Number__c
            FROM Asset
            WHERE Id IN :assetIds
            WITH USER_MODE
        ];
        if (assets.isEmpty()) {
            return;
        }

        HttpRequest request = new HttpRequest();
        request.setEndpoint('callout:Renewal_API/v1/quotes');
        request.setMethod('POST');
        request.setHeader('Content-Type', 'application/json');
        request.setBody(JSON.serialize(new Map<String, Object>{ 'assetIds' => new List<Id>(assetIds) }));

        HttpResponse response = new Http().send(request);
        Boolean accepted = response.getStatusCode() == 200;
        String quoteNumber = null;
        if (accepted) {
            Map<String, Object> payload = (Map<String, Object>) JSON.deserializeUntyped(response.getBody());
            quoteNumber = (String) payload.get('quoteNumber');
        }

        for (Asset record : assets) {
            record.Renewal_Status__c = accepted ? 'Renewed' : 'Failed';
            record.Renewal_Quote_Number__c = quoteNumber;
        }
        update as user assets;
    }
}
```

## 3. The Test Class

Four methods, one per contract the service makes: bulk, negative, access, and
remote-failure. Note the ordering inside the first method — `Test.startTest()`
is called **before** `Test.setMock(...)`, which is the documented requirement
when DML has already run in the transaction (apexdev L35135-L35141).

```apex
/**
 * AssetRenewalServiceTest — behaviour tests for AssetRenewalService and its
 * renewal callout Queueable.
 *
 * Shared test classes this file depends on (all must ship with it):
 *   TestDataFactory, TestRecordBuilder, TestUserFactory, MockHttpResponseGenerator
 */
@IsTest
private class AssetRenewalServiceTest {

    private static final Integer BULK_SIZE = 200;
    private static final String RENEWAL_PERMISSION_SET = 'Asset_Renewal_Manager';
    private static final String QUOTE_BODY = '{"quoteNumber":"Q-88213"}';

    @TestSetup
    static void seedAssets() {
        List<Account> accounts = TestDataFactory.createAccounts(BULK_SIZE, new Map<String, Object>{
            'Industry' => 'Manufacturing',
            'BillingCountry' => 'United States'
        });
        insert accounts;

        List<Asset> assets = new List<Asset>();
        for (Integer i = 0; i < BULK_SIZE; i++) {
            assets.add((Asset) new TestRecordBuilder(Asset.SObjectType)
                .set('Name', 'Renewable Asset ' + i)
                .set('AccountId', accounts[i].Id)
                .set('UsageEndDate', Date.today().addDays(10))
                .set('Renewal_Status__c', 'Not Started')
                .build());
        }
        insert assets;
    }

    @IsTest
    static void queuesRenewalsForAllDueAssets() {
        List<Asset> due = [SELECT Id, UsageEndDate, Renewal_Status__c FROM Asset];
        Assert.areEqual(BULK_SIZE, due.size(), 'Setup must seed a full bulk batch');

        // startTest opens the new governor context, and must precede setMock
        // because the setup DML above leaves work pending in this transaction.
        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
            .routeByPathContains('/v1/quotes', 200, QUOTE_BODY));
        AssetRenewalService.queueRenewals(due);
        Test.stopTest();

        List<Asset> renewed = [
            SELECT Id, Renewal_Status__c, Renewal_Quote_Number__c
            FROM Asset
            WHERE Renewal_Status__c = 'Renewed'
        ];
        Assert.areEqual(BULK_SIZE, renewed.size(), 'Every due Asset should be renewed after stopTest');
        Assert.areEqual('Q-88213', renewed[0].Renewal_Quote_Number__c, 'Quote number must come from the mock body');
        Assert.isTrue(
            Limits.getQueries() <= Limits.getLimitQueries() / 2,
            'Renewal path must leave SOQL headroom for callers: queries=' + Limits.getQueries()
        );
    }

    @IsTest
    static void throwsWhenAssetListIsEmpty() {
        try {
            AssetRenewalService.queueRenewals(new List<Asset>());
            Assert.fail('RenewalException expected for an empty Asset list');
        } catch (AssetRenewalService.RenewalException expected) {
            Assert.isTrue(
                expected.getMessage().contains('at least one Asset'),
                'Message should name the contract it broke, was: ' + expected.getMessage()
            );
        }
    }

    @IsTest
    static void renewsWithinRenewalManagerPermissions() {
        User renewalManager = TestUserFactory.createUser(
            'Standard User',
            new List<String>{ RENEWAL_PERMISSION_SET }
        );

        List<Asset> due = [SELECT Id, UsageEndDate, Renewal_Status__c FROM Asset LIMIT 10];

        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
            .withResponse(200, QUOTE_BODY));
        System.runAs(renewalManager) {
            AssetRenewalService.queueRenewals(due);
        }
        Test.stopTest();

        Set<Id> dueIds = new Map<Id, Asset>(due).keySet();
        List<Asset> after = [SELECT Id, Renewal_Status__c FROM Asset WHERE Id IN :dueIds];
        for (Asset record : after) {
            Assert.areEqual('Renewed', record.Renewal_Status__c, 'Renewal manager must be able to renew');
        }
    }

    @IsTest
    static void marksAssetsFailedWhenRenewalApiRejects() {
        List<Asset> due = [SELECT Id, UsageEndDate, Renewal_Status__c FROM Asset LIMIT 5];

        Test.startTest();
        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator()
            .withResponse(503, '{"error":"upstream unavailable"}'));
        AssetRenewalService.queueRenewals(due);
        Test.stopTest();

        Set<Id> dueIds = new Map<Id, Asset>(due).keySet();
        List<Asset> after = [
            SELECT Id, Renewal_Status__c, Renewal_Quote_Number__c
            FROM Asset
            WHERE Id IN :dueIds
        ];
        for (Asset record : after) {
            Assert.areEqual('Failed', record.Renewal_Status__c, 'A 503 must not leave the Asset marked Renewed');
            Assert.areEqual(null, record.Renewal_Quote_Number__c, 'No quote number should be written on failure');
        }
    }
}
```

## 4. Class Metadata

Every class in the package carries the same `-meta.xml`. This is the one for
the test class; repeat it verbatim for each `.cls` file, changing nothing.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

## 5. Deployment Manifest

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>TestDataFactory</members>
        <members>TestRecordBuilder</members>
        <members>TestUserFactory</members>
        <members>MockHttpResponseGenerator</members>
        <members>AssetRenewalService</members>
        <members>AssetRenewalCalloutQueueable</members>
        <members>AssetRenewalServiceTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Asset.Renewal_Status__c</members>
        <members>Asset.Renewal_Quote_Number__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Asset_Renewal_Manager</members>
        <name>PermissionSet</name>
    </types>
    <version>67.0</version>
</Package>
```

## 6. Deploy Order

Apex compiles as one unit, so a single `deploy start` with the manifest above
is enough. The order below is what a build plan should record, because it is
the order in which a *step-by-step* build must produce the files — each row
depends on every row above it.

| # | Artifact | Depends on |
|---|---|---|
| 1 | `Asset.Renewal_Status__c`, `Asset.Renewal_Quote_Number__c` | — |
| 2 | `Asset_Renewal_Manager` permission set | the two fields |
| 3 | `TestDataFactory.cls`, `TestRecordBuilder.cls`, `TestUserFactory.cls`, `MockHttpResponseGenerator.cls` (+ `-meta.xml`) | — |
| 4 | `AssetRenewalCalloutQueueable.cls` | the two fields |
| 5 | `AssetRenewalService.cls` | row 4 |
| 6 | `AssetRenewalServiceTest.cls` | rows 3, 4, 5 |

Rows 3-6 are the provenance set: if row 3 is dropped because "the org already
has a factory", the deploy fails on row 6, not on row 3.

## 7. Verification

Run the skill checker against the class directory before any deploy attempt.

```bash
python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py \
    --manifest-dir force-app/main/default/classes
```

Expected on this package:

```text
Scanned 7 Apex class file(s); audited 5 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0
```

Exit codes: `0` when no ERROR finding was raised, `1` on any ERROR or on a
missing `--manifest-dir`. Add `--strict` in CI to fail on WARN findings too.

Then deploy without committing:

```bash
sf project deploy start --manifest package.xml --dry-run \
    --test-level RunSpecifiedTests --tests AssetRenewalServiceTest
```

A dry run compiles the package and runs the named tests without persisting
metadata, which is the last check that the provenance set is complete.

UNVERIFIED (2026-09-12): the `sf` CLI flag spellings above are not in the Apex
Developer Guide corpus this skill was grounded against — confirm them against
`sf project deploy start --help` for your CLI version before putting the command
in a runbook. The Apex behaviour they exercise is grounded; the flags are not.
