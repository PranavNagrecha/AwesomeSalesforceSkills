# Knowledge Article LWC — Work Template

Use this template when building or reviewing an LWC component that queries, displays, or collects feedback on Salesforce Knowledge articles.

## Scope

**Skill:** `knowledge-article-lwc`

**Request summary:** (fill in what the user asked for — e.g., "Build a search component for Experience Cloud guest users" or "Add thumbs-up/down voting to an existing article detail page")

---

## Context Gathered

Answer each question before writing any code.

- **Article object API name:** `Knowledge__kav` / `______kav` (confirm in Setup > Knowledge Settings)
- **Required fields:** Title, Summary, Body field name (`Body__c` or custom), channel flags, language code
- **Target surface:** Internal app / Experience Cloud authenticated / Experience Cloud guest
- **Data category groups in use:** (list groups and relevant values, or "none")
- **Guest User data category visibility configured:** Yes / No / N/A
- **Voting / feedback required:** Yes / No
- **Known constraints or existing components:** (record what already exists)

---

## Retrieval Pattern Selected

Choose one and justify:

- [ ] `@wire(getRecord)` — single article detail page, record ID available via `@api recordId`
- [ ] Imperative Apex + SOSL — user-driven free-text search
- [ ] Imperative Apex + SOQL with `WITH DATA CATEGORY` — category-scoped programmatic list
- [ ] Hybrid — detail via `getRecord`, list via Apex

**Justification:** (explain why this pattern fits the use case)

---

## Apex Controller Checklist

- [ ] Retrieval method decorated `@AuraEnabled(cacheable=true)`
- [ ] SOQL/SOSL query filters `PublishStatus = 'Online'`
- [ ] Channel visibility flag included (`IsVisibleInPkb = true` for Experience Cloud)
- [ ] Language filter included if multi-language Knowledge is enabled
- [ ] `WITH DATA CATEGORY` clause added if category-scoped filtering is required
- [ ] Sharing declaration is appropriate: `with sharing` (internal/authenticated) or `without sharing` (guest)
- [ ] Voting method is a separate non-cacheable `@AuraEnabled` method
- [ ] Voting method queries `KnowledgeArticleId` and passes master ID to `KbManagement.PublishingService.rateKnowledgeArticle`
- [ ] SOSL user input escaped with `String.escapeSingleQuotes` before concatenation

---

## LWC Component Checklist

- [ ] Article body rendered via `<lightning-formatted-rich-text>` (never `innerHTML`)
- [ ] Search input debounced (≥ 300 ms) before triggering Apex call
- [ ] Error state handled and surfaced to the user
- [ ] Empty result state handled distinctly from error state
- [ ] `@wire` used for cacheable methods; imperative calls used for voting and dynamic searches
- [ ] Component metadata (`*.js-meta.xml`) exposes the component to the correct target (`lightningCommunity__Page` for Experience Cloud)

---

## Experience Cloud Guest Access Verification

Complete only if the component is deployed to a guest-accessible page:

- [ ] Guest User data category visibility configured in Experience Workspaces > Administration > Guest User > Data Category Visibility (or org-level equivalent)
- [ ] Article `IsVisibleInPkb` field confirmed `true` on target articles
- [ ] Knowledge OWD or site guest sharing override allows read access
- [ ] Apex controller declared `without sharing`
- [ ] Tested in incognito browser (not admin Experience Builder preview)

---

## Apex Test Class Checklist

- [ ] Happy path: returns expected articles when matching records exist
- [ ] Empty result: returns empty list when no articles match (not null)
- [ ] Invalid input: search with blank/null string returns empty list gracefully
- [ ] Voting happy path: `voteOnArticle` completes without exception
- [ ] Coverage ≥ 90% on the Apex controller class

---

## Notes

(Record any deviations from the standard pattern and why — e.g., "Used SOQL instead of SOSL because articles are always filtered by a single fixed data category, not by user input.")
