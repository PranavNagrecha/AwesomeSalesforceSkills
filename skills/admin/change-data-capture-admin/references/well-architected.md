# Well-Architected Notes — Change Data Capture Admin

## Relevant Pillars

- **Reliability** — CDC delivery has hard per-edition daily limits (50K/25K/10K events/24h). When the daily allocation is exhausted, event delivery halts silently with no subscriber-side error. Reliable CDC admin requires proactive monitoring of `PlatformEventUsageMetric`, alerting before the cap is hit, and channel topology that minimizes per-subscriber delivery consumption. The 72-hour event retention window also imposes a reliability constraint: any downstream consumer that is offline for more than 72 hours cannot recover via CDC replay alone and requires a Bulk API re-sync.

- **Security** — Entity selection determines which records' field changes flow to CDC subscribers. Enabling a highly sensitive object (e.g., one containing PII or compensation data) without reviewing who subscribes to the receiving channel creates unintended data exposure. Enriched fields amplify this risk: an enriched field on a change event may expose data the subscriber was not originally authorized to receive. Security review of enriched field lists and channel subscriber lists is a required step before production deployment.

- **Performance** — The number of active subscribers and the breadth of enabled entities directly affect CDC delivery allocation consumption, which is shared across the org. Poorly scoped channel subscriptions (many subscribers on a wide entity set) consume delivery allocation at multiples of the event publication rate, leaving less headroom for other integrations. Custom channels with narrow entity sets and server-side filtering reduce the per-subscriber delivery impact.

- **Scalability** — The default 5-entity limit and edition-based delivery caps constrain CDC scale. Growth plans must account for these limits: reaching the entity cap silently prevents new entity selections from taking effect. The CDC add-on removes the entity cap and shifts billing to a monthly volume model, enabling large-scale deployments. Custom channel topology (multiple isolated channels) also improves scalability by distributing delivery load across subscriber groups.

- **Operational Excellence** — Custom channel configuration (PlatformEventChannel, PlatformEventChannelMember, EnrichedField) is not visible in the Setup UI and is not tracked in version control unless explicitly included in the Metadata API deployment package. Orgs that manage CDC configuration ad hoc via Tooling API queries accumulate untracked drift. Operational excellence requires all channel metadata in source control, documented entity-to-channel mapping, and regular Tooling API audits.

## Architectural Tradeoffs

**Default channel vs custom channels:** The default `ChangeEvents` channel is the fastest path to production and requires no deployment. However, it provides no subscriber isolation — every subscriber receives every enabled entity's events, and every subscriber consumes the full per-event delivery allocation independently. As subscriber count or entity volume grows, the shared-channel model exhausts the daily allocation. Custom channels require more upfront configuration but provide server-side filtering and reduce per-subscriber consumption.

**Enrichment vs follow-up REST queries:** Enrichment reduces latency and REST API consumption for subscribers that need contextual fields not included in the changed-field set. The tradeoff is configuration complexity (custom channel required), enrichment field review for security (every enriched field broadens what the subscriber can see), and the constraint that formula fields cannot be enriched. Follow-up REST queries preserve a simpler channel configuration but increase per-event latency and API call consumption.

**Setup UI management vs Metadata API management:** Setup UI changes to the default channel are immediate and require no deployment. However, they are not tracked in source control unless the team manually documents them, creating audit risk. Metadata API management of all channel members (including the default channel) enables version control and CI/CD deployment at the cost of deployment overhead.

## Anti-Patterns

1. **Auditing CDC coverage via the Setup UI alone** — The Setup page shows only the default `ChangeEvents` channel. Custom channels and Data Cloud's `DataCloudEntities` channel are invisible. Any compliance or troubleshooting audit that relies only on the Setup UI will produce an incorrect baseline and may lead to inadvertent misconfiguration.

2. **Modifying the DataCloudEntities channel directly** — Removing or changing `PlatformEventChannelMember` records in the `DataCloudEntities` channel via Metadata API or Tooling API breaks Data Cloud CRM Data Stream sync without surfacing an immediate error. The correct administrative boundary is to treat this channel as Data Cloud-owned and manage it exclusively through Data Cloud CRM Data Stream configuration.

3. **Adding enrichment to standard per-object channels** — Configuring `EnrichedField` records on standard per-object channel members (e.g., `/data/AccountChangeEvent`) produces no error but delivers no enriched fields. This is a silent misconfiguration that wastes effort and leaves the subscriber issuing unnecessary follow-up REST queries.

## Official Sources Used

- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Change Data Capture: Entity Selection — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_select_objects.htm
- PlatformEventChannel Metadata — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_platformeventchannel.htm
- PlatformEventChannelMember Metadata — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_platformeventchannelmember.htm
- PlatformEventUsageMetric Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_platformeventusagemetric.htm
- Change Data Capture: Event Enrichment — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_enriched_fields.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
