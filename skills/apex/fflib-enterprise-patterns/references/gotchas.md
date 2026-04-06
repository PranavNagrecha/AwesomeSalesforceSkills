# Gotchas — fflib Enterprise Patterns

Non-obvious Salesforce platform behaviors that cause real production problems when using the fflib library.

## Gotcha 1: UnitOfWork SObject Registration Order Must Match Data Model Hierarchy

**What happens:** `commitWork()` throws `REQUIRED_FIELD_MISSING` or `ENTITY_IS_DELETED` errors even though all records were correctly registered, because the SObject type list passed to the UnitOfWork factory does not reflect the parent-child insertion/deletion order.

**When it occurs:** When you register `Contact` before `Account` in the SObject type list but use `registerRelationship` to wire a Contact's AccountId to an uncommitted Account. The UnitOfWork inserts in list order, so it tries to insert Contacts before their parent Accounts exist.

**How to avoid:** Always list parent SObjects before child SObjects in the UnitOfWork factory's SObject type list. For deletes, reverse the order (children before parents). If a single UnitOfWork handles both inserts and deletes across different hierarchies, split into separate UnitOfWork instances or carefully order to satisfy both directions.

---

## Gotcha 2: Domain Constructor Signature Is Enforced by Reflection

**What happens:** The trigger handler throws `System.TypeException` or `fflib_SObjectDomain.DomainException` at runtime when dispatching to the Domain class.

**When it occurs:** When the Domain class constructor does not accept `List<SObject>` (or `List<YourSpecificSObject>`) as its parameter. The `fflib_SObjectDomain.triggerHandler()` uses `Type.newInstance()` and casts the result, so the constructor signature must match exactly what the base class expects.

**How to avoid:** Always include a constructor that accepts `List<SObject>` (or the concrete SObject list type) and calls `super(records)`. If you add a second constructor for convenience, keep the required one intact. Example:

```apex
public class AccountsDomain extends fflib_SObjectDomain {
    public AccountsDomain(List<Account> records) {
        super(records, Account.SObjectType);
    }
}
```

---

## Gotcha 3: Selector FLS Enforcement Is Off by Default

**What happens:** Queries return all fields in `getSObjectFieldList()` regardless of the running user's field-level security, potentially exposing sensitive data.

**When it occurs:** When you extend `fflib_SObjectSelector` but do not override `isEnforcingFLS()` to return `true`. The base class defaults to `false`.

**How to avoid:** Override `isEnforcingFLS()` in every Selector and return `true` unless there is a documented internal-process reason to bypass FLS. Security reviewers should flag any Selector that returns `false` or does not override this method.

---

## Gotcha 4: Application Factory Must Be Updated When Adding New SObjects

**What happens:** `Application.Selector.newInstance(CustomObject__c.SObjectType)` throws a runtime exception because the SObject type has no registered binding in the Application factory.

**When it occurs:** When a developer creates a new Domain or Selector class but forgets to add the corresponding `put()` call in `Application.cls`. The factory map has no entry for the SObject type, so the factory cannot resolve the implementation.

**How to avoid:** Treat `Application.cls` as part of the Definition of Done for any new fflib layer class. Every new Domain, Selector, or Service class must have a corresponding registration in the Application factory. Add a test that iterates all registered SObject types and instantiates each binding to catch stale registrations.

---

## Gotcha 5: UnitOfWork registerDirty Requires Records With Id

**What happens:** `commitWork()` attempts an insert instead of an update, or throws an error, when you call `registerDirty` on an SObject record that has no Id populated.

**When it occurs:** When you create a new SObject instance (e.g., `new Account(Name = 'Test')`) and register it as dirty instead of registering it as new. The UnitOfWork uses the presence of an Id to distinguish inserts from updates.

**How to avoid:** Use `registerNew` for records without an Id and `registerDirty` only for records that were queried and already have an Id. If modifying in-memory records from a Selector query, they already have Ids and should be registered as dirty.

---

## Gotcha 6: Recursive Trigger Invocation Through Domain Layer

**What happens:** `onAfterUpdate` fires, performs DML via UnitOfWork that updates the same SObject, which fires the trigger again, looping until governor limits kill the transaction.

**When it occurs:** When Domain `onAfterUpdate` logic registers an update on the same SObject type back through UnitOfWork, and no recursion guard is in place.

**How to avoid:** Use `fflib_SObjectDomain`'s built-in `getTriggerEvent()` and static flags to detect re-entry. Alternatively, apply a static `Set<Id>` guard in the Domain class to track which records have already been processed. The Service layer should be the boundary that decides whether re-entry is expected.

---

## Gotcha 7: Apex Mocks Require Application Factory — Direct Construction Defeats Mocking

**What happens:** Tests that directly instantiate Selectors or Services (e.g., `new OpportunitiesSelector()`) cannot be stubbed with Apex Mocks, so tests remain tightly coupled to real SOQL and DML.

**When it occurs:** When developers bypass the Application factory in production code by constructing layer classes directly instead of calling `Application.Selector.newInstance(...)`.

**How to avoid:** Always obtain layer class instances through the Application factory in production code. Direct construction should only appear inside the factory registration itself. In tests, use `Application.Selector.setMock(...)` or `Application.Service.setMock(...)` to inject stubs.
