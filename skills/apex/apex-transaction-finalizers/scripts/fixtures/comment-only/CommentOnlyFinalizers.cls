public with sharing class CommentOnlyFinalizers {
    public static void documentAntiPatterns() {
        // don't flag: implements Finalizer
        // don't flag: System.attachFinalizer(fin)
        // don't flag: ctx.getJobId()
        // don't flag: transient Integer attempts;
        String buried =
            'implements Finalizer System.attachFinalizer getJobId transient';
        System.debug(buried);
    }
}
