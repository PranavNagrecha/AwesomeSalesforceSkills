# Template — Apex Class Decomposition Plan

Use this template when planning the split of an existing Apex class into Domain / Service / Selector layers using the canonical base classes in `templates/apex/`.

---

## 1. Inventory the source class

| Field | Value |
|---|---|
| Source class | `<ClassName>.cls` |
| Line count | `<n>` |
| SObjects touched | `<list>` |
| Number of `[SELECT` occurrences | `<n>` |
| Number of DML statements (`insert` / `update` / `delete` / `upsert` / `merge`) | `<n>` |
| Per-record loops with validation / derivation | `<n>` |
| HTTP callouts | `<yes / no>` |
| Test coverage of source class | `<%>` |

---

## 2. Decomposition decision flow

```
START: should I split <ClassName>?
  |
  |-- Class < 100 lines AND single responsibility?
  |     -> YES -> DO NOT split. Stop.
  |
  |-- Class is a throwaway / one-time migration?
  |     -> YES -> DO NOT split. Stop.
  |
  |-- ANY of:
  |     - line count > 400, OR
  |     - SOQL + DML + per-record rules in one class, OR
  |     - same SObject queried in 3+ places, OR
  |     - business logic inside trigger body / handler with embedded SOQL
  |     -> YES -> SPLIT. Continue.
  |
  -> NONE of the above -> revisit when the next change exposes a signal.
```

---

## 3. Map old blocks to new classes

| Old block (line range) | New class | New method | Base class |
|---|---|---|---|
| `[SELECT ... FROM Account ...]` (lines 40–48) | `AccountsSelector` | `selectByIdWithRevenue(Id)` | `BaseSelector` |
| `[SELECT ... FROM Contact ...]` (lines 55–60) | `ContactsSelector` | `selectByAccountIds(Set<Id>)` | `BaseSelector` |
| Per-record revenue rollup loop (lines 90–140) | `AccountsDomain` | `applyMergeRules(List<Account>)` | `BaseDomain` |
| Savepoint + DML orchestration (lines 200–260) | `AccountMergeService` | `merge(Id, List<Id>)` | `BaseService` |
| Trigger dispatch (if applicable) | `<X>TriggerHandler` | `run()` | (none) |

---

## 4. Extraction order (lowest risk first)

- [ ] **Step 1 — Extract Selector(s).** Replace inline `[SELECT ...]` with calls to `<X>Selector` methods named by intent. Run all tests; expect zero behaviour change.
- [ ] **Step 2 — Extract Service.** Move DML, savepoint handling, callouts, and orchestration into `<X>Service extends BaseService`. Use `beginTransaction()` and `logAndRethrow()`. Run all tests.
- [ ] **Step 3 — Extract Domain.** Move per-record validation and derivation into `<X>Domain extends BaseDomain` operating on `List<SObject>` (and `oldMap` if needed). Run all tests.
- [ ] **Step 4 — Reduce trigger handler to dispatch only.** No business rules, no SOQL, no DML in the handler body.

---

## 5. Example — before / after split

### Before — `AccountManager.cls` (612 lines)

A single class doing SOQL on Account + Contact, per-record revenue rollup rules, savepoint + DML orchestration for a merge use case.

### After

```apex
// Selector — SOQL only
public with sharing class AccountsSelector extends BaseSelector {
    public Account selectByIdWithRevenue(Id accountId) {
        assertNotNull(accountId, 'accountId');
        return [SELECT Id, Name, OwnerId, AnnualRevenue
                FROM Account WHERE Id = :accountId WITH USER_MODE];
    }
    public List<Account> selectByIds(Set<Id> ids) {
        return [SELECT Id, Name, OwnerId
                FROM Account WHERE Id IN :ids WITH USER_MODE];
    }
}

// Domain — per-record rules only
public with sharing class AccountsDomain extends BaseDomain {
    public AccountsDomain(List<Account> records) { super(records); }
    public void applyMergeRules(List<Account> dupes) {
        Account master = (Account) records[0];
        Decimal total = master.AnnualRevenue == null ? 0 : master.AnnualRevenue;
        for (Account d : dupes) {
            if (d.AnnualRevenue != null) total += d.AnnualRevenue;
        }
        master.AnnualRevenue = total;
    }
}

// Service — orchestration + transaction
public with sharing class AccountMergeService extends BaseService {
    private final AccountsSelector accountsSel = new AccountsSelector();
    private final ContactsSelector contactsSel = new ContactsSelector();

    public void merge(Id masterId, List<Id> dupeIds) {
        Savepoint sp = beginTransaction();
        try {
            Account master = accountsSel.selectByIdWithRevenue(masterId);
            List<Account> dupes = accountsSel.selectByIds(new Set<Id>(dupeIds));
            List<Contact> dupeContacts = contactsSel.selectByAccountIds(new Set<Id>(dupeIds));

            new AccountsDomain(new List<Account>{ master }).applyMergeRules(dupes);

            update master;
            for (Contact c : dupeContacts) c.AccountId = masterId;
            update dupeContacts;
            delete dupes;
            commitTransaction();
        } catch (Exception e) {
            rollbackTransaction(sp);
            logAndRethrow('AccountMergeService.merge', e);
        }
    }
}
```

---

## 6. Verification

Confirm each item before considering the split done:

- [ ] No `[SELECT` remains outside a class extending `BaseSelector`.
- [ ] No `insert` / `update` / `delete` / `upsert` / `merge` inside any class extending `BaseSelector`.
- [ ] No `[SELECT` / DML / `Http`-callout inside any class extending `BaseDomain`.
- [ ] Trigger handler body contains only dispatch — no business rules.
- [ ] All Service entry points use `beginTransaction()` + `rollbackTransaction()` for transactional work, and `logAndRethrow(source, e)` for error handling.
- [ ] Cross-Service dependencies typed against an interface, not a concrete class.
- [ ] `python3 skills/apex/apex-class-decomposition-pattern/scripts/check_apex_class_decomposition_pattern.py <path-to-cls-files>` exits 0.
- [ ] All existing tests pass; new Domain methods covered by Domain-only unit tests with no DML.
