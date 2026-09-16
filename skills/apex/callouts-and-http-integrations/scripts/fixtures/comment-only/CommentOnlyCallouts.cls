public with sharing class CommentOnlyCallouts {
    public static void documentAntiPatterns() {
        // don't flag: new Http();
        // don't flag: http.send(req);
        // don't flag: req.setEndpoint('https://x.com');
        // don't flag: insert a;
        // don't flag: Test.setMock(HttpCalloutMock.class, mock);
        String buried =
            'new Http http.send insert accounts Test.setMock';
        System.debug(buried);
    }
}
