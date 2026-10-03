# Well-Architected Notes: Einstein Analytics Data Model (XMD)

## Relevant Pillars

### Reliability
XMD is a runtime dependency for every dashboard and lens on a dataset. An invalid upload reverts all formatting to defaults, and a schema change can leave stale entries that surface only in `errorMessage`. The back-up, full-document PUT, and post-run `errorMessage` check make recovery a one-step restore.

### Operational Excellence
Formatting that must exist in more than one org belongs in a `WaveXmd` file under source control, deployed and followed by a dataflow run. Formatting edited by hand in each org drifts, and a UI edit makes the next MDAPI retrieve return an empty file.

### Security
`showInExplorer: false` is not an access control. Hidden fields remain reachable through SAQL, dashboard JSON, and the REST API.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Repeatable Operations | Keep the full user XMD JSON or the `WaveXmd` file in version control |
| Configuration as Code | One owner per dataset XMD: source control or the UI, never both |
| Change Management | Schema-changing recipe or dataflow edits include a post-run XMD check |

## Cross-Skill References

- `admin/analytics-dataflow-development`: dataflow runs create new dataset versions and apply the Primary User XMD
- `admin/analytics-recipe-design`: recipe schema changes can break XMD entries
- `admin/analytics-dataset-management`: dataset scheduling decides when new versions appear

## Official Sources Used

- CRM Analytics REST API Developer Guide, Summer '26 (262): "Xmd Resources," "Xmd Resource," "Dataset Resource," "Dataset Versions List Resource," Dataset and Xmd response bodies, Dataset Input (`userXmd`). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_rest.pdf
- Analytics Extended Metadata (XMD) Developer Guide, Summer '26 (262): "Basic Structure of the XMD JSON File," "Packaging Considerations for XMD," "Configure the XMD for a Dataset," "Hide Dataset Fields," "Format the Results of a Query with Multiple Datasets," "Dates in XMD," "Measures and Derived Measures in XMD." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_xmd.pdf
- Metadata API Developer Guide, Summer '26 (262): "WaveXmd" and its subtypes, "WaveDataset." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- CRM Analytics External Data API Developer Guide, Summer '26 (262): "External Data Metadata Format Reference" (field `type`, `precision`, `scale`, `label` limits). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_ext_data.pdf
- CRM Analytics SAQL Developer Guide, Summer '26 (262): "Combine Data from Multiple Data Streams with cogroup." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_dev_guide_saql.pdf
- Object Reference for the Salesforce Platform, Summer '26 (262), and Tooling API Developer Guide (262): searched for a `WaveXmd` object; none exists. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf and https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_tooling.pdf

### Earlier references kept from version 1.0.0 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- CRM Analytics REST API Developer Guide, Wave XMD (atlas page): https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_xmd.htm
- CRM Analytics REST API, Datasets Resource (atlas page): https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_resources_datasets.htm
- Salesforce Help, CRM Analytics Extended Metadata (XMD): https://help.salesforce.com/s/articleView?id=sf.bi_xmd.htm (help.salesforce.com does not return article text to a fetch)
