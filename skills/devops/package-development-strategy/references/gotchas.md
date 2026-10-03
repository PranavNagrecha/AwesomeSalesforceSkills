# Gotchas: Package Development Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names the official source it rests on.

## Gotcha 1: A Namespace Can't Be Changed or Reused Once Associated

**What happens:** A team registers a namespace for early experiments, links it, and later wants it for the real product, or wants to rename it after a rebrand. Neither is possible. Every packaged component's API name carries the prefix, so a new namespace means a new package and a subscriber migration.

**When it occurs:** Namespaces chosen during proofs of concept, or before the product name is final.

**How to avoid:** Use a disposable namespace for experiments. Choose the production namespace as a long-lived brand decision. Register it in a dedicated Developer Edition namespace org and link that org to the Dev Hub that will own the packages.

**Source:** Second-Generation Managed Packaging Developer Guide, "Link a Namespace to a Dev Hub Org": "Don't choose a namespace that you want to use in the future for a production org or some other real use case. After you associate a namespace with an org, you can't change it or reuse it."

---

## Gotcha 2: A Package's Namespace and Dev Hub Are Fixed at Creation

**What happens:** A team creates an unlocked package with `--no-namespace` for an internal app. Two years later they want a namespace to avoid API name collisions. The package can't be given one. The same is true for moving a package to another Dev Hub on your own.

**When it occurs:** Any `sf package create` run before the namespace and Dev Hub decisions are final.

**How to avoid:** Decide the namespace and owning Dev Hub before the first `sf package create`. For managed 2GP, a transfer to another Dev Hub is possible only through a Salesforce Customer Support case, with the namespace linked to both Dev Hubs.

**Source:** Second-Generation Managed Packaging Developer Guide: "After you create a package, you can't change or add a namespace, or change the Dev Hub the package is associated with," and "Transfer a Second-Generation Managed Package to a Different Dev Hub". Salesforce DX Developer Guide: "You can't change the package namespace or package type after you create the package."

---

## Gotcha 3: Unlocked Packages Are Not an AppExchange Product Vehicle

**What happens:** An ISV builds a commercial product as unlocked packages because the team knows them from internal work. At listing time the product needs IP protection, which unlocked packages don't give, and the team must rebuild as managed 2GP with namespaced API names.

**When it occurs:** Teams that pick a package type by familiarity rather than distribution intent.

**How to avoid:** If the product will be distributed on AppExchange, start with managed 2GP. Keep unlocked packages for internal business apps.

**Source:** Salesforce DX Developer Guide, "What's an Unlocked Package?" ("Unless you plan to distribute an app on AppExchange, an unlocked package is the right package type for most use cases"; "metadata in unlocked packages can be modified in a production org") and the note that AppExchange partners should use managed 2GP. Second-Generation Managed Packaging Developer Guide: managed package Apex "is obfuscated and can't be viewed in an installing org" except global method signatures.

---

## Gotcha 4: Managed 1GP Is Org-Centric

**What happens:** A 1GP team adopts Salesforce DX expecting scratch-org-built versions. Package versions still come from the packaging org, which owns the package and its metadata. Some operations, such as package create and uninstall, can't be automated, and patches require patch orgs.

**When it occurs:** Existing 1GP products modernizing their ALM.

**How to avoid:** Accept the packaging org for existing 1GP products. Build new products as managed 2GP, where version control is the source of truth and every operation runs through Salesforce CLI.

**Source:** Second-Generation Managed Packaging Developer Guide, "Comparison of First- and Second-Generation Managed Packages".

---

## Gotcha 5: Deletion Rules Invert Between Managed 2GP and Unlocked Packages

**What happens:** A team assumes released versions are permanent for every package type. For managed 2GP that is true. For unlocked packages, released versions can be deleted. "Deletion is permanent," and "Attempts to install a deleted package version will fail," so a pipeline that installs a pinned `04t` breaks.

**When it occurs:** Clean-up of old unlocked versions, or advice that generalizes managed-package rules to all package types.

**How to avoid:** Keep pre-release work on beta versions, which both package types can delete. Before deleting an unlocked version, confirm it "isn't referenced as a dependency" and is not pinned in any pipeline. Grant the Delete Second-Generation Packages permission only to release owners. Delete all versions before deleting the package itself.

**Source:** Salesforce DX Developer Guide, "Delete an Unlocked Package or Package Version" (deletion matrix and considerations).

---

## Gotcha 6: Beta Versions Install Only in Scratch Orgs and Sandboxes, and Can't Be Upgraded

**What happens:** A team installs a beta version in a long-lived UAT sandbox. Later, the promoted version can't upgrade that installed beta, so the sandbox must uninstall first. A request to install a beta in a customer's production org is not possible.

**When it occurs:** Pre-release testing in shared environments.

**How to avoid:** Test beta versions in disposable scratch orgs. Promote a version before any production install. Uninstall a beta before installing a newer beta or released version.

**Source:** Second-Generation Managed Packaging Developer Guide, "Get Ready to Promote and Release": "Beta versions can be installed in only scratch orgs and sandboxes. After you install a beta version into an org, you can't later upgrade that installed beta version." and "Beta packages aren't upgradeable."

---

## Gotcha 7: Versions Built With `--skip-validation` Can't Be Promoted

**What happens:** A pipeline uses `--skip-validation` to speed up version creation, then fails at the promote step on release day.

**When it occurs:** Release pipelines that reuse the fast development build for promotion.

**How to avoid:** Build release candidates with full validation and `--code-coverage`. Unlocked and managed 2GP versions need 75% Apex coverage to be promoted.

**Source:** Salesforce DX Developer Guide, "Skip Validation" ("package versions created using skip validation can't be promoted to the released state") and "Code Coverage for Unlocked Packages". Salesforce CLI `sf package version create --help` (`--skip-validation`: "you can't promote unvalidated package versions").

---

## Gotcha 8: Org-Dependent Unlocked Packages Trade Portability for Convenience

**What happens:** A team uses `--org-dependent` to package metadata that still references unpackaged org metadata. The package then installs only into orgs that contain that metadata, can't depend on other packages, and validates dependencies at install time instead of version creation time.

**When it occurs:** Large legacy orgs starting package-based ALM.

**How to avoid:** Use org-dependent packages as a stepping stone for specific production and sandbox orgs. Plan to untangle dependencies and move to regular unlocked packages.

**Source:** Salesforce DX Developer Guide, "Create Org-Dependent Unlocked Packages" (comparison table).

---

## Gotcha 9: `InstalledPackage` Installs Only Managed 1GP Packages, Alone

**What happens:** A pipeline tries to install an unlocked or managed 2GP dependency by deploying `InstalledPackage` metadata alongside other components. The deploy fails, or the package's Remote Site Settings and CSP Trusted Sites arrive inactive and callouts break.

**When it occurs:** CI pipelines that treat every package dependency the same way, and installs where `activateRSS` is left at its default of false.

**How to avoid:** Use `sf package install --package <04t>` for unlocked and managed 2GP packages. Use `InstalledPackage` only for managed 1GP packages, in a deployment that contains no other metadata type, with `activateRSS` set deliberately.

**Source:** Metadata API Developer Guide, InstalledPackage ("Represents a first-generation managed package to be installed or uninstalled... To install an unlocked or second-generation managed package, use the sf package install Salesforce CLI command"; "When you deploy InstalledPackage, it must be the only metadata type specified in the manifest file"; `activateRSS` field).

