---
name: omnistudio-metadata-management
description: "Use this skill when tracking, auditing, or cleaning up OmniStudio component dependencies and cross-references — covering the four OmniStudio metadata API types (OmniProcess, OmniDataTransform, OmniUiCard, OmniInteractionConfig), dependency graph construction from embedded JSON bodies, impact analysis before deleting or modifying a component, and stale-component cleanup. Trigger keywords: OmniStudio metadata types, OmniStudio dependency tracking, FlexCard DataRaptor dependency, OmniScript Integration Procedure reference, OmniStudio component cleanup, metadata impact analysis. NOT for DataPack export/import mechanics (use data/omnistudio-datapack-migration), standard Salesforce Metadata API coverage (use a metadata coverage skill), or OmniStudio CI/CD pipeline automation."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "need to find all OmniStudio components that depend on a specific DataRaptor or Integration Procedure before deleting it"
  - "Tooling API MetadataComponentDependency query returns no results for OmniStudio cross-component references"
  - "trying to build a full dependency map of FlexCards, OmniScripts, and DataRaptors in a Salesforce org"
  - "need to identify stale or unused OmniStudio components for cleanup before a major release"
  - "impact analysis required before modifying an Integration Procedure that may be referenced by multiple OmniScripts"
  - "OmniStudio Metadata API Support must be enabled uniformly across sandboxes and production for reliable deployments"
tags:
  - omnistudio
  - metadata
  - dependencies
  - impact-analysis
  - omnistudio-metadata-management
  - flexcard
  - omniscript
  - dataraptor
  - integration-procedure
inputs:
  - "List of OmniStudio component names or types to analyze (OmniScript, Integration Procedure, DataRaptor, FlexCard)"
  - "Org type and runtime mode (Standard Runtime vs Package Runtime)"
  - "Whether OmniStudio Metadata API Support is enabled in the target org"
  - "Scope of analysis: single component, domain, or full org inventory"
outputs:
  - "Dependency graph showing which OmniStudio components reference which other components"
  - "Impact list — all components that call or embed a target component"
  - "Stale component candidates — components with no inbound references"
  - "Metadata API enablement status and remediation steps if mixed-mode is detected"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-15
---

# OmniStudio Metadata Management

This skill activates when a practitioner needs to track, audit, or clean up OmniStudio component dependencies and cross-references. It covers how to build accurate dependency graphs from the four OmniStudio metadata API types, why the standard Tooling API MetadataComponentDependency object does not resolve embedded JSON references between OmniStudio components, and how to enable and enforce OmniStudio Metadata API Support uniformly across an org pipeline.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether OmniStudio Metadata API Support is enabled in the org. This setting must be on before OmniStudio components appear as the correct metadata types (OmniProcess, OmniDataTransform, OmniUiCard, OmniInteractionConfig) in retrieve/deploy operations. Without it, components deploy as Vlocity-namespace sObjects, not as standard metadata.
- Confirm the org is running Standard Runtime (OmniStudio on Core). Mixed-mode pipelines — where some orgs use Standard Runtime with Metadata API Support and others use legacy Package Runtime with DataPacks — cannot be deployed reliably and produce metadata type mismatches.
- The most common wrong assumption: that the Tooling API MetadataComponentDependency object will reveal cross-component references such as which FlexCards embed a given DataRaptor, or which OmniScripts invoke a given Integration Procedure. These references are stored as embedded JSON inside the component body, not as explicit dependency edges in the Tooling API graph.
- As of Spring '25, automated dependency resolution and atomic deployment of OmniStudio component trees is not yet shipped. Salesforce announced roadmap items for automated dependency management in February 2026, targeted mid-2026, but they are not available in production orgs as of this writing.

---

## Core Concepts

### The Four OmniStudio Metadata API Types

OmniStudio Metadata API Support introduces four metadata types that replace legacy Vlocity DataPack-based deployment for Standard Runtime orgs:

| Metadata Type | Covers |
|---|---|
| `OmniProcess` | OmniScripts and Integration Procedures |
| `OmniDataTransform` | DataRaptors (Extract, Load, Transform) |
| `OmniUiCard` | FlexCards |
| `OmniInteractionConfig` | Interaction Launcher configurations |

Each type exposes the component as a retrievable/deployable metadata file rather than a DataPack JSON blob. The component body is still a rich JSON structure containing the full definition — element tree, actions, remote calls, and embedded references to other components.

OmniStudio Metadata API Support must be enabled in every org that participates in a deployment pipeline. A pipeline that mixes orgs with the setting enabled and orgs without it will encounter metadata type mismatches and deployment failures because the component representation differs between modes.

### Embedded JSON References Are Not Tooling API Dependency Edges

The Tooling API `MetadataComponentDependency` object is the standard platform mechanism for dependency tracking. For many metadata types it works correctly — for example, it resolves Apex class references, Flow references to custom objects, and LWC component composition graphs.

For OmniStudio components, `MetadataComponentDependency` does not resolve cross-component references. A FlexCard that invokes a DataRaptor stores that reference inside its `propertySet` JSON body as a string field (`dataRaptorBundleName`). A FlexCard that calls an Integration Procedure stores the reference inside `actionList[].actionAttributes.remoteClass`. An OmniScript that calls an Integration Procedure stores the reference inside `childElements[].propertySet.remoteClass`. None of these fields are exposed as tooling API dependency edges.

This means that querying `MetadataComponentDependency` for OmniStudio components returns only structural metadata relationships (such as a component belonging to a namespace), not the meaningful cross-component call graph. Practitioners who rely on this query to build impact-analysis lists will see an incomplete or empty graph and will incorrectly conclude that a component has no dependents.

### Dependency Resolution Requires JSON Body Parsing

Because cross-component references live inside embedded JSON, the only reliable way to build an OmniStudio dependency graph is to:

1. Retrieve all OmniStudio metadata files for the org using `sf project retrieve start` with the four metadata types.
2. Parse each component's JSON body and extract the cross-reference fields for the relevant component type.
3. Build an in-memory graph of caller → callee relationships.
4. Run reachability or impact analysis over that graph.

Key JSON paths to extract for each component type:

- **OmniUiCard (FlexCard):** `propertySet.dataRaptorBundleName` (DataRaptor reference), `actionList[*].actionAttributes.remoteClass` (Integration Procedure or OmniScript reference)
- **OmniProcess (OmniScript):** `childElements[*].propertySet.remoteClass` (Integration Procedure reference), `childElements[*].propertySet.dataRaptorBundleName` (DataRaptor reference in Integration Procedure steps)
- **OmniProcess (Integration Procedure):** `childElements[*].propertySet.procedureName` (nested IP reference), `childElements[*].propertySet.dataRaptorBundleName` (DataRaptor reference)

References use the component's API name, not its Salesforce ID, so the graph can be constructed from retrieved metadata files without org connectivity after the initial retrieve.

### OmniStudio Metadata API Support Enablement Requirements

Enabling OmniStudio Metadata API Support is a one-way toggle at the org level. Once enabled, OmniStudio components are exposed as the four metadata types and can no longer be deployed via DataPacks in that org. The setting must be consistent across every org in the pipeline — dev sandboxes, QA, UAT, staging, and production must all have the same setting.

If a pipeline mixes modes — one sandbox has Metadata API Support enabled while another does not — the deployed metadata representation will be incompatible. A retrieve from the Standard Runtime org produces `OmniProcess` XML; deploying that XML to a legacy org without the setting enabled fails because the metadata type is not recognized.

---

## Common Patterns

### Pattern: Full Org OmniStudio Dependency Graph

**When to use:** Before a major refactor, large deletion, or component rename that could break calling components in production.

**How it works:**
1. Retrieve all four OmniStudio metadata types from the target org: `sf project retrieve start --metadata OmniProcess OmniDataTransform OmniUiCard OmniInteractionConfig`
2. Parse each retrieved XML file. The component body is base64-encoded JSON inside the `<content>` element; decode it first.
3. For each FlexCard, extract `propertySet.dataRaptorBundleName` and all `actionList[*].actionAttributes.remoteClass` entries.
4. For each OmniScript and Integration Procedure (`OmniProcess`), extract all `childElements[*].propertySet.remoteClass` and `childElements[*].propertySet.dataRaptorBundleName` entries.
5. Build a dictionary: `{callee_api_name: [list of caller api names]}`.
6. To find all dependents of a target component, look up its API name in the dictionary.

**Why not the alternative:** Querying `MetadataComponentDependency` via Tooling API returns no cross-component edges for OmniStudio components. An impact analysis built on that query will miss all actual dependencies and give a false "safe to delete" signal.

### Pattern: Stale Component Identification

**When to use:** Periodic org hygiene, pre-release cleanup, or license usage reduction.

**How it works:**
1. Build the full dependency graph as above.
2. Collect the set of all components that appear as a callee (are referenced by at least one other component).
3. Collect the set of all components that appear as a caller.
4. Components that appear in neither set — not called by anything and not calling anything — are leaf nodes with no inbound or outbound references. These are stale candidates.
5. Cross-reference against recently-active usage logs (OmniProcess execution events in Event Monitoring if available) before deleting — a FlexCard may be launched directly from an App Page and have no JSON-body reference from another OmniStudio component.
6. Archive stale components by setting them to Inactive status before deletion; maintain a list for audit.

**Why not the alternative:** Deleting without the dependency graph risks removing components that are called by others or that call shared DataRaptors — orphaning callers that fail silently at runtime.

### Pattern: Pre-Deletion Impact Check

**When to use:** Any time a single OmniStudio component is being deleted, renamed, or substantially reworked.

**How it works:**
1. Build the caller-callee graph (or use a previously generated snapshot if recent).
2. Look up the target component's API name as a callee.
3. Report all callers. Review each caller to determine whether the reference can be updated or whether the caller's behavior changes.
4. If callers exist: update all calling components to reference the new API name or replacement component before removing the original.
5. After updates: re-retrieve metadata, re-parse, and confirm the deleted component's API name no longer appears in any callee list.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to find all OmniStudio components that call a specific DataRaptor | Retrieve + JSON body parse; do NOT use Tooling API MetadataComponentDependency | Tooling API does not surface embedded JSON references |
| Need to determine whether it is safe to delete an OmniScript | Build full caller-callee graph from retrieved metadata; check for inbound references | Risk of orphaning callers that fail at runtime |
| Org pipeline mixes Metadata-API-enabled and DataPack-mode orgs | Block deployment until all orgs enable OmniStudio Metadata API Support uniformly | Mixed-mode deployment causes metadata type mismatch failures |
| Need automated dependency graph generation in CI/CD | Implement custom JSON parsing step in pipeline; do NOT rely on Tooling API | No native platform tooling currently resolves OmniStudio cross-component edges |
| Planning to use upcoming Salesforce automated dependency management | Wait for mid-2026 GA release; do not architect around a roadmap feature | Roadmap announced Feb 2026 but not yet shipped as of Spring '25 |
| Auditing for stale / unused OmniStudio components | Build dependency graph + check against no-inbound-reference set | Components with no callers are candidates for archiving |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm OmniStudio Metadata API Support is enabled in the org and that all orgs in the pipeline share the same setting — if any org in the pipeline has it disabled, stop and resolve the mixed-mode conflict first.
2. Retrieve all four OmniStudio metadata types from the org: `sf project retrieve start --metadata OmniProcess OmniDataTransform OmniUiCard OmniInteractionConfig --target-org <alias>`.
3. For each retrieved file, decode the base64 JSON body from inside the `<content>` XML element and save it as a parseable JSON object.
4. Parse each component's JSON body using the type-specific reference field paths (see Core Concepts) to extract all cross-component references (DataRaptor names, Integration Procedure names, OmniScript names).
5. Build the caller-callee dictionary from the extracted references; verify the graph by spot-checking a known FlexCard → DataRaptor relationship.
6. For impact analysis: look up the target component's API name as a callee and list all callers; communicate these to the practitioner before any change is made.
7. For stale-component identification: compare all component API names against the set of components that appear as callees; report components with zero inbound references for archival review.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] OmniStudio Metadata API Support confirmed enabled in all orgs in the pipeline
- [ ] All four metadata types retrieved: OmniProcess, OmniDataTransform, OmniUiCard, OmniInteractionConfig
- [ ] JSON body decoded and parsed for each component (not just XML outer structure)
- [ ] Reference extraction used type-specific JSON field paths, not Tooling API MetadataComponentDependency
- [ ] Caller-callee graph built and spot-checked against a known cross-component relationship
- [ ] Impact list reviewed by practitioner before any deletion or rename
- [ ] Stale components confirmed against usage logs or event monitoring before deletion recommendation
- [ ] No mixed-mode orgs left in the pipeline

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **MetadataComponentDependency returns zero edges for OmniStudio cross-component calls** — The Tooling API dependency object tracks explicit metadata relationships, not embedded JSON body references. Querying it for `OmniUiCard` or `OmniProcess` components will return results only for namespace-level structural relationships, not for the FlexCard → DataRaptor or OmniScript → Integration Procedure call chains that matter operationally. Practitioners who trust this query will delete a DataRaptor that is still in active use by multiple FlexCards.
2. **OmniStudio Metadata API Support is a one-way toggle with pipeline-wide impact** — Enabling the setting in one org and not another creates a split-mode pipeline where component representations are incompatible. This is not detectable from within a single org — the failure only surfaces when a deployment from the Metadata-API-mode org is applied to a DataPack-mode org or vice versa.
3. **Component API names in JSON bodies are case-sensitive** — When parsing embedded references to match against component inventory, exact case must be preserved. A DataRaptor named `GetAccountData` will not match a reference to `getAccountData` in the parsed graph, creating false negatives in the dependency check.
4. **FlexCards can reference other FlexCards as child cards** — Nested FlexCard references (`childCards`) are stored in the `childElements` array of the parent FlexCard's JSON body. An impact analysis that only checks DataRaptor and Integration Procedure references will miss FlexCard-to-FlexCard dependency chains.
5. **Automated dependency management is not yet available** — Salesforce announced automated OmniStudio dependency management and atomic deployment on their February 2026 roadmap post, targeting mid-2026. As of Spring '25, this feature has not shipped. Pipeline designs that assume it is available will fail in production orgs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OmniStudio dependency graph | Caller-callee dictionary keyed by component API name, built from parsed JSON bodies |
| Impact list | All caller components for a specified target component, used before deletion or rename |
| Stale component report | Components with no inbound references from other OmniStudio components, flagged for archival review |
| Metadata API enablement audit | Per-org confirmation that OmniStudio Metadata API Support is enabled uniformly across the pipeline |

---

## Related Skills

- `data/omnistudio-datapack-migration` — use for DataPack export/import mechanics in Package Runtime orgs; this skill covers metadata structure, not DataPack execution
- `devops/metadata-coverage-and-dependencies` — use for standard Tooling API MetadataComponentDependency patterns on non-OmniStudio metadata types
- `omnistudio/omnistudio-deployment-datapacks` — use for DataPack CLI configuration and deployment setup
