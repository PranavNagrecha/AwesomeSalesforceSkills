# Examples — fflib Enterprise Patterns

## Example 1: Service Layer Coordinating UnitOfWork Across Parent-Child Records

**Context:** A service method needs to create an Account and related Contacts in a single transaction, where the Contact lookup to Account must be resolved automatically.

**Problem:** Without UnitOfWork, you would insert the Account first, capture its Id, assign it to each Contact, then insert Contacts. If the Contact insert fails, the Account insert has already committed and you have orphaned data.

**Solution:**

```apex
public class AccountService {

    public static void createAccountWithContacts(
        Account acc,
        List<Contact> contacts
    ) {
        fflib_ISObjectUnitOfWork uow = Application.UnitOfWork.newInstance();

        uow.registerNew(acc);

        for (Contact c : contacts) {
            uow.registerNew(c, Contact.AccountId, acc);
            // registerRelationship wires the lookup —
            // UnitOfWork resolves the Account Id after insert
        }

        uow.commitWork();
        // Single transaction: if Contacts fail, Account rolls back too
    }
}
```

**Why it works:** `registerRelationship` (the three-argument `registerNew`) tells UnitOfWork to populate `Contact.AccountId` with the parent Account's Id after the Account is inserted but before the Contact DML fires. The SObject type order in the UnitOfWork factory (`Account` before `Contact`) guarantees the insert sequence. A single `commitWork()` wraps everything in one savepoint.

---

## Example 2: Selector With FLS Enforcement and Custom Query Method

**Context:** Multiple service and domain classes need to query Opportunities by AccountId with a consistent field list and FLS enforcement.

**Problem:** When SOQL is scattered across services, field lists drift, FLS is inconsistently enforced, and adding a new field to the query requires updating multiple classes.

**Solution:**

```apex
public class OpportunitiesSelector extends fflib_SObjectSelector {

    public OpportunitiesSelector() {
        super();
    }

    public Schema.SObjectType getSObjectType() {
        return Opportunity.SObjectType;
    }

    public List<Schema.SObjectField> getSObjectFieldList() {
        return new List<Schema.SObjectField>{
            Opportunity.Id,
            Opportunity.Name,
            Opportunity.StageName,
            Opportunity.Amount,
            Opportunity.CloseDate,
            Opportunity.AccountId
        };
    }

    public override String getOrderBy() {
        return 'CloseDate DESC';
    }

    // Opt in to FLS enforcement
    public Boolean isEnforcingFLS() {
        return true;
    }

    public List<Opportunity> selectByAccountId(Set<Id> accountIds) {
        fflib_QueryFactory qf = newQueryFactory();
        qf.setCondition('AccountId IN :accountIds');
        return (List<Opportunity>) Database.query(qf.toSOQL());
    }
}
```

**Why it works:** Every query against Opportunity flows through this selector. The field list is defined once in `getSObjectFieldList()`. FLS enforcement is enabled via `isEnforcingFLS()`, so the query factory automatically strips fields the running user cannot read. Adding a new field to all Opportunity queries is a single-line change. Service classes call `((OpportunitiesSelector) Application.Selector.newInstance(Opportunity.SObjectType)).selectByAccountId(ids)` — and in tests, Apex Mocks can stub this call to return controlled data.

---

## Anti-Pattern: Direct DML Inside Domain Classes

**What practitioners do:** Developers put `insert`, `update`, or `delete` statements directly inside Domain `onAfterInsert` or `onAfterUpdate` methods, bypassing the UnitOfWork entirely.

**What goes wrong:** Direct DML inside a Domain class:
- Breaks the single-transaction guarantee that UnitOfWork provides. A failure in a later DML statement does not roll back the earlier one inside the Domain.
- Makes the Domain class untestable in isolation because you cannot mock the DML.
- Leads to governor limit pressure from multiple DML statements instead of the batched DML that UnitOfWork provides.

**Correct approach:** Domain classes should register work against the UnitOfWork passed to them by the Service layer. If the Domain needs to create child records in `onAfterInsert`, the Service should pass the UnitOfWork into the Domain method:

```apex
// In the Service layer
fflib_ISObjectUnitOfWork uow = Application.UnitOfWork.newInstance();
AccountsDomain domain = new AccountsDomain(accounts);
domain.createDefaultContacts(uow);
uow.commitWork();

// In the Domain class
public void createDefaultContacts(fflib_ISObjectUnitOfWork uow) {
    for (Account acc : (List<Account>) Records) {
        Contact c = new Contact(LastName = acc.Name + ' Default');
        uow.registerNew(c, Contact.AccountId, acc);
    }
    // No direct DML here — UnitOfWork handles it
}
```
