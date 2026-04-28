/**
 * AccountAfterInsert — synthetic sample for trigger-consolidator eval.
 * Inline-logic trigger that DML-inserts a child Task. Must be folded
 * into AccountTriggerHandler.afterInsert preserving the logic verbatim.
 */
trigger AccountAfterInsert on Account (after insert) {
    List<Task> welcomeTasks = new List<Task>();
    for (Account a : Trigger.new) {
        welcomeTasks.add(new Task(
            Subject = 'Welcome ' + a.Name,
            WhatId = a.Id
        ));
    }
    insert welcomeTasks;
}
