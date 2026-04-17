/**
 * SummarizeAccountCasesAction — Agentforce invocable action.
 *
 * Emitted by the agentforce-builder live-green fixture. Returns a plain-text
 * summary of case counts for a given Account so a Service Agent can answer
 * "how many cases does this account have" without a raw SOQL excursion.
 *
 * Gate C live oracle: sf project deploy validate against sfskills-dev.
 */
public with sharing class SummarizeAccountCasesAction {

    @InvocableMethod(
        label='Summarize Account Cases'
        description='Returns a plain-text summary of recent case counts for the given Account ids.'
        category='Agentforce'
    )
    public static List<Response> run(List<Request> requests) {
        List<Response> responses = new List<Response>();
        if (requests == null || requests.isEmpty()) {
            return responses;
        }

        Set<Id> accountIds = new Set<Id>();
        for (Request r : requests) {
            if (r != null && r.accountId != null) {
                accountIds.add(r.accountId);
            }
        }

        Map<Id, Account> accounts = new Map<Id, Account>(
            [SELECT Id, Name FROM Account WHERE Id IN :accountIds]
        );

        Map<Id, Integer> caseCounts = new Map<Id, Integer>();
        for (AggregateResult ar : [
            SELECT AccountId acct, COUNT(Id) cnt
            FROM Case
            WHERE AccountId IN :accountIds
            GROUP BY AccountId
        ]) {
            caseCounts.put((Id) ar.get('acct'), (Integer) ar.get('cnt'));
        }

        for (Request r : requests) {
            Response resp = new Response();
            try {
                if (r == null || r.accountId == null) {
                    resp.success = false;
                    resp.errorMessage = 'accountId is required';
                    resp.summary = null;
                } else if (!accounts.containsKey(r.accountId)) {
                    resp.success = false;
                    resp.errorMessage = 'Account not found or not accessible';
                    resp.summary = null;
                } else {
                    Account a = accounts.get(r.accountId);
                    Integer count = caseCounts.containsKey(r.accountId) ? caseCounts.get(r.accountId) : 0;
                    resp.success = true;
                    resp.errorMessage = null;
                    resp.summary = a.Name + ' has ' + count + ' case(s) on file.';
                }
            } catch (Exception e) {
                resp.success = false;
                resp.errorMessage = e.getMessage();
                resp.summary = null;
            }
            responses.add(resp);
        }
        return responses;
    }

    public class Request {
        @InvocableVariable(label='Account Id' description='Id of the Account to summarize' required=true)
        public Id accountId;
    }

    public class Response {
        @InvocableVariable(label='Success' description='True when the action produced a summary')
        public Boolean success;

        @InvocableVariable(label='Summary' description='Plain-text summary for the Agent to speak')
        public String summary;

        @InvocableVariable(label='Error Message' description='Human-readable error, null on success')
        public String errorMessage;
    }
}
