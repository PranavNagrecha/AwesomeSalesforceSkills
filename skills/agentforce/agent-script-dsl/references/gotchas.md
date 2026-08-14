# Gotchas — Agent Script DSL

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: GenAiPlannerBundle Is Only Available at API v64.0+ — and v64.0 Is Summer '25, Not Spring '26

**What happens:** Deploying a GenAiPlannerBundle metadata record from a project configured for API v63.0 or lower fails with an unknown-type error naming GenAiPlannerBundle. This is often misdiagnosed as a packaging or manifest problem, or — worse — as the *org* being too old.

**When it occurs:** When `sourceApiVersion` in `sfdx-project.json` (or the version in the Metadata API call) is set to 63.0 or lower. The Metadata API guide is explicit: "GenAiPlanner components are available in API version 60.0 to 63.0. GenAiPlannerBundle replaces GenAiPlanner in API version 64.0 and later." API v64.0 shipped with **Summer '25**. A widespread misattribution places the cutover at Spring '26 (which is API v66.0), three releases later, so teams on a Winter '26 or Spring '26 sandbox conclude their org can't support the bundle type and downgrade to GenAiPlanner unnecessarily.

**How to avoid:** Read the *project* pin, not the org release banner — every org from Summer '25 forward supports GenAiPlannerBundle, and any org will still accept a project pinned to 63.0 and behave like the old type. Set `"sourceApiVersion": "64.0"` (or higher) in `sfdx-project.json` — that is the documented key; a hand-written `apiVersion` property is ignored and in each `package.xml` `<version>`. Only genuinely pre-Summer-'25 targets need the GenAiPlanner path.

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

---

## Gotcha 6: A Bot/BotVersion/GenAiPlugin Manifest Silently Versions an Incomplete Agent

**What happens:** A CI pipeline retrieves and deploys Bot, BotVersion, GenAiPlannerBundle, GenAiPlugin, and GenAiFunction, reports success, and the agent works in the target org — but the Agent Script source was never versioned. The next Builder edit has no baseline to diff against, and a rollback restores runtime metadata whose authoring source is gone.

**When it occurs:** For any agent authored in the new Agentforce Builder. Its blueprint lives in `AiAuthoringBundle` (API v65.0+, Winter '26), described in the Metadata API guide as "a container for AI-related authoring content. For example, an AI authoring bundle for an Agentforce agent contains an Agent Script file and the associated metadata content." Manifests written against the 2024-era five-type list predate that type entirely, and a `sourceApiVersion` of 62.0/63.0 sits below its floor, so nothing errors — the type is simply never requested.

**How to avoid:** Add `AiAuthoringBundle` to the manifest and raise `sourceApiVersion` to 65.0 or higher. Expect `aiAuthoringBundles/<Name>/<Name>.agent` plus `<Name>.bundle-meta.xml` in the retrieve; if the `.agent` file is absent, the retrieve did not capture the agent. Watch the bundle's `target` field in review — omitting it deploys the agent in draft state, while setting it to `{Bot}.{BotVersion}` commits the agent version, the equivalent of Agentforce Builder's version commit. Committing a version is still not activation; Gotcha 2 applies regardless.
