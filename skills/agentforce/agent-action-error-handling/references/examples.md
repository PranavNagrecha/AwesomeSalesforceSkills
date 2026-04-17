# Examples — Agent Action Error Handling

## Example 1: Typed Response envelope for a Case-update action

**Context:** Agentforce service agent closes Cases on user request.

**Problem:** Raw DmlException surfaces 'FIELD_CUSTOM_VALIDATION_EXCEPTION' text to the customer; agent retries 3x and the loop times out.

**Solution:**

```apex
public with sharing class CloseCaseAction {
    public class Request { @InvocableVariable(required=true) public Id caseId; }
    public class Response {
        @InvocableVariable public String status;        // OK | USER_ERROR | SYSTEM_ERROR
        @InvocableVariable public String reason_code;   // e.g. VALIDATION_BLOCKED
        @InvocableVariable public String user_message;  // ≤140 chars
    }
    @InvocableMethod(label='Close Case')
    public static List<Response> run(List<Request> reqs) {
        List<Response> out = new List<Response>();
        for (Request r : reqs) {
            Response resp = new Response();
            try {
                Case c = new Case(Id=r.caseId, Status='Closed');
                update c;
                resp.status='OK'; resp.reason_code='CLOSED'; resp.user_message='Closed the case.';
            } catch (DmlException e) {
                resp.status='USER_ERROR'; resp.reason_code='VALIDATION_BLOCKED';
                resp.user_message='A validation rule prevents closing this case. Please check required fields.';
            } catch (Exception e) {
                resp.status='SYSTEM_ERROR'; resp.reason_code='UNKNOWN';
                resp.user_message='Something went wrong on our side. I notified the team.';
            }
            out.add(resp);
        }
        return out;
    }
}
```

**Why it works:** Agent receives a structured result; topic instruction 'on USER_ERROR restate user_message; on SYSTEM_ERROR apologize' gives deterministic behavior instead of retry loops.


---

## Example 2: Stable reason_code enum across releases

**Context:** A new DML error type appears after a managed-package install.

**Problem:** The generic catch-all buckets it as SYSTEM_ERROR/UNKNOWN with no way for SRE to disambiguate in logs or prompt tests.

**Solution:**

Maintain the `reason_code` list in a single Custom Metadata Type `Agent_Reason_Code__mdt` with `Developer_Name`, `Is_Retryable__c`, `Severity__c`. Actions reference codes by DeveloperName; the topic instructions read the same CMDT for routing; dashboards group logs by `reason_code`.

**Why it works:** Decouples the LLM contract from Apex internals; adding a new code is a CMDT change + one topic-instruction update, not an action rewrite.

