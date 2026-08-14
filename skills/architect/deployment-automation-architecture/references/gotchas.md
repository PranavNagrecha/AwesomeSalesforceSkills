# Gotchas — Deployment Automation Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: A Profile deploy is an overlay, and the retrieve that produced it was scoped

**What happens:** Two documented behaviours compound into silent permission drift. On retrieve: "The content of a
profile returned by Metadata API depends on the content requested in the `RetrieveRequest` message. For example,
profiles only include field-level security for fields included in custom objects returned in the same `RetrieveRequest`
as the profiles." On deploy: "Profile metadata deployment is designed to overlay the existing Profile settings in a
target org. For example, if you disable permissions for a profile, the newly disabled permission information isn't
exported."

The consequence is that a Profile file in source control is not a description of a Profile. It is a partial patch whose
contents depend on what else was in the manifest the day it was retrieved, and deploying it can only *add* permissions
unless every revocation is written out explicitly as `<value>false</value>`.

**When it occurs:** Every pipeline that treats `force-app/main/default/profiles/*.profile-meta.xml` as the source of
truth for access. The security team revokes a permission in the source branch, the deploy is green, and the permission
is still enabled in production.

**How to avoid:** Do not attempt to govern access through Profile deploys. Move permissions to Permission Sets and
Permission Set Groups, which deploy as whole objects, and keep Profiles minimal. Where a Profile must carry a
revocation, write the explicit `false` element and add a post-deploy assertion that reads the permission back. One more
trap for new Profiles: "If you deploy a profile that doesn't exist in the target org and don't specify any permissions
or settings, then the resulting profile contains all permissions and settings in the standard Minimum Access -
Salesforce profile (API version 60.0 and later) or the standard Standard User profile (API version 59.0 and earlier)" —
so the same empty file yields a very different Profile depending on the manifest's API version.

---

## Gotcha 2: `rollbackOnError` defaults to `false`, and the API version comes from `package.xml`

**What happens:** Two `DeployOptions` defaults surprise people who assume the CLI is in charge.

- `rollbackOnError`: "Indicates whether any failure causes a complete rollback (`true`) or not (`false`)." The default
  is `false`. The guide adds: "This parameter must be set to `true` if you're deploying to a production org." So a
  sandbox deploy can and does leave a partially-applied state that production would have rejected — which is exactly
  the environment where teams first observe "it deployed fine in UAT".
- API version: "The API version that the deployment uses is the API version that's specified in `package.xml`." Not the
  CLI version, not the org's release. A manifest left at `<version>58.0</version>` deploys Apex that keeps the API 58.0
  behaviour — including system mode as the default access mode for database operations.

**When it occurs:** On the first non-trivial failure in a shared integration sandbox, and on every Apex class whose
manifest nobody has bumped since the pipeline was built.

**How to avoid:** Set `rollbackOnError: true` explicitly for every environment, not just production, so lower
environments fail the same way production will. Pin and review `<version>` in `package.xml` as a deliberate decision
with an owner, and treat bumping it as a change that requires a test run — not a cosmetic edit.

---

## Gotcha 3: Destructive changes have an ordering contract, and one field type ignores `purgeOnDelete`

**What happens:** "By default, deletions are processed before component additions." Since API version 33.0 you can
override this with two manifests: `destructiveChangesPre.xml` for deletions before additions, and
`destructiveChangesPost.xml` for deletions after — which is what you need when an Apex class must be updated to drop a
dependency before the object it references can go. The guide adds a detail that breaks naive test sequencing: "Post
destructive changes are processed before running any tests."

Recycle Bin behaviour is not uniform either: "When you delete a roll-up summary field using Metadata API, the field
isn't saved in the Recycle Bin. The field is purged even if you don't set the `purgeOnDelete` deployment option to
`true`." And `purgeOnDelete` itself "only functions in Developer Edition or sandbox environments, not production".

**When it occurs:** The first time a release removes a field that something still references, and the first time
somebody assumes a deleted roll-up summary can be undeleted during a rollback window.

**How to avoid:** Choose `Pre` or `Post` deliberately per destructive change rather than defaulting to
`destructiveChanges.xml`, and record the choice in the release notes. Treat roll-up summary deletion as irreversible —
capture the field definition and a data snapshot before the deploy, because rollback will not bring it back. One more:
"If you try to delete some components that don't exist in the organization, the rest of the deletions are still
attempted", so a green destructive deploy is not evidence that everything named in the manifest existed.

---

## Gotcha 4: `RunSpecifiedTests` enforces 75% per class, not org-wide

**What happens:** The `testLevel` enumeration accepts `NoTestRun`, `RunSpecifiedTests`, `RunRelevantTests` (beta),
`RunLocalTests`, and `RunAllTestsInOrg`. For the narrow levels the guide is specific: "Each class and trigger in the
deployment package must be covered by the executed tests for a minimum of 75% code coverage." That is a per-component
floor. An org sitting comfortably at 88% overall still fails the deploy if one trigger in the package lands at 70%.

**When it occurs:** On the fast pipeline everybody builds to avoid `RunLocalTests` on large orgs. It works until a
release includes a thinly-covered class, and then it fails at the worst moment with a coverage error rather than a
test failure, which sends people looking in the wrong place.

**How to avoid:** If the pipeline uses `RunSpecifiedTests`, compute the specified list from the changed components'
actual test dependencies rather than from a hand-maintained list, and gate the PR on per-class coverage so the failure
surfaces in review instead of at deploy time.

---

## Gotcha 5: Some metadata types carry per-deploy and daily counts

**What happens:** "Certain metadata types have deploy and retrieve limits. Limits apply to each individual deploy or
retrieve transaction, and there are daily limits for specific metadata types." The published figures are: Individual
Metadata Deploy 50, Daily Metadata Deploys 100, Individual Metadata Retrieve 100, Daily Metadata Retrievals 200 — and
they apply to a named list of types including `AIAuthoringBundle`, `AnalyticsDashboard`, `AnalyticsVisualization`, and
`AnalyticsWorkspace`, not to metadata generally.

**When it occurs:** In analytics-heavy orgs, and in any pipeline that redeploys the full manifest on every merge. The
daily ceiling is per-org over a rolling 24 hours, so a busy branch day can exhaust it and block the hotfix that
follows.

**How to avoid:** Deploy deltas rather than the full manifest, and check the affected type against the Metadata
Coverage report and the Metadata Type Limits section before designing a pipeline that redeploys it on every commit.

## Official Sources Used

- Metadata API Developer Guide, Version 67.0 (Summer '26) — *deploy()* / `DeployOptions`: confirms `rollbackOnError`
  default `false` and the production requirement, `checkOnly`, the `testLevel` enumeration values, the 75%
  per-class-and-trigger coverage rule, `ignoreWarnings`, and that `purgeOnDelete` functions only in Developer Edition
  and sandboxes.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Deleting Components from an Organization*: default deletion ordering,
  `destructiveChangesPre.xml` and
  `destructiveChangesPost.xml` (API 33.0+), "Post destructive changes are processed before running any tests", the
  roll-up summary Recycle Bin exception, and that the deployment's API version comes from `package.xml`.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_deleting_files.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Profile*: the `RetrieveRequest`-scoped retrieve, the overlay deployment
  design, and the Minimum Access / Standard User default for a profile that doesn't exist in the target org.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_profile.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Metadata Type Limits*: Individual Metadata Deploy 50, Daily Metadata
  Deploys 100, Individual Metadata Retrieve 100, Daily Metadata Retrievals 200, applied to `AIAuthoringBundle`,
  `AnalyticsDashboard`, `AnalyticsVisualization`, and `AnalyticsWorkspace`.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_metadata_type_limits.htm (verified 2026-08-14)
