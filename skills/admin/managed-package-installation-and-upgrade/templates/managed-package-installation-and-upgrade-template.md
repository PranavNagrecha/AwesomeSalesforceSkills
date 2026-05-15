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
| AppExchange Security Review status | |
| Released or Beta | |
| Install URL | |

## Target Environment

| Field | Value |
|---|---|
| Target org alias | |
| Org type (production / full / partial / dev sandbox / scratch) | |
| Existing install? Y/N | |
| Existing version (if upgrading) | |

## Pre-Install Inventory

- [ ] Components the package will add (objects, fields, classes, Flows, Permission Sets) listed from publisher docs
- [ ] Subscriber-added fields on packaged objects audited for API-name collisions
- [ ] Subscriber Apex / Flow references to the publisher's namespace audited (run `check_managed_package_installation_and_upgrade.py`)
- [ ] License SKUs procured for intended audience
- [ ] Named Credential / External Credential pre-staging plan documented (if package requires)
- [ ] Existing org automation on objects the package extends listed and reviewed

## Install Audience Decision

- [ ] Install for Admins Only (default — preferred)
- [ ] Install for All Users (justification: ________)
- [ ] Install for Specific Profiles (justification: ________)

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
| Notes / deviations | |
