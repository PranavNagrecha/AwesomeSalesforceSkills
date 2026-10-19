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
| DevOps Center edition | Managed package (`enableDevOpsCenterGA`) / Next-generation (`enableALMDevopsCorePref`) |
| Source control provider / repository URL | GitHub / Bitbucket — |
| Named Credential and the account behind it | (service account, not personal) |
| Branch protection rules active on stage branches? | Yes / No / Not yet configured |
| Production org type | Production / Developer Edition |

---

## Pipeline Stage Map

Fill in one row per stage. Every stage has its own environment and branch; exactly one stage (production) has no next stage.

| Stage # | Stage Name | Environment (org) | Branch | Next Stage | IsBundled | Test Level |
|---|---|---|---|---|---|---|
| 1 | QA | | | UAT | false | RunLocalTests / RunSpecifiedTests |
| 2 | UAT | | | Production | true / false | |
| 3 | Production | | (repository default branch, typically `main`) | — | false | RunLocalTests |

Development environments (source-tracked Developer/Developer Pro sandboxes or scratch orgs): ______________________

---

## Work Items in Scope

List the Work Items included in this release or being diagnosed.

| Work Item Name | Status | Stage | Metadata Components Changed | Ready to Promote? |
|---|---|---|---|---|
| | NEW / IN_PROGRESS / IN_REVIEW / READY_TO_PROMOTE / PROMOTED / MERGE_CONFLICT / COMBINED / CLOSED | | | Yes / No |
| | | | | |
| | | | | |

---

## Bundle Strategy

- [ ] Promote all Work Items as individual items (no bundling needed — no shared metadata components)
- [ ] Bundling stage (IsBundled = true): ___________________________
- [ ] Combine Work Items with dependencies before promoting: ___________________________

**Rationale:**
(e.g., "Work Items A and B both modify the Opportunity record page layout — they must be bundled to avoid a conflict on QA promotion.")

---

## Conflict Status

| Work Item | Conflicting Item | Conflicting Component | Pull request reference | Resolution (rebase / combine / back sync) |
|---|---|---|---|---|
| | | | | Open / Resolved / N/A |

---

## Pre-Promotion Checklist

Complete all items before promoting to the next stage.

### Before any stage promotion
- [ ] The provider connection (Named Credential) is active
- [ ] All Work Items in scope are READY_TO_PROMOTE or PROMOTED to the current stage
- [ ] No Work Item in scope is in MERGE_CONFLICT
- [ ] `check_devops_center_pipeline.py --manifest-dir .` exits 0 on the current stage export

### Before production promotion specifically
- [ ] All Work Items have passed QA and UAT in their respective stage orgs
- [ ] Change management approval obtained (if required by org change policy)
- [ ] Deployment window confirmed with stakeholders
- [ ] Rollback plan documented: if the production promotion fails, which Work Items need to be reverted and in what order?
- [ ] Owner named for the `DevopsRequestInfo` ERROR / INTERRUPTED query during the promotion window
- [ ] No SFDX CLI deployments or Metadata API direct deploys scheduled to the same production org during the promotion window

---

## Post-Promotion Notes

**Promotion outcome:** Success / Failure / Partial

**DevopsRequestInfo error (if failed):**
(paste `OperationType`, `Status`, `Message`, and `ErrorDetails` from the failed request record)

**Resolution taken:**

**Follow-up Work Items created:**

---

## Deviations from Standard Pattern

(Record any step that deviated from the SKILL.md patterns and the reason why.)
