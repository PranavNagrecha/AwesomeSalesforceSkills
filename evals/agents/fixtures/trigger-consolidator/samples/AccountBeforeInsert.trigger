/**
 * AccountBeforeInsert — synthetic sample for trigger-consolidator eval.
 * Inline-logic trigger (not on the framework). Should be folded into
 * AccountTriggerHandler.beforeInsert by the consolidator.
 */
trigger AccountBeforeInsert on Account (before insert) {
    for (Account a : Trigger.new) {
        if (String.isBlank(a.Name)) {
            a.addError('Name is required');
        }
        if (a.Industry == null) {
            a.Industry = 'Other';
        }
    }
}
