# LLM Anti-Patterns — Knowledge Article Import

Common mistakes AI coding assistants make when generating or advising on Knowledge Article Import.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming Articles Can Be Published During Import

**What the LLM generates:** "Add a `PublishStatus` column to your CSV with the value `Online` to publish articles automatically during import."

**Why it happens:** LLMs generalize from Salesforce record create/update patterns where status fields are settable on write. They are unaware that the Knowledge import mechanism ignores publish status and that there is no publish-on-import option.

**Correct pattern:**

```
All imported articles land in Draft status regardless of CSV content.
After import, publish separately:
- UI: Knowledge list view > filter Draft > select all > Publish (max 200 per action)
- API: PATCH /services/data/vXX.0/knowledgeManagement/articles/<id>
        Body: { "publishStatus": "Online" }
```

**Detection hint:** Any instruction containing `PublishStatus=Online` or `publish=true` in the context of the import CSV or .properties file is incorrect.

---

## Anti-Pattern 2: Using Commas or Semicolons as Data Category Delimiters

**What the LLM generates:** `datacategorygroup__Products: "CRM,Analytics,Platform"` or `"CRM;Analytics"` in CSV examples.

**Why it happens:** LLMs default to comma or semicolon as multi-value delimiters because those are standard in most CSV and list formats. The `+`-delimiter is unique to Salesforce Knowledge import and is not widely represented in training data.

**Correct pattern:**

```csv
datacategorygroup__Products
CRM+Analytics+Platform
```

No spaces around `+`. No other delimiter is accepted.

**Detection hint:** Check any `datacategorygroup__` cell value containing `,` or `;` — those are always wrong.

---

## Anti-Pattern 3: Using the Article Type Label Instead of API Name in .properties

**What the LLM generates:**
```
ArticleType=FAQ
ArticleType=Help Article
ArticleType=Product Documentation
```

**Why it happens:** LLMs use the human-readable label because that is what appears in most UI-facing documentation and setup screenshots. The `__kav` suffix requirement is a metadata detail not well represented in general knowledge.

**Correct pattern:**

```
ArticleType=FAQ__kav
ArticleType=Help_Article__kav
ArticleType=Product_Documentation__kav
```

The value must be the metadata DeveloperName with `__kav` appended, not the UI display label.

**Detection hint:** Any `ArticleType` value in a .properties file that does not end in `__kav` is incorrect.

---

## Anti-Pattern 4: Placing HTML Body Content Inline in the CSV

**What the LLM generates:** A CSV where the body field column contains the full HTML string directly:

```csv
Title,Body__c
My Article,"<h1>Title</h1><p>Some content with <strong>bold</strong> text...</p>"
```

**Why it happens:** LLMs default to inline content because it is conceptually simpler and matches how Salesforce REST API record creation works. They are unaware of the CSV cell length limitations and the encoding issues with inline HTML in CSV.

**Correct pattern:**

```csv
Title,Body__c
My Article,html/my-article.html
```

The body column should contain a relative path to an HTML file in the `html/` folder within the ZIP. The HTML content belongs in that file, not in the CSV cell.

**Detection hint:** CSV body columns containing `<html>`, `<h1>`, `<p>`, or any HTML tag strings are likely using the inline anti-pattern.

---

## Anti-Pattern 5: Treating Import Completion as Migration Completion

**What the LLM generates:** A migration plan or checklist that ends with "Upload the ZIP file to Setup > Knowledge > Import Articles and the migration is complete."

**Why it happens:** LLMs model import as a terminal operation analogous to a database insert, not as a two-phase process (import then publish). The Draft landing status is a Salesforce-specific constraint that is often omitted in general descriptions of the import feature.

**Correct pattern:**

```
Migration is complete only after:
1. Import job completed with 0 row errors (verify row count)
2. Data category assignments validated on sample articles
3. All imported articles bulk-published (none left in Draft unintentionally)
4. Published articles confirmed visible in expected channels (pkb, app, etc.)
```

**Detection hint:** Any migration plan, runbook, or checklist that does not include an explicit post-import publish step for Knowledge articles is missing this phase.

---

## Anti-Pattern 6: Assuming URLName Is Unique Per Article Type

**What the LLM generates:** "URLName must be unique within each article type. You can reuse the same URLName across different article types."

**Why it happens:** LLMs may analogize to other scoping rules in Salesforce (e.g., API names being unique per object) and incorrectly scope URLName uniqueness to the article type level.

**Correct pattern:**

```sql
-- Pre-check uniqueness across the entire org
SELECT UrlName, ArticleType, PublishStatus
FROM KnowledgeArticleVersion
WHERE UrlName IN ('your-slug-1', 'your-slug-2')
```

URLName must be globally unique across all article types in the org.

**Detection hint:** Any statement claiming URLName uniqueness is scoped to an article type is incorrect.
