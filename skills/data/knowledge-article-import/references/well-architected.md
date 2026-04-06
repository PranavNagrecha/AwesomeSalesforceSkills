# Well-Architected Notes — Knowledge Article Import

## Relevant Pillars

- **Reliability** — Knowledge article imports must be idempotent and recoverable. Import jobs that fail mid-batch leave the org in a partial state (some articles imported as Drafts, others not created). A reliable import process pre-validates CSV content and URLName uniqueness before uploading, splits large content sets into independently retryable batches, and verifies row counts post-import against expected totals before triggering the publish step.

- **Operational Excellence** — Bulk imports are operational events, not one-time scripts. Maintain a record of which ZIP batches were imported, their import job IDs, and the resulting article IDs. Document the post-import publish step explicitly in runbooks. Use consistent URLName naming conventions that survive re-runs and future migrations.

- **Security** — Knowledge articles have data category-based visibility. Articles published without correct data category assignments are visible to users who should not see them, or invisible to users who need them. Validate data category assignment on a test batch before mass-publishing. Do not publish imported articles until category assignments have been verified.

- **Performance** — The 20 MB ZIP limit is the primary throughput constraint. Batch strategy should account for this ceiling from the outset. Post-import bulk publishing via the UI list view is capped at 200 articles per action; large imports require API-based publishing to avoid hours of manual UI work.

## Architectural Tradeoffs

**ZIP import vs. API-based article creation:** The ZIP import is the only Salesforce-native mechanism for bulk-creating articles with HTML body content in one operation. The alternative — creating articles via the REST API or Bulk API 2.0 — requires separate steps for the article shell and the article version body, and does not support HTML file uploads directly. Use the ZIP import for initial migrations; use the API for ongoing programmatic creation.

**Inline CSV body vs. html/ folder:** Inline body content in the CSV is simpler to generate but breaks on rich HTML and hits undocumented cell length limits silently. The html/ folder approach is more complex to build but handles all article content types reliably. Always use the html/ folder for production migrations.

**Single large batch vs. multiple small batches:** A single batch is easier to manage but has no partial recovery path if it hits the 20 MB limit or a mid-job failure. Multiple smaller batches add operational overhead but allow targeted retry without re-processing successfully imported articles.

## Anti-Patterns

1. **Publishing all imported articles immediately without category validation** — Rushing to publish removes the Draft safety net before verifying that data category assignments are correct. If categories were misconfigured (wrong delimiter, wrong casing), articles are published with no category — making them visible to all users regardless of knowledge visibility settings. Always validate a sample batch's category assignments before mass-publishing.

2. **Ignoring the post-import publish step in migration plans** — Project plans that treat import completion as migration completion cause go-live delays when stakeholders discover all articles are in Draft. The publish step is a separate, time-consuming operation for large content sets and must be planned, estimated, and resourced explicitly.

3. **Reusing URLNames from the source system without uniqueness validation** — Source system slugs often conflict with existing Salesforce Knowledge articles or with each other (when slugs were not enforced globally in the source system). Importing without pre-checking uniqueness results in silent row failures that are only discoverable by comparing expected vs. actual row counts in the import log.

## Official Sources Used

- Import External Content into Salesforce Knowledge — https://help.salesforce.com/s/articleView?id=sf.knowledge_import_existing_content.htm&type=5
- Create a CSV File for a Knowledge Article Import — https://help.salesforce.com/s/articleView?id=sf.knowledge_import_csv.htm&type=5
- Lightning Knowledge Guide — https://help.salesforce.com/s/articleView?id=sf.knowledge_whatis.htm&type=5
- KnowledgeArticleVersion Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_knowledgearticleversion.htm
- Knowledge Management REST API — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_knowledge_support_art.htm
