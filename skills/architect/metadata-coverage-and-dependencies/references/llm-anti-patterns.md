# LLM Anti-Patterns — Metadata Coverage and Dependencies

Mistakes AI assistants commonly make when advising on Salesforce metadata coverage and dependency analysis.

---

## Anti-Pattern 1: Assuming All Metadata Types Are Deployable via Metadata API

**What the LLM generates:** "You can retrieve and deploy all your org configuration using `sf project retrieve start` and `sf project deploy start`."

**Why it is wrong:** Not all metadata types are supported by the Metadata API. Salesforce publishes an explicit list of unsupported types, and the Metadata Coverage Report shows that many types are only partially supported (e.g., supported for Metadata API but not for packages, or Beta only). Blanket statements about full metadata deployability are factually incorrect and lead to incomplete deployments.

**Correct guidance:** Always qualify deployment advice with "check the Metadata Coverage Report for your specific metadata types and target channel." Name the report explicitly so the user knows where to verify.

---

## Anti-Pattern 2: Suggesting MetadataComponentDependency Can Modify Dependencies

**What the LLM generates:** "Use the MetadataComponentDependency object to add or remove dependencies between components."

**Why it is wrong:** `MetadataComponentDependency` is a read-only Tooling API object. You cannot insert, update, or delete records. It is a computed view of the org's current dependency state. The only way to change dependencies is to modify the metadata components themselves (update the Apex code, change the Flow, edit the page layout, etc.).

**Correct guidance:** `MetadataComponentDependency` is for querying and analyzing dependencies. To change a dependency relationship, modify the source component that creates the reference.

---

## Anti-Pattern 3: Recommending Standard SOQL Instead of Tooling API SOQL

**What the LLM generates:** "Query MetadataComponentDependency using a standard SOQL query: `SELECT ... FROM MetadataComponentDependency`."

**Why it is wrong:** `MetadataComponentDependency` is a Tooling API object, not a standard sObject. Standard SOQL queries (via `/services/data/vXX.0/query/`) will return an error. The query must be executed through the Tooling API endpoint (`/services/data/vXX.0/tooling/query/`) or via CLI with the `--use-tooling-api` flag.

**Correct guidance:** Always specify the Tooling API endpoint when querying `MetadataComponentDependency`. In CLI context: `sf data query --query "..." --use-tooling-api`. In REST context: use `/tooling/query/`.

---

## Anti-Pattern 4: Treating the Dependency Graph as Complete

**What the LLM generates:** "Query MetadataComponentDependency to find all references to this field. If no dependencies are returned, it is safe to delete."

**Why it is wrong:** `MetadataComponentDependency` captures static, compile-time metadata references. It does not capture dynamic references: field names in Custom Metadata/Custom Settings used at runtime, dynamic SOQL that constructs field names from strings, Flow text template interpolations, or runtime-evaluated Visualforce expressions. Declaring a component safe to delete based solely on this query can cause runtime failures that were invisible in the dependency graph.

**Correct guidance:** Use the dependency graph as the starting point for impact analysis, not the final answer. Supplement with text search across Apex source, Flow metadata XML, and configuration records. For high-risk deletions, search Custom Metadata and Custom Settings values for the component's API name.

---

## Anti-Pattern 5: Ignoring API Version When Citing Coverage

**What the LLM generates:** "CustomIndex is supported in unlocked packages" or "ExternalServiceRegistration is not supported in Metadata API" — without specifying the API version.

**Why it is wrong:** Metadata coverage changes with every Salesforce release. A type unsupported in v59.0 may be supported in v60.0. Coverage claims without an API version are unreliable and may be outdated by the time the user acts on them.

**Correct guidance:** Always qualify coverage claims with the API version: "As of API version 60.0 (Spring '25), ExternalServiceRegistration is supported in Metadata API." Direct the user to verify at the current version of the Metadata Coverage Report.

---

## Anti-Pattern 6: Proposing Circular Package Dependencies

**What the LLM generates:** "Create Package A with your Lending components and Package B with your Compliance components. Package A can depend on Package B and Package B can depend on Package A."

**Why it is wrong:** Salesforce enforces a strict directed acyclic graph (DAG) for package dependencies. Circular dependencies are rejected at package version creation time. This is a hard platform constraint, not a best-practice suggestion.

**Correct guidance:** If two component groups have mutual dependencies, they either belong in the same package or the shared components must be extracted into a base package that both depend on. Always validate that the dependency graph between packages is acyclic before committing to a packaging structure.

---

## Anti-Pattern 7: Omitting Bulk API 2.0 for Large Org Dependency Extraction

**What the LLM generates:** "Run this Tooling API SOQL query to get all dependencies in your org" — providing a simple query without mentioning scale considerations.

**Why it is wrong:** Standard Tooling API queries are subject to query timeout and row limits that make them unsuitable for production orgs with thousands of components. The full dependency graph for a large org can exceed 100,000 rows. Without using Bulk API 2.0, the query will either time out or return incomplete results.

**Correct guidance:** For full-org dependency extraction, recommend Bulk API 2.0 via `sf data query --bulk --use-tooling-api`. Note the 100,000-row-per-job limit and recommend segmenting by `MetadataComponentType` if the org exceeds that threshold.
