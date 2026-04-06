# Gotchas — Metadata Coverage and Dependencies

Non-obvious Salesforce platform behaviors that cause real problems in metadata coverage and dependency analysis.

---

## Gotcha 1: MetadataComponentDependency Is Still Beta

**What happens:** Teams build automated dependency analysis pipelines around `MetadataComponentDependency` and treat it as a stable, GA API object.

**The reality:** As of Spring '25, `MetadataComponentDependency` remains in Beta status. Salesforce states that Beta features are not guaranteed to be complete and may change without notice. The object is functional and widely used, but it carries no forward-compatibility commitment. Fields, query behavior, or availability could change between releases.

**How to handle it:** Use `MetadataComponentDependency` for dependency analysis — it is the best tool available — but do not build hard production gates that assume its schema or behavior will remain unchanged. Version-pin your queries and re-validate after major Salesforce releases.

---

## Gotcha 2: The Coverage Report Changes Every Release

**What happens:** An architect checks the Metadata Coverage Report once during project planning and treats the results as permanent.

**The reality:** Salesforce updates metadata coverage with every major release. A type that was "Not Supported" for unlocked packages in Winter '25 may become "Supported" in Spring '25, and a "Beta" type may be promoted to "Supported" or removed. The report is versioned by API version — always select the version that matches your target deployment.

**How to handle it:** Re-check the Metadata Coverage Report at the start of every release cycle. When planning multi-release projects, document the API version at which coverage was assessed and schedule a re-check at each subsequent release boundary.

---

## Gotcha 3: Dependency Query Does Not Capture Dynamic References

**What happens:** An impact analysis queries `MetadataComponentDependency` before deleting a custom field. No dependencies are found. After deletion, a Flow fails because it used a dynamic field reference via a text template variable.

**The reality:** `MetadataComponentDependency` captures static, compile-time references in the metadata graph. It does not capture dynamic references such as: field names stored in Custom Metadata or Custom Settings and referenced at runtime, dynamic SOQL/SOSL that constructs field references from strings, Flow text templates that interpolate field names, or Visualforce `{!relatedList}` expressions that are evaluated at runtime.

**How to handle it:** Treat the dependency graph as the minimum set of dependencies. Supplement with text search across Apex source, Flow XML, and configuration records for the component name. For critical deletions, search Custom Metadata/Custom Settings values for the field or component API name.

---

## Gotcha 4: Bulk API 2.0 Query Has a 100,000 Row Limit

**What happens:** A large enterprise org with 5,000+ metadata components attempts a full dependency graph export via Bulk API 2.0. The query returns exactly 100,000 rows and the team assumes that is the complete graph.

**The reality:** Bulk API 2.0 queries against `MetadataComponentDependency` are limited to 100,000 records per job. If the org's dependency graph exceeds this, the result is silently truncated. There is no next-page mechanism for Bulk API 2.0 query jobs.

**How to handle it:** After a Bulk API 2.0 export, check the row count. If it is exactly 100,000, the result is likely truncated. Break the query into segments by `MetadataComponentType` or `RefMetadataComponentType` to stay under the limit per job. Reassemble the segments into a complete graph.

---

## Gotcha 5: Unsupported Types Are Silently Excluded from Packages

**What happens:** A developer adds all project metadata to a package directory. During `sf package version create`, certain types are silently dropped from the package version. The developer does not notice until a subscriber installs the package and the configuration is missing.

**The reality:** When a metadata type is listed as "Not Supported" for the packaging channel (unlocked or managed), the CLI does not throw an error during package version creation. The type is simply excluded from the package artifact. There is no warning in the command output unless you specifically look for it.

**How to handle it:** Before creating a package version, cross-reference every metadata type in the package directory against the Metadata Coverage Report for the target packaging channel. Automate this check as a CI validation step. Any type not supported must be moved to a separate unpackaged deployment step or documented as a post-install configuration task.

---

## Gotcha 6: Package Dependencies Must Be Acyclic

**What happens:** During a packaging boundary redesign, an architect draws two packages where Package A depends on Package B and Package B depends on Package A.

**The reality:** Salesforce unlocked and managed packages enforce a strict directed acyclic graph (DAG) for dependencies. Circular dependencies are not allowed and will fail at package version creation time. This constraint applies transitively: if A depends on B, B depends on C, and C depends on A, the cycle is detected and rejected.

**How to handle it:** When designing package boundaries from the dependency graph, check for cycles in the cross-boundary dependency edges before committing to the design. If a cycle exists, the boundary must be redrawn — typically by extracting the shared components into a base package that both packages depend on.

---

## Gotcha 7: Standard Object Fields Appear as Dependencies but Cannot Be Packaged

**What happens:** The dependency graph shows that a custom Apex class depends on standard fields like `Account.Name` or `Contact.Email`. An architect includes these in the dependency count when evaluating cross-boundary coupling.

**The reality:** Standard object fields are not metadata that you own or package. They are always available in every org. Including them in dependency analysis inflates the coupling metrics and can lead to incorrect packaging boundary decisions.

**How to handle it:** Filter out standard object and standard field dependencies when calculating coupling metrics for packaging boundaries. Only count dependencies on custom metadata components that are owned by the project.
