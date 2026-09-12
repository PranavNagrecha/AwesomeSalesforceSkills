/**
 * CaseMilestoneServiceTest — proves the four behaviours that matter:
 *   1. a real Case save runs CaseMilestoneTrigger and CompletionDate is written
 *   2. an already-completed milestone is skipped on a second pass
 *   3. 200 Cases still cost one query and one DML
 *   4. a Case whose Status did not change never reaches the query
 *
 * SeeAllData=true is not laziness. SlaProcess has no create() call, so no test can build
 * an entitlement process; and CaseMilestone has no create() call, so no test can fake the
 * rows. Both have to come from the org. Two constraints come with that choice: this class
 * cannot also be @IsTest(IsParallel=true) — the two annotations cannot be used together —
 * and it reads the org's actual data, so an admin deactivating the entitlement process
 * breaks it. That cost is accepted deliberately: a test that returns early on a missing
 * process is indistinguishable from a passing one, and a green test certifying milestone
 * automation that has never executed is the worst outcome in this domain.
 *
 * Build note (case-onboarding M4-S05): the org prerequisites this class needs, and what it
 * proves and does not prove in a design-only build, are in artefacts/M4-S05/deploy-order.md § 4.
 */
@IsTest(SeeAllData=true)
private class CaseMilestoneServiceTest {

    private static final String MILESTONE_TYPE = 'First Response';

    /** Matches CaseMilestoneService.OPENING_STATUS and M1-S01's two business processes. */
    private static final String OPENING_STATUS = 'New';

    /**
     * The Status the test moves a Case into. 'Closed' is the one value that both
     * artefacts/M1-S01/objects/Case/businessProcesses/Support_Process and Billing_Process
     * expose, so this test does not depend on which record type the running user defaults
     * to. The service completes on any transition out of OPENING_STATUS, not on this value
     * specifically.
     */
    private static final String RESPONDED_STATUS = 'Closed';

    /**
     * Field values every Case in this build needs in order to survive the two active
     * validation rules M3-S01 writes: Origin_Must_Be_Known (Origin must be Email-Support,
     * Email-Billing or Web) and Priority_Required_On_Agent_Save (Priority not blank).
     * TestDataFactory.createCases defaults Origin to 'Email', which is not one of the
     * three values this build's CaseOrigin standard value set defines.
     */
    private static Map<String, Object> caseOverrides(Id entitlementId) {
        Map<String, Object> overrides = new Map<String, Object>{
            'Origin'   => 'Web',
            'Priority' => 'Medium'
        };
        if (entitlementId != null) {
            overrides.put('EntitlementId', entitlementId);
        }
        return overrides;
    }

    /**
     * Returns an active entitlement process, or fails the run with a message that names
     * the missing prerequisite. Deliberately an assertion rather than `return null` — a
     * skipped test in this domain is indistinguishable from a passing one.
     */
    private static SlaProcess requireActiveProcess() {
        List<SlaProcess> processes = [
            SELECT Id, Name
            FROM SlaProcess
            WHERE IsActive = true
            LIMIT 1
        ];
        if (processes.isEmpty()) {
            Assert.isTrue(
                false,
                'No active SlaProcess in this org. CaseMilestoneServiceTest cannot ' +
                'create one (SlaProcess has no create() call), so an entitlement ' +
                'process with a "' + MILESTONE_TYPE + '" milestone must exist in the ' +
                'target org before this test can prove anything.'
            );
        }
        return processes[0];
    }

    /** Account + Entitlement, so Cases created against it enter the entitlement process. */
    private static Entitlement entitlementFor(SlaProcess process, String label) {
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        insert accounts;

        Entitlement entitlement = new Entitlement(
            Name         = label,
            AccountId    = accounts[0].Id,
            SlaProcessId = process.Id,
            StartDate    = Date.today().addDays(-1),
            EndDate      = Date.today().addYears(1)
        );
        insert entitlement;
        return entitlement;
    }

    /** One Case already inside the entitlement process, at OPENING_STATUS. */
    private static Case caseInsideProcess(SlaProcess process) {
        Entitlement entitlement = entitlementFor(process, 'Milestone Test Entitlement');
        List<Case> cases = TestDataFactory.createCases(
            1,
            entitlement.AccountId,
            caseOverrides(entitlement.Id)
        );
        insert cases;
        return cases[0];
    }

    @IsTest
    static void triggerWritesCompletionDateOnAnOpenMilestone() {
        SlaProcess process = requireActiveProcess();
        Case subject = caseInsideProcess(process);

        List<CaseMilestone> before = [
            SELECT Id, CompletionDate
            FROM CaseMilestone
            WHERE CaseId = :subject.Id
              AND MilestoneType.Name = :MILESTONE_TYPE
              AND CompletionDate = NULL
        ];
        Assert.isFalse(
            before.isEmpty(),
            'No open "' + MILESTONE_TYPE + '" milestone was generated for the test ' +
            'Case. The entitlement process exists but does not include this milestone, ' +
            'or the Case did not enter the process. Nothing below would prove anything.'
        );

        // A real save, not a direct service call: this is the only method that runs
        // CaseMilestoneTrigger itself. The Case was inserted on an earlier save, so the
        // milestone rows the entitlement engine created at step 15 of that save exist by
        // the time this one runs.
        Case responded = new Case(Id = subject.Id, Status = RESPONDED_STATUS);

        Test.startTest();
        update responded;
        Test.stopTest();

        CaseMilestone reloaded = [
            SELECT Id, CompletionDate, IsCompleted
            FROM CaseMilestone
            WHERE Id = :before[0].Id
        ];
        Assert.isTrue(
            reloaded.CompletionDate != null,
            'CompletionDate is the only writable completion control on CaseMilestone; ' +
            'if it is still null the trigger did not run or the update did not take.'
        );
    }

    @IsTest
    static void skipsAMilestoneThatIsAlreadyCompleted() {
        SlaProcess process = requireActiveProcess();
        Case subject = caseInsideProcess(process);

        Case previous = new Case(Id = subject.Id, Status = OPENING_STATUS);
        Case responded = new Case(Id = subject.Id, Status = RESPONDED_STATUS);
        List<Case> newCases = new List<Case>{ responded };
        Map<Id, Case> oldCases = new Map<Id, Case>{ previous.Id => previous };

        // First pass completes whatever is open.
        CaseMilestoneService.CompletionResult first = CaseMilestoneService.completeMilestones(
            newCases, oldCases, MILESTONE_TYPE
        );
        Assert.isTrue(first.attempted > 0, 'Set-up pass must complete at least one milestone.');

        // Second pass with exactly the same arguments — which is what a workflow field
        // update produces: it re-fires before-update and after-update triggers one more
        // time on the same save, so the body genuinely runs twice. The CompletionDate =
        // NULL filter must exclude everything the first pass stamped.
        Test.startTest();
        CaseMilestoneService.CompletionResult second = CaseMilestoneService.completeMilestones(
            newCases, oldCases, MILESTONE_TYPE
        );
        Test.stopTest();

        Assert.areEqual(
            0,
            second.attempted,
            'A completed milestone must not be re-stamped. attempted > 0 means the ' +
            'CompletionDate = NULL filter is missing from the query.'
        );
        Assert.areEqual(0, second.failures.size(), String.join(second.failures, ' | '));
    }

    @IsTest
    static void staysAtOneQueryAndOneDmlFor200Cases() {
        SlaProcess process = requireActiveProcess();
        Entitlement entitlement = entitlementFor(process, 'Bulk Milestone Test Entitlement');

        List<Case> cases = TestDataFactory.createCases(
            200,
            entitlement.AccountId,
            caseOverrides(entitlement.Id)
        );
        insert cases;

        Map<Id, Case> oldCases = new Map<Id, Case>();
        List<Case> newCases = new List<Case>();
        for (Case original : cases) {
            oldCases.put(original.Id, new Case(Id = original.Id, Status = OPENING_STATUS));
            newCases.add(new Case(Id = original.Id, Status = RESPONDED_STATUS));
        }

        Test.startTest();
        Integer queriesBefore = Limits.getQueries();
        Integer dmlBefore = Limits.getDmlStatements();

        CaseMilestoneService.CompletionResult result = CaseMilestoneService.completeMilestones(
            newCases, oldCases, MILESTONE_TYPE
        );

        Integer queriesUsed = Limits.getQueries() - queriesBefore;
        Integer dmlUsed = Limits.getDmlStatements() - dmlBefore;
        Test.stopTest();

        Assert.areEqual(1, queriesUsed, '200 Cases must cost exactly one SOQL query.');
        Assert.isTrue(dmlUsed <= 1, '200 Cases must cost at most one DML statement.');
        Assert.areEqual(
            result.attempted,
            result.completed + result.failures.size(),
            'Every attempted milestone must be accounted for as a success or a failure.'
        );
    }

    @IsTest
    static void ignoresCasesWhoseStatusDidNotChange() {
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        insert accounts;
        List<Case> cases = TestDataFactory.createCases(1, accounts[0].Id, caseOverrides(null));
        insert cases;

        // No Status change, so the service must return before it queries anything.
        Test.startTest();
        Integer queriesBefore = Limits.getQueries();
        CaseMilestoneService.CompletionResult result = CaseMilestoneService.completeMilestones(
            cases,
            new Map<Id, Case>(cases),
            MILESTONE_TYPE
        );
        Integer queriesUsed = Limits.getQueries() - queriesBefore;
        Test.stopTest();

        Assert.areEqual(0, result.attempted, 'An unchanged Status must attempt nothing.');
        Assert.areEqual(0, queriesUsed, 'An unchanged Status must not reach the query.');
    }
}
