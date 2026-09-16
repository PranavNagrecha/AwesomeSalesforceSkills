public with sharing class CommentOnlyPatterns {
    public static void documentAntiPatterns() {
        // don't flag: [SELECT Id FROM Account LIMIT 1]
        // don't flag: insert new Account(Name = 'x');
        // don't flag: Test.isRunningTest() — use injection instead
        // don't flag: Type.forName('Foo') hardcodes a strategy
        /* don't flag: for (Account a : accts) { } */
        // don't flag: new Http().send(req);
        String buried =
            'Test.isRunningTest() insert accounts [SELECT Id FROM Account] '
            + 'Type.forName and for (Account a : accts) Http send';
        System.debug(buried);
    }
}
