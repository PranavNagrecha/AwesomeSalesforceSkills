public with sharing class CommentOnlyIds {
    public static void documentAntiPatterns() {
        // P0 example: '001000000000001' must never appear as a literal Id
        // P1 example: [SELECT Id FROM Profile WHERE Name = 'Admin']
        // P2 example: String accountId holds a 15/18-char comparison risk
        System.debug('hardcoded-id patterns live in comments only');
    }
}
