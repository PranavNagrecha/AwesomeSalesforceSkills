# NPSP Trigger Framework Extension (TDTM) — Work Template

Use this template when implementing a custom NPSP TDTM handler.

---

## Scope

**Skill:** `npsp-trigger-framework-extension`

**Request summary:** (fill in what the user asked for — which object, which trigger actions, what business logic)

---

## Context Gathered

Answer the Before Starting questions from SKILL.md before writing any code:

- **NPSP version / namespace confirmed?** Yes / No — version: ___
- **Target sObject:** (e.g. Opportunity, Contact, npe01__OppPayment__c)
- **Trigger actions required:** (e.g. AfterInsert, AfterUpdate — list only what is needed)
- **Highest existing load order on this object:** (query result from npsp__Trigger_Handler__c)
- **Org namespace for Owned_by_Namespace__c:** ___
- **Any existing custom TDTM handlers on same object?** Yes / No — list if yes

---

## Handler Class Scaffold

Fill in the blanks and verify all placeholders are replaced before deploying.

```apex
public class [HandlerClassName] extends npsp.TDTM_Runnable {

    // Recursion guard — prevents double-processing in the same transaction
    private static Set<Id> processedIds = new Set<Id>();

    public override npsp.TDTM_Runnable.DmlWrapper run(
        List<SObject> newlist,
        List<SObject> oldlist,
        npsp.TDTM_Runnable.Action triggerAction,
        Schema.DescribeSObjectResult objResult
    ) {
        npsp.TDTM_Runnable.DmlWrapper wrapper = new npsp.TDTM_Runnable.DmlWrapper();

        // Guard: only act on intended trigger actions
        if (triggerAction != npsp.TDTM_Runnable.Action.[TriggerAction]) {
            return wrapper;
        }

        // Cast to the specific sObject type
        List<[SObjectType]> newRecords = (List<[SObjectType]>) newlist;
        Map<Id, [SObjectType]> oldMap = oldlist != null
            ? new Map<Id, [SObjectType]>((List<[SObjectType]>) oldlist)
            : new Map<Id, [SObjectType]>();

        for ([SObjectType] rec : newRecords) {
            if (processedIds.contains(rec.Id)) {
                continue;
            }

            // TODO: Add condition check (e.g., field transition)
            if ([condition]) {
                // Build related record — do NOT issue DML directly
                [RelatedSObject] related = new [RelatedSObject](
                    [LookupField__c] = rec.Id
                    // ... other fields
                );
                wrapper.objectsToInsert.add(related);
                processedIds.add(rec.Id);
            }
        }

        return wrapper;
    }
}
```

---

## Handler Registration Record

```apex
// Run this in a post-install script, data deployment, or sandbox setup script.
// Never set npsp__Owned_by_Namespace__c to 'npsp' — use your org's namespace or a custom value.

npsp__Trigger_Handler__c th = new npsp__Trigger_Handler__c(
    Name = '[HandlerClassName]',
    npsp__Class__c = '[HandlerClassName]',           // no npsp. prefix
    npsp__Object__c = '[SObjectAPIName]',
    npsp__Trigger_Action__c = '[Action1;Action2]',   // semicolon-delimited, no spaces
    npsp__Load_Order__c = [100+],                    // above packaged handlers (1-50 range)
    npsp__Active__c = true,
    npsp__Owned_by_Namespace__c = '[your-namespace-or-custom-value]'
);
insert th;
```

---

## Test Class Scaffold

```apex
@isTest
private class [HandlerClassName]Test {

    @testSetup
    static void setupHandlers() {
        // DO NOT call getTdtmConfig() before setTdtmConfig() — cache bug drops custom handlers
        List<npsp__Trigger_Handler__c> handlers = new List<npsp__Trigger_Handler__c>{
            new npsp__Trigger_Handler__c(
                Name = '[HandlerClassName]',
                npsp__Class__c = '[HandlerClassName]',
                npsp__Object__c = '[SObjectAPIName]',
                npsp__Trigger_Action__c = '[Action1;Action2]',
                npsp__Load_Order__c = 100,
                npsp__Active__c = true,
                npsp__Owned_by_Namespace__c = '[your-namespace]'
            )
        };
        npsp.TDTM_Global_API.setTdtmConfig(handlers);
    }

    @isTest
    static void [testMethodName]() {
        // Arrange
        // TODO: Set up parent records (Account, Contact) as needed

        Test.startTest();
        // Act
        // TODO: Insert or update the record that triggers the handler

        Test.stopTest();

        // Assert
        // TODO: Query the records produced by DmlWrapper and assert expected state
        List<[RelatedSObject]> results = [SELECT Id FROM [RelatedSObject] WHERE [condition]];
        System.assertEquals([expectedCount], results.size(), '[Descriptive assertion message]');
    }
}
```

---

## Checklist

Tick each item before marking the work complete.

- [ ] Handler class extends `npsp.TDTM_Runnable` with correct four-parameter `run()` signature
- [ ] All DML routed through `DmlWrapper` — no direct `insert`, `update`, `delete` in `run()`
- [ ] `return wrapper;` on every code path — no `return null;`
- [ ] Static `Set<Id>` recursion guard declared and used
- [ ] `npsp__Trigger_Handler__c` record has `npsp__Owned_by_Namespace__c` set (not blank, not `npsp`)
- [ ] `npsp__Load_Order__c` is 100 or above on standard NPSP objects
- [ ] `npsp__Trigger_Action__c` is semicolon-delimited with no spaces
- [ ] Test class uses `setTdtmConfig()` without prior `getTdtmConfig()` call
- [ ] Test assertions query actual DML-wrapper-produced records (not just assert no exception)
- [ ] Verified in sandbox before production deployment

---

## Notes

(Record any deviations from the standard pattern and why.)
