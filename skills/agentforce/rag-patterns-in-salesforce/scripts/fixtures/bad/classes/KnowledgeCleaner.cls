public with sharing class KnowledgeCleaner {
    public static String clean(Knowledge__kav article) {
        return article.Body__c.stripHtmlTags();
    }
}
