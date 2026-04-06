# Well-Architected Notes -- Org Shape And Scratch Definition

## Relevant Pillars

- **Reliability** -- A well-authored scratch org definition file ensures that every developer and CI run gets a consistent, reproducible environment. Mismatched features or missing settings cause intermittent deployment and test failures that erode team confidence in the development pipeline. Org Shape increases reliability by sourcing configuration from a known-good org, but must be supplemented with explicit feature declarations for features it does not capture.

- **Operational Excellence** -- The definition file is a key operational artifact. Keeping it version-controlled, validated, and documented reduces environment provisioning friction. Migrating from deprecated `orgPreferences` to `settings` prevents silent drift. Pinning the release channel prevents surprise CI breakage during preview windows.

- **Security** -- The definition file can enable security-relevant settings such as session timeout policies, password complexity requirements, and IP restrictions via the `settings` block. Using Org Shape to mirror a security-hardened production org ensures scratch orgs inherit security posture by default, reducing the risk of developers building and testing against permissive environments that differ from production.

- **Scalability** -- Minimal, well-targeted definition files provision faster and consume fewer Dev Hub scratch org allocations. Over-specifying features wastes allocation resources and slows provisioning. Teams that manage multiple products can maintain separate definition files per product, each with only the features that product requires.

## Architectural Tradeoffs

The primary tradeoff is between **reproducibility via Org Shape** and **control via manual declaration**:

- Org Shape reduces maintenance burden -- when the source org changes, scratch orgs automatically reflect the new shape. But it introduces a runtime dependency on the source org and Dev Hub connectivity.
- Manual declaration gives full control and no external dependencies, but requires updating the definition file whenever the target org's feature set changes.
- The hybrid approach (Org Shape + explicit overrides) offers the best balance for most teams but adds complexity in documenting which features are manually declared and why.

A secondary tradeoff is **release pinning vs. early detection**. Pinning to `Previous` gives CI stability but delays discovery of preview-release breaking changes. Running both a pinned pipeline and a non-blocking preview pipeline resolves this at the cost of additional CI resources.

## Anti-Patterns

1. **Monolithic definition file for all use cases** -- Using a single definition file for package development, integration testing, and UAT when each context needs different features and settings. This leads to over-provisioned scratch orgs that take longer to create and conflate concerns. Instead, maintain separate definition files per purpose under `config/`.

2. **Ignoring Org Shape gaps** -- Relying entirely on Org Shape and never verifying that the resulting scratch org has all required features. When deployments fail weeks later, the root cause is difficult to trace back to the definition file. Always document and test for features Org Shape is known to exclude.

3. **Treating the definition file as write-once** -- Writing the definition file once during project setup and never revisiting it as the org evolves. New features enabled in production (e.g., enabling Einstein, adding Communities) are not reflected in the definition file, causing developer environments to diverge from production over time.

## Official Sources Used

- Metadata API Developer Guide -- https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Scratch Org Definition File -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file.htm
- Scratch Org Definition Configuration Values -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file_config_values.htm
