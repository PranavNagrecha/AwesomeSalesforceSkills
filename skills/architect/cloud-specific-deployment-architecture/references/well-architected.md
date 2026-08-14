# Well-Architected Notes — Cloud-Specific Deployment Architecture

## Relevant Pillars

- **Automated (primary)** — the pillar's promise is that a change reaches production the same way every time. Per-cloud
  deployment breaks that promise structurally: some component types have no Metadata API representation at all, and for
  those "you must do it manually in each of your organizations." The architecture's job is not to pretend otherwise but
  to make the manual set explicit, small, owned, and shrinking release over release.
- **Resilient** — cross-cloud releases fail on ordering. Deletions run before additions by default, connectors are
  separate metadata from the objects that consume them, and org-level settings are a third deployable. A pipeline whose
  stages do not encode those dependencies produces partial states that nobody designed and nobody tested.
- **Adaptable** — coverage moves every release. A design that hardcodes today's coverage assumptions is a design that
  will be wrong in three releases, silently, because unsupported types drop out of a payload without failing it.
- **Efficient** — counted metadata types carry an org-wide daily ceiling (100 deploys per rolling 24 hours for the
  affected list). In a shared org that ceiling is a shared resource, and a pipeline that redeploys the full manifest per
  merge spends other teams' budget.

## Architectural Tradeoffs

**One orchestrator vs one tool.** No single tool covers platform metadata, Data 360 data kits, and the non-core clouds
well. The realistic choice is an orchestrator that calls per-cloud tooling, which buys correctness at the cost of a
pipeline with several failure modes and several sets of credentials. The alternative — forcing everything through one
tool — buys operational simplicity and quietly drops the components that tool does not model.

**Full-manifest deploys vs deltas.** Full-manifest deploys are idempotent, easy to reason about, and the honest answer
to drift. They also spend counted-type allowances on every merge and lengthen every release. Deltas are cheaper and
require the pipeline to compute the change set correctly — a computation that fails open, deploying less than intended,
which is the harder failure to notice. Prefer deltas for counted types specifically and full manifests elsewhere, so
the risk sits where the cost is.

**Automating a manual step vs documenting it.** Some cloud components can be driven through a cloud-specific API even
though they are absent from the Metadata API. Automating them adds a bespoke integration to maintain; documenting them
adds a runbook step that will be skipped one day under time pressure. Automate the ones that appear in every release;
document the ones that appear once a year, and name an owner for each rather than assigning them to a team.

**Uniform API version vs per-team upgrade.** A single `<version>` across every manifest gives uniform runtime semantics
and forces every team to upgrade together. Per-cloud versions let one team move early — and mean two stages of one
release run under different semantics, including the pre-67.0 system-mode default for database operations. Choose
uniform unless a specific team has a specific reason, and record the exception.

## Anti-Patterns

1. **Coverage from memory.** Asserting in a design document that a component type "deploys via Metadata API" without
   opening the Metadata Coverage report. The guide names that report "the ultimate source of truth" and it needs no org
   login, so this is a check that was skipped rather than one that was hard.
2. **Searching the old product name.** Looking for `Data Cloud` in the Metadata API guide, finding nothing, and
   concluding the types are unsupported. The chapter is *Data 360 Metadata Types* and it is substantial. Product
   renames are how architectures acquire imaginary gaps.
3. **Treating a green multi-cloud deploy as complete.** Unsupported types do not travel and do not fail. The release is
   complete when the manual steps in the coverage matrix have been executed and verified in each environment, not when
   the pipeline goes green.

## Official Sources Used

- Metadata API Developer Guide, Version 67.0 (Summer '26) — *Metadata Types*: the Metadata Coverage report as "the
  ultimate source of truth for metadata coverage across several channels".
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_types_list.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Unsupported Metadata Types*: the manual-in-every-org consequence for
  unsupported types.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_unsupported_types.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Data 360 Metadata Types*: current naming and the data-kit /
  connector / settings split.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_data_cloud_types.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Metadata Type Limits*: individual and daily deploy/retrieve counts.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_metadata_type_limits.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Deleting Components from an Organization*: deletion
  ordering and the `package.xml`-sourced API version.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_deleting_files.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Versioned Behavior Changes*: the 67.0 user-context default that a stale
  manifest version pins.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security_sharing_chapter.htm (verified 2026-08-14)
