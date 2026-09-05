# Examples — Invocable Methods

## Example 1: Wrapper DTO Pattern For Flow

**Context:** A Flow needs to request contact reactivation with a reason code and return per-record outcomes.

**Problem:** A primitive-only method signature cannot express the contract clearly or return structured results.

**Solution:**

```apex
public with sharing class ContactReactivationAction {

    public class Request {
        @InvocableVariable(required=true label='Contact Id')
        public Id contactId;

        @InvocableVariable(required=true label='Reason Code')
        public String reasonCode;
    }

    public class Result {
        @InvocableVariable(label='Success')
        public Boolean success;

        @InvocableVariable(label='Message')
        public String message;
    }

    @InvocableMethod(label='Reactivate Contacts' description='Reactivates contacts and returns per-record outcomes')
    public static List<Result> reactivate(List<Request> requests) {
        return ContactReactivationService.reactivate(requests);
    }
}
```

**Why it works:** Flow builders get labeled inputs and outputs, while the service layer stays reusable. `required=true` is on the *input* fields only — on an output variable "The value is ignored" (apexdev L5691), so it would promise the flow builder nothing.

---

## Example 2: Bulk-Safe Action Delegating To A Service

**Context:** A record-triggered Flow can invoke the action for multiple records.

**Problem:** A single-record implementation works in a demo but fails under bulk orchestration.

**Solution:**

```apex
public inherited sharing class ContactReactivationService {
    public static List<ContactReactivationAction.Result> reactivate(
        List<ContactReactivationAction.Request> requests
    ) {
        Set<Id> contactIds = new Set<Id>();
        for (ContactReactivationAction.Request request : requests) {
            contactIds.add(request.contactId);
        }

        Map<Id, Contact> contactsById = new Map<Id, Contact>([
            SELECT Id, Status__c
            FROM Contact
            WHERE Id IN :contactIds
        ]);

        List<Contact> updates = new List<Contact>();
        List<ContactReactivationAction.Result> results = new List<ContactReactivationAction.Result>();

        for (ContactReactivationAction.Request request : requests) {
            Contact contactRecord = contactsById.get(request.contactId);
            ContactReactivationAction.Result result = new ContactReactivationAction.Result();
            if (contactRecord == null) {
                result.success = false;
                result.message = 'Contact not found.';
            } else {
                contactRecord.Status__c = 'Active';
                updates.add(contactRecord);
                result.success = true;
                result.message = 'Reactivated.';
            }
            results.add(result);
        }

        update updates;
        return results;
    }
}
```

**Why it works:** The action gathers IDs, queries once, and updates in bulk while still returning per-request results — one result appended per request, so the output list is the same size and order as the input (apexdev L5456–5457).

What this version still owes: the `update` is all-or-nothing, so one row-level failure rolls back the other 199 and the `success` flags already set become fiction. `references/code-examples.md` §3 shows the `Database.update(records, false, AccessLevel.USER_MODE)` form the guide's own `AccountInsertAction` sample uses (apexdev L5220–5236), which gives per-row outcomes and enforces the running user's FLS.

---

## Anti-Pattern: Single Primitive Input With Hidden Single-Record Assumption

**What practitioners do:** They write an invocable that handles one record only because that is how the first Flow uses it.

**What goes wrong:** Later bulk invocations hit SOQL-in-loop or DML-in-loop patterns and the contract becomes hard to extend.

**Correct approach:** Treat invocable methods as list-oriented from the start.


---

## Example 3: Proving The Index Contract Over REST Before Wiring A Flow

**Context:** The action is deployed and the team wants evidence that the output list is
index-aligned before an admin builds a flow on top of it.

**Problem:** A flow run proves the happy path. It does not prove that result `[1]` belongs to input
`[1]` when input `[1]` fails, which is the case that silently corrupts data later.

**Solution:** POST two inputs — one that must succeed, one that must fail — to the custom-action
resource and read the shape of the response, not just its status code.

```json
{
  "inputs": [
    { "caseId": "5003000000D8cuIAAR", "reason": "SLA breach",   "targetPriority": "High" },
    { "caseId": "5003000000AAAAAAAA", "reason": "Deleted case", "targetPriority": "High" }
  ]
}
```

A correct action answers with **two** entries, positionally aligned with the request:

```json
[
  {
    "actionName": "CaseEscalationAction",
    "errors": null,
    "isSuccess": true,
    "outputValues": {
      "success": true,
      "caseId": "5003000000D8cuIAAR",
      "previousPriority": "Low",
      "errorMessage": null
    }
  },
  {
    "actionName": "CaseEscalationAction",
    "errors": null,
    "isSuccess": true,
    "outputValues": {
      "success": false,
      "caseId": "5003000000AAAAAAAA",
      "previousPriority": null,
      "errorMessage": "Case 5003000000AAAAAAAA was not found or is not visible to you."
    }
  }
]
```

**Why it works:** Three defects show up in this one response and in no other cheap test.

| Symptom in the response | What it means |
|---|---|
| One entry returned for two inputs | The result list is built on the success path only — breaks "the Inputs and Outputs must match on both the size and the order" (apexdev L5456–5457) |
| Two entries, both `success: true` | The failure was swallowed rather than reported per input |
| `isSuccess: false` with a stack trace instead of two entries | The action threw. In a flow this takes the whole batch of interviews down the `faultConnector` path (api_meta L68479), not just the bad input |

Note the ceiling on this test: "When invoking an Apex action using the POST method and supplying the
inputs in the request, only the following primitive types are supported as inputs" — `Blob, Boolean,
Date, Datetime, Decimal, Double, ID, Integer, Long, String, Time` (api_rest L13767–13779). A wrapper
carrying an sObject or a collection field cannot be exercised this way; that contract needs the
200-input Apex test in `references/code-examples.md` §4.

UNVERIFIED (2026-09-05): the exact JSON envelope key names above (`actionName`, `errors`,
`isSuccess`, `outputValues`) are the shape the invocable-actions REST resource returns, but the
REST API Developer Guide's Apex-action section documents the request body and the resource URI
rather than a field-by-field response schema. Read the real response from your org before asserting
on key names in a CI check.
