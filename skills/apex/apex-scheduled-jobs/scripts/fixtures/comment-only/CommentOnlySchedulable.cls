public with sharing class CommentOnlySchedulable {
    public static void documentAntiPatterns() {
        // don't flag: implements Schedulable
        // don't flag: System.schedule('job', cron, sched);
        // don't flag: new HttpRequest();
        // cron shape stays in a comment so R3 never sees a live literal:
        // '0 0 12 * * ?'
        String buried =
            'implements Schedulable System.schedule new HttpRequest';
        System.debug(buried);
    }
}
