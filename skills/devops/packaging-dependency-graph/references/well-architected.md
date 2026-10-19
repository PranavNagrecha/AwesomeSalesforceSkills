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

Corpus: Summer '26 (API 67.0) PDFs fetched from resources.docs.salesforce.com/262 and converted with `pdftotext -layout`; line numbers are `grep -n` positions. `sfdx_dev.txt` = Salesforce DX Developer Guide, `pkg2_dev.txt` = Second-Generation Managed Packaging Developer Guide.

- `sfdx_dev.txt` L14708–14722 — `calculateTransitiveDependencies`: list direct dependencies only when true; enables `package version displaydependencies` (SKILL.md Core Concepts, gotcha 3).
- `sfdx_dev.txt` L14750–14826 — `dependencies` syntax: alias form, name + `versionNumber`, outside-Dev-Hub form, `0Ho`/`04t` IDs, list in order of installation (SKILL.md JSON fence, checker).
- `sfdx_dev.txt` L14995–15058 — Unlocked Packaging Keywords: `LATEST`, `NEXT`, `RELEASED`, `HIGHEST`, `NONE` (existing customers can't upgrade) (keyword table, anti-patterns 2–3).
- `sfdx_dev.txt` L16170–16201 — Considerations for Promoting Packages with Dependencies: skip validation, promote base then use `RELEASED`, `LATEST` vs `RELEASED` mapping with the 1.0.0.2/1.0.0.3 example (gotchas 1–2, worked-example.md).
- `sfdx_dev.txt` L15102–15190 — `SubscriberPackageVersion.Dependencies` (Tooling API) returns dependency 04t IDs in install order (gotcha 4, worked-example.md).
- `sfdx_dev.txt` L15713, L16136–16138, L16237 — release status can't be changed by update; no new versions on a promoted MAJOR.MINOR.PATCH; promote permission in the Dev Hub (gotcha 5).
- `sfdx_dev.txt` L16522–16540 — deletion: unlocked beta and released versions deletable, released 2GP managed not; deletion permanent; check it isn't a dependency first (gotcha 7).
- `pkg2_dev.txt` L19465–19485 — 2GP ancestor must be the highest promoted version; `HIGHEST` keyword recommended (anti-pattern 3).
- `sfdx_dev.txt` L15882–15893 and `api_rest.txt` L8057 — `Package2VersionCreates` daily limit, visible with `sf limits api display` (CI job sizing).
