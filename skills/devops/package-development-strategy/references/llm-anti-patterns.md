# LLM Anti-Patterns: Package Development Strategy

Common mistakes AI coding assistants make when advising on Salesforce package type selection and development strategy.

---

## Anti-Pattern 1: Recommending Unlocked Packages for AppExchange ISV Products

**What the LLM generates:** "Use unlocked packages for your new AppExchange app, they're the modern recommended approach."

**Why it happens:** LLMs associate "unlocked packages" with "modern DX development" without distinguishing between internal org use and ISV AppExchange listing requirements.

**The correct pattern:** Unlocked packages do not provide IP protection, Apex source is accessible to the subscriber org admin. AppExchange Security Review requires managed packages (1GP or 2GP) for ISV product listings. Use 2GP managed packages for new ISV products; use unlocked packages only for internal customer org modularization.

**Detection hint:** Any recommendation of unlocked packages for a product intended for AppExchange listing is incorrect. If the context is "internal org" and no AppExchange listing is intended, unlocked packages are appropriate.

---

## Anti-Pattern 2: Treating 1GP and 2GP as Equivalent Choices

**What the LLM generates:** "You can use either 1GP or 2GP managed packages for your new product, choose based on your team's experience."

**Why it happens:** LLMs present both as valid options without applying Salesforce's own recommendation to use 2GP for all new development.

**The correct pattern:** Salesforce explicitly recommends 2GP for all new managed package development. 1GP is org-centric, not DX-compatible, and has limited dependency management. 2GP supports scratch org development, source format, CI/CD, and explicit package dependencies. The choice of 1GP for new development is a deliberate tradeoff that should be justified, not a default.

**Detection hint:** Any recommendation of 1GP for a new ISV product without explicitly acknowledging that 2GP is the Salesforce-recommended choice should be questioned.

---

## Anti-Pattern 3: Suggesting Namespace Can Be Changed Post-Registration

**What the LLM generates:** "You can rename your namespace later by submitting a support case to Salesforce."

**Why it happens:** LLMs generate plausible-sounding workarounds for irreversible platform decisions.

**The correct pattern:** "After you associate a namespace with an org, you can't change it or reuse it," and a package's namespace can't be changed or added after the package is created. All packaged API names carry the prefix. A different namespace means a new package and a subscriber migration. Do not confuse this with a package transfer: Salesforce Customer Support can transfer a managed 2GP package (with its namespace) to another Dev Hub, which moves ownership but does not rename anything.

**Detection hint:** Any response that suggests renaming a namespace, or adding one to an existing package, through a support case or any other mechanism.

---

## Anti-Pattern 4: Recommending 2GP for Internal Org Modularization Without License Considerations

**What the LLM generates:** "Use 2GP managed packages to modularize your internal org, it's the most modern approach."

**Why it happens:** LLMs recommend 2GP broadly without distinguishing the licensing and namespace requirements of managed packages vs. unlocked packages.

**The correct pattern:** 2GP managed packages require namespace registration (a permanent decision) and are intended for ISV/AppExchange use. For internal org modularization without AppExchange ambitions, unlocked packages are the correct choice, no namespace required, no IP protection overhead, simpler dependency model for internal use.

**Detection hint:** If the use case is explicitly internal customer org development (not ISV), recommending 2GP managed packages over unlocked packages adds unnecessary complexity.

---

## Anti-Pattern 5: Confusing Package Type with Deployment Method

**What the LLM generates:** "Unmanaged packages are the same as metadata API deployments, just use whichever you prefer."

**Why it happens:** LLMs conflate unmanaged packages (which use the same metadata format as deployments) with the Metadata API deployment mechanism.

**The correct pattern:** Unmanaged packages are a specific Salesforce artifact type that can be installed via a URL. Metadata API deployments are a deployment mechanism. Unlocked packages and managed packages are versioned, immutable artifacts with distinct lifecycle management. These are not interchangeable, each has distinct installation, versioning, and dependency management behaviors.

**Detection hint:** Any response that equates "unmanaged package" with "metadata deployment" without noting the installation and lifecycle differences is imprecise.

---

## Anti-Pattern 6: Equating "Beta" With `--skip-validation` and Installing Betas in Production

**What the LLM generates:** "Create a beta version with `--skip-validation` and install it in the subscriber's production org to test before releasing."

**Why it happens:** LLMs apply general "beta testing" ideas and merge two different package concepts.

**The correct pattern:** Every package version is beta until it is promoted. `--skip-validation` is a separate option that skips dependency, ancestor, and metadata validation; versions built with it can't be promoted at all. Beta versions install only in scratch orgs and sandboxes, and an installed beta can't be upgraded later. For a customer to test pre-release code, use a sandbox of their org, then promote a fully validated version that meets 75% coverage.

**Detection hint:** Any workflow that installs a beta in a production org, or that calls `--skip-validation` builds "beta" as if that were the definition.

---

## Anti-Pattern 7: Applying the Managed-Package Immutability Rule to Unlocked Packages

**What the LLM generates:** "Package versions are immutable, a released version can never be deleted, so old unlocked versions are safe to leave in place." Or the inverse: "Delete the old unlocked betas and releases to clean up your package list."

**Why it happens:** LLMs learn one blanket "package versions are immutable" rule from managed-package documentation and generalize it to every package type, so they never warn about deletion risk. When they do know deletion is possible, they present it as harmless housekeeping.

**The correct pattern:** Immutability and deletability are different properties, a released version's *contents* never change, which says nothing about whether the version can be removed. The deletion rule is per-package-type: released 2GP managed versions cannot be deleted; released unlocked versions can. For unlocked, "Deletion is permanent" and "Attempts to install a deleted package version will fail", so deleting a version is a breaking change for every pipeline or org that installs by `04t` ID, not a tidy-up. It requires the **Delete Second-Generation Packages** user permission, deletion of all package versions before the package itself, and confirmation that nothing references the package or version as a dependency.

**Detection hint:** Any claim that released Salesforce package versions "can never be deleted" without naming the package type is wrong for unlocked packages. Any suggestion to delete an unlocked package version without a dependency check and a downstream-install warning is unsafe advice.

---

## Anti-Pattern 8: Registering the Namespace "in the Dev Hub"

**What the LLM generates:** "Register your namespace in your Dev Hub org, then create the package."

**Why it happens:** The Dev Hub owns 2GP packages, so LLMs assume it also hosts the namespace registration.

**The correct pattern:** Create and register the namespace in a separate Developer Edition org (the namespace org). Then, in the Dev Hub, open Namespace Registries and link that org. Set the namespace in `sfdx-project.json` before `sf package create`, because the namespace is bound to the package at creation. A Dev Hub can have several linked namespaces.

**Detection hint:** Instructions that register a namespace directly in the Dev Hub, or that create the package before the namespace is in `sfdx-project.json`.
