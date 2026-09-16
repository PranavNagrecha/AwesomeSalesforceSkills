public with sharing class CommentOnlyQueueable {
    public static void documentAntiPatterns() {
        // don't flag: System.enqueueJob(new Job());
        // don't flag: implements Queueable
        // don't flag: @future
        // don't flag: HttpRequest
        String buried =
            'System.enqueueJob implements Queueable @future HttpRequest';
        System.debug(buried);
    }
}
