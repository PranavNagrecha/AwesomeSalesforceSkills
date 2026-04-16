# Well-Architected Notes — Analytics Data Preparation (XMD)

## Relevant Pillars

### Reliability
XMD metadata directly affects how datasets render in dashboards. Corrupted or missing field labels cause dashboard failures. The backup-before-PATCH requirement prevents irreversible metadata corruption.

### Operational Excellence
External CSV augmentation should be treated as a managed data source with a documented refresh process, not as a one-time upload. Operational excellence requires that all data sources have a defined owner and refresh cadence.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Repeatable Operations | XMD PATCH payloads should be version-controlled and reapplied as part of deployment pipelines |
| Data Freshness | External CSV sources need explicit refresh processes to avoid stale data |
| Auditability | Main XMD backups provide a record of the state before each modification |

## Cross-Skill References

- `admin/analytics-recipe-design` — Recipe node configuration for external augmentation and transformation logic
- `admin/analytics-dataset-management` — Dataset scheduling and row limits that determine data freshness
- `data/einstein-analytics-data-model` — Conceptual XMD layer model and dataset versioning

## Official Sources Used

- CRM Analytics REST API Developer Guide — XMD Resource: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_xmd.htm
- Salesforce Help: CRM Analytics Extended Metadata (XMD): https://help.salesforce.com/s/articleView?id=sf.bi_xmd.htm
- CRM Analytics REST API — Datasets: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_resources_datasets.htm
