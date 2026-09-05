---
name: managed-package-installation-and-upgrade
description: "Use when a subscriber admin is installing, upgrading, or rolling back a managed package (1GP or 2GP) sourced from AppExchange or a private install URL — covers pre-install evaluation, sandbox dry runs, license and dependency checks, the install/upgrade audit trail, post-install configuration the package's InstallHandler cannot perform, and uninstall fallback. NOT for building managed packages as an ISV (use devops/managed-package-development), unlocked-package development (use devops/unlocked-package-development), or AppExchange listing setup. Trigger keywords: InstalledPackage, installedPackages, securityType, activateRSS, sf package install, sf package installed list, PackageLicense, UserPackageLicense, AllowedLicenses, UsedLicenses, push upgrade, PackageSubscriber, namespace prefix, 04t, certified managed package limits."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Reliability
triggers:
  - "how do I safely install a managed package in production"
  - "AppExchange package upgrade failed in production what went wrong"
  - "what should I check before installing an AppExchange package"
  - "post-install configuration steps for managed package"
  - "uninstall managed package rollback after failed install"
  - "package install limit exceeded during upgrade"
  - "managed package upgrade overwrote my customizations"
  - "installedPackage metadata deploy to install a managed package"
  - "sf package install security type AdminsOnly or AllUsers"
  - "package license expired users cannot access installed package"
  - "query PackageLicense AllowedLicenses UsedLicenses for seat reconciliation"
  - "block push upgrades from a package publisher"
  - "managed package trigger consuming my SOQL governor limit"
  - "package remote site settings inactive after install so callouts fail"
  - "how do I uninstall a first-generation managed package"
  - "package license seats assigned but users cannot access packaged objects"
tags:
  - managed-package
  - appexchange
  - subscriber
  - install
  - upgrade
  - uninstall
  - subscriber-admin
inputs:
  - "package install URL or AppExchange listing"
  - "target org type (production, full sandbox, partial sandbox, developer sandbox, scratch org)"
  - "package metadata footprint (objects, fields, Apex classes, Flows, Permission Sets the package will add)"
  - "user license types in the target org and any per-package license SKUs required"
outputs:
  - "pre-install readiness assessment with go/no-go recommendation"
  - "ordered install / upgrade runbook (sandbox-first, production-second) with rollback step"
  - "post-install configuration checklist for items the InstallHandler cannot complete"
  - "uninstall plan with data-export step for objects the package introduced"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Managed Package Installation and Upgrade

Activate when a Salesforce admin is responsible for installing a third-party managed package, upgrading an installed package version, or unwinding a failed install. The skill produces a readiness assessment, an environment-by-environment install runbook, a post-install configuration checklist, and an uninstall fallback. Publisher-side concerns (building the package, authoring `InstallHandler`, push-upgrade scheduling) belong to `devops/managed-package-development` and are out of scope here.

---

## Before Starting

Gather this context before touching any install URL:

- **Package identity.** Confirm the package ID (`033...` for 1GP, `0Ho...` for 2GP package) and the specific version ID (`04t...`) you intend to install. Different `04t` IDs mean different code — never assume "latest stable" without resolving the version.
- **Target environment.** Production, full sandbox, partial-copy sandbox, developer sandbox, or scratch org? Installation behavior, IP-protection visibility, and rollback options differ. Production gets the install last, never first.
- **License posture.** Does the package require per-user license SKUs? How many users in the target org need licenses, and have those been procured? An install can succeed while leaving 90% of users unable to use the feature because licenses are missing.
- **Existing footprint.** Is the package already installed? At what version? If upgrading, what's the version delta — patch, minor, or major? Patch versions may push without consent on the next maintenance window; majors will not.
- **Subscriber org customizations on the package surface.** If users have already configured the package (custom Permission Set assignments, Custom Metadata records, Flow versions of unmanaged variants), the upgrade may overwrite or invalidate them.

---

## Questions to Ask Before Configuring

Ask these before the install URL is opened or the pipeline stage is written. Each one maps to a
failure that is cheap now and expensive after the package is in production.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which exact `04t` version, and is it Released or Beta?" | The version ID is the only unambiguous identifier; release state is queryable only in the publisher's org, from `MetadataPackageVersion.ReleaseState` | A pinned version in `config/package-inventory.json` instead of "latest" |
| "Is this package certified — did it pass AppExchange security review?" | Certified packages get their own per-transaction governor limits; non-certified packages spend yours, and only certified/unlocked packages can be push-upgraded | A limits impact assessment for the objects the package shares with your automation |
| "Who is the named owner of this package in our org, and who pays for the seats?" | Licences expire and seats run out independently of object permissions; an unowned package is one nobody renews | An owner row in the inventory and a renewal date on someone's calendar |
| "How many users need a seat, versus how many need the permission set?" | `PackageLicense.AllowedLicenses` is a hard ceiling; a user can hold every object permission and still be locked out with no seat | The seat count to procure, and the reconciliation query to run after install |
| "Does the package ship Remote Site Settings, CSP Trusted Sites, or Named Credentials?" | `activateRSS` defaults to `false`, and secrets cannot be set by the publisher's install script | The pre-staging steps that must precede the install, and the endpoints to review |
| "Will the install be clicked in Setup, deployed as metadata, or run from the CLI?" | The three paths differ in what they support and in what they default to — the Metadata API defaults `securityType` to `AllUsers`, the CLI defaults it to `AdminsOnly` | An explicit audience decision written into the artefact, not inherited from a default |
| "What subscriber code, Flows, and validation rules reference this namespace today?" | Those references break on a rename in an upgrade and block an uninstall outright | The reference list the checker produces, refreshed before every version change |

What a proper configuration adds over just clicking Install: the audience and the remote-site state
are explicit rather than defaulted, seats are reconciled against the permission set rather than
assumed, and the version, owner, licence expiry, and namespace references are recorded in an
artefact the next upgrade can be planned from.

---

## Core Concepts

### Install URL Anatomy

A package install URL takes one of two shapes:

- **AppExchange managed listing** — clicking "Get It Now" from the listing redirects to a Salesforce-managed install page (`/packaging/installPackage.apexp?p0=04t...`). The listing has passed Security Review.
- **Direct install URL** — `https://login.salesforce.com/packaging/installPackage.apexp?p0=04t...` or `https://test.salesforce.com/packaging/installPackage.apexp?p0=04t...` for sandbox. ISVs share this for beta packages, patch versions, or unlisted distributions. Direct URLs may not have passed Security Review — confirm explicitly with the ISV.

The version-ID suffix is the load-bearing piece. Two URLs that differ only after `?p0=` are two different package versions and may differ materially in metadata or code.

### The Three Install Paths

| Path | Covers | Audience control | Where it is grounded |
|---|---|---|---|
| Setup UI — Installed Packages | 1GP and 2GP | Three radio buttons, chosen at click time | The install page itself |
| Metadata API — `InstalledPackage` | **1GP only** | `securityType`, **defaults to `AllUsers`** when omitted | `api_meta.txt` L81389–81451 |
| CLI — `sf package install` | 1GP, 2GP, unlocked | `--security-type`, **defaults to `AdminsOnly`** | `sf package install --help`, `@salesforce/cli/2.149.9` |

The Metadata API type is explicit that it "represents a first-generation managed package" and that
2GP and unlocked packages install through the CLI instead. Two constraints follow the metadata
path: an `InstalledPackage` deployment cannot contain any other metadata type, and a single
deployment installs at most 20 of them. Uninstall is asymmetric too — `sf package uninstall` is
documented as a second-generation command, and 1GP removal goes through Setup.

Deployable XML, package.xml, and the full CLI flag table are in `references/metadata-examples.md`.

### Install Audience Choice

The install dialog presents three radio buttons:

| Choice | What it does | When to use |
|---|---|---|
| Install for Admins Only | Grants object/field access only to System Administrator profile | Default-safe choice; defer user access to Permission Set assignment later |
| Install for All Users | Grants access via the package's bundled profile settings to every internal user | Only if the package documentation says so AND you've validated profile settings in sandbox |
| Install for Specific Profiles | Per-profile grant configuration | Rare; the matrix is hard to maintain and Permission Set Groups are the modern alternative |

The modern recommendation: Install for Admins Only, then grant feature access via Permission Sets / Permission Set Groups the package ships. Avoid baking access into existing profile settings — it makes future audits and least-privilege reviews painful.

Only the first two choices exist outside the UI: the Metadata API `securityType` field and the CLI
`--security-type` flag both accept exactly `AdminsOnly` and `AllUsers`. A scripted install therefore
cannot express "Install for Specific Profiles" — plan that grant as a separate Permission Set deploy.

### IP Protection Visibility Rules

In a managed-1GP-installed subscriber org, the following are invisible or uneditable:

- Apex class and trigger source code (only public method signatures are visible)
- Flow XML (the Flow Builder canvas is read-only; "View" not "Edit")
- Custom Object and Field metadata for non-Global components (renames blocked; only Activate/Deactivate for some types)

Subscribers can:

- Read public Apex method signatures via the API and call them from their own code
- Override certain components if the publisher marked them as overridable in `package.xml`
- Add their own fields to managed objects (these are non-managed and survive uninstalls)

### Post-Install Configuration Gap

The publisher's `InstallHandler` Apex class runs during install with subscriber-org context but cannot:

- Set Named Credential client secrets (the secret value is not known at install time)
- Activate Flow versions if multiple managed versions exist (subscriber must pick which one is active)
- Assign Permission Sets to specific user records (the subscriber's user list is unknown at package build time)
- Insert subscriber-specific configuration data (Custom Settings org-default records, Custom Metadata records that depend on subscriber data, External Credential principals)

These items live in the post-install checklist the publisher's documentation should provide. If it doesn't, write your own from the package's `package.xml` (visible after install via Setup → Installed Packages → View Components).

### Upgrade Semantics

Upgrades preserve subscriber data and unmanaged additions, but:

- A managed component renamed by the publisher loses its old name (downstream references in subscriber-written Apex break at compile time)
- A managed component deleted by the publisher becomes a "missing component" error if subscriber code references it
- A new required field added by the publisher must have a default or a backfill plan, or the upgrade fails on a row count check
- Flow upgrades activate the new managed version if it has the same DeveloperName; subscribers cannot keep "v1 active" once "v2" is pushed

### Push Upgrades vs. Pull Upgrades

| Mechanism | Initiated by | Subscriber consent | Use case |
|---|---|---|---|
| Pull upgrade | Subscriber clicks install URL, deploys `InstalledPackage`, or runs `sf package install` | Yes — the audience choice is made at install time | Major versions, anything with new licensing |
| Push upgrade | Publisher creates a `PackagePushRequest` with a `ScheduledStartTime` | No click, but blockable — see below | Publisher-driven fixes and coordinated migrations |

If a package version changes in a subscriber org without anyone installing it, it was a push.

Push is not unconditional. It is available only to 1GP and 2GP managed packages that have passed
AppExchange security review, and to unlocked packages, where it is on by default. The subscriber
org can refuse: the publisher's `PackageSubscriber` record carries `HasRestrictionEnabled`, which
"indicates whether the subscriber org has blocked push upgrades," and a `CustomUpgradeType` value
of `BlockedBySubscriber`. Both default to off, so the usual state is "not blocked," not "cannot
block." Scheduling is also approximate — Salesforce documents that a push may start hours after the
requested time, and orgs whose `OrgStatus` is `Inactive` never receive one
(`references/gotchas.md`, Gotcha 2).

### Licences Are Not Permissions

A package licence and an object permission are separate grants, and an install produces neither
automatically. `PackageLicense` holds one row per licensed managed package with `AllowedLicenses`,
`UsedLicenses`, `ExpirationDate`, and a `Status` restricted to `Active`, `Expired`, `Free`, `Trial`;
it is read-only through the API. `UserPackageLicense` holds the per-user seat and does support
`create()` / `delete()`, so seat assignment is DML. A user with every field permission and no seat
is locked out, and the platform reports it as the DML status code `LICENSE_LIMIT_EXCEEDED` only
when you have already run out. The reconciliation queries and an Apex assigner are in
`references/metadata-examples.md` §6.

### Governor Limits Change Shape After Install

A **certified** managed package — one that passed AppExchange security review — gets its own set of
per-transaction limits: its Apex has its own 150 DML statements and its own 100 synchronous SOQL
queries on top of yours. A **non-certified** package gets no separate budget and spends your org's.
Four limits are never duplicated and count for the whole transaction no matter how many packages
run in it: total heap size, maximum CPU time, maximum transaction execution time, and the maximum
number of unique namespaces. Cumulative cross-namespace ceilings are 11× the per-namespace limit
(`references/gotchas.md`, Gotcha 12). Certification status therefore belongs in the pre-install
assessment, not just in the security conversation.

---

## Common Patterns

### Pattern: Sandbox-First Install Runbook

**When to use:** Any new package installation, any upgrade of a package that touches business-critical data, any package new to your org governance.

**How it works:**

1. Install in a Developer Sandbox (or scratch org) first. Note the install duration, components added (Setup → Installed Packages → View Components), and any warnings.
2. Run a smoke test of the org's existing custom code that references the package's namespace or public methods. Compile-time breaks surface here.
3. Install in a Full Sandbox refreshed from production. This catches data-volume-dependent issues the Developer Sandbox misses.
4. Install in production during a low-traffic window. The runbook for production is the sandbox runbook with the install URL switched from `test.salesforce.com` to `login.salesforce.com`.

**Why not the alternative:** "Install directly in production because it's just a managed package" is the most common cause of post-install support tickets. Even a Security-Reviewed package can interact badly with org-specific automation.

### Pattern: Install for Admins Only + Permission Set Group Grant

**When to use:** Default for every install. Reverse only if the package documentation explicitly says otherwise and you've validated.

**How it works:**

1. At install time, choose Install for Admins Only.
2. After install, find the Permission Sets and Permission Set Groups the package created (Setup → Permission Sets, filter by namespace).
3. Build a subscriber-org Permission Set Group that combines: a relevant package Permission Set + your org's role-specific Permission Sets.
4. Assign the Permission Set Group to users via Setup → Permission Set Groups → Manage Assignments, or via SOQL-driven assignment if user count is high.

**Why not the alternative:** Install for All Users grants access via the package's profile settings, which bypass your org's principle-of-least-privilege model and are hard to revoke selectively.

### Pattern: Uninstall with Data Export

**When to use:** A package is being removed because it's no longer licensed, the vendor pivoted, or a competing product replaced it.

**How it works:**

1. Export package-introduced data first. Setup → Installed Packages → click the package name → View Components. Identify all Custom Objects added by the package (rows with the package namespace). For each, run a Data Export via Data Loader or Bulk API — these records will be permanently deleted when the package is uninstalled.
2. Identify subscriber-written code that references the package. Search the org's Apex, Flow, and Validation Rules for the package namespace. Each reference must be removed or refactored before uninstall, or the uninstall fails with "component is referenced."
3. Run uninstall in sandbox first. Setup → Installed Packages → Uninstall. Salesforce produces an export of package data as a CSV that's emailed to the running admin and retained for 48 hours. This is the only post-uninstall recovery path.
4. Verify org integrity in sandbox — broken page layouts, missing Flow elements, failed scheduled jobs.
5. Repeat in production during a low-traffic window. The 48-hour export retention is your only undo button.

**Why not the alternative:** "Just uninstall" loses any data in package-introduced Custom Objects irrecoverably after the 48-hour window.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New package, never installed in any org | Developer sandbox → Full sandbox → Production, with smoke test at each step | Catches integration and data-volume issues progressively |
| Patch upgrade (`X.Y.Z` → `X.Y.Z+1`) | Sandbox install if possible; production proceeds even if sandbox not run | Patches are bug-fix-only and limited in metadata surface; push patches may not give sandbox window |
| Minor upgrade (`X.Y` → `X.Y+1`) | Mandatory sandbox-first with smoke test | New features may add required fields or new Permission Sets to manage |
| Major upgrade (`X` → `X+1`) | Mandatory sandbox-first + UAT + release-train slot | Likely breaking changes; treat as a project, not a maintenance task |
| Package targets a feature you don't license yet | Do not install until license SKUs are confirmed | Installing without licenses leaves users locked out and creates support-ticket noise |
| Package needs Named Credential secrets at install time | Pre-create the External Credential principal in target org before install | InstallHandler cannot set client secrets; UI step must precede or follow install per docs |
| Removing a package | Export package object data, audit subscriber references, sandbox-uninstall first | 48-hour data recovery window is non-negotiable; subscriber code references block the uninstall |
| Package is not AppExchange-certified | Model its Apex against your own governor budget before install, and expect no push-upgrade option | Non-certified namespaces get no separate per-transaction limits and cannot be push-upgraded |
| Install must run from a pipeline, not a click | Source-track `installedPackages/<ns>.installedPackage-meta.xml` with `securityType` and `activateRSS` explicit, in its own single-type manifest | The metadata path defaults to `AllUsers` and inactive remote sites; the type cannot share a manifest |
| Package is 2GP or unlocked | `sf package install`; do not reach for `InstalledPackage` | The metadata type represents first-generation managed packages only |
| Users have every permission and still cannot use the feature | Check `PackageLicense.Status`, `ExpirationDate`, and `AllowedLicenses` vs `UsedLicenses` before touching permissions again | Seats and permissions are independent grants; an install assigns neither |

---

## Recommended Workflow

1. **Establish the baseline.** Run `sf package installed list --target-org <env> --json` for every environment and the `PackageLicense` query in `references/metadata-examples.md` §6. Write the result into `config/package-inventory.json` in the shape shown in §7 — namespace, version per environment, owner, licence counts, expiry, certification status.
2. **Lint the baseline before planning anything.** `python3 scripts/check_managed_package_installation_and_upgrade.py --manifest-dir .` reports expired or over-allocated licences, version drift between environments, packages with no owner, `installedPackage` files with an implicit `securityType`, permission sets referencing a namespace that is not in the inventory, and the subscriber code that references each namespace. Resolve the drift and ownership findings before writing the runbook, not after.
3. **Resolve the version and its properties.** Pin the exact `04t`, confirm Released rather than Beta, and confirm AppExchange certification — certification decides both the governor-limit shape (`references/gotchas.md`, Gotcha 12) and whether push upgrades are possible at all. Record both in the inventory.
4. **Author the install artefacts.** Write `installedPackages/<ns>.installedPackage-meta.xml` with `versionNumber`, `securityType`, and `activateRSS` all explicit, and its own single-type `package.xml`, from `references/metadata-examples.md` §2–3. Write the subscriber-owned Permission Set from §5 as a **separate** deploy — the install manifest cannot carry it.
5. **Dry-run, then install, sandbox first.** `sf project deploy start --source-dir force-app/main/default/installedPackages --target-org <sandbox> --dry-run`, then the real deploy. Run the org's existing Apex tests against the new namespace; record the install duration in a full sandbox that mirrors production volumes.
6. **Execute the post-install checklist.** The items the publisher's install script cannot do — Named Credential and External Credential secrets, Flow version activation, Custom Metadata seeded from subscriber data, seat assignment via `UserPackageLicense`, Permission Set Group assignment. Sequence them in `templates/managed-package-installation-and-upgrade-template.md`.
7. **Verify, then re-baseline.** Run the three checks in `references/metadata-examples.md` §8: the version that actually landed, `PackageLicense` seats and expiry, and a canary user exercising the packaged tab end to end. Regenerate `config/package-inventory.json` and re-run the checker so the next upgrade starts from truth.

---

## Review Checklist

- [ ] Version ID (`04t...`) resolved and matched to AppExchange Security Review status
- [ ] Installation footprint inventoried (objects, fields, classes, Flows, Permission Sets)
- [ ] Install audience set to Install for Admins Only (or explicit justification recorded)
- [ ] Developer Sandbox install completed with smoke test
- [ ] Full Sandbox install completed with business-process integration test
- [ ] License SKUs confirmed for all intended user audience
- [ ] Post-install configuration checklist authored, sequenced, and assigned
- [ ] Named Credential / External Credential secrets pre-staged or post-stage path documented
- [ ] Production install runbook scheduled in a low-traffic window
- [ ] Canary user / business validation gate identified before broader rollout
- [ ] Change-log entry written (version, date, approver, post-install runbook reference)
- [ ] `config/package-inventory.json` regenerated and `scripts/check_managed_package_installation_and_upgrade.py` clean
- [ ] `securityType` and `activateRSS` both explicit in every `installedPackage` file (neither left to its default)
- [ ] Certification status recorded — it decides both the governor-limit shape and whether push upgrades are possible
- [ ] Seats reconciled: `PackageLicense.UsedLicenses` matches the intended audience, `ExpirationDate` is beyond the next renewal
- [ ] Uninstall path documented even for installs you intend to keep — license expiry or vendor pivot will happen eventually

---

## Salesforce-Specific Gotchas

1. **The 48-hour uninstall data window is a hard limit.** Salesforce emails a CSV export to the uninstalling admin and retains it server-side for 48 hours, then deletes it. There is no recovery path after that. UNVERIFIED (2026-09-05): the 48-hour figure could not be re-confirmed against the doc extracts available here — see `references/gotchas.md`, Gotcha 1, and never let a runbook depend on it in place of a durable pre-export.
2. **Push upgrades need no subscriber click, and blocking them is opt-in.** `PackageSubscriber.HasRestrictionEnabled` defaults to `false`, so the default posture is "not blocked." Ask each publisher whether push is enabled for your org.
3. **The publisher's install script runs as the package's own system user.** Records it creates are attributed to that user, not to the installing admin — `InstallContext.installerId()` is the only handle on who ran the install. It cannot access session IDs and can only make callouts asynchronously, after the install commits.
4. **Subscriber-org Permission Sets can be created for managed package access surfaces.** Permission Sets that grant access to managed objects/fields are stored in the subscriber org and survive uninstalls (whereas package-bundled Permission Sets are deleted).
5. **API name collisions block install.** If the subscriber org has a Custom Object `Foo__c` and the package introduces `pkg__Foo__c`, the namespace prefix usually prevents collision — but fields without namespace prefixes on packaged objects can collide with subscriber-added fields on the same object. Inventory before install.
6. **Install for All Users grants via profile settings.** The grant is durable across upgrades and cannot be selectively revoked without modifying every affected profile. Permission Set Groups are reversible; profile grants are not, easily.
7. **Beta packages cannot be installed in production.** A beta version ID (`04t...` from a non-released package) only installs into Developer Edition orgs, sandboxes, and scratch orgs. The install URL appears to work but Salesforce blocks the final step. UNVERIFIED (2026-09-05): the block itself is not stated in the doc extracts available here; what is grounded is that `MetadataPackageVersion.ReleaseState` is `Beta` or `Released`, visible only in the publisher org, and that push upgrades refuse a beta version — see `references/gotchas.md`, Gotcha 4.
8. **`activateRSS` is required and defaults to `false`.** Deploy an `InstalledPackage` without it and every Remote Site Setting and CSP Trusted Site the package ships arrives inactive; the package's callouts fail on first real use, long after the install looked clean.
9. **A failed install script aborts the install; a failed uninstall script does not stop the uninstall.** In both cases the error email goes to the publisher's Notify on Apex Error address, not to you.
10. **Grants on packaged components cannot use wildcards.** Each packaged object and field must be enumerated by name, prefixed with the namespace and two underscores, in the Permission Set XML.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pre-install readiness assessment | Version ID, audience choice, license posture, footprint inventory, dependency check |
| Sandbox-first install runbook | Step-by-step for Developer Sandbox → Full Sandbox → Production with smoke-test gates |
| Post-install configuration checklist | Items `InstallHandler` cannot do, with owners and sequencing |
| Uninstall plan | Data export step, subscriber-code reference audit, 48-hour recovery awareness |
| Change-log entry | Version, install date, approver, link to post-install runbook execution evidence |
| `config/package-inventory.json` | Machine-readable state per package: namespace, version per environment, owner, seats allowed/used, licence status and expiry, certification, push-block posture, subscriber code references — the input the checker lints and the baseline the next upgrade is planned from |
| `installedPackages/<ns>.installedPackage-meta.xml` + single-type `package.xml` | The install itself as reviewable, diffable source rather than a click |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the deployable `installedPackage` XML, the single-type `package.xml`, the `sf package install` / `installed list` / `uninstall` commands with grounded flag defaults, the subscriber-owned Permission Set for packaged components, the `PackageLicense` / `UserPackageLicense` reconciliation SOQL and Apex, the `config/package-inventory.json` artefact, and the three post-install verification checks |
| `references/gotchas.md` | The install succeeded and something is wrong anyway — callouts failing, users locked out with full permissions, a version that changed on its own, your own Apex suddenly hitting governor limits, or an uninstall that left cleanup undone |
| `references/examples.md` | Planning a first install, diagnosing a push upgrade that broke subscriber Apex, or retiring a package with data in it — three worked runbooks plus the inventory row each one produces |
| `references/well-architected.md` | Justifying the sandbox-depth or install-audience tradeoff to a reviewer, or locating the official source behind any claim in this skill |
| `references/llm-anti-patterns.md` | Reviewing install or uninstall guidance an AI assistant produced, especially anything that says "the InstallHandler will handle it" or "Salesforce keeps a backup for 48 hours" |
| `templates/managed-package-installation-and-upgrade-template.md` | Running workflow steps 1 and 6 — the package identity, footprint inventory, environment sequence, and post-install checklist |
| `scripts/check_managed_package_installation_and_upgrade.py` | Workflow step 2 and again at step 7, and before every deploy that touches `installedPackages/` or a permission set naming a packaged component |

---

## Related Skills

- `devops/managed-package-development` — Publisher-side counterpart: building the package, authoring `InstallHandler`, push upgrades.
- `devops/package-development-strategy` — Selecting between 1GP, 2GP, unlocked, and unmanaged packaging models (publisher choice).
- `admin/permission-set-group-composition` — The modern subscriber-side access-grant mechanism for package features.
- `integration/named-credentials-setup` — Pre-staging credentials for packages that need them.
- `admin/sandbox-strategy` — Selecting the right sandbox type for the sandbox-first install runbook.
- `devops/second-generation-managed-packages` — why 2GP and unlocked packages install and uninstall through `sf package install` / `sf package uninstall` rather than the `InstalledPackage` metadata type.
- `devops/packaging-dependency-graph` — resolving install order when a package depends on other packages.
