# LLM Anti-Patterns — Apex Class Decomposition Pattern

Common mistakes AI coding assistants make when asked to decompose an Apex class into Domain / Service / Selector. These help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Putting SOQL in a Service "for convenience"

**What the LLM generates:** a Service method that begins with `Account a = [SELECT Id, Name FROM Account WHERE Id = :id WITH USER_MODE];` because "the change is small and adding a Selector feels heavyweight."

**Why it happens:** training data is full of Apex examples where SOQL lives wherever it's used. The LLM optimises for line count, not for the architectural seam.

**Correct pattern:**

```apex
// Selector
public with sharing class AccountsSelector extends BaseSelector {
    public Account selectById(Id id) {
        return [SELECT Id, Name FROM Account WHERE Id = :id WITH USER_MODE];
    }
}
// Service
public with sharing class MyService extends BaseService {
    private final AccountsSelector accountsSel = new AccountsSelector();
    public void doWork(Id id) {
        Account a = accountsSel.selectById(id);
        // ...
    }
}
```

**Detection hint:** grep for `\[\s*SELECT` inside any class extending `BaseService`. The skill-local checker (`scripts/check_apex_class_decomposition_pattern.py`) reports this as a P0 / P1 depending on context.

---

## Anti-Pattern 2: Making the Selector stateful with cached results

**What the LLM generates:** a Selector with `private static Map<Id, Account> cache` that short-circuits repeated calls to "improve performance."

**Why it happens:** the LLM sees a perceived inefficiency (repeated identical queries) and reaches for memoisation, not realising it breaks the stateless contract and surfaces stale data across test methods (static state survives across them).

**Correct pattern:**

```apex
// Selector remains pure — no static caches.
public with sharing class AccountsSelector extends BaseSelector {
    public List<Account> selectByIds(Set<Id> ids) {
        return [SELECT Id, Name FROM Account WHERE Id IN :ids WITH USER_MODE];
    }
}
// If caching is genuinely required, use Platform Cache or a request-scoped cache class
// owned by the Service — never the Selector.
```

**Detection hint:** grep for `static\s+Map` or `static\s+List` inside any class extending `BaseSelector`.

---

## Anti-Pattern 3: Routing per-record validation through the Service instead of the Domain

**What the LLM generates:** `accountService.validate(accounts)` that loops through records inside the Service body.

**Why it happens:** the LLM treats "Service" as the catch-all "business logic" layer (Java mental model) and forgets the Domain exists for per-record rules.

**Correct pattern:**

```apex
// Domain owns per-record rules.
public with sharing class AccountsDomain extends BaseDomain {
    public AccountsDomain(List<Account> records) { super(records); }
    public void validateAll() {
        for (Account a : (List<Account>) records) {
            if (String.isBlank(a.Name)) a.addError('Name required');
        }
    }
}
// Service orchestrates.
public with sharing class AccountSyncService extends BaseService {
    public void run(List<Account> accounts) {
        new AccountsDomain(accounts).validateAll();
        // then DML, callouts, transactions...
    }
}
```

**Detection hint:** grep for `validate` / `addError` inside any class extending `BaseService`.

---

## Anti-Pattern 4: Over-decomposing a 50-line utility

**What the LLM generates:** for a 50-line `CsvParser` utility, four files: `CsvParserDomain`, `CsvParserService`, `CsvParserSelector`, `CsvParserHandler` — three of them with one method, all of them holding `// TODO`.

**Why it happens:** the LLM applies the brief literally to every Apex class in sight without reading "When NOT to split."

**Correct pattern:** leave sub-100-line single-responsibility utilities as one class. The pattern applies to classes that touch SObjects with multiple responsibilities.

**Detection hint:** any new package where the Service / Domain / Selector files are each under ~30 lines and contain only one method.

---

## Anti-Pattern 5: Auto-generating empty Domain/Service/Selector trios for every SObject "just in case"

**What the LLM generates:** walks the SObject list and scaffolds `<X>Domain`, `<X>Service`, `<X>Selector` for every standard and custom object. The org now has 200 empty classes.

**Why it happens:** the LLM interprets "set up the architecture" as "create the whole shape up front."

**Correct pattern:** create the layer class the moment a real query / orchestration / validation needs a home. Empty shells are noise that pollutes search and slows IDE indexing.

**Detection hint:** any newly created `*Domain.cls` / `*Service.cls` / `*Selector.cls` with zero methods or only a constructor.

---

## Anti-Pattern 6: Calling another Service via its concrete class instead of an interface

**What the LLM generates:** `private AccountRevenueService rev = new AccountRevenueService();` inside another Service.

**Why it happens:** the LLM defaults to concrete types because the brief did not explicitly mention testability.

**Correct pattern:**

```apex
public interface IAccountRevenueService { void recalculate(Set<Id> ids); }
public with sharing class AccountRevenueService extends BaseService implements IAccountRevenueService { ... }

public with sharing class OpportunityCloseService extends BaseService {
    @TestVisible private IAccountRevenueService revenueSvc = new AccountRevenueService();
}
```

**Detection hint:** any Service field typed as a concrete `*Service` class without an `I*Service` interface.

---

## Anti-Pattern 7: Wrapping `BaseSelector` queries in `WITHOUT_SHARING` "to make tests pass"

**What the LLM generates:** changes a Selector method from `userMode()` to `systemMode()` because a test threw an FLS error.

**Why it happens:** the LLM optimises for the immediate test failure, not the security regression it introduces.

**Correct pattern:** fix the test setup (grant the permission via PermissionSet), or — if the bypass is genuinely required for a documented batch / integration context — keep `userMode()` as the default and add a separate, named, commented system-mode method that one specific caller invokes.

**Detection hint:** any Selector method that calls `systemMode()` without an accompanying `// SYSTEM-MODE JUSTIFICATION:` comment.
