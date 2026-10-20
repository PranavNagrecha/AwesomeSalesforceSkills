# Well-Architected Notes — Git Branching For Salesforce

## Relevant Pillars

- **Operational Excellence** — A well-chosen branching strategy is foundational to operational excellence. It determines how reliably and efficiently code moves from development to production. Poor branching models create manual merge overhead, deployment failures, and slow recovery from production incidents. The Well-Architected framework emphasizes repeatable, automated, and observable processes — all of which start with the branch model.
- **Reliability** — Branch protection rules, mandatory CI checks, and structured merge flows directly support reliability. A hotfix branch that can bypass the normal release train ensures rapid recovery. Package ancestry (the highest promoted version as ancestor, pkg2_dev 264 L18256-18258) ensures that every promoted version is a known-good successor to the previous one, preventing upgrade failures in subscriber orgs.
- **Security** — Branch protection (no direct pushes, required reviews) is a security control. It ensures that no single developer can push unreviewed code to production-bound branches. For managed packages, controlling which branch can create package versions prevents unauthorized code from entering the distribution channel.

## Architectural Tradeoffs

**Simplicity vs. isolation.** Trunk-based development minimizes branch management overhead but requires mature CI and disciplined developers. Environment branching provides isolation for parallel workstreams but introduces merge debt and longer feedback loops. The right choice depends on team maturity and release cadence, not on a universal best practice.

**Scratch orgs vs. persistent sandboxes.** Scratch orgs pair naturally with short-lived feature branches — each branch gets a fresh, disposable org. Persistent sandboxes pair with long-lived branches but accumulate state drift. Teams that rely on sandboxes for feature development will face more merge conflicts because sandbox state and branch state diverge over time.

**Monorepo vs. multi-repo for packages.** A single repository with all packages simplifies cross-package dependency management and atomic commits. Multiple repositories provide stronger isolation and independent release cycles but require coordinated versioning. The branching strategy must account for this: monorepo trunk-based is simpler; multi-repo requires per-repo branch policies.

## Anti-Patterns

1. **Branching without automation** — Creating a complex branching model (GitFlow with release, hotfix, develop, and feature branches) without CI/CD automation to enforce it. Without automated merge checks, deploy validations, and branch protection, the model degrades into manual gatekeeping that developers bypass under deadline pressure.
2. **One branch per developer instead of per feature** — Giving each developer a long-lived personal branch creates silos. Changes accumulate for weeks before merging, producing massive conflicts. Salesforce metadata (profiles, permission sets, custom labels) is particularly vulnerable because many developers touch the same files.
3. **Promoting package versions from feature branches** — Branch-tagged versions are documented (`--branch`, sfdx_dev 264 L15993-15995), but only one version per major.minor.patch can be promoted and released (sfdx_dev 264 L16033-16034). An earlier version of this note said feature-branch versions "cannot be promoted or used as ancestors" and "violate the linear ancestry requirement"; UNVERIFIED (2026-10-20) as stated. Promote from one controlled path; promoting from several wastes build time and creates confusion about which version is the "real" one.

## Official Sources Used

- Corpus citations used by this skill: sfdx_dev 264 L1568-1625 (decomposed types), L9970 and L3712-3713 (scratch org duration), L15084-15086, L15993-16034 (ancestry keywords, branches, promotion), L16300-16301; pkg2_dev 264 L584-586, L1081, L18256-18258, L18448-18449, L18674-18679 (flexible versioning, ancestor rules, `--tag`); api_meta 264 L4707, L4746 (destructive changes).
- Salesforce DX Developer Guide — branching strategy guidance, scratch org lifecycle, source-driven development model: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce DX Developer Guide (Use Branches in Unlocked Packaging) — package-aligned branching, version ancestry constraints: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_pkg_use_branches.htm
- Second-Generation Managed Packaging Developer Guide (Package Ancestors) — ancestry and flexible versioning (managed 2GP allows branches, pkg2_dev 264 L584-586), ancestor specification in sfdx-project.json: https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/sfdx_dev_dev2gp_package_ancestor_intro.htm
- Salesforce Well-Architected: Operational Excellence — repeatable delivery processes, automation, and observability: https://architect.salesforce.com/well-architected/operational-excellence
- Metadata API Developer Guide — deploy/retrieve behavior, destructive changes manifests: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
