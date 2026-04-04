---
name: scratch-org-management
description: "Use this skill when designing, configuring, or troubleshooting scratch orgs: definition file structure, edition selection, allocation limits, Org Shape, CI automation via ScratchOrgInfo, and lifecycle management from the Dev Hub. NOT for SFDX CLI basics (use sf-cli-and-sfdx-essentials), sandbox management, or production org administration."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Scalability
tags:
  - scratch-org
  - dev-hub
  - sfdx
  - ci-cd
  - org-shape
  - devops
triggers:
  - "my scratch org create command is failing with an allocation or limit error"
  - "I need to set up a scratch org definition file that mirrors production features and settings"
  - "how do I automate scratch org creation and teardown in a CI pipeline"
  - "team members are running out of scratch orgs and builds are failing because active org limit is hit"
  - "I want to use Org Shape so my scratch org matches the features enabled in our production org"
  - "what edition should I use in my scratch org definition file for package development"
inputs:
  - "Dev Hub edition (Developer, Enterprise, Performance, Unlimited, Partner)"
  - "Target org edition for development (Developer, Enterprise, Group, Professional, Partner Developer, Partner Enterprise)"
  - "Feature flags and settings needed in the scratch org (e.g., API, Communities, LightningServiceConsole)"
  - "Source org ID if using Org Shape"
  - "Desired scratch org lifespan in days (1–30)"
  - "CI platform context (GitHub Actions, Jenkins, etc.) if automating lifecycle"
outputs:
  - "Compliant project-scratch-def.json definition file"
  - "sf CLI commands for org creation, deletion, and audit"
  - "ScratchOrgInfo SOQL query for Dev Hub automation"
  - "CI pipeline snippet for scratch org lifecycle"
  - "Diagnosis and remediation steps for allocation or provisioning failures"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Scratch Org Management

This skill activates when you need to design the shape of a scratch org (definition file), manage allocation limits across a team or CI system, troubleshoot provisioning failures, or automate scratch org lifecycle via the Dev Hub API. It assumes Dev Hub is already enabled; for basic CLI commands and first-time setup see `sf-cli-and-sfdx-essentials`.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What is the Dev Hub edition?** The edition determines hard daily and active limits (see Core Concepts). Hitting the active limit is the most common cause of `org create scratch` failures.
- **What features does the target environment need?** Every feature the org under test depends on must be declared in the definition file — or provisioned via Org Shape — or tests will behave differently than in a real org.
- **Is this for a single developer, a team, or CI?** Teams and CI pipelines exhaust limits faster and require a discipline around explicit org deletion and alias conventions.

---

## Core Concepts

### 1. The Scratch Org Definition File

The definition file (`config/project-scratch-def.json`) is a JSON blueprint that tells Dev Hub exactly what kind of scratch org to provision. It is not part of `sfdx-project.json`; it is a standalone file in the `config/` directory by convention.

**Minimal required field:**

```json
{
  "edition": "Developer"
}
```

**Full annotated example:**

```json
{
  "edition": "Enterprise",
  "description": "Feature branch — Communities + API",
  "duration": 7,
  "hasSampleData": false,
  "language": "en_US",
  "country": "US",
  "features": ["Communities", "LightningServiceConsole"],
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    },
    "mobileSettings": {
      "enableS1EncryptedStoragePref2": false
    }
  }
}
```

Key fields:

| Field | Required | Notes |
|---|---|---|
| `edition` | Yes | Controls base feature set — see Edition Types below |
| `duration` | No | Days until expiry; default 7, max 30 |
| `features` | No | Array of feature strings; additive on top of edition |
| `settings` | No | Metadata API settings objects; most comprehensive config option |
| `hasSampleData` | No | Default `false`; `true` pre-populates Accounts, Contacts, etc. |
| `orgPreferences` | No | Deprecated in favor of `settings`; still works but avoid for new orgs |

### 2. Edition Types and What They Control

The `edition` field sets the base feature set and license model. Choose the edition that most closely matches the org your code will be deployed to in production or the target packaging environment.

| Edition | Use Case |
|---|---|
| `Developer` | Default for most feature development; lean, fast to provision |
| `Enterprise` | When production is Enterprise and you need Enterprise-only metadata |
| `Group` | Testing in small-business org shape |
| `Professional` | Testing Professional edition constraints (no Apex by default) |
| `Partner Developer` | ISV/partner package development in a Partner Business Org |
| `Partner Enterprise` | ISV enterprise package testing |

Do not use `Developer` edition if the production org is `Enterprise` and you need to test features that require Enterprise licensing — the org will provision successfully but will be missing feature flags.

### 3. Allocation Limits by Dev Hub Edition

Limits are enforced at the Dev Hub org level, not per user. All users sharing a Dev Hub share the same pool.

| Dev Hub Edition | Daily Creates | Max Active Orgs |
|---|---|---|
| Developer Edition | 6 | 3 |
| Enterprise Edition | 40 | 20 |
| Performance Edition | 100 | 50 |
| Unlimited Edition | 100 | 50 |
| Partner Business Org | Varies; typically 200+ daily / 100 active for active PBOs |

*Source: Salesforce DX Developer Guide — Supported Scratch Org Editions and Allocations*

**Expiration:** Default is 7 days. Max is 30 days. Expired orgs are automatically deleted by Salesforce along with their `ActiveScratchOrg` records. Specify `--duration-days` at creation time; you cannot extend a scratch org after it is created.

### 4. Dev Hub Objects for Automation

Two standard objects in the Dev Hub org expose scratch org state for SOQL queries and automation:

- **`ActiveScratchOrg`** — one record per currently active scratch org. Deleting this record deletes the scratch org. The `ExpirationDate` field is queryable.
- **`ScratchOrgInfo`** — one record per scratch org creation request, both active and historical. Use this for audit trails, CI dashboards, and to detect orgs approaching expiry.

```soql
SELECT Id, OrgName, ExpirationDate, CreatedBy.Name
FROM ActiveScratchOrg
WHERE ExpirationDate <= NEXT_N_DAYS:2
ORDER BY ExpirationDate ASC
```

### 5. Org Shape

Org Shape captures the edition, features, settings, and licenses of a specific source org (typically production or a staging sandbox) and uses them as the blueprint for scratch org creation — without manually maintaining a definition file for every feature toggle. Org Shape is available for Enterprise and above Dev Hubs.

When to prefer Org Shape over a hand-maintained definition file:
- Production has many enabled features that are hard to enumerate manually
- You want scratch orgs to automatically reflect new features enabled in production
- The team's definition file drifts from production and causes "works in scratch, breaks in prod" failures

When to keep a definition file:
- You want a deliberately minimal or controlled environment (e.g., packaging)
- You need portability across multiple source orgs

---

## Common Patterns

### Mode 1: Create a Scratch Org from a Definition File

**When to use:** Standard feature branch development; new team member onboarding; CI jobs.

```bash
# Create org from definition file, set as default, expire in 14 days
sf org create scratch \
  --definition-file config/project-scratch-def.json \
  --alias feature-myfeature \
  --duration-days 14 \
  --set-default \
  --target-dev-hub MyDevHub

# Push source to the new org
sf project deploy start

# Open the org in a browser
sf org open --target-org feature-myfeature

# When done — explicitly delete to free allocation
sf org delete scratch --target-org feature-myfeature --no-prompt
```

### Mode 2: Audit and Manage Active Org Pool from Dev Hub

**When to use:** Team lead or CI admin needs to reclaim allocations; pre-flight check before a CI run; regular hygiene.

```bash
# List all orgs known to the local CLI
sf org list --all

# From inside the Dev Hub org, query active orgs
sf data query \
  --query "SELECT OrgName, ExpirationDate, CreatedBy.Name FROM ActiveScratchOrg ORDER BY ExpirationDate ASC" \
  --target-org MyDevHub

# Delete a specific scratch org by alias
sf org delete scratch --target-org stale-org-alias --no-prompt
```

### Mode 3: Automate in CI (GitHub Actions pattern)

**When to use:** Pull request pipelines that need a fresh org per run and must release it when done.

```yaml
# .github/workflows/ci.yml (relevant steps)
- name: Authenticate Dev Hub
  run: sf org login jwt --client-id ${{ secrets.SF_CLIENT_ID }} \
       --jwt-key-file server.key \
       --username ${{ secrets.SF_USERNAME }} \
       --alias DevHub --set-default-dev-hub

- name: Create scratch org
  run: sf org create scratch \
       --definition-file config/project-scratch-def.json \
       --alias ci-org --duration-days 1 \
       --target-dev-hub DevHub

- name: Deploy and test
  run: |
    sf project deploy start --target-org ci-org
    sf apex run test --target-org ci-org --result-format tap --code-coverage

- name: Delete scratch org
  if: always()
  run: sf org delete scratch --target-org ci-org --no-prompt
```

The `if: always()` guard ensures the org is deleted even when prior steps fail, preventing allocation leaks.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Team hitting active org limit daily | Enforce `--duration-days 1` for CI orgs; add `if: always()` delete step to pipeline | Active limit is per Dev Hub, shared across all users |
| Scratch org missing a feature present in production | Add feature string to `features` array, or switch to Org Shape | Features not declared at creation cannot be added after provisioning |
| Need to reproduce a production-specific bug | Use Org Shape sourced from production replica or staging sandbox | Captures actual feature flags, avoiding manual enumeration errors |
| ISV building a managed package | Use `Partner Developer` or `Partner Enterprise` edition with linked namespace | Partner editions include packaging permissions not in standard Developer edition |
| New developer hits "allocation exceeded" | Run SOQL on `ActiveScratchOrg` in Dev Hub; delete orgs older than 7 days | Expired orgs pending auto-cleanup still count against the limit |
| CI org creation failing intermittently | Add retry logic; check `ScratchOrgInfo.Status` for `Failed` records | Scratch org provisioning is asynchronous; transient failures occur under heavy load |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `edition` in definition file matches the target deployment environment
- [ ] All required `features` are declared; no relying on defaults that differ across editions
- [ ] `duration` is appropriate: CI orgs use 1 day, developer orgs use no more than 14 days
- [ ] CI pipeline includes an unconditional delete step (`if: always()`)
- [ ] Team is not sharing a Developer Edition Dev Hub for multi-person CI (only 3 active orgs)
- [ ] `hasSampleData: false` unless test data is explicitly needed
- [ ] Org Shape source org is specified when using Org Shape
- [ ] `ScratchOrgInfo` records reviewed in Dev Hub after any provisioning failure

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Daily limit is a rolling 24-hour window, not a midnight reset** — The daily scratch org limit resets on Salesforce's rolling 24-hour window tied to the Dev Hub instance, not the user's local midnight. Teams scheduling CI jobs at midnight may still be within the previous window's count.

2. **`orgPreferences` is deprecated and silently drops settings** — Definition files using the old `orgPreferences` format provision successfully, but some settings are silently ignored. The correct format is `settings` using Metadata API setting objects. A definition file that "worked before" may be missing settings on newer API versions without any error.

3. **Scratch org expiration cannot be extended after creation** — The `--duration-days` flag is set once at creation time. There is no extension command. If work is in progress on an expiring org, the only recovery path is to push source, create a new org, and re-pull — or extract the org's metadata before expiry.

4. **Deleting from Active Scratch Orgs list does NOT delete the ScratchOrgInfo record** — `ScratchOrgInfo` is a permanent audit record of every creation request. Only `ActiveScratchOrg` is deleted (and the org freed). This confuses practitioners expecting both records to be cleaned up, but it is correct behavior.

5. **`hasSampleData: true` dramatically slows provisioning** — Sample data injection adds 3–5 minutes to scratch org creation. In CI with parallel jobs, this compounds significantly. Disable it unless tests depend on standard sample objects.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `config/project-scratch-def.json` | Scratch org definition file — source of truth for org shape in the project |
| `sf org list --all` output | Snapshot of all locally tracked orgs for audit |
| SOQL on `ActiveScratchOrg` | Real-time view of active pool from Dev Hub |
| CI pipeline YAML snippet | Workflow fragment for automated scratch org lifecycle |

---

## Related Skills

- `sf-cli-and-sfdx-essentials` — First-time CLI setup, Dev Hub enablement, basic push/pull/open commands; use this when the user is new to SFDX
- `cicd-pipeline-setup` — Full CI/CD pipeline configuration beyond the scratch org lifecycle step
- `source-tracking-and-deploy` — Deep dive on source tracking behavior, delta deploys, and retrieve conflicts
