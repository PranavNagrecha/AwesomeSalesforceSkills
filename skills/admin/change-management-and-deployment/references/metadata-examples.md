# Deployment Artifacts: What an Admin Hands to the Pipeline

This file is the *artefact* half of the skill. It shows the exact files and commands
that carry an admin release, and it maps every command flag back to the `DeployOptions`
field it sets, so a reviewer can check the release without guessing.

Scope note: the mechanics of building an outbound Change Set live in
`devops/change-set-deployment`; the raw `retrieve()`/`deploy()` call shapes live in
`devops/metadata-api-retrieve-deploy`; deletion mechanics live in
`devops/destructive-changes-deployment`. This file covers the admin's deliverable —
the manifest, the test level, the validation, and the proof it worked.

---

## 1. `package.xml` for a typical admin release

A release that adds two fields, a validation rule, a Flow, a permission set, and a
layout. Save as `manifest/package.xml`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case.Escalation_Tier__c</members>
        <members>Case.Escalation_Reviewed_On__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Case.Escalation_Tier_Required</members>
        <name>ValidationRule</name>
    </types>
    <types>
        <members>Case_Escalation_Router</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Case_Escalation_Reviewer</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Case-Case Layout</members>
        <name>Layout</name>
    </types>
    <version>66.0</version>
</Package>
```

**How to read it**

- `<types>` is one metadata type plus its named members; a manifest may hold many
  `<types>` blocks. `<name>` must match a type in the Metadata API WSDL.
  (Metadata API Developer Guide, "Deploying and Retrieving Metadata with the Zip
  File", api_meta L2082–L2110.)
- `<members>` holds the component's `fullName`. Fields are object-qualified:
  `objectName.field`, e.g. `Account.SLA__c` — the guide states this syntax directly
  for `CustomField` (api_meta L2265–L2287) and the same shape for `ListView`
  (`objectName.listViewUniqueName`, api_meta L2318).
- `Layout` members join the object and the layout label with a hyphen — the guide's
  own example is `<members>Idea-Idea Layout</members>` (api_meta L82285–L82289).
  The space inside the layout name is literal; do not URL-encode it.
- `<version>` is the API version used for the deploy or retrieve. The guide states
  "Currently the valid value is 66.0" (api_meta L2106). It is not optional for a
  destructive deploy (see §2).
- **`ValidationRule` does not support the `*` wildcard** in a manifest — the guide says
  so explicitly in the ValidationRule type reference (api_meta L45447–L45449). Neither
  do several other types; check the type's own "Wildcard Support in the Manifest File"
  section before reaching for `*`.
- UNVERIFIED (2026-09-04): the guide shows no `package.xml` sample for
  `ValidationRule`, so the object-qualified `Case.Escalation_Tier_Required` member form
  above is inferred from the `CustomField`/`ListView` `objectName.componentName` pattern
  the guide does document, not quoted from a ValidationRule example.
- Manifest membership, not the zip contents, is what gets deployed: "Metadata API
  references the components listed in the manifest, not the directories in the .zip
  file" (api_meta L2054–L2056). A file present in the folder but absent from
  `package.xml` is a silent no-op.

---

## 2. `destructiveChangesPost.xml` — retiring the old field

Deleting is a *separate manifest* on the same deploy. Three files sit in the same
directory: `package.xml`, `destructiveChangesPost.xml`, and (optionally)
`destructiveChangesPre.xml`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case.Legacy_Escalation_Flag__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

**How to read it**

- Same shape as `package.xml` "except that wildcards aren't supported"
  (api_meta L4615–L4616). A `*` in a destructive manifest is a bug, not a shortcut.
- Naming decides ordering. `destructiveChangesPre.xml` deletes **before** the additions
  in `package.xml`; `destructiveChangesPost.xml` deletes **after** them
  (api_meta L4650–L4655). Post-order is what you want when the thing being deleted is
  still referenced by something the same deploy is updating.
- "Post destructive changes are processed before running any tests" (api_meta L4687) —
  so a test that still references the deleted component fails the whole deploy.
- A destructive deploy still needs a `package.xml` beside it. When there is nothing to
  add, it lists no components but **must** carry the version (api_meta L4630–L4637):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <version>66.0</version>
</Package>
```

- "If you try to delete some components that don't exist in the organization, the rest
  of the deletions are still attempted" (api_meta L4641) — a destructive manifest is not
  all-or-nothing about *missing* members.
- Deleted components land in the Recycle Bin unless `purgeOnDelete` is `true`, and that
  option "only works in Developer Edition or sandbox orgs. It doesn't work in production
  orgs" (api_meta L4232–L4245). Roll-up summary fields are purged either way.

---

## 3. The validate → quick deploy → report sequence

The three-command admin release. Run from the project root, with `manifest/package.xml`
as above.

```bash
# 1. Validation only. Nothing is written to production.
sf project deploy validate \
  --manifest manifest/package.xml \
  --pre-destructive-changes manifest/destructiveChangesPre.xml \
  --post-destructive-changes manifest/destructiveChangesPost.xml \
  --test-level RunLocalTests \
  --target-org production \
  --wait 60

# -> note the job id it returns, e.g. 0Af...ABC. That is the *validation* id.

# 2. Within 10 days, promote the validated set without re-running tests.
sf project deploy quick --job-id 0Af...ABC --target-org production

# -> this returns a NEW job id. Watch that one, not the validation id.

# 3. Read the result.
sf project deploy report --job-id <new id from step 2> --target-org production --json
```

UNVERIFIED (2026-09-04): the `sf` CLI flag spellings above come from the Salesforce CLI
Command Reference, which is not among the extracted PDFs used to ground this skill. The
*semantics* each flag sets are grounded below. If a flag is rejected, run
`sf project deploy validate --help` rather than guessing a synonym.

### What each command is, in `DeployOptions` terms

| Command | Underlying call | `DeployOptions` it sets | Guide |
|---|---|---|---|
| `deploy validate` | `deploy()` | `checkOnly = true` — "perform a test deployment (validation) of components without saving the components in the target org … doesn't commit any changes" | api_meta L4170–L4177 |
| `deploy quick` | `deployRecentValidation()` | none — it takes the validation id and skips tests | api_meta L4854–L4872 |
| `deploy report` | `checkDeployStatus()` | `includeDetails = true` for the `--json` component detail | api_meta L4731–L4733 |
| `--test-level` | either | `testLevel` enum | api_meta L4281–L4322 |
| `--pre/--post-destructive-changes` | `deploy()` | the extra manifest files of §2 | api_meta L4650–L4655 |

### Choosing `--test-level`

The enum has four production-relevant values (`RunRelevantTests` is beta):

| `testLevel` | What runs | Allowed in production? |
|---|---|---|
| `NoTestRun` | No tests | **No.** "This test level applies only to deployments to development environments, such as sandbox, Developer Edition, or trial organizations." It is the *default* for those environments. |
| `RunSpecifiedTests` | Only the classes named in `runTests` | Yes. Coverage rule changes: "Each class and trigger in the deployment package must be covered by the executed tests for a minimum of 75% code coverage … computed for each class and trigger individually". |
| `RunLocalTests` | All org tests except those from installed managed and unlocked packages | Yes — and it is "the default for production deployments that include Apex classes or triggers". |
| `RunAllTestsInOrg` | Everything, including managed-package tests | Yes. Slowest; use when a managed package upgrade is in the same window. |

(All quotations: Metadata API Developer Guide, `deploy()` → `DeployOptions` → `testLevel`,
api_meta L4281–L4322.)

Two behaviours that decide the choice for you:

- **Tests run synchronously and serially** during a deployment (api_meta L4327–L4328).
  The test level *is* the length of your production window.
- **Test level is enforced regardless of what is in the package.** "The test level is
  enforced regardless of the types of components that are present in the deployment
  package" (api_meta L4281–L4282) — so an admin-only, Apex-free release can still be
  told to run all local tests, which is how you catch a validation rule that breaks an
  existing test.

---

## 4. Change Set equivalent — the same release, without a manifest

An admin doing this through Setup produces the same logical artefact. Hand the pipeline
owner (or your own future self) this checklist instead of a `package.xml`.

| Manifest concept | Change Set equivalent |
|---|---|
| `<types>`/`<members>` | Components added in Setup → Outbound Change Sets, plus whatever "Add Dependencies" pulled in |
| `<version>` | Implicit — set by the org, not chooseable |
| `checkOnly = true` | Inbound Change Set → **Validate** |
| `deployRecentValidation()` | Inbound Change Set → **Quick Deploy** |
| `testLevel` | The test-level radio group on the inbound Change Set screen |
| `destructiveChanges*.xml` | No equivalent — see below |

**What a Change Set cannot carry.** Do not assert a list from memory. The guide names
the authority and gives only scattered examples:

- The **Metadata Coverage report** is "the ultimate source of truth for metadata coverage
  across several channels", including change sets; "some metadata types may also be
  unsupported in source tracking, packaging, and change sets" (api_meta L9548–L9558).
  Check a type there before promising it will ride in a Change Set.
- Grounded examples the guide does spell out: Sales Territories components "don't support
  packaging or change sets and aren't supported in CRUD calls" (api_meta L127867), and
  the same for Territory Management 2.0 components (api_meta L133659).
- `ProfileActionOverrides` are "supported in change sets, but you have to add them
  manually" (api_meta L98581) — supported is not the same as auto-detected by
  "Add Dependencies".
- **Deletion.** UNVERIFIED (2026-09-04): the Metadata API guide documents deletion only
  through a destructive-changes manifest on `deploy()` (api_meta L4600–L4610) and
  describes no Change Set deletion path. Treat "the Change Set will remove the old field"
  as unsupported until confirmed in `devops/change-set-deployment`, and plan a manual
  Setup deletion or a CLI destructive deploy for retirements.
- Size ceiling: "Inbound and outbound change sets can have up to 10,000 files of
  metadata" (App Limits Cheat Sheet, Metadata Limits, L1038).

The org-connection, immutability, and upload mechanics are the sibling skill's job — see
`devops/change-set-deployment`.

---

## 5. Verification — proving the release landed

Three checks, in increasing cost. Do at least the first two.

**A. Read the deploy result.**

```bash
sf project deploy report --job-id 0Af... --target-org production --json
```

Read these `DeployResult` fields, not the exit code
(api_meta L7336–L7440):

| Field | What you are checking |
|---|---|
| `status` | One of `Pending`, `InProgress`, `FinalizingDeploy`, `FinalizingDeployFailed`, `Succeeded`, `SucceededPartial`, `Failed`, `Canceling`, `Canceled`. **`SucceededPartial` is not success** — it is what a `rollbackOnError = false` deploy returns when some components failed. |
| `checkOnly` | `true` means you read a validation, not a deployment. The most common false "we deployed it". |
| `numberComponentErrors` / `numberComponentsDeployed` / `numberComponentsTotal` | Whether the whole manifest landed |
| `numberTestErrors` / `numberTestsCompleted` / `numberTestsTotal` | Whether the test level you asked for actually ran |
| `runTestsEnabled` | Whether *any* tests ran. `false` on a production release you believed was test-gated is a finding. |
| `details.componentFailures[]` | The `DeployMessage` array — each has `componentType`, `fullName`, `problem`, `problemType` (`Warning` or `Error`), `lineNumber`, `columnNumber` (api_meta L7509–L7560) |
| `details.runTestResult` | `RunTestsResult`: `numTestsRun`, `numFailures`, `failures[]`, `codeCoverageWarnings[]`, `flowCoverage[]`, `totalTime` (api_meta L7570–L7615) |

**B. Setup check — Deployment Status.**

Setup → Quick Find → **Deployment Status**. It shows in-progress and completed
deployments "in the last 30 days", with a live component chart and a second chart for
Apex tests as they run (api_meta L4090–L4094). This is where a non-CLI admin confirms a
Change Set outcome and where you find a deploy id started by someone else.

**C. SOQL, if the org runs DevOps Center.**

`DevopsEnvDeployment` "represents a record created during the promotion or deployment
process to track deployment actions, status, and associated details within a DevOps
Center pipeline", supports `query()`, and is available in API version 66.0 and later
(Object Reference, DevopsEnvDeployment, object_reference L96437–L96448).

```sql
SELECT Id, Name, DeployStatus, CheckDeployStatus,
       DeployCompletionDate, CheckDeployDate
FROM   DevopsEnvDeployment
WHERE  DeployCompletionDate = LAST_N_DAYS:7
ORDER  BY DeployCompletionDate DESC
```

`CheckDeployStatus` is the validation half (`NEW`, `IN_PROGRESS`, `FINALIZING`,
`SUCCESS`, `ERROR`, `INTERRUPTED`, `CANCELLED`) and `DeployStatus` the deployment half
(object_reference L96496–L96545). Orgs not on DevOps Center have no such object —
fall back to check B.

---

## 6. Rollback reality

State this to stakeholders before the window, not after. Everything here is what the
guide says; nothing here is an inferred workaround.

**Within one deploy, `rollbackOnError` is the whole story.** It "indicates whether any
failure causes a complete rollback (`true`) or not (`false`). If `false`, whatever
actions can be performed without errors are performed, and errors are returned for the
remaining actions. This parameter must be set to `true` if you're deploying to a
production org." (api_meta L4256–L4260.) So a production deploy is atomic *by
requirement*: it either lands whole or leaves nothing behind. That is the only "rollback"
the platform performs for you.

Note the guide contradicts itself on the default: the `DeployOptions` table says "The
default is false" (api_meta L4260) while the `DeployResult` table says "Optional.
Defaults to true" (api_meta L7434–L7437). Set it explicitly and never rely on the
default.

**After a successful deploy there is no undo.** The guide documents `cancelDeploy()` for
a deployment "that hasn't completed yet" — queued or in progress (api_meta L4741–L4752) —
and nothing that reverses a completed one. For API 65.0 and higher, even an in-flight
deploy at status `FinalizingDeploy` "can't be cancelled"; below 65.0, a cancellation
"may fail if the deployment has started committing data" or may succeed *while the data
is also committed* (api_meta L4752–L4755).

So a real rollback plan is one of these, decided before go-live:

| Backout path | What it actually is | Constraint from the guide |
|---|---|---|
| Redeploy the prior version | A second, forward deploy of the retrieved pre-release metadata | You must have retrieved it *before* the release. Nothing captures it for you. |
| Destructive manifest | A second deploy carrying `destructiveChanges.xml` | Deleted items go to the Recycle Bin in production; `purgeOnDelete` "doesn't work in production orgs" (api_meta L4239–L4240) |
| Deactivate, don't delete | Flip `active` on a validation rule, or the Flow's active version | Cheapest and fastest; usually the right first move |
| Cancel mid-flight | `cancelDeploy()` / Setup → Deployment Status → Cancel | Only while `Pending`/`InProgress`, never at `FinalizingDeploy` on API 65.0+ |

**Metadata rollback does not touch data.** If the release ran a Flow, a batch, or a load
that edited records, redeploying the old metadata leaves those edits in place. Plan the
data reversal as a separate, separately-owned step — see `admin/data-import-and-management`.

**One extra hazard for object-model releases.** A Metadata API deployment that includes
Master-Detail relationships "deletes all detail records in the Recycle Bin" in two cases:
adding a new Master-Detail field, and converting a Lookup to Master-Detail. Those detail
records "are permanently deleted from the Recycle Bin and can't be recovered"
(api_meta L4191–L4207). There is no rollback from that at all.
