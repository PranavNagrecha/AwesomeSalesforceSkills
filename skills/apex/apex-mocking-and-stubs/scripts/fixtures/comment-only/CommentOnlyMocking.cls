public with sharing class CommentOnlyMocking {
    public static void documentAntiPatterns() {
        // don't flag: Test.isRunningTest()
        // don't flag: Test.createStub(Foo.class, provider)
        // don't flag: Test.setMock(HttpCalloutMock.class, mock)
        // don't flag: implements StubProvider
        String buried =
            'Test.isRunningTest Test.createStub Test.setMock implements StubProvider';
        System.debug(buried);
    }
}
