# Well-Architected Notes — Analytics Data Preparation (XMD)

## Relevant Pillars

### Reliability
XMD metadata directly affects how datasets render in dashboards. Each XMD upload overwrites the previous customizations, and an invalid upload reverts all formatting to defaults, so a backup before every write is the only undo.

### Operational Excellence
External CSV augmentation should be treated as a managed data source with a documented refresh process, not as a one-time upload. Operational excellence requires that all data sources have a defined owner and refresh cadence.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Repeatable Operations | Deployable formatting lives in WaveXmd (Primary User XMD) in source control, followed by a dataflow run; version-bound user XMD changes are for one-off fixes |
| Data Freshness | External CSV sources need explicit refresh processes to avoid stale data |
| Auditability | Main XMD backups provide a record of the state before each modification |

## Cross-Skill References

- `admin/analytics-recipe-design` — Recipe node configuration for external augmentation and transformation logic
- `admin/analytics-dataset-management` — Dataset scheduling and row limits that determine data freshness
- `data/einstein-analytics-data-model` — Conceptual XMD layer model and dataset versioning

## Official Sources Used

Read for this revision (2026-10-03):

- CRM Analytics REST API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_rest.pdf. Xmd Resources (Xmd List, Xmd Resource with GET and PUT on user type only, Asset Xmd); Dataset Resource (GET, DELETE, PATCH) and Dataset Input `userXmd`; Xmd type enumeration (asset, main, system, user).
- Analytics Extended Metadata (XMD) Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_xmd.pdf. XMD overview (dataset-wide effect), Basic Structure (no empty strings, dataset block), Packaging Considerations (Standard versus Primary User XMD, MDAPI retrieve behaviour), Configure the XMD (overwrite on upload, permissions, renamed fields), hidden fields note, Format Measures (customFormat), multi-dataset formatting.
- Analytics External Data API Developer Guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_ext_data.pdf. Limits, InsightsExternalData and InsightsExternalDataPart fields, numberOfLinesToIgnore, metadata format reference (defaultValue, isUniqueId, precision, scale, field name restrictions).
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. WaveXmd (suffix, folder, fields, type values, sample with the `<dimesions>` typo), WaveXmdDimension, WaveXmdDimensionMember, WaveXmdMeasure.
- Salesforce Object Reference, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf. Searched for a WaveXmd object; none is listed.

Listed in the original version and not re-read:

- CRM Analytics REST API Developer Guide, XMD Resource (atlas page): https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_xmd.htm (same guide read as PDF above).
- Salesforce Help: CRM Analytics Extended Metadata (XMD): https://help.salesforce.com/s/articleView?id=sf.bi_xmd.htm (Salesforce Help does not fetch).
- CRM Analytics REST API, Datasets (atlas page): https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_resources_datasets.htm (same guide read as PDF above).
