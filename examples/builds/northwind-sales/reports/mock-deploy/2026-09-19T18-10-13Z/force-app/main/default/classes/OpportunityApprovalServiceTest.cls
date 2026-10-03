/**
 * OpportunityApprovalServiceTest — covers the service, the @AuraEnabled controller and
 * the @InvocableMethod action of build step M3-S03, including the refusal paths.
 *
 * Build northwind-sales. One test class for all three classes because a
 * `RunSpecifiedTests` deploy applies the 75% floor per class, and the controller and the
 * action are both thin delegations with no body of their own to test separately.
 *
 * Three rules from apex/test-class-standards shape the fixture below:
 *
 *  - Gotcha 13. `OpportunityApprovalService` enforces the FLS of the running user
 *    (`WITH USER_MODE`), so a test that never leaves the context of the deploying user proves
 *    nothing about it and fails at validation when the custom fields ship in the same
 *    deployment. Every action under test therefore runs inside a persona runAs block
 *    whose user holds the `Enterprise_Sales_Record_Types` permission set this build
 *    ships (step M2-S02), which grants FLS on `Opportunity.Discount__c` and
 *    `Opportunity.Approval_Status__c` and visibility of the Enterprise and Renewal
 *    record types.
 *  - Gotcha 15. The fixture is seeded in system mode, through
 *    `TestDataFactory.insertAsSystem`, OUTSIDE any persona runAs block. Only the
 *    submission itself runs as the rep.
 *  - Gotcha 3 / apex/mixed-dml-and-setup-objects. `User` and `PermissionSetAssignment`
 *    are setup objects and cannot share a transaction with Account and Opportunity DML,
 *    so the setup-object half sits inside the self-user runAs fence in `seedFixture`.
 *    That form re-enters the context of the SAME user and grants no permission — it is not,
 *    and is not used as, the Gotcha 13 persona block.
 *
 * A note on how that is checked, and on the comment style below. The
 * `user-mode-test-without-runas` rule in `check_test_class_standards.py` blanks string
 * literals but not comments before it looks for runAs calls, and it does that on the raw
 * file. Two things follow, and this file is written around both. A runAs call spelled out
 * with an argument inside a comment satisfies the rule on its own, so no comment here
 * spells one out. And a lone apostrophe in a comment opens a phantom string literal that
 * blanks every line until the next one, hiding the real runAs calls from the rule, so the
 * comments here are written without possessive apostrophes. Neither is a style
 * preference; both are what make the declared acceptance test read the executable code.
 *
 * `TestDataFactory` is the canonical shared factory, shipped verbatim beside these
 * classes in this same step (templates/apex/tests/TestDataFactory.cls). No other
 * `templates/apex/**` class is referenced, because no other one ships here.
 *
 * The approval process under test is built by step M3-S02: one step, approver = the
 * Manager of the record owner via `nextAutomatedApprover`, entry criteria = a discount
 * above 20% on an Enterprise or Renewal record type that is not closed.
 */
@IsTest
private class OpportunityApprovalServiceTest {

    // The persona profile this build actually uses, per Q19 ("Reps and managers: the
    // standard Sales User profile") and artefacts/M2-S02/profiles/Sales User.profile-meta.xml.
    // UNVERIFIED (2026-09-19): M2-S02 deploy-order.md section 5 records the same caveat --
    // the profile Name including its space has to be confirmed against the target org, and a
    // mismatch surfaces here as a QueryException on this line rather than as a deploy error.
    private static final String PERSONA_PROFILE = 'Sales User';
    private static final String PERSONA_PERMISSION_SET = 'Enterprise_Sales_Record_Types';
    private static final String REP_ALIAS = 'nwrep';
    private static final String MANAGER_ALIAS = 'nwmgr';
    private static final String ENTERPRISE_RECORD_TYPE = 'Enterprise';
    private static final String ENTRY_STAGE = 'Qualify';
    private static final String PENDING_STATUS = 'Pending';

    // UNVERIFIED (2026-09-19): assumption A35. A Percent field carries the fraction in
    // formula context (0.20 for 20%) and the plain number outside it (20); only the
    // formula half is grounded in this library, and the entry criteria on the approval
    // process uses 0.20 accordingly. These two literals are the Apex half of that
    // assumption. If a retrieved record shows Apex reading 0.25 rather than 25, these
    // two constants are what changes — nothing else in this step depends on the reading.
    private static final Decimal QUALIFYING_DISCOUNT = 25;
    private static final Decimal BELOW_THRESHOLD_DISCOUNT = 10;

    @TestSetup
    static void seedFixture() {
        Id repId;
        // Mixed-DML fence, not a persona block — see the class header.
        System.runAs(new User(Id = UserInfo.getUserId())) {
            Profile personaProfile = [SELECT Id FROM Profile WHERE Name = :PERSONA_PROFILE LIMIT 1];

            User manager = buildUser(personaProfile.Id, MANAGER_ALIAS);
            insert manager;

            // The approval process routes to the Manager of the record owner
            // (nextAutomatedApprover / userHierarchyField Manager), so the rep needs one
            // or the submission has no approver to assign.
            User rep = buildUser(personaProfile.Id, REP_ALIAS);
            rep.ManagerId = manager.Id;
            insert rep;
            repId = rep.Id;

            PermissionSet personaSet = [
                SELECT Id FROM PermissionSet WHERE Name = :PERSONA_PERMISSION_SET LIMIT 1
            ];
            insert new List<PermissionSetAssignment>{
                new PermissionSetAssignment(AssigneeId = manager.Id, PermissionSetId = personaSet.Id),
                new PermissionSetAssignment(AssigneeId = rep.Id, PermissionSetId = personaSet.Id)
            };
        }

        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        TestDataFactory.insertAsSystem(accounts);

        // Describe-driven, never a hardcoded 012 prefix. Spelled exactly as
        // skills/apex/apex-hardcoded-id-elimination/references/examples.md:74-77 spells it.
        Id enterpriseRecordTypeId = Schema.SObjectType.Opportunity
            .getRecordTypeInfosByDeveloperName()
            .get(ENTERPRISE_RECORD_TYPE)
            .getRecordTypeId();

        // Qualify, not the default stage in the factory: the Enterprise business process built
        // by M1-S01 carries Qualify / Discover / Propose / Negotiate / Closed Won /
        // Closed Lost, and Prospecting is not one of them.
        List<Opportunity> opportunities = TestDataFactory.createOpportunities(
            1,
            accounts[0].Id,
            new Map<String, Object>{
                'RecordTypeId' => enterpriseRecordTypeId,
                'StageName'    => ENTRY_STAGE,
                'Discount__c'  => QUALIFYING_DISCOUNT,
                'OwnerId'      => repId
            }
        );
        opportunities.addAll(TestDataFactory.createOpportunities(
            1,
            accounts[0].Id,
            new Map<String, Object>{
                'RecordTypeId' => enterpriseRecordTypeId,
                'StageName'    => ENTRY_STAGE,
                'Discount__c'  => BELOW_THRESHOLD_DISCOUNT,
                'OwnerId'      => repId
            }
        ));
        TestDataFactory.insertAsSystem(opportunities);
    }

    @IsTest
    static void submitsQualifyingOpportunityAsItsOwner() {
        Opportunity target = opportunityWithDiscount(QUALIFYING_DISCOUNT);
        OpportunityApprovalService.SubmitOutcome outcome;

        Test.startTest();
        System.runAs(persona()) {
            outcome = OpportunityApprovalService.submitOne(target.Id);
        }
        Test.stopTest();

        Assert.isTrue(
            outcome.success,
            'An Enterprise opportunity above the 20% threshold and not closed meets the entry criteria: '
                + outcome.message
        );
        Assert.areEqual(
            PENDING_STATUS,
            outcome.instanceStatus,
            'A one-step process leaves the approval instance Pending after submission'
        );
        Assert.areEqual(
            1,
            [
                SELECT COUNT()
                FROM ProcessInstance
                WHERE TargetObjectId = :target.Id AND Status = :PENDING_STATUS
            ],
            'Exactly one pending ProcessInstance exists for the opportunity after a submit'
        );
    }

    @IsTest
    static void secondSubmitWhilePendingIsRefusedWithAReason() {
        Opportunity target = opportunityWithDiscount(QUALIFYING_DISCOUNT);
        OpportunityApprovalService.SubmitOutcome first;
        OpportunityApprovalService.SubmitOutcome second;

        Test.startTest();
        System.runAs(persona()) {
            first = OpportunityApprovalService.submitOne(target.Id);
            second = OpportunityApprovalService.submitOne(target.Id);
        }
        Test.stopTest();

        Assert.isTrue(first.success, 'The first submission is the one that creates the pending instance');
        Assert.isFalse(second.success, 'A record already in the approval process cannot be submitted again');
        Assert.isNotNull(
            second.message,
            'Q30: the rep is shown the reason inline, so a refused outcome always carries one'
        );
        Assert.areEqual(
            1,
            [
                SELECT COUNT()
                FROM ProcessInstance
                WHERE TargetObjectId = :target.Id AND Status = :PENDING_STATUS
            ],
            'The refused second submit created no second pending instance'
        );
    }

    @IsTest
    static void belowThresholdOpportunityIsRefusedByEntryCriteria() {
        Opportunity target = opportunityWithDiscount(BELOW_THRESHOLD_DISCOUNT);
        OpportunityApprovalService.SubmitOutcome outcome;

        Test.startTest();
        System.runAs(persona()) {
            outcome = OpportunityApprovalService.submitOne(target.Id);
        }
        Test.stopTest();

        Assert.isFalse(
            outcome.success,
            'A discount at or below the 20% threshold does not meet the process entry criteria'
        );
        Assert.isNotNull(outcome.message, 'The refusal carries the platform reason for the rep');
        Assert.areEqual(
            0,
            [SELECT COUNT() FROM ProcessInstance WHERE TargetObjectId = :target.Id],
            'A refused submission creates no approval instance at all'
        );
    }

    @IsTest
    static void controllerReturnsTheServiceOutcomeToTheComponent() {
        Opportunity target = opportunityWithDiscount(QUALIFYING_DISCOUNT);
        OpportunityApprovalService.SubmitOutcome outcome;

        Test.startTest();
        System.runAs(persona()) {
            outcome = OpportunityApprovalController.submitForApproval(target.Id);
        }
        Test.stopTest();

        Assert.isTrue(outcome.success, 'The controller submits through the same service path: ' + outcome.message);
        Assert.areEqual(
            target.Id,
            outcome.opportunityId,
            'The outcome names the record the component asked about, so the LWC can refresh it'
        );
    }

    @IsTest
    static void invocableReturnsOneResultPerRequestInInputOrder() {
        Opportunity belowThreshold = opportunityWithDiscount(BELOW_THRESHOLD_DISCOUNT);
        Opportunity qualifying = opportunityWithDiscount(QUALIFYING_DISCOUNT);

        OpportunityApprovalSubmitAction.Request refusedInput = new OpportunityApprovalSubmitAction.Request();
        refusedInput.opportunityId = belowThreshold.Id;
        OpportunityApprovalSubmitAction.Request acceptedInput = new OpportunityApprovalSubmitAction.Request();
        acceptedInput.opportunityId = qualifying.Id;

        List<OpportunityApprovalSubmitAction.Request> requests =
            new List<OpportunityApprovalSubmitAction.Request>();
        requests.add(refusedInput);
        requests.add(acceptedInput);

        List<OpportunityApprovalSubmitAction.Result> results;
        Test.startTest();
        System.runAs(persona()) {
            results = OpportunityApprovalSubmitAction.submit(requests);
        }
        Test.stopTest();

        Assert.areEqual(2, results.size(), 'One output per input, whatever each outcome was');
        Assert.isFalse(
            results[0].success,
            'Input 0 is the below-threshold opportunity, so output 0 must be its refusal'
        );
        Assert.isTrue(
            results[1].success,
            'Input 1 is the qualifying opportunity, so output 1 must be its success: ' + results[1].message
        );
        Assert.areEqual(
            PENDING_STATUS,
            results[1].instanceStatus,
            'The accepted input carries the approval instance status back to the flow'
        );
    }

    @IsTest
    static void unreadableOpportunityIsReportedWithoutASubmission() {
        Opportunity target = opportunityWithDiscount(QUALIFYING_DISCOUNT);
        Id unreadableId = target.Id;
        delete target;

        OpportunityApprovalService.SubmitOutcome outcome;
        Test.startTest();
        System.runAs(persona()) {
            outcome = OpportunityApprovalService.submitOne(unreadableId);
        }
        Test.stopTest();

        Assert.isFalse(
            outcome.success,
            'A record the WITH USER_MODE read does not return is never submitted'
        );
        Assert.isNotNull(outcome.message, 'The rep is told why nothing happened rather than seeing silence');
        Assert.areEqual(
            0,
            [SELECT COUNT() FROM ProcessInstance WHERE TargetObjectId = :unreadableId],
            'No approval instance was created for a record that could not be read'
        );
    }

    // ------------------------------------------------------------------ helpers

    private static User persona() {
        return [SELECT Id FROM User WHERE Alias = :REP_ALIAS LIMIT 1];
    }

    private static Opportunity opportunityWithDiscount(Decimal discount) {
        return [SELECT Id, OwnerId FROM Opportunity WHERE Discount__c = :discount LIMIT 1];
    }

    private static User buildUser(Id profileId, String alias) {
        String unique = String.valueOf(DateTime.now().getTime());
        return new User(
            FirstName         = 'Northwind',
            LastName          = alias,
            Alias             = alias,
            Username          = 'northwind.' + alias + '.' + unique + '@example.invalid',
            Email             = 'northwind.' + alias + '@example.invalid',
            ProfileId         = profileId,
            TimeZoneSidKey    = 'America/New_York',
            LocaleSidKey      = 'en_US',
            EmailEncodingKey  = 'UTF-8',
            LanguageLocaleKey = 'en_US'
        );
    }
}
