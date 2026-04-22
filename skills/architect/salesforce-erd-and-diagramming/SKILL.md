---
name: salesforce-erd-and-diagramming
description: "Salesforce ERD and architecture diagram generation: Mermaid/PlantUML data-model diagrams for Sales, Service, FSL, Commerce, Revenue Cloud; OAuth flow diagrams; integration architecture diagrams; object-relationship visualization. NOT for data model design decisions (use data-model-design-patterns). NOT for UI wireframing (use lightning-experience-design)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - erd
  - diagramming
  - mermaid
  - plantuml
  - architecture-diagrams
  - data-model
  - documentation
triggers:
  - "generate an erd for salesforce sales cloud"
  - "diagram the oauth flow for experience cloud"
  - "mermaid erd for service cloud objects"
  - "how do i document my salesforce data model"
  - "plantuml diagram of integration architecture"
  - "object relationship diagram as code"
inputs:
  - Scope (which cloud, which objects, which integrations)
  - Target diagram format (Mermaid, PlantUML, draw.io, Lucid)
  - Audience (architect peers, execs, developers, auditors)
  - Level of detail (logical vs physical, with fields vs object-only)
outputs:
  - ERD in chosen format (Mermaid / PlantUML source)
  - Integration architecture diagram (OAuth, data flow, callouts)
  - Diagram stored in repo alongside code, regeneratable
  - README pointer to the diagram source
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Salesforce ERD and Diagramming

Activate when an architect needs to produce data-model or architecture diagrams for a Salesforce implementation: an ERD for a cloud's core objects, an integration flow, an OAuth sequence, or a Well-Architected review deliverable. The focus is on "diagram-as-code" approaches that live next to metadata and regenerate deterministically.

## Before Starting

- **Confirm the audience and level of detail.** A CIO-level architecture diagram elides fields; a developer-level ERD includes them. Diagrams in the wrong style waste the audience's time.
- **Choose diagram-as-code over drawing tools for anything version-controlled.** Mermaid and PlantUML render in PRs; Lucidchart and draw.io fit hand-maintained executive decks but rot out of sync with the org.
- **Identify the source of truth.** If the ERD can be generated from `sf org describe` or metadata XML, generate it; never hand-draw what automation can.

## Core Concepts

### Object graph is already in metadata

Every Salesforce object has a metadata file. Fields, lookups, and master-details are in the XML. A diagram is a projection of that graph. Tools like Schema Builder render the full graph in-org; external tools read metadata and emit Mermaid/PlantUML.

### Logical vs physical ERD

Logical ERD shows business entities and their meaningful relationships (Account, Contact, Opportunity). Physical ERD includes system objects (Task, Note, Attachment, ContentDocumentLink). Almost all stakeholder-facing ERDs are logical; physical is reserved for integration and data migration work.

### Standard object conventions in diagrams

Reusable shorthand: `ACC` for Account, `OPP` for Opportunity, `CON` for Contact, `CAS` for Case. Mark master-detail with a solid line + filled diamond on the parent; lookup with dashed + open diamond. This matches Salesforce Architect-published diagrams.

### Integration architecture diagrams

Diagram types: OAuth sequence, event flow, data flow, deployment topology. Each follows a distinct shape library. Mermaid's `sequenceDiagram`, PlantUML's `@startuml ... actor` blocks cover most needs.

## Common Patterns

### Pattern: Mermaid ERD from metadata

Script reads `objects/*/fields/*.field-meta.xml`, emits Mermaid ER syntax. Each lookup becomes `ACC ||--o{ OPP : has`. Committed to `docs/diagrams/erd-sales.md` with source. Regenerates on metadata change via CI.

### Pattern: OAuth flow sequence

Mermaid `sequenceDiagram` with actors: User, Browser, Salesforce, External App, Token Endpoint. Use for Experience Cloud SSO, Salesforce-to-X connected apps, JWT bearer flows.

### Pattern: Integration topology diagram

PlantUML deployment diagram shows systems, named credentials, protocols, payload formats. Reference for operations on-call.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| ERD for a single cloud | Mermaid ER from metadata | Renders in GitHub, regenerates |
| Integration architecture | PlantUML deployment or C4 | Richer syntax for systems |
| Executive view | Lucid / draw.io with simplified labels | Editable by non-engineers |
| OAuth flow | Mermaid sequenceDiagram | Universal, renders anywhere |
| Ad hoc whiteboard | Excalidraw or draw.io | Quick, not versioned |

## Recommended Workflow

1. Identify the diagram type and audience; pick logical vs physical, executive vs developer.
2. Generate the base shape from metadata if possible (`sf org describe`, schema introspection).
3. Write diagram source in Mermaid or PlantUML; store in `docs/diagrams/` alongside metadata.
4. Render locally with the relevant CLI; iterate on layout.
5. Commit with the metadata PR that introduced any schema changes.
6. Add a README pointer so future reviewers find the diagram.
7. Add CI to regenerate diagrams on metadata change; fail the build if source drifts from diagram.

## Review Checklist

- [ ] Diagram matches current metadata (regenerate if in doubt)
- [ ] Logical vs physical choice matches audience
- [ ] Diagram source is version-controlled text
- [ ] Legend shows lookup vs master-detail convention
- [ ] Standard-object shorthand consistent with team style
- [ ] Sensitive detail (PII, field-level security) redacted where audience warrants
- [ ] Diagram file referenced from relevant README / ADR

## Salesforce-Specific Gotchas

1. **Polymorphic relationships break simple ERD syntax.** `WhatId` on Task points to many objects; show as a composite edge with a note, not a single arrow.
2. **Implicit junction objects are easy to miss.** `AccountContactRelation`, `OpportunityContactRole` don't appear in Object Manager's top view but belong in the diagram.
3. **Metadata-to-diagram scripts miss managed-package objects.** Either include the package XML in the source or annotate the diagram with "external: package-name".

## Output Artifacts

| Artifact | Description |
|---|---|
| Mermaid ERD source | Versioned, regeneratable ER diagram |
| OAuth sequence diagram | For SSO and connected app patterns |
| Integration topology | Systems, credentials, protocols |
| Diagram generation script | Metadata → diagram source automation |

## Related Skills

- `architect/well-architected-reviews` — review deliverable usage
- `integration/integration-pattern-selection` — integration diagram subject
- `devops/metadata-api-fundamentals` — diagram source material
