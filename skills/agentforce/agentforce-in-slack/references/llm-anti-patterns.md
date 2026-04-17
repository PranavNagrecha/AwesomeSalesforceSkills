# LLM Anti-Patterns — Agentforce In Slack

Common mistakes AI assistants make when helping with Agentforce Slack-specific configuration.

---

## Anti-Pattern 1: Assuming Agents Can Use Custom Slack Apps Instead Of The Salesforce-Managed App

**What the AI does:** When a user asks how to add Slack-native capabilities (canvas creation, DMs, message search) to an Agentforce agent, the AI recommends creating a custom Slack app, registering it at api.slack.com, generating a Bot User OAuth token, and storing it as a Named Credential in Salesforce. The AI then suggests building an Apex invocable method that calls the Slack API directly using that token.

**Why it is wrong:** Agentforce integrates with Slack via a Salesforce-managed Slack app — not a customer-created custom app. The managed app is installed through the Salesforce Setup Slack deployment flow and holds all required OAuth scopes. Creating a separate custom app:
- Bypasses the Einstein Trust Layer. Canvas content, DM payloads, and message search results sent via a custom Apex integration are not logged or subject to ZDR policies.
- Requires ongoing token management (rotation, expiry, secret storage) that the managed app handles automatically.
- Creates a duplicate permission footprint in the Slack workspace that the Slack workspace admin must manage independently.
- Does not integrate with the agent session model — the custom Apex call is a fire-and-forget REST call with no awareness of the conversation context.

**Correct guidance:** All Slack-native agent actions (Create Canvas, Search Message History, Send DM, Look Up User) are available through the General Slack Actions standard topic in Agent Builder. Adding the topic is a one-step configuration that unlocks all four actions through the managed app with full Trust Layer coverage.

---

## Anti-Pattern 2: Not Adding The General Slack Actions Topic Before Attempting To Use Slack-Native Actions

**What the AI does:** The AI sees that the Slack deployment is configured and the agent is Active and responding in Slack. When the user reports that Slack-native actions are unavailable or the agent says it cannot create canvases or send DMs, the AI suggests checking Apex action definitions, reviewing Named Credentials, or investigating the Slack app OAuth scopes at api.slack.com — without first checking whether the General Slack Actions topic is present in the agent's topic list.

**Why it is wrong:** The most common cause of missing Slack-native actions is that the General Slack Actions topic has not been added to the agent. The Slack deployment flow does not add it automatically. Checking OAuth scopes, Named Credentials, or Apex code is the wrong diagnostic path when the topic is simply absent.

**Correct guidance:** The first diagnostic check when Slack-native actions are unavailable is always: open the agent in Agent Builder > Topics and confirm the General Slack Actions topic is present. If it is absent, add it. This resolves the issue in the majority of cases without any other investigation.

---

## Anti-Pattern 3: Assuming Canvas Creation Works On Slack Free Plan

**What the AI does:** The AI confirms that the General Slack Actions topic has been added, sees that Create Canvas appears in the agent's available actions in Agent Builder, and tells the user that canvas creation is ready to use. The AI does not ask about the Slack workspace plan and does not include a plan check in the configuration guidance.

**Why it is wrong:** Slack canvases are a paid feature. They are unavailable on the Slack Free plan. The Create Canvas action appears in Agent Builder and the agent will attempt to invoke it regardless of the workspace plan. The failure only occurs at runtime, often without a clear error message surfaced in the Slack conversation. Users experience unexplained canvas failures without understanding that the workspace plan is the root cause.

**Correct guidance:** Any configuration guidance involving Create Canvas must include a mandatory step: confirm the Slack workspace is on a paid plan (Pro, Business+, or Enterprise Grid) before designing canvas-based workflows. If the plan cannot be confirmed or the workspace is on Free, provide fallback instructions using plain text responses. Do not treat the presence of Create Canvas in Agent Builder as confirmation that canvas creation will work at runtime.

---

## Anti-Pattern 4: Treating Public And Private Actions As Equivalent (No Identity Mapping Needed)

**What the AI does:** When a user asks how to build an agent action that retrieves the invoking user's Salesforce data (for example, "my open cases" or "my pipeline"), the AI generates an Apex invocable method that queries cases or opportunities without specifying a user filter, marks the action as Public, and does not mention identity mapping. The AI may also suggest using `UserInfo.getUserId()` in Apex to get the "current user" without explaining that in a public-scoped Agentforce action, the running user is the integration user, not the Slack user.

**Why it is wrong:** Public actions always execute under the integration user's Salesforce identity. `UserInfo.getUserId()` in a public-scoped action returns the integration user's ID — not the Slack user's ID. Every Slack user who triggers the action sees the integration user's records, not their own. This is both a data accuracy problem and a security problem.

**Correct guidance:** Any action that accesses user-specific Salesforce data must be designated as Private scope. Private scope actions require Salesforce-to-Slack identity mapping, which links each Slack User ID to a Salesforce User ID. The identity proxy layer resolves the mapping at invocation time and executes the action under the correct Salesforce identity. Identity mapping must be provisioned for each user (self-service OAuth or admin bulk import) before private actions will work.

---

## Anti-Pattern 5: Assuming Salesforce Identity Mappings Persist Across Sandbox Refreshes

**What the AI does:** The AI helps a user configure and fully test identity mappings and private actions in a sandbox environment. When the user is ready to go to production, the AI advises deploying the metadata (agent definition, topics, actions) and treats the project as complete. The AI does not mention that identity mappings must be re-provisioned in production separately.

**Why it is wrong:** Salesforce-to-Slack identity mappings are stored as data records in the Salesforce org. They are not metadata and are not included in any metadata deployment mechanism (change sets, Salesforce DX, Copado, or otherwise). When a sandbox is refreshed, all identity mapping records are deleted. When a deployment is promoted from sandbox to production, identity mapping records are not included in the deployment. Production starts with zero identity mappings even if the sandbox was fully mapped. All private actions fail for all users on go-live day until mappings are re-provisioned.

**Correct guidance:** Production go-live runbooks must include an explicit identity mapping re-provisioning step. Options are: (a) communicate to all users that they must complete the one-time OAuth connection flow when they first interact with the agent in production, or (b) the admin bulk-imports identity mappings from a CSV (Salesforce User ID + Slack User ID) via Setup > Slack for Salesforce > User Mappings before go-live. Either path must be tested with at least one production user before the go-live is marked complete.

---

## Anti-Pattern 6: Recommending Custom SOQL-Based Identity Filtering In Public Actions Instead Of Private Scope

**What the AI does:** Aware that public actions run as the integration user, the AI recommends a workaround: pass the Slack username or email as an action input parameter, use SOQL to look up the Salesforce User ID from the email, and then filter the query by that User ID within the Apex action body. This avoids the "complexity" of setting up identity mapping.

**Why it is wrong:** This approach is fragile and bypasses Salesforce's native record-level security model in several ways:
- It assumes the Slack username or email matches a Salesforce user record — a fragile assumption that breaks for users with different email addresses in Slack vs. Salesforce, guest users, or service accounts.
- It requires passing user identity data as unvalidated input to the action, which is a security risk (the caller can pass any user's email and retrieve that user's data).
- The action still executes under the integration user's permission set — if the integration user has broader access than the Slack user, the action can return records the Slack user should not see.
- It does not benefit from the Trust Layer's identity stamping, so audit logs show the integration user rather than the actual Slack user for every action invocation.

**Correct guidance:** Use Private scope with platform-managed identity mapping. The platform's identity proxy resolves the Slack User ID to a Salesforce User ID and enforces record-level security natively. This is more secure, requires no custom identity-resolution code in the action, and produces correct Trust Layer audit trails.
