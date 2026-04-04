# Well-Architected Notes — Second-Generation Managed Packages

## Relevant Pillars

### Security

2GP managed packages enforce IP protection by obfuscating Apex source in subscriber orgs. Practitioners must account for this by designing self-describing error handling, diagnostic instrumentation, and support tooling that does not rely on source visibility. AppExchange listing requires a Salesforce security review — passing this review gates public distribution, so security posture must be designed in from the start, not patched in before review. The `@namespaceAccessible` annotation expands the Apex API surface across packages within the same namespace; over-use exposes more of the internal implementation than necessary. Restrict `@namespaceAccessible` to the minimum required public API.

### Operational Excellence

The Dev Hub-centric model moves all package lifecycle operations (create, version, promote, install, push-upgrade) into CLI commands that are fully scriptable and CI/CD-integrable. Operational excellence in 2GP means codifying the full release pipeline — from JWT-based Dev Hub auth through version creation with code coverage through promotion — so that no release step requires manual UI interaction. Scratch orgs replace long-lived development environments, enforcing ephemeral-environment discipline. Version metadata (04t IDs) should be tracked in release artifacts and linked to the VCS commit that produced them.

### Adaptability

Flexible versioning (ancestor selection) allows ISVs to course-correct before a version reaches subscribers. Patch versions enable targeted bug fixes without forcing minor version progression on the full subscriber base. Namespace sharing across 2GP packages enables a modular ISV architecture where capabilities can be packaged independently and composed at the subscriber level — this is a significant architectural improvement over the monolithic namespace-per-package model forced by 1GP.

---

## Architectural Tradeoffs

**Dev Hub org choice:** Using a Partner Business Org as Dev Hub provides package durability (no expiry risk) and higher daily limits. Using a Developer Edition org is faster to set up but creates existential risk for any packages built against it if the org expires. For any production-intent package, there is no valid reason to use a Developer Edition org as the Dev Hub.

**Namespace sharing vs. isolation:** Sharing a namespace across multiple 2GP packages enables modular ISV architectures and cross-package Apex reuse via `@namespaceAccessible`. However, it requires careful governance of what is exposed — a poorly scoped public Apex API becomes a breaking change obligation on every future package release. Isolated namespaces (one per product line) remain appropriate when products are truly independent.

**Patch versions vs. minor releases:** Patch versions are appropriate for bug fixes that must not expand the API or metadata surface. Minor versions are appropriate for new features or additive metadata changes. Using minor releases for bug fixes inflates the subscriber upgrade burden and may trigger AppExchange re-review requirements. Abusing patch versions for feature additions risks introducing breaking changes to the patch-version contract.

**Push upgrades vs. subscriber-initiated installs:** Push upgrades can migrate subscribers without their action but carry risk if the package version is not thoroughly tested. Subscriber-initiated installs give subscribers control and time to test in sandboxes first. Best practice for managed upgrades is to validate in sandboxes before pushing to production, using a staggered rollout.

---

## Anti-Patterns

1. **Using a Developer Edition org as the production Dev Hub** — Any package created against a Developer Edition org is at risk of permanent loss if the org expires. All production-intent managed packages must be created against the Partner Business Org. This is not a preference — it is a durability requirement.

2. **Creating package versions without `--code-coverage` and attempting late-stage promotion** — Omitting `--code-coverage` is acceptable only for throwaway builds that will never be promoted. Treating it as an optimization that can be added "before release" creates unpromotable build artifacts. The correct practice is to always include `--code-coverage` in any version creation that is part of a release pipeline.

3. **Over-exposing Apex via `@namespaceAccessible`** — Annotating broad internal classes as `@namespaceAccessible` to enable cross-package access creates a wide public API surface that becomes a breaking change commitment. Expose only the minimum interface required by dependent packages, and design that interface explicitly rather than annotating existing internal classes.

4. **Hardcoding package version IDs in deployment scripts instead of `packageAliases`** — Hardcoded 04t IDs in scripts drift out of sync as versions are promoted. All version references should go through named aliases in `sfdx-project.json`, updated as part of the release process, so that downstream scripts and dependent packages pick up the correct version automatically.

---

## Official Sources Used

- Second-Generation Managed Packages Developer Guide (First-Generation Managed Packages companion) — local import at `knowledge/imports/pkg1-dev.md`; covers Dev Hub enabling, namespace linking, 1GP→2GP migration, patch versioning, and conversion workflow
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm — project structure, scratch org patterns, sfdx-project.json configuration
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm — `sf package create`, `sf package version create`, `sf package version promote`, `sf package install`, `sf package push-upgrade schedule`
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — metadata type support in managed packages
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — operational excellence, adaptability, and security pillar framing
