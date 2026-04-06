# Knowledge Article Import — Work Template

Use this template when planning and executing a Knowledge article import into Salesforce.

## Scope

**Skill:** `knowledge-article-import`

**Request summary:** (fill in — e.g., "Migrate 200 FAQ articles from Zendesk to Salesforce Knowledge")

---

## Context Gathered

Answer these before starting:

- **Lightning Knowledge enabled?** Yes / No
- **Article record type API name (ends in __kav):** _______________
- **RecordTypeId (18 chars):** _______________
- **Data category groups and category API names:**
  - Group: _______________ Categories: _______________
  - Group: _______________ Categories: _______________
- **Target language(s) (BCP-47 codes, e.g. en_US, de, fr):** _______________
- **Channels to publish to (pkb / app / csp / prm):** _______________
- **Estimated article count:** _______________
- **Estimated total content size (HTML + images):** _______________
- **URLName pre-check done (SOQL query run for conflicts)?** Yes / No

---

## Batch Plan

| Batch # | Article Range / Group | Estimated ZIP Size | Status |
|---|---|---|---|
| 1 | | | Not started |
| 2 | | | Not started |

---

## ZIP Package Checklist

For each batch:

- [ ] CSV created with required columns: `Title`, `URLName`, `RecordTypeId`, `IsMasterLanguage`, `Language`
- [ ] `channels` column populated if needed
- [ ] `datacategorygroup__<GroupApiName>` columns added with `+`-delimited multi-values
- [ ] HTML body files placed in `html/` folder; CSV body column contains relative paths
- [ ] Binary assets (images, PDFs) placed in `resources/` folder
- [ ] `.properties` file created:
  - `ArticleType=<DeveloperName>__kav` (not the label)
  - `Encoding=UTF-8`
  - `CSVFile=<exact filename>.csv`
- [ ] ZIP assembled and file size confirmed under 20 MB
- [ ] `check_knowledge_article_import.py --zip <file>` run with no WARNs

---

## Import Execution

| Step | Action | Result |
|---|---|---|
| Upload | Setup > Knowledge > Import Articles — upload ZIP | |
| Monitor | Check import job status in Setup | |
| Validate | Review import log: rows attempted vs. rows succeeded | |
| Sample check | Open 3-5 imported Draft articles and verify field values, HTML rendering, category assignment | |

---

## Post-Import Publish Step

All articles land in Draft. Complete this section before marking the migration done:

- [ ] Knowledge list view filtered to Draft articles from this import batch
- [ ] Data category assignments verified on sample articles before publishing
- [ ] Bulk publish executed (UI list view for ≤ 200; REST API or Apex batch for > 200)
- [ ] Published article count matches expected count
- [ ] Published articles confirmed visible in expected channels

---

## Notes

Record any deviations from the standard pattern and why:

-
