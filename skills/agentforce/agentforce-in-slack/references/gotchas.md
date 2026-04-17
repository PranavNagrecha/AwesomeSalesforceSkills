# Gotchas — Agentforce In Slack

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: General Slack Actions Topic Is Not Auto-Included After Slack Deployment

**What happens:** After successfully connecting an Agentforce agent to Slack using the standard Slack deployment flow in Setup, the agent responds to Slack messages but has no Slack-native capabilities (no canvas creation, no DM sending, no message history search). Attempts to ask the agent to perform these tasks result in the agent saying it cannot help or returning a generic "I don't have that capability" response.

**When it occurs:** Every time a new Slack deployment is created. The General Slack Actions topic is a standard topic that must be explicitly added — it is not bundled or auto-activated as part of the Slack deployment process. This affects every agent connected to Slack, regardless of the agent type or how it was created.

**How to avoid:** After completing the Slack deployment flow, always open the agent in Agent Builder, navigate to Topics, and explicitly add the **General Slack Actions** topic. Treat this as a mandatory post-deployment step in any Slack deployment runbook or checklist.

---

## Gotcha 2: Canvas Creation Silently Fails On Slack Free Workspaces

**What happens:** The Create Canvas action is available in the agent's action set (the General Slack Actions topic has been added and the agent is Active), but when users ask the agent to create a canvas, the action either fails with a non-descriptive error or the agent responds that it is unable to complete the request. There is no clear plan-restriction error surfaced in the Slack conversation.

**When it occurs:** When the target Slack workspace is on the Free plan. Slack canvases are a paid feature. The Salesforce-managed Slack app registers the Create Canvas action regardless of the workspace plan, so it appears available in Agent Builder even though it will fail at runtime in a Free workspace.

**How to avoid:** Before configuring any canvas-based workflows or communicating canvas capabilities to users, confirm the Slack workspace plan by asking the Slack workspace admin or checking the workspace billing settings. If the workspace is on Free, either upgrade the plan or remove canvas-dependent workflows from the agent's response design. Do not rely on the presence of Create Canvas in the action picker as confirmation that canvas creation will work in the target workspace.

---

## Gotcha 3: Private Action Falls Through To A Hard Failure, Not A Graceful Downgrade

**What happens:** A Slack user who has not completed the Salesforce identity mapping triggers a private action. Instead of silently executing with a broader context or returning a generic answer, the agent refuses to execute the action entirely. Depending on how the agent's error handling is configured, this may surface as an unhelpful generic error rather than a clear "please connect your account" message.

**When it occurs:** Any time a Slack user who is not mapped to a Salesforce user triggers a topic that contains private actions. This is particularly common with new employees who have Salesforce accounts but have never interacted with the Agentforce agent in Slack before, or with users who joined the Slack workspace after the initial identity mapping provisioning was done.

**How to avoid:** Design the agent's topic instructions to include explicit handling for authorization failures. Add an instruction to the relevant topic such as: "If the user's Salesforce identity cannot be resolved, respond with: 'I need to connect to your Salesforce account to answer this. Please use this link to connect: [connection prompt]'." Also ensure that the initial Slack deployment communication to users includes onboarding instructions for completing the identity connection step.

---

## Gotcha 4: Identity Mapping Is Per-Org — Sandbox Mappings Do Not Carry To Production

**What happens:** An admin sets up Salesforce-to-Slack identity mappings for all users in a sandbox environment and fully tests private actions. After deploying the agent and Slack configuration to production, private actions fail for all users because the identity mappings do not exist in the production org.

**When it occurs:** During any promotion from sandbox to production. Identity mappings are stored as data records (not metadata) in the Salesforce org. Metadata deployments (change sets, Salesforce DX, Copado) do not include these data records. The production org starts with zero identity mappings even if the sandbox was fully populated.

**How to avoid:** Include identity mapping re-provisioning as an explicit step in the production go-live runbook. Either communicate to all users that they must complete the one-time connection flow, or export the sandbox mapping data and re-import it into production via the Slack for Salesforce app's bulk mapping interface. Build this step into the release checklist and test with at least one mapped production user before go-live.

---

## Gotcha 5: Send DM Requires `im:write` Scope Which May Not Be Granted In Older Slack Deployments

**What happens:** The General Slack Actions topic is added, the agent is Active, but when the agent attempts to send a direct message via the Send DM action, it fails with a permission or scope error. Other Slack-native actions (Look Up User, Search Message History) may work correctly.

**When it occurs:** When the Salesforce-managed Slack app was installed before the `im:write` scope was added to the app's required OAuth scope set (typically in deployments configured before Spring '25). The OAuth consent granted at installation time does not automatically expand to include new scopes added in subsequent Salesforce releases.

**How to avoid:** Check the currently granted scopes in the Slack app management console (api.slack.com/apps) for the Salesforce-managed app. If `im:write` is missing from the granted scopes, the Slack workspace admin must re-authorize the app. In the Salesforce Setup Slack deployment flow, there is typically an option to refresh or re-authorize the OAuth connection, which triggers a new scope consent screen. After re-authorization, re-test the Send DM action.
