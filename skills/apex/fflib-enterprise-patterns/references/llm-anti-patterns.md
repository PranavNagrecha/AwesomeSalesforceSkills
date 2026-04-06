# LLM Anti-Patterns — fflib Enterprise Patterns

Common mistakes AI coding assistants make when generating or advising on fflib Enterprise Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Hallucinating fflib Method Signatures

**What the LLM generates:** Calls to methods that do not exist on `fflib_SObjectUnitOfWork`, such as `uow.registerInsert(record)`, `uow.addNew(record)`, or `uow.register(record, DmlType.INSERT)`.

**Why it happens:** LLMs blend naming conventions from other ORM/Unit-of-Work implementations (Java Hibernate, .NET Entity Framework) into Apex fflib output. The training data contains many UoW patterns from non-Apex languages.

**Correct pattern:**

```apex
// Correct fflib UnitOfWork methods:
uow.registerNew(record);               // insert
uow.registerDirty(record);             // update
uow.registerDeleted(record);           // delete
uow.registerNew(child, Contact.AccountId, parent); // insert with relationship
```

**Detection hint:** Any UnitOfWork method call that is not `registerNew`, `registerDirty`, `registerDeleted`, `registerRelationship`, or `commitWork` is likely hallucinated.

---

## Anti-Pattern 2: Constructing Layer Classes Directly Instead of Using Application Factory

**What the LLM generates:** Code like `OpportunitiesSelector sel = new OpportunitiesSelector();` or `AccountService svc = new AccountService();` in production code.

**Why it happens:** LLMs default to the simplest construction pattern. Direct instantiation is valid Apex, so it compiles, but it breaks the factory pattern that enables Apex Mocks test isolation.

**Correct pattern:**

```apex
// Selectors
OpportunitiesSelector sel = (OpportunitiesSelector)
    Application.Selector.newInstance(Opportunity.SObjectType);

// Services — typically called via static methods that internally use the factory
OpportunityService.closeOpportunities(oppIds);

// UnitOfWork
fflib_ISObjectUnitOfWork uow = Application.UnitOfWork.newInstance();
```

**Detection hint:** Look for `new <ClassName>Selector()` or `new <ClassName>Domain()` outside of Application factory registrations or constructor internals.

---

## Anti-Pattern 3: Missing super() Call in Domain Constructor

**What the LLM generates:** Domain class constructors that do not call `super(records)` or `super(records, sObjectType)`, or that accept non-standard parameters.

**Why it happens:** LLMs sometimes generate constructors that follow generic Apex class patterns instead of the fflib-specific constructor contract required by `triggerHandler()` reflection.

**Correct pattern:**

```apex
public class AccountsDomain extends fflib_SObjectDomain {
    public AccountsDomain(List<Account> records) {
        super(records, Account.SObjectType);
    }

    // Inner class required for trigger handler dispatch
    public class Constructor implements fflib_SObjectDomain.IConstructable {
        public fflib_SObjectDomain construct(List<SObject> records) {
            return new AccountsDomain((List<Account>) records);
        }
    }
}
```

**Detection hint:** Check that every Domain class has a `super(records` call in its constructor and an inner `Constructor` class implementing `IConstructable`.

---

## Anti-Pattern 4: Putting SOQL Directly in Service or Domain Classes

**What the LLM generates:** Inline SOQL queries in Service methods like `[SELECT Id, Name FROM Account WHERE Id IN :accountIds]` instead of routing through a Selector.

**Why it happens:** Inline SOQL is simpler and more common in Apex training data. LLMs optimize for conciseness and generate working code that violates the Selector pattern.

**Correct pattern:**

```apex
// Wrong — inline SOQL in service
List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :accountIds];

// Right — use the Selector via Application factory
AccountsSelector sel = (AccountsSelector)
    Application.Selector.newInstance(Account.SObjectType);
List<Account> accounts = sel.selectById(accountIds);
```

**Detection hint:** Any `[SELECT` statement outside a Selector class violates the pattern. Search for SOQL brackets in Service and Domain files.

---

## Anti-Pattern 5: Omitting FLS Enforcement in Selectors

**What the LLM generates:** Selector classes that never override `isEnforcingFLS()`, leaving the default `false` behavior active.

**Why it happens:** The base `fflib_SObjectSelector` class defaults to FLS-off for backward compatibility. LLMs generate working code without FLS because the base class compiles and runs fine without the override. Security is an additive step that LLMs skip.

**Correct pattern:**

```apex
public class AccountsSelector extends fflib_SObjectSelector {
    // Must override to enforce FLS
    public Boolean isEnforcingFLS() {
        return true;
    }

    // ... rest of selector
}
```

**Detection hint:** Grep Selector classes for `isEnforcingFLS`. If the method is absent or returns `false`, flag it for security review.

---

## Anti-Pattern 6: Registering UnitOfWork SObject Types in Wrong Order

**What the LLM generates:** UnitOfWork instantiation with child SObjects listed before parent SObjects, like `new List<SObjectType>{ Contact.SObjectType, Account.SObjectType }`.

**Why it happens:** LLMs list SObject types alphabetically or in the order they appear in the prompt, not in data-model hierarchy order. The significance of list order in UnitOfWork is a library-specific convention that general Apex training data does not emphasize.

**Correct pattern:**

```apex
// Correct: parents before children
Application.UnitOfWork.newInstance(
    new List<SObjectType>{
        Account.SObjectType,    // parent
        Contact.SObjectType,    // child of Account
        Case.SObjectType        // child of Account/Contact
    }
);
```

**Detection hint:** Compare the SObject type list against the data model. Any child SObject listed before its parent is a bug.

---

## Anti-Pattern 7: Creating Multiple UnitOfWork Instances When One Should Be Shared

**What the LLM generates:** Separate `Application.UnitOfWork.newInstance()` calls in each helper method within a single service operation, with separate `commitWork()` calls.

**Why it happens:** LLMs treat each method as independent. Without understanding the transactional scope, they create a new UnitOfWork per method for "encapsulation."

**Correct pattern:**

```apex
public static void processAccounts(Set<Id> accountIds) {
    fflib_ISObjectUnitOfWork uow = Application.UnitOfWork.newInstance();

    // Pass the SAME uow to all helper methods
    updateAccountFields(uow, accountIds);
    createRelatedContacts(uow, accountIds);
    logAuditRecords(uow, accountIds);

    // Single commit for the entire operation
    uow.commitWork();
}
```

**Detection hint:** Multiple `commitWork()` calls within a single top-level service method indicate fragmented transactions.
