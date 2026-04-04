# Environment Strategy Template

Use this template to document the full environment topology for a Salesforce program. Fill in one row per environment. This template covers both scratch orgs and sandboxes.

---

## Program Context

**Program / Org name:**
**Salesforce edition:**
**Sandbox allocations (Full / Partial / Developer Pro / Developer):**
**Dev Hub org (if using scratch orgs):**
**Branching strategy (trunk-based / Gitflow / feature-branch):**
**CI/CD tooling:**

---

## Environment Matrix

| Environment Name | Org Type | Pipeline Stage | Branch Tier | Purpose | Data Volume | Source Tracked | Refresh / Expiry | Owner | Post-Refresh Automation |
|---|---|---|---|---|---|---|---|---|---|
| `ci-scratch` | Scratch Org | CI / Unit Test | `feature/*` (per PR) | Isolated Apex test run per pull request | None (empty) | Yes | 7-day expiry, deleted after CI run | CI pipeline | Delete on completion |
| `dev-<name>` | Scratch Org | Individual Development | `feature/<name>` | Developer's isolated build environment | None (seeded via scripts) | Yes | 30-day max, renewed as needed | Developer | Re-seed data scripts |
| `integration` | Developer Pro Sandbox | Integration | `main` | Shared merge target after PR approval | None | Yes (CLI flag) | On demand (post-sprint) | Tech Lead | Named Credentials, users, schedules |
| `uat` | Partial Copy Sandbox | UAT | `release/*` | Stakeholder review with realistic data | Up to 5 GB sample | No | Every 5 days minimum | Release Manager | Masking, Named Credentials, users |
| `performance` | Full Sandbox | Performance Testing | `release/*` | Load and performance testing | Full production copy | No | Every 29 days minimum | Architect | Masking, anonymization, Named Credentials |
| `pre-production` | Full Sandbox | Pre-Production Regression | `release/*` | Final regression and cutover rehearsal | Full production copy | No | Each major release cycle | Release Manager | Full post-refresh runbook |

> Add or remove rows to match your actual pipeline stages. Every environment must have a defined purpose and owner.

---

## Scratch Org Definition Reference

If using scratch orgs, record the definition file path and key shape settings:

**Definition file:** `config/project-scratch-def.json`

**Key settings:**
- `edition`: (Developer / Enterprise)
- `features`: list features required (e.g., `["Communities", "ServiceCloud"]`)
- `orgPreferences`: (e.g., `{ "Lightning": true }`)
- `release`: leave unset unless explicitly testing preview release behavior

**Active org limit (Dev Hub):** ___ / ___ (current / maximum)

---

## Branching-to-Environment Map

| Branch Tier | Target Environment | Deployment Trigger |
|---|---|---|
| `feature/*` | Scratch org (per developer or per PR) | On branch create / PR open |
| `main` / `integration` | Integration (Developer Pro Sandbox) | On PR merge to main |
| `release/*` | UAT (Partial Copy Sandbox) | On release branch creation |
| `release/*` (pre-prod) | Pre-Production (Full Sandbox) | On release sign-off |
| `main` (post-release) | Production | On approved release deployment |

---

## Refresh and Governance Schedule

| Environment | Refresh Cadence | Refresh Owner | Masking Required | Post-Refresh Steps |
|---|---|---|---|---|
| Integration sandbox | Each sprint start | Tech Lead | No | Named Credentials, users, schedules |
| UAT sandbox | Each sprint or on demand (min 5 days) | Release Manager | Yes — PII masking policy | Masking run, data seeding, Named Credentials, users |
| Performance sandbox | Each performance test cycle (min 29 days) | Architect | Yes — anonymize all PII | Anonymization, load test data seeding |
| Pre-production sandbox | Each major release cycle (min 29 days) | Release Manager | Yes — full masking policy | Full post-refresh runbook (see runbook doc) |

---

## Notes and Deviations

Record any decisions that deviate from the standard topology above and the rationale:

- _Example: We do not use a dedicated performance sandbox because Edition X does not include a second Full sandbox allocation. Performance testing runs in the pre-production sandbox in a separate window before regression testing begins._
