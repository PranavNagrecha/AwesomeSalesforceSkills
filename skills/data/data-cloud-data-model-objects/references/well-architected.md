# Well-Architected Notes — Data Cloud Data Model Objects

## Relevant Pillars

### Operational Excellence

DMO design is a foundational architecture decision in Data Cloud. Changes to DMO schema after deployment are constrained: field API names cannot be changed, and relationships are limited to one per field pair. Operational excellence requires thorough schema design before go-live, with XMD customization planned for field label management without API name changes.

### Reliability

Five mandatory DMOs must be mapped correctly for identity resolution to function. Missing or incomplete mandatory DMO mappings silently disable identity resolution for that data source with no error message. Reliability requires validating mandatory DMO coverage after every new data stream onboarding.

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Operational Excellence | Design DMO schema thoroughly before deployment; plan XMD customization for label management |
| Reliability | Validate mandatory DMO coverage after each new data stream; test identity resolution with each new source |
| Security | Data Cloud field-level security applied at the Data Space and permission set level, not at the DMO field level |
| Performance | Streaming transforms for single-source near-real-time; batch transforms for joins and aggregations |

---

## Cross-Skill References

- `data/data-cloud-data-streams` — For configuring DLO ingestion and DLO-to-DMO field mapping
- `admin/data-cloud-identity-resolution` — For identity resolution ruleset and matching rule design
- `admin/data-cloud-segmentation` — For building segments that query unified DMO profiles
- `architect/data-cloud-architecture` — For overall Data Cloud platform architecture

---

## Official Sources Used

- Model Data in Data Cloud — Data 360 DMO and Mapping Guide: https://developer.salesforce.com/docs/data/data-cloud-dmo-mapping/guide/c360dm-model-data.html
- Standard Data Model Objects — Data 360 DMO and Mapping Guide: https://developer.salesforce.com/docs/data/data-cloud-dmo-mapping/guide/c360dm-datamodelobjects.html
- WaveXmd Metadata API Reference: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_wavexmd.htm
- Data Cloud Query API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_query.htm
- Learn How Data Cloud Works (Data 360 lifecycle: Connect → Transform and Model/harmonize → Unify → Analyze and Act): https://trailhead.salesforce.com/content/learn/modules/data-cloud-powered-experiences/learn-how-data-cloud-works
- Map and Unify Data (DLO-to-DMO harmonization mapping, fully qualified keys): https://trailhead.salesforce.com/content/learn/modules/data-cloud-connect-and-unify/map-and-unify-data
- Explore the Stages of Data Cloud (data prep and transformations as a lifecycle stage): https://trailhead.salesforce.com/content/learn/modules/data-cloud-explore-the-data-landscape/explore-the-stages-of-data-cloud
- Get Started with Batch Data Transforms in Data 360 (visual editor, node types, Output to DLO/DMO, Data 360 rebrand): https://trailhead.salesforce.com/content/learn/modules/batch-data-transforms-in-data-cloud-quick-look/get-started-with-batch-data-transforms-in-data-360
- Get Started with Streaming Data Transforms in Data Cloud (near-real-time enrichment, batch vs. streaming scope): https://trailhead.salesforce.com/content/learn/modules/streaming-data-transforms-quick-look/get-started-with-streaming-data-transforms-in-data-cloud
- Run Batch Transform Flow action reference: https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_actions_run_batch_transform.htm&language=en_US&type=5
