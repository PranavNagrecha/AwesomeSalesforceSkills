public with sharing class CommentOnlyNamedCredentials {
    public static void documentAntiPatterns() {
        // req.setEndpoint('https://evil.example');
        // req.setHeader('Authorization', 'Bearer x');
        // String url = 'callout:Missing_NC/resource';
        System.debug('named-credential patterns live in comments only');
    }
}
