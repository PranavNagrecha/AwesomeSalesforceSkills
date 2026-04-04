# Well-Architected Notes — Unlocked Package Development

## Relevant Pillars

### Reliability

Unlocked packages directly support reliability by making deployments deterministic and repeatable. A package version is an immutable artifact: the same `04t...` ID installs identically in every subscriber org, every time. This eliminates the "works in sandbox, breaks in production" failure mode caused by drift in change-set or metadata-API-based deployments.

Key reliability practices:
- Pin dependency versions to specific `04t...` IDs in production pipeline references (not `LATEST`) to prevent unexpected upstream changes from affecting releases.
- Treat package version promotion as a one-way gate — only release-quality code is promoted.
- Validate installation in a production-equivalent sandbox before promoting and targeting production.

### Operational Excellence

The package lifecycle (create, version, promote, install) is designed for automation. CI/CD integration is a first-class use case: `sf package version create` is idempotent per version number and supports `--json` output for pipeline parsing. Operational maturity in this space means:

- Version IDs are stored in source control (`sfdx-project.json`) and treated as release artifacts.
- Package install status is queryable via `sf package installed list` for drift detection.
- `sf package version list` provides a complete audit trail of every version created, including creator, date, code coverage, and promotion status.
- Dev Hub `Package2Version` and `Package2` objects are queryable via SOQL for custom dashboards and release tracking.

### Scalability

The multi-package architecture pattern scales development teams by decomposing a monolithic org into independently versionable domains. This allows:

- Teams to release on different cadences without coordinating a single "org deploy."
- Parallel development in isolated scratch orgs without stepping on each other's package versions.
- Incremental delivery: only the changed package version needs to be installed in subscriber orgs, not a full org deployment.

Limits to be aware of (as of Spring '25):
- Dev Hub orgs can have up to 500 active unlocked packages (combined with 2GP managed packages).
- Package version creation has a concurrent limit — too many simultaneous `sf package version create` calls in CI may queue or fail.
- Subscriber orgs can have up to 250 installed packages (managed + unlocked combined).

---

## Architectural Tradeoffs

### Single Package vs. Multi-Package Architecture

| Factor | Single Package | Multi-Package |
|---|---|---|
| Initial setup complexity | Low | Higher (dependency management) |
| Version independence | None — one version for everything | Each package versions independently |
| Deploy time per change | All-or-nothing full package deploy | Only changed packages need new versions |
| Team autonomy | Single deployment bottleneck | Teams own their package release cadence |
| Rollback granularity | Entire org | Per-package rollback |
| Coverage gate | Single coverage check | Each package must independently meet 75% |

**Recommendation:** Start with a single package for small teams (1–3 developers). Decompose into multi-package when teams grow, domains diverge, or release cadences differ across features.

### Namespaced vs. Namespace-Less

| Factor | Namespace-Less | Namespaced |
|---|---|---|
| Setup | No registration required | Namespace must be registered and linked |
| API name safety | Risk of conflicts in subscriber org | Prefix isolates all API names |
| Refactoring | Easier (no prefix in code) | All references must include prefix |
| Distribution | Internal use; not AppExchange-ready | Required for AppExchange or managed packaging |
| Reversibility | Cannot add namespace later | Can convert to managed package (2GP) path |

**Recommendation:** For internal enterprise packages, namespace-less is appropriate and simpler. For any package intended for external distribution or that needs strict API name isolation, use a namespace from the start.

---

## Anti-Patterns

1. **Treating unlocked packages as change sets** — Using `sf package version create` and `sf package install` as glorified change set deployments without managing the package lifecycle (no promotion gate, no version tracking, no dependency declarations) eliminates the reliability and repeatability benefits of packaging. The correct model is: version IDs are immutable release artifacts that flow through dev → QA → production as a unit. Do not create a new version for every commit and install without gates.

2. **One giant package for the entire org** — Placing all org metadata in a single package directory creates a deployment monolith. Every change triggers a full version creation cycle, code coverage must pass org-wide, and rollback is all-or-nothing. This anti-pattern also prevents teams from working independently. Decompose by domain or layer.

3. **Skipping the promotion step in the pipeline** — Beta versions installed in sandboxes cannot be installed in production. Teams that automate sandbox installs but skip promotion create a hidden gap in their pipeline that only surfaces at the production deployment step — typically at the worst possible time. Make `sf package version promote` an explicit, auditable, approval-gated step in every release pipeline.

4. **Hardcoding subscriber package version IDs in source outside `sfdx-project.json`** — Scattering `04t...` IDs in pipeline YAML, README files, or scripts creates stale references that diverge from `sfdx-project.json`. The package manifest is the single source of truth. All tooling should derive version IDs from it via `sf` CLI commands or JSON parsing of the manifest.

---

## Official Sources Used

- Salesforce DX Developer Guide: Unlocked Packages — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_pkg_intro.htm
- Second-Generation Package Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/pkg2_dev_intro.htm
- Salesforce DX Developer Guide: Second-Generation Packaging — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp.htm
- Salesforce CLI Reference: sf package commands — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce Architects: Unlocked Packages for Customers — https://architect.salesforce.com/deliver/release-management-deployment/unlocked-packages-for-customers/learn
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
