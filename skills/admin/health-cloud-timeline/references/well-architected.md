# Well-Architected Notes — Health Cloud Timeline

## Relevant Pillars

- **Security** — The Industries Timeline component respects Salesforce's standard object-level, field-level, and record-level security. Records that the running user cannot read due to profile permissions, field-level security, or sharing rules will not appear on the timeline. Admins must validate that timeline objects have correct OWD settings and sharing rules so clinical staff see the records they are authorized to access — and no others. Sensitive clinical data objects (e.g., `EhrPatientMedication`) must have FLS reviewed for every timeline field referenced in the `TimelineObjectDefinition` (dateField, nameField, descriptionField).

- **Performance** — Each `TimelineObjectDefinition` adds a SOQL query to the timeline component's page load. Orgs with many active definitions (10+) should review query counts and apply selective date range filters on the component if page load time degrades. The timeline renders records within a configurable time window; limiting this window reduces query result set size. Avoid using formula fields or roll-up summary fields as the `dateField` — these are less index-friendly and can cause full table scans on large clinical data objects.

- **Operational Excellence** — `TimelineObjectDefinition` metadata is source-controllable and deployable via SFDX or the Metadata API, making it suitable for standard CI/CD pipelines. Timeline category values, however, are configured in Setup and are not deployable as metadata — they must be managed via destructive post-install scripts or manual Setup steps documented in deployment runbooks. This split between metadata-controlled definitions and Setup-controlled categories is the primary operational complexity to manage.

- **Reliability** — Because timeline category names are not validated at deployment time, category mismatches cause silent data gaps rather than errors. Reliability requires compensating controls: a post-deployment smoke test script that opens 2+ representative patient records and confirms each expected category appears in the filter picklist, and a checker script (see `scripts/check_health_cloud_timeline.py`) that validates category name consistency between the org's category list and deployed definitions.

## Architectural Tradeoffs

**Enhanced Timeline vs. Related Lists:** The Industries Timeline provides a unified chronological view across multiple object types. Related lists provide sortable tabular views of one object at a time. For clinical use cases where care staff need to understand the sequence of events across medication changes, encounters, and care gaps, the timeline is the correct architecture. For administrative use cases where a user needs to bulk-process a specific record type, a related list or custom component is more appropriate. Do not replace related lists with the timeline wholesale — they serve different user tasks.

**Org-Wide Definitions vs. Per-Layout Filtering:** `TimelineObjectDefinition` is org-wide. The primary mechanism for showing different sets of events to different user populations is timeline categories combined with component-level default filter settings. This is less granular than per-layout component configuration but is the supported architecture. Attempts to use custom LWC wrappers to dynamically suppress certain definitions are fragile and unsupported by Salesforce.

**Migration Timing:** Migrating from the legacy `HealthCloud.Timeline` to Industries Timeline requires coordination between the metadata deployment (new definitions), Setup changes (category creation), and page layout changes (component swap). Running both components simultaneously is not safe (see gotchas). A blue-green approach using separate sandbox validation followed by a single production deployment is the recommended migration architecture.

## Anti-Patterns

1. **Configuring the legacy HealthCloud.Timeline component for new use cases** — The legacy component is deprecated. Adding new object types or categories to it locks the org into a dead-end configuration path. Every new timeline requirement should be implemented against the Industries Timeline + `TimelineObjectDefinition` stack, even if the legacy component is still present during a transition period.

2. **Using formula fields or cross-object references as the timeline date field** — `TimelineObjectDefinition.dateField` must be a real date or datetime field on the base object. Formula fields that derive dates from related objects are not supported as the `dateField` and will cause the definition to fail silently or return unexpected ordering. Materialize the date value into a real field on the object if the canonical date lives on a related record.

3. **Skipping relationship path validation before writing TimelineObjectDefinition** — Writing and deploying a `TimelineObjectDefinition` for an object without first confirming the Account relationship path results in an empty timeline entry with no diagnostic signal. Always confirm the Account lookup field name before authoring the metadata.

## Official Sources Used

- Health Cloud Administration Guide — Customize the Timeline View: https://help.salesforce.com/s/articleView?id=sf.admin_network_timeline.htm&type=5
- Life Sciences Cloud Developer Guide — TimelineObjectDefinition: https://developer.salesforce.com/docs/atlas.en-us.life_sciences_dev.meta/life_sciences_dev/life_sciences_timelineobjectdefinition.htm
- Metadata API Developer Guide — TimelineObjectDefinition: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_timelineobjectdefinition.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Object Reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
