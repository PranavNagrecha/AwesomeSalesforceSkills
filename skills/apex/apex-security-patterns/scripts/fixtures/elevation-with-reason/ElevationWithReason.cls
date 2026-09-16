public with sharing class ElevationWithReason {
    public static void stamp(List<Account> rows) {
        // reason: platform-owned milestone stamp
        Database.update(rows, false, AccessLevel.SYSTEM_MODE);
    }
}
