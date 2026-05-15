---
name: managed-package-installation-and-upgrade
description: "Use when a subscriber admin is installing, upgrading, or rolling back a managed package (1GP or 2GP) sourced from AppExchange or a private install URL — covers pre-install evaluation, sandbox dry runs, license and dependency checks, the install/upgrade audit trail, post-install configuration the package's InstallHandler cannot perform, and uninstall fallback. NOT for building managed packages as an ISV (use devops/managed-package-development), unlocked-package development (use devops/unlocked-package-development), or AppExchange listing setup."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-15
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

## Core Concepts

### Install URL Anatomy

A package install URL takes one of two shapes:

- **AppExchange managed listing** — clicking "Get It Now" from the listing redirects to a Salesforce-managed install page (`/packaging/installPackage.apexp?p0=04t...`). The listing has passed Security Review.
- **Direct install URL** — `https://login.salesforce.com/packaging/installPackage.apexp?p0=04t...` or `https://test.salesforce.com/packaging/installPackage.apexp?p0=04t...` for sandbox. ISVs share this for beta packages, patch versions, or unlisted distributions. Direct URLs may not have passed Security Review — confirm explicitly with the ISV.

The version-ID suffix is the load-bearing piece. Two URLs that differ only after `?p0=` are two different package versions and may differ materially in metadata or code.

### Install Audience Choice

The install dialog presents three radio buttons:

| Choice | What it does | When to use |
|---|---|---|
| Install for Admins Only | Grants object/field access only to System Administrator profile | Default-safe choice; defer user access to Permission Set assignment later |
| Install for All Users | Grants access via the package's bundled profile settings to every internal user | Only if the package documentation says so AND you've validated profile settings in sandbox |
| Install for Specific Profiles | Per-profile grant configuration | Rare; the matrix is hard to maintain and Permission Set Groups are the modern alternative |

The modern recommendation: Install for Admins Only, then grant feature access via Permission Sets / Permission Set Groups the package ships. Avoid baking access into existing profile settings — it makes future audits and least-privilege reviews painful.

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
| Pull upgrade | Subscriber clicks install URL | Yes — admin explicitly chooses install audience | Major versions, anything with new licensing |
| Push patch | Publisher schedules from packaging org | No — happens during maintenance window | Bug fixes only; cannot change API surface |
| Push major (rare, with subscriber approval) | Publisher with sign-off | Subscriber pre-authorizes | Coordinated major migrations |

If a managed package upgrade appears in a subscriber org without anyone clicking install, it was a push patch.

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

---

## Recommended Workflow

1. **Resolve the version ID.** Confirm the exact `04t...` version, the namespace prefix it claims, and the publisher. Match against AppExchange Security Review status. For direct install URLs, request the Security Review evidence from the ISV in writing.
2. **Inventory the install footprint.** From AppExchange / publisher docs, list the components the package will add: objects, fields, Apex classes, Flows, Permission Sets, Custom Settings, Named Credentials. Match against your org's existing namespace usage to spot collisions.
3. **Plan the install audience.** Default to Install for Admins Only. Identify the Permission Set / Permission Set Group the package will introduce for user access grants.
4. **Install in a Developer Sandbox or scratch org** using the `test.salesforce.com` install URL. Record install duration, components added, and any warnings. Smoke-test existing org code against the new namespace.
5. **Install in a Full Sandbox** that mirrors production data volumes. Re-run the smoke test plus business-process integration tests.
6. **Build the post-install configuration checklist.** Items the publisher's `InstallHandler` cannot do: Named Credential secrets, Flow version activation, Custom Metadata record seeding from subscriber data, Permission Set Group assignment to live users. Sequence them.
7. **Install in production** during a low-traffic window. Execute the post-install checklist immediately. Validate via a canary user before rolling out to broader audience.

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
- [ ] Uninstall path documented even for installs you intend to keep — license expiry or vendor pivot will happen eventually

---

## Salesforce-Specific Gotchas

1. **The 48-hour uninstall data window is a hard limit.** Salesforce emails a CSV export to the uninstalling admin and retains it server-side for 48 hours, then deletes it. There is no recovery path after that.
2. **Push patches require no subscriber consent.** A 1GP / 2GP-managed package patch can land in production on a publisher's schedule. Subscribers cannot defer a patch within the maintenance window. Monitor publisher release notes proactively.
3. **`InstallHandler` runs as the special "Automated Process" user, not the installing admin.** It cannot perform actions that require interactive consent (OAuth approval, secret entry).
4. **Subscriber-org Permission Sets can be created for managed package access surfaces.** Permission Sets that grant access to managed objects/fields are stored in the subscriber org and survive uninstalls (whereas package-bundled Permission Sets are deleted).
5. **API name collisions block install.** If the subscriber org has a Custom Object `Foo__c` and the package introduces `pkg__Foo__c`, the namespace prefix usually prevents collision — but fields without namespace prefixes on packaged objects can collide with subscriber-added fields on the same object. Inventory before install.
6. **Install for All Users grants via profile settings.** The grant is durable across upgrades and cannot be selectively revoked without modifying every affected profile. Permission Set Groups are reversible; profile grants are not, easily.
7. **Beta packages cannot be installed in production.** A beta version ID (`04t...` from a non-released package) only installs into Developer Edition orgs, sandboxes, and scratch orgs. The install URL appears to work but Salesforce blocks the final step.
8. **Spring '25 release notes refresh package dependency rules.** Re-read the current release notes' "Packaging" section before any major-version install to catch new validation gates.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Pre-install readiness assessment | Version ID, audience choice, license posture, footprint inventory, dependency check |
| Sandbox-first install runbook | Step-by-step for Developer Sandbox → Full Sandbox → Production with smoke-test gates |
| Post-install configuration checklist | Items `InstallHandler` cannot do, with owners and sequencing |
| Uninstall plan | Data export step, subscriber-code reference audit, 48-hour recovery awareness |
| Change-log entry | Version, install date, approver, link to post-install runbook execution evidence |

---

## Related Skills

- `devops/managed-package-development` — Publisher-side counterpart: building the package, authoring `InstallHandler`, push upgrades.
- `devops/package-development-strategy` — Selecting between 1GP, 2GP, unlocked, and unmanaged packaging models (publisher choice).
- `admin/permission-set-groups` — The modern subscriber-side access-grant mechanism for package features.
- `security/external-credentials-and-named-credentials` — Pre-staging credentials for packages that need them.
- `admin/sandbox-strategy` — Selecting the right sandbox type for the sandbox-first install runbook.
