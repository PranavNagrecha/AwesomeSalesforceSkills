trigger AccountContactSync on Account (after update) {
    List<Contact> related = [SELECT Id, AccountId FROM Contact WHERE AccountId IN :Trigger.newMap.keySet()];
    update related;
}
