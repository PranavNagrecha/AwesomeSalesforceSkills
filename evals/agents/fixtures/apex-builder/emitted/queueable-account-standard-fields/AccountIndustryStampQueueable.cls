/**
 * AccountIndustryStampQueueable
 *
 * Rewrites Account.Description with a standard "Industry: <value>" line
 * for every Account whose Industry changed. Uses only standard fields so
 * it compiles cleanly against a fresh scratch org.
 *
 * Emitted by apex-builder — conforms to templates/apex/BaseService.cls pattern.
 * Every SOQL path uses WITH USER_MODE; every DML path goes through standard update.
 */
public with sharing class AccountIndustryStampQueueable implements Queueable {

    private final Set<Id> accountIds;

    public AccountIndustryStampQueueable(Set<Id> accountIds) {
        this.accountIds = accountIds == null ? new Set<Id>() : accountIds;
    }

    public void execute(QueueableContext context) {
        if (accountIds.isEmpty()) {
            return;
        }
        List<Account> toUpdate = new List<Account>();
        for (Account a : [
            SELECT Id, Industry, Description
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ]) {
            a.Description = stamp(a);
            toUpdate.add(a);
        }
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }

    private String stamp(Account a) {
        String industry = a.Industry == null ? 'Unknown' : a.Industry;
        return 'Industry: ' + industry;
    }
}
