public with sharing class RealSecurityEnforced {
    public static List<CaseMilestone> openMilestones(Id caseId) {
        return [
            SELECT Id, CompletionDate
            FROM CaseMilestone
            WHERE CaseId = :caseId
            WITH SECURITY_ENFORCED
        ];
    }
}
