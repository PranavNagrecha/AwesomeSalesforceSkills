public with sharing class AttachOutsideQueueable {
    public static void run() {
        System.attachFinalizer(new OutsideFinalizer());
    }

    private class OutsideFinalizer implements Finalizer {
        public void execute(FinalizerContext ctx) {
        }
    }
}
