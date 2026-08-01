# Well-Architected Notes — SFDX Monorepo Patterns

**Operational Excellence:** the directory layout is the deployment boundary. Anything under
a `packageDirectories` path is package content and reaches every org that installs it, so
the decision about where a file lives is a decision about what ships — not an organisational
preference. Seed data and one-off scripts kept inside a package become permanent metadata in
a subscriber org that nobody can later account for; the same files in a sibling directory
outside every package path are equally accessible to CI and invisible to the artefact.

**Operational Excellence, the default directory:** exactly one path can be the default, and
its real function is to catch metadata retrieved without an explicit destination. Pointing
it at the base package makes an accidental retrieve land somewhere reviewers are already
looking, instead of quietly inside a feature team's package where it will be shipped by the
next version create. This is cheap insurance against a mistake that is otherwise silent.

**Scalability:** teams scale independently only if the shared surface has an owner. Two
packages both extending Account is normal; two packages both believing they define Account
is a defect that development scratch orgs cannot detect, because everything is pushed into
them. Give every shared object one owning package and make the extensions depend on it — the
dependency is what makes install order deterministic instead of incidental.

**Scalability, CI economics:** validating everything on every push is correct and
unaffordable, and a gate slow enough to be ignored is worse than no gate, because it still
consumes the time. The affordable version scopes both the *set* and the *depth*: build the
packages affected by the change — expanded through the dependency graph, since a base change
breaks consumers whose files did not move — and choose the test level by risk, with specified
tests on a pull request and the full local-test run before production.

**Reliability:** the failure mode unique to this layout is that the development environment
cannot reproduce it. A scratch org with all packages pushed installs fine regardless of
whether dependencies are declared, ownership is clear, or the order is right. Every one of
those defects surfaces first in a clean org — which is the argument for having a clean-install
job at all, and for not treating a green scratch org as evidence about installation.

## Official Sources Used

- Salesforce DX Project Configuration — `packageDirectories`, the one-default-path rule, and `sourceApiVersion` as a project-level key — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_ws_config.htm
- Project Configuration File for Unlocked Packages — the multi-package file with per-directory `package`, `versionNumber` and `dependencies` — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_pkg_config_file.htm
- Salesforce DX Project Structure and Source File Format — what lives under a package directory and therefore what ships — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_source_file_format.htm
- Metadata API `deploy()` — `testLevel` semantics, including what `RunLocalTests` excludes — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
- Apex Code Coverage — the 75% requirement that keeps test classes inside the package — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_code_coverage_intro.htm
