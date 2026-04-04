# Well-Architected Notes — Platform Selection Guidance

## Relevant Pillars

### Operational Excellence

Platform feature selection is fundamentally an operational excellence decision. Choosing Custom Metadata Types over Custom Settings means the team can deploy configuration changes through standard release pipelines without manual data seeding. Choosing LWC over Aura means the team is building on a framework that receives active platform investment, security updates, and new API support — reducing the operational burden of maintaining components against a moving platform.

The operational cost of a wrong platform choice compounds over time. A Custom Settings-based configuration store that should have been Custom Metadata Types accumulates manual deployment steps with every release. An Aura component portfolio that grows instead of migrates becomes an increasingly expensive maintenance liability as the platform evolves features exclusively for LWC.

Operational excellence at the platform selection layer means choosing features whose operational characteristics — deployability, maintainability, tooling support — match the team's release cadence and skill profile. The right feature for the requirement is the one the team can operate reliably across its full lifecycle, not just build initially.

### Reliability

Platform feature selection affects reliability through two mechanisms: feature longevity and runtime behavior.

**Feature longevity:** Deprecated or legacy features are reliability risks. Outbound Messaging tied to Workflow Rules was a reliable integration pattern — until Workflow Rules were retired. Teams that built integrations on Outbound Messaging faced forced migration under time pressure. Aura components built after 2022 represent investment in a framework that receives no new platform capabilities. Choosing strategic features — those on Salesforce's active investment roadmap — reduces the risk that a platform deprecation event forces emergency rework.

**Runtime behavior:** Custom Metadata Types load from the metadata cache, reducing SOQL query overhead compared to Custom Object queries for configuration reads in high-transaction contexts. Change Data Capture provides at-least-once delivery semantics within the retention window. Platform Events have a 72-hour replay window but no auto-retry to external endpoints. These runtime characteristics must match the reliability requirements of the use case.

## Architectural Tradeoffs

**Deployability vs. flexibility for configuration storage:** Custom Metadata Types are the most deployable configuration storage — records travel with the code in standard release pipelines. The cost is inflexibility: no relationships to standard sObjects, no hierarchy (per-user/per-profile), and a practical record volume ceiling well below what a Custom Object can handle. Accepting the CMT constraint is the right trade for most configuration use cases because deployability reduces operational risk across the org's entire release lifecycle.

**Strategic investment vs. team familiarity for UI framework:** Aura is familiar to teams that have been on the Salesforce platform since 2014. LWC is the current standard but requires JavaScript skills that some admin-heavy teams lack. The right choice is LWC for all new development — not because Aura is broken, but because building new investment in a legacy framework defers migration cost and interest accrues. If the team lacks LWC skills, the right answer is skill development, not continued Aura investment.

**Native platform integration patterns vs. middleware:** Platform Events and Change Data Capture are native Salesforce integration patterns. They reduce infrastructure overhead (no middleware required for publish/subscribe). The cost is that delivery guarantee semantics are limited to the replay window. For integrations where guaranteed delivery to external endpoints is a hard requirement, middleware (MuleSoft, Boomi) provides the additional reliability layer at the cost of infrastructure complexity.

**OmniStudio guided experience vs. Screen Flow + LWC:** OmniStudio OmniScript is purpose-built for complex guided journeys with multiple data sources and branch logic. Screen Flow + LWC can achieve similar outcomes but requires more build effort per journey. The tradeoff is license cost vs. build cost. For orgs with OmniStudio included (Salesforce Industries clouds), the license cost is sunk; OmniStudio wins for complex guided use cases. For orgs without the license, Screen Flow + LWC is the correct default.

## Anti-Patterns

1. **Using Custom Settings (List type) for new deployable configuration.** List Custom Settings offer no hierarchy support and carry the same deployment liability as Hierarchy Custom Settings. There is no reason to choose Custom Settings over Custom Metadata Types for new configuration design.

2. **Building new Aura components.** Every new Aura component is technical debt from day one. The platform does not add new Aura-only capabilities. New LWC capabilities (Slack, Mobile, Experience Cloud features) are not available to Aura components. Building new Aura is a choice to carry legacy overhead indefinitely.

3. **Using Outbound Messaging for new integrations.** Outbound Messaging requires Workflow Rules, which are retired. Any new Outbound Message configuration requires an active Workflow Rule to trigger it — a retired feature. Migrate to Platform Events.

4. **Assuming CDC and Platform Events are interchangeable.** CDC is for record-change synchronization. Platform Events are for application-level event publishing. Conflating them leads to designs where Platform Events manually replicate what CDC provides natively (unnecessary publisher code) or where CDC is misused for non-record-change events (semantic confusion and incorrect field-delta assumptions).

5. **Adopting OmniStudio without validating license inclusion.** OmniStudio is not included in all Salesforce editions. Building an OmniScript-based guided experience in a sandbox environment that has OmniStudio provisioned, then discovering the production org license does not include it, creates a deployment blocker. Always verify license inclusion before beginning OmniStudio design.

## Official Sources Used

- Custom Metadata Types (Metadata API Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custommetadata.htm — authority for CMT deployment semantics, record structure, and Metadata API coverage
- Lightning Web Components Developer Guide — https://developer.salesforce.com/docs/component-library/documentation/en/lwc — authority for LWC capabilities, Lightning Message Service, and Aura interoperability
- Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm — authority for Platform Events publish/subscribe model, retention windows, and replay semantics
- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm — authority for CDC event model, field-delta payload, retention windows, and Shield extensions
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/well-architected/operational-excellence — framing for deployment simplicity, maintainability, and release pipeline design
- Salesforce Well-Architected — Reliability — https://architect.salesforce.com/well-architected/reliability — framing for feature longevity, deprecation risk, and runtime behavior reliability
- Salesforce Architects: Decision Guide — https://architect.salesforce.com/design/decision-guides — platform feature selection framing and architectural tradeoff analysis
