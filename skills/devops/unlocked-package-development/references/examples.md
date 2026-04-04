# Examples — Unlocked Package Development

## Example 1: Multi-Package Project with Inter-Package Dependencies

**Context:** A team is building an internal Salesforce platform with two unlocked packages: `SharedComponents` (reusable LWC and Apex utilities) and `SalesApp` (sales-specific features that depend on `SharedComponents`). They need to set up `sfdx-project.json` so both packages can be versioned independently but maintain the correct dependency order.

**Problem:** Without explicit dependency declaration, version create for `SalesApp` succeeds locally but fails in CI with `PACKAGE2_VERSION_CREATE_DEPENDENCY_UNRESOLVED` because the CI scratch org does not have `SharedComponents` installed.

**Solution:**

```json
// sfdx-project.json
{
  "packageDirectories": [
    {
      "path": "shared-components",
      "default": false,
      "package": "SharedComponents",
      "versionName": "Core Utils 1.2",
      "versionNumber": "1.2.0.NEXT",
      "dependencies": []
    },
    {
      "path": "sales-app",
      "default": true,
      "package": "SalesApp",
      "versionName": "Sales Spring 2025",
      "versionNumber": "3.0.0.NEXT",
      "dependencies": [
        {
          "package": "SharedComponents",
          "versionNumber": "1.2.0.LATEST"
        }
      ]
    }
  ],
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "63.0",
  "packageAliases": {
    "SharedComponents": "0Ho000000000001AAA",
    "SharedComponents@1.2.0-1": "04t000000000001AAA",
    "SalesApp": "0Ho000000000002AAA",
    "SalesApp@3.0.0-1": "04t000000000002AAA"
  }
}
```

```bash
# CI pipeline order — SharedComponents must be created and installed first

# 1. Create SharedComponents version
sf package version create \
  --package SharedComponents \
  --installation-key-bypass \
  --wait 15 \
  --target-dev-hub MyDevHub

# 2. Install SharedComponents in the scratch org used for SalesApp version creation
sf package install \
  --package 04t000000000001AAA \
  --target-org pkg-scratch \
  --wait 10

# 3. Create SalesApp version (dependencies now satisfied in scratch org)
sf package version create \
  --package SalesApp \
  --installation-key-bypass \
  --wait 15 \
  --target-dev-hub MyDevHub
```

**Why it works:** Declaring the dependency in `packageDirectories.dependencies` tells Salesforce to validate that `SharedComponents` is present when creating the `SalesApp` version. Using `LATEST` in the version number allows the CI pipeline to pick up the most recently released version of `SharedComponents` without hardcoding a version ID — reducing maintenance overhead as the dependency package evolves.

---

## Example 2: Promoting a Package Version Through Dev/QA/Production Pipeline

**Context:** An enterprise team uses a three-stage pipeline: scratch org (development) → QA sandbox → production. They build an unlocked package version and need to promote it through stages with the correct gates.

**Problem:** The team installs a beta package version in QA and approves it, then attempts to install the same `04t...` ID in production. The platform rejects it with `PACKAGE_UNAVAILABLE` because beta versions cannot be installed in production orgs.

**Solution:**

```bash
# Stage 1: Development — create beta version in scratch org
sf package version create \
  --package InternalCRM \
  --installation-key-bypass \
  --code-coverage \
  --wait 20 \
  --target-dev-hub MyDevHub

# Capture the new version ID from the output, e.g. 04tXXXXXXXXXXXXX
PACKAGE_VERSION_ID="04tXXXXXXXXXXXXX"

# Stage 2: QA — install beta in sandbox (beta is allowed in sandboxes)
sf package install \
  --package $PACKAGE_VERSION_ID \
  --target-org QASandbox \
  --wait 10

# Run automated tests in QA sandbox to validate
sf apex run test \
  --target-org QASandbox \
  --result-format tap \
  --code-coverage \
  --wait 10

# Gate: check code coverage from version report before promoting
sf package version report \
  --package $PACKAGE_VERSION_ID \
  --target-dev-hub MyDevHub

# Stage 3 gate: promote to Released (irreversible — only do after QA sign-off)
sf package version promote \
  --package $PACKAGE_VERSION_ID \
  --no-prompt \
  --target-dev-hub MyDevHub

# Stage 3: Production install (now works because version is Released)
sf package install \
  --package $PACKAGE_VERSION_ID \
  --target-org Production \
  --wait 10
```

**Why it works:** The `--code-coverage` flag on `package version create` causes Salesforce to run Apex tests during version creation and record per-class coverage in the version record. This enables the `package version report` check to surface coverage before promotion, rather than discovering low coverage at the promotion step and blocking the release. Promotion is a one-way operation and must be a deliberate pipeline gate after QA approval — not an automatic step.

---

## Example 3: Using an Installation Key to Restrict Package Distribution

**Context:** A platform team publishes an internal shared-services unlocked package to multiple business unit orgs. They want to prevent unauthorized orgs from installing it without an approved key.

**Problem:** Without an installation key, any org with network access to the Dev Hub could theoretically install the package by guessing the `04t...` ID. The team wants a lightweight access control mechanism without building a full licensing system.

**Solution:**

```bash
# Create the package version with an installation key
sf package version create \
  --package SharedServices \
  --installation-key "MyS3cr3tK3y#2025" \
  --wait 15 \
  --target-dev-hub MyDevHub

# Distribute the key to authorized subscribers via secrets management (not in sfdx-project.json)

# Subscriber installs with the key
sf package install \
  --package 04tXXXXXXXXXXXXX \
  --installation-key "MyS3cr3tK3y#2025" \
  --target-org AuthorizedSandbox \
  --wait 10
```

**Why it works:** The installation key is a password set at version create time and required at install time. Salesforce validates the key server-side during installation. Orgs that attempt to install without the key receive a `PACKAGE_INSTALL_FAILED` error. The key must be stored in a secrets manager (e.g., GitHub Actions secrets, HashiCorp Vault) and never committed to `sfdx-project.json` or source control. Note: the key is fixed per version and cannot be rotated after version creation — rotate by creating a new version with a new key.

---

## Anti-Pattern: Putting All Metadata in One Giant Package Directory

**What practitioners do:** Place every custom object, Apex class, LWC, flow, and permission set for the entire org into a single `force-app` directory under one unlocked package.

**What goes wrong:**
- Package version create times grow to 30–60+ minutes as the package grows
- A change to any component forces a full version creation cycle, even if only one LWC changed
- Dependencies between logical domains cannot be modeled — everything is in one package
- Apex coverage failures in any part of the codebase block all deployments, not just the affected domain
- Rollback is all-or-nothing — you cannot roll back a single feature without rolling back the entire package

**Correct approach:** Decompose into multiple unlocked packages organized by domain or layer. A common pattern:
- `platform-core` — shared utilities, base Apex services, custom settings
- `sales-domain` — sales-specific objects, logic, and UI; depends on `platform-core`
- `service-domain` — service-specific components; depends on `platform-core`

Each package can be versioned, deployed, and rolled back independently. Teams owning different domains can release on different cadences without coordination overhead.
