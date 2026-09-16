public with sharing class DiscardedPublish {
    public static void run() {
        EventBus.publish(new Foo__e());
    }
}
