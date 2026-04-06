# Well-Architected Notes — Document Generation OmniStudio

## Relevant Pillars

- **Reliability** — Document generation must produce correct, complete output every time. Token mismatches, missing Data Mapper mappings, or omitted conversion steps all produce silently incorrect documents that may reach customers. Reliability depends on strict contract alignment between template tokens and the JSON payload, plus thorough testing with representative data including edge cases (empty arrays, null values, maximum-size images).

- **Performance** — Client-side DocGen runs synchronously in the user's browser, so template complexity and data volume directly impact user wait time. Large documents with many repeating sections or embedded images can cause browser memory issues. Server-side DocGen runs asynchronously on Salesforce compute but still has processing time and governor limit considerations for batch scenarios. Choose the generation mode based on document size and volume requirements.

- **Security** — Generated documents often contain sensitive data (PII, financial details, legal terms). Ensure that the OmniScript or Integration Procedure enforces record-level and field-level security before passing data to the template. Documents stored as ContentVersion records inherit Salesforce sharing rules, but documents delivered externally (email, API) must be secured at the transport and storage level.

- **Operational Excellence** — Document Templates, Data Mappers, and Document Generation Settings must be managed as deployable artifacts across environments. Template changes must be version-controlled, tested in sandboxes, and deployed with the corresponding Data Mapper updates. Orphaned or stale templates in production cause generation failures that are difficult to diagnose.

## Architectural Tradeoffs

### Client-Side vs Server-Side Generation

Client-side generation provides immediate feedback and supports the full token feature set (including images and rich text), but is limited to single-document interactive scenarios and depends on browser resources. Server-side generation supports batch and headless scenarios with Salesforce compute resources, but lacks image/rich text token support and produces output asynchronously.

The tradeoff is between **feature richness and interactivity** (client-side) vs **scalability and automation** (server-side). Most implementations need both modes for different use cases within the same org.

### OmniDataTransform vs Custom Class for Token Mapping

OmniDataTransform provides a declarative, visual mapping interface with automatic token extraction from templates. A custom Apex class provides full programmatic control over JSON construction. The tradeoff is **maintainability and speed of change** (Data Mapper) vs **flexibility for complex transformations** (custom class). Prefer the Data Mapper for standard field mappings and reserve custom classes for scenarios requiring complex calculations, external data integration, or transformations that exceed the Data Mapper's formula capabilities.

### Single Template vs Multi-Template Package

A single monolithic template is simpler to manage but becomes unwieldy as document complexity grows. Splitting into multiple templates (cover letter, body, appendix) improves maintainability and enables conditional document inclusion, but requires orchestration logic to manage multiple DocGen steps and combine outputs. Prefer multi-template when the document package exceeds 10 pages or contains independently variable sections.

## Anti-Patterns

1. **Bypassing the Data Mapper to construct JSON manually in OmniScript Set Values.** This creates a brittle, unmaintainable mapping layer that does not benefit from automatic token extraction or visual mapping. When the template changes, every Set Values action must be manually audited and updated. Use the OmniDataTransform as the single source of truth for token mapping.

2. **Reusing a client-side template for server-side generation without removing unsupported tokens.** Image and rich text tokens silently fail in server-side mode, producing documents with missing content. Maintain separate templates per generation mode, or design templates to use only universally supported token types when cross-mode reuse is intended.

3. **Deploying templates without corresponding Data Mapper and Document Generation Setting updates.** Partial deployments leave the generation pipeline in an inconsistent state. A new token in the template without a corresponding Data Mapper mapping produces blank output. Always deploy the template, Data Mapper, and Document Generation Setting as a single change set or package.

## Official Sources Used

- OmniStudio Document Generation Overview (SF Help) -- feature overview, client-side and server-side modes
- OmniStudio Document Templates (SF Help) -- template authoring, token types, merge syntax
- OmniStudio Client-Side Document Generation (SF Help) -- OmniScript orchestration, PDF conversion
- OmniStudio Server-Side Document Generation (SF Help) -- Integration Procedure orchestration, limitations
- OmniStudio Document Generation Troubleshooting Guide (SF Help) -- common errors and resolution steps
- OmniStudio DocGen Foundations (Trailhead) -- end-to-end learning path for document generation
- Salesforce Well-Architected Overview -- architecture quality framing
