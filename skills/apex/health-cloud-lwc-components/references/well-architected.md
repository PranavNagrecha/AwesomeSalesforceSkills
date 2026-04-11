# Well-Architected Notes — Health Cloud LWC Components

## Relevant Pillars

- **Security** — Clinical LWC Apex controllers access PHI. All Apex controllers must enforce FLS (field-level security) for clinical fields. Debug log policies must prevent clinical data exposure. Custom LWCs on patient records must not cache PHI in localStorage or browser storage.
- **Operational Excellence** — Patient card and timeline configurations are metadata-driven, not code-driven. Declarative configurations (Health Cloud Setup, TimelineObjectDefinition) are more maintainable and upgradable than code-based overrides. Prefer declarative approaches for all Health Cloud component configurations.
- **Reliability** — Custom clinical LWC components that query clinical objects must handle empty results gracefully (patients with no conditions, no encounters). Missing null checks on clinical data queries are a common source of component runtime errors.

## Architectural Tradeoffs

**Declarative vs. Custom LWC for Timeline/Patient Card:** TimelineObjectDefinition and Health Cloud Setup > Patient Card Configuration provide declarative configuration that is maintainable through Salesforce upgrades. Custom LWC components that replicate timeline or patient card functionality add maintenance overhead and are not upgraded automatically. Prefer declarative configuration whenever it meets the requirements.

**Apex Controller vs. Wire Service for Clinical Queries:** Apex controllers with `@AuraEnabled(cacheable=true)` are appropriate for most clinical data queries. Wire service with standard Lightning Data Service cannot query clinical objects by arbitrary filter criteria (e.g., `WHERE PatientId = :recordId`) — use Apex controllers for filtered clinical queries.

## Anti-Patterns

1. **Extending Patient Card via App Builder slot injection** — the component does not support this pattern. All patient card field additions must go through Health Cloud Setup.
2. **Storing clinical data in Account fields for component display** — clinical UI components query clinical objects, not Account fields. Data in Account fields is never consumed by PatientCard, Timeline, or clinical components.
3. **Using legacy HC timeline configuration for new timeline entries** — the legacy timeline is deprecated. All new configuration should use TimelineObjectDefinition for the Industries Timeline.

## Official Sources Used

- Health Cloud Administration Guide (help.salesforce.com): https://help.salesforce.com/s/articleView?id=ind.hc_admin.htm
- Health Cloud Developer Guide — TimelineObjectDefinition: https://developer.salesforce.com/docs/atlas.en-us.health_cloud.meta/health_cloud/hco_dev_timeline_object_definition.htm
- TimelineObjectDefinition Object Reference (API v55.0+): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_timelineobjectdefinition.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
