# LLM Anti-Patterns — Record Merge Implications

## Anti-Pattern 1: Calling Database.merge() Without Copying Fields First

**What the LLM generates:** Apex code that calls `Database.merge(masterRecord, losingRecordIds)` directly without first reading and copying field values from the losing records.

**Why it happens:** LLMs model `Database.merge()` as a complete merge operation, similar to the UI merge, without knowing that Apex merge only preserves the master record's existing field values.

**Correct pattern:**
```apex
// WRONG: direct merge without field copy
Database.merge(masterAccount, losingAccountIds);

// CORRECT: copy needed fields first
Account losingAccount = [SELECT Custom_Field__c FROM Account WHERE Id = :losingId LIMIT 1];
if (losingAccount.Custom_Field__c != null && masterAccount.Custom_Field__c == null) {
    masterAccount.Custom_Field__c = losingAccount.Custom_Field__c;
    update masterAccount;
}
Database.merge(masterAccount, losingId);
```

**Detection hint:** Any Apex merge code that does not have an `update masterRecord` call before the `Database.merge()` call when custom fields may differ.

---

## Anti-Pattern 2: Including Converted Leads in a Lead Merge Batch

**What the LLM generates:** A SOQL query for Lead merge candidates without a `IsConverted = false` filter.

**Why it happens:** LLMs do not know that converted Leads are excluded from merge operations and generate generic Lead queries without this filter.

**Correct pattern:**
```apex
// WRONG: no converted filter
List<Lead> duplicates = [SELECT Id FROM Lead WHERE Email = :email];

// CORRECT: exclude converted leads
List<Lead> duplicates = [SELECT Id FROM Lead WHERE Email = :email AND IsConverted = false];
```

**Detection hint:** Any Lead merge query missing `AND IsConverted = false`.

---

## Anti-Pattern 3: Assuming OwnerId Can Be Selected From a Losing Record in the UI Merge

**What the LLM generates:** Instructions telling the user to "select the correct Owner from the merge screen" to preserve the losing record's owner.

**Why it happens:** LLMs describe the UI merge field selection screen as if all fields are selectable, without knowing that `OwnerId` is always taken from the master record.

**Correct pattern:** OwnerId is non-selectable in the merge UI. To set the correct owner on the merged record, update the master record's Owner before initiating the merge, not during the merge screen. Document this limitation when advising on merge procedures.

**Detection hint:** Any instruction that says "select the owner from the merge screen" or "choose the losing record's owner during merge."

---

## Anti-Pattern 4: Recommending a Merge Undo or Rollback Step

**What the LLM generates:** A suggestion to "undo the merge" or "restore the original records" after a mistaken merge using a standard Salesforce feature.

**Why it happens:** LLMs apply general "undo" patterns without knowing that Salesforce merges are permanent and irreversible through standard features.

**Correct pattern:** There is no native undo for a record merge in Salesforce. Recovery requires either a full org restore from a sandbox backup, manual recreation of the deleted records from exported data, or (for contacts) using Data Loader to re-insert records with the old data. Always advise pre-merge data export as a mandatory step before any bulk merge operation.

**Detection hint:** Any recommendation to "undo," "reverse," or "rollback" a Salesforce merge.

---

## Anti-Pattern 5: Assuming Child Records Are Always Preserved After Merge

**What the LLM generates:** A statement that "all child records from the losing record are moved to the master record" without qualifying exceptions.

**Why it happens:** The general re-parenting behavior is correct for most objects, but LLMs miss the exceptions: Campaign Members are deduplicated (one per Campaign per Contact/Lead), and some system objects may behave differently.

**Correct pattern:** Most child records (Opportunities, Cases, Activities, Notes) are re-parented to the master record. However, duplicate Campaign Members on the same Campaign are deduplicated — one is kept, one is deleted, and the deleted one's response data is lost. Always verify Campaign Member counts before and after merging Contacts with Campaign history. Include explicit Campaign Member verification in any merge checklist.

**Detection hint:** Any claim that "all child records" are preserved without noting the Campaign Member deduplication exception.
