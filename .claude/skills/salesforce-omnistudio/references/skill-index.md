# SfSkills — `omnistudio` skill roster (34 packages)

The zero-setup lookup path: this file ships with the plugin and needs
no search index. Scan it, pick a package by name, then read that
package from the repository root under `${CLAUDE_PLUGIN_ROOT}`.

Generated from `registry/skills.json` by `scripts/build_plugin.py`.
Do not hand-edit.

**How to read a gloss.** The package id is on the line already, so the
gloss does not repeat it. It carries what the id cannot, in this order:
the package's own **trigger vocabulary** (the phrasings that should
land here), then its **`NOT for …` redirect** (which names the package
to use instead), then a short scope phrase if there is room. A
`…` marks a truncation, always at a word, keyword or
whole-clause boundary. Budget: 220 characters.

**A `NOT for X - use Y` clause is the most useful thing on the line.**
If your question is X, stop and open Y instead of this package.

- `skills/omnistudio/business-rules-engine/SKILL.md` — Triggers: 'business rules engine', 'BRE', 'decision table', 'rule matrix', 'eligibility determination', 'ExpressionSetService', 'expression set evaluate'. NOT for Flow decision elements or Flow-based branching logic …
- `skills/omnistudio/calculation-procedure-design/SKILL.md` — Design OmniStudio Calculation Procedures and Calculation Matrices for pricing, rating, and …. Triggers: calculation procedure, calculation matrix, rating engine, pricing matrix, expression set, decision matrix, ….
- `skills/omnistudio/calculation-procedures/SKILL.md` — Triggers: 'calculation procedure', 'expression set', 'calculation matrix', 'decision matrix', 'pricing calculation', 'lookup step', 'matrix versioning'. NOT for DataRaptor transforms or DataRaptor-based field mapping.
- `skills/omnistudio/dataraptor-load-and-extract/SKILL.md` — building or debugging DataRaptor Extract or DataRaptor Load operations in …. NOT for DataRaptor Transform operations (use dataraptor-patterns), NOT for Integration Procedure design (use integration-procedures), NOT …
- `skills/omnistudio/dataraptor-patterns/SKILL.md` — Triggers: 'DataRaptor Extract', 'Turbo Extract', 'DataRaptor Load', 'DataRaptor Transform', 'OmniStudio data mapping'. NOT for overall OmniScript journey design or Integration Procedure sequencing when the main …
- `skills/omnistudio/dataraptor-transform-optimization/SKILL.md` — DataRaptor Transform operations are slow, hit …. Triggers: 'dataraptor transform slow', 'dataraptor formula vs apex', 'dataraptor bulk transform', 'dr governor limit'. NOT for DataRaptor Extract or Load performance.
- `skills/omnistudio/document-generation-omnistudio/SKILL.md` — Generating documents (PDF, DOCX, PPTX) from OmniStudio using Document Templates, OmniDataTransform …. NOT for Salesforce CPQ document generation. NOT for standard Salesforce mail merge or Lightning email templates.
- `skills/omnistudio/flexcard-container-composition/SKILL.md` — Design FlexCard composition: parent/child state flow, layout modes, actions, event wiring, and data source selection. Triggers: flexcard, flex card composition, parent child flexcard, flexcard state, flexcard events, ….
- `skills/omnistudio/flexcard-design-patterns/SKILL.md` — Triggers: 'FlexCard', 'card template', 'flyout', 'card action', 'card state', 'data source', 'child card', 'conditional visibility'. NOT for OmniScript design, standalone LWC development, or Apex controller …
- `skills/omnistudio/flexcard-state-management/SKILL.md` — designing FlexCard actions …. Triggers: 'flexcard state', 'flexcard conditional visibility', 'flexcard actions', 'flexcard refresh', 'child flexcard state'. NOT for raw LWC state or for OmniScript step state.
- `skills/omnistudio/industries-api-extensions/SKILL.md` — Triggers: Insurance policy issuance API, endorsement API, TMF679, Communications Cloud REST API, Update Asset Status, Service Process API, …. NOT for standard Salesforce REST API, SOAP API, Bulk API, or platform event …
- `skills/omnistudio/industries-cpq-vs-salesforce-cpq/SKILL.md` — Triggers: Vlocity CPQ, Industries CPQ, Salesforce CPQ comparison, Revenue Cloud migration, CPQ selection, which CPQ to use. NOT for implementing, configuring, or debugging either CPQ product.
- `skills/omnistudio/integration-procedure-cacheable-patterns/SKILL.md` — designing Integration Procedures (IPs) with platform cache to cut latency and callout load. Covers cache key design, TTL selection, per-user vs ….
- `skills/omnistudio/integration-procedures/SKILL.md` — Triggers: 'integration procedure', 'IP', 'HTTP action', 'DataRaptor', 'rollbackOnError', 'failureResponse'. NOT for Apex-only integrations unless the main design choice is whether OmniStudio is still appropriate.
- `skills/omnistudio/omniscript-design-patterns/SKILL.md` — Triggers: 'omniscript design', 'too many steps in omniscript', 'save and resume omniscript', 'branching in omniscript', …. NOT for deep Integration Procedure or DataRaptor design when the guided interaction layer is …
- `skills/omnistudio/omniscript-session-state/SKILL.md` — an OmniScript must persist mid-flow state across refresh, navigation, multi-device resume, or abandonment recovery. Covers session objects, staging ….
- `skills/omnistudio/omniscript-versioning/SKILL.md` — managing OmniScript versions: activating new versions, deactivating prior versions, testing a specific version …. NOT for OmniStudio deployment or DataPack migration (use omnistudio/omnistudio-deployment-datapacks).
- `skills/omnistudio/omnistudio-asynchronous-data-operations/SKILL.md` — Use Integration Procedures queues, DataRaptor Chain, and Remote Actions with async patterns for long-running OmniStudio flows. NOT for simple DataRaptor reads.
- `skills/omnistudio/omnistudio-cache-strategies/SKILL.md` — Configure caching on DataRaptors and Integration Procedures to cut response times, with cache-bust and freshness guarantees. NOT for platform-level org cache.
- `skills/omnistudio/omnistudio-ci-cd-patterns/SKILL.md` — designing or implementing CI/CD pipelines for OmniStudio components — DataPack export/import, versioning, environment promotion, and automated …. NOT for standard Salesforce metadata CI/CD or Apex-only pipelines.
- `skills/omnistudio/omnistudio-custom-lwc-elements/SKILL.md` — Creating and integrating custom Lightning Web Components within OmniScripts: LWC override patterns …. NOT for standalone LWC development (use lwc/* skills). NOT for Integration Procedures (use integration-procedures).
- `skills/omnistudio/omnistudio-debugging/SKILL.md` — Triggers: 'omniscript not working', 'dataraptor returns empty', 'integration procedure failing', 'debug mode', 'action debugger', 'preview not running'. NOT for Apex debugging, LWC console errors unrelated to …
- `skills/omnistudio/omnistudio-deployment-datapacks/SKILL.md` — exporting, importing, or version-controlling OmniStudio components using DataPacks via the OmniStudio DataPacks tool or vlocity CLI. Covers …. NOT for SFDX-based metadata deployment of non-OmniStudio components.
- `skills/omnistudio/omnistudio-error-handling-patterns/SKILL.md` — Triggers: 'omnistudio error', 'integration procedure fault', 'dataraptor error handling', 'omniscript retry', 'flexcard action failure'. NOT for general Apex exception design or Flow fault paths.
- `skills/omnistudio/omnistudio-field-mapping-governance/SKILL.md` — Govern DataRaptor field mappings to prevent runtime errors when source metadata changes: naming, versioning, and dependency tracking. NOT for DataRaptor authoring fundamentals.
- `skills/omnistudio/omnistudio-lwc-integration/SKILL.md` — Triggers: embed omniscript in LWC, custom LWC element in OmniScript, call OmniScript from Lightning page, omnistudio-omni-script tag, seed data JSON, …. NOT for standalone LWC development, standard Flow embedding, or …
- `skills/omnistudio/omnistudio-lwc-omniscript-migration/SKILL.md` — Migrate classic Visualforce-based OmniScripts to LWC-based runtime with feature parity and regression testing. NOT for new OmniScript design.
- `skills/omnistudio/omnistudio-multi-language/SKILL.md` — Localize OmniScripts, FlexCards, and DataRaptors using Label-based translation, multi-language JSON, and locale-aware number/date formatting. NOT for Salesforce Translation Workbench alone.
- `skills/omnistudio/omnistudio-performance/SKILL.md` — Triggers: 'OmniScript slow', 'Integration Procedure timeout', 'DataRaptor cache', 'FlexCard loading too long', 'reduce API calls OmniStudio'. NOT for LWC performance outside of OmniScript runtime (use lwc-performance …
- `skills/omnistudio/omnistudio-remote-actions/SKILL.md` — Triggers: 'remote action', 'OmniScript action', 'IP action', 'Apex action element', 'VlocityOpenInterface2', 'Send/Response JSON Path'. NOT for Integration Procedure internal design (use integration-procedures) or …
- `skills/omnistudio/omnistudio-security/SKILL.md` — Triggers: 'OmniStudio security', 'guest user omniscript', 'DataRaptor CRUD FLS', 'OmniStudio Apex security', 'HTTP action data exposure'. NOT for general portal identity architecture or generic Apex security reviews …
- `skills/omnistudio/omnistudio-testing-patterns/SKILL.md` — testing or validating OmniStudio components — OmniScript preview, Integration Procedure step debugging, DataRaptor field-mapping validation, and …. NOT for Apex unit testing or standard Flow debugging.
- `skills/omnistudio/omnistudio-vs-flow-decision/SKILL.md` — Triggers: 'omnistudio or flow', 'omniscript vs screen flow', 'integration procedure vs subflow', 'flexcard vs lightning page'. NOT for general automation selection across Workflow/Process Builder/Apex (see …
- `skills/omnistudio/vlocity-to-native-omnistudio-migration/SKILL.md` — Triggers: Vlocity to OmniStudio migration, namespace migration, vlocity_ins to omnistudio, OmniStudio Migration Tool, DataRaptor namespace update, …. NOT for new OmniStudio setup in greenfield orgs, nor for migrating …

