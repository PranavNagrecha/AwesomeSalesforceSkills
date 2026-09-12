/**
 * CaseMilestoneTrigger — completes CaseMilestone rows when a Case Status changes.
 *
 * Named for what it does to milestones, but it is a Case trigger: CaseMilestone rows are
 * created by the platform, not by DML, so there is no CaseMilestone DML event to hang
 * completion off. The Case save is the observable event.
 *
 * `after update` is not a style choice. Entitlement rules — the engine that creates the
 * milestone rows — run at step 15 of the order of execution, after all before triggers
 * (step 4) and all after triggers (step 8), so neither trigger context can see milestones
 * created by the save it is running inside. Completion therefore hangs off a later save
 * than the one that applies the entitlement.
 */
trigger CaseMilestoneTrigger on Case (after update) {
    CaseMilestoneService.completeFirstResponseMilestone(Trigger.new, Trigger.oldMap);
}
