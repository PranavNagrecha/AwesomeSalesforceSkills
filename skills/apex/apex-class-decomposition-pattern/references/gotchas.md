# Gotchas — Apex Class Decomposition Pattern

Subtle traps when applying the lightweight Domain / Service / Selector pattern from `templates/apex/`.

---

## 1. Extending `BaseSelector` does not magically scope queries to one SObject

**What happens:** developers assume that subclassing `BaseSelector` enforces "this class queries only Account." It doesn't. `BaseSelector` is intentionally minimal — it exposes `userMode()`, `systemMode()`, `commaSeparated()`, and `assertNotNull()`. It does NOT take an `SObjectType` in its constructor and does NOT enforce that all methods query the same SObject.

**When it occurs:** any time someone adds a "convenience" cross-object SOQL to an existing Selector.

**How to avoid:** discipline — one Selector per SObject, queries named by intent (`selectByIds`, `selectActiveByOwner`), never a generic `runQuery(String soql)` escape hatch. If you need the SObjectType wiring of fflib's `fflib_SObjectSelector`, see `apex/fflib-enterprise-patterns`.

---

## 2. Domain operates on `Trigger.new` collection — never on individual records

**What happens:** a Domain method written as `validate(Account a)` invites callers to loop OUTSIDE the Domain, which becomes a per-record SOQL bug the day someone adds a parent lookup.

**When it occurs:** when the Domain API surface is shaped one-record-at-a-time instead of bulk-collection-at-a-time.

**How to avoid:** every Domain method **iterates the collection itself**:

```apex
// WRONG
public void validate(Account a) { ... }
for (Account a : accounts) new AccountsDomain(...).validate(a);  // loop outside Domain

// RIGHT
public void validateAll() {
    for (Account a : (List<Account>) records) { ... }
}
```

`BaseDomain` constructors accept a `List<SObject>` (and optional `oldMap`) precisely to enforce bulk shape.

---

## 3. Service must not directly fire its own triggers (recursive entry)

**What happens:** a Service that does `update accounts` re-enters the Account trigger, which calls back into a handler, which may call back into the same Service. Without a recursion guard you get `LimitException` or duplicated side effects.

**When it occurs:** any time a Service updates the same SObject whose handler called it (directly or indirectly).

**How to avoid:** either (a) gate the handler with a static recursion flag (see `apex/trigger-framework`), (b) have the Service set a context flag the handler reads, or (c) restructure so the trigger-side and Service-side paths are not both performing the same orchestration. The decomposition pattern does NOT solve recursion on its own.

---

## 4. Cross-Service calls should go through interfaces, not concrete types

**What happens:** when `OpportunityCloseService` declares a field of type `AccountRevenueService`, the two are welded together — there is no way to stub the dependency in a unit test without DML.

**When it occurs:** every time someone writes `private AccountRevenueService rev = new AccountRevenueService();`.

**How to avoid:**

```apex
public interface IAccountRevenueService {
    void recalculate(Set<Id> accountIds);
}

public with sharing class AccountRevenueService extends BaseService implements IAccountRevenueService { ... }

public with sharing class OpportunityCloseService extends BaseService {
    @TestVisible private IAccountRevenueService revenueSvc = new AccountRevenueService();
    // tests can assign a stub implementation
}
```

---

## 5. `BaseService.beginTransaction()` returns a `Savepoint` — not a transaction object

**What happens:** the method name suggests a richer transaction abstraction, but it literally calls `Database.setSavepoint()`. That means: it costs **1 DML statement** against the 150-statement governor limit, and the corresponding `rollbackTransaction(sp)` costs another.

**When it occurs:** any time a Service is called many times in one transaction (e.g., from a batch job).

**How to avoid:** know the cost. All the rules from `apex/apex-savepoint-and-rollback` apply — most importantly: never call rollback after an HTTP callout in the same transaction.

---

## 6. Plural-name collision: `Accounts` Domain vs `Account` SObject

**What happens:** renaming `AccountsDomain` to bare `Accounts` "for readability" collides with the `Account` SObject name in subtle ways (especially across namespaces) and breaks the searchability convention this repo standardises on.

**When it occurs:** when an enthusiastic refactor strips the `Domain` suffix.

**How to avoid:** keep `<X>Domain`, `<X>Service`, `<X>Selector` exactly. Suffixes are load-bearing.

---

## 7. `with sharing` on Domain, `inherited sharing` on Selector

**What happens:** `BaseDomain` is `with sharing`, but `BaseSelector` is `inherited sharing` so Selectors inherit the caller's sharing context. Downgrading `BaseSelector` to `with sharing` "to be safer" silently breaks legitimate `WITHOUT_SHARING` callers (e.g., scheduled batch jobs).

**When it occurs:** during a security review where someone "tightens" the base class without auditing callers.

**How to avoid:** treat the `inherited sharing` declaration on `BaseSelector` as load-bearing. If you need to change it, audit every caller and document the reason.

---

## 8. A Selector with no methods is worse than no Selector

**What happens:** auto-generating empty `<X>Selector` shells "in case we need them" creates dead files that lint warnings ignore and refactors must keep up to date.

**When it occurs:** when an LLM or a new contributor decides to "set up the architecture" up front.

**How to avoid:** create a Selector the moment a SOQL query needs a home — not before.
