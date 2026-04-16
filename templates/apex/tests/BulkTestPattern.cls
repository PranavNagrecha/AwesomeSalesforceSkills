/**
 * BulkTestPattern — reference test class demonstrating the canonical
 * bulk-test pattern for Apex triggers / services.
 *
 * Every production Apex test MUST:
 *  1. Insert / update at least 200 records of the triggering object.
 *  2. Wrap the DML in `Test.startTest()/Test.stopTest()` so async work runs.
 *  3. Assert on both governor-limit headroom AND the business outcome.
 *  4. Use `TestDataFactory` or `TestRecordBuilder` — never inline `new SObject()`.
 *  5. For sharing / FLS, also run the same test inside `System.runAs()`
 *     with `TestUserFactory`-minted users.
 */
@IsTest
private class BulkTestPattern {

    @TestSetup
    static void setup() {
        insert TestDataFactory.createAccounts(200, null);
    }

    @IsTest
    static void handlesBulkInsert() {
        List<Account> accounts = [SELECT Id, Name FROM Account LIMIT 200];
        System.assertEquals(200, accounts.size(), 'Setup should create 200 accounts');

        List<Contact> contacts = new List<Contact>();
        for (Account a : accounts) {
            contacts.addAll(TestDataFactory.createContacts(1, a.Id, null));
        }

        Test.startTest();
        insert contacts;
        Test.stopTest();

        System.assertEquals(200, contacts.size(), 'Expected one contact per account');
        System.assert(
            Limits.getQueries() <= Limits.getLimitQueries() / 2,
            'Trigger must leave headroom for callers: queries=' + Limits.getQueries()
        );
        System.assert(
            Limits.getDmlStatements() <= Limits.getLimitDmlStatements() / 2,
            'Trigger must leave DML headroom: dml=' + Limits.getDmlStatements()
        );

        Integer linked = [
            SELECT COUNT() FROM Contact
            WHERE AccountId IN :new Map<Id, Account>(accounts).keySet()
        ];
        System.assertEquals(200, linked, 'All contacts must link to accounts');
    }

    @IsTest
    static void handlesBulkUpdate() {
        List<Account> accounts = [SELECT Id FROM Account LIMIT 200];
        for (Account a : accounts) { a.Name = 'Renamed'; }

        Test.startTest();
        update accounts;
        Test.stopTest();

        Integer renamed = [SELECT COUNT() FROM Account WHERE Name = 'Renamed'];
        System.assertEquals(200, renamed);
    }
}
