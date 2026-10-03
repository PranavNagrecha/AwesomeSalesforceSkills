/**
 * OpportunityApprovalSubmitAction — the Flow-invocable half of step M3-S03.
 *
 * Build northwind-sales. One @InvocableMethod in its own outer class, per decision D6
 * and apexdev L5422 ("Only one method in a class can have the InvocableMethod
 * annotation") — `OpportunityApprovalController` carries the @AuraEnabled entry point
 * and `OpportunityApprovalService` carries the body.
 *
 * Bulk contract. Flow calls the action once with the whole batch of interviews, so the
 * method collects the ids first, makes one service call, and returns one Result per
 * Request in input order: "the i-th Output entry must correspond to the i-th Input entry"
 * (apexdev L5456-5458). No SOQL and no DML runs inside a loop here or in the service.
 *
 * The record-page button is a single-record path (Q29, assumption A23); this action is
 * the Flow-facing surface and is written to be correct at any batch size regardless.
 *
 * `with sharing` is declared rather than inherited, per apex/apex-security-patterns
 * ("The Default Sharing Mode Changed In API 67.0" — never rely on the version default).
 */
public with sharing class OpportunityApprovalSubmitAction {

    public class Request {
        @InvocableVariable(label='Opportunity ID' description='The opportunity to submit into the Discount Approval process.' required=true)
        public Id opportunityId;
    }

    public class Result {
        @InvocableVariable(label='Submitted' description='True when the opportunity entered the Discount Approval process.')
        public Boolean success;

        @InvocableVariable(label='Message' description='The reason the submission was refused, blank on success.')
        public String message;

        @InvocableVariable(label='Approval Instance Status' description='The approval instance status returned by the platform, for example Pending.')
        public String instanceStatus;
    }

    @InvocableMethod(label='Submit Opportunity for Discount Approval' description='Submits each opportunity into the Discount Approval process and returns one result per input, in input order.' category='Opportunity')
    public static List<Result> submit(List<Request> requests) {
        List<Id> opportunityIds = new List<Id>();
        for (Request request : requests) {
            opportunityIds.add(request.opportunityId);
        }

        List<OpportunityApprovalService.SubmitOutcome> outcomes =
            OpportunityApprovalService.submitBatch(opportunityIds);

        List<Result> results = new List<Result>();
        for (OpportunityApprovalService.SubmitOutcome outcome : outcomes) {
            Result result = new Result();
            result.success = outcome.success;
            result.message = outcome.message;
            result.instanceStatus = outcome.instanceStatus;
            results.add(result);
        }
        return results;
    }
}
