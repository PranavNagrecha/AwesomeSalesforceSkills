public with sharing class DiscardedSend {
    public static void send(Messaging.SingleEmailMessage msg) {
        Messaging.sendEmail(new List<Messaging.Email>{ msg });
    }
}
