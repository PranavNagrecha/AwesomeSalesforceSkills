# Examples — NPSP Trigger Framework Extension (TDTM)

---

## Example 1: Custom Handler That Stamps a Related Record on Opportunity Closed Won

**Context:** A nonprofit wants to automatically create a Program Enrollment record whenever an Opportunity moves to Closed Won, after NPSP's payment handler has already fired. Direct Flow or Process Builder solutions have been rejected due to governor limit concerns at batch volume.

**Problem:** A developer writes a standard Apex trigger on Opportunity and issues a direct `insert` inside it. This fires before NPSP's own trigger handlers complete, corrupting payment rollup state. Alternatively, they try to extend a non-NPSP handler framework, which runs in a separate trigger execution and misses the NPSP-managed transaction context.

**Solution:**

```apex
public class ProgramEnrollmentOnCloseHandler extends npsp.TDTM_Runnable {

    private static Set<Id> processedIds = new Set<Id>();

    public override npsp.TDTM_Runnable.DmlWrapper run(
        List<SObject> newlist,
        List<SObject> oldlist,
        npsp.TDTM_Runnable.Action triggerAction,
        Schema.DescribeSObjectResult objResult
    ) {
        npsp.TDTM_Runnable.DmlWrapper wrapper = new npsp.TDTM_Runnable.DmlWrapper();

        if (triggerAction != npsp.TDTM_Runnable.Action.AfterUpdate) {
            return wrapper;
        }

        Map<Id, Opportunity> oldMap = new Map<Id, Opportunity>((List<Opportunity>) oldlist);

        for (Opportunity opp : (List<Opportunity>) newlist) {
            if (processedIds.contains(opp.Id)) {
                continue;
            }
            Opportunity oldOpp = oldMap.get(opp.Id);
            if (opp.StageName == 'Closed Won' && oldOpp.StageName != 'Closed Won') {
                Program_Enrollment__c pe = new Program_Enrollment__c(
                    Opportunity__c = opp.Id,
                    Contact__c = opp.npsp__Primary_Contact__c,
                    Status__c = 'Active'
                );
                wrapper.objectsToInsert.add(pe);
                processedIds.add(opp.Id);
            }
        }

        return wrapper;
    }
}
```

Registration record (data script or deployment metadata):

```apex
npsp__Trigger_Handler__c th = new npsp__Trigger_Handler__c(
    Name = 'ProgramEnrollmentOnCloseHandler',
    npsp__Class__c = 'ProgramEnrollmentOnCloseHandler',
    npsp__Object__c = 'Opportunity',
    npsp__Trigger_Action__c = 'AfterUpdate',
    npsp__Load_Order__c = 100,
    npsp__Active__c = true,
    npsp__Owned_by_Namespace__c = 'myorg'
);
insert th;
```

**Why it works:** The handler only fires on AfterUpdate when `StageName` transitions to Closed Won, the static `processedIds` guard prevents double-processing in the same transaction, and `DmlWrapper.objectsToInsert` ensures the enrollment is inserted after all handlers complete — not mid-pipeline.

---

## Example 2: Test Class Using setTdtmConfig for Isolation

**Context:** Testing the `ProgramEnrollmentOnCloseHandler` in a scratch org or sandbox where all packaged NPSP handlers are active. Without test isolation, the full NPSP handler chain fires and consumes CPU time and DML rows, making tests slow, brittle, and dependent on NPSP's internal state.

**Problem:** A developer calls `npsp.TDTM_Global_API.getTdtmConfig()` first to get the existing handler list, appends the custom handler to it, then calls `setTdtmConfig()`. Due to the static cache bug, the custom handler entry is overwritten by the cached packaged entry and never actually runs during the test. The test passes vacuously.

**Solution:**

```apex
@isTest
private class ProgramEnrollmentOnCloseHandlerTest {

    @testSetup
    static void setupHandlers() {
        // DO NOT call getTdtmConfig() here — doing so populates a static cache
        // that causes setTdtmConfig() to silently drop the custom handler.

        List<npsp__Trigger_Handler__c> handlers = new List<npsp__Trigger_Handler__c>{
            new npsp__Trigger_Handler__c(
                Name = 'ProgramEnrollmentOnCloseHandler',
                npsp__Class__c = 'ProgramEnrollmentOnCloseHandler',
                npsp__Object__c = 'Opportunity',
                npsp__Trigger_Action__c = 'AfterUpdate',
                npsp__Load_Order__c = 100,
                npsp__Active__c = true,
                npsp__Owned_by_Namespace__c = 'myorg'
            )
        };
        // Replace the full TDTM handler chain with only the custom handler.
        npsp.TDTM_Global_API.setTdtmConfig(handlers);
    }

    @isTest
    static void testEnrollmentCreatedOnClose() {
        Account acc = new Account(Name = 'Test Nonprofit');
        insert acc;

        Contact con = new Contact(LastName = 'Donor', AccountId = acc.Id);
        insert con;

        Opportunity opp = new Opportunity(
            Name = 'Test Gift',
            AccountId = acc.Id,
            npsp__Primary_Contact__c = con.Id,
            StageName = 'Prospecting',
            CloseDate = Date.today()
        );
        insert opp;

        Test.startTest();
        opp.StageName = 'Closed Won';
        update opp;
        Test.stopTest();

        List<Program_Enrollment__c> enrollments = [
            SELECT Id, Opportunity__c, Status__c
            FROM Program_Enrollment__c
            WHERE Opportunity__c = :opp.Id
        ];
        System.assertEquals(1, enrollments.size(), 'Expected exactly one Program Enrollment');
        System.assertEquals('Active', enrollments[0].Status__c);
    }
}
```

**Why it works:** `setTdtmConfig()` is called with an explicit handler list — no prior `getTdtmConfig()` call. The test runs only the custom handler, making assertions deterministic and independent of NPSP's internal handler chain changes across upgrades.

---

## Anti-Pattern: Direct DML Inside run()

**What practitioners do:** Issue `insert relatedRecords;` directly inside the `run()` method body, treating it like a standard Apex trigger handler.

**What goes wrong:** The direct `insert` fires the target object's Apex trigger pipeline immediately, which includes any NPSP handlers registered on that object. Those handlers may fire with incomplete state (because the current handler chain has not finished). DML row counts and CPU time double. In worst cases, if the inserted records also have triggers that chain back to the same Opportunity, the entire TDTM dispatcher re-runs recursively until hitting the recursion limit or a governor limit.

**Correct approach:** Return all records to insert, update, or delete via the `DmlWrapper` returned from `run()`. NPSP's dispatcher batches all handler DmlWrappers and issues a single combined DML after the full chain completes.
