public with sharing class AccountRow implements Comparable {
    // Only public instance properties with @AuraEnabled are serialized to the component.
    // get/set lets the component send the object back as a parameter.
    @AuraEnabled public Id accountId { get; set; }
    @AuraEnabled public String accountName { get; set; }
    @AuraEnabled public String industry { get; set; }
    @AuraEnabled public Integer openOpportunityCount { get; set; }

    public AccountRow() {
    }

    public AccountRow(Account acct, Integer openCount) {
        accountId = acct.Id;
        accountName = acct.Name;
        industry = acct.Industry;
        openOpportunityCount = openCount == null ? 0 : openCount;
    }

    // Natural order: by name, nulls last. The Comparable reference requires explicit null handling.
    public Integer compareTo(Object other) {
        if (other == null) {
            return -1;
        }
        AccountRow that = (AccountRow) other;
        if (accountName == null && that.accountName == null) {
            return 0;
        }
        if (accountName == null) {
            return 1;
        }
        if (that.accountName == null) {
            return -1;
        }
        return accountName.compareTo(that.accountName);
    }
}
