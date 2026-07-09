# LLM Anti-Patterns — SOQL Object Limits and Restrictions

Common mistakes AI coding assistants make when generating or advising on SOQL against objects
that carry their own limits. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating an unfiltered ContentDocumentLink / ContentHubItem / Vote query

**What the LLM generates:**

```apex
List<ContentDocumentLink> links =
    [SELECT ContentDocumentId, LinkedEntityId FROM ContentDocumentLink];
```

**Why it happens:** the model treats `ContentDocumentLink` like any other sObject, for which a
filterless `SELECT` is legal. Its training data is dominated by ordinary objects where "select
all" works, so it never adds the mandatory filter.

**Correct pattern:**

```apex
[SELECT ContentDocumentId, LinkedEntityId FROM ContentDocumentLink
 WHERE LinkedEntityId IN :recordIds]
```

**Detection hint:** a `FROM ContentDocumentLink` / `ContentHubItem` / `Vote` with no `WHERE`, or
a `WHERE` that does not reference one of the object's allowed filter fields.

---

## Anti-Pattern 2: Treating a big object like a custom object

**What the LLM generates:**

```apex
[SELECT AccountId__c, Channel__c FROM Interaction__b
 WHERE Channel__c LIKE 'web%' AND Event_Date__c != null]
```

**Why it happens:** big-object query syntax *looks* identical to custom-object SOQL, so the model
reuses the full operator set (`LIKE`, `!=`, arbitrary field filters) it uses everywhere else.

**Correct pattern:**

```apex
// filter index fields in order: = on all but the last, one range op on the last
[SELECT AccountId__c, Event_Date__c FROM Interaction__b
 WHERE AccountId__c = :acctId AND Event_Date__c >= :cutoff]
```

**Detection hint:** a query on a `__b` object using `LIKE`, `!=`, `NOT IN`, `EXCLUDES`,
`INCLUDES`, a non-index field, or a range operator on anything but the last filtered field.

---

## Anti-Pattern 3: Assuming Attachment just paginates past 100,000

**What the LLM generates:** advice to "page through with `LIMIT` and `OFFSET`" or a claim that
the query returns the first 100,000 rows, when the query actually fails outright past the cap.

**Why it happens:** the model generalizes the standard `LIMIT`/`OFFSET` paging idiom to every
object and assumes large result sets degrade gracefully rather than erroring.

**Correct pattern:** state that `Attachment` **fails** past 100,000 records, that `OFFSET` does
not help, and that the fix is a bounded `WHERE` + `LIMIT` under the ceiling or migrating to
`ContentVersion` / `ContentDocument`.

**Detection hint:** any suggestion to use `OFFSET` on `Attachment`, or wording that implies the
query truncates rather than fails.

---

## Anti-Pattern 4: Recommending View All Data (or system mode) as the fix

**What the LLM generates:** "Grant the user View All Data" or "run this in `without sharing` /
system mode" as the remedy for a failing `Attachment`, `TopicAssignment`, `NewsFeed`, or
`UserProfileFeed` query.

**Why it happens:** the docs literally say the limit lifts with View All Data, so the model
surfaces that as the answer without weighing the security blast radius.

**Correct pattern:** scope the query — add the required `LIMIT`, bound the `WHERE`, or migrate the
object — and explicitly flag that View All Data bypasses sharing for the entire transaction, not
just the object that was failing.

**Detection hint:** any remediation that grants a permission or switches sharing mode to make a
per-object limit disappear, rather than constraining the query.

---

## Anti-Pattern 5: Using an inline bind variable on KnowledgeArticleVersion

**What the LLM generates:**

```apex
[SELECT Id, Title FROM KnowledgeArticleVersion WHERE Title LIKE :term]
```

**Why it happens:** inline bind variables (`:term`) are the normal, safe way to parameterize
Apex SOQL, so the model applies the idiom uniformly and never learns the object-specific
exception.

**Correct pattern:**

```apex
Database.queryWithBinds(
    'SELECT Id, Title FROM KnowledgeArticleVersion WHERE Title LIKE :searchTerm',
    new Map<String, Object>{ 'searchTerm' => term },
    AccessLevel.USER_MODE);
```

**Detection hint:** a static/inline `[SELECT ... FROM KnowledgeArticleVersion ... :var ...]` with
a bind variable, instead of `Database.query` / `Database.queryWithBinds`.

---

## Anti-Pattern 6: Conflating per-object limits with the generic governor limits

**What the LLM generates:** attributing a per-object failure to "the 50,000-row SOQL governor
limit," or inventing a single unified "SOQL limit" number that does not match any object's actual
rule.

**Why it happens:** the well-known 50,000-rows / 100-queries governor limits dominate training
data, so the model reaches for them to explain any query failure — even one caused by a distinct
per-object restriction.

**Correct pattern:** name the specific per-object rule (Attachment 100,000; UserRecordAccess 200;
`TopicAssignment` `LIMIT` 1,100; big-object index filtering; external-object 4-join / 1,000-row
subquery cap) and note these sit *on top of* the generic governor limits, not instead of them.

**Detection hint:** an explanation that cites "50,000 rows" or "100 queries" for a failure on
`Attachment`, a big object, an external object, or a feed object.
