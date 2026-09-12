/**
 * CaseMilestoneServiceTest — proves the four behaviours that matter:
 *   1. a real Case save runs CaseMilestoneTrigger and CompletionDate is written
 *   2. an already-completed milestone is skipped on a second pass
 *   3. 200 Cases still cost one query and one DML
 *   4. a Case whose Status did not change never reaches the query
 *
 * The class-level SeeAllData annotation below is not laziness. SlaProcess has no create() call, so no test can build
 * an entitlement process; and CaseMilestone has no create() call, so no test can fake the
 * rows. Both have to come from the org. Two constraints come with that choice: this class
 * cannot also be @IsTest(IsParallel=true) — the two annotations cannot be used together —
 * and it reads the actual data in the org, so an admin deactivating the entitlement process
 * breaks it. That cost is accepted deliberately: a test that returns early on a missing
 * process is indistinguishable from a passing one, and a green test certifying milestone
 * automation that has never executed is the worst outcome in this domain.
 *
 * Build note (case-onboarding M4-S05): the org prerequisites this class needs, and what it
 * proves and does not prove in a design-only build, are in artefacts/M4-S05/deploy-order.md § 4.
 *
 * Test-only repair (F-59, artefacts/M4-S05/deploy-order.md, section 8): every method action
 * and assertion now runs inside a runAs block for a user holding the Tier 1 agent permission
 * sets this build ships. At apiVersion 67.0 Apex runs in user mode by default (no WITH USER_MODE
 * needed at any call site in this class or in CaseMilestoneService), so the deploying user
 * this class ran as before had no bearing on whether a real Tier 1 agent can complete a
 * milestone -- only the runAs wrap does. See skills/apex/test-class-standards/references
 * directory, gotchas file Gotchas 13-14, and examples file Example 5.
 *
 * Second test-only repair (F-60, artefacts/M4-S05/deploy-order.md, section 9): wrapping the
 * fixture inserts themselves in runAs(agent) went one field too far. Case_Agent_Core grants
 * Create on Case but field permissions on only Severity__c -- not Subject, Origin, AccountId,
 * Priority or EntitlementId -- so a fixture Case built with those fields cannot be inserted
 * while running as the Tier 1 persona; that is the correct, narrow grant, not a gap to widen.
 * Every fixture insert (Account, Entitlement, the Case rows) now goes through
 * TestDataFactory.insertAsSystem(...) outside System.runAs(agent); only the action under test
 * -- the Status change that fires CaseMilestoneTrigger, and the CaseMilestoneService call that
 * stands in for it -- runs inside System.runAs(agent). See
 * skills/apex/test-class-standards/references/gotchas.md Gotcha 15.
 *
 * Third test-only repair (F-61, artefacts/M4-S05/deploy-order.md, section 10): with the
 * fixture seeding fixed, the persona could create and update the Case, and the two
 * milestone-dependent methods still failed -- requireActiveProcess() selected any active
 * SlaProcess rather than the deployed First_Response_Standard, and a pre-existing active
 * process already in the target org (no First Response milestone) won the LIMIT 1. The query
 * now names the deployed process explicitly and asserts exactly one match. Shipped code
 * (CaseMilestoneService.cls, CaseMilestoneTrigger.trigger) is unchanged.
 *
 * Fourth repair (F-62, artefacts/M4-S05/deploy-order.md, section 11) -- this one touches
 * shipped code. The persona now enters the right process, but no permission set in this
 * build grants any access to CaseMilestone, so the WITH USER_MODE query and update inside
 * CaseMilestoneService ran silently empty/refused for the agent. CaseMilestoneService.cls
 * now runs its CaseMilestone query and DML in explicit system mode; see that class doc
 * comment for the reasoning. This test class gained three new assertions -- after every
 * CaseMilestoneService.completeMilestones(...) call, the result failures list is asserted
 * empty -- so a refused write fails loudly instead of surfacing later as a wrong attempted
 * count.
 */
// SeeAllData required: SlaProcess and CaseMilestone rows cannot be created by a test,
// per the class doc above -- both must be read from the org.
@IsTest(SeeAllData=true)
private class CaseMilestoneServiceTest {

    private static final String MILESTONE_TYPE = 'First Response';

    /** Matches CaseMilestoneService.OPENING_STATUS and the two business processes from M1-S01. */
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
     * The persona under test: a working Tier 1 support agent. Both members are named
     * directly (TestUserFactory.createUser assigns PermissionSets by name, not
     * PermissionSetGroups) but together they are exactly the member list PSG_Tier1_Prod
     * declares under artefacts/M2-S02/permissionsetgroups --
     * Case_Agent_Core (base Case CRU; Account/Contact/Entitlement stay read-only) plus
     * Case_Tier1 (Support record-type visibility, Case.Severity__c edit). See
     * artefacts/M4-S05/deploy-order.md section 8 for why this pair and not Case_Tier2 or
     * Case_Billing.
     */
    private static final String AGENT_PROFILE = 'Acme Support Tier 1';
    private static final List<String> AGENT_PERMISSION_SETS = new List<String>{
        'Case_Agent_Core', 'Case_Tier1'
    };

    /**
     * Mints a user holding the Tier 1 persona permission sets, for use in a runAs block. The
     * User insert and the PermissionSetAssignment inserts that TestUserFactory.createUser
     * performs are both setup-object DML; fencing the call inside a runAs block that
     * re-enters the current user (Id set from UserInfo.getUserId) keeps that DML out of the
     * same transaction as the Account / Entitlement / Case DML the rest of this class
     * performs, which is exactly what a mixed-DML error is
     * (skills/apex/mixed-dml-and-setup-objects). This re-entrant runAs grants nothing --
     * see the test-class-standards examples file, Example 5, note (1).
     */
    private static User mintAgent() {
        User agent;
        System.runAs(new User(Id = UserInfo.getUserId())) {
            agent = TestUserFactory.createUser(AGENT_PROFILE, AGENT_PERMISSION_SETS);
        }
        return agent;
    }

    /**
     * Field values every Case in this build needs in order to survive the two active
     * validation rules M3-S01 writes: Origin_Must_Be_Known (Origin must be Email-Support,
     * Email-Billing or Web) and Priority_Required_On_Agent_Save (Priority not blank).
     * TestDataFactory.createCases defaults Origin to 'Email', which is not one of the
     * three values the CaseOrigin standard value set for this build defines.
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
     * Both spellings this test will accept for the deployed Standard-tier process name.
     * F-61 (reports/MOCK-DEPLOY-M5.md run 6): requireActiveProcess() previously selected
     * WHERE IsActive = true LIMIT 1 with no name filter, and a pre-existing active process
     * already in the target org (no First Response milestone) was returned instead of the
     * deployed First_Response_Standard. Standard, not Premier, is the process this test
     * fixture is written to enter -- artefacts/M4-S02/entitlementProcesses/ ships both, and
     * decisions.md D-M1S01-04 records that Support_Tier__c carries no field default, so
     * Standard is the tier this fixture names explicitly rather than assumes. Neither
     * skills/apex/entitlement-apex-hooks nor skills/admin/entitlements-and-milestones states
     * whether SlaProcess.Name preserves the metadata name attribute literally
     * (First_Response_Standard, per artefacts/M4-S02/deploy-order.md section 4.1 -- name was
     * set to match the declared file base name) or whether the platform stores a
     * space-separated label form (First Response Standard) -- UNVERIFIED, so both spellings
     * are queried rather than guessed.
     */
    private static final List<String> STANDARD_PROCESS_NAMES = new List<String>{
        'First_Response_Standard', 'First Response Standard'
    };

    /**
     * Returns the one deployed Standard-tier entitlement process, or fails the run with a
     * message that names it. Deliberately an assertion rather than `return null` -- a
     * skipped test in this domain is indistinguishable from a passing one. Filtering by name
     * (F-61) replaces the earlier any-active-process query, which a second active process in
     * the target org made unsafe to assume picks the right one.
     */
    private static SlaProcess requireActiveProcess() {
        List<SlaProcess> processes = [
            SELECT Id, Name
            FROM SlaProcess
            WHERE IsActive = true
              AND Name IN :STANDARD_PROCESS_NAMES
        ];
        Assert.areEqual(
            1,
            processes.size(),
            'Expected exactly one active SlaProcess named "First_Response_Standard" (or ' +
            'its label form "First Response Standard") in this org -- found ' +
            processes.size() + '. CaseMilestoneServiceTest cannot create this row ' +
            '(SlaProcess has no create() call), so the deployed Standard-tier entitlement ' +
            'process at artefacts/M4-S02/entitlementProcesses/' +
            'First_Response_Standard.entitlementProcess-meta.xml must exist, be active, ' +
            'and be the only match before this test can prove anything.'
        );
        return processes[0];
    }

    /**
     * Account + Entitlement, so Cases created against it enter the entitlement process. Seeded
     * in system mode (Gotcha 15): Case_Agent_Core grants the Tier 1 agent Read only on Account
     * and Entitlement, never Create, so a real Tier 1 agent could not seed this fixture and this
     * test does not pretend one does or run it under a permissioned runAs.
     */
    private static Entitlement entitlementFor(SlaProcess process, String label) {
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        TestDataFactory.insertAsSystem(accounts);

        Entitlement entitlement = new Entitlement(
            Name         = label,
            AccountId    = accounts[0].Id,
            SlaProcessId = process.Id,
            StartDate    = Date.today().addDays(-1),
            EndDate      = Date.today().addYears(1)
        );
        TestDataFactory.insertAsSystem(new List<Entitlement>{ entitlement });
        return entitlement;
    }

    /**
     * One Case already inside the entitlement process, at OPENING_STATUS. Seeded in system mode
     * (Gotcha 15), not as the agent: Case_Agent_Core carries field permissions on only
     * Severity__c, so a Case built with Subject, Origin, AccountId, Priority and EntitlementId
     * populated -- every field this fixture needs to exist for the test to be meaningful --
     * cannot be inserted while running as the Tier 1 persona. That is the correct, narrow grant
     * a real Tier 1 agent has, not a gap this fixture works around by widening it; the persona
     * only acts on the Case afterward, inside System.runAs(agent) in the calling test method.
     */
    private static Case caseInsideProcess(SlaProcess process) {
        Entitlement entitlement = entitlementFor(process, 'Milestone Test Entitlement');
        List<Case> cases = TestDataFactory.createCases(
            1,
            entitlement.AccountId,
            caseOverrides(entitlement.Id)
        );
        TestDataFactory.insertAsSystem(cases);
        return cases[0];
    }

    @IsTest
    static void triggerWritesCompletionDateOnAnOpenMilestone() {
        SlaProcess process = requireActiveProcess();
        User agent = mintAgent();
        Case subject = caseInsideProcess(process);

        System.runAs(agent) {
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
    }

    @IsTest
    static void skipsAMilestoneThatIsAlreadyCompleted() {
        SlaProcess process = requireActiveProcess();
        User agent = mintAgent();
        Case subject = caseInsideProcess(process);

        System.runAs(agent) {
            Case previous = new Case(Id = subject.Id, Status = OPENING_STATUS);
            Case responded = new Case(Id = subject.Id, Status = RESPONDED_STATUS);
            List<Case> newCases = new List<Case>{ responded };
            Map<Id, Case> oldCases = new Map<Id, Case>{ previous.Id => previous };

            // First pass completes whatever is open.
            CaseMilestoneService.CompletionResult first = CaseMilestoneService.completeMilestones(
                newCases, oldCases, MILESTONE_TYPE
            );
            Assert.isTrue(first.attempted > 0, 'Set-up pass must complete at least one milestone.');
            // F-62: a refused write (e.g. a persona with no CaseMilestone access) must fail
            // loudly here, not surface later as a second pass that finds the same open row.
            Assert.areEqual(0, first.failures.size(), String.join(first.failures, ' | '));

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
    }

    @IsTest
    static void staysAtOneQueryAndOneDmlFor200Cases() {
        SlaProcess process = requireActiveProcess();
        Entitlement entitlement = entitlementFor(process, 'Bulk Milestone Test Entitlement');
        User agent = mintAgent();

        List<Case> cases = TestDataFactory.createCases(
            200,
            entitlement.AccountId,
            caseOverrides(entitlement.Id)
        );
        // Fixture seed, not the action under test (Gotcha 15): Origin, Priority and
        // EntitlementId on these 200 Cases are fields Case_Agent_Core does not grant the
        // Tier 1 persona Edit on, so the insert runs in system mode, outside runAs(agent).
        TestDataFactory.insertAsSystem(cases);

        System.runAs(agent) {
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
            // F-62: accounted-for math alone passes even if every row failed. Assert the
            // refusal count directly so a persona lacking CaseMilestone access fails loudly.
            Assert.areEqual(0, result.failures.size(), String.join(result.failures, ' | '));
        }
    }

    @IsTest
    static void ignoresCasesWhoseStatusDidNotChange() {
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        TestDataFactory.insertAsSystem(accounts);
        User agent = mintAgent();
        List<Case> cases = TestDataFactory.createCases(1, accounts[0].Id, caseOverrides(null));
        // Fixture seed, not the action under test (Gotcha 15): Origin and Priority on this
        // Case are fields Case_Agent_Core does not grant the Tier 1 persona Edit on, so the
        // insert runs in system mode, outside runAs(agent).
        TestDataFactory.insertAsSystem(cases);

        System.runAs(agent) {
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
            // F-62: consistent with the other three completeMilestones call sites, even
            // though zero attempted implies zero failures here.
            Assert.areEqual(0, result.failures.size(), String.join(result.failures, ' | '));
        }
    }
}
