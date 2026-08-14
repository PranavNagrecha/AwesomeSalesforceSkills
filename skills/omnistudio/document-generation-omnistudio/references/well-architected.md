# Well-Architected Notes — Document Generation OmniStudio

## Relevant Pillars

- **Reliability** — Document generation must produce correct, complete output every time. Token mismatches, missing Data Mapper mappings, or omitted conversion steps all produce silently incorrect documents that may reach customers. Reliability depends on strict contract alignment between template tokens and the JSON payload, plus thorough testing with representative data including edge cases (empty arrays, null values, maximum-size images).

- **Performance** — Client-side DocGen runs synchronously in the user's browser, so template complexity and data volume directly impact user wait time. Large documents with many repeating sections or embedded images can cause browser memory issues. Server-side DocGen runs asynchronously on Salesforce compute but still has processing time and governor limit considerations for batch scenarios. Choose the generation mode based on document size and volume requirements.

- **Security** — Generated documents often contain sensitive data (PII, financial details, legal terms). The controls are OmniStudio's own, not Apex's: set **Required Permission** on every Data Mapper and Integration Procedure in the pipeline (blank means any user can run it), and confirm `EnforceDMFLSAndDataEncryption` and `CheckCachedMetadataRecordSecurity` are on in the Omni Interaction Configuration custom setting — see `references/gotchas.md` Gotcha 7. Note that a Required Permission on a child component is not re-checked when a parent Integration Procedure invokes it, so the entry point carries the access decision. Documents stored as ContentVersion records inherit Salesforce sharing rules, but documents delivered externally (email, API) must be secured at the transport and storage level.

- **Operational Excellence** — Document Templates, Data Mappers, and Document Generation Settings must be managed as deployable artifacts across environments. Template changes must be version-controlled, tested in sandboxes, and deployed with the corresponding Data Mapper updates. Orphaned or stale templates in production cause generation failures that are difficult to diagnose.

## Architectural Tradeoffs

### Client-Side vs Server-Side Generation

Client-side generation provides immediate feedback and preview, but is limited to single-document interactive scenarios and depends on browser resources. Server-side generation supports batch and headless scenarios on Salesforce compute and produces output asynchronously. **Token support is not the axis of this tradeoff** — image tokens are documented for server-side generation through the Data Mapper, and the token reference does not restrict rich text or hyperlink tokens by mode. Decide on interactivity, volume and trigger source.

The tradeoff is between **feature richness and interactivity** (client-side) vs **scalability and automation** (server-side). Most implementations need both modes for different use cases within the same org.

### OmniDataTransform vs Custom Class for Token Mapping

OmniDataTransform provides a declarative, visual mapping interface with automatic token extraction from templates. A custom Apex class provides full programmatic control over JSON construction. The tradeoff is **maintainability and speed of change** (Data Mapper) vs **flexibility for complex transformations** (custom class). Prefer the Data Mapper for standard field mappings and reserve custom classes for scenarios requiring complex calculations, external data integration, or transformations that exceed the Data Mapper's formula capabilities.

### Single Template vs Multi-Template Package

A single monolithic template is simpler to manage but becomes unwieldy as document complexity grows. Splitting into multiple templates (cover letter, body, appendix) improves maintainability and enables conditional document inclusion, but requires orchestration logic to manage multiple DocGen steps and combine outputs. Prefer multi-template when the document package exceeds 10 pages or contains independently variable sections.

## Anti-Patterns

1. **Bypassing the Data Mapper to construct JSON manually in OmniScript Set Values.** This creates a brittle, unmaintainable mapping layer that does not benefit from automatic token extraction or visual mapping. When the template changes, every Set Values action must be manually audited and updated. Use the OmniDataTransform as the single source of truth for token mapping.

2. **Forking a template per generation mode on the false belief that server-side cannot render images or rich text.** Maintaining two templates for one document doubles the change surface and guarantees drift. Image tokens are documented for server-side generation via a Data Mapper Extract + Transform pair, and rich text and hyperlink tokens are listed in the token reference without a mode restriction. Keep one template; if an image fails to render server-side, debug the Data Mapper pair and the `IMG_` prefix rather than forking.

3. **Deploying templates without corresponding Data Mapper and Document Generation Setting updates.** Partial deployments leave the generation pipeline in an inconsistent state. A new token in the template without a corresponding Data Mapper mapping produces blank output. Always deploy the template, Data Mapper, and Document Generation Setting as a single change set or package.

## Official Sources Used

- OmniStudio Document Generation Overview (SF Help) -- feature overview, client-side and server-side modes
- OmniStudio Document Templates (SF Help) -- template authoring, token types, merge syntax
- Tokens in Microsoft Word or Microsoft PowerPoint Documents (SF Help) -- the canonical token-prefix reference: variable, `{{#…}}`/`{{^…}}` repeating, `{{#IF_…}}` condition, `{{IMG_…}}` image, `{{HYP_…}}` hyperlink, `{{RTB_…}}` rich text, `{{DT_…}}` data true-up, `bypass_tokens` (verified 2026-08-01) -- https://help.salesforce.com/s/articleView?id=ind.doc_gen_tokens_in_microsoft_word_or_microsoft_powerpoint_documents.htm&language=en_US&type=5
- Map Image Tokens in the Omnistudio Data Mapper for Server-Side Omnistudio Document Generation (SF Help) -- confirms server-side image token support; Data Mapper Extract (ContentDocument / Attachment / Contract Document) + Transform; max 350 px × 400 px on A4 portrait by default, 600 px × 800 px when both dimensions are defined; "to maintain the original aspect ratio of an image, define either the height or the width, but not both" (verified 2026-08-01) -- https://help.salesforce.com/s/articleView?id=ind.doc_gen_serverside_dynamic_images_five.htm&language=en_US&type=5
- Map Rich Text Tokens in Omnistudio Data Mapper (SF Help) -- `{{RTB_…}}` syntax and Data Mapper Extract/Transform mapping steps (verified 2026-08-01) -- https://help.salesforce.com/s/articleView?id=ind.doc_gen_map_rich_text_tokens_in_the_dataraptors.htm&language=en_US&type=5
- Security for Omnistudio Data Mappers and Integration Procedures (SF Help) -- Required Permission property accepts "roles, profiles, permission sets, custom permissions, or any combination"; "If Required Permission is blank, any user can run the Data Mapper or Integration Procedure unless the DefaultRequiredPermission property is set"; `DefaultRequiredPermission` needs `VlocityRequiredPermissionCheck` implemented manually (verified 2026-08-13) -- https://help.salesforce.com/s/articleView?id=xcloud.os_security_for_dataraptors_and_integration_procedures_56519.htm&language=en_US&type=5
- Omnistudio Data Mapper and Integration Procedure Security Settings (SF Help) -- `DefaultRequiredPermission` (String, default none), `EnforceDMFLSAndDataEncryption` (True/False), `CheckCachedMetadataRecordSecurity` (True/False, default False), all in the Omni Interaction Configuration custom setting (verified 2026-08-13) -- https://help.salesforce.com/s/articleView?id=xcloud.os_dataraptor_and_integration_procedure_security_settings_48215.htm&language=en_US&type=5
- OmniInteractionConfig (Industries Metadata API Developer Guide) -- "If set to true, this setting enforces field-level security for all Data Mappers and displays encrypted fields in plain text only for users with the View Encrypted Data permission"; Data Mappers then "run in the user context instead of the system context"; Salesforce enables `EnforceDMFLSAndDataEncryption` (with `AdvancedOmnistudioAccessCheck`, `ApexClassCheckForIP`, `ApexClassCheck`, `EnableQueryWithFLS`) by default during the week of February 2, 2026 (verified 2026-08-13) -- https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omniinteractionconfig.htm
- OmniStudio Client-Side Document Generation (SF Help) -- OmniScript orchestration, PDF conversion
- OmniStudio Server-Side Document Generation (SF Help) -- Integration Procedure orchestration, limitations
- OmniStudio Document Generation Troubleshooting Guide (SF Help) -- common errors and resolution steps
- OmniStudio DocGen Foundations (Trailhead) -- end-to-end learning path for document generation
- Salesforce Well-Architected Overview -- architecture quality framing
