/**
 * AccountHierarchyRebuildQueueable
 *
 * Recalculates Account.Hierarchy_Depth__c for accounts whose ParentId changed.
 * Emitted by apex-builder — conforms to templates/apex/BaseService.cls pattern.
 * Every SOQL path uses WITH USER_MODE; every DML path wraps SecurityUtils.
 *
 * Generated for run: {{run_id}}
 */
public with sharing class AccountHierarchyRebuildQueueable implements Queueable {

    private final Set<Id> accountIds;

    public AccountHierarchyRebuildQueueable(Set<Id> accountIds) {
        this.accountIds = accountIds == null ? new Set<Id>() : accountIds;
    }

    public void execute(QueueableContext context) {
        if (accountIds.isEmpty()) {
            return;
        }
        List<Account> toUpdate = new List<Account>();
        for (Account a : [
            SELECT Id, ParentId, Hierarchy_Depth__c
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ]) {
            a.Hierarchy_Depth__c = computeDepth(a);
            toUpdate.add(a);
        }
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }

    private Decimal computeDepth(Account a) {
        Decimal depth = 0;
        Id cursor = a.ParentId;
        Integer safety = 0;
        while (cursor != null && safety < 100) {
            depth += 1;
            cursor = null;
            safety += 1;
        }
        return depth;
    }
}
