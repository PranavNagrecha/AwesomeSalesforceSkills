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
   - Agent User: select the dedicated agent user, or create one with New Agent User.
     It needs a permission set that carries the Agent User license.
   - Enable Enhanced Event Logs checkbox.
4. Add topics and actions in Agentforce Builder.
5. Review Agent Instructions for tone, constraints, and fallback wording.
6. Click Activate (upper right) — agent moves to Active state.
7. Setup > Embedded Service Deployments > New (Messaging for In-App and Web).
   - Name and configure the deployment.
   - Set routing rule: Route To = Agentforce Service Agent > CC Support Agent.
8. In Experience Builder: add Embedded Messaging component to target page.
9. Publish the Experience Cloud site.
10. Test with a guest user. (UNVERIFIED 2026-10-03: the earlier "wait up to 10 minutes
    for CDN propagation" figure.)
```

**Why it works:** Activation happens before channel publishing. The Embedded Service deployment captures the Active agent state at publish time. Reversing the order leaves the deployment pointing at a Draft agent.

---

## Example 2: Promoting An Agent From Sandbox To Production

**Context:** A team builds and tests an Agentforce agent in a Full Sandbox. The agent is Active, working, and ready to go to production. After deploying metadata via Salesforce CLI, production users cannot find the agent.

**Problem:** Nobody activated the agent in production. Activation is a separate step in every org, and the runbook stopped at the deploy. UNVERIFIED (2026-10-03): the earlier statement that metadata deployment never carries activation state; the sources read show activation as its own command, not the arrival state.

**Solution:**

```text
Sandbox preparation:
- Confirm agent is functioning in sandbox (Active state, topics tested).
- Retrieve metadata bundle using Salesforce CLI:
    sf project retrieve start --metadata Bot,BotVersion,GenAiPlannerBundle,GenAiPlugin,GenAiFunction

Deploy to production:
- sf project deploy start --metadata Bot,BotVersion,GenAiPlannerBundle,GenAiPlugin,GenAiFunction

Post-deployment activation in production (must be in the release runbook):
1. sf agent activate --api-name <AgentApiName> --version <N> --target-org prod
   (or open the agent in Agentforce Builder and click Activate).
2. Confirm the agent user is the production user (string replacement or manual update).
3. Republish any Embedded Service Deployment that references the agent.
4. Smoke test with Conversation Preview or `sf agent test run` before declaring the release complete.
```

**Why it works:** Treating activation as a deliberate production step rather than an assumed carry-over prevents silent failures. It also gives the release team a clean gate for go/no-go in production.

---

## Anti-Pattern: Typing The Agent User Name Instead Of Using The Dropdown

**What practitioners do:** During agent creation, they type the agent user's name directly into the Agent User field rather than selecting it from the dropdown picker.

**What goes wrong:** UNVERIFIED (2026-10-03): the earlier report that a typed user name passes validation but leaves actions failing at runtime. No source read describes this failure. What is documented is that the agent user determines what the agent can access, so a wrong or under-permissioned user makes actions fail.

**Correct approach:** Use the Agent User dropdown: select the dedicated user or create one with New Agent User. If the user does not appear, verify it exists and holds a permission set that carries the Agent User license. In Agent Script, set `default_agent_user` in the access block to the user's username.
