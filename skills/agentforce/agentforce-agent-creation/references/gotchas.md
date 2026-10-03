# Gotchas: Agentforce Agent Creation

Non-obvious platform behaviours that cause real production problems. Gotchas 1 to 5 are carried from the earlier version; each now says what an official source supports and marks the rest UNVERIFIED. Gotchas 6 to 13 are new and cited.

---

## Gotcha 1: The agent API name deserves the care of an object API name

**What happens:** A placeholder API name such as `Test_Agent_1` reaches production, and changing it means rebuilding the agent.

**When it occurs:** The API name is chosen before the naming convention is settled.

**How to avoid:** Agree the API name before creating the agent. It must be unique in the org, at most 80 characters, start with a letter, use only letters, digits and underscores, and not end with or double an underscore. The label can be friendlier.

**Source:** Agentforce Developer Guide, Agent Script Blocks (`developer_name` rules). UNVERIFIED (2026-10-03): the earlier claim that the API name can never be changed after creation; no source read states it.

---

## Gotcha 2: Activation is a separate step in every org

**What happens:** The agent is deployed to production but nobody can reach it, and the team debugs channels and permissions first.

**When it occurs:** The release runbook deploys metadata and stops.

**How to avoid:** Add an explicit activation step to every promotion (`sf agent activate --api-name ... --version N`). Only one version can be active; activating a committed version deactivates the version that was active.

**Source:** Agentforce Developer Guide, Manage an Agent ("Activating an agent makes it available to users on the channels that your agent is connected to") and Troubleshoot Agentforce DX Issues ("Add an agent activate step before running tests in your CI script"); Customizing User Interface Using Custom Lightning Types example ("The currently active version (if any) is automatically deactivated"); Salesforce CLI `sf agent activate --help`. UNVERIFIED (2026-10-03): that a deployed agent always arrives inactive; the sources show activation as separate, not the arrival state.

---

## Gotcha 3: The web chat deployment is its own published artefact

**What happens:** The agent is updated and activated, but visitors still see old behaviour or no chat at all.

**When it occurs:** The embedded service deployment was never created, never published, or was published before the channel pointed at the active agent.

**How to avoid:** After the agent is active and the channel routes to it, create and publish the embedded service deployment and embed it on the site, either an external website or an Experience Builder site. Re-publish after channel changes.

**Source:** Agentforce Developer Guide, Multi-Surface Example: Build and Deploy an Enhanced Chat Agent ("To surface the chat to your customers, create and publish an embedded service deployment, and then embed it on your site"). UNVERIFIED (2026-10-03): the earlier statements that every agent change needs a republish and that propagation takes up to 10 minutes.

---

## Gotcha 4: Trust Layer masking does not apply to agents

**What happens:** Record data, PII included, reaches the model unmasked even though masking is configured for prompt templates.

**When it occurs:** The team assumes Trust Layer masking covers agent prompts.

**How to avoid:** Limit what the agent can read through the agent user's permissions and the actions' field lists. Review the Trust Layer for what it does provide (zero-data retention, toxicity detection, audit), not for masking.

**Source:** Generative AI guide (Spring '26), Trust and Agents: "Data masking through the Einstein Trust Layer is disabled to improve the performance and accuracy of agents." This now grounds the earlier gotcha, which said masking does not apply "by default".

---

## Gotcha 5: Subagent and action design comes before activation

**What happens:** An agent goes live with template subagents and no working actions; it routes poorly and answers "I can't help with that".

**When it occurs:** Creating the agent shell is treated as the project.

**How to avoid:** Finish at least one subagent with a clear classification description and a tested action before activating. When generating an authoring bundle, pass a detailed agent spec; without one you get boilerplate blocks with no subagents.

**Source:** Generative AI guide, Agent Action Assignments ("An agent uses only the actions that are assigned to it"); Agentforce Developer Guide, Troubleshoot Agentforce DX Issues ("Pass an agent spec file with the --spec flag. Without a spec, the command generates a default template").

---

## Gotcha 6: Messaging channel links on a Bot are not deployable

**What happens:** A Bot deployed from a sandbox arrives without its messaging channels, and the channel list in the retrieved XML is empty.

**When it occurs:** The team expects Metadata API to carry channel assignments.

**How to avoid:** Configure messaging channels in the target org's UI as a runbook step after deployment.

**Source:** Metadata API reference, Bot, ConversationDefinitionChannelProvider: "To add, edit, or remove a messaging channel, you must use the UI. If you deploy a bot with messaging channel providers, those providers aren't visible in Metadata API."

---

## Gotcha 7: Channel choice is limited by agent type

**What happens:** A team designs an Agentforce (Default) employee agent for an enhanced Messaging channel or an Agent API client, and it cannot be connected.

**When it occurs:** Channel is chosen before agent type.

**How to avoid:** Choose the agent type from the channel. Only Agentforce Service Agent connects to enhanced Messaging channels and Bring Your Own Channel. Agent API does not support agents of type Agentforce (Default).

**Source:** Generative AI guide, Considerations for Agents ("Currently, only Agentforce Service Agent can connect to enhanced Messaging channels and Bring Your Own Channel"); Agentforce Developer Guide, Agent API Considerations ("The Agent API isn't supported for agents of type Agentforce (Default)").

---

## Gotcha 8: Promotion rules for agent metadata are strict

**What happens:** A deploy fails on missing Bot components, a single-version deploy fails in a fresh org, or a wildcard manifest times out.

**When it occurs:** The manifest is improvised.

**How to avoid:** Deploy the full agent the first time. Use `BotVersion` for later single-version deploys. Include both `AiAuthoringBundle` and `Bot`/`BotVersion` for committed agents. Name Apex classes, flows and prompt templates instead of using wildcards. Keep source and target versions matched, or future deployments are blocked.

**Source:** Agentforce Developer Guide, Define Agent Metadata (v67 and Earlier), Troubleshoot Agentforce DX Issues ("A committed agent requires both AiAuthoringBundle and Bot/BotVersion to deploy") and Use Metadata to Move an Agent to a New Org ("the agents in both your source and target orgs must match or future deployments will be blocked").

---

## Gotcha 9: Publishing an agent does not deploy its Apex or flows

**What happens:** An action fix is published with the agent, but the preview still shows the old behaviour.

**When it occurs:** The team expects the authoring bundle publish to carry the reference actions.

**How to avoid:** Deploy Apex classes and flows first, then publish the authoring bundle.

**Source:** Agentforce Developer Guide, Troubleshoot Agentforce DX Issues: "Publishing an authoring bundle doesn't deploy Apex classes or flows, which are separate metadata types."

---

## Gotcha 10: Editing a live agent drops live conversations

**What happens:** An admin deactivates the agent to add an action; every open conversation gets the system error message, and users are not told why.

**When it occurs:** Changes are made directly on the active agent.

**How to avoid:** Make changes on a new version and activate it when tested. If you must deactivate, do it in a quiet window.

**Source:** Generative AI guide, Activate or Deactivate Your Agent ("To make changes to an agent, such as adding or removing topics or actions, deactivate it"; "Deactivating an agent interrupts any ongoing user conversations. Users aren't notified"; "To make and test changes to your agent without taking the active version out of production, create multiple versions of an agent").

---

## Gotcha 11: Org and license limits cap how many agents you can create

**What happens:** The guided setup does not offer an agent type the team planned for, or a new agent cannot be created.

**When it occurs:** The org reaches the agent limit or a license-limited agent type is used up.

**How to avoid:** Inventory agents before planning a new one. The documented limit is 20 agents, of which one can be the default Agentforce agent, and license-limited types are disabled in guided setup when the license count is reached.

**Source:** Generative AI guide, Agents Limits.

---

## Gotcha 12: System messages have limits and are not translated

**What happens:** A long welcome message is rejected, or French-speaking users get an English welcome.

**When it occurs:** System messages are written like marketing copy, or language settings are expected to translate them.

**How to avoid:** Keep the welcome message under 800 characters. Introduce the agent as an AI assistant. Add one manual translation per system message where needed. Only Agentforce (Default) and Agentforce Service Agent have system messages.

**Source:** Generative AI guide, Define System Messages ("There's an 800 character limit on welcome messages"; introduce the agent "as a bot or AI assistant") and Considerations for Agents ("System messages ... aren't translated into other languages. You can manually add one translation for each system message").

---

## Gotcha 13: Agent template packaging does not support Agent Script agents

**What happens:** A team plans to distribute a new agent as a packaged template and the packaging step fails.

**When it occurs:** The agent was built from an Agent Script authoring bundle.

**How to avoid:** Choose the distribution method before choosing the build method, and check current Agentforce DX release notes.

**Source:** Agentforce Developer Guide, Troubleshoot Agentforce DX Issues: "Agent template packaging currently doesn't support agents that use Agent Script as their blueprint."
