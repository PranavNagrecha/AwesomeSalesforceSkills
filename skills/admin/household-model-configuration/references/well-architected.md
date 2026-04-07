# Well-Architected Notes — Household Model Configuration

## Relevant Pillars

- **Reliable** — The FSC household rollup model has two execution paths (real-time triggers and scheduled batch jobs). A reliable implementation ensures both paths are configured, tested, and monitored. Relying solely on trigger-based rollups without a batch fallback creates a reliability gap: bulk data loads can exhaust trigger capacity, leaving household totals stale until the next save event. Always configure the batch rollup job and schedule it to run nightly.
- **Adaptable** — The FSC household model is extensible via the `Rollups__c` picklist. Adding rollup support for new object types (custom financial objects, insurance products, CPQ quotes) requires adding picklist values rather than code changes. This is an intentional extensibility point. Designing household configurations to leverage this picklist keeps the model adaptable to business changes without Apex deployment.
- **Trusted** — Access to household financial aggregations is sensitive. The Household Account record's rollup fields should be protected by field-level security (FLS) profiles and permission sets. ACR records should only be modifiable by users with explicit permissions — household membership changes (adding/removing members, toggling `FinServ__IncludeInGroup__c`) directly affect financial aggregations and should be audited via field history tracking.
- **Performant** — The real-time rollup trigger runs synchronously on every financial account save. In high-volume orgs with large households (many members, many financial accounts), this can contribute to governor limit pressure. The batch rollup job is designed for bulk scenarios and should be used for mass data loads rather than triggering recalculations via individual record saves.
- **Operational Excellence** — Documenting the org's `Rollups__c` picklist state, the batch schedule, and the ACR field conventions is essential for maintainability. FSC orgs that go through releases without documentation of which picklist values exist (and which do not) routinely encounter the "missing rollup values for new object types" problem in production.

## Architectural Tradeoffs

**Real-time triggers vs. batch rollup job:** Real-time triggers provide immediate consistency for single-record operations (an advisor adds a financial account; the household balance updates instantly). The batch job provides recovery for bulk operations and mass corrections. The tradeoff is that running the batch job too frequently can generate excessive Apex job history and compete with other scheduled processes. Running it too infrequently means household totals can lag after bulk data changes. Nightly scheduling is the standard recommendation; some orgs with real-time reporting requirements run the batch on a shorter cadence.

**Single primary group vs. multiple group membership:** A Person Account can belong to multiple households (e.g., an individual with a personal household and a joint household with a spouse). The `FinServ__PrimaryGroup__c` flag determines which household is "primary" for display and certain rollup defaults. The tradeoff is complexity: the more households an individual belongs to, the more ACR records must be maintained and the more rollup calculations fire on each financial account change. For high-relationship orgs (family offices, multi-generational wealth management), this can be significant. Consider limiting the number of household memberships per individual and documenting the business rule.

**Extensibility via `Rollups__c` picklist:** Adding picklist values is low-risk and reversible. However, each new value adds to the rollup engine's computational scope. Large orgs with many custom object types in the `Rollups__c` picklist may see batch rollup job performance degrade as the scope grows. Periodically audit which picklist values are actually generating rollup data and remove values for object types with no active records.

## Anti-Patterns

1. **Mixing FSC and NPSP household models in the same org** — NPSP installs its own rollup triggers that conflict with FSC's ACR-based rollup engine. Both systems attempt to write to the same Account rollup fields using different source data, producing non-deterministic results. The correct approach is to use one household model for the entire org; FSC orgs should not have NPSP installed unless a formal migration and isolation plan is in place with Salesforce support.

2. **Relying on trigger-based rollups alone without scheduling the batch job** — Real-time triggers handle normal operation well but do not recover from bulk data loads, failed transactions, or situations where `FinServ__IncludeInGroup__c` is toggled retroactively. Orgs without a scheduled batch rollup job accumulate stale household totals over time and typically discover the problem only during audits or client complaints. The batch job is a required component of any production FSC deployment, not optional infrastructure.

3. **Creating ACR records without auditing `Rollups__c` picklist completeness first** — Building out the household membership model and then discovering that rollup data is absent for key object types (Cases, Insurance Policies, Opportunities) leads to reactive fixes that require running the batch job in production. The better architectural approach is to audit and complete the `Rollups__c` picklist before populating any household membership records, so the first rollup run reflects a complete data model.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- FSC Admin Guide: What Is a Group? — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_groups_overview.htm
- FSC Admin Guide: Configure Record Rollups — https://help.salesforce.com/s/articleView?id=sf.fsc_admin_rollups.htm
- FSC Object Reference: AccountContactRelation FSC Fields — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_obj_accountcontactrelation.htm
- FSC Trailhead: Configure Record Rollups — Group Level Opportunities — https://trailhead.salesforce.com/content/learn/modules/fsc-rollups/configure-group-level-rollups
- FSC Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_intro.htm
