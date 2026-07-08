# Examples — SOQL Object Limits and Restrictions

All code below is illustrative scaffolding authored from the official SOQL and SOSL Reference.
Object names and field names are the documented ones; replace record IDs, filter values, and
selector class names with your own. These are per-object restrictions, distinct from the
generic SOQL governor limits.

## Example 1: ContentDocumentLink mandatory filter

**Context:** you want the files attached to a set of Cases so you can show them in a UI.

**Problem:** `ContentDocumentLink` is invalid without a filter on `Id`, `ContentDocumentId`, or
`LinkedEntityId`. A "give me everything" query throws at runtime — there is no unfiltered mode.

**Solution:**

```apex
// WRONG — no mandatory filter; fails with an implementation-restriction error
List<ContentDocumentLink> bad =
    [SELECT ContentDocumentId, LinkedEntityId FROM ContentDocumentLink];

// RIGHT — filter on LinkedEntityId (the records the files are attached to)
Set<Id> caseIds = new Set<Id>{ /* ... */ };
List<ContentDocumentLink> links = [
    SELECT ContentDocumentId, LinkedEntityId, ShareType, Visibility
    FROM ContentDocumentLink
    WHERE LinkedEntityId IN :caseIds
];
```

**Why it works:** the `WHERE LinkedEntityId IN :caseIds` satisfies the object's mandatory-filter
rule. To go the other direction (which records a file is shared to), filter on
`ContentDocumentId` instead. `ContentHubItem` follows the same pattern on `Id` / `ExternalId` /
`ContentHubRepositoryId`, and `Vote` on `ParentId` / `Parent.Type` / `Id`.

---

## Example 2: Keeping Attachment under the 100,000 ceiling

**Context:** a nightly job scans attachments created for a batch of parent records.

**Problem:** `SELECT ... FROM Attachment` fails once the result set exceeds 100,000 records. The
query does not truncate to the first 100,000 — it errors out, and `OFFSET` cannot page past it.

**Solution:**

```apex
// WRONG — unbounded; explodes the moment the org has > 100,000 attachments in scope
List<Attachment> all = [SELECT Id, ParentId, Name FROM Attachment];

// RIGHT — bound the query to a parent set and cap the result
Set<Id> parentIds = getParentIdsForThisBatch();      // e.g. one chunk of parents
List<Attachment> scoped = [
    SELECT Id, ParentId, Name, BodyLength
    FROM Attachment
    WHERE ParentId IN :parentIds
    LIMIT 50000
];
```

**Why it works:** the `WHERE` shrinks the candidate set below the ceiling and the `LIMIT` is an
explicit guard. For a genuinely large file workload, the durable fix is to move off the legacy
`Attachment` object to `ContentVersion` / `ContentDocument`. Note what the *wrong* fix is:
granting the running user **View All Data** does lift the cap, but it bypasses sharing org-wide
— never reach for it just to make one query compile.

---

## Example 3: UserRecordAccess — the 200-row cap and ORDER BY rule

**Context:** you want to know which of a list of records the current user can edit.

**Problem:** `UserRecordAccess` returns at most **200** records no matter how you filter, and
selecting `HasAccess` without `ORDER BY HasAccess` is invalid.

**Solution:**

```apex
// RIGHT — batch IDs into chunks of <= 200 and order by HasAccess
List<Id> recordIds = getCandidateIds();
List<UserRecordAccess> access = [
    SELECT RecordId, HasEditAccess, HasReadAccess, HasAccess
    FROM UserRecordAccess
    WHERE UserId = :UserInfo.getUserId()
      AND RecordId IN :chunkOf200(recordIds)
    ORDER BY HasAccess
];
```

**Why it works:** the chunking keeps each query within the hard 200-row cap, and `ORDER BY
HasAccess` satisfies the object's ordering requirement. If you have more than 200 candidate
records, you must issue multiple queries — there is no way to raise the ceiling.

---

## Example 4: Big-object index filtering and KnowledgeArticleVersion dynamic SOQL

**Context:** a big object `Interaction__b` has an index of (`AccountId__c`, `Event_Date__c`),
and separately you need to query knowledge articles by a runtime search term.

**Problem:** a big object filters **only** on its index fields, in order, with no gaps and only
`=` on all but the last field. Separately, `KnowledgeArticleVersion` rejects inline Apex bind
variables and must be queried with dynamic SOQL.

**Solution:**

```apex
// RIGHT — big object: leading index field uses =, last field uses a range op
Id acctId = someAccountId;
Datetime cutoff = Datetime.now().addDays(-30);
List<Interaction__b> rows = [
    SELECT AccountId__c, Event_Date__c, Channel__c
    FROM Interaction__b
    WHERE AccountId__c = :acctId          // leading index field, equality
      AND Event_Date__c >= :cutoff        // last field in filter, range operator
];

// WRONG — LIKE / != / gaps in the index are unsupported on big objects
// WHERE Channel__c LIKE 'web%'  ->  rejected

// RIGHT — KnowledgeArticleVersion needs dynamic SOQL, not an inline bind
String term = '%' + String.escapeSingleQuotes(userInput) + '%';
String soql =
    'SELECT Id, Title, UrlName FROM KnowledgeArticleVersion ' +
    'WHERE PublishStatus = \'Online\' AND Language = \'en_US\' ' +
    'AND Title LIKE :searchTerm';
List<KnowledgeArticleVersion> articles =
    Database.queryWithBinds(soql, new Map<String, Object>{ 'searchTerm' => term },
                            AccessLevel.USER_MODE);
```

**Why it works:** the big-object filter walks the index in order (`=` then one range operator),
so the platform can resolve it. For `KnowledgeArticleVersion`, moving to `Database.queryWithBinds`
sidesteps the inline-bind restriction while `queryWithBinds` + `String.escapeSingleQuotes` keeps
the dynamic query injection-safe.

---

## Anti-Pattern: "fixing" a per-object limit by widening access

**What practitioners do:** hit a failure on `Attachment` (over 100,000), `TopicAssignment`,
`NewsFeed`, or `UserProfileFeed`, discover the limit lifts with **View All Data**, and either
grant that permission to the running user or move the code into system mode so the query passes.

**What goes wrong:** View All Data is one of the broadest permissions on the platform. Using it
to make a single query compile bypasses sharing for **every** object the transaction reads, not
just the one that was failing — a data-exposure regression that a code review rarely catches
because the query itself now "works."

**Correct approach:** scope the query instead of widening access. Add the required `LIMIT`
(`TopicAssignment` ≤ 1,100; `NewsFeed` / `UserProfileFeed` ≤ 1,000), bound the `Attachment`
`WHERE` and add a `LIMIT`, or migrate the workload to the modern file objects. Keep the query in
a `WITH USER_MODE` selector so it honours the running user's real access.
