# Gotchas — Package Development Strategy

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Namespace Selection Is Permanent and Irreversible

**What happens:** A team registers a namespace for their managed package during development without fully considering long-term implications (brand change, acquisition, naming conflicts). After the package is published to AppExchange and has subscribers, the team discovers they cannot change the namespace.

**Impact:** Every API name of every component in every package version includes the namespace prefix permanently. All subscriber orgs that have installed the package reference those namespaced component names. A namespace change would require a new package and a full subscriber migration.

**How to avoid:** Treat namespace selection as a permanent architectural decision. Choose a short, brand-stable, conflict-free string. Reserve the namespace in the Dev Hub before any external communications about the product name. Verify namespace availability on AppExchange Partner Community before registering.

---

## Gotcha 2: Unlocked Packages Cannot Be Listed on AppExchange as ISV Products

**What happens:** An ISV team chooses unlocked packages for a new product because they have prior experience with them for internal customer org development. At submission time, the AppExchange Security Review rejects the package because unlocked packages do not provide IP protection.

**Impact:** The team must rebuild the product as a 2GP managed package to pass AppExchange Security Review. All component API names must be updated with the new namespace prefix, and all subscriber installation and migration paths must be re-planned.

**How to avoid:** If the product will be listed on AppExchange as an ISV offering, it must be a 1GP or 2GP managed package. Only managed packages provide IP protection (Apex classes are compiled; source is not accessible to subscribers). Use unlocked packages only for internal customer org modular deployment.

---

## Gotcha 3: 1GP Packaging Org Is Org-Centric — Not Compatible with DX and Scratch Orgs

**What happens:** A 1GP managed package team tries to adopt Salesforce DX (scratch orgs, source format, CI/CD). They discover that metadata must still be pushed to and pulled from the 1GP packaging org. Scratch orgs cannot produce a 1GP managed package version.

**Impact:** The CI/CD pipeline must maintain a connection to the packaging org for 1GP version creation. Git source format metadata cannot be directly uploaded to the packaging org — a metadata API deploy to the packaging org is required. Modern DX workflows do not fully apply to 1GP.

**How to avoid:** 1GP is org-centric by design. Accept this constraint for existing 1GP products. For new products, use 2GP which is fully DX-compatible: scratch org development, `sf package version create` from source, no packaging org needed.

---

## Gotcha 4: Deletion Rules Invert Between 2GP Managed and Unlocked Packages

**What happens:** A team creates a 2GP managed package version with a critical bug, assumes deletion is safe because no subscriber has installed it, and discovers that released 2GP managed versions cannot be deleted. The same team later carries that rule over to its unlocked packages and treats those released versions as equally permanent — they are not. Salesforce's deletion matrix answers "Can I delete released packages and package versions?" with No for Second-Generation Managed Packages and Yes for Unlocked Packages; beta versions of both types are deletable.

**Impact:** For 2GP managed, the buggy released version stays in the system permanently — Salesforce can deprecate a version (mark it as not for installation) but cannot delete it. For unlocked, the opposite failure mode applies: "Deletion is permanent," and "Attempts to install a deleted package version will fail." Any CI/CD job, install script, or org that installs that `04t` version ID after the deletion fails, and there is no undo. The docs state only the install-time failure — they say nothing about orgs that already have the version installed, so do not promise either way.

**How to avoid:** Keep pre-release work on beta versions — beta is deletable for both package types. Before running `sf package version delete` or `sf package delete` against an unlocked package, confirm the package or version "isn't referenced as a dependency" by another package and is not pinned in any install pipeline; deleting the package itself requires deleting all associated package versions first. Deletion is gated by the **Delete Second-Generation Packages** user permission in the Dev Hub — withhold it from anyone who does not own the release train.
