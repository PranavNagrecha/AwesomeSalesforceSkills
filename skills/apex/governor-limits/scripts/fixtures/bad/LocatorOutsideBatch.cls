public with sharing class LocatorOutsideBatch {
    public static Integer countAll() {
        Database.QueryLocator ql = Database.getQueryLocator([SELECT Id FROM Account]);
        Integer n = 0;
        Database.QueryLocatorIterator it = ql.iterator();
        while (it.hasNext()) { it.next(); n++; }
        return n;
    }
}
