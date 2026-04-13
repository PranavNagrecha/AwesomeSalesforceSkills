# Gotchas — Conversational AI Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Agentforce Topics Have No Utterance Training — Description Precision Is the Only Routing Lever

**What happens:** Practitioners familiar with Einstein Bot NLU attempt to improve Agentforce routing by adding example utterances or training phrases to topic descriptions. The platform accepts any prose in the description field, so no error is thrown. Routing does not improve — and may worsen — because the utterance list format wastes description space and provides less precise scope information than well-written prose.

**When it occurs:** Any time a practitioner with Einstein Bot background designs Agentforce topics, or when an AI assistant generates topic descriptions using the Einstein Bot utterance pattern.

**How to avoid:** Write Agentforce topic descriptions as precision prose, not utterance lists. Each description must state: (1) what business function the topic serves, (2) what specific request types are in scope, (3) what is explicitly out of scope. Review all topic descriptions together before deployment to identify overlapping scope language. The only way to improve routing accuracy is to refine description wording and test with adversarial boundary requests.

---

## Gotcha 2: Omni-Channel Capacity Rules Do Not Apply to Agentforce Agents

**What happens:** Architects designing channel routing assume that Agentforce agents are subject to Omni-Channel capacity-based routing the same way human agents are. Capacity rules configured for an Agentforce queue are silently ignored — Agentforce agents do not consume or track capacity units. This means capacity overflow rules (e.g., "if queue is full, route to overflow queue") do not trigger for Agentforce workloads in the same way they do for human agents.

**When it occurs:** When Omni-Channel routing rules include capacity-based conditions targeting Agentforce agent queues, or when an architect tries to implement load balancing across Agentforce agents using Omni-Channel capacity configuration.

**How to avoid:** Do not rely on Omni-Channel capacity management to load-balance or throttle Agentforce agents. Agentforce session concurrency is governed by Agentforce platform limits, not by Omni-Channel capacity objects. Design fallback routing (e.g., fallback to human queue) using queue conditions that do not depend on Agentforce capacity state. Confirm Agentforce session limits for the org's edition and design overflow routing against those platform limits, not against Omni-Channel capacity configuration.

---

## Gotcha 3: Session Context Is Not Automatically Inherited on Einstein Bot to Agentforce Transfer

**What happens:** When an Einstein Bot executes a "Transfer to Agent" action and the target is an Agentforce agent queue, the Agentforce agent starts a new session with no knowledge of the prior bot conversation. Bot variables, collected slot values, verified identity data, and conversation history are not automatically forwarded. The Agentforce agent greets the customer as a new session. The customer must repeat information already collected by the bot.

**When it occurs:** Any Einstein Bot-to-Agentforce handoff where transfer attributes are not explicitly configured on the bot's "Transfer to Agent" action, or where the Agentforce agent has no Action to consume the incoming transfer attributes.

**How to avoid:** Before implementing the transfer, enumerate all bot variables that downstream agents will need (at minimum: verified customer identifier, detected request category, conversation summary). Configure the Einstein Bot's "Transfer to Agent" action to populate named transfer attributes from those variables. On the Agentforce agent, define an Action that reads the transfer attributes and injects them into the agent's working context at session start. Test the full transfer flow end-to-end with a live session and verify that the Agentforce agent's first response reflects the transferred context.

---

## Gotcha 4: Topic Description Overlap Causes Silent Mis-Routing With No Runtime Warning

**What happens:** When two Agentforce topics have descriptions that share overlapping scope language, the Atlas Reasoning Engine routes boundary requests inconsistently. Unlike a configuration error, there is no warning, error log, or alert. The agent produces plausible-looking responses — just to the wrong topic. This means the failure is invisible in error logs and only detectable through targeted adversarial testing.

**When it occurs:** When a practitioner writes topic descriptions independently without reviewing all descriptions together, or when topic descriptions use generic phrases like "account questions" or "financial matters" that apply equally to multiple business functions.

**How to avoid:** After drafting all topic descriptions, review them together in a single pass. Identify any sentence or phrase that could apply to more than one topic — that phrase is an overlap risk. Rewrite overlapping sections to include explicit cross-exclusions ("this topic does not handle X; route those requests to the Y topic"). Run adversarial boundary tests: construct requests that sit at the boundary between each adjacent topic pair and verify routing is consistent across multiple runs.
