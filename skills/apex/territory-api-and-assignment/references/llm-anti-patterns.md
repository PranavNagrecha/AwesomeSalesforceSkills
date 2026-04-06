# LLM Anti-Patterns — Territory API and Assignment

Common mistakes AI coding assistants make when generating or advising on Territory API and Assignment.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Writing an Apex Trigger on ObjectTerritory2Association

**What the LLM generates:** A trigger declaration like `trigger OTATrigger on ObjectTerritory2Association (after insert, after delete)` with business logic inside it, presented as a valid way to react to territory-account association changes.

**Why it happens:** LLMs generalize from the pattern "trigger on SObject fires on DML" which is true for most objects. The platform exception for `ObjectTerritory2Association` (triggers never fire on it) is not well-represented in training data, so the LLM applies the general rule incorrectly.

**Correct pattern:**

```apex
// WRONG — this trigger deploys but never fires
trigger OTATrigger on ObjectTerritory2Association (after insert) {
    // This code never executes
}

// CORRECT — dispatch a Platform Event from the service that does the DML
List<ObjectTerritory2Association> toInsert = buildAssociations(...);
Database.insert(toInsert, false);
List<Territory_Account_Assigned__e> events = new List<Territory_Account_Assigned__e>();
for (ObjectTerritory2Association ota : toInsert) {
    events.add(new Territory_Account_Assigned__e(
        Account_Id__c   = ota.ObjectId,
        Territory_Id__c = ota.Territory2Id
    ));
}
EventBus.publish(events);
```

**Detection hint:** Grep for `trigger\s+\w+\s+on\s+ObjectTerritory2Association` — any such trigger is a no-op and should be flagged.

---

## Anti-Pattern 2: Calling UserInfo.getSessionId() for SOAP Callout Inside Batch or Queueable

**What the LLM generates:** A Batch Apex class or Queueable that calls `UserInfo.getSessionId()` inside `execute()` to build an Authorization header for a SOAP callout to trigger ETM rule evaluation.

**Why it happens:** LLMs know that `UserInfo.getSessionId()` is how Apex obtains a session token for SOAP callouts. They are not trained to distinguish that this method returns `null` in asynchronous contexts, because the failure is silent (a null string, not an exception at the call site).

**Correct pattern:**

```apex
// WRONG — getSessionId() returns null in async context
global void execute(Database.BatchableContext bc, List<Account> scope) {
    String sessionId = UserInfo.getSessionId(); // Returns null — callout will fail
    callSoapRuleEvaluation(sessionId, accountIds); // Silent failure or CalloutException
}

// CORRECT — defer rule evaluation to a synchronous context via Platform Event
global void finish(Database.BatchableContext bc) {
    EventBus.publish(new Territory_Rules_Eval_Needed__e(Account_Ids__c = idsJson));
}
// Subscriber trigger runs in a synchronous context where getSessionId() works
```

**Detection hint:** Look for `UserInfo.getSessionId()` inside classes that also implement `Database.Batchable`, `Queueable`, `Schedulable`, or are annotated with `@future`.

---

## Anti-Pattern 3: Using Raw insert Instead of Database.insert(list, false) for Association DML

**What the LLM generates:** `insert associationList;` or `insert new UserTerritory2Association(...)` as a single-record insert in a loop, without `DUPLICATE_VALUE` handling.

**Why it happens:** LLMs default to the simplest DML form. The `DUPLICATE_VALUE` constraint on territory association objects (unique on `Territory2Id + UserId` for `UserTerritory2Association`, and `Territory2Id + ObjectId + AssociationCause` for `ObjectTerritory2Association`) is a runtime constraint not visible in the sObject definition, so LLMs do not anticipate it.

**Correct pattern:**

```apex
// WRONG — rolls back entire transaction on first duplicate
insert userTerritoryAssociations;

// CORRECT — partial success; inspect SaveResult for non-duplicate errors
List<Database.SaveResult> results = Database.insert(userTerritoryAssociations, false);
for (Database.SaveResult sr : results) {
    if (!sr.isSuccess()) {
        for (Database.Error err : sr.getErrors()) {
            if (err.getStatusCode() != StatusCode.DUPLICATE_VALUE) {
                throw new DmlException(err.getMessage());
            }
        }
    }
}
```

**Detection hint:** Grep for `insert\s+\w*(UserTerritory2Association|ObjectTerritory2Association)` without `Database.insert` on the same line or nearby — these are unsafe inserts.

---

## Anti-Pattern 4: Assuming Territory Assignment Rules Fire Automatically on Account Field Updates

**What the LLM generates:** Instructions like "update the Account's BillingState field and the territory assignment will automatically update based on your assignment rules" — without mentioning that explicit rule evaluation must be triggered.

**Why it happens:** LLMs conflate ETM assignment rules with Salesforce validation rules or workflow rules, which do fire automatically on record save. ETM assignment rules require an explicit evaluation request, which is a less common pattern that LLMs generalize away.

**Correct pattern:**

```apex
// WRONG assumption — updating BillingState does NOT re-evaluate territory rules
account.BillingState = 'CA';
update account;
// Territories are still the same as before — no automatic re-evaluation

// CORRECT — update field AND explicitly trigger rule evaluation
update account;
// Then call the SOAP rule evaluation endpoint for this account's ID
// (must be in synchronous context — see Pattern 3 in SKILL.md)
List<Id> idsToEvaluate = new List<Id>{ account.Id };
TerritoryRuleEvalService.evaluateRules(idsToEvaluate);
```

**Detection hint:** Look for explanations or comments that claim "territory rules will fire automatically" or "the platform will reassign" without a corresponding SOAP callout or Setup UI step.

---

## Anti-Pattern 5: Setting AssociationCause = 'Territory2RuleAssociation' on a New ObjectTerritory2Association

**What the LLM generates:** Code that queries existing rule-based associations (which have `AssociationCause = 'Territory2RuleAssociation'`), clones the records, and re-inserts them — for example, to copy associations from one territory model to another during a migration.

**Why it happens:** LLMs clone queried sObjects by copying all fields, including `AssociationCause`. They are not trained on the constraint that `Territory2RuleAssociation` is a read-only, platform-controlled value that cannot be written via DML.

**Correct pattern:**

```apex
// WRONG — copying AssociationCause = 'Territory2RuleAssociation' throws FIELD_INTEGRITY_EXCEPTION
List<ObjectTerritory2Association> toMigrate = [
    SELECT ObjectId, Territory2Id, AssociationCause FROM ObjectTerritory2Association
    WHERE Territory2Id IN :oldTerritoryIds
];
Database.insert(toMigrate, false); // Throws FIELD_INTEGRITY_EXCEPTION for rule-based rows

// CORRECT — always use 'Territory' for API-managed inserts
List<ObjectTerritory2Association> toInsert = new List<ObjectTerritory2Association>();
for (ObjectTerritory2Association src : toMigrate) {
    toInsert.add(new ObjectTerritory2Association(
        ObjectId         = src.ObjectId,
        Territory2Id     = newTerritoryIdMap.get(src.Territory2Id),
        AssociationCause = 'Territory'  // Always set explicitly; never copy from source
    ));
}
Database.insert(toInsert, false);
```

**Detection hint:** Grep for `AssociationCause.*Territory2RuleAssociation` in DML contexts — any insert with this value will throw at runtime.

---

## Anti-Pattern 6: Making More Than 200 Account IDs in a Single SOAP Rule Evaluation Request

**What the LLM generates:** A loop that collects all Account IDs and passes the entire list to a single SOAP rule evaluation callout, without chunking.

**Why it happens:** LLMs are familiar with the general pattern of "collect all IDs, pass them in one call" which works for most Salesforce APIs. The 200-record limit on the ETM SOAP rule evaluation endpoint is a domain-specific constraint not generalized across APIs.

**Correct pattern:**

```apex
// WRONG — passes all IDs at once; SOAP fault if > 200
evaluateRules(allAccountIds); // Fails for large lists

// CORRECT — chunk into batches of 200
Integer batchSize = 200;
for (Integer i = 0; i < allAccountIds.size(); i += batchSize) {
    List<Id> chunk = allAccountIds.subList(i, Math.min(i + batchSize, allAccountIds.size()));
    evaluateRules(chunk);
}
```

**Detection hint:** Look for SOAP rule evaluation callout code that does not contain chunking logic (`subList` with size 200 or a `Math.min` guard). Any call that passes a list directly without chunking should be flagged.
