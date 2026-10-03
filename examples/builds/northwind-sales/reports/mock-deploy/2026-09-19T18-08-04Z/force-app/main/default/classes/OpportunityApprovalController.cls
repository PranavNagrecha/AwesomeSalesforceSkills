/**
 * OpportunityApprovalController — the @AuraEnabled entry point the
 * `discountApprovalPanel` LWC (build step M3-S04) imports.
 *
 * Build northwind-sales, step M3-S03. It exists as its own class for the reason
 * decision D6 records: an LWC can only import an @AuraEnabled method, and
 * "The only annotation that can be used with the InvocableMethod annotation is
 * Deprecated" (apexdev L5430), so the two entry points cannot share a method.
 * All behaviour lives in `OpportunityApprovalService`; this class adds nothing but
 * the annotation.
 *
 * Not `cacheable=true`: the method submits a record for approval, and a cacheable
 * Apex method must not mutate data.
 *
 * It returns the outcome object rather than throwing an AuraHandledException on
 * refusal, because Q30's answer is that the rep sees the failure reason inline in
 * the component (toast and text) — an outcome with `success = false` and a
 * `message` gives the component both without an exception path to unwrap.
 *
 * `with sharing` is declared rather than inherited, per apex/apex-security-patterns
 * ("The Default Sharing Mode Changed In API 67.0" — never rely on the version default).
 */
public with sharing class OpportunityApprovalController {

    @AuraEnabled
    public static OpportunityApprovalService.SubmitOutcome submitForApproval(Id opportunityId) {
        return OpportunityApprovalService.submitOne(opportunityId);
    }
}
