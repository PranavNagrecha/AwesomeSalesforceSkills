# Knowledge Classic to Lightning — Work Template

Use this template when planning a Knowledge Classic to Lightning Knowledge migration.

UNVERIFIED (2026-10-20) (file-level): Migration Tool log behaviour, approval-process recreation and Service Console component behaviour below are Help-only.

---

## Scope

**Skill:** `knowledge-classic-to-lightning`

**Target migration date (production):** _(date)_

**Sandbox dry-run date:** _(date — must precede production by at least 2 weeks)_

---

## Inventory

```sql
-- Classic: PublishStatus or Id is required in WHERE (Lightning, API 47.0+: optional,
-- L163435-163436); ArticleType is Filter-only; category
-- fields live on <Type>__DataCategorySelection and are not groupable (obj 264
-- L163280-163281, L163041-163048, L38769-38800). Repeat per type / status.
SELECT COUNT(Id) FROM KnowledgeArticleVersion WHERE PublishStatus='Online' AND IsLatestVersion=true AND ArticleType='FAQ__kav';
SELECT Language, COUNT(Id) FROM KnowledgeArticleVersion WHERE PublishStatus='Online' GROUP BY Language;
SELECT ParentId, DataCategoryGroupName, DataCategoryName FROM FAQ__DataCategorySelection;
```

| Article Type | Online | Draft | Translations |
|---|---|---|---|
| | | | |

| Language | Article Count |
|---|---|
| en_US | |
| | |

---

## Article Type → Record Type Mapping

| Classic Article Type | Lightning Record Type | Consolidated From | Notes |
|---|---|---|---|
| FAQ__kav | FAQ | FAQ + Q_and_A | Field merge required for Description__c / Summary__c |
| HowTo__kav | HowTo | HowTo | |
| | | | |

---

## Field Pre-Normalization (if consolidating)

| Source Article Type | Source Field | Target Field on Migration | Apex Script Run? |
|---|---|---|---|
| | | | [ ] |

---

## Channel Cutover Plan

| Channel | Cutover Date | Verified By |
|---|---|---|
| Internal | | |
| Customer (Csp) | | |
| Partner (Prm) | | |
| Public KB (Pkb) | | |

---

## Downstream Consumer Audit

| Consumer | Reference Pattern | Update Required |
|---|---|---|
| Apex code | `__kav` sObject reference | remove triggers + rewrite + deploy BEFORE the Tool runs (apexdev 264 L16013-16014) |
| Quick Actions | URL or relationship to article-type | Setup edit |
| Reports | Report Type | New Report Types on Knowledge__kav |
| Service Console | Knowledge Component config | App Builder edit |
| Communities | Community Builder pages | Builder edit |
| Einstein Bots | Knowledge action | Bot Builder edit |
| Approval Processes | Per-Article-Type process | Recreate on Knowledge__kav |

---

## Visibility Verification (User-Impersonation)

| Profile / Permission Set | Sample Record Type | Pre-Migration Visible Count | Post-Migration Visible Count | Match? |
|---|---|---|---|---|
| Support Agent | FAQ | | | [ ] |
| Community User | HowTo | | | [ ] |
| Public KB | All public-flagged | | | [ ] |

---

## Sign-Off Checklist

- [ ] Migration Tool ran successfully in sandbox; zero unrecoverable errors in log
- [ ] Article counts per former type → record type match exactly
- [ ] Translation counts per language match
- [ ] Data category assignments preserved
- [ ] Publication state distribution matches (Online / Draft / Archived)
- [ ] Channel visibility flags preserved (`IsVisibleIn*`)
- [ ] Approval processes recreated per record type
- [ ] All `__kav` Apex references updated and deployed before migration; no triggers left on article types
- [ ] Quick Actions audited for `__kav` substring; updated
- [ ] Service Console Knowledge Component active and showing migrated articles
- [ ] Phased channel cutover scheduled (surface by surface; the article-type objects are gone after a multi-type migration)
- [ ] Migration audit log persisted with classic→lightning ID mapping (`MigratedToFromArticleVersion`, obj 264 L162069-162076)
