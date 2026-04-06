# Well-Architected Alignment — Metadata Coverage and Dependencies

## Adaptability Pillar

The Salesforce Well-Architected Adaptability pillar requires that systems are designed to evolve over time without accumulating brittleness or technical debt. Metadata coverage awareness and dependency management are foundational controls for adaptability.

Key adaptability practices this skill addresses:
- **Know what you can automate before you commit to a channel** — choosing unlocked packages without confirming metadata type coverage leads to manual workarounds that erode the packaging model over time.
- **Design for safe removal** — understanding the dependency graph before deleting or refactoring components prevents cascading failures and allows confident evolution of the org's metadata landscape.
- **Define modular boundaries** — dependency-graph-informed packaging creates loosely coupled modules that can be updated, replaced, or retired independently.
- **Plan for coverage changes across releases** — metadata coverage improves each Salesforce release. Re-evaluating coverage gaps after major releases ensures the architecture takes advantage of newly supported types.

## Operational Excellence Pillar

The Operational Excellence pillar covers the processes, tooling, and team practices needed to manage Salesforce systems reliably over time.

Key operational excellence practices this skill addresses:
- **Impact analysis as a deployment gate** — querying MetadataComponentDependency before any destructive change is an operational control that prevents deployment failures.
- **Dependency graph as living documentation** — the Tooling API dependency graph is always current. Using it as the source of truth for component relationships is more reliable than manually maintained architecture diagrams.
- **Runbook documentation for unsupported types** — when metadata types are unsupported in the deployment channel, the workaround steps must be documented in the release runbook to avoid configuration drift.
- **Bulk extraction for auditing** — periodic full-org dependency extraction via Bulk API 2.0 provides a baseline for measuring coupling trends and technical debt.

---

## Official Sources Used

- Metadata Coverage Report — canonical source for metadata type support across deployment channels
  URL: https://developer.salesforce.com/docs/metadata-coverage
- Metadata API Developer Guide — retrieve/deploy behavior, unsupported types list, metadata type reference
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- MetadataComponentDependency (Tooling API) — dependency graph object definition and query semantics
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_metadatacomponentdependency.htm
- MetadataComponentDependency Bulk API 2.0 Usage — bulk extraction of dependency data
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_metadatacomponentdependency_bulk2_usage.htm
- Salesforce Well-Architected Framework Overview — adaptability and operational excellence pillars framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce DX Developer Guide — metadata coverage in SFDX context, source tracking
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_supported_mdapi_types.htm
- Unsupported Metadata Types — official list of types not available through Metadata API
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_unsupported_types.htm
