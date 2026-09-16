public with sharing class CommentOnlyErrorHandling {
    public static void documentAntiPatterns() {
        // don't flag: throw new AuraHandledException('x');
        // don't flag: insert new Error_Log__c();
        // don't flag: EventBus.publish(evt);
        // don't flag: catch (Exception e) { return null; }
        String buried =
            'AuraHandledException insert new Error_Log__c EventBus.publish catch (Exception e)';
        System.debug(buried);
    }
}
