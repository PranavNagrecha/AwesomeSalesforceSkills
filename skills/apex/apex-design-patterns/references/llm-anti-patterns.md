# LLM Anti-Patterns — Apex Design Patterns

Common mistakes AI coding assistants make when generating or advising on Apex service, selector, domain, and dependency-injection layers.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Creating a service layer that queries data directly instead of using a selector

**What the LLM generates:**

```apex
public class AccountService {
    public static void deactivateAccounts(Set<Id> accountIds) {
        List<Account> accounts = [SELECT Id, Status__c FROM Account WHERE Id IN :accountIds];
        for (Account a : accounts) {
            a.Status__c = 'Inactive';
        }
        update accounts;
    }
}
```

**Why it happens:** LLMs generate compact, self-contained methods. Inlining SOQL in the service layer feels simpler, but it scatters query definitions across every service method, making them impossible to test without hitting the database and violating the separation of concerns the pattern exists to provide.

**Correct pattern:**

```apex
public class AccountService {
    public static void deactivateAccounts(Set<Id> accountIds) {
        List<Account> accounts = AccountSelector.selectByIds(accountIds);
        AccountDomain.markInactive(accounts);
        update accounts;
    }
}

public class AccountSelector {
    public static List<Account> selectByIds(Set<Id> accountIds) {
        return [SELECT Id, Status__c FROM Account WHERE Id IN :accountIds];
    }
}
```

**Detection hint:** `\[SELECT.*FROM.*WHERE` appearing directly inside a class whose name ends in `Service`.

---

## Anti-Pattern 2: Making every method static, killing dependency injection seams

**What the LLM generates:**

```apex
public class OrderService {
    public static void processOrders(List<Order> orders) {
        PricingService.calculateTotals(orders);
        InventoryService.reserveStock(orders);
    }
}
```

**Why it happens:** Apex examples in documentation heavily favor static methods. LLMs replicate this pattern, but static calls create hard-wired dependencies that cannot be replaced in tests. There is no way to inject a stub for `PricingService` or `InventoryService`.

**Correct pattern:**

```apex
public class OrderService {
    private IPricingService pricingService;
    private IInventoryService inventoryService;

    public OrderService(IPricingService pricing, IInventoryService inventory) {
        this.pricingService = pricing;
        this.inventoryService = inventory;
    }

    public void processOrders(List<Order> orders) {
        pricingService.calculateTotals(orders);
        inventoryService.reserveStock(orders);
    }
}
```

**Detection hint:** Service classes where every public method is `static` and calls other `ServiceClassName.staticMethod()` directly.

---

## Anti-Pattern 3: Building a domain layer that mutates records AND performs DML

**What the LLM generates:**

```apex
public class AccountDomain {
    public static void applyDiscount(List<Account> accounts, Decimal pct) {
        for (Account a : accounts) {
            a.Discount__c = pct;
        }
        update accounts; // Domain should not own DML
    }
}
```

**Why it happens:** LLMs try to make each method "complete." But if the domain layer performs DML, the service layer loses control over transaction boundaries — it cannot batch multiple domain operations into a single DML call or wrap them in a savepoint.

**Correct pattern:**

```apex
public class AccountDomain {
    public static void applyDiscount(List<Account> accounts, Decimal pct) {
        for (Account a : accounts) {
            a.Discount__c = pct;
        }
        // Return mutated records — let the service layer decide when to DML
    }
}

// In the service layer:
AccountDomain.applyDiscount(accounts, 0.15);
AccountDomain.setStatus(accounts, 'Preferred');
update accounts; // Single DML for both mutations
```

**Detection hint:** `update ` or `insert ` DML statements inside a class whose name ends in `Domain`.

---

## Anti-Pattern 4: Creating a factory that returns concrete types instead of interfaces

**What the LLM generates:**

```apex
public class ServiceFactory {
    public static AccountService getAccountService() {
        return new AccountService();
    }
}
```

**Why it happens:** LLMs generate the simplest possible factory. Returning a concrete class means the factory provides no test-time substitution benefit — callers are still coupled to the real implementation.

**Correct pattern:**

```apex
public class ServiceFactory {
    @TestVisible
    private static IAccountService mockInstance;

    public static IAccountService getAccountService() {
        if (mockInstance != null) return mockInstance;
        return new AccountService();
    }
}

// In test:
ServiceFactory.mockInstance = new AccountServiceStub();
```

**Detection hint:** Factory method return types that are concrete classes rather than interfaces — look for `public static [A-Z]\w+Service get` without a preceding `I` in the return type.

---

## Anti-Pattern 5: Putting all business logic in the trigger handler, calling it a "framework"

**What the LLM generates:**

```apex
public class AccountTriggerHandler {
    public void afterUpdate(List<Account> newList, Map<Id, Account> oldMap) {
        // 200 lines of validation, field calculation, callout queueing,
        // child record updates, and email sending all in this one method
    }
}
```

**Why it happens:** LLMs see "trigger handler pattern" and move code out of the trigger body into a handler class. But they dump everything into the handler instead of delegating to service and domain layers — the handler becomes a god-class that is just as untestable as a fat trigger.

**Correct pattern:**

```apex
public class AccountTriggerHandler {
    public void afterUpdate(List<Account> newList, Map<Id, Account> oldMap) {
        List<Account> statusChanged = filterStatusChanged(newList, oldMap);
        if (!statusChanged.isEmpty()) {
            AccountService.processStatusChange(statusChanged);
        }
    }

    private List<Account> filterStatusChanged(List<Account> newList, Map<Id, Account> oldMap) {
        List<Account> changed = new List<Account>();
        for (Account a : newList) {
            if (a.Status__c != oldMap.get(a.Id).Status__c) {
                changed.add(a);
            }
        }
        return changed;
    }
}
```

**Detection hint:** A trigger handler class with methods longer than 50 lines that contain SOQL, DML, and business validation all together.

---

## Anti-Pattern 6: Generating a selector with no field set reuse

**What the LLM generates:**

```apex
public class ContactSelector {
    public static List<Contact> getByAccountId(Id accountId) {
        return [SELECT Id, FirstName, LastName FROM Contact WHERE AccountId = :accountId];
    }
    public static List<Contact> getByEmail(String email) {
        return [SELECT Id, FirstName, LastName, Email, Phone FROM Contact WHERE Email = :email];
    }
}
```

**Why it happens:** LLMs generate each query independently, hard-coding field lists. When a new field is needed, every method must be updated. This defeats the purpose of centralizing queries.

**Correct pattern:**

```apex
public class ContactSelector {
    private static final List<String> BASE_FIELDS = new List<String>{
        'Id', 'FirstName', 'LastName', 'Email', 'Phone', 'AccountId'
    };

    private static String baseQuery() {
        return 'SELECT ' + String.join(BASE_FIELDS, ', ') + ' FROM Contact';
    }

    public static List<Contact> getByAccountId(Id accountId) {
        return Database.query(baseQuery() + ' WHERE AccountId = :accountId');
    }

    public static List<Contact> getByEmail(String email) {
        return Database.query(baseQuery() + ' WHERE Email = :email');
    }
}
```

**Detection hint:** Multiple SOQL queries in the same selector class with overlapping but inconsistent field lists.
