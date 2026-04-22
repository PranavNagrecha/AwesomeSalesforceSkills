---
name: cloud-specific-deployment-architecture
description: "Deployment architecture quirks per Salesforce cloud: Industries (OmniStudio), Marketing Cloud (MC packages), Commerce Cloud, Data Cloud, Agentforce. What ships via metadata API, what ships via cloud-specific tools, ordering, dependencies. NOT for generic DevOps (use devops skills). NOT for cross-cloud data flow (use cross-cloud-data-deployment)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Scalability
tags:
  - deployment
  - industries
  - marketing-cloud
  - commerce-cloud
  - data-cloud
  - agentforce
  - omnistudio
triggers:
  - "how do we deploy omnistudio components between orgs"
  - "marketing cloud package deployment strategy"
  - "commerce cloud b2c site deploy pipeline"
  - "data cloud metadata deployment what is supported"
  - "agentforce agent deployment across orgs"
  - "industries omnistudio deployment ordering and dependencies"
inputs:
  - Clouds in scope and their components
  - Source and target environments (sandbox, UAT, prod)
  - Tooling currently in use (SFDX, Copado, Flosum, Gearset, MC DevTools)
  - Deployment cadence and risk tolerance
outputs:
  - Per-cloud deployment pipeline map
  - Component ordering and dependency graph
  - Tool selection per cloud
  - Rollback strategy per cloud
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Cloud-Specific Deployment Architecture

Activate when planning deployments that include non-core components: OmniStudio (FlexCards, Integration Procedures, DataRaptors), Marketing Cloud packages, Commerce Cloud sites, Data Cloud Data Streams and DMOs, Agentforce agents, Industries Data Kit. Each cloud has quirks in what the metadata API covers and what needs cloud-specific tools.

## Before Starting

- **Inventory the component types per cloud.** Metadata API covers most of Platform + Sales/Service; OmniStudio, Marketing Cloud, Commerce Cloud, Data Cloud each have their own piece of the puzzle.
- **Understand dependency direction.** Permission sets reference objects; OmniScripts reference Integration Procedures; Agentforce Topics reference Actions. Deploy dependencies first.
- **Decide the tool per cloud.** One tool rarely covers all. Combine: SFDX for platform, MC DevTools for Marketing Cloud, B2C Commerce CLI for Commerce Cloud, Data Cloud Migration Tool for Data Cloud.

## Core Concepts

### OmniStudio deployment

OmniStudio components (FlexCards, OmniScripts, Integration Procedures, DataRaptors, Expression Sets) deploy via the OmniStudio Migration Tool or via SFDX with the Industries Data Kit. Ordering matters: DataRaptors before Integration Procedures before OmniScripts before FlexCards.

### Marketing Cloud deployment

Marketing Cloud is a separate stack. Email templates, journeys, automations, data extensions — handled via MC DevTools (Accenture/Salesforce community-maintained), MC REST API, or enterprise tools like Copado MC. Metadata API does NOT cover Marketing Cloud content.

### Commerce Cloud (B2C / B2B) deployment

B2C: Storefront cartridges via SFCC Studio + Business Manager + Build API. B2B: Experience Cloud site + Commerce Cloud metadata via SFDX. Shared services (catalogs, price books) need coordinated deploys.

### Data Cloud deployment

Data Streams, DMOs, Calculated Insights, Activations: partial metadata-API coverage improving by release. Data Cloud Migration Tool + JSON definitions cover the rest. Identity resolution rules deploy separately.

### Agentforce deployment

Agents, topics, actions, prompt templates ship via metadata API as of late 2025 / early 2026. Guardrails and Einstein Trust Layer settings are org-scoped. Cross-org test must re-run after every topic/action change.

## Common Patterns

### Pattern: Hybrid pipeline per cloud, single orchestrator

Orchestrator (Copado, Gearset, custom Jenkins) calls per-cloud tools: SFDX for platform, MC DevTools for Marketing Cloud, OmniStudio Migration Tool for Industries. One PR can carry all but deploys branch by cloud with ordering.

### Pattern: Data Kit as the Industries distribution unit

For Industries customers, the Industries Data Kit bundles OmniStudio + SObjects + data mappings. Deploying a Data Kit is the unit of change for many Industries components.

### Pattern: Agentforce topic + action atomic unit

A topic and the actions it calls deploy together. Separating them breaks agent routing. Package them as a single deployable change set or pipeline stage.

## Decision Guidance

| Cloud / Component | Primary Tool | Secondary |
|---|---|---|
| Platform (Apex, LWC, Flow) | SFDX / Metadata API | Copado, Gearset, Flosum |
| OmniStudio | OmniStudio Migration Tool + SFDX | Industries Data Kit |
| Marketing Cloud | MC DevTools + MC API | Copado MC |
| Commerce Cloud B2C | SFCC Studio + Build API | Salesforce CLI plugins |
| Data Cloud | Data Cloud Migration Tool | Metadata API (partial) |
| Agentforce | Metadata API | Agentforce management console |

## Recommended Workflow

1. Inventory the components by cloud and classify by deploy mechanism.
2. Draw the per-cloud deploy pipeline and mark ordering dependencies.
3. Pick tooling per cloud with one orchestrator coordinating stage gates.
4. Build a dependency graph across clouds (e.g., OmniScript → Platform Apex class).
5. Validate on a pilot sandbox; measure deploy time per stage.
6. Document rollback per cloud; note that some clouds (Marketing, Commerce) do not support "rollback" natively and require replay.
7. Instrument pipeline with health checks per cloud; failures alert to owner teams.

## Review Checklist

- [ ] Component inventory per cloud complete
- [ ] Tool selected per cloud with rationale
- [ ] Ordering dependencies documented in a diagram
- [ ] Pilot deployment validated end-to-end
- [ ] Rollback strategy per cloud documented
- [ ] Secrets and connected app credentials stored securely
- [ ] Pipeline health dashboard live

## Salesforce-Specific Gotchas

1. **OmniStudio export is JSON; ordering matters.** Loading OmniScripts before their Integration Procedures breaks references silently.
2. **Marketing Cloud data extensions include schema and data.** Deploying a DE over an existing one with a schema drift deletes the drift fields.
3. **Data Cloud DMO activation flags are environment-scoped.** A DMO deployed from sandbox to prod may be inactive until manually activated.

## Output Artifacts

| Artifact | Description |
|---|---|
| Per-cloud component inventory | What exists, in which cloud |
| Tool map | Tool chosen per cloud with rationale |
| Dependency graph | Cross-cloud ordering |
| Rollback playbook per cloud | Replay vs revert per cloud |

## Related Skills

- `architect/deployment-automation-architecture` — orchestration layer
- `architect/cross-cloud-data-deployment` — data flow between clouds
- `devops/cicd-pipeline-design` — platform CI/CD
