# Gotchas — Einstein Bots to Agentforce Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Migration Tool Only Works with Enhanced Bots — Classic Bots Are Not Supported

**What happens:** When a practitioner opens Setup > Einstein Bots for a Classic/Legacy bot and looks for the "Create AI Agent" option, it does not appear. The migration tool is gated on Enhanced Bot infrastructure. Classic bots have no automated migration path.

**When it occurs:** Any time a team plans a migration assuming the tool is universally available and only discovers the limitation when they attempt it — often close to the Feb 14 2026 deadline.

**How to avoid:** Confirm the bot type before planning a migration timeline. In Setup > Einstein Bots, the bot list shows the type column. If the bot is Classic, budget time for a manual migration: dialog inventory, manual Topic scaffolding in Agentforce Builder, and Action implementation for each dialog step. Classic bots that need to migrate before Feb 14 2026 should start the manual process immediately — it takes significantly longer than the tool-assisted path.

---

## Gotcha 2: Generated Topic Descriptions Are Not LLM-Routing-Ready

**What happens:** The migration tool generates Topics with descriptions that match the original Dialog names (e.g., "Order Status", "Password Reset"). These one-phrase descriptions are ambiguous to the LLM routing model, causing incorrect topic selection — especially when multiple topics have overlapping intent vocabulary.

**When it occurs:** Immediately after activating the generated draft agent. The problem surfaces during Conversation Preview when test phrases route to the wrong Topic.

**How to avoid:** Treat every generated Topic description as a placeholder, not a finished output. Before testing, rewrite each description as a complete routing instruction: include what the topic covers, what it does not cover, and at least one example intent in sentence form. Topics with boundary overlap (e.g., Order Status vs Return Request) must have explicit negative scope clauses to prevent the LLM from resolving ambiguity incorrectly.

---

## Gotcha 3: Handoff Latency Is Perceptible and Differs from Scripted Bot Response Time

**What happens:** After migration, users and QA testers report that the agent feels "slow" or "unresponsive" compared to the original bot. The wait time before the first agent response is noticeably longer.

**When it occurs:** This is inherent to Agentforce's LLM planning model. Before executing any Action, the reasoning engine runs a planning cycle — it decides which Topic applies, selects the appropriate Action, prepares the prompt, and waits for the LLM response. Classic and Enhanced bots execute deterministic dialog steps in milliseconds. LLM planning typically adds several hundred milliseconds to a few seconds depending on model load and prompt complexity.

**How to avoid:** Do not assume the existing SLA for bot response time applies to the migrated Agentforce agent. Measure actual LLM planning latency in a sandbox before committing to a go-live date. Communicate the latency characteristic to stakeholders and QA teams so they can adjust acceptance criteria. For extremely latency-sensitive flows (e.g., authentication steps, form validation), consider keeping those dialogs in the Enhanced Bot under the hybrid pattern rather than migrating them to Agentforce Actions.

---

## Gotcha 4: MessagingSession Context Fields Must Be Explicitly Populated — They Are Not Automatic

**What happens:** Teams implementing the hybrid handoff pattern find that the Agentforce agent has no context from the bot portion of the conversation. Variables the bot collected (authenticated user ID, case number, slot values) are not available to the agent.

**When it occurs:** When the handoff is configured but the bot dialog does not include an explicit Flow step that writes values to `MessagingSession` custom fields before the session transitions.

**How to avoid:** Add a dedicated Flow step at the end of every bot dialog that should hand off to Agentforce. The Flow must explicitly write all relevant context values to `MessagingSession` custom fields before the bot session ends. These fields must already exist on the `MessagingSession` object (create them via Setup > Object Manager). Then implement a "Get Session Context" Action in the Agentforce agent that reads these fields at the start of the agent session. Without both sides of this handshake — bot writes, agent reads — the context is lost.

---

## Gotcha 5: Deploying BotVersion Without GenAiPlannerBundle Produces a Chatbot, Not an Agent

**What happens:** A migration team deploys their Agentforce agent metadata to production. The bot appears active and responds to messages — but it does not perform reasoning, does not route to Topics, and answers with generic scripted responses instead of LLM-driven replies.

**When it occurs:** When the deployment package includes `Bot` and `BotVersion` but omits `GenAiPlannerBundle`. This commonly happens when the team manually builds the deployment package without understanding the full metadata dependency graph.

**How to avoid:** Always retrieve and deploy the complete agent metadata bundle: `Bot`, `BotVersion`, `GenAiPlannerBundle`, `GenAiPlugin` (Topics), and `GenAiFunction` (Actions). Use `sfdx force:source:retrieve` with an explicit manifest that lists all five component types. Validate in the target org by confirming the bot appears in Setup > Agentforce Agents (not just Setup > Einstein Bots) — only agents with `GenAiPlannerBundle` appear in the Agentforce Agents list.
