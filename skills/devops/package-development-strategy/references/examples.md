# Examples — Package Development Strategy

## Example 1: ISV Choosing 2GP Managed Package for New AppExchange App

**Scenario:** An ISV is building a new Field Service add-on product for AppExchange listing. The team has experience with 1GP managed packages from a previous product but is evaluating whether to use 2GP for the new product.

**Problem:** 1GP packages are org-centric (namespace must be registered in a packaging org, not portable to DX) and do not support modern CI/CD workflows with scratch orgs. Metadata changes must be pulled from the packaging org rather than tracked in version control. Dependency management is limited.

**Solution:** Build the new product as a 2GP managed package. Register a namespace in a Dev Hub org. Create scratch orgs with `sfdx force:org:create` and develop all metadata in source format. Package versions are created with `sf package version create`. The namespace is permanently bound to the Dev Hub at registration.

**Why it works:** 2GP is the Salesforce-recommended approach for all new ISV development. 2GP supports: (a) multiple packages with explicit dependencies, (b) scratch org-based development (no packaging org), (c) source-format metadata compatible with Git version control, (d) AppExchange listing. The namespace cannot be changed after registration, so selecting the namespace is a permanent decision.

---

## Example 2: Internal Customer Team Using Unlocked Packages for Modular Org Development

**Scenario:** A large enterprise has a single Salesforce org shared by Sales, Service, and Finance teams. Each team has its own deployment lifecycle. The DevOps team wants to allow each business unit to deploy independently without breaking other teams' metadata.

**Problem:** Using a single unmanaged metadata deployment treats all metadata as one monolithic deployment unit. A Service Cloud change can accidentally overwrite a Sales Cloud Profile permission if both are in the same deployment package.

**Solution:** Create three unlocked packages: `SalesCloud-Core`, `ServiceCloud-Core`, and `FinanceCloud-Core`. Each package owns the metadata for its domain. Packages declare dependencies on shared components in a fourth `Shared-Core` package. Each team has an independent release pipeline targeting their package.

**Why it works:** Unlocked packages provide modular deployment boundaries within a single org. Package versions are immutable once created; deploying package version 2.5 of ServiceCloud-Core does not touch SalesCloud metadata. Unlocked packages do not require a namespace and are not eligible for AppExchange listing.

---

## Example 3: Namespace Selection Mistake — Cannot Be Changed

**Scenario:** A team registers a namespace `myns` for their new 2GP managed package during development. After the product launches on AppExchange, the company is acquired and rebranded. The team wants to rename the namespace to match the new brand.

**Problem:** Salesforce namespace selection is permanent and irreversible. Once a namespace is registered and bound to a Dev Hub, it cannot be changed or transferred. The API names of all components in all package versions include the namespace prefix permanently.

**Solution:** There is no workaround within the same package. A brand-new package with the new namespace would be a completely separate product, requiring all subscribers to uninstall the old package and install the new one — a disruptive migration. The only mitigation is to choose a namespace carefully (short, brand-neutral if possible) before registering.

**Why it matters:** This gotcha has destroyed acquisition integrations and forced full subscriber migrations. Namespace selection deserves the same due diligence as a domain name selection.
