/**
 * OpportunityApprovalService — submits Opportunities into the `Discount_Approval`
 * approval process and reports one outcome per record.
 *
 * Build northwind-sales, step M3-S03. The approval process this names is built by
 * M3-S02 (`artefacts/M3-S02/approvalProcesses/Opportunity.Discount_Approval.approvalProcess-meta.xml`):
 * one step, approver = the record owner's Manager, entry criteria = Discount above
 * 20% on an Enterprise or Renewal record type that is not closed, record locked on
 * submit (`recordEditability` AdminOnly).
 *
 * Shape (plan decision D6): this class holds the body. `OpportunityApprovalController`
 * is the @AuraEnabled entry point the LWC imports and `OpportunityApprovalSubmitAction`
 * holds the single @InvocableMethod, because "The only annotation that can be used with
 * the InvocableMethod annotation is Deprecated" (apexdev L5430).
 *
 * Sharing and access mode. `with sharing` is declared rather than inherited: per
 * apex/apex-security-patterns ("The Default Sharing Mode Changed In API 67.0"), never
 * rely on the version default. This class's `.cls-meta.xml` pins apiVersion 62.0, where
 * the default ACCESS mode is still system mode, so the single SOQL below states
 * `WITH USER_MODE` explicitly — the read idiom for 57.0–66.0 in
 * agents/_shared/AGENT_CONTRACT.md § "Apex security idiom by API version".
 * There is no elevation anywhere in this class and therefore no `// reason:` comment.
 *
 * Source for every Approval.* identifier below:
 * skills/admin/approval-process-apex-patterns/references/metadata-examples.md
 * ("The Apex service class").
 */
public with sharing class OpportunityApprovalService {

    /** Written into the approval history so the approver knows where the request came from. */
    @TestVisible
    private static final String SUBMIT_COMMENT =
        'Submitted from the Discount panel on the opportunity record page.';

    /** Returned when the running user cannot read the record, so nothing is submitted. */
    @TestVisible
    private static final String NOT_READABLE_MESSAGE =
        'This opportunity could not be read with your permissions, so nothing was submitted.';

    /**
     * What the caller gets back. @AuraEnabled on each member because the LWC built by
     * M3-S04 reads this object directly (Q30: the rep sees the failure reason inline).
     */
    public class SubmitOutcome {
        @AuraEnabled public Id opportunityId;
        @AuraEnabled public Boolean success;
        @AuraEnabled public String message;
        @AuraEnabled public String instanceStatus;
    }

    /**
     * The capability the requirement asks for: one opportunity, one outcome
     * (Q29 "Always exactly one opportunity from the button click"; assumption A23).
     * Delegates to `submitBatch` so there is exactly one submission path to test.
     */
    public static SubmitOutcome submitOne(Id opportunityId) {
        return submitBatch(new List<Id>{ opportunityId })[0];
    }

    /**
     * The bulk primitive. It exists because @InvocableMethod is a List-in / List-out
     * contract (apexdev L5432, L5443-5454) and a Flow hands the action a whole batch of
     * interviews at once; a per-input query and a per-input `Approval.process` would burn
     * the 100-SOQL / 150-DML transaction budget. One SOQL and one `Approval.process`
     * call serve any input size.
     *
     * Returns one outcome per input id, in input order, so the i-th output corresponds
     * to the i-th input (apexdev L5456-5458).
     */
    public static List<SubmitOutcome> submitBatch(List<Id> opportunityIds) {
        Map<Id, SubmitOutcome> outcomeById = new Map<Id, SubmitOutcome>();
        for (Id opportunityId : opportunityIds) {
            outcomeById.put(opportunityId, outcome(opportunityId, false, NOT_READABLE_MESSAGE, null));
        }

        // WITH USER_MODE: the running user's object permissions, FLS and sharing rules
        // decide what comes back, so a rep who cannot see the record gets the seeded
        // refusal above instead of a submission on a record they cannot read.
        Map<Id, Opportunity> readable = new Map<Id, Opportunity>([
            SELECT Id, OwnerId
            FROM Opportunity
            WHERE Id IN :opportunityIds
            WITH USER_MODE
        ]);

        List<Id> submittedIds = new List<Id>();
        List<Approval.ProcessSubmitRequest> requests = new List<Approval.ProcessSubmitRequest>();
        for (Id opportunityId : opportunityIds) {
            Opportunity record = readable.get(opportunityId);
            if (record == null) {
                continue;
            }
            Approval.ProcessSubmitRequest request = new Approval.ProcessSubmitRequest();
            request.setObjectId(record.Id);
            // The developer name as a literal, never a 300-prefixed record Id:
            // "Approval-process record Ids differ per org and per sandbox refresh"
            // (approval-process-apex-patterns gotcha 1). It is written inline rather than
            // read from a constant on purpose — check_approval_process_apex_patterns.py
            // resolves the name against the approvalProcess metadata in the tree only when
            // it can see the string in the call, and a constant hides it (the declared
            // acceptance test then exits 0 having checked nothing). Naming the process is
            // also what makes setSkipEntryCriteria meaningful at all (gotcha 15) and what
            // decision D9 relies on when it ships the process `active` true.
            request.setProcessDefinitionNameOrId('Discount_Approval');
            // The process's allowedSubmitters is <type>owner</type>, so the owner always
            // qualifies (gotcha 11), and naming the submitter keeps the approval history
            // reading "submitted by the rep" rather than by whatever context ran the code
            // (gotcha 3).
            request.setSubmitterId(record.OwnerId);
            // False, deliberately: the 20% threshold is the admin's entry criterion and
            // this service does not get to bypass it. The pair is only honoured because
            // the process is named above (gotcha 15).
            request.setSkipEntryCriteria(false);
            request.setComments(SUBMIT_COMMENT);
            requests.add(request);
            submittedIds.add(record.Id);
        }

        if (!requests.isEmpty()) {
            try {
                // allOrNone = false: one refused row must not roll back the others
                // (gotcha 2). Each call is ONE DML statement against the 150 budget.
                Approval.ProcessResult[] results = Approval.process(requests, false);
                for (Integer i = 0; i < results.size(); i++) {
                    outcomeById.put(submittedIds[i], fromResult(submittedIds[i], results[i]));
                }
            } catch (DmlException error) {
                // Defensive: allOrNone=false returns per-row errors rather than throwing,
                // so this path is reached only when the platform rejects the whole call.
                // Q30 says the rep is shown a reason either way, so it is turned into one.
                for (Id opportunityId : submittedIds) {
                    outcomeById.put(opportunityId, outcome(opportunityId, false, error.getMessage(), null));
                }
            }
        }

        return inInputOrder(opportunityIds, outcomeById);
    }

    private static SubmitOutcome fromResult(Id opportunityId, Approval.ProcessResult result) {
        if (result.isSuccess()) {
            // Assert on the status, not only the boolean: a one-step process leaves the
            // instance Pending, and the component shows that to the rep.
            return outcome(opportunityId, true, null, result.getInstanceStatus());
        }
        return outcome(opportunityId, false, describe(result.getErrors()), null);
    }

    private static String describe(Database.Error[] errors) {
        List<String> parts = new List<String>();
        for (Database.Error error : errors) {
            parts.add(error.getStatusCode() + ': ' + error.getMessage());
        }
        return String.join(parts, ' | ');
    }

    private static List<SubmitOutcome> inInputOrder(
        List<Id> opportunityIds,
        Map<Id, SubmitOutcome> outcomeById
    ) {
        List<SubmitOutcome> ordered = new List<SubmitOutcome>();
        for (Id opportunityId : opportunityIds) {
            ordered.add(outcomeById.get(opportunityId));
        }
        return ordered;
    }

    private static SubmitOutcome outcome(
        Id opportunityId,
        Boolean success,
        String message,
        String instanceStatus
    ) {
        SubmitOutcome built = new SubmitOutcome();
        built.opportunityId = opportunityId;
        built.success = success;
        built.message = message;
        built.instanceStatus = instanceStatus;
        return built;
    }
}
