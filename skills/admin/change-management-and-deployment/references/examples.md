# Examples: Change Management and Deployment

---

## Example: Small Admin Hotfix

**Scenario:** A validation rule typo is blocking Case creation in production. The admin team has connected sandboxes but no source-driven release process yet.

**Decision:** Use a tightly scoped Change Set for the hotfix, document the change, and update source afterward.

**Why this is acceptable:** The release is small, urgent, and low in dependency complexity.

**What would be wrong:** treating that success as proof that weekly multi-feature releases should stay on Change Sets forever.

---

## Example: Moving from Change Sets to DevOps Center

**Scenario:** An admin team deploys page layouts, fields, flows, and permission sets every sprint. Releases are manual and regression-prone.

**Decision:** Move to DevOps Center with source-tracked Developer sandboxes and a simple Sandbox -> Production promotion path.

**Why:** The team needs Git-backed promotion discipline and review, but not a fully custom CI/CD program on day one.

---

## Example: Metadata Release Coupled to Data Cutover

**Scenario:** A release adds new Opportunity stages, validation rules, and a bulk update to open Opportunities.

**Release handling:**
1. deploy metadata to lower environments
2. rehearse data load and reconciliation
3. define production sequence explicitly
4. keep data rollback separate from metadata rollback

**The deploy contract, written down before the window.** This is what the release plan
hands to whoever runs the pipeline. Every value is chosen; none is left to a default.

```yaml
release: 2026-09-12-opportunity-stage-realignment
target_org: production
vehicle: sf CLI              # decision matrix row 3 - weekly cadence, 4 environments

deploy_options:
  checkOnly:        true     # pass 1 only; pass 2 is a quick deploy of this validation
  rollbackOnError:  true     # required in production; set explicitly in sandbox too
  testLevel:        RunLocalTests
  runTests:         []       # empty - only read when testLevel is RunSpecifiedTests
  purgeOnDelete:    false    # inert in production anyway; deletions go to the Recycle Bin
  ignoreWarnings:   false
  allowMissingFiles: false   # the guide says do not set this for production

manifests:
  package:              manifest/package.xml
  destructive_pre:      null
  destructive_post:     manifest/destructiveChangesPost.xml   # retires Stage_Legacy__c

validation:
  run_on:        2026-09-09          # 3 days before the window
  expires_on:    2026-09-19          # 10-day quick-deploy clock
  target:        production          # NOT staging - a staging validation licenses nothing here

sequence:
  1_metadata:    "validated package, quick deploy"
  2_data:        "bulk update of open Opportunities - separate job, separate owner"
  3_activation:  "activate Opportunity_Stage_Router flow"

backout:
  metadata: "redeploy manifest/pre-release/ (retrieved 2026-09-08, before any change)"
  data:     "restore StageName from the pre-load export - NOT covered by the metadata backout"
  fastest:  "deactivate Opportunity_Stage_Router; leaves fields in place, stops the behaviour"
```

**Lesson:** one release window can contain both metadata and data, but they must not share one vague rollback sentence. Note that `backout.metadata` and `backout.data` are two different jobs with two different owners — redeploying the old manifest does not un-edit the records the release touched.
