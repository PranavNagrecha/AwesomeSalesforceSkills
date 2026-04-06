# Examples — Knowledge Article Import

## Example 1: Migrating a Help Center to Salesforce Knowledge

**Context:** A support team is retiring an external Zendesk-style help center. They have 350 articles in HTML format, all in English, assigned to a single article type called "Help Article" (API name: `Help_Article__kav`). Articles need to land in the `General` data category.

**Problem:** Without this skill, teams typically try to paste HTML directly into the CSV body column, which breaks on any article with tables, images, or special characters, and hits CSV cell size limits silently — those rows are skipped without a clear error.

**Solution:**

Place each article's HTML in the `html/` folder and reference by relative path in the CSV. The ZIP structure:

```
knowledge_import_batch_01.zip
├── articles.csv
├── articles.properties
├── html/
│   ├── article-001.html
│   ├── article-002.html
│   └── ...
└── resources/
    ├── screenshot-1.png
    └── diagram-2.png
```

`articles.properties`:
```
ArticleType=Help_Article__kav
Encoding=UTF-8
CSVFile=articles.csv
HTMLFolderPath=html
ResourceFolderPath=resources
```

`articles.csv` (header + two sample rows):
```csv
Title,URLName,RecordTypeId,IsMasterLanguage,Language,channels,datacategorygroup__General,Body__c
How to Reset Your Password,how-to-reset-your-password,012000000000001AAA,true,en_US,pkb,General_Usage,html/article-001.html
Setting Up Two-Factor Authentication,setting-up-two-factor-auth,012000000000001AAA,true,en_US,pkb,General_Usage,html/article-002.html
```

After import, all 350 articles land in Draft. Bulk-publish from the Knowledge list view filtered to Draft, or use the REST API for batches over 200.

**Why it works:** Separating HTML content into files avoids CSV cell limits and encoding issues. The `resources/` folder lets images resolve correctly in the rendered article.

---

## Example 2: Multi-Language Article Import with Data Categories

**Context:** A global software company is importing 80 product articles in both English and German. Articles belong to multiple data categories across two groups: `Product` (values: `CRM`, `Analytics`) and `Region` (values: `EMEA`, `AMER`, `APAC`). The article type is `Product_Article__kav`.

**Problem:** Teams often create separate import runs for each language, losing the link between master and translation versions. They also forget that data category column headers are case-sensitive, so category assignment silently fails.

**Solution:**

One CSV contains both English (master) and German (translation) rows. Language rows are linked by sharing the same `URLName`.

```csv
Title,URLName,RecordTypeId,IsMasterLanguage,Language,datacategorygroup__Product,datacategorygroup__Region,Body__c
CRM Overview,crm-overview,012000000000002BBB,true,en_US,CRM,EMEA+AMER,html/crm-overview-en.html
CRM Übersicht,crm-overview,012000000000002BBB,false,de,CRM,EMEA,html/crm-overview-de.html
Analytics Guide,analytics-guide,012000000000002BBB,true,en_US,Analytics,APAC+AMER,html/analytics-guide-en.html
```

Key points:
- The German row uses the same `URLName` as the English master — this links them as translations of the same article.
- `IsMasterLanguage=false` on the German row.
- `datacategorygroup__Product` and `datacategorygroup__Region` headers match group API names exactly (case-sensitive).
- Multi-category values use `+` with no spaces: `EMEA+AMER`.

**Why it works:** Sharing `URLName` between master and translation rows is how Salesforce Knowledge associates language versions. The `+`-delimited category syntax allows multi-category assignment without multiple import passes.

---

## Anti-Pattern: Using Commas or Semicolons as Data Category Delimiters

**What practitioners do:** When assigning multiple data categories, they write `EMEA,AMER` or `EMEA;AMER` in the datacategorygroup column, following normal CSV or list conventions.

**What goes wrong:** The import silently ignores the category assignment or fails the category mapping for that cell. The article imports successfully but has no data categories assigned — meaning it is invisible to users whose Knowledge visibility is controlled by data category permissions. No error appears in the import log.

**Correct approach:** Always use `+` as the delimiter with no surrounding spaces: `EMEA+AMER+APAC`. This is documented in the Salesforce Knowledge import guide and is the only supported delimiter for multi-value category fields in the import CSV.
