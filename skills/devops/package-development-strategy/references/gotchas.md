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

## Gotcha 4: Package Version Deletion Is Restricted — Beta Versions Can Be Deleted, Released Cannot

**What happens:** A team creates a 2GP package version with a critical bug and wants to delete it from the system. Subscribers have not yet installed it, so the team assumes deletion is safe. They discover that released package versions cannot be deleted.

**Impact:** The buggy released version remains in the system permanently. Salesforce can deprecate a version (mark it as not for installation) but cannot delete a released version. The version is visible in the package version list indefinitely.

**How to avoid:** Use beta versions (`--skip-validation` flag) during development and testing. Beta versions can be deleted. Only create a released version when the package is ready for subscriber installation. A released version is a permanent record.
