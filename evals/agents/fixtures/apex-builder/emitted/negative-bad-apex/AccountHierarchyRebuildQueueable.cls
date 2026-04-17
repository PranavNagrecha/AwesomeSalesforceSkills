// Bad fixture — unbalanced braces; Gate C must catch this.
public with sharing class AccountHierarchyRebuildQueueable implements Queueable {
    public void execute(QueueableContext c) {
        System.debug('started';
    // missing closing brace on method AND class
