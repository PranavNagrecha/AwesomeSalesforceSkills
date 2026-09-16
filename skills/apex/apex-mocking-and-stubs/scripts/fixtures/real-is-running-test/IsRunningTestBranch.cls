public with sharing class IsRunningTestBranch {
    public static String collaboratorValue() {
        if (Test.isRunningTest()) {
            return 'stubbed';
        }
        return 'live';
    }
}
