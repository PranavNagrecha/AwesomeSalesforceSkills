# LLM Anti-Patterns — Knowledge Article LWC

Common mistakes AI coding assistants make when generating or advising on Knowledge Article LWC components. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inventing a Dedicated Knowledge Wire Adapter

**What the LLM generates:** Code that attempts to use a nonexistent `@wire` adapter such as `getKnowledgeArticle` or `getKnowledgeArticles` from `lightning/knowledgeApi` or a similar invented module:

```javascript
// WRONG — this module does not exist
import { getKnowledgeArticles } from 'lightning/knowledgeApi';

@wire(getKnowledgeArticles, { searchTerm: '$searchTerm' })
articles;
```

**Why it happens:** LLMs trained on Salesforce documentation and community posts often pattern-match from other wire adapters (e.g., `getRelatedListRecords`, `getContentDocumentBody`) and hallucinate an equivalent for Knowledge. There is a `lightning/knowledgeManagementApi` import in older Aura documentation but no equivalent LWC wire adapter for article content retrieval.

**Correct pattern:**

```javascript
// CORRECT — custom Apex method wired or called imperatively
import searchArticles from '@salesforce/apex/KnowledgeSearchController.searchArticles';

@wire(searchArticles, { searchTerm: '$searchTerm' })
wiredArticles({ data, error }) {
    if (data) { this.articles = data; }
    if (error) { this.error = error; }
}
```

**Detection hint:** Any import path containing `knowledge` or `knowledgeApi` outside of `@salesforce/apex` is almost certainly hallucinated. Flag any line matching `from 'lightning/knowledge`.

---

## Anti-Pattern 2: DML on KnowledgeArticleVoteStat for Voting

**What the LLM generates:** An Apex method that attempts to insert or upsert records into `KnowledgeArticleVoteStat` to record a user vote:

```apex
// WRONG — KnowledgeArticleVoteStat is a read-only aggregate; DML fails
KnowledgeArticleVoteStat stat = new KnowledgeArticleVoteStat();
stat.ParentId = articleId;
stat.Rating = 5;
insert stat; // throws System.DmlException at runtime
```

**Why it happens:** LLMs see `KnowledgeArticleVoteStat` in the schema and assume it is writable like other sObject records. The object exposes a `Rating` field, reinforcing the assumption that votes can be written via DML.

**Correct pattern:**

```apex
// CORRECT — use the platform publishing service method
KbManagement.PublishingService.rateKnowledgeArticle(
    kav.KnowledgeArticleId, rating, UserInfo.getUserId()
);
```

**Detection hint:** Any `insert`, `update`, or `upsert` statement whose sObject variable resolves to `KnowledgeArticleVoteStat` is incorrect. Flag lines matching `KnowledgeArticleVoteStat` combined with `insert|upsert|update`.

---

## Anti-Pattern 3: Using innerHTML to Render Article Body

**What the LLM generates:** JavaScript that sets the rich text body field value directly on a DOM element's `innerHTML` property inside `renderedCallback`:

```javascript
// WRONG — XSS risk; also violates Locker Service
renderedCallback() {
    const el = this.template.querySelector('.body');
    if (el && this.articleBody) {
        el.innerHTML = this.articleBody;
    }
}
```

**Why it happens:** LLMs often generate vanilla JavaScript patterns for rendering HTML strings. The `lightning-formatted-rich-text` component is less prominent in generic LWC training examples, so the model defaults to the familiar `innerHTML` assignment pattern.

**Correct pattern:**

```html
<!-- CORRECT — safe platform component for rich text rendering -->
<lightning-formatted-rich-text value={body}></lightning-formatted-rich-text>
```

**Detection hint:** Any occurrence of `.innerHTML` assigned from a Knowledge body field is incorrect. Flag `innerHTML` in any LWC component that handles Knowledge data.

---

## Anti-Pattern 4: Assuming Admin Experience Builder Preview Validates Guest Access

**What the LLM generates:** Test instructions that say to "preview the site in Experience Builder" or "test as admin" to verify that guest users can see articles:

```
// WRONG test guidance
"Preview the site in Experience Builder to confirm articles appear for guest users."
```

**Why it happens:** LLMs know that Experience Builder has a preview mode and correctly recommend using it for general UI testing. They do not always model the distinction between admin preview security context and actual guest user security context.

**Correct pattern:**

```
// CORRECT test guidance
Open an incognito browser window and navigate directly to the Experience Cloud site URL
(not via Experience Builder). This replicates the actual guest user security context,
including data category visibility and OWD sharing rules that admin preview bypasses.
```

**Detection hint:** Any test instruction that says "preview in Experience Builder" as a substitute for guest access verification should be flagged and supplemented with incognito browser testing instructions.

---

## Anti-Pattern 5: Missing PublishStatus Filter in Knowledge SOQL

**What the LLM generates:** SOQL queries against `Knowledge__kav` that omit the `PublishStatus = 'Online'` filter:

```apex
// WRONG — returns draft, archived, and online versions
List<Knowledge__kav> articles = [
    SELECT Id, Title, Summary
    FROM Knowledge__kav
    WHERE IsVisibleInPkb = true
];
```

**Why it happens:** LLMs trained on generic SOQL patterns do not always know that `Knowledge__kav` stores multiple version states (draft, online, archived) for each article. The absence of a status filter returns unexpected records including unpublished drafts and archived versions.

**Correct pattern:**

```apex
// CORRECT — only live published articles
List<Knowledge__kav> articles = [
    SELECT Id, Title, Summary
    FROM Knowledge__kav
    WHERE PublishStatus = 'Online'
    AND IsVisibleInPkb = true
    AND Language = 'en_US'
];
```

**Detection hint:** Any SOQL `SELECT ... FROM Knowledge__kav` statement that does not include `PublishStatus = 'Online'` in the WHERE clause is a likely bug. Flag queries against `Knowledge__kav` that lack a `PublishStatus` filter.

---

## Anti-Pattern 6: Passing Version Record Id Instead of KnowledgeArticleId to rateKnowledgeArticle

**What the LLM generates:** A voting method that passes the `Knowledge__kav` version record `Id` directly to `KbManagement.PublishingService.rateKnowledgeArticle`:

```apex
// WRONG — articleId is the Knowledge__kav version Id, not the master article Id
KbManagement.PublishingService.rateKnowledgeArticle(articleId, rating, userId);
```

**Why it happens:** LLMs retrieve the article record ID from search results or from `@api recordId` and pass it directly without awareness of the distinction between the version record ID and the master `KnowledgeArticleId` field.

**Correct pattern:**

```apex
// CORRECT — query KnowledgeArticleId explicitly, pass master article Id
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

**Detection hint:** Any call to `rateKnowledgeArticle` where the first argument is a variable that was populated directly from a SOQL `Id` field (without a subsequent lookup of `KnowledgeArticleId`) should be reviewed.
