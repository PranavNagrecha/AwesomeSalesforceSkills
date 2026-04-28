/**
 * CaseEscalationService — synthetic sample for deployment-risk-scorer eval.
 * Intentionally simple. Do not deploy.
 *
 * Represents a "new Apex class added in this change set" with no
 * corresponding test class, which the scorer should flag as
 * test-coverage-unknown HIGH risk.
 */
public with sharing class CaseEscalationService {
    public static void escalate(Set<Id> caseIds) {
        if (caseIds == null || caseIds.isEmpty()) {
            return;
        }
        List<Case> toUpdate = [
            SELECT Id, Status FROM Case WHERE Id IN :caseIds WITH SECURITY_ENFORCED
        ];
        for (Case c : toUpdate) {
            c.Status = 'Escalated';
        }
        update toUpdate;
    }
}
