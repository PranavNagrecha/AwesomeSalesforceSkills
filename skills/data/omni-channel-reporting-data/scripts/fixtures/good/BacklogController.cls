public with sharing class BacklogController {
    // Historical wait comes from AgentWork, never WaitTime: see SpeedToAnswer.
    public static List<AggregateResult> waitingNow() {
        return [SELECT GroupId, COUNT(Id) n FROM PendingServiceRouting WHERE IsReadyForRouting = true GROUP BY GroupId];
    }
}
