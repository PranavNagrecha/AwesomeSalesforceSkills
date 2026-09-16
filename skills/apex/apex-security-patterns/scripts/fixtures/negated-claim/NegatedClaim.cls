public with sharing class NegatedClaim {
    public static void touch(Account a) {
        // at 66.0 this ran in system mode; at 67.0 it does not
        update a;
    }
}
