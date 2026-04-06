---
name: metadata-coverage-and-dependencies
description: "Assessing metadata type coverage across Salesforce deployment channels (Metadata API, SFDX, unlocked packages, managed packages) and mapping component dependency graphs using Tooling API MetadataComponentDependency. Use when planning packaging strategies, evaluating deployment risk, performing impact analysis before component deletion, or mapping tightly coupled metadata for modular architecture. Trigger keywords: metadata coverage report, dependency graph, MetadataComponentDependency, impact analysis, unsupported metadata types, packaging eligibility. NOT for deployment mechanics (use destructive-changes-deployment). NOT for CI/CD pipeline design (use continuous-integration-testing)."
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
  - which metadata types are supported by Metadata API
  - how to check if a metadata type can go in an unlocked package
  - how to find all components that depend on a custom field
  - impact analysis before deleting an Apex class
  - dependency graph for packaging boundary decisions
  - MetadataComponentDependency query examples
  - unsupported metadata types workaround
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Metadata Coverage and Dependencies

## Overview

Every Salesforce org accumulates metadata over time. Before you can safely deploy, package, refactor, or delete any component, you need to answer two questions: (1) is this metadata type supported in the channel I plan to use, and (2) what other components depend on it?

The Metadata Coverage Report answers the first question. The Tooling API MetadataComponentDependency object answers the second. Together they form the foundation for packaging strategy, impact analysis, and modular architecture decisions.

---

## Metadata Coverage Report

The Metadata Coverage Report is the canonical source of truth for which metadata types are supported across Salesforce deployment channels. It is published by Salesforce at `https://developer.salesforce.com/docs/metadata-coverage` and is versioned by API release.

The report covers support status across these channels:
- **Metadata API** — retrieve and deploy via `sf project retrieve/deploy` or the SOAP/REST deploy endpoints.
- **Source Tracking** — whether changes to the type are tracked in scratch orgs and sandboxes for incremental pull/push.
- **Unlocked Packages** — whether the type can be included in an unlocked package.
- **2GP Managed Packages** — second-generation managed package support.
- **1GP Managed Packages** — classic (first-generation) managed package support.

Each metadata type has one of three statuses per channel: **Supported**, **Not Supported**, or **Beta**. Beta types may work but carry no forward-compatibility guarantee.

### How to Use the Coverage Report

1. Identify the deployment channel(s) your project uses (e.g., unlocked packages for modular delivery, Metadata API for sandbox-to-production promotion).
2. For each metadata type in scope, check the coverage report at your target API version.
3. Flag any type that is **Not Supported** or **Beta** in your channel as a packaging risk.
4. For unsupported types, determine a workaround: manual configuration steps, post-deployment scripts, or separate unpackaged metadata promotion.

### Common Unsupported or Partially Supported Types

Not all metadata is created equal. Some frequently encountered types with coverage gaps include:

- **Knowledge Settings** — often unsupported in packages; requires post-deploy configuration.
- **Territory Management** — Enterprise Territory Management metadata has partial Metadata API support; packaging support varies by type and version.
- **Certain Standard Value Sets** — some picklist standard value sets are not retrievable or deployable.
- **Einstein/AI Configuration** — prediction builders, recommendation strategies, and some AI features have limited or no Metadata API coverage.
- **Shield Platform Encryption** — encryption policies and tenant secrets are not deployable via Metadata API.

Always verify against the current API version. Coverage improves with each release.

---

## Unsupported Metadata Types

Salesforce publishes an explicit list of unsupported metadata types in the Metadata API Developer Guide. These types cannot be retrieved, deployed, or packaged through the Metadata API at all. They must be configured manually or through the Tooling API (for types that support it).

When an unsupported type is part of your solution architecture, document it as a manual deployment step in your release runbook. Do not assume future support — plan for the current state.

---

## MetadataComponentDependency (Tooling API)

The `MetadataComponentDependency` object in the Tooling API provides a read-only, queryable dependency graph for metadata components in an org. Each record represents a directional dependency: component A depends on component B.

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

For production orgs with thousands of metadata components, the standard Tooling API query may hit governor limits. Salesforce supports querying `MetadataComponentDependency` through Bulk API 2.0, which can return up to 100,000 records per query job. This is the recommended approach for full-org dependency extraction.

```bash
sf data query --query "SELECT MetadataComponentName, MetadataComponentType, RefMetadataComponentName, RefMetadataComponentType FROM MetadataComponentDependency" --use-tooling-api --bulk --target-org myOrg
```

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
6. Cross-boundary dependencies require package dependency declarations. Circular cross-boundary dependencies are not allowed and indicate the boundary is wrong.

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
