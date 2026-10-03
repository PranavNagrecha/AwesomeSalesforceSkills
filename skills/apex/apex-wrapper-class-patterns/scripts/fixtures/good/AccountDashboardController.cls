public with sharing class AccountDashboardController {

    @AuraEnabled(cacheable=true)
    public static List<AccountRow> getAccountRows(String sortBy) {
        List<Account> accounts = [
            SELECT Id, Name, Industry
            FROM Account
            WITH USER_MODE
            ORDER BY Name
            LIMIT 200
        ];

        // One aggregate for all accounts: COUNT with GROUP BY uses one query row per group.
        Map<Id, Integer> openCountByAccount = new Map<Id, Integer>();
        for (AggregateResult ar : [
            SELECT AccountId accountId, COUNT(Id) openCount
            FROM Opportunity
            WHERE IsClosed = false AND AccountId IN :accounts
            WITH USER_MODE
            GROUP BY AccountId
        ]) {
            openCountByAccount.put((Id) ar.get('accountId'), (Integer) ar.get('openCount'));
        }

        List<AccountRow> rows = new List<AccountRow>();
        for (Account acct : accounts) {
            rows.add(new AccountRow(acct, openCountByAccount.get(acct.Id)));
        }

        if (sortBy == 'openCount') {
            rows.sort(new AccountRowComparators.ByOpenCountDesc());
        } else {
            rows.sort(); // AccountRow.compareTo: by name
        }
        return rows;
    }
}
