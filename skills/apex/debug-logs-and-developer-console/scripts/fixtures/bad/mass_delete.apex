List<Account> doomed = [SELECT Id FROM Account WHERE Legacy_Code__c != null];
delete doomed;
System.debug('deleted ' + doomed.size());
