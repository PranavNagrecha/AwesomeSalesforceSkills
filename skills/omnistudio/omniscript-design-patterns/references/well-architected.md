# Well-Architected Notes: OmniScript Design Patterns

## Relevant Pillars

### User Experience

OmniScript lives at the interaction layer, so step clarity, branching discipline, and save/resume behavior directly shape the user experience.

### Operational Excellence

The script must stay supportable. Thin guided flows, predictable branching, and clear delegation to backend services keep operations manageable.

### Reliability

Long guided journeys fail when state restoration, backend handoffs, or embedded custom components are not designed intentionally.

## Architectural Tradeoffs

- **Rich guided experience vs script complexity:** OmniScript is powerful for user journeys, but too much logic in the script harms maintainability.
- **Branch flexibility vs testability:** More branches can improve personalization, but they quickly raise the support and regression burden.
- **Custom components vs standard OmniStudio elements:** Custom LWCs unlock flexibility while adding more contracts and failure modes.

## Anti-Patterns

1. **Using OmniScript as the full integration and transformation layer**: backend-heavy logic should move behind the script.
2. **Excessive step counts with weak milestones**: the journey becomes harder for users and operators alike.
3. **Save/resume with no context revalidation plan**: resumed journeys can submit stale assumptions.

## Official Sources Used

- Industries Common Resources Developer Guide, Summer '26 (release 262): Omnistudio Metadata API Types > OmniScript (`uniqueName`, `isActive`, `isOmniScriptEmbeddable`, `isWebCompEnabled`, `omniProcessElements`), OmniProcessElement, OmniscriptDefinition, OmniStudioSettings (`enableOmniStudioMetadata` one-way), Omnistudio Standard Objects (OmniProcess, OmniProcessElement, OmniScriptSavedSession internal use) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_industries_dev_guide.pdf
- Trailhead, Omnistudio Omniscripts, "Learn the Fundamentals of Omniscripts" (modular architecture, data from multiple sources) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript/learn-the-fundamentals-of-omniscripts
- Trailhead, Omnistudio Omniscripts, "Dig into the Omniscript Designer" (Setup panel Save Options, Preview with Context ID, Data JSON, Action Debugger, versions) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript/dig-into-the-omniscript-designer
- Trailhead, Omnistudio Omniscripts, "Design a Simple Omniscript" (element families, Integration Procedure Action, Type Ahead Blocks, child Omniscripts) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript/design-a-simple-omniscript
- Trailhead, Omnistudio Omniscripts, "Create a Simple Omniscript" (Type/SubType/Language identity, one active version, unique element names, Integration Procedures as best practice) - https://trailhead.salesforce.com/content/learn/modules/omnistudio-omniscript/create-a-simple-omniscript
- Salesforce CLI source-deploy-retrieve 12.22.6 metadata registry (`omniScripts` directory, `os` suffix), local install at /usr/local/lib/sf/node_modules/@salesforce/source-deploy-retrieve/lib/src/registry/metadataRegistry.json
