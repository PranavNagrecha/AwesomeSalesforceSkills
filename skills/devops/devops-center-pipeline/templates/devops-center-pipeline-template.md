# DevOps Center Pipeline — Work Template

Use this template when setting up a new pipeline, planning a release promotion, or diagnosing a DevOps Center issue. Fill in every section before beginning work.

---

## Request Summary

**What was asked:**
(e.g., "Set up a three-stage DevOps Center pipeline for our admin team" / "Why is our promotion to UAT failing?")

**Requestor:**

**Date:**

---

## Pipeline Context

| Property | Value |
|---|---|
| DevOps Center package version installed | (check Setup > Installed Packages) |
| GitHub organization / repository URL | |
| GitHub connection type | OAuth (personal) / OAuth (service account) / GitHub App |
| Branch protection rules active on stage branches? | Yes / No / Not yet configured |
| Production org type | Production / Developer Edition |

---

## Pipeline Stage Map

Fill in one row per stage. Every stage must have a unique org and a unique branch.

| Stage # | Stage Name | Org Name | Org Type | GitHub Branch Name | Notes |
|---|---|---|---|---|---|
| 1 | Development | | Developer Sandbox / Scratch Org | `stage/development` | |
| 2 | QA | | Developer Sandbox | `stage/qa` | |
| 3 | UAT | | Partial Copy / Full Sandbox | `stage/uat` | |
| 4 | Staging | | Full Sandbox | `stage/staging` | |
| 5 | Production | | Production | `main` | |

(Delete rows for stages not in use. Add rows if more than 5 stages are needed — max 15.)

---

## Work Items in Scope

List the Work Items included in this release or being diagnosed.

| Work Item Name | Status | Stage | Metadata Components Changed | Ready to Promote? |
|---|---|---|---|---|
| | In Progress / Ready to Promote / Promoted | | | Yes / No |
| | | | | |
| | | | | |

---

## Bundle Strategy

- [ ] Promote all Work Items as individual items (no bundling needed — no shared metadata components)
- [ ] Bundle all Work Items into one Bundle before QA promotion
- [ ] Bundle subset (list items that share components): ___________________________
- [ ] Combine Work Items with dependencies before promoting: ___________________________

**Rationale:**
(e.g., "Work Items A and B both modify the Opportunity record page layout — they must be bundled to avoid a conflict on QA promotion.")

---

## Conflict Status

| Work Item | Conflicting Item | Conflicting Component | GitHub PR URL | Resolution Status |
|---|---|---|---|---|
| | | | | Open / Resolved / N/A |

---

## Pre-Promotion Checklist

Complete all items before promoting to the next stage.

### Before any stage promotion
- [ ] DevOps Center package is installed and up to date
- [ ] GitHub repository is reachable and OAuth connection is active
- [ ] All Work Items in scope are marked Ready to Promote
- [ ] No unresolved conflicts flagged in the DevOps Center promotion view
- [ ] All conflicted GitHub PRs are merged

### Before production promotion specifically
- [ ] All Work Items have passed QA and UAT in their respective stage orgs
- [ ] Change management approval obtained (if required by org change policy)
- [ ] Deployment window confirmed with stakeholders
- [ ] Rollback plan documented: if the production promotion fails, which Work Items need to be reverted and in what order?
- [ ] Deployment Status page (Setup > Environments > Deploy > Deployment Status) bookmarked for monitoring
- [ ] No SFDX CLI deployments or Metadata API direct deploys scheduled to the same production org during the promotion window

---

## Post-Promotion Notes

**Promotion outcome:** Success / Failure / Partial

**Deployment Status page error log (if failed):**
(paste the component error message from Setup > Environments > Deploy > Deployment Status)

**Resolution taken:**

**Follow-up Work Items created:**

---

## Deviations from Standard Pattern

(Record any step that deviated from the SKILL.md patterns and the reason why.)
