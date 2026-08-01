# Examples — Agent Security Review

## Example 1: Write-scope tightening

**Context:** a Service agent carries a generic "Update Case" action that accepts a field
name and a value, so it can write any writable field on Case.

**Problem:** the reviewable write scope is "every field on Case", which includes
`OwnerId`, `RecordTypeId` and the escalation fields. There is no server-side rule that
can distinguish a legitimate call from an abusive one, because the action has no
semantics to check against.

**Finding as written in the review, and the fix:**

**FINDING AF-03 (High)** — unbounded write scope, no sharing keyword, no FLS
enforcement. Effective write scope is every updateable field on Case:

```apex
public class UpdateCaseAction {
    public class Request {
        @InvocableVariable(required=true) public Id caseId;
        @InvocableVariable(required=true) public String fieldName;   // unbounded
        @InvocableVariable(required=true) public String value;
    }
    @InvocableMethod(label='Update Case')
    public static List<Response> run(List<Request> reqs) {
        List<Case> updates = new List<Case>();
        for (Request r : reqs) {
            Case c = new Case(Id = r.caseId);
            c.put(r.fieldName, r.value);          // any field, including OwnerId
            updates.add(c);
        }
        update updates;                            // no sharing, no FLS check
        ...
    }
}
```

**Remediation** — one named action per business operation; the field list is the scope:

```apex
public with sharing class CloseCaseAction {
    public class Request {
        @InvocableVariable(required=true) public Id caseId;
        @InvocableVariable(required=true) public String resolutionNote;
    }
    @InvocableMethod(label='Close Case')
    public static List<Response> run(List<Request> reqs) {
        Set<Id> ids = new Set<Id>();
        for (Request r : reqs) { ids.add(r.caseId); }

        // WITH USER_MODE enforces object and field permissions as well as sharing;
        // a case the running user cannot see simply does not come back.
        Map<Id, Case> visible = new Map<Id, Case>(
            [SELECT Id, Status FROM Case WHERE Id IN :ids WITH USER_MODE]);

        List<Case> updates = new List<Case>();
        List<Response> out = new List<Response>();
        for (Request r : reqs) {                   // one Response per Request, same order
            Response resp = new Response();
            if (!visible.containsKey(r.caseId)) {
                resp.reasonCode = 'NOT_VISIBLE';
            } else {
                updates.add(new Case(
                    Id = r.caseId, Status = 'Closed', Resolution__c = r.resolutionNote));
                resp.reasonCode = 'CLOSED';
            }
            out.add(resp);
        }
        Database.update(updates, AccessLevel.USER_MODE);   // FLS enforced on write too
        return out;
    }
}
```

**Why it works:** the review artefact becomes a short, diffable list — `Status` and
`Resolution__c` — instead of "every field on Case". `OwnerId` is not reachable because no
code path writes it, which is a stronger statement than any instruction or guardrail can
make. `AccessLevel.USER_MODE` on the DML closes the write side, which `with sharing`
alone does not cover.

---

## Example 2: Regulated-field exposure through grounding

**Context:** the agent grounds on Contact to answer identity questions. The grounding
selector was written by an assistant and selects a generous field list "so the agent has
context", including `Social_Security_Number__c`.

**Problem:** two separate defects, and reviewers usually find only the second. First,
the field is in the prompt at all — output filtering cannot un-send it to the model.
Second, the selector runs in system mode, so it returns contacts the running user has no
sharing access to.

**Solution — fix the projection and the access mode first, then add the output control:**

```apex
public with sharing class ContactGroundingSelector {
    // The field list is the security boundary. Anything not named here cannot be
    // exfiltrated by any prompt, because it never enters the context window.
    private static final String FIELDS =
        'Id, Name, Email, Phone, Account.Name, Preferred_Language__c';

    public static List<Contact> forGrounding(Set<Id> contactIds) {
        return Database.query(
            'SELECT ' + FIELDS + ' FROM Contact WHERE Id IN :contactIds LIMIT 50',
            AccessLevel.USER_MODE);      // sharing + CRUD + FLS, all enforced
    }
}
```

Review assertions that go with it:

1. `Social_Security_Number__c` appears in no grounding selector — grep the field API
   name across the action and selector classes; the expected result count is zero.
2. The field is classified on the object so its sensitivity is discoverable, and Trust
   Layer masking covers the corresponding PII category as a backstop.
3. A negative test exists: as a low-privilege user, ask the agent for a contact owned by
   another user and assert it cannot answer.

**Why it works:** the three controls sit at different boundaries and fail independently —
projection (the data never reaches the model), access mode (the row never reaches the
query result), masking (the value is filtered on the way out). Reviews that check only
the third one pass agents that leak.
