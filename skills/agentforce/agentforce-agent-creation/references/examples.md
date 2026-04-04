# Examples — Agentforce Agent Creation

## Example 1: Creating A Service Agent With Embedded Service Deployment

**Context:** A Service Cloud team wants to add a customer-facing chat agent to their Experience Cloud portal. They need to create the agent from scratch, configure it for web chat, and make it available to guests.

**Problem:** The team activates the agent in Setup but visitors to the portal see no chat widget. The deployment was published before the agent was activated, so the channel does not surface the active agent.

**Solution:**

```text
Correct sequence:
1. Setup > Einstein Setup — confirm Einstein is On.
2. Setup > Agentforce Agents — confirm Agentforce toggle is Active.
3. Setup > Agentforce Agents > +New Agent > Agentforce Service Agent template.
   - Label: CC Support Agent
   - API Name: CC_Support_Agent  (immutable — choose carefully)
   - Role: "Customer service representative for Coral Cloud, helping guests
            with reservations, session bookings, and experience inquiries."
   - Agent User: select EinsteinServiceAgent User from dropdown (do not type).
   - Enable Enhanced Event Logs checkbox.
4. Add topics and actions in Agentforce Builder.
5. Review Agent Instructions for tone, constraints, and fallback wording.
6. Click Activate (upper right) — agent moves to Active state.
7. Setup > Embedded Service Deployments > New (Messaging for In-App and Web).
   - Name and configure the deployment.
   - Set routing rule: Route To = Agentforce Service Agent > CC Support Agent.
8. In Experience Builder: add Embedded Messaging component to target page.
9. Publish the Experience Cloud site.
10. Wait up to 10 minutes for CDN propagation before testing with a guest user.
```

**Why it works:** Activation happens before channel publishing. The Embedded Service deployment captures the Active agent state at publish time. Reversing the order leaves the deployment pointing at a Draft agent.

---

## Example 2: Promoting An Agent From Sandbox To Production

**Context:** A team builds and tests an Agentforce agent in a Full Sandbox. The agent is Active, working, and ready to go to production. After deploying metadata via Salesforce CLI, production users cannot find the agent.

**Problem:** The agent arrives in production in Inactive state. Metadata deployment never carries activation state between orgs. The team did not plan for a manual activation step in the production release runbook.

**Solution:**

```text
Sandbox preparation:
- Confirm agent is functioning in sandbox (Active state, topics tested).
- Retrieve metadata bundle using Salesforce CLI:
    sf project retrieve start --metadata Bot,BotVersion,GenAiPlannerBundle,GenAiPlugin,GenAiFunction

Deploy to production:
- sf project deploy start --metadata Bot,BotVersion,GenAiPlannerBundle,GenAiPlugin,GenAiFunction

Post-deployment activation in production (manual step — must be in release runbook):
1. Setup > Agentforce Agents — find the agent, status shows Inactive.
2. Open the agent in Agentforce Builder.
3. Click Activate.
4. Republish any Embedded Service Deployment that references the agent.
5. Smoke test with Conversation Preview before declaring the release complete.
```

**Why it works:** Treating activation as a deliberate production step rather than an assumed carry-over prevents silent failures. It also gives the release team a clean gate for go/no-go in production.

---

## Anti-Pattern: Typing The Agent User Name Instead Of Using The Dropdown

**What practitioners do:** During agent creation, they type the EinsteinServiceAgent User name directly into the Agent User field rather than selecting it from the dropdown picker.

**What goes wrong:** The agent passes setup validation but the agent user is misconfigured. At runtime, agent actions fail because the system user context is not correctly established. The error is not immediately obvious — the agent may appear active but silently fail to complete tasks or retrieve records.

**Correct approach:** Always use the Agent User dropdown picker. Navigate to Setup > Agentforce Agents > New Agent, scroll to the Agent User field, and select the user from the list. If the EinsteinServiceAgent User does not appear, verify the user exists and has the Einstein Agent User permission set assigned before returning to agent setup.
