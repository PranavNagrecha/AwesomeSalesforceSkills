# Well-Architected Notes — Analytics Requirements Gathering

## Relevant Pillars

- **Reliability** — Complete requirements prevent mid-project dataset redesigns; the most expensive analytics failures come from incorrect data source type selection discovered after recipes are built.
- **Operational Excellence** — Requirements documents become the canonical reference for future analytics maintenance; without them, every change requires re-eliciting requirements.
- **Security** — Row-level security requirements must be captured before dataset design; implementing RLS as an afterthought requires recipe rebuilds and potential data exposure between design and fix.
- **Performance** — Data source selection (Salesforce sync vs external connector) and field-level scoping (avoiding unnecessary fields) are performance decisions that must be specified in requirements.
- **Scalability** — Refresh cadence and incremental vs full-refresh requirements determine whether the analytics scales to large datasets; these must be documented at requirements time.

## Architectural Tradeoffs

**CRM Analytics vs Standard Reports:** Not every reporting need justifies CRM Analytics and its license cost. The decision must be documented with rationale. Standard Reports are sufficient for single-object use cases with standard row-level security.

**Salesforce object sync vs External connector:** Salesforce local sync does not count toward org Bulk API limits, while external Salesforce connections and output connections do. UNVERIFIED (2026-10-03): the field-count and row-count limits on object sync are not restated in the setup guide read for this pass. External connectors (Snowflake, BigQuery) require Named Credential setup and incremental refresh planning for large tables. The choice must be specified in requirements.

**Full refresh vs incremental refresh:** External data sources default to full refresh (UNVERIFIED (2026-10-03): not restated in the guides read; the REST guide shows only a `connectionMode` of `Full`). For large datasets, incremental refresh is required. Requirements must specify refresh requirements and verify that the data source supports a reliable watermark field.

## Anti-Patterns

1. **Object names without field-level scoping** — Requirements that list "Opportunity object" without specifying which fields are needed cause recipes to sync all fields, increasing dataset size, dataflow runtime, and storage costs unnecessarily.

2. **Skipping CRM Analytics vs Reports decision** — Building CRM Analytics when standard Reports are sufficient wastes license cost and development effort. The decision must be made and documented as the first step of requirements gathering.

3. **No audience matrix** — Requirements without a row-level security specification for each user role result in either over-sharing (users see data they shouldn't) or under-sharing (users can't see data they need) that requires recipe and dashboard rebuilds.

## Official Sources Used

Read for the 2026-10-03 pass (fetched with plain `curl`; line numbers cite the `pdftotext -layout` extraction):

- Analytics Platform Setup Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_setup.pdf (Integration User and Security User L87-106; dataset row storage per license L974-1004; local versus external connection limits L1140-1141; Recipe and Dataflow Limits L1148-1191; output connector limits L1241-1244)
- Analytics Security Implementation Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_security.pdf (sharing inheritance tradeoff L253-257; predicate behavior after dataset creation and the `'false'` default L274-277; no-RLS warning L289; `$User` session note L295; where predicates are defined L297-301)
- CRM Analytics REST API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_rest.pdf (connected objects cannot be visualized directly L6012-6015; `connectionMode` example L6195-6200)
- Metadata API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (WaveApplication L138608-138650; FolderShare L74693-74745; WaveRecipe `securityPredicate` L138986-139040)

Listed by the original author and not re-read in this pass (help.salesforce.com and architect.salesforce.com do not serve article content to plain HTTP clients):

- CRM Analytics Requirements: https://help.salesforce.com/s/articleView?id=sf.bi_requirements.htm
- Integrate and Prepare Data for Analysis: https://help.salesforce.com/s/articleView?id=sf.bi_integrate_data.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `admin/analytics-kpi-definition` — downstream skill to define KPI formulas after requirements are gathered
- `admin/requirements-gathering-for-sf` — general requirements gathering patterns
