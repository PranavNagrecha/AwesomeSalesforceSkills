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

---

## Anti-Pattern 7: Wrapping every DML in its own savepoint and calling it a unit of work

**What the LLM generates:**

```apex
public class OrderService {
    public void placeOrder(Order o, List<OrderItem> items, Shipment__c shipment) {
        Savepoint sp1 = Database.setSavepoint();
        insert o;
        Savepoint sp2 = Database.setSavepoint();
        insert items;
        Savepoint sp3 = Database.setSavepoint();
        try {
            insert shipment;
        } catch (DmlException e) {
            Database.rollback(sp1);   // sp2 and sp3 are now invalid
            ApplicationLogger.error('OrderService.placeOrder', e);  // and this row is gone too
            throw e;
        }
    }
}
```

**Why it happens:** "Unit of work" reads like "a transaction object", and LLMs reach for one savepoint per step by analogy with nested transactions in other platforms. On this platform three things go wrong at once. Each savepoint costs one of the 150 DML statements per transaction (Apex Developer Guide L8691, L19554). Rolling back to `sp1` invalidates `sp2` and `sp3`, so touching either afterwards is a run-time error (L8686–8688). And the logger's own `insert` happens *after* the savepoint, so the rollback deletes the audit row the catch block just created (L8682–8684).

**Correct pattern:**

```apex
public with sharing class OrderService extends BaseService {
    public void placeOrder(Order o, List<OrderItem> items, Shipment__c shipment) {
        Savepoint sp = beginTransaction();     // exactly one, at the method boundary
        try {
            insert o;
            for (OrderItem i : items) { i.OrderId = o.Id; }
            insert items;
            shipment.Order__c = o.Id;
            insert shipment;
            commitTransaction();
        } catch (Exception e) {
            rollbackTransaction(sp);           // roll back FIRST
            logAndRethrow('OrderService.placeOrder', e);   // then log, so the row survives
        }
    }
}
```

**Detection hint:** More than one `Database.setSavepoint()` in a single method, or a `Database.rollback(` that appears *after* a logging call inside the same `catch` block.

---

## Anti-Pattern 8: A `Type.forName` factory with no null guard, no interface check, and no fallback

**What the LLM generates:**

```apex
public class StrategyFactory {
    public static ICaseEscalationStrategy get(String origin) {
        Strategy__mdt row = Strategy__mdt.getInstance(origin);
        return (ICaseEscalationStrategy) Type.forName(row.Apex_Class__c).newInstance();
    }
}
```

**Why it happens:** The Apex Reference Guide's own `Type` example is a three-line happy path, and LLMs reproduce its shape without the production guards. Every failure mode here is silent until run time: `getInstance` returns `null` for a missing developer name, `Type.forName` returns `null` for an inner class, a private class, or a class that was renamed since the row was written (Apex Reference Guide L241920–241922, L242076–242082), the cast throws if the class does not implement the interface, and `newInstance()` can only reach a no-argument constructor (L242303). None of these is a compile error, so the deploy is green and the trigger dies in production.

**Correct pattern:**

```apex
public with sharing class StrategyFactory {
    @TestVisible private static Map<String, ICaseEscalationStrategy> cache =
        new Map<String, ICaseEscalationStrategy>();

    public ICaseEscalationStrategy get(String origin) {
        String key = String.isBlank(origin) ? '' : origin.toLowerCase();
        if (cache.containsKey(key)) { return cache.get(key); }

        Type resolved = Type.forName(classNameFor(key));      // may be null
        Object instance = resolved == null ? null : resolved.newInstance();
        ICaseEscalationStrategy strategy = (instance instanceof ICaseEscalationStrategy)
            ? (ICaseEscalationStrategy) instance
            : new DefaultCaseEscalationStrategy();            // named fallback, never null

        cache.put(key, strategy);
        return strategy;
    }

    @TestVisible
    private static void reset() { cache = new Map<String, ICaseEscalationStrategy>(); }
}
```

**Detection hint:** `Type.forName(` on the same expression as `.newInstance()` with no intervening null check, or a `(ISomething)` cast applied directly to `newInstance()`. Also flag any static mutable `Map`/`Set`/`List` in a factory with no `reset()` — a rollback does not clear it (Apex Developer Guide L8692–8693).

---

## Anti-Pattern 9: Declaring the outer class `with sharing` and assuming the inner classes inherit it

**What the LLM generates:**

```apex
public with sharing class CaseEscalationService {
    // The LLM believes this inner class is covered by the outer declaration.
    public class EscalationBatch implements Database.Batchable<SObject> {
        public Database.QueryLocator start(Database.BatchableContext bc) {
            return Database.getQueryLocator('SELECT Id FROM Case WHERE IsEscalated = false');
        }
        public void execute(Database.BatchableContext bc, List<Case> scope) { /* ... */ }
        public void finish(Database.BatchableContext bc) {}
    }
}
```

**Why it happens:** Nesting looks like containment, and the outer keyword looks like it applies to everything inside. It does not: "You can declare a sharing mode on both inner classes and outer classes. Inner classes don't adopt the sharing mode of the container class." (Apex Developer Guide L4931–4932.) The batch is also an asynchronous entry point, which changes the answer again — an `inherited sharing` class always runs `with sharing` for asynchronous operations (L4935–4936). And no sharing keyword of any kind enforces object- or field-level security (L4925–4926).

**Correct pattern:**

```apex
public with sharing class CaseEscalationService extends BaseService {
    public with sharing class EscalationBatch implements Database.Batchable<SObject> {
        public Database.QueryLocator start(Database.BatchableContext bc) {
            // AccessLevel is separate from sharing: this enforces CRUD + FLS too.
            return Database.getQueryLocatorWithBinds(
                'SELECT Id FROM Case WHERE IsEscalated = false',
                new Map<String, Object>(),
                AccessLevel.USER_MODE
            );
        }
        public void execute(Database.BatchableContext bc, List<Case> scope) { /* ... */ }
        public void finish(Database.BatchableContext bc) {}
    }
}
```

**Detection hint:** Any `class` declaration nested inside another class with no `with sharing` / `without sharing` / `inherited sharing` keyword of its own. Note that this is a *readability and version-safety* defect as well as a behavioural one: from API version 67.0 an undeclared class runs `with sharing` (L4961), so the same source means different things at different API versions unless the keyword is written down.
