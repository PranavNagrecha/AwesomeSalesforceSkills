# Examples — Knowledge Article LWC

## Example 1: SOSL-Backed Knowledge Search Component

**Context:** An Experience Cloud site (authenticated members) needs a search bar that retrieves Knowledge articles matching a user's query. Articles are filed under multiple data categories.

**Problem:** Without a dedicated Knowledge wire adapter, developers either try to use `getRecord` (which requires a known record ID) or call Apex on every keystroke without debouncing, causing excessive server round trips and poor UX.

**Solution:**

Apex controller:

```apex
public with sharing class KnowledgeSearchController {

    @AuraEnabled(cacheable=true)
    public static List<Knowledge__kav> searchArticles(String searchTerm) {
        if (String.isBlank(searchTerm)) {
            return new List<Knowledge__kav>();
        }
        // Sanitize input — SOSL injection risk if concatenated directly
        String escapedTerm = String.escapeSingleQuotes(searchTerm);
        List<List<SObject>> results = [
            FIND :escapedTerm
            IN ALL FIELDS
            RETURNING Knowledge__kav(
                Id, Title, Summary, LastPublishedDate
                WHERE PublishStatus = 'Online'
                AND IsVisibleInPkb = true
                AND Language = 'en_US'
            )
            LIMIT 10
        ];
        return (List<Knowledge__kav>) results[0];
    }
}
```

LWC JavaScript (`knowledgeSearch.js`):

```javascript
import { LightningElement, track } from 'lwc';
import searchArticles from '@salesforce/apex/KnowledgeSearchController.searchArticles';

const DEBOUNCE_MS = 300;

export default class KnowledgeSearch extends LightningElement {
    @track articles = [];
    @track error;
    _debounceTimer;

    handleSearchInput(event) {
        const term = event.target.value;
        clearTimeout(this._debounceTimer);
        this._debounceTimer = setTimeout(() => {
            this.fetchArticles(term);
        }, DEBOUNCE_MS);
    }

    fetchArticles(term) {
        searchArticles({ searchTerm: term })
            .then(data => {
                this.articles = data;
                this.error = undefined;
            })
            .catch(error => {
                this.error = error;
                this.articles = [];
            });
    }
}
```

LWC template (`knowledgeSearch.html`):

```html
<template>
    <lightning-input
        type="search"
        label="Search Articles"
        onchange={handleSearchInput}>
    </lightning-input>

    <template if:true={articles}>
        <ul>
            <template for:each={articles} for:item="article">
                <li key={article.Id}>
                    <a href={article.Id}>{article.Title}</a>
                    <p>{article.Summary}</p>
                </li>
            </template>
        </ul>
    </template>

    <template if:true={error}>
        <p class="slds-text-color_error">Unable to load articles. Please try again.</p>
    </template>
</template>
```

**Why it works:** The Apex method is `cacheable=true`, so repeated searches for the same term are served from the LDS cache. Debouncing limits Apex invocations to one per 300 ms of idle time. The `IsVisibleInPkb = true` filter ensures only Experience Cloud-visible articles are returned. SOSL injection is mitigated by `String.escapeSingleQuotes`.

---

## Example 2: Single Article Detail Page with Voting

**Context:** An Experience Cloud article detail page needs to display the full article body and allow authenticated members to submit a thumbs-up (5-star) or thumbs-down (1-star) rating.

**Problem:** Developers often attempt to render the article body using `innerHTML` directly, which introduces XSS risk for Knowledge articles that contain user-submitted or admin-authored HTML. Voting is also commonly attempted via DML on `KnowledgeArticleVoteStat`, which fails at runtime because the object is read-only.

**Solution:**

Apex controller:

```apex
public with sharing class KnowledgeArticleController {

    @AuraEnabled(cacheable=true)
    public static Knowledge__kav getArticle(Id articleId) {
        return [
            SELECT Id, Title, Summary, Body__c, LastPublishedDate,
                   KnowledgeArticleId
            FROM Knowledge__kav
            WHERE Id = :articleId
            AND PublishStatus = 'Online'
            LIMIT 1
        ];
    }

    // Non-cacheable — performs DML-equivalent platform service call
    @AuraEnabled
    public static void voteOnArticle(Id articleId, Integer rating) {
        if (rating < 1 || rating > 5) {
            throw new AuraHandledException('Rating must be between 1 and 5.');
        }
        // KnowledgeArticleId (15/18-char) is the master article ID,
        // distinct from the version record ID used in SOQL
        Knowledge__kav kav = [
            SELECT KnowledgeArticleId
            FROM Knowledge__kav
            WHERE Id = :articleId
            AND PublishStatus = 'Online'
            LIMIT 1
        ];
        KbManagement.PublishingService.rateKnowledgeArticle(
            kav.KnowledgeArticleId, rating, UserInfo.getUserId()
        );
    }
}
```

LWC JavaScript (`knowledgeArticleDetail.js`):

```javascript
import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import TITLE_FIELD from '@salesforce/schema/Knowledge__kav.Title';
import BODY_FIELD from '@salesforce/schema/Knowledge__kav.Body__c';
import voteOnArticle from '@salesforce/apex/KnowledgeArticleController.voteOnArticle';

const FIELDS = [TITLE_FIELD, BODY_FIELD];

export default class KnowledgeArticleDetail extends LightningElement {
    @api recordId;

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    article;

    get title() {
        return getFieldValue(this.article.data, TITLE_FIELD);
    }

    get body() {
        return getFieldValue(this.article.data, BODY_FIELD);
    }

    handleThumbsUp() {
        this.submitVote(5);
    }

    handleThumbsDown() {
        this.submitVote(1);
    }

    submitVote(rating) {
        voteOnArticle({ articleId: this.recordId, rating })
            .then(() => {
                this.dispatchEvent(
                    new CustomEvent('votereceived', { detail: { rating } })
                );
            })
            .catch(error => {
                console.error('Vote submission failed', error);
            });
    }
}
```

LWC template (`knowledgeArticleDetail.html`):

```html
<template>
    <template if:true={article.data}>
        <h1>{title}</h1>
        <!-- Use lightning-formatted-rich-text — never innerHTML -->
        <lightning-formatted-rich-text value={body}></lightning-formatted-rich-text>
        <div class="vote-controls">
            <lightning-button-icon
                icon-name="utility:like"
                alternative-text="Helpful"
                onclick={handleThumbsUp}>
            </lightning-button-icon>
            <lightning-button-icon
                icon-name="utility:dislike"
                alternative-text="Not helpful"
                onclick={handleThumbsDown}>
            </lightning-button-icon>
        </div>
    </template>
    <template if:true={article.error}>
        <p>Article could not be loaded.</p>
    </template>
</template>
```

**Why it works:** `lightning-formatted-rich-text` renders the HTML body safely without XSS risk. The `@wire(getRecord)` pattern uses Lightning Data Service caching, avoiding a custom Apex call for the detail view. Voting routes through `KbManagement.PublishingService.rateKnowledgeArticle` — the only supported platform mechanism — using the `KnowledgeArticleId` master ID (not the version record ID).

---

## Anti-Pattern: Using innerHTML to Render Article Body

**What practitioners do:** Assign the rich text body field value directly to a DOM element's `innerHTML` property inside a `renderedCallback`:

```javascript
// WRONG — XSS risk
renderedCallback() {
    const container = this.template.querySelector('.article-body');
    if (container && this.body) {
        container.innerHTML = this.body; // Never do this
    }
}
```

**What goes wrong:** Knowledge article body fields can contain HTML authored by admins or imported from external systems. Directly setting `innerHTML` bypasses Locker Service sanitization and exposes the page to stored XSS if the article body contains malicious script tags. Locker Service will also throw a security error in some contexts.

**Correct approach:** Always use `lightning-formatted-rich-text` in the component template. It renders HTML safely and is the platform-sanctioned method for displaying rich text fields in LWC.
