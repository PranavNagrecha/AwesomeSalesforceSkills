public with sharing class CommentOnlyOutboundEmail {
    public static void documentAntiPatterns() {
        // Messaging.sendEmail(messages) return value must be checked
        // msg.setHtmlBody('{!Contact.Name}') sends merge syntax literally
        // for (Case c : Trigger.new) { Messaging.sendEmail(...); }
        // msg.setTemplateId(tplId);
        // msg.setTargetObjectId(account.Id);
        System.debug('outbound-email patterns live in comments only');
    }
}
