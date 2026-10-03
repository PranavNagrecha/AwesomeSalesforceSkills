public with sharing class QueueHistory {
    public static List<PendingServiceRouting> lastMonth() {
        return [SELECT Id, QueueId FROM PendingServiceRouting WHERE CreatedDate = LAST_MONTH];
    }
    public static List<AgentWork> focus() {
        return [SELECT Id, OriginalQueueId, ActiveTime FROM AgentWork WHERE CloseDateTime = LAST_WEEK];
    }
}
