# Gotchas — Knowledge Article Import

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Articles Always Land in Draft — No Publish-on-Import Option

**What happens:** Every article imported via the ZIP mechanism lands in `Draft` status, regardless of the source system's publish status, any field value in the CSV, or any configuration in the .properties file. There is no `PublishStatus` column in the import CSV that Salesforce honors.

**When it occurs:** Every import run, every time. This is not a bug or misconfiguration — it is platform behavior by design as of Spring '26.

**How to avoid:** Plan a mandatory post-import publish step before starting the migration. For batches under 200 articles, use the Knowledge list view (filter to Draft, select all, click Publish). For larger batches, use the Knowledge REST API (`PATCH /services/data/vXX.0/knowledgeManagement/articles/<id>` with `publishStatus=Online`) or write a short Apex batch job. Do not assume articles are live after the import job completes.

---

## Gotcha 2: 20 MB ZIP Limit Applies to the Compressed File Size

**What happens:** Salesforce enforces a 20 MB maximum on the ZIP file itself (the compressed archive, not the uncompressed content). However, HTML files with embedded base64-encoded images are already essentially pre-encoded and do not compress well, so the ZIP file can approach the limit faster than expected. Import jobs that exceed 20 MB fail immediately with no partial processing.

**When it occurs:** Imports with rich HTML content, many images, or large knowledge bases. Particularly common when migrating from systems that embed images as base64 `<img src="data:image/...">` tags.

**How to avoid:** Strip base64-encoded images from HTML before import and move them to the `resources/` folder, referencing them with relative paths (`<img src="../resources/diagram.png">`). Pre-check ZIP file size before uploading. Split large migrations into multiple batches grouped by article category or article type.

---

## Gotcha 3: URLName Must Be Globally Unique Across All Article Types

**What happens:** `URLName` (the article's URL slug) must be unique across all article types in the org, not just within a single article type. If a URLName already exists — even on a Draft article of a different type — the import row fails with an error referencing a constraint violation. The rest of the batch continues processing, so failures are silent within a successful import job.

**When it occurs:** When importing articles whose titles overlap with existing articles in the org, or when re-importing after a failed run that left Draft articles with the same URLNames.

**How to avoid:** Before importing, run a SOQL query to check for conflicts:
```sql
SELECT UrlName, ArticleType, PublishStatus
FROM KnowledgeArticleVersion
WHERE UrlName IN ('your-url-name-1', 'your-url-name-2')
```
If duplicates exist from a failed prior run, delete the Draft versions first. Consider prefixing URLNames with a migration batch identifier (e.g., `import-2026-crm-overview`) to avoid collisions.

---

## Gotcha 4: .properties ArticleType Must Be the API Name, Not the Label

**What happens:** The `ArticleType` key in the `.properties` file must be the metadata API name of the article record type, which ends in `__kav` (e.g., `FAQ__kav`, `Help_Article__kav`). Using the display label (e.g., `FAQ`, `Help Article`) causes the entire import job to fail immediately with a misleading "invalid article type" message before any rows are processed.

**When it occurs:** Any time the .properties file is built manually by someone who looks up the article type by its UI label.

**How to avoid:** Retrieve the API name from Setup > Object Manager > Knowledge > Record Types, or via SOQL:
```sql
SELECT DeveloperName FROM RecordType WHERE SObjectType = 'Knowledge__kav'
```
The `ArticleType` in .properties is `<DeveloperName>__kav` (append `__kav` to the DeveloperName). Always validate the .properties file before uploading.

---

## Gotcha 5: Data Category Column Headers Are Case-Sensitive

**What happens:** The column header for data category assignment must exactly match the data category group's API name with the `datacategorygroup__` prefix and correct casing. For example, if the group API name is `Products` (capital P), the header must be `datacategorygroup__Products` — not `datacategorygroup__products`. A casing mismatch causes the category assignment to be silently skipped: the article imports successfully but has no categories assigned.

**When it occurs:** When CSV files are built programmatically or when the category group API name contains mixed case (common for groups created with labels like "Product Area").

**How to avoid:** Retrieve the exact data category group API name via SOQL:
```sql
SELECT DeveloperName FROM DataCategoryGroup WHERE IsActive = true
```
Use the `DeveloperName` value exactly (preserving casing) in the column header. Validate category assignment on a small test batch before the full import.
