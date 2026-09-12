/**
 * IntegrationFailureTrigger — the admin resend path.
 *
 * after update only: an admin ticks Resend__c on a failure row and the same
 * Queueable the escalation path already uses is re-entered for that Case. This
 * trigger emits no callout, publishes no event, and introduces no class the
 * escalation path does not already need — it is one more call site, which is why
 * it lives in step M1-S03 rather than a step of its own.
 */
trigger IntegrationFailureTrigger on Integration_Failure__c (after update) {
    IntegrationFailureTriggerHandler.afterUpdate(Trigger.new, Trigger.oldMap);
}
