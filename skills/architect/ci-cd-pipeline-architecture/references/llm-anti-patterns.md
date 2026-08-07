# LLM Anti-Patterns — CI/CD Pipeline Architecture

Common mistakes AI coding assistants make when generating or advising on CI/CD pipeline architecture for Salesforce.

## Anti-Pattern 1: Conflating Pipeline Architecture With CI Tool Configuration

**What the LLM generates:** A detailed GitHub Actions workflow YAML with job steps, authentication commands, and test flags, presented as "your CI/CD pipeline architecture."

**Why it happens:** Training data heavily skews toward CI tool tutorials and workflow files. The LLM pattern-matches "CI/CD pipeline" to "YAML configuration" rather than to "stage sequence and gate design."

**Correct pattern:**

```
A CI/CD pipeline architecture output should include:
- A stage sequence table: Stage Name | Environment | Trigger | Gate Criteria | Promotion Owner
- A quality gate specification per stage transition
- A rollback strategy per stage
- A decision record explaining why this topology was chosen

The YAML implementation is a separate, downstream artifact.
Use devops/github-actions-for-salesforce for the YAML.
Use this skill (architect/ci-cd-pipeline-architecture) for the architecture.
```

**Detection hint:** If the output contains `jobs:`, `steps:`, `uses: actions/checkout`, or `sfdx force:source:deploy` but no stage sequence table or gate specification, the response is answering a CI tool question, not a pipeline architecture question.

---

## Anti-Pattern 2: Claiming DevOps Center Supports Custom Quality Gates or Code Scanning

**What the LLM generates:** "DevOps Center includes built-in code quality gates. You can configure custom test thresholds and PMD scan rules directly in DevOps Center settings."

**Why it happens:** The LLM interpolates from general DevOps platform descriptions (which often do include configurable quality gates) onto DevOps Center, which does not. DevOps Center's promotion check is limited to conflict detection and merge status as of Spring '25.

**Correct pattern:**

```
DevOps Center does NOT provide:
- Custom test coverage thresholds
- PMD / Salesforce Code Analyzer integration
- Code scanning gates
- Configurable pass/fail criteria on quality metrics

These must be implemented in an external CI tool (GitHub Actions, GitLab CI, Jenkins)
layered alongside DevOps Center. DevOps Center handles promotion; the CI tool handles gates.
```

**Detection hint:** If the response includes phrases like "configure quality gates in DevOps Center" or "DevOps Center code scanning" without qualifying that these must be external tools, flag for review.

---

## Anti-Pattern 2b: Inventing a DevOps Center Maximum Stage Count (and Citing a Guide for It)

**What the LLM generates:** "DevOps Center supports a maximum of 15 pipeline stages per pipeline, as documented in the DevOps Center Setup and Administration Guide. Pipelines exceeding 15 stages must move overflow stages to a CLI-driven or third-party tool (Copado, Flosum, AutoRABIT)." Often escalated with a fabricated observable behaviour — "attempting to add a 16th stage produces an error."

**Why it happens:** Two mechanisms compound. First, **limit-shaped-slot filling**: Salesforce documentation is dense with hard numeric ceilings, so when asked "what's the limit on X?" the model produces a number rather than the correct answer "there isn't one." A missing limit is not a shape the training distribution represents well. Second, **citation laundering**: the model attaches the invented figure to a real-sounding document title ("DevOps Center Setup and Administration Guide"), which makes the claim survive review — a reader who trusts the citation does not go and check it. Note that a real nearby number exists to be relabelled: guidance recommends keeping a *bundling* stage to roughly 50 or fewer **work items**. That is a work-item count on one stage, not a stage count on a pipeline.

**Correct pattern:**

```
Salesforce, "Plan Your Pipeline" (DevOps Center Help):

  "Your pipeline can contain any number of pipeline stages."

There is NO documented maximum stage count. The real ceilings on a deep pipeline:
  - Sandbox entitlement — every stage needs its own connected environment
    (edition-dependent Developer / Developer Pro / Partial Copy / Full counts,
     plus each type's refresh interval)
  - Lead time — promotion is sequential; each stage adds a merge and a deploy
  - Long-lived branch count — one per stage, in the connected repo

Legitimate reasons to leave DevOps Center for Copado / Flosum / AutoRABIT:
  - non-linear or branching promotion
  - per-stage approval workflows
  - data seeding / test data management
  - back-promotion from a higher stage
  - custom quality gates and code scanning (see Anti-Pattern 2)
Stage count is NOT one of them.
```

**Detection hint:** Two mechanical checks. (1) Grep generated architecture text for a bare integer within 60 characters of `stage` plus `DevOps Center` — any such pairing is suspect, because the documented answer is "any number." (2) Treat *any* claim attributed to the "DevOps Center Setup and Administration Guide" as unverified until the URL is produced: the canonical source is the DevOps Center section of Salesforce Help (`help.salesforce.com/.../devops_center_pipeline_plan.htm`), and a citation given as a guide *title* with no URL is the signature of a laundered fabrication. More generally: when a tool-selection recommendation turns on a numeric ceiling, require the ceiling's URL before acting on it.

---

## Anti-Pattern 3: Recommending Native Rollback for Declarative Metadata

**What the LLM generates:** "If the deployment breaks production, you can roll back using the Deployment Status page in Setup, or by clicking 'Rollback' in the DevOps Center pipeline view."

**Why it happens:** Software engineering training data includes platforms (Kubernetes, Heroku, AWS Elastic Beanstalk) that do support native rollback. The LLM generalizes this to Salesforce where it does not exist for declarative metadata.

**Correct pattern:**

```
Salesforce declarative metadata (Flows, Page Layouts, Custom Objects, Profiles)
has NO native rollback mechanism. Recovery requires:
1. git revert the offending commit
2. sf project deploy start (re-deploy the reverted state)
   - OR -
3. sf project deploy start --manifest destructiveChanges.xml (remove added metadata)

Document the rollback procedure in the pipeline runbook BEFORE each production deploy.
For Apex and LWC, a forward-fix commit is often faster than a rollback deployment.
```

**Detection hint:** Any mention of a "rollback button," "undo deployment," or "revert in DevOps Center" for production metadata should be flagged as incorrect.

---

## Anti-Pattern 4: Recommending RunAllTestsInOrg for All CI Gates

**What the LLM generates:** "For your CI gate, use `--test-level RunAllTestsInOrg` to ensure maximum test coverage and catch all regressions before every deploy."

**Why it happens:** RunAllTestsInOrg sounds like the most thorough option and LLMs default to "most thorough" without considering execution time cost. On a large org, RunAllTestsInOrg can take 30–90 minutes per run, blocking developer feedback loops.

**Correct pattern:**

```
Stage 1 (CI, per PR): --test-level RunSpecifiedTests or RunLocalTests
  - Run only tests directly related to changed classes
  - Fast feedback (target < 10 minutes)
  - Catches regressions in modified code

Stage 2 (QA, per sprint merge): --test-level RunLocalTests
  - Full local test suite
  - Acceptable on a less frequent cadence

Pre-Production only: Consider RunAllTestsInOrg for the final staging gate
  - High confidence but expensive; run once per release, not per PR

RunAllTestsInOrg on every PR is a pipeline velocity anti-pattern.
```

**Detection hint:** If the pipeline spec recommends RunAllTestsInOrg at the feature branch or PR stage without qualifying frequency or cost, the recommendation is likely miscalibrated.

---

## Anti-Pattern 5: Designing Pipelines Without Accounting for the 10-Minute Apex Test Timeout

**What the LLM generates:** A pipeline with a CI gate that runs `sf apex run test --test-level RunLocalTests` with no mention of test execution time limits, no per-class timeout monitoring, and no error-handling for timeout-vs-failure distinction.

**Why it happens:** The 10-minute per-class Apex test timeout is a Salesforce-specific platform constraint not commonly known outside the Salesforce ecosystem. LLMs trained primarily on general software engineering content do not surface it.

**Correct pattern:**

```
In CI pipeline scripts:
1. Monitor deployment result for timeout errors (distinct from test failures)
   - Timeout: deploymentStatus.status = "InProgress" past elapsed time threshold
   - Test failure: deploymentStatus.numberTestErrors > 0

2. Set a pipeline job timeout (e.g., 20 minutes for RunLocalTests)
   with a distinct "timeout" exit code vs. "test failed" exit code

3. For any test class consistently approaching 8-9 minutes:
   - Split the class into smaller focused test classes
   - Remove expensive @TestSetup that creates unnecessary data volumes

4. Add test execution time monitoring to the CI job output
   (parse sf apex run test --json result for each class duration)
```

**Detection hint:** If the CI pipeline spec does not mention test execution time limits or does not distinguish timeout errors from test assertion failures, add the platform constraint to the output.

---

## Anti-Pattern 6: Ignoring the 96-Hour Quick Deploy Expiry in Release Runbooks

**What the LLM generates:** "Validate your deployment on Thursday, get CAB approval, then use quick deploy on Monday to minimize your production change window."

**Why it happens:** Quick deploy is a well-known Salesforce optimization, but the 96-hour expiry is a constraint mentioned only in the Salesforce deployment documentation footnotes. LLMs familiar with quick deploy may not surface the expiry constraint.

**Correct pattern:**

```
Quick deploy (sf project deploy quick --job-id <ID>) requires:
- The validation job ID to be less than 96 hours old at time of deployment
- The same Apex tests that ran during validation must still exist in the org

Pipeline runbook must include:
- Timestamp the validation job completion
- Check expiry before scheduling the production window
- If expiry risk exists: re-run validation as part of the deploy preparation step
- Never schedule CAB approval more than 3 days after validation without a re-validate step
```

**Detection hint:** Any pipeline or runbook that references quick deploy without mentioning the 96-hour expiry window should be flagged for addition of this constraint.
