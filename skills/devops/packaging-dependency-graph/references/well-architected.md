# Well-Architected Notes — Packaging Dependency Graph

**Reliability:** the `dependencies` block is what turns an install order held in someone's
head into a property of the artefact. Undeclared, the graph still exists — it is simply
enforced by whoever runs the install, which works until the person doing the installing is a
subscriber. Declaring it moves the failure from a customer org at go-live to a version
create in CI.

**Reliability, reproducibility:** `LATEST` re-resolves every time a version is created, so
the same commit can produce two artefacts bound to different dependency builds. That is a
reasonable trade during development and an unreasonable one for anything promoted, because
it means the version id no longer identifies a single set of inputs. Pin literal build
numbers for release candidates; keep `LATEST` for the fast inner loop.

**Reliability, the gate that cannot see the defect:** a development scratch org has the
source pushed into it, so a dependent package installs whether or not the dependency is
declared. Any release gate that runs in such an org is structurally incapable of detecting a
missing declaration. The only test that can is an install into an org that has never seen
the source, in subscriber order — which is why that job is worth its runtime even though it
is the slowest thing in the pipeline.

**Operational Excellence:** promotion follows the graph bottom-up because a package cannot
be promoted while it depends on a beta version. That means the promotion order and the
`dependencies` arrays encode the same information, and maintaining them as two independent
lists guarantees they drift — with the drift only observable during a release. Derive one
from the other.

**Irreversibility:** promotion is not a movable tag. Subscribers install a specific
subscriber package version id, so a promoted version that reached anyone has to keep
working and the remedy for a bad release is a new version. That asymmetry is the argument
for promoting late, from the exact commit intended for release, and for recording the
version id next to the commit — when a defect is reported against a version, the id is the
only thing that identifies which source produced it. Where ancestry applies at all, it is a
managed second-generation concept, and its own rule is the same shape: only versions
promoted to managed-released state can be named as an ancestor.

## Official Sources Used

- Project Configuration File for Unlocked Packages — the `dependencies` array shape, `packageAliases`, and the `LATEST` / `NEXT` build keywords — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_pkg_config_file.htm
- Unlocked Packaging Keywords — what each keyword resolves to — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_pkg_config_keywords.htm
- Considerations for Promoting Packages with Dependencies — why promotion runs bottom-up — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/dev2gp_considerations_pkg_dependency.htm
- Which Package Types Can Your Package Depend On? — the legal edges in the graph — https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/sfdx_dev_dev2gp_dependency_overview.htm
- Specify a Package Ancestor in the Project File — `ancestorId` / `ancestorVersion`, the managed-released rule, and `HIGHEST` — https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/sfdx_dev_dev2gp_config_ancestors.htm
- Salesforce CLI Reference — unified `package` commands (confirms `sf package version displaydependencies`; there is no `sf package dependencies` topic; verified 2026-08-01) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_package_commands_unified.htm
- package Commands — `sf package version create`, `promote`, `install`, `version list` — https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_package.html
