# Gotchas — Agentforce Guardrails

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Classification Description Drives Routing — Scope Field Does Not

**What happens:** Practitioners write topic boundary rules in the Scope field expecting them to prevent certain user inputs from routing to that topic. The routing ignores the Scope field entirely. The LLM reads Classification Description at routing time and Scope at action-planning time. These are two distinct processing stages. A Scope field that says "Do not handle billing" has zero effect on whether billing questions are routed to that topic.

**When it occurs:** Any time a practitioner adds routing intent ("do not route X here") to the Scope field instead of the Classification Description. The mistake is invisible until conversation logs show misrouted conversations. Because the Scope field still influences action planning, the agent may partially refuse some requests in a topic it should never have been in — leading to inconsistent behavior that is hard to diagnose.

**How to avoid:** Keep the two fields strictly separated in purpose. Classification Description = routing instructions (which user intents belong here; which explicitly do not). Scope = post-selection behavioral constraints (what the agent will and will not do once in this topic). Audit all topics and check that no routing language has bled into Scope fields and no behavioral language has been omitted from Scope.

---

## Gotcha 2: Escalation Topic Requires Omni-Channel — Silent Failure Without It

**What happens:** The Escalation topic appears to fire correctly in the agent UI — the pre-handoff message is displayed to the user — but no conversation ever appears in the Omni-Channel supervisor console. No error is surfaced to the user or in standard agent logs. The conversation simply goes nowhere after the pre-handoff message.

**When it occurs:** When the Escalation topic's routing destination (queue or flow) is not configured, when the assigned Omni-Channel queue has no active agents or capacity, or when Omni-Channel itself is not enabled in the org. This often happens when teams configure the agent before completing Omni-Channel setup, or when the queue is created but agent presence is not tested.

**How to avoid:** Test the escalation path end-to-end in sandbox: initiate a conversation, trigger escalation, confirm the conversation appears in the Omni-Channel supervisor dashboard and can be accepted by a test agent. Do not rely on the presence of the Escalation topic configuration alone as confirmation of a working escalation path. Include Omni-Channel queue capacity in the go-live checklist.

---

## Gotcha 3: Imperative Instruction Keywords Degrade Reasoning Loop Reliability

**What happens:** System instructions and topic Scope fields that use chains of imperative prohibitions (must, never, always, do not, you must not, under no circumstances) cause the LLM reasoning loop to produce contradictory internal self-instructions. The agent enters a state where it repeatedly re-evaluates the same conversation turn without producing output, eventually timing out. To the user this appears as the agent stalling or returning an error. In Agentforce Analytics this appears as elevated turn failure rates.

**When it occurs:** When instructions contain three or more imperative prohibitions applied to the same decision point, or when two instructions conflict (e.g., "always escalate if the user is frustrated" and "never escalate without prior troubleshooting steps"). Also occurs when practitioners copy security policy language (written for humans) directly into agent instructions.

**How to avoid:** Rewrite imperative prohibitions as declarative boundary statements. Instead of "Never provide pricing information. You must not discuss competitor products. Do not give legal advice." write: "This agent addresses [scope] only. Requests about pricing, competitors, or legal matters receive: '[refusal response].'" Declarative statements describe desired outcome state rather than commanding negative actions, which the LLM reasoning loop handles more stably.

---

## Gotcha 4: Restricted Topics Are Subject Descriptions, Not Keyword Filters

**What happens:** Practitioners add short keyword strings (e.g., "politics", "competitor") as restricted topic entries expecting keyword-level matching. Short keyword entries produce high false-positive rates (blocking innocuous uses of the word) and also miss paraphrased prohibited inputs. For example, a restricted topic entry of "competitor" may block a customer saying "I used to be a customer of yours but switched" while missing "How does your plan compare to Verizon?".

**When it occurs:** When restricted topic entries are written as keywords or short phrases rather than subject descriptions. The restricted topic matching is semantic, not purely lexical, but the quality of matching depends on how well the entry describes the prohibited subject.

**How to avoid:** Write restricted topic entries as complete subject descriptions: "Questions about competitor pricing, promotions, plan comparisons, or recommendations to switch to a different provider." Test with paraphrased and adversarial phrasings of the prohibited subject after configuration. Review restricted topic match logs regularly to identify false positives and missed matches, and refine entries accordingly.

---

## Gotcha 5: Action Filters and Topic Filters Are Not Interchangeable

**What happens:** A practitioner wants to prevent an action from being called in the wrong topic and adds a topic filter on the action within one topic — expecting this to block it in all other topics. But topic filters only control availability within the topic where the filter is set. If the same action is also attached to another topic with no filter, it can still be invoked there.

**When it occurs:** When the same invocable action (e.g., a sensitive data lookup action) is attached to multiple topics and the practitioner adds a topic filter on only one of them, believing it is a global restriction.

**How to avoid:** Use action filters (configured on the action itself, not on the topic) to globally prevent an action from being invoked by any topic. Reserve topic filters for narrowing action availability within a specific topic context. When configuring a sensitive action, always check every topic it is attached to, or apply an action filter at the action level as the definitive control.

---

## Gotcha 6: Instruction Adherence Score Lags Behind Configuration Changes

**What happens:** After revising topic instructions or system instructions to improve guardrail compliance, the Instruction Adherence score in Agentforce Analytics does not immediately reflect the improvement. The score is computed over a rolling window of conversation data, so it continues to reflect old conversation turns for days after the change.

**When it occurs:** Any time instructions are revised and practitioners check the score immediately to validate the fix. A stable or still-low score is misread as evidence that the fix did not work, leading to further (unnecessary) instruction changes.

**How to avoid:** After instruction revisions, allow at least 48–72 hours of production traffic before re-evaluating Instruction Adherence. Test immediate behavior by reviewing individual conversation turns in the conversation detail view, not by waiting for the aggregated score to update. Document the revision date and re-check the score after the lag window.
