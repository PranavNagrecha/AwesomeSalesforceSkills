public with sharing class AccountRowComparators {

    // Highest open count first; null rows and null counts last.
    public class ByOpenCountDesc implements Comparator<AccountRow> {
        public Integer compare(AccountRow a, AccountRow b) {
            if (a == null && b == null) {
                return 0;
            }
            if (a == null) {
                return 1;
            }
            if (b == null) {
                return -1;
            }
            Integer x = a.openOpportunityCount == null ? -1 : a.openOpportunityCount;
            Integer y = b.openOpportunityCount == null ? -1 : b.openOpportunityCount;
            if (x == y) {
                return 0;
            }
            return x > y ? -1 : 1;
        }
    }
}
