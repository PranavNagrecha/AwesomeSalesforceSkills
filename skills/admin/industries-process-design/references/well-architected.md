# Well-Architected Notes — Industries Process Design

## Relevant Pillars

### Reliability

Industry process design is reliability-critical because each vertical depends on external system integrations that can fail independently of Salesforce. E&U service order workflows call external CIS APIs; Communications Cloud technical orders are notifications to provisioning systems; Insurance Claims Management API endpoints handle financial records. Reliable industry process design requires:

- Designing exception paths for every external API callout before the happy path is signed off
- Ensuring service order and claims processes do not silently stall when downstream systems are unavailable
- Testing against production-equivalent external endpoints, not just sandbox mocks
- Building observable failure states: failed service orders, failed CIS callouts, and stalled technical orders must produce actionable signals (Tasks, platform events, or named statuses) that operations staff can act on

### Operational Excellence

Industry processes are long-lived business workflows — an insurance claim may span weeks; a telecom order may involve multi-day provisioning; a utility service connection may require field crew scheduling. Operational excellence in this context means:

- Designing status models with sufficient granularity that operations staff can identify where a case/order is stalled without custom reporting
- Customizing prebuilt industry OmniScript frameworks within Salesforce's supported extension points to preserve upgrade compatibility
- Documenting which stages are prebuilt vs customized so that when Salesforce releases new Claims Management or order management capabilities, the org can adopt them without rework
- Maintaining the decomposition rule configurations and CIS callout mappings as version-controlled metadata rather than ad hoc configuration

### Adaptability

Salesforce Industries clouds evolve rapidly — the Digital Insurance Platform is migrating from managed package to native core; Communications Cloud receives TM Forum-aligned updates; E&U Cloud integrations shift with CIS vendor changes. Adaptable process design means:

- Avoiding deep forks of managed-package OmniScripts that will conflict with future package upgrades
- Keeping business logic in the platform-native configuration layers (OmniScript elements, decomposition rules, service order configuration) rather than in Apex triggers that are harder to upgrade
- Designing integration contracts (CIS API payloads, Claims API calls) as discrete, documented artifacts that can be updated without rebuilding the full process

## Architectural Tradeoffs

**Prebuilt framework customization vs rebuild:** The primary tradeoff in industry process design is between customizing Salesforce's prebuilt OmniScript frameworks and rebuilding the process in a more familiar tool (Screen Flow, Apex). Customization within the framework is harder to learn and constrains design to the framework's data model but preserves integration compatibility, upgrade path, and access to Salesforce-managed API endpoints. Rebuilding in Screen Flow or Apex is faster for developers unfamiliar with OmniStudio but produces a process that cannot access Claims Management APIs, Adjuster's Workbench, or the Industries Order Management lifecycle.

**Declarative decomposition rules vs Apex order orchestration:** For Communications Cloud, declarative decomposition rules in Industries Order Management are the platform-native mechanism for commercial-to-technical order mapping. Apex-based order orchestration can create the correct records but cannot participate in the managed order lifecycle (status callbacks, dependency tracking, retry logic). The decomposition rules approach requires learning a new configuration paradigm; the Apex approach produces a fragile system that requires custom maintenance of what the platform provides natively.

**CIS integration first vs process design first:** For E&U Cloud, designing the service order process before validating the CIS integration is a common sequencing mistake. CIS-first gating adds lead time but eliminates the risk of building a process that fails silently in production.

## Anti-Patterns

1. **Replacing industry OmniScript frameworks with generic Screen Flows** — Industry cloud process frameworks (Claims Management OmniScripts, order capture OmniScripts) are pre-integrated with cloud-specific APIs, data models, and platform components. Replacing them with Screen Flows loses all of these integrations and produces processes that appear functional but cannot drive the downstream financial, fulfillment, or provisioning lifecycle. The anti-pattern is extremely difficult to remediate post-deployment because the data created by the Screen Flow lacks the structural relationships expected by the industry platform.

2. **Designing E&U or Comms process without external system integration contract** — Industry process design that treats Salesforce as the end-to-end system ignores that E&U service orders call CIS APIs, and Communications Cloud technical orders must notify external provisioning systems. A process design that is not scoped to include the external integration contract produces a system that functions within Salesforce but does not produce real-world outcomes (utility service connection, network provisioning). This anti-pattern is discovered at go-live when operations staff realize orders are completing in Salesforce but field crews have no work orders.

3. **Treating Communications Cloud order management and Salesforce Order Management (Commerce) as the same platform** — These are entirely separate platforms with different object models, APIs, namespace, and documentation. Code, configuration, or guidance written for one does not apply to the other. The anti-pattern surfaces as missing field errors, unresolvable object references, and complete absence of decomposition behavior.

## Official Sources Used

- Salesforce Insurance Developer Guide — Claims lifecycle stages, Claims Management API endpoints (POST claims, coverage, payment detail), and data state transitions: https://developer.salesforce.com/docs/atlas.en-us.insurance_dev.meta/insurance_dev/insurance_dev_guide.htm
- Trailhead: Claims Management System Essentials (insurance-claims-foundations/get-to-know-claims-management) — six claims lifecycle stages and FNOL OmniScript framework overview
- Trailhead: Digital Insurance Platform Foundations (digital-insurance-platform-foundations/dive-into-platform-capabilities) — DIP managed-package vs native-core distinction
- Trailhead: OmniStudio OmniScripts Overview (omnistudio-omniscript/learn-the-fundamentals-of-omniscripts) — OmniScript structural requirements and design patterns
- Trailhead: Insurance Claims Management Data Model (insurance-for-financial-services-cloud-data-model/say-hello-to-insurance-claims) — Claim, ClaimParticipant, and financial record relationships
- Salesforce Well-Architected Overview — reliability, operational excellence, and adaptability framing: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Industries Data Models for Communications — EPC and order decomposition object model: https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/industries_comms_data_model.htm
- Energy and Utilities Cloud Developer Guide — service order and CIS integration design: https://developer.salesforce.com/docs/atlas.en-us.eu_dev.meta/eu_dev/eu_dev_guide.htm
