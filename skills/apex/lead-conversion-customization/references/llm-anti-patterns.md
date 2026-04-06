# LLM Anti-Patterns — Lead Conversion Customization

Common mistakes AI coding assistants make when generating or advising on Lead Conversion Customization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Instantiating LeadConvertResult in Test Code

**What the LLM generates:**

```apex
Database.LeadConvertResult mockResult = new Database.LeadConvertResult();
mockResult.success = true;
```

**Why it happens:** LLMs pattern-match against other result classes that do have constructors (e.g., `Database.SaveResult` is sometimes faked in older examples). They extrapolate that all Database result types are constructable.

**Correct pattern:**

```apex
// Call convertLead in test and use the real returned result
List<Database.LeadConvert> lcList = new List<Database.LeadConvert>{ lc };
List<Database.LeadConvertResult> results = Database.convertLead(lcList);
System.assert(results[0].isSuccess());
// OR, for mocking: deserialize from JSON
Database.LeadConvertResult mockResult = (Database.LeadConvertResult)
    JSON.deserialize('{"success":true,"leadId":"' + lid + '"}',
    Database.LeadConvertResult.class);
```

**Detection hint:** Any line matching `new Database.LeadConvertResult(` is always wrong and will not compile.

---

## Anti-Pattern 2: Reading ConvertedContactId in before update

**What the LLM generates:**

```apex
trigger LeadTrigger on Lead (before update) {
    for (Lead l : Trigger.new) {
        if (l.IsConverted) {
            Contact c = new Contact(Id = l.ConvertedContactId, ...);
            update c; // ConvertedContactId is null here — this silently does nothing
        }
    }
}
```

**Why it happens:** LLMs conflate `before update` and `after update` trigger contexts. They know `IsConverted` flips during conversion and assume all Lead fields including the converted-record Ids are immediately available.

**Correct pattern:**

```apex
trigger LeadTrigger on Lead (after update) {
    List<Id> justConverted = new List<Id>();
    for (Lead l : Trigger.new) {
        if (l.IsConverted && !Trigger.oldMap.get(l.Id).IsConverted) {
            justConverted.add(l.Id);
        }
    }
    if (!justConverted.isEmpty()) {
        // Re-query to get ConvertedContactId and custom fields
        for (Lead l : [SELECT Id, ConvertedContactId, Custom__c FROM Lead WHERE Id IN :justConverted]) {
            // ConvertedContactId is populated here
        }
    }
}
```

**Detection hint:** Any trigger on Lead using `before update` that references `ConvertedContactId`, `ConvertedAccountId`, or `ConvertedOpportunityId` is wrong.

---

## Anti-Pattern 3: Hardcoding the Converted Status String

**What the LLM generates:**

```apex
lc.setConvertedStatus('Converted');
```

**Why it happens:** Training data contains many examples using `'Converted'` as the status label because it is the Salesforce default. LLMs cargo-cult this without noting it may not match the org's actual API name or that orgs may have renamed or added additional converted statuses.

**Correct pattern:**

```apex
String convertedStatus = [
    SELECT MasterLabel FROM LeadStatus
    WHERE IsConverted = true
    LIMIT 1
].MasterLabel;
lc.setConvertedStatus(convertedStatus);
```

**Detection hint:** Any `setConvertedStatus('...')` call with a hardcoded string literal should be flagged for review.

---

## Anti-Pattern 4: Calling convertLead() Once Per Lead Inside a Loop

**What the LLM generates:**

```apex
for (Lead l : leads) {
    Database.LeadConvert lc = new Database.LeadConvert();
    lc.setLeadId(l.Id);
    lc.setConvertedStatus(convertedStatus);
    Database.convertLead(new List<Database.LeadConvert>{ lc }); // DML in loop
}
```

**Why it happens:** LLMs default to per-record iteration patterns when they are not confident about the bulk API. They treat `convertLead()` like `update record` inside a loop — a well-known mistake for normal DML that LLMs still frequently reproduce.

**Correct pattern:**

```apex
List<Database.LeadConvert> conversions = new List<Database.LeadConvert>();
for (Lead l : leads) {
    Database.LeadConvert lc = new Database.LeadConvert();
    lc.setLeadId(l.Id);
    lc.setConvertedStatus(convertedStatus);
    conversions.add(lc);
}
// Single call (or chunked at 100)
List<Database.LeadConvertResult> results = Database.convertLead(conversions);
```

**Detection hint:** Any `Database.convertLead(` call inside a `for` loop is wrong.

---

## Anti-Pattern 5: Assuming Custom Fields Are Transferred Automatically

**What the LLM generates:**

"When you convert a Lead, all custom fields are automatically mapped to the corresponding fields on the Contact and Account. You do not need to write any Apex for field transfer."

**Why it happens:** LLMs trained on general Salesforce documentation often conflate the existence of the field-mapping UI feature with it being complete and automatic. They do not distinguish between "a mapping feature exists" and "all fields are mapped by default."

**Correct pattern:**

Only fields with mappings configured in Setup (Object Manager > Lead > Map Lead Fields) are transferred. All unmapped custom fields must be transferred via post-conversion Apex. After `convertLead()` returns, query the source Lead records for unmapped fields and DML-update the resulting Contact, Account, or Opportunity records.

**Detection hint:** Any generated response saying custom fields "automatically" transfer without qualification is misleading. Look for missing post-conversion DML when custom fields are in scope.

---

## Anti-Pattern 6: Omitting the Batch Limit Guard

**What the LLM generates:**

```apex
// "Bulkified" conversion — passes the whole list without chunking
List<Database.LeadConvertResult> results = Database.convertLead(allConversions);
```

**Why it happens:** LLMs know that Salesforce DML is bulk-safe and pattern-match `convertLead()` to standard `insert`/`update` which have no explicit record count limits. They do not know about the 100-record hard limit on `convertLead()`.

**Correct pattern:**

```apex
List<Database.LeadConvertResult> allResults = new List<Database.LeadConvertResult>();
for (Integer i = 0; i < allConversions.size(); i += 100) {
    List<Database.LeadConvert> chunk = allConversions.subList(i,
        Math.min(i + 100, allConversions.size()));
    allResults.addAll(Database.convertLead(chunk));
}
```

**Detection hint:** Any `Database.convertLead(list)` call where the list is not demonstrably capped at 100 should be flagged if volume is uncertain.
