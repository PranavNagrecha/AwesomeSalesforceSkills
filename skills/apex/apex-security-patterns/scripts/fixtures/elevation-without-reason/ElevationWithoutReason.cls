public with sharing class ElevationWithoutReason {
    public static void stamp(List<Account> rows) {
        Database.update(rows, false, AccessLevel.SYSTEM_MODE);
    }
}
