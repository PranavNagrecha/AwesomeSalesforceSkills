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
- `skills/omnistudio/calculation-procedure-design/SKILL.md` — Design Calculation Procedures and Matrices for pricing, rating …. Triggers: calculation procedure, calculation matrix, expression set, decision matrix. NOT for Salesforce CPQ price rules — use admin/cpq-pricing-rules.
- `skills/omnistudio/calculation-procedures/SKILL.md` — Triggers: calculation procedure, expression set, calculation matrix, decision matrix, pricing calculation, lookup step, matrix versioning. NOT for pricing/rating design … use omnistudio/calculation-procedure-design
- `skills/omnistudio/dataraptor-load-and-extract/SKILL.md` — Build or debug DataRaptor Extract and Load — multi-object extracts …. Triggers: DataRaptor Extract, DataRaptor Load, Turbo Extract debug. NOT for Extract vs Load design tradeoffs — use omnistudio/dataraptor-patterns.
- `skills/omnistudio/dataraptor-patterns/SKILL.md` — Triggers: DataRaptor Extract, Turbo Extract, DataRaptor Load, DataRaptor Transform, OmniStudio data mapping. NOT for Extract/Load debugging — use omnistudio/dataraptor-load-and-extract.
- `skills/omnistudio/dataraptor-transform-optimization/SKILL.md` — DataRaptor Transform operations are slow, hit governor limits, or use Apex where formula …. Triggers: 'dataraptor transform slow'. NOT for DataRaptor Extract or Load performance — use omnistudio/dataraptor-patterns.
- `skills/omnistudio/document-generation-omnistudio/SKILL.md` — Generating documents (PDF, DOCX, PPTX) from OmniStudio using Document Templates, OmniDataTransform token mapping, and OmniScript or …. NOT for Salesforce CPQ document generation — use apex/fsc-document-generation.
- `skills/omnistudio/flexcard-container-composition/SKILL.md` — Triggers: flexcard, flex card composition, parent child flexcard, flexcard state, flexcard. NOT for the first-time FlexCard Hello-World, LWC alternatives, or Experience Cloud theming — use admin/flexcard-requirements.
- `skills/omnistudio/flexcard-design-patterns/SKILL.md` — Design FlexCard layout, data sources, states, actions, and child-card iteration. Triggers: FlexCard, card states, flyout, child card. NOT for FlexCard state across navigation — use omnistudio/flexcard-state-management.
- `skills/omnistudio/flexcard-state-management/SKILL.md` — Triggers: flexcard state, flexcard actions, flexcard refresh. NOT for FlexCard layout/design — use omnistudio/flexcard-design-patterns. NOT for admin requirements — use admin/flexcard-requirements.
- `skills/omnistudio/industries-api-extensions/SKILL.md` — Triggers: Insurance policy issuance API, endorsement API, TMF679, Communications Cloud REST API, Update Asset Status, Service Process API, …. NOT for designing the … use architect/industries-integration-architecture
- `skills/omnistudio/industries-cpq-vs-salesforce-cpq/SKILL.md` — comparing Industries CPQ (formerly Vlocity CPQ) with Salesforce CPQ (Revenue Cloud …. Triggers: Vlocity. NOT for implementing, configuring, or debugging either CPQ product — use architect/industries-cloud-selection.
- `skills/omnistudio/integration-procedure-cacheable-patterns/SKILL.md` — designing Integration Procedures (IPs) with platform cache to cut latency and callout load. Covers Cache Block …. NOT for general IP authoring or LWC client-side caching — use omnistudio/integration-procedures.
- `skills/omnistudio/integration-procedures/SKILL.md` — Triggers: 'integration procedure', 'IP', 'HTTP action', 'DataRaptor', 'rollbackOnError', 'failureResponse'. Triggers: 'integration procedure'. NOT for Apex-only integrations unless … use omnistudio/omnistudio-security
- `skills/omnistudio/omniscript-design-patterns/SKILL.md` — Triggers: 'omniscript design', 'too many steps in omniscript', 'save and resume omniscript', 'branching in omniscript', …. NOT for deep Integration Procedure design — use omnistudio/integration-procedures.
- `skills/omnistudio/omniscript-session-state/SKILL.md` — an OmniScript must persist mid-flow state across refresh, navigation, multi-device resume, or abandonment recovery. Covers session …. NOT for OmniScript UI step layout — use omnistudio/omniscript-design-patterns.
- `skills/omnistudio/omniscript-versioning/SKILL.md` — managing OmniScript versions: activating new versions, deactivating prior versions, testing a specific version …. NOT for OmniStudio deployment or DataPack migration (use omnistudio/omnistudio-deployment-datapacks).
- `skills/omnistudio/omnistudio-asynchronous-data-operations/SKILL.md` — Use Integration Procedures queues, DataRaptor Chain, and Remote Actions with async patterns for long-running OmniStudio flows. NOT for simple DataRaptor reads — use omnistudio/dataraptor-patterns.
- `skills/omnistudio/omnistudio-cache-strategies/SKILL.md` — Configure caching on DataRaptors and Integration Procedures …. Triggers: OmniStudio cache, DataRaptor cache, IP cache TTL. NOT for IP-specific cacheable design — use omnistudio/integration-procedure-cacheable-patterns.
- `skills/omnistudio/omnistudio-ci-cd-patterns/SKILL.md` — CI/CD pipelines for OmniStudio — DataPack export/import …. Triggers: OmniStudio CI/CD, DataPack pipeline, OmniStudio deployment. NOT for manual DataPack operations — use omnistudio/omnistudio-deployment-datapacks.
- `skills/omnistudio/omnistudio-custom-lwc-elements/SKILL.md` — Creating and integrating custom Lightning Web Components within OmniScripts: LWC override patterns, pubsub event handling …. NOT for standalone LWC development (use lwc/* skills) — use lwc/lwc-web-components-interop.
- `skills/omnistudio/omnistudio-debugging/SKILL.md` — Triggers: 'omniscript not working', 'dataraptor returns empty', 'integration procedure. NOT for Apex debugging, LWC console errors unrelated to OmniStudio, or Flow fault path d — use omnistudio/omnistudio-performance.
- `skills/omnistudio/omnistudio-deployment-datapacks/SKILL.md` — exporting, importing, or version-controlling OmniStudio components using DataPacks via the OmniStudio …. NOT for SFDX-based metadata deployment of non-OmniStudio components — use data/omnistudio-datapack-migration.
- `skills/omnistudio/omnistudio-error-handling-patterns/SKILL.md` — designing fault behavior across Integration Procedures …. Triggers: 'omnistudio error', 'integration procedure fault'. NOT for general Apex exception design or Flow fault paths — use data/omnistudio-metadata-management.
- `skills/omnistudio/omnistudio-field-mapping-governance/SKILL.md` — Govern DataRaptor field mappings to prevent runtime errors when source metadata changes: naming, versioning, and dependency tracking. NOT for DataRaptor authoring fundamentals — use data/omnistudio-metadata-management.
- `skills/omnistudio/omnistudio-lwc-integration/SKILL.md` — Triggers: embed omniscript in LWC, custom LWC element in OmniScript, call OmniScript from Lightning page, omnistudio-omni-script tag. NOT for standalone LWC development when … use lwc/component-communication
- `skills/omnistudio/omnistudio-lwc-omniscript-migration/SKILL.md` — Migrate classic Visualforce-based OmniScripts to LWC-based runtime with feature parity and regression testing. NOT for new OmniScript design — use omnistudio/omnistudio-lwc-integration.
- `skills/omnistudio/omnistudio-multi-language/SKILL.md` — Localize OmniScripts, FlexCards, and DataRaptors using Label-based translation, multi-language JSON, and locale-aware …. NOT for Salesforce Translation Workbench alone — use admin/multi-language-and-translation.
- `skills/omnistudio/omnistudio-performance/SKILL.md` — diagnosing or improving runtime performance in OmniStudio assets: slow …. NOT for LWC performance outside of OmniScript runtime (use lwc-performance skill) — use omnistudio/integration-procedure-cacheable-patterns.
- `skills/omnistudio/omnistudio-remote-actions/SKILL.md` — Triggers: 'remote action', 'OmniScript action', 'IP action', 'Apex action element'. NOT for Integration Procedure internal design or generic Apex callout patterns — use omnistudio/integration-procedures.
- `skills/omnistudio/omnistudio-security/SKILL.md` — Triggers: 'OmniStudio security', 'guest user omniscript', 'DataRaptor CRUD FLS', 'OmniStudio Apex security', 'HTTP action data exposure'. NOT for generic Apex security review when … use apex/apex-security-patterns
- `skills/omnistudio/omnistudio-testing-patterns/SKILL.md` — Test OmniStudio components — OmniScript preview, IP step debugging, DataRaptor …. Triggers: OmniStudio testing, UTAM automation, OmniScript test. NOT for live runtime debugging — use omnistudio/omnistudio-debugging.
- `skills/omnistudio/omnistudio-vs-flow-decision/SKILL.md` — Triggers: 'omnistudio or flow', 'omniscript vs screen flow'. NOT for general automation selection (use admin/process-automation-selection) — use architect/omnistudio-vs-standard-decision.
- `skills/omnistudio/vlocity-to-native-omnistudio-migration/SKILL.md` — Triggers: Vlocity to OmniStudio migration, namespace migration, vlocity_ins to omnistudio. NOT for greenfield OmniStudio setup or migrating between OmniStudio-native orgs — use omnistudio/omnistudio-deployment-datapacks.

