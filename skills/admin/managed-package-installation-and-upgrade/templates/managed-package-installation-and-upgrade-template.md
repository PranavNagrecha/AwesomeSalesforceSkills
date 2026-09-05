# Managed Package Installation And Upgrade — Work Template

Use this template when planning, executing, or auditing a managed package install / upgrade / uninstall.

## Scope

**Skill:** `managed-package-installation-and-upgrade`

**Request summary:**

- [ ] New install
- [ ] Upgrade (patch / minor / major — circle one)
- [ ] Uninstall
- [ ] Post-install configuration only (install already happened)

## Package Identity

| Field | Value |
|---|---|
| Publisher | |
| Package name | |
| 1GP or 2GP | |
| Package ID (`033...` / `0Ho...`) | |
| Version ID (`04t...`) | |
| Version semantic (e.g. `4.2.1`) | |
| AppExchange Security Review status (certified?) | |
| Released or Beta (`MetadataPackageVersion.ReleaseState`) | |
| Install URL | |
| Named owner in our org (person, not team alias) | |
| Licence seats allowed / used / expiry | |
| Push upgrades enabled by publisher? Blocked by us? | |

## Target Environment

| Field | Value |
|---|---|
| Target org alias | |
| Org type (production / full / partial / dev sandbox / scratch) | |
| Existing install? Y/N | |
| Existing version (if upgrading) | |

## Pre-Install Inventory

- [ ] `config/package-inventory.json` regenerated from `sf package installed list --json` + the `PackageLicense` query (`references/metadata-examples.md` §6–7)
- [ ] `python3 scripts/check_managed_package_installation_and_upgrade.py --manifest-dir .` run and findings dispositioned
- [ ] Components the package will add (objects, fields, classes, Flows, Permission Sets) listed from publisher docs
- [ ] Subscriber-added fields on packaged objects audited for API-name collisions
- [ ] Subscriber Apex / Flow references to the publisher's namespace audited (run `check_managed_package_installation_and_upgrade.py`)
- [ ] License SKUs procured for intended audience
- [ ] Named Credential / External Credential pre-staging plan documented (if package requires)
- [ ] Existing org automation on objects the package extends listed and reviewed

## Install Audience Decision

- [ ] Install for Admins Only (default — preferred)
- [ ] Install for All Users (justification: ________)
- [ ] Install for Specific Profiles (justification: ________ — UI install only; the Metadata API and CLI accept only `AdminsOnly` / `AllUsers`)

Record the decision in the artefact, not just here:

- [ ] `securityType` written explicitly in `installedPackages/<ns>.installedPackage-meta.xml`
- [ ] `activateRSS` written explicitly (it is required and defaults to `false`)
- [ ] `--security-type` passed explicitly if the install runs from the CLI
- [ ] Install has its own single-type `package.xml` (it cannot share a manifest)

## Environment Sequence

| Env | Install date/time | Owner | Smoke test pass? | Notes |
|---|---|---|---|---|
| Developer Sandbox | | | | |
| Full Sandbox | | | | |
| Production | | | | |

## Post-Install Configuration Checklist (items InstallHandler cannot do)

- [ ] Named Credential client secrets configured
- [ ] Flow versions activated (if multiple)
- [ ] Permission Set Group built and assigned to canary user(s)
- [ ] Custom Metadata seeded with subscriber-specific data
- [ ] Custom Settings org-default records populated
- [ ] Package seats assigned (`UserPackageLicense` inserts) — separate from permission sets
- [ ] Every packaged Remote Site Setting / CSP Trusted Site confirmed in the intended state
- [ ] Subscriber-owned Permission Set deployed naming each packaged component (no wildcards available)
- [ ] Canary user validates end-to-end workflow
- [ ] Broader rollout (Permission Set Group assigned to full audience)

## Uninstall Plan (always document, even if not removing today)

- [ ] Custom Object data export step (target storage: ________)
- [ ] Subscriber Apex / Flow reference removal step
- [ ] Sandbox uninstall dry-run scheduled
- [ ] Production uninstall window scheduled
- [ ] 48-hour Salesforce export archive plan

## Change-Log Entry

| Field | Value |
|---|---|
| Install date | |
| Approver | |
| Post-install runbook execution evidence (link) | |
| Version confirmed by `sf package installed list` after install | |
| `PackageLicense` seats / expiry after install | |
| `config/package-inventory.json` re-baselined and checker clean | |
| Notes / deviations | |
