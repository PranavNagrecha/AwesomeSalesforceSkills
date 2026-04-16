# Well-Architected Notes — Einstein Analytics Data Model (XMD)

## Relevant Pillars

### Reliability
XMD customizations are a runtime dependency for all CRM Analytics dashboards. Corrupted or orphaned XMD causes rendering failures. The backup-before-PATCH workflow ensures recovery is possible.

### Operational Excellence
Treating XMD updates as a repeatable documented process (GET backup → PATCH → validate) ensures XMD state is auditable and reproducible across environments.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Repeatable Operations | XMD updates should use version-controlled JSON payloads |
| Configuration as Code | Main XMD PATCH payloads stored alongside dataflow/recipe definitions |
| Change Management | Recipe schema changes should trigger a post-run XMD validation step |

## Cross-Skill References

- `admin/analytics-dataflow-development` — Dataflow runs create new dataset versions; XMD attached at dataset level
- `admin/analytics-recipe-design` — Recipe schema changes can orphan main XMD customizations
- `admin/analytics-dataset-management` — Dataset scheduling affects when new versions are created

## Official Sources Used

- CRM Analytics REST API Developer Guide — Wave XMD: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_xmd.htm
- CRM Analytics REST API — Datasets Resource: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_resources_datasets.htm
- Salesforce Help: CRM Analytics Extended Metadata (XMD): https://help.salesforce.com/s/articleView?id=sf.bi_xmd.htm
