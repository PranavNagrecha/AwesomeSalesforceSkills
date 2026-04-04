# Well-Architected Notes — Metadata API and Package.xml

## Relevant Pillars

- **Operational Excellence** — The Metadata API and package.xml are the foundational mechanism for repeatable, automated deployment pipelines. Correct package.xml construction directly determines whether deployments are predictable and auditable. Poorly constructed manifests lead to partial or incorrect deployments that are difficult to diagnose and repeat.
- **Reliability** — Correct deployment ordering (using destructiveChangesPre/Post), proper test level selection, and per-component code coverage verification are the primary reliability controls for metadata changes promoted to production.
- **Security** — The "Modify Metadata Through Metadata API Functions" permission grants significant access to org configuration including Apex and Profiles. Incorrect permission delegation (e.g., granting Modify All Data instead of the scoped metadata permission) violates least-privilege principles.

## Architectural Tradeoffs

**File-based vs CRUD-based API:** File-based deploy/retrieve is asynchronous and optimized for bulk metadata movement — ideal for CI/CD pipelines. CRUD-based calls are synchronous and act on one component at a time — better for programmatic org setup scripts or ISV tooling that needs immediate confirmation. Do not use CRUD-based calls for large-scale migrations; they do not scale to the same throughput as file-based operations.

**Wildcard retrieval vs explicit manifest:** Wildcards are convenient for initial org captures but carry risk in incremental workflows — they will retrieve all components of a type and can silently miss standard objects. Explicit manifests are more brittle to maintain but provide deterministic retrieval. For CI/CD, prefer explicit manifests. For initial org-to-source-control migrations, use wildcards first and then audit for missing standard object customizations.

**Test level selection in production:** Choosing `RunSpecifiedTests` accelerates deployments but requires the team to manually verify per-class coverage. `RunLocalTests` is slower but provides a safety net. `RunRelevantTests` (Beta, API v58+) offers an automatic middle ground. The right choice depends on deployment frequency, test suite size, and confidence in coverage analysis tooling.

## Anti-Patterns

1. **Committing stale package.xml with outdated `<version>` tags** — Using an old API version in package.xml silently downgrades the Metadata API behavior for retrieves and deploys, potentially missing new metadata types, serialization changes, or behavior fixes introduced in newer API versions. Always update `<version>` when upgrading to a new Salesforce release.

2. **Relying on org-wide code coverage instead of per-component coverage** — Teams that check the aggregate coverage number in Setup miss the individual class/trigger requirement. A deployment to production fails when any single deployed Apex component falls below 75% coverage, regardless of the org total. Build per-component coverage reporting into CI pipelines.

3. **Using `destructiveChanges.xml` (pre-deletion) when dependencies exist** — Attempting to delete a component that is referenced by other metadata in the same deployment fails when deletions run first (the default). Use `destructiveChangesPost.xml` to ensure referencing components are updated before the deletion is attempted, keeping the operation atomic.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — primary source for deploy/retrieve behavior, package.xml structure, destructiveChanges semantics, and test level options
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Operational Excellence and Reliability pillar framing for deployment quality
