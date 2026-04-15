---
name: industries-process-design
description: "Use when designing or customizing industry-specific guided processes in Salesforce Industries clouds: insurance claims lifecycle (FNOL through closure), telecom order management decomposition, and utility service request workflows. Trigger keywords: FNOL process design, claims OmniScript customization, Industries order decomposition workflow, utility service order design, insurance claim lifecycle stages, telecom commercial-to-technical order flow. NOT for generic Screen Flow process design, standard Service Cloud Case workflows, OmniStudio runtime setup, EPC service catalog configuration, or initial cloud org activation."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I customize the insurance FNOL claim intake process in Salesforce Insurance Cloud"
  - "designing the insurance claims lifecycle OmniScript stages from intake through closure"
  - "telecom commercial order to technical order decomposition flow design in Communications Cloud"
  - "configuring the service request workflow for utility connect and disconnect orders in E&U Cloud"
  - "insurance adjuster workbench process steps and how to customize them for our line of business"
  - "how does the TM Forum order decomposition process work in Industries Order Management"
  - "designing service order process stages for energy utility provider customer requests"
tags:
  - industries
  - insurance-cloud
  - communications-cloud
  - energy-utilities-cloud
  - omniscript
  - claims-management
  - order-management
  - service-order
  - process-design
  - fnol
inputs:
  - "Industry vertical in scope: Insurance (FSC), Communications Cloud, or Energy and Utilities Cloud"
  - "Whether Insurance Cloud includes the Claims Management module license (distinct from base FSC Insurance)"
  - "Whether Communications Cloud has OmniStudio licensed for process capture UIs"
  - "External CIS or billing system integration status for E&U (required before service order design)"
  - "Business process description: which lifecycle stages exist, user roles per stage, branching conditions"
  - "Customization scope: which prebuilt OmniScript stages need modification vs which need to be built new"
outputs:
  - "Industry process design blueprint identifying prebuilt vs custom stages per vertical"
  - "OmniScript stage inventory for insurance claims lifecycle (FNOL through closure)"
  - "Order decomposition rule design document for Communications Cloud (commercial to technical order)"
  - "Service order process design for E&U Cloud with CIS integration dependency map"
  - "Decision table: which process runtime applies per vertical and what cannot be replaced by generic Flow"
dependencies:
  - industries-insurance-setup
  - industries-communications-setup
  - industries-energy-utilities-setup
  - omniscript-flow-design-requirements
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# Industries Process Design

This skill activates when a practitioner needs to design, map, or customize industry-specific business process flows across Salesforce Industries clouds — covering the insurance claims lifecycle (FNOL intake through financial closure), telecom commercial-to-technical order decomposition in Communications Cloud, and utility service request workflows in Energy and Utilities Cloud. It produces process design blueprints that account for the prebuilt industry OmniScript frameworks, the declarative decomposition rule engines, and the external system integration dependencies that govern when industry processes can execute.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the correct license for the cloud in scope.** Insurance process design requires the Claims Management module license (separate from base FSC Insurance). Communications Cloud process design requires both the Communications Cloud package and OmniStudio. E&U Cloud service order design requires the E&U Cloud package and, critically, a functional CIS integration — service orders trigger automated CIS API callouts and will fail at runtime if the integration is not active.
- **Identify the prebuilt OmniScript framework before designing custom stages.** Each industry vertical ships prebuilt OmniScript-based process flows. The most common and costly mistake is assuming these must be rebuilt from scratch. Salesforce ships prebuilt FNOL OmniScript guided flows for Insurance Cloud covering six lifecycle stages; Communications Cloud ships TM Forum-aligned decomposition flows; E&U Cloud ships service order workflows with CIS callout steps. The design task is customization, not reconstruction.
- **Process runtime differs per vertical.** Insurance process design runs on the Claims Management OmniScript framework within FSC. Communications Cloud process design centers on Industries Order Management declarative decomposition rules (not Flows, not Apex). E&U process design uses service order records plus CIS callout automation. Designing one vertical's process using another vertical's runtime tooling produces solutions that cannot be activated or deployed.

---

## Core Concepts

### Insurance Claims Lifecycle: Prebuilt OmniScript Framework on FSC

Salesforce Insurance Cloud (within FSC) ships a prebuilt claims management framework based on OmniScripts. The claims process is not a single monolithic OmniScript — it is structured across six lifecycle stages, each implemented as a separate OmniScript or OmniScript step group:

1. **FNOL (First Notice of Loss) intake** — the initial claim report. The prebuilt FNOL OmniScript collects incident details, policy number, claimant information, and initial loss description. It creates the `Claim` record and links it to the `InsurancePolicy`.
2. **Segmentation and assignment** — routes the claim to the appropriate handler (catastrophe queue, standard adjuster, or automated settlement pathway) based on loss type, coverage type, and claim complexity rules.
3. **Workload management** — the adjuster's queue management interface for tracking open claims by status, reserve amounts, and SLA timers.
4. **Investigation** — the adjuster-facing OmniScript steps for recording site inspections, witness statements, third-party reports, and liability assessments against `Claim` and `ClaimParticipant` records.
5. **Financials via Adjuster's Workbench** — reserve setting, coverage validation against `InsurancePolicyCoverage`, deductible calculation, and payment authorization. The Claims Management API endpoints (`POST /connect/insurance/claims/{claimId}/coverages`, `POST /connect/insurance/claims/coverages/{claimCoverageId}/payment-details`) are the programmatic path for financial actions.
6. **Closure** — final status update, subrogation and salvage recording, closure reason selection, and claimant notification.

Customization work targets individual stage OmniScripts — adjusting screen elements, branching conditions, and Remote Action calls — not the overall framework architecture. Rebuilding the framework from scratch discards Salesforce's prebuilt claims data integration logic and voids upgrade compatibility.

### Communications Cloud: TM Forum Order Decomposition (Declarative, Not Flow)

Communications Cloud implements TM Forum SID TR139-aligned order decomposition. The core design artifact is not a Flow or an OmniScript — it is a **decomposition rule configuration** in Industries Order Management.

When a subscriber places a commercial order (an Order record with OrderItem records referencing EPC Product Offerings), the Industries Order Management engine reads the EPC child item definitions and applies decomposition rules to generate technical order records in the `vlocity_cmt` namespace. The process design task is:

1. **Define the commercial-to-technical mapping**: for each commercial product offering (e.g., "Broadband 100Mbps Bundle"), specify the atomic technical fulfillment actions (provision broadband circuit, activate CPE equipment, configure voice port) as technical order line items.
2. **Configure decomposition rules**: these are declarative configuration records in Industries Order Management, not Apex code and not standard Flows. They reference EPC child item relationships to determine what technical order items to generate.
3. **Design the orchestration sequence**: technical order items may have dependencies — broadband circuit provisioning must precede CPE activation. Dependency sequencing is configured in the decomposition rule set, not in a separate workflow tool.

Industries Order Management is NOT Salesforce Order Management (B2C/B2B Commerce). See the Gotchas section for the consequences of conflating these two platforms.

### E&U Cloud: Service Order Process Design with CIS Dependency Gate

Energy and Utilities Cloud service processes (connect, disconnect, rate change) are modeled as service order records. Each service order type has a defined set of status transitions and, critically, triggers an automated callout to the external CIS or billing system when the order executes.

The fundamental design constraint for E&U process design is: **CIS integration must be functional before service order workflows can be activated.** If the CIS integration is not active, service orders will reach a terminal state with no downstream action and no meaningful error message. This is not a configuration option to design around — it is a platform dependency.

E&U service order process design includes:
- Defining the order type taxonomy (connect, disconnect, temporary disconnect, rate change, meter change)
- Mapping each order type to the correct CIS API endpoint and the expected CIS response states
- Designing the OmniStudio-based order capture UI (if used) that creates the service order record
- Designing the status management and exception handling process for CIS callout failures
- Defining the ServiceContract update steps that follow successful service order execution

---

## Common Patterns

### Pattern 1: Customizing a Prebuilt Insurance FNOL OmniScript Stage

**When to use:** The organization uses Insurance Cloud and the prebuilt FNOL OmniScript exists, but needs field additions, branching conditions, or custom integrations for a specific line of business (e.g., commercial property vs. auto).

**How it works:**
1. Navigate to the OmniStudio app and locate the prebuilt FNOL OmniScript (typically named within the Insurance or Claims namespace). Do not clone it unless explicitly required — work in place on a sandbox copy.
2. Identify which Step elements cover the customization scope: incident details, policy lookup, claimant information, or initial reserve entry.
3. Add or modify Block containers within the relevant Steps. Use Conditional View properties on Blocks for branching (e.g., show "Commercial Property Details" Block only when `ClaimType:value == 'CommercialProperty'`).
4. If the customization requires new data reads, add a Pre-Step DataRaptor Load or Integration Procedure action. If it requires writing additional fields to Claim or ClaimParticipant, modify the Post-Step DataRaptor Transform.
5. Test with a sample claim scenario in sandbox. Confirm the `Claim` record is created with the correct ClaimType, linked InsurancePolicy, and all custom field values populated.
6. Before deploying to production, verify the OmniScript activation status and confirm the Claims Management process connections are intact.

**Why not the alternative:** Rebuilding the FNOL process as a standard Screen Flow loses the prebuilt data integration with Claims Management APIs, voids upgrade compatibility, and requires manual recreation of all claimant notification and adjuster assignment logic that ships prebuilt.

### Pattern 2: Designing Order Decomposition Rules for a Telecom Bundle

**When to use:** A new bundle product (e.g., "5G Home Bundle" combining broadband, home phone, and TV streaming) has been configured in EPC and needs decomposition rules so commercial orders generate correct technical orders.

**How it works:**
1. Confirm the EPC Product Offering and all child Product Offerings (component services) are fully configured with ProductChildItem records linking them.
2. In Industries Order Management (accessed through the Communications Cloud app), open the Decomposition Rule set for the relevant product category.
3. Create a decomposition rule for the bundle Product Offering that maps it to its child technical order actions: one rule entry per atomic fulfillment step (e.g., broadband circuit provisioning, CPE device activation, TV streaming account creation).
4. Set dependency sequences where required — specify which technical order items must complete before others can start.
5. Submit a test commercial order in sandbox against the bundle Product Offering. Verify that technical order records are generated in the vlocity_cmt decomposed order objects, with correct item counts and dependency sequencing.
6. Confirm technical order status transitions to completion and that no items are left in a pending state due to missing decomposition rules.

**Why not the alternative:** Creating a Flow or Apex trigger to generate technical order records based on a commercial order bypasses the decomposition engine, breaks upgrade compatibility, and requires the flow to replicate EPC child item relationship logic manually. Decomposition rules are the platform-native mechanism for this pattern.

### Pattern 3: Designing an E&U Service Order Process with CIS Dependency Gate

**When to use:** The organization needs to add a new service order type (e.g., temporary meter disconnect for non-payment) or extend an existing service order workflow with additional CIS callout steps.

**How it works:**
1. Confirm the CIS integration is functional: run a test service order of an existing type and verify the CIS callout fires and returns a success response. Do not design a new order type until this is confirmed.
2. Define the new service order type in the service order configuration: name, status transitions, required fields, and the CIS API endpoint to call.
3. Design the order capture interface (OmniScript if OmniStudio is licensed, or a custom LWC page if not) that creates the service order record with the required fields.
4. Configure the CIS callout mapping: which service order fields map to the CIS API request payload, and how the CIS response status updates the service order status in Salesforce.
5. Design the exception path: if the CIS callout fails (timeout, API error), define the service order status to land on, the retry mechanism (if any), and the manual resolution process.
6. Update the ServiceContract update logic to fire after successful order execution — confirm the correct RatePlan or service terms are reflected.

**Why not the alternative:** Creating the service order type and designing the customer-facing process before validating the CIS integration produces a process that appears functional in sandbox (where CIS callouts may be mocked) but fails silently in production when the live CIS does not receive or acknowledge the callout.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to add fields to insurance FNOL intake | Modify the prebuilt FNOL OmniScript — add Block/element to the relevant Step | Rebuilding as Screen Flow loses Claims Management integration and upgrade path |
| Need a new claims process stage not in the prebuilt set | Extend the Claims Management OmniScript framework — add a new Step group within the existing OmniScript chain | Staying in the OmniScript framework preserves data flow to Claims APIs |
| Need to add a new telecom bundle to order management | Configure EPC Product Offerings and ProductChildItem records first, then define decomposition rules | Decomposition engine reads EPC child item structure; rules cannot be defined without EPC |
| Telecom order generates commercial records but no technical orders | Check whether decomposition rules are configured for that product offering | Missing decomposition rules = silent fulfillment failure; no error is thrown |
| CIS not yet integrated but E&U service order process must be designed | Design the process blueprint and create sandbox mocks, but do not activate service order automation | CIS callout automation cannot be tested or trusted without a live CIS endpoint |
| Tempted to replace OmniScript claims flow with standard Screen Flow | Do not — retain the OmniScript framework | Screen Flow cannot call Claims Management APIs or preserve the claims data model integrations |
| Team uses term "Salesforce Order Management" for Communications Cloud | Clarify: Communications Cloud uses Industries Order Management (vlocity_cmt), not Salesforce Order Management (Commerce) | These are separate platforms with different object models, APIs, and fulfillment engines |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on industry process design:

1. **Identify the vertical and confirm the license** — determine whether the project is Insurance (FSC + Claims Management module), Communications Cloud (with OmniStudio), or Energy and Utilities Cloud (with CIS integration active). Confirm the relevant license is provisioned before any design work begins. Use `admin/industries-insurance-setup`, `admin/industries-communications-setup`, or `admin/industries-energy-utilities-setup` to validate org readiness.

2. **Inventory the prebuilt process components** — for Insurance, locate the prebuilt Claims Management OmniScripts and document which lifecycle stages are already implemented. For Communications Cloud, identify the existing decomposition rule sets in Industries Order Management. For E&U Cloud, identify the existing service order types and their CIS callout configurations. Do not design new components for capabilities already shipped by Salesforce.

3. **Map the customization scope** — produce a stage-by-stage comparison of the prebuilt process and the required business process. For each stage, classify it as: (a) use prebuilt as-is, (b) customize prebuilt (add fields, branching, integrations), or (c) build new stage within the existing framework. Avoid classification (d) rebuild in a different runtime tool.

4. **Design the data flow per stage** — for each stage requiring customization or new build, document: the input data required (which objects and fields), the output data written (which objects and fields), the branching conditions (claim type, order type, service type), and any external API calls needed. For Insurance, map to Claims Management API endpoints. For Communications Cloud, map to EPC child item relationships and decomposition rule entries. For E&U, map to CIS API endpoint and request/response payload.

5. **Build and test in sandbox** — implement the customizations in the OmniScript designer (Insurance and optionally E&U/Comms), or in the Industries Order Management decomposition rule configuration (Communications Cloud). Test each stage with representative data scenarios including edge cases (missing policy, failed CIS callout, bundle with missing child item).

6. **Validate the end-to-end process** — for Insurance: run a complete claim through all six stages from FNOL intake to closure and confirm all Claim, ClaimParticipant, and financial records are correctly created and updated. For Communications Cloud: submit a commercial order and verify technical order records are generated with correct item counts and dependency sequence. For E&U: execute a service order and confirm the CIS callout fires, returns a success state, and the ServiceContract is updated correctly.

7. **Review for upgrade compatibility** — confirm that any modifications to prebuilt OmniScripts are contained within the correct extension points (not direct edits to managed package components), and that decomposition rules and service order configurations are deployed as unlocked package or metadata components that will survive a Salesforce package upgrade.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Industry vertical and module license confirmed (Claims Management, OmniStudio, CIS integration active)
- [ ] Prebuilt process components inventoried before any custom design began
- [ ] Customization scope classified per stage: use as-is / customize / build new (no rebuild-in-different-runtime classifications)
- [ ] Data flow documented per stage: inputs, outputs, branching conditions, external API calls
- [ ] No Screen Flow used as a replacement for an industry OmniScript framework
- [ ] Communications Cloud: Industries Order Management used for decomposition, not Salesforce Order Management (Commerce)
- [ ] E&U Cloud: CIS integration validated before service order automation is activated
- [ ] End-to-end process tested in sandbox with representative data scenarios
- [ ] Financial or CIS API integration paths validated with real endpoint responses (not just sandbox mocks)
- [ ] Upgrade compatibility reviewed for any prebuilt OmniScript modifications

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Screen Flow cannot replace the Claims Management OmniScript framework** — The Claims Management OmniScript framework is pre-integrated with Claims Management API endpoints, the Adjuster's Workbench component, and the Claims financial data model. A standard Screen Flow built to replicate the FNOL intake process does not have access to these integrations and cannot call the insurance-specific Connect API endpoints. The result appears functional in sandbox testing but fails to create correct Claim and ClaimParticipant records at runtime.

2. **E&U service order execution requires a live CIS — mocking in sandbox hides this dependency** — In E&U sandbox environments, CIS API callouts are typically mocked or skipped. Service orders appear to complete successfully in sandbox. In production, if the CIS integration is not active, service orders reach an execution status and the CIS callout fires — but if the endpoint is unreachable or returns an error, the service order stalls with no user-visible error and no automatic retry. Design the exception path and monitor the CIS callout logs from day one.

3. **Communications Cloud decomposition rules are declarative configuration, not code** — Teams with Apex backgrounds attempt to write Apex triggers or Flows to generate technical order records from commercial orders. This bypasses the Industries Order Management decomposition engine entirely. The decomposition engine only processes orders that have matching decomposition rules configured against their EPC Product Offering chain. Apex-generated technical orders may appear in the vlocity_cmt objects initially but will not participate in the platform's order lifecycle management, status tracking, or fulfillment callbacks.

4. **Insurance FNOL OmniScript namespace differs between managed-package and native-core DIP orgs** — On managed-package Digital Insurance Platform orgs, FNOL OmniScript components live in the managed package namespace and cannot be directly edited. On native-core orgs (post-October 2025 target), components are in the org namespace. Cloning a managed-package OmniScript into the org namespace breaks the remote action bindings to `InsProductService` and the Claims Management API unless the cloned version explicitly re-wires those integrations. Always confirm whether the org is on managed-package or native-core DIP before planning OmniScript customizations.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Industry process design blueprint | Per-stage classification of prebuilt vs customized vs new stages, with the runtime tool confirmed for each vertical |
| Claims lifecycle stage inventory | Six-stage FNOL-to-closure OmniScript map with customization scope per stage and Claims API endpoint references |
| Order decomposition rule design | Commercial-to-technical order mapping for each telecom bundle, with EPC child item references and dependency sequencing |
| E&U service order design | Service order type taxonomy, CIS callout mapping, exception path design, and ServiceContract update logic |
| Process data flow matrix | Per-stage documentation of input objects, output objects, branching conditions, and external API calls |

---

## Related Skills

- `admin/industries-insurance-setup` — configure the FSC Insurance license, org settings, and core insurance objects before designing claims processes; use this to validate org readiness
- `admin/industries-communications-setup` — configure Communications Cloud, EPC service catalog, and decomposition rule infrastructure before designing order processes
- `admin/industries-energy-utilities-setup` — configure E&U Cloud license, service points, and CIS integration before designing service order workflows
- `admin/omniscript-flow-design-requirements` — use to produce structured requirements artifacts for any OmniScript-based industry process stage before development begins
- `admin/omnistudio-vs-standard-decision` — use to confirm whether OmniScript is the correct runtime tool for a given industry process before committing to design
