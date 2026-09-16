trigger CommentOnlyTrigger on Case (before insert) {
    // SOQL: [SELECT Id FROM Account]
    // DML: update cases;
    // loop: for (Case c : Trigger.new) { }
    // bypass note: TriggerControl.skip('Case');
    // string form: 'TriggerControl' 'insert accounts' 'for (Case c : Trigger.new)'
    List<Trigger_Setting__mdt> settings = [
        SELECT Is_Active__c
        FROM Trigger_Setting__mdt
        WHERE Object_API_Name__c = 'Case'
        LIMIT 1
    ];
    if (!settings.isEmpty() && !settings[0].Is_Active__c) {
        return;
    }
}
