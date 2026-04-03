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

**Correct approach:** Keep the controller thin, move orchestration to a service, query shape to selectors, and object rules to domain logic.
