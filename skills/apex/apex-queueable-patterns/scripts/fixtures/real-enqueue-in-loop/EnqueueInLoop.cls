public with sharing class EnqueueInLoop {
    public static void run(List<Id> ids) {
        for (Id jobId : ids) {
            System.enqueueJob(new LoopWorker());
        }
    }

    private class LoopWorker implements Queueable {
        public void execute(QueueableContext ctx) {
        }
    }
}
