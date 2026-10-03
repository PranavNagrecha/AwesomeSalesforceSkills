# Examples: Package Development Strategy

## Example 1: ISV Choosing Managed 2GP for a New AppExchange App

**Scenario:** An ISV is building a new Field Service add-on for AppExchange. The team shipped a previous product as managed 1GP and is deciding whether to use 2GP for the new one.

**Problem:** In managed 1GP the packaging org is the source of truth and owns the package. Each namespace holds only one package, versioning is linear, and patches need patch orgs. Some operations can't be automated.

**Solution:** Build the new product as managed 2GP.

```bash
# 1. In a separate Developer Edition org: create and register the namespace "fsaddon".
# 2. In the Dev Hub: App Launcher > Namespace Registries > Link Namespace (log in to the namespace org).
# 3. Put "namespace": "fsaddon" in sfdx-project.json, then create the package (namespace binds here).
sf package create --name "FS Add-on" --path force-app --package-type Managed --target-dev-hub devhub

# 4. Develop in scratch orgs (sf org create scratch replaces the retired sfdx force:org:create).
sf org create scratch --definition-file config/project-scratch-def.json --alias fs-dev --target-dev-hub devhub

# 5. Build a release candidate with full validation and coverage, then promote it.
sf package version create --package "FS Add-on" --code-coverage --installation-key-bypass --wait 30 --target-dev-hub devhub
sf package version promote --package "FS Add-on@1.0.0-1" --target-dev-hub devhub
```

**Why it works:** Managed 2GP keeps version control as the source of truth, runs every operation through Salesforce CLI, allows several packages per namespace, and supports AppExchange listing. The namespace is bound to the package when `sf package create` runs and can't be changed afterward, so it is chosen first.

---

## Example 2: Internal Team Using Unlocked Packages for Modular Org Development

**Scenario:** A large enterprise has one org shared by Sales, Service, and Finance teams. Each team has its own release lifecycle. The DevOps team wants each business unit to deploy independently.

**Problem:** A single org-wide metadata deployment couples all teams. A Service change can overwrite a Sales profile permission if both are in the same deployment.

**Solution:**

```text
Shared-Core       (no dependencies)
  ^        ^        ^
  |        |        |
Sales-Core  Service-Core  Finance-Core   (each depends on Shared-Core@x.y.0.RELEASED)
```

Create four unlocked packages: `Shared-Core`, `Sales-Core`, `Service-Core`, and `Finance-Core`. Each owns its domain's metadata. The three domain packages declare a dependency on a released `Shared-Core` version. Each team runs its own pipeline. The full `sfdx-project.json` is in [metadata-examples.md](metadata-examples.md).

**Why it works:** Each package version is an immutable artifact, so installing `Service-Core` 2.5 does not touch Sales metadata. Unlocked packages can be created without a namespace and are aimed at internal business apps. Because unlocked metadata can be edited in production, the team agrees that admins report any direct production edit to the package owners.

---

## Example 3: Namespace Selection Mistake

**Scenario:** A team registers the namespace `myns` for a managed 2GP package during development. After launch, the company is acquired and rebranded, and the team wants the namespace to match the new brand.

**Problem:** "After you associate a namespace with an org, you can't change it or reuse it." The namespace is bound to the package at creation and appears in every packaged API name.

**Solution:** There is no rename. A package with a new namespace is a separate product, and subscribers must move to it. What is possible is a transfer of the existing package (with `myns`) to the acquirer's Dev Hub through a Salesforce Customer Support case, with the namespace linked to both Dev Hubs first. That changes ownership, not the prefix.

**Why it matters:** Namespace selection deserves the same diligence as a domain name. Giving each sellable product its own namespace keeps the transfer path open.
