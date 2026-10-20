---
name: metadata-coverage-and-dependencies
description: "Assessing metadata type coverage across Salesforce deployment channels (Metadata API, SFDX, unlocked packages, managed packages) and mapping component dependency graphs using Tooling API MetadataComponentDependency. Use when planning packaging strategies, evaluating deployment risk, or performing impact analysis before component deletion. Trigger keywords: metadata coverage report, dependency graph, MetadataComponentDependency, impact analysis, unsupported metadata types, packaging eligibility. NOT for a deployment that already failed on an unsupported type — use devops/metadata-api-coverage-gaps. NOT for writing package.xml or running retrieve and deploy — use apex/metadata-api-and-package-xml."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Operational Excellence
tags:
  - metadata-api
  - metadata-coverage
  - dependency-graph
  - tooling-api
  - packaging
  - impact-analysis
  - MetadataComponentDependency
inputs:
  - Salesforce org edition and API version
  - List of metadata components under evaluation
  - Packaging strategy (unlocked, managed, or unpackaged)
  - Components targeted for deletion or refactoring
outputs:
  - Metadata coverage gap analysis per deployment channel
  - Component dependency graph (upstream and downstream)
  - Impact analysis report for deletion or refactoring candidates
  - Packaging eligibility assessment
  - Unsupported metadata type workaround recommendations
triggers:
  - "which metadata types are supported by Metadata API"
  - "how to check if a metadata type can go in an unlocked package"
  - "how to find all components that depend on a custom field"
  - "impact analysis before deleting an Apex class"
  - "dependency graph for packaging boundary decisions"
  - "MetadataComponentDependency query examples"
  - "unsupported metadata types workaround"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Metadata Coverage and Dependencies

## Overview

Every Salesforce org accumulates metadata over time. Before you can safely deploy, package, refactor, or delete any component, you need to answer two questions: (1) is this metadata type supported in the channel I plan to use, and (2) what other components depend on it?

The Metadata Coverage Report answers the first question. The Tooling API MetadataComponentDependency object answers the second. Together they form the foundation for packaging strategy, impact analysis, and modular architecture decisions.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which channel ships this metadata — Metadata API, unlocked, 2GP, 1GP? | Gotcha 5: unsupported types drop out | The coverage column to read |
| At which API version was coverage last checked? | Gotcha 2: coverage changes each release | A dated, versioned coverage record |
| Will automation gate releases on the dependency query? | Gotcha 1: the object's status is unverified | Whether a manual review must back it |
| Is any field or class referenced dynamically (strings, CMDT, templates)? | Gotcha 3: dynamic references are invisible | A text search alongside the query |
| How many dependency rows could the org return? | Gotcha 4: per-job limits and paging | Segmented extraction, row-count checks |
| Do candidate packages reference each other both ways? | Gotcha 6: circular dependencies aren't supported | A base package for shared components |
| Are standard fields counted as coupling? | Gotcha 7: they inflate metrics | Custom-only coupling counts |

A proper configuration records the channel, API version and dependency evidence behind each packaging decision, where "just doing it" discovers the unsupported type at subscriber install.

---

## Metadata Coverage Report

The Metadata Coverage Report is the canonical source of truth for which metadata types are supported across Salesforce deployment channels. Metadata API calls it "the ultimate source of truth for metadata coverage across several channels" — Metadata API, scratch org source tracking, unlocked packages, second-generation managed packages, classic managed packages (api_meta 264 L10250-10252); you don't have to be logged into an org to view it (L10253). The URL and "versioned by API release" are UNVERIFIED (2026-10-20).

The report covers support status across these channels:

| Channel | What it indicates |
|---|---|
| Metadata API | Retrieve and deploy via `sf project retrieve/deploy` or the SOAP/REST deploy endpoints. |
| Source Tracking | Whether changes to the type are tracked in scratch orgs and sandboxes for incremental pull/push. |
| Unlocked Packages | Whether the type can be included in an unlocked package. |
| 2GP Managed Packages | Second-generation managed package support. |
| 1GP Managed Packages | Classic (first-generation) managed package support. |

Each metadata type has one of three statuses per channel: **Supported**, **Not Supported**, or **Beta** (UNVERIFIED (2026-10-20): the report's status vocabulary is not in the corpus). Beta types may work but carry no forward-compatibility guarantee.

### How to Use the Coverage Report

1. Identify the deployment channel(s) your project uses (e.g., unlocked packages for modular delivery, Metadata API for sandbox-to-production promotion).
2. For each metadata type in scope, check the coverage report at your target API version.
3. Flag any type that is **Not Supported** or **Beta** in your channel as a packaging risk.
4. For unsupported types, determine a workaround: manual configuration steps, post-deployment scripts, or separate unpackaged metadata promotion.

### Common Unsupported or Partially Supported Types

Not all metadata is created equal. Some frequently encountered types with coverage gaps include (UNVERIFIED (2026-10-20): every row below is a field observation, not a corpus statement; `KnowledgeSettings`, `Territory2Model`, `StandardValueSet` and `PlatformEncryptionSettings` all exist as Metadata API types — api_meta 264 L123802, L137016, L134303, L127832 — so check the report per type):

| Type | Coverage gap |
|---|---|
| Knowledge Settings | Often unsupported in packages; requires post-deploy configuration. |
| Territory Management | Enterprise Territory Management metadata has partial Metadata API support; packaging support varies by type and version. |
| Certain Standard Value Sets | Some picklist standard value sets are not retrievable or deployable. |
| Einstein/AI Configuration | Prediction builders, recommendation strategies, and some AI features have limited or no Metadata API coverage. |
| Shield Platform Encryption | Encryption policies and tenant secrets are not deployable via Metadata API. |

Always verify against the current API version. Coverage improves with each release.

---

## Unsupported Metadata Types

Corrected 2026-10-20: the Metadata API guide does not carry its own list; it says some features' types "can't be retrieved or deployed with Metadata API. To make changes to these types, you must do it manually in each of your organizations", that types "may also be unsupported in source tracking, packaging, and change sets", and "For a complete list ... see Metadata Coverage" (api_meta 264 L10256-10260). The old text claimed an explicit list in the guide and a Tooling API alternative (UNVERIFIED (2026-10-20)).

When an unsupported type is part of your solution architecture, document it as a manual deployment step in your release runbook. Do not assume future support — plan for the current state.

---

## MetadataComponentDependency (Tooling API)

The `MetadataComponentDependency` object in the Tooling API provides a read-only, queryable dependency graph for metadata components in an org (UNVERIFIED (2026-10-20): the Tooling API guide that defines `MetadataComponentDependency` is not in the corpus; no corpus line names the object; the field names, read-only status and Bulk API 2.0 support below are unverified with it). Each record represents a directional dependency: component A depends on component B.

### Key Fields

| Field | Description |
|-------|-------------|
| `MetadataComponentId` | The ID of the dependent component (the one that references another). |
| `MetadataComponentName` | Name of the dependent component. |
| `MetadataComponentType` | Type of the dependent component (e.g., `ApexClass`, `CustomField`). |
| `RefMetadataComponentId` | The ID of the referenced component (the one being depended upon). |
| `RefMetadataComponentName` | Name of the referenced component. |
| `RefMetadataComponentType` | Type of the referenced component. |

### Querying Dependencies

MetadataComponentDependency is a read-only Tooling API object. It supports SOQL queries through the Tooling API endpoint (`/services/data/vXX.0/tooling/query/`) and through Bulk API 2.0 for large-scale extraction.

**Find all components that depend on a specific custom field:**

```sql
SELECT MetadataComponentName, MetadataComponentType
FROM MetadataComponentDependency
WHERE RefMetadataComponentName = 'My_Custom_Field__c'
  AND RefMetadataComponentType = 'CustomField'
```

**Find all dependencies of a specific Apex class:**

```sql
SELECT RefMetadataComponentName, RefMetadataComponentType
FROM MetadataComponentDependency
WHERE MetadataComponentName = 'MyApexClass'
  AND MetadataComponentType = 'ApexClass'
```

**Export the full dependency graph (use Bulk API 2.0 for orgs with >2,000 components):**

```sql
SELECT MetadataComponentName, MetadataComponentType,
       RefMetadataComponentName, RefMetadataComponentType
FROM MetadataComponentDependency
```

### Bulk API 2.0 for Large Dependency Graphs

For production orgs with thousands of metadata components, the standard Tooling API query may hit governor limits. Salesforce supports querying `MetadataComponentDependency` through Bulk API 2.0, which can return up to 100,000 records per query job (UNVERIFIED (2026-10-20); Bulk API 2.0 results page with the `Sforce-Locator` header, api_asynch 264 L3295-3296). This is the recommended approach for full-org dependency extraction.

```bash
sf data query --query "SELECT MetadataComponentName, MetadataComponentType, RefMetadataComponentName, RefMetadataComponentType FROM MetadataComponentDependency" --use-tooling-api --bulk --target-org myOrg
```

Whether `sf data query` accepts `--bulk` together with `--use-tooling-api` is UNVERIFIED (2026-10-20): the CLI guide shows `--use-tooling-api` only on plain queries (sfdx 264 L12664-12666). If the CLI rejects the pair, run the plain Tooling query segmented by `MetadataComponentType`.

### Dependency Graph Is Read-Only

The dependency graph is computed by Salesforce. You cannot insert, update, or delete `MetadataComponentDependency` records. The graph reflects the current state of the org and updates automatically as metadata is added, modified, or removed.

---

## Impact Analysis Before Deletion

Deleting or refactoring a metadata component without understanding its downstream dependencies is one of the most common causes of deployment failures and production incidents.

### Deletion Impact Workflow

1. Query `MetadataComponentDependency` for all components where `RefMetadataComponentId` matches the component you plan to delete.
2. Review each dependent component — is it still active? Is it in a package?
3. For each dependency, determine whether the dependent component will break (hard dependency) or merely lose optional functionality (soft dependency).
4. If hard dependencies exist, refactor or remove them before deleting the target component.
5. Test the deletion in a sandbox with the full dependency chain resolved.

### Hard vs Soft Dependencies

- **Hard dependency:** The dependent component will fail to compile, deploy, or execute if the referenced component is removed. Example: an Apex class that references a custom field in a SOQL query.
- **Soft dependency:** The dependent component references the target but will not break if it is removed. Example: a report column referencing a field — the report may lose the column but will not error.

The `MetadataComponentDependency` object does not distinguish between hard and soft dependencies. That determination requires human review of the dependency type and context.

---

## Packaging Boundary Decisions

One of the highest-value uses of the dependency graph is defining packaging boundaries for unlocked packages. Tightly coupled metadata clusters — groups of components with many internal dependencies and few external ones — are natural candidates for a single package.

### Approach

1. Export the full dependency graph via Bulk API 2.0.
2. Model the graph as a directed graph (nodes = components, edges = dependencies).
3. Identify clusters using community detection or manual grouping by functional domain.
4. For each candidate package boundary, count:
   - **Internal edges** — dependencies between components inside the boundary.
   - **External edges** — dependencies that cross the boundary (incoming or outgoing).
5. A good package boundary has high internal cohesion (many internal edges) and low external coupling (few cross-boundary edges).
6. Cross-boundary dependencies require package dependency declarations. "Circular dependencies among packages aren't supported"; multi-level dependencies are (pkg2 264 L20669-20673).

### Package Dependency Order

When packages depend on each other, they must be installed and deployed in dependency order. The dependency graph from `MetadataComponentDependency` informs this order. A package cannot reference a component in another package unless the referenced package is declared as a dependency and installed first.

---

## Recommended Workflow

1. **Check the Metadata Coverage Report** — for every metadata type in scope, confirm support status in your target deployment channel (Metadata API, unlocked packages, managed packages). Flag unsupported and beta types as risks.
2. **Query the dependency graph** — use `MetadataComponentDependency` via Tooling API to extract dependencies for the components under evaluation. Use Bulk API 2.0 for full-org extraction.
3. **Map upstream and downstream dependencies** — for each component of interest, identify both what it depends on (upstream) and what depends on it (downstream). Document both directions.
4. **Perform impact analysis** — before any deletion or refactoring, enumerate all downstream dependents. Classify each as a hard or soft dependency. Resolve hard dependencies before proceeding.
5. **Evaluate packaging boundaries** — if the goal is modularization, use the dependency graph to identify tightly coupled clusters. Draw candidate package boundaries and validate that cross-boundary dependencies are acyclic and minimal.
6. **Document coverage gaps and workarounds** — for any metadata type that is unsupported in your channel, document the manual configuration steps or alternative deployment strategy in the release runbook.
7. **Re-validate after changes** — after deploying, deleting, or refactoring components, re-query the dependency graph to confirm no orphaned or broken references remain.
