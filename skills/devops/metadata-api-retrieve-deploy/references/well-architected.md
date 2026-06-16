# Well-Architected Notes — Metadata API Retrieve / Deploy

## Relevant Pillars

Metadata movement sits at the intersection of how a Salesforce org
is built and how it's *kept buildable*. Three pillars carry the
weight here; Operational Excellence is dominant because the daily
question is "can a junior engineer ship a change without breaking
prod?"

- **Operational Excellence** — The single largest determinant of
  release velocity in a Salesforce org is whether metadata moves
  via a reproducible, git-tracked artifact (`package.xml` + the
  retrieved component XML, deployed by `sf project deploy
  validate` → `quick`) or via Change Sets / clicks. Teams that
  treat metadata as code ship daily; teams that don't ship monthly
  and regress regularly. The pillar is dominant because every
  symptom of poor operational excellence (no rollback story,
  no diff in code review, no automated test gate) traces back
  to this one substrate decision.

- **Reliability** — The `validate → quick` deploy pattern is a
  reliability lever, not a convenience: validation runs the test
  suite against the target's actual metadata state and produces
  a 10-day-reusable job ID. If the actual deploy is run within
  the window via `quick`, tests don't re-execute; the org sees
  exactly the validated state. Skipping validation and going
  straight to `sf project deploy start` against prod means
  every deploy is also a test run, which compresses the
  feedback loop in a bad way — a test failure mid-deploy means
  the deploy already started touching metadata before the
  failure surfaced. `rollbackOnError=true` (the default) limits
  the damage but doesn't eliminate the "we were 60 seconds
  into a 6-minute deploy when it failed" window.

- **Security** — `package.xml` is the canonical audit trail for
  what was deployed when. Pairing it with git history gives
  change-management auditors a complete "who, what, when, why"
  per release without any custom tooling. JWT bearer-flow auth
  for CI (server.key + Connected App with a digital signature)
  removes the username/password failure mode entirely — no
  rotating passwords, no MFA prompts, no token expiration
  surprises mid-pipeline. Setup → Deployment Settings'
  per-environment gating is a real defense for orgs that need
  it but is also the source of the `deployedFromIde` confusion
  (see `gotchas.md` Gotcha 5) — treat it as a deliberate choice,
  not a default-on safety net.

## Architectural Tradeoffs

The defining tradeoff is **which substrate moves metadata across orgs**:

| Substrate | Best for | Tradeoff |
|---|---|---|
| **Metadata API (SOAP, raw)** via `package.xml` | Direct platform-level control; bespoke deploy tooling; integration-partner managed services that can't run the sf CLI | Verbose envelope; no source-tracking; manual dependency authoring; the `deployedFromIde` flag is settable directly |
| **Source Format (SFDX project)** via `sf project deploy/retrieve` | The default for modern teams; CI-native; integrates with VS Code source-tracking; lets multiple developers work on the same project in scratch orgs | Source format is opinionated — some metadata types decompose oddly (e.g., `CustomLabels` splits into one file per label); conversion to/from "MDAPI format" is sometimes needed for legacy tooling |
| **Tooling API** | Single-component on-the-fly edits (toggle a flag on an `ApexClass`, update a `CustomField` from a Lightning component) | Not a deploy substrate — designed for IDE/dev-tool use, not release management; no built-in test gating or rollback |
| **Raw REST/CRUD on `*__c` objects** | Configuration-as-data: feature flags via `FeatureFlag__c` records, per-tenant tunables via `Tenant_Config__c` | Data, not metadata — moves with `sf data import tree` or a Bulk API job; no test gating; no per-environment promotion model beyond CSV exports |
| **Change Sets** | Truly one-off rescues against an org with no source-control history | All the failure modes of clicks-not-code (see `examples.md` anti-pattern); should be migrated away from as soon as practical |

The "right" answer in a healthy Salesforce org is "Source Format
SFDX project for 95% of work, raw Metadata API for the remaining
5% (integration-partner-driven deploys, custom CI scripts that
need to introspect the SOAP response, or one-off destructive
operations the sf CLI doesn't expose cleanly)." Change Sets and
Tooling API live at the edges — Change Sets for the unmigratable
legacy org, Tooling API for one-off dev tooling.

A second tradeoff: **wildcard vs explicit members in `package.xml`**.
The trap is treating this as a stylistic choice; it's a release-
posture choice. Wildcards are right for the full-tenant snapshot
job that runs once a night for backup purposes; explicit members
are right for every PR-driven change set deploy. Mixing the two
in the same manifest (e.g., wildcards on `ApexClass` and explicit
members on `CustomField`) is usually a sign that the team isn't
clear which posture they're in — pick one per manifest and split
into two manifests if both postures genuinely apply.

A third tradeoff: **`rollbackOnError` true vs false**. The default
(`true`) is correct in 99% of cases; the partial-state risk of
`false` is almost never worth the throughput gain. The only
legitimate use case is a scripted cleanup deploy that's
explicitly designed for partial success (e.g., "delete these 50
old reports, skip the ones already gone") with a rollback runbook
documented alongside.

## Anti-Patterns

1. **Change Sets as the release substrate.** No diff, no review,
   no rollback narrative, no CI gate. Even one Change Set per
   month accumulates into "we can't tell what's in prod."
   Migrate to git-tracked source-format the first time a release
   breaks something the team can't trivially revert.

2. **`rollbackOnError=false` (or `--ignore-errors`) on production
   deploys.** Partial deploys leave the org in a half-configured
   state that's harder to debug than a clean rollback. Reserve
   the flag for explicitly scripted cleanup jobs with a runbook;
   never use it as a "get past this failing component" workaround.

3. **Wildcards in `package.xml` for CI deploys.** Diff becomes
   incoherent, validation runtime explodes, reviewers can't
   tell what's actually shipping. Wildcards are for one-shot
   snapshots only.

4. **`NoTestRun` for production deploys.** Salesforce rejects
   this outright on prod, but the deeper issue is teams trying
   to *get around* the test gate (by deploying to sandbox first
   with NoTestRun, then promoting "validated metadata" without
   re-running tests). The validate → quick pattern exists exactly
   to amortize the test cost across the validation + deploy
   sequence — use it.

5. **Username/password auth in CI.** Hard-coded credentials,
   90-day password rotations breaking the pipeline overnight,
   MFA blocking the CI user. JWT bearer flow (server.key +
   Connected App) eliminates all three failure modes and is
   the Salesforce-recommended CI auth pattern.

## Official Sources Used

- Metadata API Developer Guide — Introduction:
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Metadata API Developer Guide — Metadata Types Reference:
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/types_list.htm
- Metadata API Developer Guide — `retrieve()` call:
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_retrieve.htm
- Metadata API Developer Guide — `deploy()` call:
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
- Salesforce CLI Reference — `sf project retrieve` / `sf project deploy`:
  https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_retrieve_commands_unified.htm
- Salesforce Well-Architected — Operationally Excellent (Resilient):
  https://architect.salesforce.com/well-architected/operational-excellence/resilient
