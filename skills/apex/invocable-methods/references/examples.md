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

**Why it works:** Flow builders get labeled inputs and outputs, while the service layer stays reusable.

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

**Why it works:** The action gathers IDs, queries once, and updates in bulk while still returning per-request results.

---

## Anti-Pattern: Single Primitive Input With Hidden Single-Record Assumption

**What practitioners do:** They write an invocable that handles one record only because that is how the first Flow uses it.

**What goes wrong:** Later bulk invocations hit SOQL-in-loop or DML-in-loop patterns and the contract becomes hard to extend.

**Correct approach:** Treat invocable methods as list-oriented from the start.
