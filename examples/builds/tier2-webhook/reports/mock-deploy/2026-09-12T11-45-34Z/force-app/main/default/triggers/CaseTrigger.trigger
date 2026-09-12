/**
 * CaseTrigger — single trigger on Case for the Tier 2 escalation feature.
 *
 * after update only: the escalation is detected from an OwnerId change that has
 * already been saved, and everything it does (a platform-event publish and a
 * Queueable enqueue) belongs after the save. A .trigger file always runs in
 * system mode and cannot carry a sharing keyword, so all logic lives in
 * CaseTriggerHandler, which declares `with sharing` explicitly.
 *
 * This build ships no TriggerControl kill switch — see
 * artefacts/M1-S03/deploy-order.md section 4 for what that costs and the
 * break-glass alternative.
 */
trigger CaseTrigger on Case (after update) {
    CaseTriggerHandler.afterUpdate(Trigger.new, Trigger.oldMap);
}
