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
  - "how do I create a scratch org from a definition file with the right edition"
  - "check how many scratch orgs my Dev Hub has left before kicking off a CI run"
  - "look up the active and daily scratch org allocation for an Enterprise Edition Dev Hub"
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
  - "Dev Hub allocation headroom check (active vs daily scratch orgs)"
  - "CI pipeline snippet for scratch org lifecycle"
  - "Diagnosis and remediation steps for allocation or provisioning failures"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-08
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
| `snapshot` | No | Name of a snapshot — a point-in-time copy of a scratch org — used to provision from a pre-built baseline instead of building the org from scratch. See `scratch-org-snapshots`. |
| `release` | No | Pins the Salesforce release relative to the Dev Hub. Options are `preview` or `previous`; defaults to the same release as the Dev Hub org. Usable **only during Salesforce release transition periods** — outside a transition window the option has nothing to resolve to. |
| `sourceOrg` | No | 15-character source org ID; the Org Shape entry point (see Org Shape below) |
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
| `Partner Group` | ISV testing against Group edition constraints |
| `Partner Professional` | ISV testing against Professional edition constraints |

The four `Partner *` editions are available only when creating scratch orgs from a Dev Hub in a Partner Business Org.

Do not use `Developer` edition if the production org is `Enterprise` and you need to test features that require Enterprise licensing — the org will provision successfully but will be missing feature flags.

### 3. Allocation Limits by Dev Hub Edition

Limits are enforced at the Dev Hub org level, not per user. All users sharing a Dev Hub share the same pool.

There are two distinct allocations, and conflating them is the root of most capacity-planning mistakes:

- **Active allocation** — the maximum number of scratch orgs you can have at any given time, based on the Dev Hub edition.
- **Daily allocation** — the maximum number of *successful* scratch org creations you can initiate in a rolling (sliding) 24-hour window. It is not a calendar-day counter and does not reset at midnight.

| Dev Hub Edition | Active Scratch Orgs | Daily Scratch Org Creations |
|---|---|---|
| Developer Edition or trial | 3 | 6 |
| Enterprise Edition | 40 | 80 |
| Unlimited Edition | 100 | 200 |
| Performance Edition | 100 | 200 |
| Partner Business Org (active) | 150 | 300 |
| Partner Business Org (trial) | 20 | 40 |

*Sources: Salesforce DX Developer Guide — Supported Scratch Org Editions and Allocations (standard editions); ISVforce Guide — Scratch Org Allocations for Partners (PBO rows).*

**Check remaining allocation before you plan around it.** Rather than inferring headroom from `sf org list`, ask the Dev Hub directly:

```bash
sf org list limits --target-org <Dev Hub username or alias>
```

Look for the `ActiveScratchOrgs` and `DailyScratchOrgs` limits in the output — each reports a `Remaining` and a `Max`. This is the authoritative view of what the Dev Hub will actually grant, and it is the right pre-flight check before a burst of CI runs.

> **Naming note.** The Salesforce CLI Command Reference lists this command as `sf org list limits`. The SFDX Developer Guide still writes it as `sf limits api display`, which the CLI retains as an alias of the same command. Prefer the canonical `sf org list limits` form; treat `sf limits api display` as legacy spelling you may encounter in older docs and scripts.

**Storage:** Scratch orgs are limited to 500 MB for data and 50 MB for files. Entities defined as metadata types are not counted against scratch org storage allocations — so a large metadata footprint is fine, but a large seeded data set is not. Plan test-data seeding against the 500 MB data ceiling rather than assuming the storage profile of the edition being emulated.

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

Org Shape captures the edition, features, Metadata API settings, limits, and licenses of a specific source org (typically production) and uses them as the blueprint for scratch org creation — without manually maintaining a definition file for every feature toggle. The scratch org created from an org shape is the same edition as the source org.

Org Shape is available in Developer, Group, Professional, Unlimited, and Enterprise editions, so a Developer Edition source org can be shaped just as an Enterprise one can. It is **not** available in scratch orgs and sandboxes — the source org cannot itself be a scratch org or a sandbox.

Org shapes are tied to a specific Salesforce release. Recreate the shape after the source org is upgraded to a new release; during a major release transition the Dev Hub and the source org can sit on different versions.

When to prefer Org Shape over a hand-maintained definition file:
- Production has many enabled features that are hard to enumerate manually
- You want scratch orgs to automatically reflect new features enabled in production
- The team's definition file drifts from production and causes "works in scratch, breaks in prod" failures

When to keep a definition file:
- You want a deliberately minimal or controlled environment (e.g., packaging)
- You need portability across multiple source orgs
- You depend on Metadata API settings with integer or string values, or on metadata and data — none of which the shape captures

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
# Authoritative headroom check — read ActiveScratchOrgs and DailyScratchOrgs
# from the Dev Hub itself before assuming you have capacity
sf org list limits --target-org MyDevHub

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
| New developer hits "allocation exceeded" | Run `sf org list limits` against the Dev Hub to see which limit is exhausted (`ActiveScratchOrgs` vs `DailyScratchOrgs`), then SOQL `ActiveScratchOrg` and delete stale orgs | The two allocations fail with similar errors but have different fixes — deleting orgs frees active slots, not daily creations |
| Daily creations exhausted but active slots free | Wait for the oldest creation to age out of the rolling window; do not delete orgs | Daily allocation is a sliding 24-hour window of *creations*; deleting orgs does not refund it |
| Seeding a large test data set into a scratch org | Trim the data set or load a subset; verify against the 500 MB data / 50 MB file ceiling | Scratch org storage is fixed and does not inherit the storage profile of the edition being emulated |
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
- [ ] Team is not sharing a Developer Edition Dev Hub for multi-person CI (only 3 active orgs, 6 daily creations)
- [ ] `sf org list limits --target-org <DevHub>` run before a planned burst of CI runs; `ActiveScratchOrgs` and `DailyScratchOrgs` both have headroom
- [ ] Peak concurrent orgs (developers + CI) sized against the Dev Hub's *active* allocation, and peak creations per 24 hours sized against the *daily* allocation — these are separate budgets
- [ ] Any seeded test data fits within 500 MB data / 50 MB files
- [ ] `hasSampleData: false` unless test data is explicitly needed
- [ ] Org Shape source org is specified when using Org Shape
- [ ] `ScratchOrgInfo` records reviewed in Dev Hub after any provisioning failure

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Daily limit is a rolling 24-hour window, not a midnight reset** — The daily allocation counts successful scratch org creations initiated in a rolling (sliding) 24-hour window, not a calendar day. Teams scheduling CI jobs at midnight may still be within the previous window's count. Deleting active orgs frees active slots but does not refund daily creations. Check both with `sf org list limits --target-org <DevHub>`.

2. **`orgPreferences` is deprecated and silently drops settings** — Definition files using the old `orgPreferences` format provision successfully, but some settings are silently ignored. The correct format is `settings` using Metadata API setting objects. A definition file that "worked before" may be missing settings on newer API versions without any error.

3. **Scratch org expiration cannot be extended after creation** — The `--duration-days` flag is set once at creation time. There is no extension command. If work is in progress on an expiring org, the only recovery path is to push source, create a new org, and re-pull — or extract the org's metadata before expiry.

4. **Deleting from Active Scratch Orgs list does NOT delete the ScratchOrgInfo record** — `ScratchOrgInfo` is a permanent audit record of every creation request. Only `ActiveScratchOrg` is deleted (and the org freed). This confuses practitioners expecting both records to be cleaned up, but it is correct behavior.

5. **`hasSampleData: true` dramatically slows provisioning** — Sample data injection adds 3–5 minutes to scratch org creation. In CI with parallel jobs, this compounds significantly. Disable it unless tests depend on standard sample objects.

6. **Scratch org storage is 500 MB data / 50 MB files and does not scale with `edition`** — Setting `"edition": "Enterprise"` gives you the Enterprise feature set, not Enterprise storage. Data-heavy seeding scripts that succeed in a sandbox fail in a scratch org. Metadata types are excluded from the calculation, so a large metadata footprint is not the problem — records are.

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
- `org-shape-and-scratch-definition` — Full definition-file schema walkthrough and Org Shape configuration
- `scratch-org-snapshots` — Provisioning from a snapshot baseline via the `snapshot` definition-file field
- `github-actions-for-salesforce` — Full CI/CD pipeline configuration beyond the scratch org lifecycle step
- `source-tracking-and-conflict-resolution` — Deep dive on source tracking behavior, delta deploys, and retrieve conflicts
