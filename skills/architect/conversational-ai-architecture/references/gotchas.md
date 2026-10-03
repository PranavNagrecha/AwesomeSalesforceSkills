# Gotchas — Conversational AI Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Sources are named in each gotcha. "Generative AI guide" means *Quickstart Your Einstein Generative AI Solution* (`generative_ai.pdf`, Spring '26 edition served under the 262 release path). Claims no fetched source confirms carry an inline `UNVERIFIED (date):` marker.

## Gotcha 1: Agentforce Topics Have No Training Step; the Classification Description Drives Routing

**What happens:** Practitioners familiar with Einstein Bot NLU try to improve Agentforce routing by pasting example utterances into the topic description. The platform accepts any prose, so no error is thrown, and routing does not improve the way retraining a bot model would. The Generative AI guide ("Agent Topics", "Parts of a Topic") says the agent compares the user utterance to the names and classification descriptions of all assigned topics and picks the best match. It defines the classification description as 1–3 sentences describing what the topic does and which requests belong to it. A long utterance list in that field dilutes the routing text.

Correction (2026-10-03): earlier versions of this skill said writing utterances for topics "produces no effect". The Metadata API Developer Guide (`GenAiPlugin`) defines an `aiPluginUtterances` field: "A list of utterances that can be used to pick a topic during runtime." So example utterances have a place. It is that field, not the classification description, and there is still no training or versioned model.

**When it occurs:** Any time a practitioner with Einstein Bot background designs Agentforce topics, or when an AI assistant generates topic descriptions using the Einstein Bot utterance pattern.

**How to avoid:** Split the content across the fields the platform defines: a 1–3 sentence classification description (`description`), a job description (`scope`), single-guideline instructions (`genAiPluginInstructions`), and, if wanted, sample utterances (`aiPluginUtterances`). Review all classification descriptions together before deployment to find overlapping language, then test with adversarial boundary requests.

---

## Gotcha 2: Omni-Channel Capacity Rules Do Not Apply to Agentforce Agents

**What happens:** Architects designing channel routing assume that Agentforce agents are subject to Omni-Channel capacity-based routing the same way human agents are. UNVERIFIED (2026-10-03): the claim that capacity rules configured for an Agentforce queue are silently ignored, and that Agentforce agents do not consume or track capacity units, appears in no fetched source (Generative AI guide, Omni-Channel Developer Guide table of contents, Object Reference). Treat it as a field observation to confirm in a sandbox. If it holds, capacity overflow rules (for example "if queue is full, route to overflow queue") do not trigger for Agentforce workloads the way they do for human agents.

**When it occurs:** When Omni-Channel routing rules include capacity-based conditions targeting Agentforce agent queues, or when an architect tries to load-balance across Agentforce agents with Omni-Channel capacity configuration.

**How to avoid:** Do not rely on Omni-Channel capacity management to load-balance or throttle Agentforce agents until a sandbox test proves it works. Design fallback routing to a human queue on conditions that do not depend on Agentforce capacity state. The Metadata API `Bot` type offers `defaultOutboundFlow` (API 65.0 and later), described as a fallback escalation behavior when the primary agent escalation behavior is not available.

---

## Gotcha 3: Session Context Is Not Automatically Inherited on Einstein Bot to Agentforce Transfer

**What happens:** When a conversation moves from an Einstein Bot to an Agentforce agent, the agent does not see bot variables, collected slot values, or verified identity data unless the design puts them somewhere the agent reads. The customer then repeats information the bot already collected.

The documented carrier is the agent's context variables. The Metadata API Developer Guide (`Bot`, `ConversationContextVariable`, `ConversationContextVariableMapping`) defines context variables that map a channel (`messageType`, for example `EmbeddedMessaging` or `WhatsApp`) to a field on `MessagingSession`, `MessagingEndUser` or `LiveChatTranscript`. The `includeInPrompt` flag (API 63.0 and later) decides whether the variable is injected into the prompt sent to the model. The default variables `Id`, `EndUserId` and `EndUserLanguage` always appear. UNVERIFIED (2026-10-03): earlier text described a bot "Transfer to Agent" action that passes named attributes to an Agentforce Action; no fetched source documents that mechanism.

**When it occurs:** Any Einstein Bot-to-Agentforce handoff where the bot never writes its collected values to a session field, or where the agent's context variables do not map that field with `includeInPrompt` set.

**How to avoid:** Enumerate the values downstream agents need (at minimum a verified customer identifier, a request category, and a conversation summary). Have the bot write them to custom fields on `MessagingSession`. Define matching context variables on the Agentforce agent, map them to those fields for each channel, and set `includeInPrompt` only on the ones the agent needs. Test the full transfer end to end and check that the agent's first response reflects the transferred context.

---

## Gotcha 4: Topic Description Overlap Causes Silent Mis-Routing With No Runtime Warning

**What happens:** When two topics have classification descriptions with overlapping scope language, boundary requests route inconsistently. There is no warning, error log, or alert. The agent produces plausible-looking answers from the wrong topic. The Generative AI guide also notes that agents in general support one intent per utterance, so a message that spans two topics lands in one of them.

**When it occurs:** When topic descriptions are written independently without reviewing all of them together, or when they use generic phrases like "account questions" that apply to several business functions.

**How to avoid:** Review all classification descriptions together in one pass. Remove any phrase that could apply to more than one topic, and put cross-exclusions in the topic `scope` ("You aren't able to change payment methods"). Run adversarial boundary tests for each adjacent topic pair and repeat them after every description change.

---

## Gotcha 5: Only the Standard Escalation Topic Can Hand a Conversation to a Human

**What happens:** An architect designs a custom "Talk to an expert" topic that should transfer to a live rep. It never transfers. The Generative AI guide ("Agent Topic: Escalation") says the Escalation topic that ships with Agentforce Service Agents routes conversations through the associated outbound Omni Flow, which only the standard Escalation topic can invoke. No other standard topic can route to live service representatives, and a custom topic cannot be configured to do so. The `GenAiPlugin` metadata type carries a `canEscalate` flag for this eligibility.

**When it occurs:** Hybrid designs that want several escalation paths (billing expert, fraud team), or designs that rename or replace the Escalation topic.

**How to avoid:** Keep one Escalation topic and customize its classification description and instructions (the guide allows escalating on, for example, a return request). Put routing differences (which queue, which skill) in the outbound Omni Flow, not in extra topics. Add custom actions that create or update a Case before transfer. The guide warns against attaching standard actions to the Escalation topic because they have broad data access not intended for external use.

---

## Gotcha 6: Changing a Live Agent Interrupts Conversations

**What happens:** The Generative AI guide ("Create a Custom Topic") tells you to deactivate an active agent before adding a topic. Its "Considerations for Agents" says deactivating an agent interrupts ongoing conversations without notifying users, and that versioning agents is not supported in that edition of the guide.

**When it occurs:** A team tunes topic descriptions in production during business hours, or treats topic edits as a no-downtime config change.

**How to avoid:** Make topic and action changes in a sandbox and deploy them as metadata during a low-traffic window. Plan the window as a channel outage and point the channel's fallback at a human queue while the agent is inactive. Record each change so that adversarial routing tests can be rerun after deployment.

---

## Gotcha 7: Topic Instructions Are Not a Control

**What happens:** A design puts "Never issue a refund over 30 days" or "Always verify identity before showing balances" in topic instructions. The Generative AI guide ("Parts of a Topic", "Best Practices for Writing Topic Instructions") says instructions are nondeterministic and rely on an LLM for interpretation, so they should not hold sensitive or deterministic business rules. The guide's example moves a refund rule into a flow-based agent action.

**When it occurs:** Regulated flows (identity verification, disclosures, eligibility checks) designed as prompt text.

**How to avoid:** Put deterministic rules inside the action (a flow or Apex invocable action that refuses to act when the rule fails). For flows that must be explainable end to end, the guide lists regulated industries that need explainable processes and deterministic conversation flows as cases where Einstein Bots fit better. That is the basis for the hybrid pattern in this skill.

---

## Gotcha 8: Channel and Cloud Availability Constrain the Agent Type

**What happens:** The Generative AI guide ("Considerations for Agents") says only Agentforce Service Agent can connect to enhanced Messaging channels and Bring Your Own Channel, and that agents are not available for Government Cloud. A design that puts an employee-type agent on a customer messaging channel, or proposes Agentforce for a Government Cloud org, cannot be built.

**When it occurs:** Early architecture choices made before the channel inventory and org type are confirmed.

**How to avoid:** Confirm the org type and the exact channels first (see Questions to Ask). For Government Cloud orgs, keep the design on Einstein Bots and human routing and record Agentforce as unavailable. For customer messaging, specify the Agentforce Service Agent type (`Bot.agentType` = `AgentforceServiceAgent`, `Bot.type` = `ExternalCopilot` in the Metadata API).

---

## Gotcha 9: Context Passed to the Agent Is Not Masked

**What happens:** The Generative AI guide ("Trust and Agents") says data masking through the Einstein Trust Layer is disabled for agents to improve performance and accuracy. Data the agent accesses, including PII, is protected in transit and covered by zero data retention at the external LLM provider, but it reaches the model unmasked.

**When it occurs:** A bot-to-agent handoff that sets `includeInPrompt` on every context variable, including date of birth, account numbers, or verification answers.

**How to avoid:** Pass identifiers and categories, not secrets. Set `includeInPrompt` only on variables the agent needs to reason with, and let actions look up sensitive fields server-side under the agent user's access. The agent user holds a permission set with the Agent User license (for a Service Agent, the Agentforce Service Agent User permission set), so scope that user's object and field access to the minimum.

---

## Gotcha 10: Topic Metadata Moved Between Types in Winter '26

**What happens:** A deployment pipeline retrieves `GenAiPlugin` components and misses the topics that were created inside an agent. The Metadata API Developer Guide (`GenAiPlugin`, Usage) says that in Winter '26 orgs and later, topics created within a particular agent are retrieved with `GenAiPlannerBundle`, while `GenAiPlugin` retrieves asset-library topics. It also says to retrieve with API version 64.0 when deploying topic or action metadata to a Summer '25 (64.0) org.

**When it occurs:** Promoting an agent from a Winter '26+ sandbox to an org on an older release, or reusing a pre-Winter '26 `package.xml`.

**How to avoid:** List both `GenAiPlannerBundle` and `GenAiPlugin` (and `GenAiFunction` for actions, plus `Bot`) in the manifest. Pin the retrieve API version to the target org's version when releases differ.
