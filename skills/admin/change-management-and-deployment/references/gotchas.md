# Gotchas: Change Management and Deployment

---

## Hidden Dependencies in Change Sets

**What happens:** A seemingly simple change set misses a required field, permission, or Flow dependency. Production validation fails late.

**When it bites you:** Admin-heavy orgs with loosely tracked metadata dependencies.

**How to avoid it:** Validate scope in lower environments and move toward source-driven release methods for recurring work.

---

## Flow Deployment Without Activation Planning

**What happens:** A Flow deploys successfully, but activation timing or version handling causes unexpected runtime behavior.

**When it bites you:** Record-triggered automation, entry-criteria changes, and cutovers replacing old automation.

**How to avoid it:** Treat activation as a release decision with smoke tests and fallback steps.

---

## Metadata Rollback Cannot Undo Data Damage

**What happens:** The team redeploys prior metadata and assumes the release is reversed. Data changes made by the release remain behind.

**When it bites you:** validation-rule relaxations, auto-updates, owner changes, and cutovers with record edits.

**How to avoid it:** Pair metadata rollback with data rollback or data repair steps when production records can change.

---

## Profiles Slip Into Every Release

**What happens:** Broad profile deployments create noisy diffs, accidental permission changes, and hard-to-review release packages.

**When it bites you:** older orgs and admin teams that never shifted to permission-set-centric delivery.

**How to avoid it:** isolate access changes into permission sets wherever possible and review profile deployments as exceptions.

---

## `rollbackOnError` Defaults to False, and the Guide Contradicts Itself About It

**What happens:** A deploy against a sandbox partly lands. Some components are in, some
are not, and the result comes back `SucceededPartial` — which reads as success in a
dashboard and in most scripts. The org is now in a state no environment has ever been in.

**When it bites you:** Any deploy where the option was never set explicitly, most often
a sandbox rehearsal driven by a tool or script that leaves `DeployOptions` at defaults.
Production is protected — the guide says the parameter "must be set to `true` if you're
deploying to a production org" (Metadata API Developer Guide, `deploy()` →
`DeployOptions` → `rollbackOnError`, api_meta L4256–L4260) — so the half-deployed state
only ever shows up in the environment you were using to prove the release was safe.

**How to avoid it:** Set `rollbackOnError` explicitly on every deploy, in every
environment, and never infer it. The two tables in the guide disagree: `DeployOptions`
says "The default is `false`" (api_meta L4260) and `DeployResult` says "Optional.
Defaults to `true`" (api_meta L7434–L7437). Then treat `SucceededPartial` in the
`DeployResult` `status` enum as a failure state in your release gate, not a pass —
it is one of nine values alongside `Succeeded` and `Failed` (api_meta L7444–L7456).

---

## The Default Test Level Is Different in Sandbox and Production — and Depends on the Package

**What happens:** A release rehearsed in a sandbox runs no tests and takes four minutes.
The same package against production runs every local test and takes ninety, blowing the
maintenance window. Or the reverse: an admin assumes a production deploy is test-gated,
and it silently runs nothing.

**When it bites you:** Whenever the test level is left unspecified. Three separate rules
apply, all from the guide.

**How to avoid it:** Know all three, then set `testLevel` explicitly so none of them
apply. (1) `NoTestRun` "applies only to deployments to development environments, such as
sandbox, Developer Edition, or trial organizations. This test level is the default for
development environments" (api_meta L4283–L4286). (2) `RunLocalTests` is "the default for
production deployments that include Apex classes or triggers" (api_meta L4317–L4321).
(3) If the production package contains no Apex components, "no tests are run by default"
(api_meta L2483–L2485) — and this changed at API 34.0: in API 33.0 and earlier a package
containing just a `CustomField` ran all local tests; from 34.0 it runs none
(api_meta L2486–L2489). A modern admin release of fields and layouts therefore ships to
production with zero test coverage unless you ask for some.

---

## Quick Deploy Has a Ten-Day Clock and Four Preconditions

**What happens:** A release validated on the 1st is promoted on the 12th. The quick
deploy is refused and the team either re-runs the full test suite inside the window they
had budgeted for a five-minute promotion, or postpones the release.

**When it bites you:** Long approval chains, releases parked behind a business freeze,
and any process where validation is done "early, to be safe".

**How to avoid it:** Validate close to the window, not far from it. The guide lists the
requirements for `deployRecentValidation()` (api_meta L4864–L4876): the components were
"validated successfully for the target environment within the last 10 days"; the Apex
tests in the *target* org passed as part of that validation; and coverage is met — 75%
overall with some trigger coverage if all or all-local tests ran, or 75% *per class and
trigger* if `RunSpecifiedTests` was used. Also note the target environment is part of the
contract: a validation against a staging sandbox does not license a quick deploy to
production. The mechanics of watching the resulting job (it returns a *new* id) are
covered in `devops/release-management`.

---

## A Destructive Manifest Is Inert Without a Companion `package.xml`

**What happens:** A delete-only release is zipped with just `destructiveChanges.xml`.
The deploy fails, or worse, reports success having deleted nothing, and the retired
field is still on the layout on Monday.

**When it bites you:** Field and object retirements, cleanup releases after a migration,
and any hand-built zip that skips the manifest because "there is nothing to add".

**How to avoid it:** Ship both files in the same directory. The guide is explicit: "To
deploy the destructive changes, you must also have a `package.xml` file that lists no
components to deploy, includes the API version, and is in the same directory as
`destructiveChanges.xml`" (api_meta L4630–L4637). Two more constraints ride along: the
destructive manifest uses the same format as `package.xml` "except that wildcards aren't
supported" (api_meta L4615–L4616), and ordering is chosen by filename —
`destructiveChangesPre.xml` runs before the additions, `destructiveChangesPost.xml` after
them, with post-deletions processed "before running any tests" (api_meta L4650–L4655,
L4687). The full retirement workflow is `devops/destructive-changes-deployment`; the
shape of both files is in `references/metadata-examples.md` §2.

---

## `purgeOnDelete` Silently Does Nothing in Production

**What happens:** A retirement release sets `purgeOnDelete` to skip the Recycle Bin. In
the sandbox rehearsal the components vanish. In production they land in the Recycle Bin
instead, and a later re-create of a field with the same API name collides with the
soft-deleted one.

**When it bites you:** Rename-by-recreate patterns, and any release that deletes then
immediately re-adds a component with the same name.

**How to avoid it:** Do not plan around it in production. The guide states the option
"only works in Developer Edition or sandbox orgs. It doesn't work in production orgs"
(api_meta L4239–L4240). One exception cuts the other way and is worth knowing before you
plan a rollback: "When you delete a roll-up summary field using Metadata API, the field
isn't saved in the Recycle Bin. The field is purged even if you don't set the
`purgeOnDelete` deployment option to `true`" (api_meta L4241–L4244). A deleted roll-up
summary is gone the moment the deploy succeeds — there is nothing to restore.

---

## A Validation Cannot Cover a Master-Detail Conversion, and the Real Deploy Empties the Recycle Bin

**What happens:** The team validates a data-model release cleanly, then the production
deploy fails on the one component validation refused to test — or succeeds and
permanently destroys detail records that were sitting in the Recycle Bin.

**When it bites you:** Releases that convert a Lookup to Master-Detail (or back), which
is a routine step when an admin tightens a relationship for roll-up summaries or sharing.

**How to avoid it:** Treat this change as un-validatable and rehearse it as a *full*
deploy to a spare sandbox. The guide: "If you change a field type from Master-Detail to
Lookup or vice versa, the change isn't supported when using the `checkOnly` option to
test a deployment… If a change that isn't supported for test deployments is included in a
deployment package, the test deployment fails and issues an error" — and its recommended
substitute is "Perform a full deployment to another test sandbox"
(api_meta L4176–L4190). Then the destructive half: a deployment including Master-Detail
relationships "deletes all detail records in the Recycle Bin" both when adding a new
Master-Detail field and when converting Lookup to Master-Detail; those records "are
permanently deleted from the Recycle Bin and can't be recovered" (api_meta L4191–L4207).
Empty or export the Recycle Bin before the window.

---

## Deployment Locks the Metadata It Is Touching, and Only One Runs at a Time

**What happens:** Two admins deploy during the same window. The second deploy sits in a
queue nobody is watching, and an admin making an unrelated Setup change to a locked
object gets an error they cannot explain.

**When it bites you:** Shared release windows, orgs with several admin teams, and any
"just push this small thing while the big one runs" moment.

**How to avoid it:** Declare a metadata freeze for the window and give it one owner. The
guide: "The deployment process locks write-access to resources getting deployed until
deployment completes. During deployment, changes made to locked resources or related
items can result in errors" (api_meta L4085–L4087). And on concurrency: "You can initiate
multiple deployments, but only one deployment can run at a time… Queued deployments are
listed under Pending Deployments and are not necessarily executed in the order in which
they were submitted. To execute deployments in a particular order, submit them one at a
time after the previous deployment has completed successfully" (api_meta L4117–L4122).
A release plan that assumes submission order is deployment order is wrong.

---

## Flow Definitions in the Package Override the Flow's Own Status

**What happens:** A Flow is deployed with `<status>Active</status>` and arrives inactive,
or an older version becomes the active one. Nothing in the deploy result indicates a
problem.

**When it bites you:** Projects retrieved from an org that still uses `FlowDefinition`
files, and any package assembled by hand from a mix of sources.

**How to avoid it:** Check whether the package contains a `flowDefinitions/` directory
before you promise an activation state. The guide: "If you deploy with flow definitions,
the active version numbers in the flow definitions override the `status` fields in the
flows. For example, the active version number in the flow definition is version 3, and
the latest version of the flow is version 4 with the `status` field as `Active`. After
you deploy your flow, the active version is version 3" (api_meta L73929–L73931). Salesforce
recommends dropping `FlowDefinition` entirely from API 44.0 and using the Flow object's
own `status` (api_meta L73923–L73927), whose values are `Active`, `Draft`, `Obsolete`,
`InvalidDraft`, `UnderReview` — with `Draft` and `Obsolete` both shown in the UI as
"Inactive" (api_meta L68416–L68424). Flow release and activation strategy belongs to the
Flow siblings; this is the deploy-time mechanic only.

---

## Deploy Size Limits Are Per-Transaction and Bite Late

**What happens:** A release grows across a sprint and the final package is rejected at
upload or deploy time, in the window, when the only remaining option is to split it
under pressure.

**When it bites you:** Full-object retrieves, releases carrying static resources or
Experience Cloud assets, and "just deploy the whole `force-app` folder" habits.

**How to avoid it:** Measure the package before the window and split by dependency
boundary, not alphabetically. The App Limits Cheat Sheet, Metadata Limits: "You can deploy
or retrieve up to 10,000 files at once. The maximum size of the deployed or retrieved
.zip file is 39 MB. If the files are uncompressed in an unzipped folder, the size limit
is 600 MB or 629,145,600 bytes" (salesforce_app_limits_cheatsheet L1025–L1036). Change
sets carry the same file count: "Inbound and outbound change sets can have up to 10,000
files of metadata" (L1038). The 39 MB figure is a consequence, not a round number —
Metadata API base-64 encodes after compression and the encoded payload must stay under
the 50 MB SOAP message limit, roughly 22% inflation (api_meta L4030–L4048). A separate
Apex ceiling applies where code rides along: "Maximum number of class and trigger code
units in a deployment of Apex — 7500" (salesforce_app_limits_cheatsheet L395).
