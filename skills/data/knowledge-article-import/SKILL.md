---
name: knowledge-article-import
description: "Use this skill when bulk-importing Knowledge articles into Salesforce from an external source using the ZIP-based import mechanism. Trigger keywords: knowledge import, article import, migrate help center, bulk upload articles, CSV article import, knowledge base migration. NOT for Knowledge admin setup (article types, data categories, permission sets), ongoing article management, or translation workflows once articles are live."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I bulk import knowledge articles from an external help center into Salesforce?"
  - "I need to migrate hundreds of articles into Lightning Knowledge — what is the CSV format and ZIP structure?"
  - "Articles imported into Salesforce Knowledge are stuck in Draft — how do I publish them after import?"
tags:
  - knowledge
  - knowledge-article-import
  - lightning-knowledge
  - data-migration
  - bulk-import
inputs:
  - "Source article content (HTML, plain text, or structured data) to be imported"
  - "Salesforce org with Lightning Knowledge enabled and at least one article record type"
  - "RecordTypeId values for each article type being imported"
  - "Data category group names and category API names for classification"
  - "Target language codes if importing multilingual content"
outputs:
  - "ZIP import package (CSV + .properties file + optional HTML/assets folder)"
  - "Post-import bulk-publish step guidance (list view or API)"
  - "Review checklist for validating imported articles"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Knowledge Article Import

This skill activates when a practitioner needs to bulk-import Knowledge articles into Salesforce Lightning Knowledge using the native ZIP-based import mechanism. It covers ZIP package construction, CSV column requirements, the .properties control file, HTML asset embedding, the Draft-only landing status constraint, and the mandatory post-import bulk publish step.

---

## Before Starting

Gather this context before working on anything in this domain:

- Lightning Knowledge must be enabled in the org (Setup > Knowledge Settings). Classic Knowledge and Lightning Knowledge use different import mechanisms — confirm which is active.
- Obtain the 18-character RecordTypeId for each article type. Articles imported without a valid RecordTypeId will fail.
- Data category groups and category API names must exist in the org before import. Categories are not created on the fly.
- The 20 MB ZIP file size limit is hard. Plan batch splitting for large content sets before building the package.

---

## Core Concepts

### ZIP Package Structure

The Salesforce Knowledge import mechanism accepts a single ZIP file (max 20 MB). The ZIP must contain:

1. A CSV file — one row per article, defining metadata and mapping to content files.
2. A `.properties` file — a key-value control file specifying the article type, encoding, and optional folder paths.
3. An optional `html/` folder — contains one HTML file per article when body content is stored externally rather than inline in the CSV.
4. An optional `resources/` folder — contains images and other binary assets referenced from HTML files.

The `.properties` file must reference the CSV file name exactly. A mismatch in the filename causes the entire import to fail with a generic error.

### CSV Column Format

The CSV controls every article field. Required and commonly used columns:

| Column | Required | Notes |
|---|---|---|
| `Title` | Yes | Article title; cannot be blank |
| `URLName` | Yes | Must be URL-safe, unique within the org, lowercase with hyphens |
| `RecordTypeId` | Yes | 18-character ID; determines article type |
| `IsMasterLanguage` | Yes | `true` for the primary language version |
| `Language` | Yes | BCP-47 code, e.g. `en_US` |
| `channels` | No | One or more of: `app`, `pkb`, `csp`, `prm` separated by semicolons |
| `datacategorygroup__<GroupApiName>` | No | One column per data category group; values are category API names delimited by `+` for multi-select |

Additional custom field columns follow the pattern `<FieldApiName>` exactly matching the API name on the article object. The HTML body column is `<FieldApiName>` pointing to a relative file path inside the `html/` folder rather than inline content.

### .properties Control File

The `.properties` file is a Java-style key-value file. Required keys:

```
ArticleType=<ArticleTypeApiName>
Encoding=UTF-8
CSVFile=<csv-filename>.csv
```

Optional keys include `HTMLFolderPath` (defaults to `html`) and `ResourceFolderPath` (defaults to `resources`). The `ArticleType` value must match the article record type API name (ending in `__kav`), not the label.

### Draft-Only Landing Status

All articles imported via the ZIP mechanism land in `Draft` status regardless of any field value in the CSV. There is no publish-on-import option. After import completes, articles must be published separately.

### Data Category Multi-Select Syntax

When an article belongs to multiple categories within the same group, values are `+`-delimited in the CSV cell: `Hardware+Networking+Security`. Do not use commas, semicolons, or spaces. A separate column is required per category group.

---

## Common Patterns

### Pattern 1: Single-Language Batch Import from External Help Center

**When to use:** Migrating a flat help center (single language, single article type) into Salesforce Knowledge in one pass.

**How it works:**
1. Export source articles to HTML files, one per article.
2. Build the CSV with one row per article; set `IsMasterLanguage=true`, `Language=en_US`, populate `RecordTypeId` uniformly.
3. Place HTML files in the `html/` folder; reference each by relative path in the body column.
4. Create the `.properties` file pointing to the CSV.
5. ZIP all files keeping paths relative (no top-level folder wrapper).
6. Import via Setup > Knowledge > Import Articles.
7. After import, bulk-publish using a Knowledge list view filtered to Draft status.

**Why not the alternative:** Inline CSV body content (no html/ folder) breaks on articles with rich HTML, embedded images, or content over the CSV cell length limit. Always use the html/ folder for body content.

### Pattern 2: Multi-Category Article Import with Data Category Assignment

**When to use:** Articles need to be assigned to multiple data categories at import time so that visibility rules apply immediately after publish.

**How it works:**
1. For each data category group (e.g. `Products`, `Region`), add a column named `datacategorygroup__Products` and `datacategorygroup__Region` to the CSV.
2. In each cell, list the category API names joined by `+`: `Laptop+Desktop`.
3. Keep category API names lowercase and exactly matching the org's category API name — not the label.
4. Import and validate that category assignments appear correctly in the imported drafts before bulk publishing.

**Why not the alternative:** Attempting to assign data categories after publish via list view is manual and does not scale. Getting categories right at import ensures visibility rules are correct from first publish.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| < 20 MB of content, single article type | Single ZIP import via Setup UI | Simplest; no API required |
| > 20 MB of content | Split into multiple ZIP batches by article group or alphabet | Hard platform limit; no workaround |
| Articles need to be published immediately after import | Import first, then bulk-publish via list view or Knowledge API | No publish-on-import option exists |
| Multilingual articles | One CSV row per language version; set `IsMasterLanguage=true` on primary, `false` on translations | Salesforce tracks language versions separately |
| Rich HTML with images | Use html/ folder + resources/ folder; reference assets by relative path | Inline image base64 encoding is not supported |
| Large-scale automation | Use Salesforce CLI + Knowledge REST API for programmatic publish post-import | UI bulk publish is capped at 200 per list view action |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify org prerequisites** — Confirm Lightning Knowledge is enabled, at least one article record type exists, and data category groups are configured. Collect the RecordTypeId(s) and category API names needed.
2. **Prepare content** — Export source articles to individual HTML files. Strip non-UTF-8 characters. Validate that image assets are available and can be placed in a `resources/` folder.
3. **Build the CSV** — Create one row per article with all required columns: `Title`, `URLName`, `RecordTypeId`, `IsMasterLanguage`, `Language`. Add `channels` and `datacategorygroup__*` columns as needed. Ensure `URLName` values are unique across the org.
4. **Create the .properties file** — Set `ArticleType`, `Encoding=UTF-8`, and `CSVFile` to match the CSV filename exactly. Confirm the `ArticleType` uses the API name (ending in `__kav`), not the label.
5. **Assemble and validate the ZIP** — Package the CSV, .properties, html/ folder, and resources/ folder. Verify total ZIP size is under 20 MB. Test ZIP integrity locally before upload.
6. **Import via Setup** — Navigate to Setup > Knowledge > Import Articles. Upload the ZIP, monitor import job status, and review the import log for per-row errors.
7. **Bulk publish imported drafts** — Filter the Knowledge list view to Draft articles imported in this batch. Select all and publish. For batches over 200 articles, use the Knowledge REST API or iterate the list view in pages.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `URLName` values are unique org-wide and contain no special characters beyond hyphens
- [ ] `RecordTypeId` is a valid 18-character ID pointing to an existing article record type
- [ ] Data category column names match group API names exactly (`datacategorygroup__GroupApiName`)
- [ ] Category values within a cell use `+` as delimiter, not commas or semicolons
- [ ] ZIP file is under 20 MB; if over, content has been split into multiple batches
- [ ] `.properties` file `CSVFile` value matches the actual CSV filename exactly
- [ ] `ArticleType` in .properties uses the API name (ending in `__kav`), not the label
- [ ] Import log reviewed and all rows processed without error
- [ ] Post-import bulk publish step completed; no articles left in Draft unintentionally

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **All imported articles land in Draft — always** — The import process ignores any publish-status field in the CSV. Every article arrives as a Draft regardless of source status. A separate bulk-publish step is mandatory. Forgetting this leaves all imported content invisible to end users.
2. **20 MB ZIP limit is uncompressed content, not compressed** — Salesforce measures the limit against the ZIP file size on disk, which is the compressed size. However, the practical limit is reached sooner than expected when HTML files contain embedded base64 images. Always use the resources/ folder for binary assets.
3. **URLName must be globally unique in the org** — URLName collisions across article types cause individual row failures with a non-obvious error. Pre-check URLName uniqueness with a SOQL query on `KnowledgeArticle` before import: `SELECT UrlName FROM KnowledgeArticle`.
4. **ArticleType in .properties must be the API name, not the label** — The API name ends in `__kav`. Using the display label (e.g., "FAQ" instead of "FAQ__kav") causes the entire import job to fail immediately with a misleading "invalid article type" message.
5. **Data category column header casing is case-sensitive** — The column header `datacategorygroup__Products` must match the group API name casing exactly. A mismatch silently skips category assignment without failing the row.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ZIP import package | The assembled ZIP file ready for upload to Setup > Knowledge > Import Articles |
| CSV article manifest | The CSV file documenting all article metadata, field values, and HTML file mappings |
| .properties control file | The import control file specifying article type, encoding, and file paths |
| Post-import publish checklist | Steps to bulk-publish Draft articles after import completes |

---

## Related Skills

- data/bulk-api-and-large-data-loads — Use for large-scale programmatic Knowledge article operations beyond what the ZIP import supports
- data/data-migration-planning — Use to plan sequencing, rollback, and validation strategy before executing a large Knowledge migration
