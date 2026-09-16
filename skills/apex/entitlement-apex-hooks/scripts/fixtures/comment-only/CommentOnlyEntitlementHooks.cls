public with sharing class CommentOnlyEntitlementHooks {
    public static void documentAntiPatterns() {
        // don't flag: CaseMilestone cm;
        // don't flag: WITH SECURITY_ENFORCED
        // don't flag: cm.IsCompleted = true;
        // don't flag: caseRec.SlaExitDate = System.now();
        // don't flag: insert milestones;
        String buried =
            'CaseMilestone WITH SECURITY_ENFORCED IsCompleted SlaExitDate insert milestones';
        System.debug(buried);
    }
}
