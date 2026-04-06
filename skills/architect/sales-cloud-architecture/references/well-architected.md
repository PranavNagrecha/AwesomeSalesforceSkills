# Well-Architected Notes — Sales Cloud Architecture

## Relevant Pillars

- **Scalability** — Sales Cloud architectures must handle growth in record volume (leads, opportunities, activities), user count, and automation complexity without redesign. Territory hierarchies, sharing calculations, and forecast rollups all degrade nonlinearly as scale increases. The architecture should document explicit volume thresholds and have a plan for each growth stage.

- **Performance** — Every Opportunity save fires the full order of execution: validation rules, before-save Flows, before triggers, after triggers, after-save Flows, assignment rules, and sharing recalculation. An architecture that allows multiple automations to compete on the same object and timing slot multiplies query counts and extends save latency. Sub-2-second save times require deliberate automation consolidation and lazy-loading query patterns.

- **Reliability** — Sales Cloud integrations with ERP, commission, and marketing systems must handle downstream failures gracefully. If an ERP callout fails during Opportunity close, the architecture must decide: block the save (unacceptable UX), silently drop the event (data loss), or queue for retry (Platform Events). Reliability requires explicit error handling contracts at every integration boundary.

- **Operational Excellence** — Sales processes change quarterly: new stages, revised approval thresholds, territory realignment. The architecture must support these changes declaratively (Flow, Custom Metadata, custom settings) without requiring developer deployments for every business rule change. Operational excellence also means the automation map is documented so that any admin can trace what fires when.

## Architectural Tradeoffs

### Declarative-First vs. Code-First Automation

Declarative automation (Flows) is faster to modify and does not require deployment pipelines. However, Flows have per-element governor limits, limited bulkification control, and no native unit testing. The tradeoff: use Flows for simple, single-object logic that business analysts may need to modify; use Apex for cross-object transactions, complex branching, and any logic that requires unit test coverage for compliance. Reference: Layered Automation Ownership pattern in SKILL.md.

### Synchronous vs. Asynchronous Integration

Synchronous callouts provide immediate confirmation but couple the CRM transaction to external system availability. Asynchronous patterns (Platform Events, Change Data Capture) decouple the systems but introduce eventual consistency — the ERP may not reflect the closed-won opportunity for seconds or minutes. The tradeoff: use synchronous only for interactions where the user needs immediate feedback (price validation, credit check); use asynchronous for everything else. Reference: Integration Facade with Platform Events pattern in SKILL.md.

### Standard Object Extension vs. Custom Object Creation

Extending Opportunity with record types and custom fields preserves compatibility with Forecasting, Pipeline Inspection, and Einstein features. Creating custom objects provides a clean schema but loses all standard feature integration. The tradeoff: extend standard objects unless the entity genuinely has a different lifecycle and cardinality (e.g., Deal Desk Approvals, Sales Play Assignments). Reference: Anti-Pattern in examples.md.

## Anti-Patterns

1. **Monolithic trigger without domain separation** — A single Apex trigger on Opportunity that contains all business logic in one class with no handler separation. This makes the trigger untestable in isolation, impossible to maintain across teams, and creates merge conflicts. Instead, use a dispatcher pattern that routes to domain-specific handler classes.

2. **Over-reliance on roll-up summary fields for reporting** — Using roll-up summary fields on Account for every KPI (total pipeline, win rate, average deal size, last activity date) consumes the 25-field limit quickly and creates lock contention during bulk updates. Instead, use scheduled batch Apex or reporting snapshots for aggregates that do not require real-time accuracy.

3. **Sharing model as an afterthought** — Designing the entire data model and automation layer before considering OWD settings, sharing rules, and territory-based sharing. Retrofitting a restrictive sharing model after go-live requires rearchitecting record access patterns and can break existing reports and dashboards. Instead, define the sharing model in the architecture phase alongside the data model.

## Official Sources Used

- Salesforce Sales Cloud Overview — https://help.salesforce.com/s/articleView?id=sf.sales_core.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
- Salesforce Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Order of Execution — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Enterprise Territory Management — https://help.salesforce.com/s/articleView?id=sf.tm2_intro.htm
