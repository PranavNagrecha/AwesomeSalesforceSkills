# Well-Architected Notes — Solution Design Patterns

## Relevant Pillars

### Adaptable

The Salesforce Well-Architected Adaptable pillar directly governs automation layer selection. The principle of "clicks before code" — preferring declarative automation over programmatic automation when both can satisfy the requirement — reflects adaptability: declarative solutions are more accessible to a wider team (admins can maintain Flow; only developers can maintain Apex), more resilient to team turnover, and more easily modified without a full deployment cycle.

The automation hierarchy (Flow → Apex → LWC) operationalizes adaptability. Choosing the lowest-complexity layer that satisfies the requirement keeps the solution within reach of the broadest set of maintainers and reduces the blast radius of future changes.

Custom Metadata Types (CMDT) are the adaptability mechanism for configuration. By externalizing routing rules, thresholds, and feature flags into CMDT, the org can change behavior at the configuration layer without touching code or Flow logic — a deployable, versionable, sandbox-safe configuration surface.

### Operational Excellence

Automation designs that mix multiple layers for the same use case (a Flow and an Apex trigger both writing to the same field on the same object) create operational complexity that raises the mean time to diagnose failures. Operational excellence demands that each automation event has a designated owner: one layer responsible for one behavior.

Debug tooling reflects this: Flow has its own debug log, Apex has its own debug log. When both are active in the same transaction for the same behavior, diagnosing a failure requires reconciling two separate log streams. This is avoidable by design.

### Reliability

The order of execution matters for reliability. Before-save Flows run before Apex before triggers. After-save Flows run after Apex after triggers. Designs that rely on implicit timing assumptions between these layers are fragile: a future Flow or trigger addition can shift the behavior. Reliable designs document ownership of each field and each behavior explicitly, reducing dependence on implicit ordering.

Flow governor limits (2,000 elements per interview, shared SOQL and DML limits with Apex) are reliability constraints. A design that pushes Flow to its element limit or that exhausts the shared SOQL budget through uncoordinated queries across Flow and Apex will fail under production volume even when it passes sandbox testing at low data volumes.

## Architectural Tradeoffs

**Flow maintainability vs. Apex flexibility:** Flow is the right default for most automation because it reduces the developer dependency and increases the maintainability surface. The cost is flexibility: Flow cannot make same-transaction callouts, cannot implement complex class-hierarchy-equivalent composition, and cannot unit test with assertion frameworks. When these constraints block the requirement, escalate to Apex — but only for the part of the requirement that Flow cannot satisfy.

**LWC custom UI vs. standard components:** Standard Lightning components are supported, documented, and maintained by Salesforce across releases. Custom LWC components are owned by the org's team indefinitely. Build a custom LWC when there is a documented gap in standard component capability for a specific user requirement — not as a default preference. The maintenance cost of a custom component compounds over years.

**Platform Events for layer decoupling:** When a requirement needs declarative logic (manageable by admins) combined with a callout (requires Apex), Platform Events are the decoupling mechanism. Flow fires the event; Apex consumes it. This prevents callout restrictions from forcing all logic into Apex while keeping the transaction boundary clean.

## Anti-Patterns

1. **Hard-coded Salesforce record IDs in Flow conditions or Apex code.** Record IDs are org-specific and change between production and sandbox. Any design that hard-codes IDs is a deployment failure waiting to happen. Use Custom Metadata Types, Custom Labels, or dynamic lookups.

2. **Using Process Builder or Workflow Rules for new automation.** Process Builder is scheduled for deprecation; Workflow Rules were deprecated in Summer '23. Building new automation in deprecated tools creates guaranteed future rework. All new automation starts in Flow.

3. **Two automations owning the same field or behavior on the same object.** When a Record-Triggered Flow and an Apex trigger both write to the same field, the execution order determines the final value — and that order is non-obvious and can shift when new automation is added. Assign one canonical owner per field and per behavior.

4. **Putting SOQL queries inside Flow loops.** Each Get Records element inside a Flow loop body issues a SOQL query per iteration. A loop over 150 records issues 150 SOQL queries, exhausting the transaction limit. Query outside the loop, filter the collection in memory.

5. **Over-engineering with LWC when standard UI suffices.** Custom components require JavaScript testing, wire adapter maintenance, and ongoing updates as Salesforce APIs evolve. Build a custom LWC only when a specific, documented standard component gap exists for the user requirement.

## Official Sources Used

- Salesforce Well-Architected — Adaptable: Automation — https://architect.salesforce.com/well-architected/adaptable/automation — primary authority for automation layer selection, "clicks before code" principle, and adaptability framing
- Salesforce Architects: Decision Guide — Build Forms — https://architect.salesforce.com/design/decision-guides/build-forms — declarative vs. programmatic decision framework
- Apex Developer Guide — Order of Execution — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm — authoritative execution order for triggers, flows, and validation rules
- Flow Considerations (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.flow_considerations.htm — Flow governor limits, callout restrictions, and element count limits
