/**
 * AgentActionSkeleton
 *
 * Canonical Apex invocable action for Agentforce / Einstein Copilot.
 * Copy, rename, and fill in the TODO sections.
 *
 * Design rules for AI agent actions:
 *   1. One action = one verb. No "do X and Y and Z" mega-actions.
 *   2. Every input and output is typed with @InvocableVariable and documented
 *      in `label` / `description` — the LLM reads these to decide whether to
 *      call your action.
 *   3. Always accept `List<Request>` and return `List<Response>`. This enables
 *      bulk invocation and is required for record-triggered paths.
 *   4. No silent fallbacks. Any validation failure returns an Error response —
 *      the LLM must see that the call failed and can replan.
 *   5. Enforce CRUD/FLS and sharing like any other Apex — the running user's
 *      context is preserved in agent actions.
 */
public with sharing class AgentActionSkeleton {

    @InvocableMethod(
        label='Example Agent Action'
        description='One-sentence summary of what this action does for the agent. Keep under 200 chars — the planner uses this to decide relevance.'
        category='Skill Category'
    )
    public static List<Response> invoke(List<Request> requests) {
        List<Response> results = new List<Response>();
        for (Request req : requests) {
            Response res = new Response();
            try {
                validate(req);
                res = execute(req);
                res.success = true;
            } catch (Exception e) {
                res.success = false;
                res.errorMessage = e.getMessage();
                ApplicationLogger.error('AgentActionSkeleton', e);
            }
            results.add(res);
        }
        return results;
    }

    private static void validate(Request req) {
        if (String.isBlank(req.recordId)) {
            throw new IllegalArgumentException('recordId is required.');
        }
    }

    private static Response execute(Request req) {
        // TODO: Implement the action. Keep this method pure — no side effects
        // beyond the single verb this action represents.
        Response r = new Response();
        r.summary = 'Action complete for ' + req.recordId;
        return r;
    }

    // ─── Request / Response contract ─────────────────────────────────────────

    public class Request {
        @InvocableVariable(
            label='Record ID'
            description='The Salesforce Id of the record this action operates on. Must be a valid 15/18 char Id.'
            required=true
        )
        public String recordId;

        @InvocableVariable(
            label='Instruction'
            description='Optional free-text instruction from the user. Use this only when structured inputs are insufficient.'
            required=false
        )
        public String instruction;
    }

    public class Response {
        @InvocableVariable(label='Success' description='True if the action completed without error.')
        public Boolean success;

        @InvocableVariable(label='Summary' description='Short user-facing summary for the agent to quote back to the user.')
        public String summary;

        @InvocableVariable(label='Error Message' description='Populated only when success=false.')
        public String errorMessage;
    }

    public class IllegalArgumentException extends Exception {}
}
