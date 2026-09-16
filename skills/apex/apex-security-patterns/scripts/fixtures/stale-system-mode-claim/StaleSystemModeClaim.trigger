trigger StaleSystemModeClaim on Account (before insert) {
    // triggers run in system mode, so FLS is not checked here
    for (Account a : Trigger.new) {
        a.Description = 'x';
    }
}
