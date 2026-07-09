# Examples — SOSL WITH Clauses

All queries below are authored from the official SOQL and SOSL Reference. Replace object
names, field names, category groups, and network IDs with your own. Clause order is fixed:
`DivisionFilter → DATA CATEGORY → SNIPPET → NETWORK → PricebookId → METADATA → HIGHLIGHT →
SPELL_CORRECTION`, then `LIMIT`, then `UPDATE`.

## Example 1: Knowledge help-center search (DATA CATEGORY + SNIPPET + HIGHLIGHT)

**Context:** a support agent searches published Knowledge articles under one product data
category and wants a short excerpt plus the matched terms emphasized in the result list.

**Problem:** a plain SOSL returns article IDs and titles with no way to preview the matching
passage or show *why* an article matched — the console has to re-derive that itself.

**Solution:**

```sql
FIND {payment failed}
  IN ALL FIELDS
  RETURNING KnowledgeArticleVersion (
    Id, Title, UrlName
    WHERE PublishStatus = 'online' AND Language = 'en_US'
  )
  WITH DATA CATEGORY Product__c AT Billing__c
  WITH SNIPPET (target_length=200)
  WITH HIGHLIGHT
```

Issued from Apex via a static SOSL, wrapped so the calling class runs with the user's access:

```apex
public with sharing class ArticleSearch {
    public static List<List<SObject>> run(String term) {
        // term is bound as a SOSL variable; do NOT string-concatenate user input.
        return [
            FIND :term IN ALL FIELDS
            RETURNING KnowledgeArticleVersion (
                Id, Title, UrlName
                WHERE PublishStatus = 'online' AND Language = 'en_US'
            )
            WITH DATA CATEGORY Product__c AT Billing__c
            WITH SNIPPET (target_length=200)
            WITH HIGHLIGHT
        ];
    }
}
```

**Why it works:** `DATA CATEGORY` requires both a `RETURNING` clause and a `WHERE PublishStatus`
filter — both are present. `SNIPPET (target_length=200)` sits inside the 50–1,000 range, and
`HIGHLIGHT` returns `<mark>`-delimited terms on the article's text fields. The three clauses are
in canonical order. Because `KnowledgeArticleVersion` supports all three, nothing is silently
dropped. (Injection-safe binding is covered in `data/sosl-search-patterns`.)

---

## Example 2: Experience Cloud site-scoped search (WITH NETWORK)

**Context:** a community search page must return only the users and feed posts that belong to
one Experience Cloud site, never org-wide or cross-site content.

**Problem:** an unscoped SOSL pulls users and feed items from every site plus internal data;
filtering them in Apex afterward risks leaking one site's posts into another.

**Solution:**

```sql
FIND {onboarding}
  RETURNING
    User (Id, Name),
    FeedItem (Id, ParentId WHERE CreatedDate = THIS_YEAR ORDER BY CreatedDate DESC)
  WITH NETWORK IN ('0DB5g000000TN1AGAW', '0DB5g000000TN1BGAW')
```

For an internal-org (non-site) search, use the reserved all-zero network ID:

```sql
FIND {onboarding} RETURNING User (Id, Name) WITH NETWORK = '000000000000000'
```

**Why it works:** `WITH NETWORK` scopes `User` and feed results to the listed site(s). Note the
documented limit: **for objects other than users and feeds the filter is ignored**, and you
**can't run scoped and unscoped searches in the same query** — so don't add an unfiltered object
alongside the scoped ones and expect it to be site-limited.

---

## Example 3: Product search in one price book + response metadata (PricebookId + METADATA)

**Context:** a quoting tool searches `Product2` but should only surface products on the active
price book, and the client also needs the response's label metadata.

**Problem:** without `PricebookId` the search returns every matching product regardless of price
book; without `METADATA` the response omits the label information the UI wants to render.

**Solution:**

```sql
FIND {laptop}
  RETURNING Product2 (Id, Name, ProductCode)
  WITH PricebookId
  WITH METADATA = 'LABELS'
```

**Why it works:** `PricebookId` is `Product2`-only and restricts the hits to a single price book;
`METADATA` is required for any metadata (such as labels) to appear in the response — nothing is
returned by default. `PricebookId` precedes `METADATA`, which matches the fixed order.

---

## Example 4: Exact-match search with spell correction disabled (SPELL_CORRECTION)

**Context:** a part-number lookup where auto-correcting the term (e.g. `SN-1000` → a "closest"
word) produces wrong hits.

**Solution:**

```sql
FIND {San Francisco} IN ALL FIELDS RETURNING Account WITH SPELL_CORRECTION = false
```

**Why it works:** `SPELL_CORRECTION` defaults to `true`, so you must explicitly set `false` to
suppress correction. It requires API version 40.0 or later and only affects searches that
support spell correction. It is the last WITH clause in the canonical order.

---

## Anti-Pattern: WITH clauses in the wrong order

**What practitioners do:** order the clauses by "importance" or the order they thought of them —
for example putting `HIGHLIGHT` before `DATA CATEGORY`:

```sql
-- INVALID: HIGHLIGHT before DATA CATEGORY breaks the fixed order
FIND {refund} RETURNING KnowledgeArticleVersion (Id WHERE PublishStatus='online')
  WITH HIGHLIGHT
  WITH DATA CATEGORY Product__c AT Billing__c
```

**What goes wrong:** SOSL rejects the query outright — each clause is valid on its own, but the
sequence violates the single fixed order, so the whole statement fails to parse.

**Correct approach:** keep the canonical sequence — `DATA CATEGORY` comes before `HIGHLIGHT`:

```sql
FIND {refund} RETURNING KnowledgeArticleVersion (Id WHERE PublishStatus='online')
  WITH DATA CATEGORY Product__c AT Billing__c
  WITH HIGHLIGHT
```
