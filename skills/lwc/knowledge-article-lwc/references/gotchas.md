# Gotchas — Knowledge Article LWC

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: No Dedicated Wire Adapter for Knowledge Article Content

**What happens:** Developers search the LWC wire adapter reference for a dedicated Knowledge adapter (similar to `getRecord` or `getRelatedListRecords`) and find none. Attempts to wire a component directly to a Knowledge article's body content without custom Apex silently fail or return only a subset of fields because `getRecord` cannot query article body fields that are not surfaced through the standard field API.

**When it occurs:** Any time a developer tries to fetch article body content (rich text fields specific to the article type) using only `lightning/uiRecordApi` without an Apex controller. The `getRecord` wire adapter can return standard Knowledge fields like `Title` and `Summary` but does not reliably surface custom body fields on all article types.

**How to avoid:** Always back Knowledge body content retrieval with a custom `@AuraEnabled(cacheable=true)` Apex method. Reserve `@wire(getRecord)` for standard metadata fields (Title, Summary, LastPublishedDate) on detail pages where the record ID is already known. Document this constraint in code comments so future maintainers do not attempt to remove the Apex layer.

---

## Gotcha 2: Guest User Silently Receives Zero Results Due to Missing Data Category Visibility

**What happens:** A Knowledge search or list LWC works correctly for authenticated users and in Experience Builder admin preview, but returns an empty result set for actual guest (unauthenticated) site visitors. No error is thrown; the list simply renders empty.

**When it occurs:** Whenever a SOQL or SOSL query against `Knowledge__kav` is executed in the Guest User's security context and the Guest User profile has not been granted data category visibility for the categories the articles are filed under. This is configured separately from standard object permissions and is invisible to normal permission set audits.

**How to avoid:** In Experience Workspaces, navigate to Administration > Guest User > Data Category Visibility (or in Setup under Channels > Data Category Visibility for the site's guest user). Grant access to all category groups that contain articles the guest should see. After configuring, test by opening the site in an incognito browser window — not in admin preview mode. Admin preview sessions bypass guest sharing rules and category visibility, making the problem invisible during development.

---

## Gotcha 3: KnowledgeArticleId vs. Knowledge__kav Record Id for Voting

**What happens:** Developers pass the `Knowledge__kav` version record ID (the 18-character ID returned by SOQL) directly to `KbManagement.PublishingService.rateKnowledgeArticle`. The method accepts the call but silently no-ops or throws a `KbManagement.KbServiceException` depending on the API version, because it expects the master article ID stored in the `KnowledgeArticleId` field, not the version record's `Id`.

**When it occurs:** Any time a voting method is implemented using the version record ID pulled from the LWC's `@api recordId` or from a search result list without explicitly querying the `KnowledgeArticleId` field.

**How to avoid:** Always query the `KnowledgeArticleId` field explicitly and pass that value to the platform voting service:

```apex
Knowledge__kav kav = [
    SELECT KnowledgeArticleId
    FROM Knowledge__kav
    WHERE Id = :versionRecordId
    AND PublishStatus = 'Online'
    LIMIT 1
];
KbManagement.PublishingService.rateKnowledgeArticle(
    kav.KnowledgeArticleId, rating, UserInfo.getUserId()
);
```

Note: `KnowledgeArticleId` is the 15/18-character master article identifier that persists across published versions.

---

## Gotcha 4: WITH DATA CATEGORY Clause Incompatible with Aggregate SOQL

**What happens:** A SOQL query that combines `WITH DATA CATEGORY` with aggregate functions (`COUNT`, `SUM`, `GROUP BY`) throws a compile-time error: `"Grouped queries not supported with Data Category filter"`. This prevents building data category-scoped article count queries in a single SOQL statement.

**When it occurs:** When a component needs to display article counts per category or paginate with a total count. Developers often write:

```apex
// FAILS — cannot combine WITH DATA CATEGORY and COUNT()
SELECT COUNT(Id) FROM Knowledge__kav
WHERE PublishStatus = 'Online'
WITH DATA CATEGORY Products__c AT 'Laptops'
```

**How to avoid:** Retrieve the full list of matching article IDs in one SOQL call (without aggregation) and perform counting in Apex. Alternatively, retrieve count and data separately using two queries: one with `WITH DATA CATEGORY` for the filtered list, and a count computed on the returned collection in Apex rather than in SOQL.

---

## Gotcha 5: Cacheable Apex Cannot Be Used for Voting

**What happens:** A developer annotates the voting method with `@AuraEnabled(cacheable=true)` to avoid a second Apex method, or wires the voting call. The platform throws a runtime exception because `KbManagement.PublishingService.rateKnowledgeArticle` is a DML-equivalent operation and cannot be executed inside a `cacheable=true` method.

**When it occurs:** When a developer consolidates retrieval and mutation logic into a single Apex method for simplicity, or when they attempt to wire the vote action to a reactive property.

**How to avoid:** Keep retrieval and voting in strictly separate Apex methods. Retrieval methods use `@AuraEnabled(cacheable=true)` and are called via `@wire` or imperatively. Voting methods use `@AuraEnabled` (no `cacheable`) and are called imperatively from user interaction event handlers only:

```apex
// Retrieval — cacheable
@AuraEnabled(cacheable=true)
public static Knowledge__kav getArticle(Id articleId) { ... }

// Voting — NOT cacheable, DML equivalent
@AuraEnabled
public static void voteOnArticle(Id articleId, Integer rating) { ... }
```
