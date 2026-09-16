public with sharing class CommentOnlyPlatformEvents {
    public static void documentAntiPatterns() {
        // don't flag: EventBus.publish(evt);
        // don't flag: throw new EventBus.RetryableException('retry');
        // don't flag: EventBus.TriggerContext.currentContext().setResumeCheckpoint(key);
        // don't flag: trigger Foo on Foo__e (after insert)
        String buried =
            'EventBus.publish RetryableException setResumeCheckpoint trigger on Foo__e';
        System.debug(buried);
    }
}
