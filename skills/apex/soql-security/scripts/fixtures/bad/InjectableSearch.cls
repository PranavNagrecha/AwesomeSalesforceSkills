public without sharing class InjectableSearch {
    @AuraEnabled
    public static List<Account> search(String term, String sortField) {
        String q = 'SELECT Id, Name FROM Account WHERE Name LIKE \'%' + term + '%\' ORDER BY ' + sortField;
        return Database.query(q);
    }

    public static Integer countAll(String filter) {
        return Database.countQuery('SELECT COUNT() FROM Account WHERE ' + filter);
    }
}
