# Gotchas — AI Platform Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: BYOLLM Models Do Not Receive Trust Layer Data Masking

**What happens:** When an agent is assigned a model registered as BYOLLM in Model Builder, the LLM inference call is made directly to the external provider endpoint. The Einstein Trust Layer masking pipeline does not intercept BYOLLM calls. Data sent to a BYOLLM model — including CRM fields, grounded record values, and any PII included in agent prompts — is transmitted to the external provider unmasked. There is no error, no warning, and no indication in the Salesforce UI that masking is not active for that model.

**When it occurs:** Any time a BYOLLM model alias is assigned to an agent that accesses sensitive data, regardless of whether data masking is enabled at the Trust Layer org level. The org-level masking setting applies to the Salesforce LLM gateway, not to BYOLLM endpoints.

**How to avoid:** Classify agent data sensitivity before model assignment. Only assign BYOLLM models to agents whose data scope is confirmed non-sensitive. For all agents accessing PII or regulated data, use Salesforce Default models or ZDR-confirmed partner models listed in Model Builder. Confirm the data handling terms of any BYOLLM provider independently — ZDR is not inherited from Salesforce's agreements.

---

## Gotcha 2: Context Budget Must Be Planned Across the Full Multi-Agent Chain, Not Per Turn

**What happens:** In a Supervisor/Specialist topology, each agent turn consumes context budget. The 65,536-token context limit when data masking is active applies to the accumulated context in the conversation, not to individual agent turns in isolation. A Supervisor that receives responses from two or three Specialists and synthesizes a final reply may accumulate context well above 65,536 tokens before the Supervisor's final LLM call. The call fails at runtime with a context limit error that is not obvious to diagnose because each individual agent turn appeared within limits during unit testing.

**When it occurs:** In any multi-agent topology where the Supervisor aggregates results from multiple Specialist invocations before generating the final response, when data masking is active, and when grounded Specialist outputs are verbose.

**How to avoid:** Calculate the worst-case accumulated context budget at the architecture level: Supervisor system prompt + user message history + each Specialist's grounded output concatenated before the Supervisor's synthesis call. Design Specialist output contracts to return structured, compact summaries rather than raw record dumps. If the budget is tight, move to dynamic grounding with scoped retrievals at the Specialist level so that each Specialist retrieves only the minimal fields needed.

---

## Gotcha 3: Shared Model Alias Changes Apply Immediately Across All Assigned Agents

**What happens:** Model Builder model aliases are shared references. When an architect updates the underlying model configuration for an alias — for example, changing the model version, adjusting parameters, or swapping to a different provider endpoint — the change takes effect immediately for every Agentforce agent assigned that alias. There is no staging, no deployment pipeline, and no per-agent model version lock. A single alias change can silently alter the behavior of multiple production agents at the same time.

**When it occurs:** Any time a model alias in Model Builder is updated while multiple production agents are assigned that alias. Common scenario: a shared "default" alias is used across all agents for convenience during initial setup. When the model is upgraded, all agents change simultaneously with no review process.

**How to avoid:** Assign each agent role that has distinct behavioral or compliance requirements its own dedicated model alias. Do not share aliases across agents with different data sensitivity classifications or different behavioral requirements. Treat model alias updates as change-controlled operations: test the change on a non-production alias and reassign the production alias only after validation.

---

## Gotcha 4: Audit Trail Does Not Capture BYOLLM Inference Calls

**What happens:** The Trust Layer audit trail in Data 360 records interactions that pass through the Salesforce LLM gateway. BYOLLM model calls bypass this gateway — the inference call goes directly to the external provider. This means interactions with agents assigned BYOLLM models are not captured in the standard audit trail. Compliance teams reviewing the audit trail have an incomplete picture: they see all Salesforce Default model interactions but have a silent gap for all BYOLLM agent interactions.

**When it occurs:** Any time BYOLLM models are used in production agents and the audit trail is the compliance evidence mechanism for AI interactions.

**How to avoid:** Design an alternative audit logging mechanism for BYOLLM agents — for example, logging agent invocation context to a custom object using an Apex action before and after the BYOLLM call. Document the audit gap in the architecture decision record and get compliance sign-off before going live with BYOLLM agents in regulated environments.

---

## Gotcha 5: Supervisor Routing Degrades When Specialist Topic Descriptions Overlap

**What happens:** The Supervisor agent classifies user intent and routes to Specialist agents based on topic configuration descriptions. This routing is performed by the LLM model assigned to the Supervisor — it is not a deterministic rule engine. When two or more Specialist topic descriptions are similar, vague, or use overlapping vocabulary, the Supervisor produces inconsistent routing in production. For example, a "Customer Issue Resolution" Specialist and a "Customer Support Cases" Specialist will receive intermixed routing for the same types of requests because the descriptions are semantically close.

**When it occurs:** Common in large multi-agent topologies where Specialists are added incrementally without reviewing the full set of topic descriptions for semantic overlap. Also common when topic descriptions are written from an internal team perspective rather than from the vocabulary of actual user requests.

**How to avoid:** Write Specialist topic descriptions from the perspective of the user's intent language, not the internal domain name. Test each topic description against a sample of real or realistic user requests and confirm routing stability. Review all topic descriptions as a set when adding a new Specialist — not just the new Specialist in isolation. Include routing accuracy testing as an explicit step in the architecture validation process.
