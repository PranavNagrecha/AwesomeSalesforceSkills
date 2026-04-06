# LLM Anti-Patterns — Multi-Package Development

Common mistakes AI coding assistants make when generating or advising on multi-package Salesforce DX projects.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inventing Automatic Dependency Resolution

**What the LLM generates:** "Run `sf package version create --resolve-dependencies` to automatically install and build all dependent packages in the correct order."

**Why it happens:** LLMs hallucinate convenience flags that do not exist. The CLI has no `--resolve-dependencies` or `--build-all` flag. Each package must be versioned individually in topological order.

**Correct pattern:**

```bash
# Build packages explicitly in dependency order
sf package version create --package Base --wait 30
sf package version create --package Sales --wait 30
sf package version create --package UI --wait 30
```

**Detection hint:** Any `sf package` flag containing `resolve`, `auto`, or `build-all` is likely hallucinated.

---

## Anti-Pattern 2: Suggesting Circular Dependencies Are Solvable with Configuration

**What the LLM generates:** "Add `"allowCircular": true` to sfdx-project.json" or "Use late binding to handle circular package dependencies."

**Why it happens:** LLMs generalize from npm/Maven ecosystems where circular dependencies are sometimes manageable. Salesforce DX strictly enforces DAG constraints. There is no configuration to allow circular dependencies.

**Correct pattern:**

```
# Extract shared components into a base package
Package A --> Base <-- Package B
# Never: Package A <--> Package B
```

**Detection hint:** Any mention of "circular dependency" paired with a workaround rather than "refactor into a base package" is wrong.

---

## Anti-Pattern 3: Confusing Package Directory Order with Build/Install Order

**What the LLM generates:** "List your packages in dependency order in sfdx-project.json and the CLI will build them in that sequence."

**Why it happens:** LLMs assume array order is semantically meaningful. The `packageDirectories` array order has no effect on build or install sequencing. The CLI processes one package at a time based on explicit `--package` flags.

**Correct pattern:**

```bash
# Build order is determined by your pipeline, not by array position
# Step 1: Build base (no dependencies)
sf package version create --package MyOrg-Base --wait 30
# Step 2: Build domain (depends on base)
sf package version create --package MyOrg-Sales --wait 30
```

**Detection hint:** Claims that "ordering the packageDirectories array" controls build behavior.

---

## Anti-Pattern 4: Using Package IDs (0Ho) Instead of Subscriber Package Version IDs (04t) in Dependencies

**What the LLM generates:** Setting a dependency's package alias to a 0Ho ID (package container ID) instead of a 04t ID (specific version).

**Why it happens:** LLMs confuse the two ID types. The `packageAliases` map uses 0Ho IDs for the package container and 04t IDs for specific versions. Dependencies must resolve to a specific version (04t).

**Correct pattern:**

```json
{
  "packageAliases": {
    "MyOrg-Base": "0HoXXXXXXXXXXXXX",
    "MyOrg-Base@1.2.0-1": "04tXXXXXXXXXXXXX"
  }
}
```

Dependencies should reference an alias that maps to a 04t ID, or use `"versionNumber"` with `LATEST` to let the CLI resolve it.

**Detection hint:** A dependency alias pointing to an ID starting with `0Ho` instead of `04t`.

---

## Anti-Pattern 5: Recommending `sf project deploy start` for Multi-Package Installs

**What the LLM generates:** "Run `sf project deploy start --source-dir force-app-base,force-app-sales` to deploy all packages at once."

**Why it happens:** LLMs conflate source deployment (metadata API push) with package installation. In a multi-package project, packages must be installed via `sf package install`, not deployed as source. Source deploy does not respect package versioning, dependency declarations, or upgrade paths.

**Correct pattern:**

```bash
# Install packages in order using package install, not source deploy
sf package install --package 04tXXXXXXXXXXXXX --target-org myOrg --wait 20
sf package install --package 04tYYYYYYYYYYYYY --target-org myOrg --wait 20

# Only use sf project deploy start for unpackaged metadata AFTER packages are installed
sf project deploy start --source-dir force-app-unpackaged --target-org myOrg
```

**Detection hint:** `sf project deploy start` used for packaged directories, or `--source-dir` pointing to a package directory path.

---

## Anti-Pattern 6: Omitting Dependency Declarations and Relying on Scratch Org Source Push

**What the LLM generates:** "Just push all source to the scratch org with `sf project deploy start` — no need to declare dependencies since everything is in the same repo."

**Why it happens:** In scratch orgs, `sf project deploy start` deploys all metadata together, masking missing dependency declarations. The code works in the scratch org but fails when packages are installed individually in a sandbox or production org.

**Correct pattern:**

Always declare inter-package dependencies in `sfdx-project.json`, even in a mono-repo. Test package installs in a sandbox to validate dependency declarations.

**Detection hint:** Advice suggesting dependency declarations are optional because "source push handles it."
