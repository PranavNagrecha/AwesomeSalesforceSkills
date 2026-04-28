# Examples — Apex Class Decomposition Pattern

Three realistic before/after splits using the canonical base classes from `templates/apex/`.

---

## Example 1 — 600-line monolith refactor

### Before

`AccountManager.cls` (612 lines) — does everything for the Account merge use case:

```apex
public with sharing class AccountManager {

    public void mergeAccounts(Id masterId, List<Id> dupeIds) {
        // 40 lines of validation against masterId / dupeIds
        // ...

        // Inline SOQL
        Account master = [
            SELECT Id, Name, OwnerId, AnnualRevenue
            FROM Account
            WHERE Id = :masterId
            WITH USER_MODE
        ];
        List<Account> dupes = [
            SELECT Id, Name, OwnerId
            FROM Account
            WHERE Id IN :dupeIds
            WITH USER_MODE
        ];
        List<Contact> dupeContacts = [
            SELECT Id, AccountId
            FROM Contact
            WHERE AccountId IN :dupeIds
            WITH USER_MODE
        ];

        // 80 lines of business rules: revenue rollup, owner conflict, name precedence
        // ...

        // DML mixed with savepoint
        Savepoint sp = Database.setSavepoint();
        try {
            update master;
            for (Contact c : dupeContacts) c.AccountId = masterId;
            update dupeContacts;
            delete dupes;
        } catch (Exception e) {
            Database.rollback(sp);
            throw e;
        }
    }
}
```

Symptoms: 612 lines, three SObjects, SOQL + DML + per-record rules + transaction handling all in one class. Violates every signal in `SKILL.md`.

### After (extract in order: Selector → Service → Domain)

**Step 1 — `AccountsSelector extends BaseSelector`** (SOQL only):

```apex
public with sharing class AccountsSelector extends BaseSelector {

    public Account selectByIdWithRevenue(Id accountId) {
        assertNotNull(accountId, 'accountId');
        return [
            SELECT Id, Name, OwnerId, AnnualRevenue
            FROM Account
            WHERE Id = :accountId
            WITH USER_MODE
        ];
    }

    public List<Account> selectByIds(Set<Id> ids) {
        return [
            SELECT Id, Name, OwnerId
            FROM Account
            WHERE Id IN :ids
            WITH USER_MODE
        ];
    }
}

public with sharing class ContactsSelector extends BaseSelector {

    public List<Contact> selectByAccountIds(Set<Id> accountIds) {
        return [
            SELECT Id, AccountId
            FROM Contact
            WHERE AccountId IN :accountIds
            WITH USER_MODE
        ];
    }
}
```

**Step 2 — `AccountMergeService extends BaseService`** (orchestration, transaction):

```apex
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

**Step 3 — `AccountsDomain extends BaseDomain`** (per-record rules):

```apex
public with sharing class AccountsDomain extends BaseDomain {

    public AccountsDomain(List<Account> records) { super(records); }

    public void applyMergeRules(List<Account> dupes) {
        Account master = (Account) records[0];
        Decimal totalRevenue = master.AnnualRevenue == null ? 0 : master.AnnualRevenue;
        for (Account d : dupes) {
            if (d.AnnualRevenue != null) totalRevenue += d.AnnualRevenue;
        }
        master.AnnualRevenue = totalRevenue;
    }
}
```

Result: four small, single-responsibility classes; SOQL isolated; DML and transactions in one place; per-record rules unit-testable without DML.

---

## Example 2 — Trigger with embedded SOQL

### Before

`OpportunityTrigger.trigger`:

```apex
trigger OpportunityTrigger on Opportunity (before update) {
    Set<Id> accountIds = new Set<Id>();
    for (Opportunity o : Trigger.new) accountIds.add(o.AccountId);

    Map<Id, Account> accounts = new Map<Id, Account>(
        [SELECT Id, Type FROM Account WHERE Id IN :accountIds WITH USER_MODE]
    );

    for (Opportunity o : Trigger.new) {
        if (accounts.get(o.AccountId)?.Type == 'Prospect' && o.Amount > 100000) {
            o.addError('Prospects cannot have deals over $100k.');
        }
    }
}
```

Symptoms: SOQL inside the trigger body, no handler class, business rule inline.

### After

**`AccountsSelector`** gets `selectByIds`. **`OpportunityTriggerHandler`** dispatches:

```apex
trigger OpportunityTrigger on Opportunity (before update) {
    new OpportunityTriggerHandler().run();
}

public with sharing class OpportunityTriggerHandler {
    public void run() {
        if (Trigger.isBefore && Trigger.isUpdate) {
            Set<Id> accountIds = new Set<Id>();
            for (Opportunity o : (List<Opportunity>) Trigger.new) accountIds.add(o.AccountId);
            Map<Id, Account> accounts = new Map<Id, Account>(
                new AccountsSelector().selectByIds(accountIds)
            );
            new OpportunitiesDomain((List<Opportunity>) Trigger.new)
                .validateProspectAmountCap(accounts);
        }
    }
}

public with sharing class OpportunitiesDomain extends BaseDomain {
    public OpportunitiesDomain(List<Opportunity> records) { super(records); }

    public void validateProspectAmountCap(Map<Id, Account> accountsById) {
        for (Opportunity o : (List<Opportunity>) records) {
            Account a = accountsById.get(o.AccountId);
            if (a != null && a.Type == 'Prospect' && o.Amount != null && o.Amount > 100000) {
                o.addError('Prospects cannot have deals over $100k.');
            }
        }
    }
}
```

The trigger now contains zero logic; the handler dispatches; the Selector queries; the Domain validates.

---

## Example 3 — Service that grew its own SOQL

### Before

`OpportunityCloseService` started clean but accumulated convenience SOQL:

```apex
public with sharing class OpportunityCloseService extends BaseService {

    public void closeWon(Id oppId) {
        // grew over time
        Opportunity opp = [SELECT Id, Amount, AccountId FROM Opportunity WHERE Id = :oppId WITH USER_MODE];
        Account acct = [SELECT Id, AnnualRevenue FROM Account WHERE Id = :opp.AccountId WITH USER_MODE];

        opp.StageName = 'Closed Won';
        acct.AnnualRevenue = (acct.AnnualRevenue == null ? 0 : acct.AnnualRevenue) + opp.Amount;

        update opp;
        update acct;
    }
}
```

Symptom: a Service is issuing SOQL directly. Even if small, this breaks the rule that SOQL only lives in a Selector — and the next change will copy-paste a third query.

### After

```apex
public with sharing class OpportunitiesSelector extends BaseSelector {
    public Opportunity selectByIdWithAccount(Id oppId) {
        return [SELECT Id, Amount, AccountId FROM Opportunity WHERE Id = :oppId WITH USER_MODE];
    }
}

public with sharing class OpportunityCloseService extends BaseService {

    private final OpportunitiesSelector oppSel = new OpportunitiesSelector();
    private final AccountsSelector acctSel = new AccountsSelector();

    public void closeWon(Id oppId) {
        Opportunity opp = oppSel.selectByIdWithAccount(oppId);
        Account acct = acctSel.selectByIdWithRevenue(opp.AccountId);

        opp.StageName = 'Closed Won';
        acct.AnnualRevenue = (acct.AnnualRevenue == null ? 0 : acct.AnnualRevenue) + opp.Amount;

        update opp;
        update acct;
    }
}
```

The Service is now back to orchestration only; the next reuse of these queries is one line, not a copy-paste.
