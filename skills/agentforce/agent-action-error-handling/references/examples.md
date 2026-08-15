# Examples — Agent Action Error Handling

Four worked examples. The platform constraint underneath all of them is a single
documented rule from the `@InvocableMethod` reference:

> The inputs and outputs *"must match on both the size and the order"*, and
> methods *"must return the same number of results as inputs received, even when
> errors occur."*
> — [InvocableMethod Annotation](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm)

An error is therefore not an exception you throw. It is a **value you return in
the slot that belongs to the failing request**. Everything else in this skill
follows from that.

The canonical starting shape is `templates/agentforce/AgentActionSkeleton.cls`.
The examples below specialise it; do not re-invent the skeleton inline.

---

## Example 1 — WRONG vs RIGHT: a Case-closing action

### Context

A service agent closes Cases on request. A validation rule on `Case` requires
`Resolution_Summary__c` before `Status = 'Closed'`.

### WRONG — throw and let the platform deal with it

```apex
public with sharing class CloseCaseAction {

    public class Request {
        @InvocableVariable(required=true)
        public Id caseId;
    }

    @InvocableMethod(label='Close Case')
    public static List<String> run(List<Request> requests) {
        List<String> out = new List<String>();
        for (Request r : requests) {
            Case c = new Case(Id = r.caseId, Status = 'Closed');
            update c;                      // throws DmlException
            out.add('Closed');
        }
        return out;
    }
}
```

Four distinct defects:

1. **The exception escapes.** The framework surfaces a failure the planner
   cannot interpret as data, and the raw message —
   `FIELD_CUSTOM_VALIDATION_EXCEPTION, Resolution summary is required: [Resolution_Summary__c]`
   — is implementation detail the customer should never see.
2. **The loop aborts.** Request 3 of 5 throws, and requests 4 and 5 never
   execute. The output list has 2 entries for 5 inputs, violating the size rule.
3. **`List<String>` carries no structure.** The planner cannot distinguish
   "the user must supply something" from "our system is down", so it has no
   basis for choosing between re-asking and giving up. In practice it re-invokes
   with identical inputs.
4. **The DML is inside the loop.** With a bulk invocation this burns the DML
   statement limit; `LimitException` is not catchable, so no amount of
   `try/catch` below saves it.

### RIGHT — typed envelope, bulk-safe, one response per request

```apex
/**
 * CloseCaseAction
 *
 * Contract with the planner:
 *   status      OK | USER_ERROR | SYSTEM_ERROR
 *   reasonCode  stable enum string, safe to branch subagent instructions on
 *   userMessage <= 140 chars, safe to read aloud verbatim
 *   retryable   true only when re-invoking with the SAME inputs could succeed
 *
 * Never throws. Never returns fewer Responses than Requests.
 */
public with sharing class CloseCaseAction {

    public class Request {
        @InvocableVariable(
            required=true
            label='Case Id'
            description='Id of the Case to close.')
        public Id caseId;

        @InvocableVariable(
            label='Resolution Summary'
            description='One-sentence summary of how the case was resolved. Required by policy.')
        public String resolutionSummary;
    }

    public class Response {
        @InvocableVariable(label='Status' description='OK, USER_ERROR, or SYSTEM_ERROR.')
        public String status;

        @InvocableVariable(label='Reason Code' description='Stable machine-readable outcome code.')
        public String reasonCode;

        @InvocableVariable(label='User Message' description='Short sentence safe to show the user.')
        public String userMessage;

        @InvocableVariable(label='Retryable' description='True if retrying with the same inputs may succeed.')
        public Boolean retryable;
    }

    @InvocableMethod(
        label='Close Case'
        description='Closes a case and records a resolution summary. Returns a status and reason code; never throws.'
        category='Case Management')
    public static List<Response> run(List<Request> requests) {

        // Pre-size the output so index i always maps to requests[i].
        List<Response> out = new List<Response>();
        for (Integer i = 0; i < requests.size(); i++) {
            out.add(null);
        }

        // --- Phase 1: validate, collect the work, and answer the rest now ---
        Map<Integer, Case> toUpdate = new Map<Integer, Case>();
        for (Integer i = 0; i < requests.size(); i++) {
            Request r = requests[i];
            if (String.isBlank(r.resolutionSummary)) {
                out[i] = fail('USER_ERROR', 'RESOLUTION_SUMMARY_REQUIRED',
                    'I need a one-sentence summary of how this was resolved before I can close it.',
                    false);
                continue;
            }
            toUpdate.put(i, new Case(
                Id = r.caseId,
                Status = 'Closed',
                Resolution_Summary__c = r.resolutionSummary));
        }

        if (toUpdate.isEmpty()) {
            return out;
        }

        // --- Phase 2: one partial-success DML for the whole batch ---
        List<Integer> indexes = new List<Integer>(toUpdate.keySet());
        List<Case> cases = new List<Case>();
        for (Integer i : indexes) {
            cases.add(toUpdate.get(i));
        }

        // allOrNone = false: one bad row must not fail the other four.
        // Database.update returns results in input order, so results[n]
        // corresponds to indexes[n].
        List<Database.SaveResult> results = Database.update(cases, false, AccessLevel.USER_MODE);

        for (Integer n = 0; n < results.size(); n++) {
            Integer slot = indexes[n];
            Database.SaveResult sr = results[n];
            if (sr.isSuccess()) {
                Response ok = new Response();
                ok.status = 'OK';
                ok.reasonCode = 'CASE_CLOSED';
                ok.userMessage = 'Done — I closed that case.';
                ok.retryable = false;
                out[slot] = ok;
            } else {
                out[slot] = classify(sr.getErrors());
            }
        }
        return out;
    }

    /**
     * Translate DML errors into a stable reason code.
     * StatusCode is an enum on the platform, so branching on it is durable in a
     * way that branching on getMessage() text is not.
     */
    private static Response classify(List<Database.Error> errors) {
        Database.Error e = errors[0];
        StatusCode code = e.getStatusCode();

        if (code == StatusCode.FIELD_CUSTOM_VALIDATION_EXCEPTION) {
            return fail('USER_ERROR', 'VALIDATION_BLOCKED',
                'A business rule is preventing this case from closing. Please check the required fields.',
                false);
        }
        if (code == StatusCode.INSUFFICIENT_ACCESS_OR_READONLY
            || code == StatusCode.INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY) {
            return fail('USER_ERROR', 'NO_ACCESS',
                'You don\'t have permission to close that case. I can route it to someone who does.',
                false);
        }
        if (code == StatusCode.ENTITY_IS_DELETED) {
            return fail('USER_ERROR', 'RECORD_GONE',
                'That case no longer exists.', false);
        }
        if (code == StatusCode.UNABLE_TO_LOCK_ROW) {
            // Genuinely transient: the same inputs can succeed on a retry.
            return fail('SYSTEM_ERROR', 'ROW_LOCK_CONTENTION',
                'The case was busy. I\'ll try that again.', true);
        }

        // Unknown platform error: log the detail, tell the user nothing about it.
        ApplicationLogger.error('CloseCaseAction',
            'Unclassified DML error: ' + code + ' | ' + e.getMessage());
        return fail('SYSTEM_ERROR', 'UNKNOWN',
            'Something went wrong on our side. I\'ve logged it for the team.', false);
    }

    private static Response fail(String status, String reason, String message, Boolean retryable) {
        Response r = new Response();
        r.status = status;
        r.reasonCode = reason;
        r.userMessage = message;
        r.retryable = retryable;
        return r;
    }
}
```

### Why each design choice is load-bearing

- **Pre-sized output list.** The slot for request *i* exists before any work
  happens, so an early `continue` cannot desynchronise the ordering. This is the
  only shape that satisfies the size-and-order rule under partial failure.
- **`Database.update(..., false, ...)`** rather than `update`. Partial success is
  the whole point: request 3 failing must not deny requests 1, 2, 4, and 5 an
  answer.
- **`AccessLevel.USER_MODE`** on the DML. Agent actions run as a real user;
  enforce their CRUD and FLS rather than relying on `with sharing` alone (which
  governs record visibility, not field permissions).
- **Branching on `StatusCode`, not on message text.** Salesforce localises and
  occasionally rewords error messages. The enum is a stable contract; the string
  is not.
- **`retryable` is a separate field from `status`.** Both `USER_ERROR` and
  `SYSTEM_ERROR` can be either. A row lock is a system error that *is* retryable;
  a validation rule failure is a user error that is not. Collapsing the two into
  one field is the most common cause of agent retry loops.

---

## Example 2 — The subagent instructions that make the envelope worth having

A typed envelope with no matching instructions is dead weight — the planner sees
JSON and improvises. Add one rule per outcome class in the subagent instructions
(called topic instructions before April 2026;
`templates/agentforce/AgentTopic_Template.md` has the section shape):

```text
When the Close Case action returns:

- status = OK
  Confirm to the user using userMessage. Do not call the action again for
  this case in this conversation.

- status = USER_ERROR and retryable = false
  Tell the user exactly what userMessage says. Ask for the missing information
  if reasonCode is RESOLUTION_SUMMARY_REQUIRED. Do not call the action again
  until the user supplies new input.

- status = USER_ERROR and reasonCode = NO_ACCESS
  Tell the user what userMessage says, then offer to escalate to a human agent.
  Do not attempt the action again.

- status = SYSTEM_ERROR and retryable = true
  Call the action once more with the same inputs. If it fails a second time,
  treat it as retryable = false.

- status = SYSTEM_ERROR and retryable = false
  Apologise using userMessage and offer to escalate. Never speculate about the
  cause and never repeat any technical detail.
```

Two properties make this work:

1. **The instruction branches on `reasonCode` and `retryable`, not on message
   text.** Rewording `userMessage` for tone cannot break routing.
2. **"Do not call the action again" is explicit.** Without it the planner's
   default behaviour on an unsatisfied goal is to try again, which is precisely
   the loop this skill exists to prevent.

---

## Example 3 — Callout failures: the error taxonomy that actually differs

### Context

An action checks order status against an external ERP through a Named
Credential. `callout=true` is required on the annotation.

### Problem

Every callout failure is caught by one `catch (CalloutException e)` and returned
as `SYSTEM_ERROR/UNKNOWN`. The agent apologises identically for a 404 (the order
genuinely does not exist — a *user* error the agent should explain) and a 503
(transient — worth one retry).

### Solution — classify on the HTTP response, not on the exception

```apex
public with sharing class GetOrderStatusAction {

    public class Request {
        @InvocableVariable(required=true label='Order Number'
            description='Customer-facing order number, e.g. SO-10045.')
        public String orderNumber;
    }

    public class Response {
        @InvocableVariable public String status;
        @InvocableVariable public String reasonCode;
        @InvocableVariable public String userMessage;
        @InvocableVariable public Boolean retryable;
        @InvocableVariable(label='Order Status'
            description='Fulfilment status when reasonCode is ORDER_FOUND.')
        public String orderStatus;
    }

    @InvocableMethod(
        label='Get Order Status'
        description='Looks up fulfilment status for one order number in the ERP.'
        callout=true)
    public static List<Response> run(List<Request> requests) {
        List<Response> out = new List<Response>();
        for (Request r : requests) {
            out.add(lookup(r));
        }
        return out;
    }

    private static Response lookup(Request r) {
        Response resp = new Response();
        resp.retryable = false;

        if (String.isBlank(r.orderNumber)) {
            return err(resp, 'USER_ERROR', 'ORDER_NUMBER_MISSING',
                'Which order number should I look up?', false);
        }

        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:ERP_Orders/v1/orders/'
            + EncodingUtil.urlEncode(r.orderNumber, 'UTF-8'));
        req.setMethod('GET');
        req.setTimeout(20000);   // ceiling is 120000 ms; 20s leaves room for the turn

        try {
            HttpResponse res = new Http().send(req);
            Integer code = res.getStatusCode();

            if (code == 200) {
                Map<String, Object> body =
                    (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
                resp.status = 'OK';
                resp.reasonCode = 'ORDER_FOUND';
                resp.orderStatus = String.valueOf(body.get('fulfilmentStatus'));
                resp.userMessage = 'I found that order.';
                return resp;
            }
            if (code == 404) {
                // Not a system failure — the agent should say so plainly.
                return err(resp, 'USER_ERROR', 'ORDER_NOT_FOUND',
                    'I couldn\'t find an order with that number. Could you double-check it?',
                    false);
            }
            if (code == 401 || code == 403) {
                // Config problem. Never expose it; page the team.
                ApplicationLogger.error('GetOrderStatusAction',
                    'ERP auth failure ' + code + ' — check Named Credential ERP_Orders');
                return err(resp, 'SYSTEM_ERROR', 'UPSTREAM_AUTH',
                    'I can\'t reach the order system right now. Let me get someone to help.',
                    false);
            }
            if (code == 429 || code >= 500) {
                return err(resp, 'SYSTEM_ERROR', 'UPSTREAM_UNAVAILABLE',
                    'The order system is busy. Give me a moment and I\'ll try again.',
                    true);
            }
            ApplicationLogger.error('GetOrderStatusAction', 'Unexpected ERP status ' + code);
            return err(resp, 'SYSTEM_ERROR', 'UNKNOWN',
                'Something went wrong looking that up. I\'ve logged it.', false);

        } catch (System.CalloutException e) {
            // Timeout, DNS failure, TLS failure, unreachable endpoint.
            ApplicationLogger.error('GetOrderStatusAction', e);
            return err(resp, 'SYSTEM_ERROR', 'UPSTREAM_TIMEOUT',
                'The order system didn\'t respond in time. I\'ll try once more.', true);
        } catch (System.JSONException e) {
            // Upstream returned 200 with a body we cannot parse — a contract break.
            ApplicationLogger.error('GetOrderStatusAction', e);
            return err(resp, 'SYSTEM_ERROR', 'UPSTREAM_CONTRACT',
                'I got an unexpected response from the order system.', false);
        }
    }

    private static Response err(Response resp, String status, String reason,
                                String message, Boolean retryable) {
        resp.status = status;
        resp.reasonCode = reason;
        resp.userMessage = message;
        resp.retryable = retryable;
        return resp;
    }
}
```

### Why `404` is `USER_ERROR`

The status class is about **who can act on it**, not about where the failure
occurred. A 404 means the user's input was wrong and the user can fix it — so
the agent should say what is wrong and ask again. A 503 means nobody in the
conversation can fix it. Classifying by locus-of-control is what turns the
envelope into useful routing instead of a relabelled stack trace.

Note the annotation carries `callout=true`. Without it the callout fails at
runtime, and `HttpClient` in `templates/apex/HttpClient.cls` is the canonical
place to put retry and timeout policy shared across actions.

---

## Example 4 — Reason codes as governed data, not string literals

### Context

Six actions, thirty reason codes, three of them spelled two ways
(`NO_ACCESS`, `NOACCESS`, `ACCESS_DENIED`). Subagent instructions branch on one
spelling and dashboards group by another.

### Problem

Reason codes are the contract between Apex, subagent instructions, and analytics.
Three consumers, string literals, no schema — they diverge on the first
release where two people add codes in parallel.

### Solution — one Custom Metadata Type as the registry

```text
Agent_Reason_Code__mdt
  DeveloperName          e.g. VALIDATION_BLOCKED
  MasterLabel            "Validation rule blocked the update"
  Status__c              OK | USER_ERROR | SYSTEM_ERROR   (picklist)
  Is_Retryable__c        Checkbox
  Severity__c            INFO | WARN | ERROR              (picklist)
  Owning_Action__c       Text — which action emits it
  Introduced_In__c       Text — release tag, for deprecation tracking
```

Three consumers, one source:

1. **Apex** asserts in a test that every literal it emits exists in the CMDT:

```apex
@IsTest
static void every_emitted_reason_code_is_registered() {
    Set<String> registered = new Set<String>();
    for (Agent_Reason_Code__mdt m : Agent_Reason_Code__mdt.getAll().values()) {
        registered.add(m.DeveloperName);
    }
    for (String code : CloseCaseAction.EMITTED_REASON_CODES) {
        Assert.isTrue(registered.contains(code),
            'Reason code ' + code + ' is emitted but not registered in Agent_Reason_Code__mdt');
    }
}
```

2. **Subagent instructions** are generated from the CMDT rather than hand-written,
   so a new code cannot ship without a routing rule.
3. **Dashboards** group log records by `reasonCode` and join to the CMDT for the
   human label and severity.

**Why CMDT rather than an Apex enum:** the codes must be readable by the
instruction-generation step and by reporting, both of which are outside Apex.
CMDT is deployable, packageable, queryable without SOQL limits
(`getAll()`), and diffable in git — every property the contract needs.

**The migration path when a code must change:** add the new code, emit both for
one release with the old marked `Deprecated__c`, update instructions, then
remove. Never rename in place — an in-flight conversation holds the old code in
its history and the planner will encounter a code its instructions don't cover.
