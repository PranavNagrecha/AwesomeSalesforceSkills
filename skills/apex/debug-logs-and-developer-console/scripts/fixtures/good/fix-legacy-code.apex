// Anonymous Apex runs as the current user, with sharing, and fails to compile
// if the user lacks access to the object or field.
Boolean dryRun = true;
List<Account> records = [
    SELECT Id, Name, Legacy_Code__c
    FROM Account
    WHERE Legacy_Code__c != null
    LIMIT 200
];
System.debug(LoggingLevel.INFO, 'Matched ' + records.size() + ' accounts');
for (Account a : records) {
    a.Legacy_Code__c = null;
}
if (!dryRun) {
    List<Database.SaveResult> results = Database.update(records, false);
    Integer failed = 0;
    for (Database.SaveResult r : results) {
        if (!r.isSuccess()) {
            failed++;
        }
    }
    System.debug(LoggingLevel.INFO, 'Updated ' + (records.size() - failed) + ', failed ' + failed);
}
