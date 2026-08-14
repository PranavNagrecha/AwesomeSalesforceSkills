# Well-Architected Notes — Deployment Automation Architecture

## Relevant Pillars

- **Resilient (primary)** — the pipeline is the org's blast-radius control. `rollbackOnError` defaults to `false`, so a
  partially-applied deployment is the platform's default outcome unless the pipeline overrides it; every environment
  that does not set it `true` is training the team to trust a result production will not reproduce.
- **Automated** — the pillar's claim is that a change should reach production the same way every time. Three defaults
  quietly break sameness: the API version comes from `package.xml` rather than the tool, destructive changes are
  ordered before additions unless you say otherwise, and Profile deploys overlay rather than replace. Each one makes
  the outcome depend on something outside the pipeline definition.
- **Secure** — Profile-based access governance fails silently in a pipeline. A revocation expressed as a deleted XML
  element deploys green and changes nothing.
- **Adaptable** — a manifest pinned to an old API version keeps old runtime semantics indefinitely, including the
  pre-67.0 system-mode default for database operations. The pipeline becomes the thing preventing the upgrade.

Performance is not a design driver here beyond one real constraint: certain metadata types carry individual and daily
deploy/retrieve counts, so a pipeline that redeploys the full manifest on every commit can exhaust an org-level daily
allowance and block a hotfix.

## Architectural Tradeoffs

**Test-level scope vs deploy duration.** `RunLocalTests` is the honest gate and the slow one. `RunSpecifiedTests` is
fast but enforces a per-component floor — 75% coverage for each class and trigger in the package — which converts a
missing test into a deploy-time coverage error rather than a review-time failure. Choosing the fast level is defensible
only if the specified test list is *derived* from the change set; a hand-maintained list decays into a fiction within a
quarter.

**Profiles vs Permission Sets in source control.** Profiles are what auditors ask for and what the pipeline handles
worst: partial on retrieve, additive on deploy. Permission Sets deploy as whole objects and diff meaningfully. The
trade is migration effort now against a permanent class of silent access drift, and the drift does not announce itself
— it shows up in an access review months later.

**One deployment vs two for destructive change.** Splitting "update the code" and "delete the field" into two releases
is simpler to reason about and creates an untested intermediate state in production. Combining them with
`destructiveChangesPost.xml` is one atomic promotion and requires the team to understand deletion ordering. Prefer the
combined form and pay the learning cost once.

**Tool-managed pipeline vs assembled pipeline.** Commercial tools bring an audit trail and approval workflow out of the
box, which matters under SOX or SOC 2. An assembled SFDX + CI pipeline can match it, but the audit trail becomes
something the team owns and must prove. Decide against the compliance envelope, not against tool preference.

## Anti-Patterns

1. **Green-deploy-as-evidence.** Treating a successful deployment as proof that the intended change took effect.
   Deleting components that don't exist still succeeds, Profile revocations are no-ops, and mixed-DML validation is
   skipped at deploy time. Deployment success means the platform accepted the payload, nothing more. Add read-back
   assertions for anything that matters.
2. **The unversioned manifest.** Leaving `<version>` in `package.xml` at whatever it was when the repo was created.
   Every Apex class redeployed through that manifest inherits the old runtime semantics, and nobody reads the file, so
   the pin survives release upgrades indefinitely.
3. **Lower environments with weaker deploy options than production.** Omitting `rollbackOnError` outside production, or
   using `NoTestRun` in UAT. The pipeline's purpose is to fail early; a stage configured more permissively than the one
   after it inverts that purpose and moves discovery to the change window.

## Official Sources Used

- Metadata API Developer Guide, Version 67.0 (Summer '26) — *deploy()* / `DeployOptions`: `rollbackOnError` default
  `false` and the production requirement, `checkOnly`, the `testLevel` enumeration, the 75% per-class-and-trigger
  coverage rule for specified-test levels, and the Developer-Edition-and-sandbox scope of `purgeOnDelete`.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Deleting Components from an Organization*: deletion
  ordering, the `Pre`/`Post` destructive manifests, "Post destructive changes are processed before running any tests",
  and that the deployment's API version comes from `package.xml`.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_deleting_files.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Profile*: the `RetrieveRequest`-scoped retrieve and the overlay
  deployment design.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_profile.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Metadata Type Limits*: individual and daily deploy/retrieve counts.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_metadata_type_limits.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Versioned Behavior Changes*: "In API version 67.0 and later, Apex runs in user
  context by default … In API version 66.0 and earlier, system mode is the default", which is what a stale
  `package.xml` version pins.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security_sharing_chapter.htm (verified 2026-08-14)
