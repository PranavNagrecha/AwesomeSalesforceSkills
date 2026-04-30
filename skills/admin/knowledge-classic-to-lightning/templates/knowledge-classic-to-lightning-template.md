# Knowledge Classic to Lightning — Work Template

Use this template when planning a Knowledge Classic to Lightning Knowledge migration.

---

## Scope

**Skill:** `knowledge-classic-to-lightning`

**Target migration date (production):** _(date)_

**Sandbox dry-run date:** _(date — must precede production by at least 2 weeks)_

---

## Inventory

```sql
SELECT ArticleType, COUNT(Id) FROM KnowledgeArticleVersion WHERE PublishStatus='Online' AND IsLatestVersion=true GROUP BY ArticleType;
SELECT Language, COUNT(Id) FROM KnowledgeArticleVersion WHERE IsLatestVersion=true GROUP BY Language;
SELECT DataCategoryGroupName, DataCategoryName, COUNT(Id) FROM KnowledgeArticleVersion WHERE IsLatestVersion=true GROUP BY DataCategoryGroupName, DataCategoryName;
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
| Apex code | `__kav` sObject reference | grep + replace + deploy |
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
- [ ] All `__kav` Apex references updated and deployed
- [ ] Quick Actions audited for `__kav` substring; updated
- [ ] Service Console Knowledge Component active and showing migrated articles
- [ ] Phased channel cutover scheduled and rollback plan documented
- [ ] Migration audit log persisted with classic→lightning ID mapping
