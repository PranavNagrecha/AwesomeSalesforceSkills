# LLM Anti-Patterns — Second Generation Managed Packages

Common mistakes AI coding assistants make when generating or advising on Salesforce 2GP managed package development.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing 1GP and 2GP Package Development Workflows

**What the LLM generates:** Instructions to use a packaging org, upload via Setup UI, or reference patch orgs — all of which are 1GP concepts that do not apply to 2GP development.

**Why it happens:** 1GP managed packages dominated ISV development for over a decade. Training data is heavily weighted toward 1GP workflows. LLMs conflate packaging org concepts with Dev Hub-based 2GP development.

**Correct pattern:**

```text
1GP vs 2GP workflow differences:

1GP (First Generation):
- Developed in a packaging org (Developer Edition)
- Uploaded via Setup > Package Manager > Upload
- Patch versions created in separate patch orgs
- Namespace tied to the packaging org

2GP (Second Generation):
- Developed in scratch orgs, source tracked in Git
- Built via: sf package version create --package MyPkg
- No packaging org — uses Dev Hub for version creation
- Namespace linked to Dev Hub, shared across packages
- Patch versions created with --version-create (no separate org)
- Promoted via: sf package version promote --package 04tXXX

Do NOT reference "packaging org" or "Upload" in 2GP contexts.
```

**Detection hint:** Flag 2GP instructions that mention "packaging org," "Upload button," "patch org," or Setup UI-based packaging. These are 1GP-only concepts.

---

## Anti-Pattern 2: Not Meeting Code Coverage Requirements for Version Promotion

**What the LLM generates:** "Create a package version and promote it to released" without noting that promotion to released status requires 75% Apex code coverage, and that coverage is computed during `sf package version create`, not during promotion.

**Why it happens:** The coverage requirement is well-known for production deployments but is applied differently in 2GP — it is checked during version creation with `--code-coverage` flag, not during the promote step. LLMs miss this sequencing.

**Correct pattern:**

```text
2GP version promotion requirements:

1. Create version WITH code coverage:
   sf package version create --package MyPkg --code-coverage --wait 30
   (--code-coverage flag is REQUIRED for versions you intend to promote)

2. Verify coverage meets 75%:
   sf package version report --package 04tXXXXXXXXXXXXXXX

3. Promote to released:
   sf package version promote --package 04tXXXXXXXXXXXXXXX

If version was created WITHOUT --code-coverage:
- Cannot promote — must recreate with the flag
- Beta versions (not promoted) do not require coverage

Common error:
"Cannot promote a package version that hasn't been tested with code coverage"
```

**Detection hint:** Flag `sf package version create` commands without `--code-coverage` when the version is intended for production/release. Check for missing coverage verification before promote.

---

## Anti-Pattern 3: Ignoring Ancestor Version for Upgrade Path Continuity

**What the LLM generates:** `sf package version create --package MyPkg` without specifying `--version-number` or addressing ancestor version, which can break the upgrade path for existing subscribers.

**Why it happens:** Ancestor version management is a 2GP-specific concept with limited training data. LLMs skip it because basic examples do not require it. However, without proper ancestor specification, subscribers cannot upgrade from older versions.

**Correct pattern:**

```text
Ancestor version in 2GP:

Purpose: ensures that a new version is compatible with a previous version,
enabling subscriber upgrades.

In sfdx-project.json:
{
  "packageDirectories": [{
    "path": "force-app",
    "package": "MyPackage",
    "versionNumber": "2.1.0.NEXT",
    "ancestorVersion": "2.0.0.1"  // or "ancestorId": "04tXXX..."
  }]
}

Rules:
- ancestorVersion must be a RELEASED (promoted) version
- First version: no ancestor needed
- Subsequent versions: set ancestor to the latest released version
- If omitted: Salesforce uses "HIGHEST" ancestor by default (Spring '24+)
- Breaking changes (removing public methods/fields) fail validation
  against the ancestor
```

**Detection hint:** Flag sfdx-project.json configurations for managed packages that omit `ancestorVersion` or `ancestorId` after the initial version. Check for version creation commands without ancestor context.

---

## Anti-Pattern 4: Sharing Namespace Credentials Insecurely

**What the LLM generates:** "Register a namespace in your Developer Edition org and link it to the Dev Hub" without securing the namespace org — which, if compromised, could allow unauthorized package versions to be published under your namespace.

**Why it happens:** Namespace registration is treated as a one-time setup step. LLMs do not cover the security implications of the namespace org or the Dev Hub's role as the package authority.

**Correct pattern:**

```text
Namespace security for 2GP:

1. Namespace org (Developer Edition):
   - Registers and owns the namespace
   - Must be linked to the Dev Hub
   - Protect with MFA, strong password, and limited admin access
   - Do NOT use this org for development — it is a namespace holder only

2. Dev Hub org:
   - Creates and manages all package versions
   - Must have "Second-Generation Packaging" feature enabled
   - Limit "Create and Update Second-Generation Packages" permission
     to a small set of trusted developers/CI users

3. CI/CD credentials:
   - Use a dedicated Connected App for CI package creation
   - Scope the Connected App to the minimum required permissions
   - Rotate JWT certificates on a regular schedule
```

**Detection hint:** Flag namespace setup instructions that do not mention securing the namespace org. Check for Dev Hub permission guidance.

---

## Anti-Pattern 5: Not Handling @namespaceAccessible Correctly for Cross-Package Access

**What the LLM generates:** Apex code in a managed package that expects to call methods or access types in another managed package without the `@namespaceAccessible` annotation, which is required for cross-namespace access in 2GP.

**Why it happens:** In 1GP, all code in the same namespace was accessible. 2GP introduced `@namespaceAccessible` to control cross-package access within the same namespace. LLMs apply 1GP access patterns to 2GP code.

**Correct pattern:**

```apex
// Package A: expose a class for use by Package B (same namespace)
@namespaceAccessible
public class SharedService {

    @namespaceAccessible
    public static String processRecord(Id recordId) {
        // Implementation
        return 'processed';
    }
}

// Rules for @namespaceAccessible:
// - Both packages must share the same namespace
// - The annotation must be on the class AND on each method/property to expose
// - Without the annotation, classes are package-private (not accessible
//   from other packages even in the same namespace)
// - This is a 2GP concept — 1GP does not require this annotation
```

**Detection hint:** Flag Apex classes in 2GP packages that are intended for cross-package use but lack `@namespaceAccessible`. Check for multi-package architectures without this annotation on shared interfaces.
