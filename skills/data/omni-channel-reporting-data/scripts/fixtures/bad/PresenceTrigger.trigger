trigger PresenceTrigger on UserServicePresence (after insert) {
    System.debug('never fires');
}
