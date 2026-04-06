# Gotchas — Agent Script DSL

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: GenAiPlannerBundle Is Only Available at API v64+

**What happens:** Deploying a GenAiPlannerBundle metadata record against an org or project configured for API v63 or lower fails with an "Unknown type: GenAiPlannerBundle" error. This error is often misdiagnosed as a packaging or manifest problem.

**When it occurs:** When `apiVersion` in `sfdx-project.json` or the Metadata API call is set to 63.0 or lower, and the project was built expecting Spring '26 (API v64) features. Also occurs when retrieving agent metadata from a Spring '26+ org and trying to deploy it to a Winter '26 sandbox.

**How to avoid:** Confirm the target org's Salesforce release and set the project API version accordingly. For Spring '26 agents, set `"apiVersion": "64.0"` in `sfdx-project.json`. When working across mixed-version environments (e.g., a production org on Winter '26 while sandboxes are on Spring '26 preview), use GenAiPlanner (v60–v63 compatible) for the production path and plan the API version upgrade as part of the promotion strategy.

---

## Gotcha 2: Activation State Is Not Deployable — Agents Arrive Inactive

**What happens:** An agent deployed from sandbox to production via Metadata API, a change set, or a pipeline arrives in Inactive state in the target org, regardless of its Active state in the source org. There is no metadata attribute for activation state. Pipelines that treat a successful deploy as a successful release will leave production with an inactive, invisible agent.

**When it occurs:** Every cross-org promotion. This affects all pipeline stages: dev sandbox to QA sandbox, QA sandbox to staging, staging to production. The behavior is consistent and by design — Salesforce deliberately requires a human to explicitly activate an agent in each environment.

**How to avoid:** Add an explicit post-deploy activation step to every pipeline stage. This step cannot be automated via Metadata API; it requires a UI action in Setup > Agentforce Agents or in Agentforce Builder. Document this as a required manual gate in the deployment runbook. For CI pipelines, use a `sf org open` command to surface the correct Setup URL as a deployment notification, prompting the operator to activate.

---

## Gotcha 3: LSP Errors in VS Code Do Not Block CLI Deploy

**What happens:** The Salesforce Agentforce VS Code extension shows inline LSP diagnostic errors in a `.agent` file, but `sf project deploy start` succeeds anyway. The deployed agent may exhibit schema violations or missing fields at runtime that only surface when the agent tries to invoke a topic.

**When it occurs:** When a developer authors a `.agent` file with structural errors, sees LSP warnings, dismisses them, and deploys directly via CLI. The Salesforce CLI does not perform the same schema-level validation as the LSP. Some violations are only caught at runtime during agent execution.

**How to avoid:** Treat LSP warnings as blocking errors, not optional hints. Before deploying, verify the VS Code Agentforce extension reports zero diagnostics. For CI pipelines, consider adding a pre-deploy step that runs `sf agent validate` (if available for the installed plugin version) or lint the `.agent` file against the published JSON Schema for the Agent DSL. Never skip LSP review on the grounds that the deploy command will catch problems.

---

## Gotcha 4: plannerInstructions Is a Plain-Text Field — Retrieves Overwrite It Entirely

**What happens:** When a developer retrieves agent metadata after someone else has edited the `plannerInstructions` (system prompt) in Agentforce Builder, the retrieved file replaces the entire `plannerInstructions` block in the local copy. If the local copy had unpublished edits to that block, they are silently overwritten. Git will show the diff, but only if the file was staged before the retrieve.

**When it occurs:** In collaborative teams where multiple developers or admins share access to the same org and some make changes in the Builder UI while others work in VS Code. The retrieve operation is not merge-aware; it is a file replacement.

**How to avoid:** Stage or commit the local `.agent` file before every retrieve. After retrieving, always run `git diff` before proceeding. Establish a team convention: Builder UI changes must be retrieved and committed before any team member deploys from source control. Consider using org-locking conventions for production agents — no Builder edits without a matching source control branch.

---

## Gotcha 5: sf agent test run Fails Silently When the Agent Is Not Active

**What happens:** Running `sf agent test run` against an agent that is in Draft or Inactive state returns an error message that reads like a CLI authentication or permission problem, not an agent state problem. Teams unfamiliar with the activation requirement spend significant debugging time on credentials and org connectivity before realizing the issue.

**When it occurs:** In CI pipelines where the deploy job ran successfully but the post-deploy activation step was skipped or failed. The test job runs immediately after deploy, hits an Inactive agent, and the error is misread as a pipeline infrastructure issue.

**How to avoid:** Add an explicit pre-test check to the CI pipeline that verifies the agent's Active status before invoking `sf agent test run`. A simple `sf data query` against the `BotVersion` or `GenAiPlannerBundle` object checking for Active status provides a fast, clear gate. Alternatively, add a pipeline step description comment that explicitly states "Agent must be manually activated before this step" and make the activation a required human approval gate in the pipeline configuration.
