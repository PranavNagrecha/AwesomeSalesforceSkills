/**
 * CaseMilestoneService — completes CaseMilestone rows in response to a Case change.
 *
 * The only supported write. CaseMilestone's documented supported calls are
 * describeLayout(), describeSObjects(), query(), retrieve(), update() — the platform
 * creates and deletes the rows, Apex can only update them. Of the object's fields, only
 * CompletionDate and StartDate carry the `Update` property; IsCompleted, IsViolated and
 * TargetDate do not. So "complete this milestone" means exactly one thing: write
 * CompletionDate.
 *
 * Bulk shape: one SOQL, one DML, regardless of how many Cases are in Trigger.new.
 *
 * Build note (case-onboarding M4-S05): this class is called directly from
 * CaseMilestoneTrigger rather than through a TriggerHandler subclass. See
 * artefacts/M4-S05/deploy-order.md § 2 for why, and for what a handler would cost.
 *
 * Shipped-code repair (F-62, artefacts/M4-S05/deploy-order.md section 11): the CaseMilestone
 * query and its DML now run in explicit system mode. Completing a milestone is a
 * system-integrity write performed on behalf of the platform, not an action the running
 * user takes deliberately, and no permission set in this build grants any access to
 * CaseMilestone at all. WITH USER_MODE at apiVersion 67.0 made both operations silently
 * see or write nothing for a persona holding no CaseMilestone access. This is the first
 * change to shipped code across the repair history of this step -- every prior repair
 * (sections 8, 9, 10) touched only CaseMilestoneServiceTest.cls.
 */
public with sharing class CaseMilestoneService {

    private static final String LOG_SOURCE = 'CaseMilestoneService.completeMilestones';

    /** Governor-safe ceiling on a single trigger pass. 10,000 is the DML row limit. */
    private static final Integer MAX_MILESTONES = 10000;

    /**
     * Exact MilestoneType.Name from Setup > Entitlement Management > Milestones. Held in
     * one named constant rather than as a literal per call site, so a Setup rename is a
     * one-line change and not a hunt. @TestVisible so the test drives the same constant
     * the trigger uses instead of a copy of it. If this org ever needs a second milestone
     * type completed, promote this to Custom Metadata rather than adding a second literal.
     *
     * The value matches artefacts/M4-S02/milestoneTypes/First Response.milestoneType-meta.xml.
     */
    @TestVisible
    private static final String MILESTONE_TYPE_NAME = 'First Response';

    /**
     * The Case Status a case leaves when the first response has been made. Leaving it is
     * the completion signal: this build's two business processes
     * (artefacts/M1-S01/objects/Case/businessProcesses/) expose New -> Escalated -> Closed
     * on support cases and New -> Closed on billing cases, so "no longer New" is the one
     * transition both ladders share. See deploy-order.md § 3 — this is a proxy for
     * "an agent replied", and Q50's answer named the first outbound EmailMessage instead.
     */
    @TestVisible
    private static final String OPENING_STATUS = 'New';

    /** What one pass did. Returned so the caller and the test can assert on it. */
    public class CompletionResult {
        public Integer attempted = 0;
        public Integer completed = 0;
        public List<String> failures = new List<String>();
    }

    /**
     * Trigger entry point. Completes the First Response milestone on every Case in the
     * batch that just left the opening Status.
     *
     * @param newCases Trigger.new
     * @param oldMap   Trigger.oldMap
     */
    public static CompletionResult completeFirstResponseMilestone(
            List<Case> newCases,
            Map<Id, Case> oldMap) {

        return completeMilestones(newCases, oldMap, MILESTONE_TYPE_NAME);
    }

    /**
     * Completes every open milestone of the named type on Cases whose Status just left
     * OPENING_STATUS.
     *
     * @param newCases          Trigger.new
     * @param oldCases          Trigger.oldMap
     * @param milestoneTypeName exact MilestoneType.Name from Setup
     */
    public static CompletionResult completeMilestones(
            List<Case> newCases,
            Map<Id, Case> oldCases,
            String milestoneTypeName) {

        CompletionResult result = new CompletionResult();
        if (newCases == null || oldCases == null || String.isBlank(milestoneTypeName)) {
            return result;
        }

        // Pass 1 — collect Ids only. No SOQL and no DML inside this loop.
        Set<Id> caseIds = new Set<Id>();
        for (Case changed : newCases) {
            Case previous = oldCases.get(changed.Id);
            if (previous == null) {
                continue;
            }
            if (previous.Status != OPENING_STATUS) {
                continue;
            }
            if (changed.Status == OPENING_STATUS) {
                continue;
            }
            caseIds.add(changed.Id);
        }
        if (caseIds.isEmpty()) {
            return result;
        }

        // The one query. The three-clause WHERE is the whole point: the case Ids, the
        // milestone type name, and CompletionDate = NULL. That last clause does two jobs —
        // it selects only open milestones, and it is the idempotency guard that makes the
        // second pass a no-op when a workflow field update re-fires the trigger on the
        // same save.
        //
        // reason: F-62 (reports/MOCK-DEPLOY-M5.md run 7) -- completing a milestone is a
        // system-integrity write performed by a trigger on behalf of the platform, not an
        // action the running user takes deliberately; no permission set in this build
        // grants any access to CaseMilestone at all (artefacts/M2-S02/), by design. At
        // apiVersion 67.0 the default is user mode, so this query previously returned zero
        // rows for a persona holding no CaseMilestone access, hiding an open milestone the
        // platform still needed completed. WITH SYSTEM_MODE opts this query into
        // platform-level visibility instead of running-user visibility, per the
        // integration/platform-utility guidance in skills/apex/apex-security-patterns and
        // the graceful-degradation boundary in
        // skills/apex/apex-stripinaccessible-and-fls-enforcement. Granting the persona Edit
        // on CaseMilestone instead was considered and rejected -- see deploy-order.md
        // section 11 for why narrowing to system mode, not widening the permission set, is
        // the correct boundary here. WITH SECURITY_ENFORCED is not used: it was removed at
        // 67.0 and does not compile.
        List<CaseMilestone> openMilestones = [
            SELECT Id, CaseId, CompletionDate
            FROM CaseMilestone
            WHERE CaseId IN :caseIds
              AND MilestoneType.Name = :milestoneTypeName
              AND CompletionDate = NULL
            WITH SYSTEM_MODE
            LIMIT 10000
        ];
        if (openMilestones.isEmpty()) {
            return result;
        }
        if (openMilestones.size() >= MAX_MILESTONES) {
            System.debug(
                LoggingLevel.WARN,
                LOG_SOURCE + ': milestone batch hit the ' + MAX_MILESTONES +
                ' ceiling for ' + caseIds.size() + ' cases; some milestones were not ' +
                'completed on this pass.'
            );
        }

        DateTime completedAt = System.now();
        for (CaseMilestone milestone : openMilestones) {
            milestone.CompletionDate = completedAt;
        }
        result.attempted = openMilestones.size();

        // The one DML. allOrNone = false so a single locked or inaccessible milestone does
        // not roll back the Case save that triggered this. Database class methods with
        // partial success return a results array instead of throwing, and the code must
        // iterate it to find out what failed — dropping this loop is how partial-success
        // DML becomes worse than all-or-nothing DML.
        //
        // reason: AccessLevel.SYSTEM_MODE matches the query above (F-62) -- the milestone
        // stamp is the platform completion signal, not a field the running user is expected
        // to edit directly, and no permission set in this build grants CaseMilestone access.
        // Narrowing to this one object and this one write, rather than granting the persona
        // Edit on CaseMilestone, keeps the same discipline skills/apex/test-class-standards
        // Gotcha 15 applies elsewhere in this build: a persona is not widened for access its
        // job does not call for.
        List<Database.SaveResult> saveResults = Database.update(
            openMilestones, false, AccessLevel.SYSTEM_MODE
        );
        for (Integer i = 0; i < saveResults.size(); i++) {
            Database.SaveResult saveResult = saveResults[i];
            if (saveResult.isSuccess()) {
                result.completed++;
                continue;
            }
            for (Database.Error err : saveResult.getErrors()) {
                String detail = 'CaseMilestone ' + openMilestones[i].Id + ' (' +
                    err.getStatusCode() + '): ' + err.getMessage();
                result.failures.add(detail);
                System.debug(LoggingLevel.ERROR, LOG_SOURCE + ': ' + detail);
            }
        }
        return result;
    }
}
