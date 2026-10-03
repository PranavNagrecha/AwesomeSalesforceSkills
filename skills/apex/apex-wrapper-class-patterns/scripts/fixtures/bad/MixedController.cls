public with sharing class MixedController {
    @AuraEnabled public String label;
    @AuraEnabled
    public static MixedController load() {
        return new MixedController();
    }
}
