# Gotchas — OmniStudio Metadata Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: MetadataComponentDependency Is Blind to OmniStudio Cross-Component References

**What happens:** Querying `MetadataComponentDependency` via the Tooling API for OmniStudio component types (`OmniUiCard`, `OmniProcess`, `OmniDataTransform`) returns only structural namespace-level relationships, not the call-graph edges between components. A FlexCard that calls a DataRaptor, an OmniScript that invokes an Integration Procedure, or an Integration Procedure that calls another Integration Procedure — none of these produce a `MetadataComponentDependency` record. The Tooling API sees the component as a monolithic blob.

**When it occurs:** Any time a practitioner or tool uses the Tooling API dependency query to perform impact analysis or safety checks before deleting, renaming, or refactoring an OmniStudio component. It also occurs when CI/CD pipelines run standard dependency checks using the Tooling API as a pre-flight before deployment.

**How to avoid:** Never use `MetadataComponentDependency` as the sole source of truth for OmniStudio dependency analysis. Build the dependency graph by retrieving all four OmniStudio metadata types and parsing the embedded JSON body of each component. Use the type-specific JSON field paths documented in SKILL.md Core Concepts to extract actual cross-component references.

---

## Gotcha 2: OmniStudio Metadata API Support Is Org-Wide and One-Way

**What happens:** OmniStudio Metadata API Support, once enabled in an org, converts all OmniStudio components from their legacy Vlocity-namespace DataPack representation to the standard metadata API format (OmniProcess, OmniDataTransform, OmniUiCard, OmniInteractionConfig). There is no org-level rollback. Any deployment pipeline that mixes enabled and disabled orgs will fail because the metadata type names and file formats differ between modes — `OmniProcess` XML from an enabled org cannot be deployed to a disabled org that expects DataPack JSON, and vice versa.

**When it occurs:** When a team enables the setting in sandbox environments to modernize their pipeline but does not update UAT or production at the same time. The failure surfaces during the first deployment attempt from the enabled org to a disabled org — typically at the UAT gate or production deploy stage, not earlier.

**How to avoid:** Treat the enablement as a pipeline-wide migration event. Enable OmniStudio Metadata API Support in all orgs in the pipeline in sequence (development sandboxes → QA → UAT → production), confirming each org's background migration of existing components is complete before enabling the next. Add a pre-deploy pipeline check that confirms the setting is active in both source and target orgs before running `sf project deploy start`.

---

## Gotcha 3: Case-Sensitive API Names in Embedded JSON References

**What happens:** Cross-component references stored inside OmniStudio JSON bodies use the API name of the called component as a plain string value. These string comparisons are case-sensitive. A DataRaptor registered in the org as `GetAccountData` will not match a reference in a FlexCard's JSON body that spells it `getAccountData` or `GetaccountData`. When building the dependency graph from parsed JSON, such mismatched references appear as dangling edges — callers that reference a component API name that does not exist in the inventory — producing false negatives in the impact analysis.

**When it occurs:** Most commonly introduced when components are manually renamed in one direction but not updated in callers, or when component names are typed directly into JSON configuration rather than selected from a dropdown in the designer UI. Also occurs in orgs that migrated from an older OmniStudio version where naming conventions were inconsistent.

**How to avoid:** Normalize all API names to a consistent case convention before building the graph. During parsing, flag any extracted reference that does not exactly match a known component API name as an unresolved reference requiring manual review. Do not discard unresolved references — they are symptoms of either misconfigured components or naming drift that must be corrected before the calling component will function reliably.

---

## Gotcha 4: FlexCard-to-FlexCard Child Card References Are a Separate Dependency Class

**What happens:** A FlexCard can embed another FlexCard as a child card. This relationship is stored in the parent FlexCard's JSON body under the `childElements` array, where child card references appear alongside standard action elements. Impact analyses that only look for DataRaptor and Integration Procedure references in `propertySet` and `actionList` fields will miss these nested FlexCard references. Deleting a child FlexCard that is embedded in multiple parent FlexCards breaks those parents at runtime without any compile-time or deploy-time error.

**When it occurs:** In orgs that use a card-composition pattern — building a library of small reusable FlexCards (address cards, contact summary cards, product tiles) and embedding them in larger composite cards. The child cards may appear infrequently used based on a naive inbound-reference check that only inspects non-FlexCard callers.

**How to avoid:** When parsing FlexCard JSON bodies for cross-component references, explicitly extract `childElements[*]` entries that have `type: "card"` or equivalent child-card type markers. Include these in the callee dictionary as a separate reference class. A FlexCard is never safe to delete without first confirming it has zero inbound references from both non-FlexCard callers and parent FlexCard child-card entries.

---

## Gotcha 5: Automated Dependency Management Is a Roadmap Feature, Not a Shipped Capability

**What happens:** Salesforce announced automated OmniStudio dependency management and atomic deployment of component trees as a roadmap item in a February 2026 developer blog post, targeting mid-2026. As of Spring '25, this capability is not available in production orgs. Teams that architect their pipeline around automated dependency resolution — expecting the platform to sequence deployments in dependency order or to block deployment if dependencies are missing — will find no such behavior in production. Deployment continues to require manually-ordered component sequences.

**When it occurs:** When pipeline designs or architectural proposals reference the February 2026 blog announcement as if the feature is currently available, or when teams delay building manual dependency-tracking tooling in anticipation of the platform providing it automatically.

**How to avoid:** Build manual dependency graph tooling using the JSON-parse approach described in this skill. Do not architect production pipelines around roadmap features. Revisit automated dependency management as a capability upgrade once Salesforce confirms GA availability and publishes the enabling documentation. Track the official OmniStudio release notes for the mid-2026 release cycle.
