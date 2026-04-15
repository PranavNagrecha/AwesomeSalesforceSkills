# Well-Architected Notes — OmniStudio Metadata Management

## Relevant Pillars

- **Operational Excellence** — Primary pillar. Managing OmniStudio dependencies accurately is a prerequisite for reliable deployments, safe component changes, and sustainable org hygiene. Without an accurate dependency graph, change management and impact analysis cannot be performed reliably. Stale component accumulation increases deployment surface and makes each release riskier.
- **Reliability** — Cross-component references that are not tracked cause silent runtime failures when a called component is deleted or renamed. Accurate dependency tracking directly reduces the incidence of runtime errors caused by broken OmniStudio call chains.
- **Security** — Indirectly relevant. Stale OmniStudio components may retain access to sensitive DataRaptors or Integration Procedures that have been superseded by more secure implementations. Cleanup reduces attack surface and ensures that only current, reviewed components are active.
- **Performance** — Not a primary pillar for this skill. Dependency tracking has no direct performance impact on running components, though identifying and deactivating unused components reduces the volume of metadata the platform must load and index.
- **Scalability** — Not a primary pillar. Relevant at the pipeline level: as component volume grows, automated JSON-parse dependency resolution scales better than manual tracking, but no platform-native scalable tooling exists until the mid-2026 roadmap feature ships.

## Architectural Tradeoffs

**Manual JSON parsing vs. Tooling API dependency query:**
The Tooling API MetadataComponentDependency approach is lower-effort and is the standard pattern for most Salesforce metadata types. For OmniStudio components it is unreliable — it misses all embedded JSON cross-component references. The correct approach (retrieve + parse JSON bodies) requires custom tooling and more implementation effort but produces accurate results. The tradeoff is implementation cost vs. correctness. There is no middle ground: a dependency graph that is known to be incomplete is more dangerous than no graph, because it gives a false "safe to proceed" signal.

**Uniform Metadata API Support enablement vs. phased rollout:**
Enabling OmniStudio Metadata API Support across all orgs simultaneously reduces the risk of mixed-mode pipeline failures but requires coordinating a migration event across all environments at once. A phased rollout (sandbox first, production later) is operationally safer but creates a window during which the pipeline is in mixed mode and deployments will fail. The correct tradeoff is to perform the migration in rapid sequence — not simultaneously and not with long delays between environments.

**Building custom dependency tooling vs. waiting for platform automation:**
As of Spring '25, the platform does not provide automated OmniStudio dependency management. Teams must decide whether to invest in building custom JSON-parse tooling now or wait for the mid-2026 roadmap feature. For teams with more than ~50 active OmniStudio components, the risk of untracked dependencies justifies building tooling now rather than waiting.

## Anti-Patterns

1. **Relying on Tooling API MetadataComponentDependency for OmniStudio impact analysis** — This query does not surface embedded JSON cross-component references. An impact analysis built on it will silently miss all FlexCard → DataRaptor and OmniScript → Integration Procedure dependencies, producing dangerously incomplete results that are mistaken for "no dependents."

2. **Running a mixed-mode deployment pipeline** — Operating a pipeline where some orgs have OmniStudio Metadata API Support enabled and others do not guarantees deployment failures at the boundary between modes. The failure is non-obvious (metadata type unrecognized) and can block release cycles at critical stages such as UAT or production.

3. **Deleting or renaming OmniStudio components without a dependency check** — In the absence of platform-enforced referential integrity for OmniStudio cross-component references, deleting a called component will not produce a warning or error at delete time. The failure is deferred to runtime, when the calling component attempts to resolve the missing reference.

## Cross-Skill References

- `data/omnistudio-datapack-migration` — DataPack execution mechanics for Package Runtime orgs; distinct from metadata type management for Standard Runtime orgs
- `devops/metadata-coverage-and-dependencies` — standard Tooling API dependency patterns for non-OmniStudio metadata types where MetadataComponentDependency is reliable

## Official Sources Used

- OmniStudio Metadata API Types — Industries Common Resources Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/omnistudio_metadata_api_parent.htm
- Enable OmniStudio Metadata API Support — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.os_enable_omnistudio_metadata_api_support.htm
- OmniStudio Deployments Made Easier — Salesforce Developer Blog, Feb 2026 — https://developer.salesforce.com/blogs/2026/02/omnistudio-deployments-made-easier-whats-coming-on-the-salesforce-roadmap
- What's New in Salesforce OmniStudio Standard Designers — Salesforce Developer Blog, Mar 2026 — https://developer.salesforce.com/blogs/2026/03/whats-new-in-salesforce-omnistudio-standard-designers
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
