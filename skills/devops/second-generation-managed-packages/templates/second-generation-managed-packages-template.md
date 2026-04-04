# 2GP Managed Package — Work Template

Use this template when planning, building, or releasing a second-generation managed package.

---

## Request Summary

**What was asked for:**

<!-- Describe the goal: new package, new version, patch release, 1GP migration, etc. -->

---

## Context Gathered

Answer these before proceeding:

| Question | Answer |
|---|---|
| Dev Hub org type (PBO or Developer Edition?) | |
| Namespace registered and linked to Dev Hub? | |
| Package already created in Dev Hub? (0Ho ID known?) | |
| Is this a new major/minor or a patch release? | |
| Are there dependencies on other packages? | |
| Is AppExchange listing intended? (Security review required?) | |
| Is this a 1GP→2GP migration? | |

---

## Pre-flight Checklist

- [ ] Dev Hub org is the Partner Business Org (PBO), not a Developer Edition org
- [ ] "Enable Unlocked Packages and Second-Generation Managed Packages" is enabled in the Dev Hub
- [ ] Namespace is registered in a Developer Edition org and linked via Namespace Registries
- [ ] Salesforce CLI is installed and authenticated to the Dev Hub (`sf org login web --set-default-dev-hub`)
- [ ] `sfdx-project.json` contains `namespace`, `packageDirectories` with `package` and `versionNumber`, and `packageAliases` with the 0Ho ID

---

## Package Setup (First Time Only)

```bash
# Authenticate Dev Hub
sf org login web --alias devhub --set-default-dev-hub

# Create the managed package (run once; ID is persisted to sfdx-project.json)
sf package create \
  --name "<PACKAGE_NAME>" \
  --package-type Managed \
  --path force-app \
  --target-dev-hub devhub
```

**Package 0Ho ID:** `0Ho_______________`

---

## Development Workflow

```bash
# Create a scratch org for active development
sf org create scratch \
  --definition-file config/project-scratch-def.json \
  --target-dev-hub devhub \
  --alias devorg \
  --duration-days 30

# Push source to scratch org
sf project deploy start --target-org devorg

# Run tests in scratch org
sf apex run test --target-org devorg --wait 10
```

---

## Version Creation

**Release type:** <!-- New minor (major.minor.0.NEXT) / Patch (major.minor.patch.NEXT) -->

**`sfdx-project.json` versionNumber:** `____.____.____.NEXT`

**`sfdx-project.json` ancestorVersion (if patch or flexible):** `____.____.____.____`

```bash
# Create package version — ALWAYS include --code-coverage for any promotable version
sf package version create \
  --package "<PACKAGE_NAME>" \
  --target-dev-hub devhub \
  --code-coverage \
  --wait 30

# Note the resulting 04t subscriber package version ID:
```

**Beta 04t ID:** `04t_______________`

---

## Testing the Beta Version

```bash
# Create a clean test scratch org
sf org create scratch \
  --definition-file config/project-scratch-def.json \
  --target-dev-hub devhub \
  --alias testorg

# Install the beta version
sf package install \
  --package 04t_______________ \
  --target-org testorg \
  --wait 10

# Run post-install validation tests
sf apex run test --target-org testorg --wait 10 --result-format human
```

- [ ] Beta version installs without errors
- [ ] All Apex tests pass in the test scratch org
- [ ] Key functionality verified manually in test scratch org
- [ ] Dependency packages install correctly (if applicable)

---

## Promotion to Managed-Released

```bash
# Promote the tested beta version
sf package version promote \
  --package 04t_______________ \
  --target-dev-hub devhub
```

**Promoted 04t ID:** `04t_______________`

- [ ] Version promoted successfully
- [ ] Version listed as `Released: true` in `sf package version list`

---

## Subscriber Delivery

**Delivery method:** <!-- Manual install URL / Push upgrade / AppExchange listing update -->

```bash
# Option A: Schedule a push upgrade to existing subscribers
sf package push-upgrade schedule \
  --package 04t_______________ \
  --start-time "YYYY-MM-DDTHH:MM:SS" \
  --org-file subscriber-orgs.csv

# Option B: Provide install URL to subscribers
# https://login.salesforce.com/packaging/installPackage.apexp?p0=04t_______________
```

- [ ] Upgrade tested in sandbox orgs before production push
- [ ] Subscribers notified per agreed communication plan
- [ ] Push upgrade results monitored

---

## AppExchange (If Applicable)

- [ ] Security review initiated via ISVforce Partner Portal
- [ ] Listing updated to reference the new promoted version ID
- [ ] App Analytics enabled and verified (if using AppExchange App Analytics)

---

## Post-Release

- [ ] 04t ID and version name committed to release tracking (e.g., CHANGELOG, release tag)
- [ ] `packageAliases` in `sfdx-project.json` updated with the promoted version alias
- [ ] Scratch orgs used for this release deleted or allowed to expire

---

## Notes and Deviations

<!-- Record any decisions that deviate from the standard pattern and why. -->
