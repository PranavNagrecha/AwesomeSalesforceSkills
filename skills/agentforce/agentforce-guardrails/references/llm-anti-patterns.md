# LLM Anti-Patterns — Agentforce Guardrails

Common mistakes AI coding assistants make when generating or advising on Agentforce Guardrails.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Putting Routing Logic in the Scope Field

**What the LLM generates:** Instructions that add routing exclusions to the topic Scope field, such as:
```
Scope: "Handle IT support questions only. Do not handle HR questions, billing questions, or returns."
```

**Why it happens:** LLMs conflate the Scope field with the Classification Description because both relate to topic boundaries. Training data may include generic descriptions of "topic scope" that blur this distinction. The LLM treats Scope as the all-purpose topic boundary control.

**Correct pattern:**
```
Classification Description:
"Select this topic for IT support questions including password resets, VPN issues,
hardware requests, and software installation. Do not select for HR, billing, or returns."

Scope:
"This topic handles IT support requests for [Company] employees. It initiates password
resets, logs hardware tickets, and provides VPN troubleshooting steps. It does not
provision new accounts — direct account creation requests to IT Admin directly."
```

**Detection hint:** Look for "Do not handle" or "Do not route" language inside a Scope field. Routing exclusions belong in the Classification Description.

---

## Anti-Pattern 2: Using Imperative Prohibition Chains in System Instructions

**What the LLM generates:** System instructions written as a list of "never" and "must not" commands:
```
You must never discuss competitor products. You must never provide pricing information.
You must never give legal or medical advice. Never make promises about refunds.
Always escalate if the user mentions a complaint. Never reveal internal policies.
```

**Why it happens:** LLMs default to imperative safety language because their RLHF training emphasizes negation as a safety signal. This language is appropriate for LLM system prompt hardening in general contexts but is counterproductive in Agentforce agent instructions where the LLM reasoning loop must balance multiple instructions without contradiction.

**Correct pattern:**
```
This agent assists [Company] customers with [scope].

Requests about competitor products, pricing, legal matters, or medical advice receive:
"I'm not able to help with that. Please contact [channel] for assistance."

If the user expresses dissatisfaction or requests to speak with a person, select the
Escalation topic to connect them with a support agent.

Internal policy documents are not shared with customers.
```

**Detection hint:** Count imperative prohibition starters (you must, never, do not, under no circumstances, always). If there are more than two in a single instruction block, refactor to declarative form.

---

## Anti-Pattern 3: Treating Restricted Topics as Keyword Filters

**What the LLM generates:** Short keyword or phrase entries for restricted topics:
```
Restricted Topic: "politics"
Restricted Topic: "religion"
Restricted Topic: "competitor"
Restricted Topic: "legal"
```

**Why it happens:** LLMs draw on keyword-filter analogies (content moderation, URL blocklists) when generating restricted topic entries. The platform's semantic matching is not documented in the same way as keyword filters, so the LLM applies the simpler mental model.

**Correct pattern:**
```
Restricted Topic: "Political opinions, election information, political party positions,
or advice about political candidates and voting."
Refusal: "I'm not able to discuss political topics. Is there something else I can help you with?"

Restricted Topic: "Competitor product comparisons, competitor pricing, or recommendations
to switch to a competing service provider."
Refusal: "I can only help with [Company] services. For competitor information, please visit
their websites directly."
```

**Detection hint:** Restricted topic entries under 10 words are likely too short to be effective. Flag for expansion into complete subject descriptions.

---

## Anti-Pattern 4: Skipping Omni-Channel Verification for the Escalation Topic

**What the LLM generates:** Configuration steps that end at setting the Escalation topic routing destination in the agent setup UI, without verifying the full Omni-Channel path:
```
Steps:
1. Go to Agent Setup > Escalation Topic
2. Set Routing Destination = IT Specialist Queue
3. Add pre-handoff message
4. Save — done.
```

**Why it happens:** LLMs generate configuration steps based on the documented UI fields. The dependency on a fully operational Omni-Channel stack (enabled, queue created, agents assigned, presence configured) is not surfaced in the Agent Setup UI directly, so the LLM omits it.

**Correct pattern:**
```
Steps:
1. Verify Omni-Channel is enabled: Setup > Omni-Channel Settings > Enable
2. Create or identify the target queue: Setup > Queues > [Queue Name]
3. Confirm active agents are assigned to the queue
4. Create or verify routing configuration pointing to the queue
5. In Agent Setup > Escalation Topic: set routing destination, set pre-handoff message
6. TEST END-TO-END in sandbox: initiate conversation, trigger escalation, confirm
   conversation appears in Omni-Channel supervisor console and can be accepted
```

**Detection hint:** Any Escalation topic configuration that does not include an end-to-end test step is incomplete. Flag for addition of verification step.

---

## Anti-Pattern 5: Confusing Action Filters With Topic Filters

**What the LLM generates:** Topic filter instructions that claim to globally block an action:
```
"To prevent the Refund Action from being called in the General Inquiry topic,
add a topic filter on the Refund Action within the General Inquiry topic.
This will prevent the action from being invoked anywhere the user might misuse it."
```

**Why it happens:** LLMs understand per-topic action configuration but conflate topic-level and global filtering because both are described as "filters" in documentation. The distinction between scope of effect (one topic vs. all topics) is frequently missed.

**Correct pattern:**
```
Topic filter: Applied within a specific topic's action configuration. Controls whether
an action is available within that topic. Does NOT prevent the action from being invoked
in other topics where it is also configured.

Action filter: Applied on the action itself (not on the topic). Globally prevents any
topic from invoking the action. Use for actions that must never be accessible to the agent,
regardless of topic context.

For the Refund Action:
- If it should be available in Returns topic only: add action to Returns topic; do NOT
  add it to General Inquiry or any other topic.
- If it should never be accessible to the agent at all: apply an action filter at the
  action level.
```

**Detection hint:** If the recommendation says "add a topic filter to block globally", that is incorrect. Global blocking requires an action filter, not a topic filter.

---

## Anti-Pattern 6: Recommending Trust Layer Configuration as a Guardrail

**What the LLM generates:** Instructions that conflate Einstein Trust Layer content filtering with Agentforce guardrail configuration, advising practitioners to "configure the Trust Layer to block prohibited topics" or "use PII masking to prevent data leakage through agent responses."

**Why it happens:** Both Trust Layer and Agentforce guardrails are described as safety/governance controls for AI agents. LLMs blend these into a single configuration surface because they are conceptually related. Trust Layer is a separate infrastructure concern (prompt defense, PII masking in LLM calls, toxicity filtering at the API level). Agentforce guardrails are agent-level behavioral configuration.

**Correct pattern:**
```
Agentforce guardrails (this skill): topic Scope, system instructions, restricted topics,
action filters, Escalation topic, Instruction Adherence monitoring.
These control agent behavior at the topic/action/instruction level.

Einstein Trust Layer (separate concern): controls the LLM API call pipeline,
including PII masking, toxicity filtering, and zero-data-retention enforcement.
Configure Trust Layer in Setup > Einstein > Einstein Trust Layer.

For behavioral guardrails (what the agent will and will not do), use this skill.
For data privacy and LLM API safety controls, use the Trust Layer setup guides.
```

**Detection hint:** Any recommendation to configure "Trust Layer" as a step in agent guardrail setup is a scope bleed. Flag and redirect to the correct configuration surface.
