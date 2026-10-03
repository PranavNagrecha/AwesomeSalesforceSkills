# Agent Topic Design — Gotchas

Sources: "Quickstart Your Einstein Generative AI Solution" (Generative AI guide, Spring '26 PDF, `generative_ai.pdf`), the Agentforce Developer Guide pages under `developer.salesforce.com/docs/ai/agentforce/guide/`, and the Metadata API Developer Guide (Spring '26), all read on 2026-10-03. The guide's April 2026 note: "agent topics are now called subagents. There are no changes to functionality."

## Gotcha 1: Broad Subagent Names Hide Weak Routing

**What happens:** Names like `Support` or `General Help` give the agent almost no signal. When a user sends a message, the agent compares it to the names and classification descriptions of all topics and picks the most relevant one, so a vague name and description attract unrelated requests.

**When it occurs:** When subagents (called topics before April 2026) are named after departments or catch-all buckets.

**How to avoid:** Name subagents by capability. Write the classification description as 1–3 sentences that say what the topic does and which requests belong in it, as the guide's Parts of a Topic table specifies.

**Source:** Generative AI guide, What are Agents? (topic classification) and Customize Your Agents, Parts of a Topic (Classification Description).

---

## Gotcha 2: The "15" Rule Is About Actions Per Topic, Not Topics Per Agent

**What happens:** Teams cap the number of subagents at fifteen, or add a router only after fifteen, believing that is documented. The documented number is different: "For best performance, we recommend assigning no more than 15 actions to a topic." A topic with twenty actions breaks the real guidance while the topic count looks fine.

**When it occurs:** When sizing rules are copied from community posts instead of the agent limits section.

**How to avoid:** Count actions per topic and keep each at 15 or fewer. Decide on an agent router from overlap between subagents, not from a count. The same limits section says an org can have up to 20 agents.

**Source:** Generative AI guide, Agents Limits and Add an Action to a Topic.

---

## Gotcha 3: Business Rules Written as Instructions Are Not Enforced

**What happens:** An instruction such as "Don't refund an order unless it was within 30 business days" is followed most of the time, not all of the time. The guide states instructions are nondeterministic and rely on an LLM for interpretation.

**When it occurs:** When eligibility, approval limits, or compliance rules are expressed only in topic instructions.

**How to avoid:** Build sensitive or deterministic rules into the action itself (the guide's example is a flow-based action that assesses refund criteria), or use a deterministic Agent Script conditional or transition. Keep instructions for guidance on how to use actions.

**Source:** Generative AI guide, Best Practices for Writing Topic Instructions ("Build sensitive or deterministic business rules into the logic of an action itself, not the topic instructions").

---

## Gotcha 4: Instruction Order Is Not a Sequence

**What happens:** An author lists instructions in the order steps should happen and expects the agent to follow that order. The guide says the LLM doesn't use the visual order of instructions in the Topic Configuration tab to make decisions. The `GenAiPluginInstructionDef` metadata type does carry a `sortOrder` field, which makes it easy to assume order is meaningful.

**When it occurs:** Multi-step procedures written as separate instructions ("First ask for the order number", "Then look up the order").

**How to avoid:** State the sequence and its conditions inside one instruction ("As a first step, ... If x, then y ..."), or enforce it with Agent Script conditionals. Do not rely on `sortOrder` for behavior.

**Source:** Generative AI guide, Best Practices for Writing Topic Instructions; Metadata API Developer Guide, GenAiPluginInstructionDef (`sortOrder`).

---

## Gotcha 5: Handoff Logic Cannot Be Bolted On Later

**What happens:** If escalation rules are missing, the agent keeps trying to do work it should hand off. Escalation is configured in topic-level places: the `canEscalate` flag on `GenAiPlugin` ("Indicates whether this topic is eligible for escalation to a rep"), Agentforce Service Agent topic instructions that decide when to escalate, or the Agent Script `@utils.escalate` utility, which needs an active Omni-Channel connection.

**When it occurs:** When escalation is treated as a separate project after the topics ship.

**How to avoid:** Define handoff criteria inside each subagent design, state what context to collect first, and confirm the Omni-Channel connection exists before relying on `@utils.escalate`.

**Source:** Metadata API Developer Guide, GenAiPlugin (`canEscalate`); Generative AI guide, What are Agents? (ASA uses topic instructions to determine when to escalate); Agentforce Developer Guide, Agent Script Reference: Utils (`utils.escalate`).

---

## Gotcha 6: Action Lists Can Distort Subagent Boundaries

**What happens:** Teams keep a bad subagent because it is the only place certain actions are attached, or they duplicate an action into a copy for every topic.

**When it occurs:** When the action set drives the topic design instead of the capability.

**How to avoid:** Fix the subagent boundary first, then attach actions. The same action can be added to several topics, so there is no need to keep a topic alive just to hold an action, and no need to clone actions.

**Source:** Generative AI guide, Add an Action to a Topic ("An action can be added to multiple topics").

---

## Gotcha 7: Retrieving GenAiPlugin Misses Topics Built Inside an Agent

**What happens:** A team retrieves `GenAiPlugin` to version its topics and gets only asset-library topics. In Winter '26 orgs and later, topics and actions created within a particular agent are retrieved through `GenAiPlannerBundle`. Deploying topic or action metadata to a Summer '25 (API 64.0) org also requires retrieving with Metadata API version 64.0.

**When it occurs:** Source-control setups and CI pipelines written before Winter '26, or deployments between orgs on different releases.

**How to avoid:** Retrieve `GenAiPlannerBundle` for agent-specific topics and `GenAiPlugin` for the asset library. For Agent Script agents, retrieve `AiAuthoringBundle`. Pin the API version to the target org's release when deploying topics or actions.

**Source:** Metadata API Developer Guide, GenAiPlugin and GenAiFunction (Usage sections); AiAuthoringBundle.

---

## Gotcha 8: One Intent Per Utterance

**What happens:** A topic design assumes the agent will handle "cancel my order and update my address" in one turn. The guide says agents generally support one intent per utterance.

**When it occurs:** When topics are drawn around compound journeys.

**How to avoid:** Design each topic for one intent and let follow-up turns or deterministic chaining handle the next step. Test compound utterances explicitly.

**Source:** Generative AI guide, Considerations for Agent Conversations.

---

## Gotcha 9: Adding a Subagent Changes Routing for the Existing Ones

**What happens:** A new subagent pulls utterances away from established ones because its classification description overlaps theirs.

**When it occurs:** Any time a topic is added or a classification description is edited.

**How to avoid:** Keep a routing regression set. `AiEvaluationDefinition` test cases accept a `topic_sequence_match` expectation per utterance, and `conversationHistory` inputs let the test run in the middle of a conversation.

**Source:** Agentforce Developer Guide, Build Tests in Metadata API (AiEvaluationDefinition sample with `topic_sequence_match`).

---

## Gotcha 10: Trust Layer Settings Do Not Vary by Subagent

**What happens:** A review asks for different data masking per subagent. Einstein Trust Layer settings are set in Setup and "are applied to your Salesforce org". In Agent Script, citation and groundedness checks are agent-level switches in the `config` block's `runtime` sub-block.

**When it occurs:** When security requirements are written per topic.

**How to avoid:** Put masking decisions at the org level, put citation and groundedness decisions at the agent level, and use topic boundaries and action filters for per-topic data access.

**Source:** Generative AI guide, Set up Einstein Trust Layer; Agentforce Developer Guide, Agent Script Blocks (Runtime Sub-Block: `citation`, `groundedness`).
