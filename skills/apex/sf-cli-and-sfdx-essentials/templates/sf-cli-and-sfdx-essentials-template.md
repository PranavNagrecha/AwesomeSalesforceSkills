# sf CLI and SFDX Essentials — Work Template

Use this template when the user needs sf CLI commands for authentication, project setup, scratch org management, or deploy/retrieve operations.

## Scope

**Skill:** `sf-cli-and-sfdx-essentials`

**Request summary:** (fill in what the user asked for — auth, scratch org, deploy, retrieve, or package.xml)

---

## Context Gathered

Answer these before generating commands:

- **Org type:** `[ ] scratch org` `[ ] sandbox` `[ ] production`
- **Environment:** `[ ] developer machine (interactive)` `[ ] CI/CD pipeline (headless)`
- **Operation:** `[ ] auth` `[ ] project setup` `[ ] create scratch org` `[ ] push/deploy` `[ ] pull/retrieve` `[ ] package.xml`
- **Org alias:** ___________
- **API version:** ___________
- **Test level (for deploy):** `[ ] NoTestRun (sandbox only)` `[ ] RunLocalTests` `[ ] RunSpecifiedTests`

---

## Commands

### Authentication

```bash
# Web flow (developer machine)
sf org login web \
  --alias <alias> \
  --instance-url https://login.salesforce.com   # use test.salesforce.com for sandbox
  # --set-default-dev-hub  (add if this is your Dev Hub)

# JWT (CI/CD pipeline, no browser)
sf org login jwt \
  --client-id <CONSUMER_KEY> \
  --jwt-key-file <path/to/server.key> \
  --username <deploying-user@org.com> \
  --alias <alias> \
  --instance-url https://login.salesforce.com
```

### Project Setup (if starting fresh)

```bash
sf project generate --name <ProjectName>
# Creates: sfdx-project.json, force-app/ directory structure
```

### Scratch Org

```bash
# Create
sf org create scratch \
  --edition developer \
  --duration-days 7 \
  --alias <alias> \
  --set-default

# Push source (uses source tracking — delta only)
sf project deploy start

# Pull changes from scratch org
sf project retrieve start

# Open in browser
sf org open --target-org <alias>

# Delete when done
sf org delete scratch --target-org <alias> --no-prompt
```

### Deploy to Sandbox / Production

```bash
# From source directory
sf project deploy start \
  --source-dir force-app \
  --target-org <alias> \
  --test-level RunLocalTests

# From package.xml manifest
sf project deploy start \
  --manifest package.xml \
  --target-org <alias> \
  --test-level RunLocalTests

# Validate only (no deployment — use for production pre-check)
sf project deploy validate \
  --manifest package.xml \
  --target-org <alias> \
  --test-level RunLocalTests

# Quick deploy after successful validation
sf project deploy quick \
  --job-id <ID-from-validate-output> \
  --target-org <alias>
```

### Retrieve from Sandbox / Production

```bash
# To source format (default — ready for git)
sf project retrieve start \
  --manifest package.xml \
  --target-org <alias>

# To mdapi format (for inspection only — breaks source tracking)
sf project retrieve start \
  --manifest package.xml \
  --target-org <alias> \
  --target-metadata-dir retrieved/
```

---

## package.xml Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Custom objects — use * for all, or list by name -->
    <types>
        <members>*</members>
        <name>CustomObject</name>
    </types>
    <!-- Standard objects — MUST list by name (wildcard not supported) -->
    <types>
        <members>Account</members>
        <members>Contact</members>
        <members>Opportunity</members>
        <name>CustomObject</name>
    </types>
    <!-- Apex Classes -->
    <types>
        <members>*</members>
        <name>ApexClass</name>
    </types>
    <!-- Flows -->
    <types>
        <members>*</members>
        <name>Flow</name>
    </types>
    <!-- API version — match your org's current version -->
    <version>62.0</version>
</Package>
```

---

## Checklist Before Delivering

- [ ] Dev Hub is enabled in the target production org (for scratch org tasks)
- [ ] Org alias is set and verified with `sf org display --target-org <alias>`
- [ ] package.xml version matches the org's API version
- [ ] Standard objects are listed by name (not wildcard) in package.xml
- [ ] Private key files excluded from version control (check `.gitignore`)
- [ ] `--test-level RunLocalTests` or higher used for production deploys
- [ ] JWT Connected App has the deploying user's profile pre-authorized

---

## Notes

(Record any deviations from standard patterns and the reason)
