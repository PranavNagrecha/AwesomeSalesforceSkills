# Release Plan Template

Use this for any production deployment with meaningful business impact.

Replace every `<angle-bracket>` placeholder. A placeholder left in place is an unmade
decision, not a formatting oversight. Where a row does not apply, write `n/a` and one
clause saying why — a blank row and a deliberate `n/a` look identical a week later.

---

## Release Summary

| Property | Value |
|----------|-------|
| Release name | `<yyyy-mm-dd>-<short-slug>` — dated so two releases never collide in the deploy log |
| Owner | One named person who can stop the release. Not a team, not a channel. |
| Planned window | Start and end in the org's time zone, plus the go/no-go time. The end time is the point at which you back out rather than keep debugging. |
| Deployment method | Change Set / DevOps Center / sf CLI / Package — name the row of the Deployment Method Decision Matrix that chose it |
| Business impact | Who is affected, doing what, and what they see if the release goes wrong. "All users" is not an answer. |

## Deploy Contract

Fill this in before the window, not during it. Every value is chosen; none is defaulted.
Sourced detail is in `references/metadata-examples.md` §3.

| Option | Value | Note |
|---|---|---|
| `checkOnly` | `true` for the validation pass / `false` for the deploy | Two passes, two rows in the deploy log |
| `rollbackOnError` | `true` | Required in production. Set it explicitly in sandbox too, or a partial failure returns `SucceededPartial` and reads as success. |
| `testLevel` | `NoTestRun` \| `RunSpecifiedTests` \| `RunLocalTests` \| `RunAllTestsInOrg` | `NoTestRun` is development-environments-only. State the expected run time next to the choice — it is the window length. |
| `runTests` | Class names, or empty | Only read when `testLevel` is `RunSpecifiedTests`; that level requires 75% coverage per class and trigger, not org-wide |
| `purgeOnDelete` | `false` | Inert in production; deletions land in the Recycle Bin regardless |
| `ignoreWarnings` | `false` unless a specific warning is accepted in writing below | |

| Manifest | Path | Contents |
|---|---|---|
| `package.xml` | `manifest/package.xml` | Components to add or update |
| `destructiveChangesPre.xml` | path or `n/a` | Deleted **before** the additions |
| `destructiveChangesPost.xml` | path or `n/a` | Deleted **after** the additions; processed before tests run |

Checker run and clean: `python3 scripts/check_deployment_manifest.py --manifest-dir manifest/` — exit 1 means an ERROR (malformed manifest, missing `<version>`, destructive manifest with no companion `package.xml`). WARNs such as `manifest includes SharingRules` exit 0 and are justified below.
— paste the date and the finding count, and justify any WARN below.

## Scope

| Item | Included | Notes |
|------|----------|-------|
| Fields / objects / layouts | Yes / No | Name the objects. Flag any Lookup ↔ Master-Detail change — validation cannot cover it and the deploy empties the Recycle Bin of detail records. |
| Flows / approvals / automation | Yes / No | Name each Flow and the state it must be in *after* deploy. Note whether the package carries a `flowDefinitions/` folder. |
| Permission sets / profiles / sharing | Yes / No | If a Profile rides along, say why a permission set could not carry it, and note that a permission absent from the file is not revoked. |
| Connected apps / Named Credentials / endpoints | Yes / No | List every value that differs between environments and who sets it post-deploy. |
| Data load or reconciliation | Yes / No | Record count, job owner, and where the pre-load export lives. |
| Deletions / retirements | Yes / No | Every component in the destructive manifests, and what still references each one. |

Package size check (limits: 10,000 files, ~39 MB compressed):
`<file count>` files, `<size>` MB.

## Deployment Sequence

1. **Pre-deploy steps** — the metadata freeze announcement, the pre-release retrieve that
   becomes your backout artefact (`sf project retrieve start --manifest …`, stored at
   `<path>`), the Recycle Bin export if Master-Detail is involved, and the data export if
   records will change. Each with an owner and an expected duration.
2. **Validation** — `sf project deploy validate` against the *production* target with the
   test level above. Record the validation job id and the date it expires (ten days).
   A validation against staging licenses nothing here.
3. **Metadata deployment** — quick deploy of the validated set. Record the **new** job id
   the quick deploy returns; that is the one to monitor, not the validation id.
4. **Manual activation / config steps** — Flow activation, permission-set assignment,
   layout assignment, environment-specific credential values, custom setting or custom
   metadata rows. One line each, with an owner and a duration. Nothing here happens by
   deploying.
5. **Post-deploy smoke tests** — the specific user actions that prove the release works,
   each with the expected result and who runs it. Plus the deploy verification itself:
   `DeployResult.status` is `Succeeded` (not `SucceededPartial`), `checkOnly` is `false`,
   `runTestsEnabled` matches the test level you asked for, `numberComponentErrors` is 0.

## Risks and Mitigations

| Risk | Mitigation | Owner |
|------|------------|-------|
| Test run overruns the window | Measured run time from the sandbox rehearsal is `<n>` minutes; window budgeted at `<n + margin>` | |
| A component in the manifest does not exist in the target | Validation catches it; validation is scheduled `<n>` days before the window so there is time to fix | |
| A concurrent Setup change collides with the deploy's write lock | Metadata freeze announced `<when>` to `<who>`; single named deploy owner for the window | |
| Add one row per real risk this release carries — not a generic list | | |

## Rollback Plan

Pick **one** backout path per failure scenario, before go-live. There is no reverse
operation for a completed deploy; every path below is a second forward action. Detail and
sourcing are in `references/metadata-examples.md` §6.

| Failure scenario | Backout step | Owner |
|------------------|--------------|-------|
| Deploy fails outright | Nothing to back out — `rollbackOnError: true` means it landed whole or not at all. Diagnose from `details.componentFailures`. | |
| Deploy succeeds, behaviour is wrong | Fastest first: deactivate the Flow / validation rule rather than redeploying. `<name the exact component>` | |
| Deploy succeeds, must be fully reversed | Redeploy the pre-release metadata retrieved in step 1 from `<path>`. Confirm that retrieve exists **before** the window. | |
| A component must be removed again | Second deploy with a destructive manifest. Deleted items go to the Recycle Bin in production; roll-up summary fields do not and cannot be restored. | |
| Records were changed by the release | Data repair from `<export path>` — a separate job with a separate owner. Metadata rollback does not touch it. | |

Decision point: who says "back out", at what time, on what signal.

## Communications

- **Stakeholders notified** — who, by which channel, how far ahead, and again at completion.
- **Support team notified** — who is on call during and after the window, and what the
  known-issue script is if users call.
- **Success criteria declared** — the specific, checkable statements that mean this
  release is done, agreed with the business *before* the window. "It works" is not one.
- **Back-merge** — if this was a production hotfix, who merges it back to source and to
  which lower environments, and by when. Unmerged hotfixes are how source stops being
  the source of truth.
