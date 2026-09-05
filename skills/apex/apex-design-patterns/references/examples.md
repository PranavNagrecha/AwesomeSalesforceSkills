# Examples — Apex Design Patterns

## Example 1: Trigger Delegates To Service And Domain Logic

**Context:** `Opportunity` trigger logic is growing: qualification rules, stage transitions, and related record creation all sit in the handler.

**Problem:** Every change requires editing one giant handler that mixes orchestration and object rules.

**Solution:**

```apex
trigger OpportunityTrigger on Opportunity (before update, after update) {
    OpportunityApplicationService service = new OpportunityApplicationService();
    if (Trigger.isBefore && Trigger.isUpdate) {
        service.beforeUpdate(Trigger.new, Trigger.oldMap);
    }
    if (Trigger.isAfter && Trigger.isUpdate) {
        service.afterUpdate(Trigger.new, Trigger.oldMap);
    }
}

public inherited sharing class OpportunityApplicationService {
    public void beforeUpdate(List<Opportunity> newRecords, Map<Id, Opportunity> oldMap) {
        OpportunityDomain.applyQualificationRules(newRecords, oldMap);
    }
}

public class OpportunityDomain {
    public static void applyQualificationRules(List<Opportunity> newRecords, Map<Id, Opportunity> oldMap) {
        for (Opportunity opp : newRecords) {
            Opportunity oldOpp = oldMap.get(opp.Id);
            if (oldOpp.StageName != 'Qualified' && opp.StageName == 'Qualified' && opp.Amount == null) {
                opp.addError('Qualified opportunities must have an Amount.');
            }
        }
    }
}
```

**Why it works:** The trigger is an adapter, the service controls the workflow, and the object-specific rule sits in a domain-oriented class.

---

## Example 2: Selector And Interface-Based Dependency Injection

**Context:** A service loads active Accounts and sends a notification through a dependency that must be replaceable in tests.

**Problem:** Query logic and callout logic live in the same class, and tests must branch on `Test.isRunningTest()`.

**Solution:**

```apex
public inherited sharing class AccountSelector {
    public List<Account> selectActiveByIds(Set<Id> accountIds) {
        return [
            SELECT Id, Name, OwnerId
            FROM Account
            WHERE Id IN :accountIds
            AND IsActive__c = true
        ];
    }
}

public interface NotificationGateway {
    void notifyAccounts(List<Account> accounts);
}

public inherited sharing class AccountNotificationService {
    private final AccountSelector selector;
    private final NotificationGateway gateway;

    public AccountNotificationService(AccountSelector selector, NotificationGateway gateway) {
        this.selector = selector;
        this.gateway = gateway;
    }

    public void notifyActiveAccounts(Set<Id> accountIds) {
        gateway.notifyAccounts(selector.selectActiveByIds(accountIds));
    }
}
```

**Why it works:** Query responsibility is separate from orchestration, and the dependency is replaceable in tests without test-only branching.

---

## Anti-Pattern: God Controller

**What practitioners do:** An Aura or REST controller queries data, validates business rules, makes callouts, and updates records directly.

**What goes wrong:** No single layer has a clear responsibility, tests cannot isolate collaborators, and refactors become risky.

**Correct approach:** Keep the controller thin, move orchestration to a service, query shape to selectors, and object rules to domain logic. The `@AuraEnabled` method becomes an adapter that translates parameters in and exceptions out — nothing else. Note that an `@AuraEnabled` method called from a Lightning web component is an entry point, so an `inherited sharing` class reached through it runs `with sharing` (Apex Developer Guide L4851–4856).

```apex
public with sharing class CaseConsoleController {

    /**
     * Adapter only: no SOQL, no DML, no branching on business rules.
     * Its whole job is parameter marshalling and turning a ServiceException
     * into something the LWC can display.
     */
    @AuraEnabled
    public static void escalateCases(List<Id> caseIds) {
        try {
            new CaseEscalationService().escalate(new Set<Id>(caseIds));
        } catch (BaseService.ServiceException e) {
            throw new AuraHandledException(e.getMessage());
        }
    }

    @AuraEnabled(cacheable=true)
    public static List<Case> openCasesForAccount(Id accountId) {
        return new CaseSelector().selectOpenByAccountIds(new Set<Id>{ accountId });
    }
}
```

---

## Example 3: One Rule, Many Business Units — Strategy Instead Of A Growing `switch`

**Context:** Escalation behaviour differs by `Case.Origin`, and a new origin arrives roughly once a quarter.

**Problem:** The service holds an `if/else` chain. Every new origin is an Apex change, a code review, a test update, and a deployment — for what is really a configuration decision.

**Solution:** One interface, one class per variant, and a Custom Metadata row that names the class. The routing table becomes data:

| `Case_Origin__c` | `Apex_Class__c` | `Is_Active__c` | Effect |
|---|---|---|---|
| `Phone` | `PhoneCaseEscalationStrategy` | true | High priority + same-day callback Task |
| `Web` | `WebCaseEscalationStrategy` | true | High priority + next-day email Task |
| `Chat` | `WebCaseEscalationStrategy` | false | Row present but switched off — falls back |
| *(no row)* | — | — | `DefaultCaseEscalationStrategy`, no Task |

Verifying the table against the org is a two-query check, and it is the check that catches a row still naming a class that was renamed:

```soql
SELECT Case_Origin__c, Apex_Class__c, Is_Active__c
FROM Case_Escalation_Strategy__mdt
WHERE Is_Active__c = true
ORDER BY Case_Origin__c
```

**Why it works:** A new origin ships as a Custom Metadata row plus one small class, and the service never changes. The cost is that the class name is now a string the compiler cannot check — which is exactly why the factory in `references/code-examples.md` § 6 null-checks the `Type`, `instanceof`-checks the instance, and always has a named fallback.

**When not to do this:** Two variants that will never become three. A `switch` over an enum is cheaper to read and impossible to misconfigure. Add the seam when the third variant arrives, not in anticipation of it.
