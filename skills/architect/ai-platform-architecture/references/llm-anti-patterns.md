# LLM Anti-Patterns — AI Platform Architecture

Common mistakes AI coding assistants make when generating or advising on AI platform architecture for Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Model Alias Selection with Platform Model Strategy

**What the LLM generates:** Step-by-step instructions that begin with "Open Model Builder and select GPT-4o as your model" without first classifying data sensitivity or establishing which model tiers are eligible based on ZDR requirements. The output treats model selection as a preference decision driven by capability ratings rather than an architectural constraint derived from data classification.

**Why it happens:** LLMs are trained on generic AI integration content where model selection is typically driven by capability or cost benchmarks. The Salesforce-specific constraint that ZDR guarantees are model-tier-dependent, and that BYOLLM bypasses Trust Layer masking, is a platform-specific nuance not well-represented in generic training data.

**Correct pattern:**

```
Step 1: Classify data sensitivity for each planned agent role.
  - Identify all CRM objects and fields the agent will access
  - Assign sensitivity tier: regulated (PII/PCI/PHI), sensitive, internal, public

Step 2: Map sensitivity to eligible model tiers.
  - Regulated or sensitive data → Salesforce Default model OR ZDR-confirmed partner model only
  - Internal or public data → may evaluate BYOLLM after confirming provider data handling terms

Step 3: Select specific model alias in Model Builder as the final configuration step,
  constrained by the tier already determined in Step 2.
```

**Detection hint:** Look for model name recommendations ("use GPT-4o", "select claude-3-5-sonnet") appearing before any data classification step. Flag responses that do not mention ZDR, Trust Layer masking, or data sensitivity as preconditions for model selection.

---

## Anti-Pattern 2: Asserting That Trust Layer Masking Covers All Salesforce AI Features Including BYOLLM

**What the LLM generates:** Guidance stating that "the Einstein Trust Layer automatically masks PII before it reaches any LLM, including custom models registered in Model Builder." This gives the false impression that enabling org-level data masking in Trust Layer setup protects all agent interactions regardless of model type.

**Why it happens:** The Trust Layer is presented as a universal platform security layer in Salesforce marketing and overview documentation. LLMs trained on this content generalize "Trust Layer protects all AI" without capturing the implementation-specific carve-out that BYOLLM inference calls bypass the LLM gateway where masking is applied.

**Correct pattern:**

```
Trust Layer data masking applies to LLM calls routed through the 
Salesforce Einstein LLM gateway.

BYOLLM model calls are routed DIRECTLY to the external provider endpoint
and DO NOT pass through the LLM gateway.

Therefore: data masking does NOT apply to BYOLLM models,
regardless of org-level masking settings.

Correct guidance:
- Salesforce Default models: masking applies (when enabled)
- ZDR-confirmed partner models in Model Builder: masking applies (when enabled)
- BYOLLM models: masking does NOT apply; architect must implement compensating controls
```

**Detection hint:** Look for phrases like "Trust Layer protects all your LLM interactions" or "data masking covers all models in Model Builder" without the BYOLLM exception. Any absolute statement about Trust Layer coverage without scoping to non-BYOLLM models is likely wrong.

---

## Anti-Pattern 3: Designing Multi-Agent Topology with Shared Actions on the Supervisor

**What the LLM generates:** A multi-agent architecture where the Supervisor agent is configured with a full set of domain actions (query Order records, search Knowledge, create Cases) alongside its routing responsibilities. The reasoning given is that the Supervisor can "handle simple requests directly without routing overhead."

**Why it happens:** LLMs default to consolidation in design recommendations. The Supervisor/Specialist pattern requires explicit documentation to generate correctly — without that, the LLM produces the more familiar single-agent-with-routing design and labels the Supervisor as the "main agent."

**Correct pattern:**

```
Supervisor Agent configuration:
  - Topic configuration: intent classification and routing descriptions only
  - No domain-specific actions assigned to Supervisor
  - Agent actions: optionally only Specialist invocation actions

Specialist Agent configuration:
  - Single domain scope (Orders, Knowledge, Cases — not mixed)
  - Explicit input contract and output contract documented
  - Model assigned based on that Specialist's data sensitivity

Rationale:
  Assigning domain actions to the Supervisor merges two concerns:
  routing reliability and action execution. When the Supervisor has 
  domain actions, the LLM may execute an action directly instead of 
  routing, bypassing the Specialist's scoped data access and model 
  assignment controls.
```

**Detection hint:** Look for Supervisor agent configurations that include specific domain action sets (Apex actions, Flow actions for domain operations) alongside routing logic. A correctly designed Supervisor in a Supervisor/Specialist topology should not have domain execution actions.

---

## Anti-Pattern 4: Ignoring Context Budget Accumulation in Multi-Agent Chains

**What the LLM generates:** A topology design with context budget guidance that calculates token usage per individual agent turn ("each Specialist uses approximately 3,000 tokens") without accounting for the Supervisor's accumulation of all Specialist outputs before the final synthesis call.

**Why it happens:** LLMs reason about context windows at the per-request level because that is how they experience context. The platform constraint that a Supervisor aggregating multiple Specialist outputs into a single synthesis prompt must fit the entire accumulated context within 65,536 tokens is a topology-level constraint that requires reasoning about the chain, not individual turns.

**Correct pattern:**

```
Context budget calculation for a 3-Specialist topology with masking active:

Supervisor system prompt:          ~2,000 tokens
User message history:              ~1,500 tokens
Specialist A output (Order data):  ~4,000 tokens
Specialist B output (Knowledge):   ~6,000 tokens
Specialist C output (Case data):   ~3,000 tokens
Supervisor synthesis prompt:       ~1,000 tokens
Buffer:                            ~2,000 tokens
Total:                             ~19,500 tokens (well within 65,536)

If Specialist outputs are verbose (raw record dumps, long articles):
  Specialist A: ~15,000 tokens
  Specialist B: ~30,000 tokens
  Specialist C: ~10,000 tokens
  Total: ~60,000 tokens — dangerously close to 65,536 limit

Recommendation: Specialist output contracts should return structured,
compact summaries — not raw record content.
```

**Detection hint:** Look for context budget guidance that only states per-agent token estimates without adding them into a chain total. Any multi-agent design that does not produce a chain-level context budget calculation is incomplete.

---

## Anti-Pattern 5: Recommending a Single Shared Model Alias for All Agents

**What the LLM generates:** Configuration guidance that sets up one model alias (e.g., "sfdc-default") in Model Builder and assigns it to all Agentforce agents across the org. The guidance presents this as a best practice for "centralized model management" and "easy updates."

**Why it happens:** Centralized configuration is a general software best practice, and LLMs trained on general infrastructure content apply it here. The Salesforce-specific consequence — that updating a shared alias changes production behavior for all assigned agents simultaneously with no per-agent rollback — requires platform-specific architectural knowledge to identify.

**Correct pattern:**

```
Model alias strategy: one dedicated alias per agent role with distinct 
compliance or behavioral requirements.

Example:
  loan-status-agent-model    → Salesforce Default (ZDR required, PCI data)
  case-routing-agent-model   → ZDR partner model (PII data)
  knowledge-agent-model      → BYOLLM large-context (non-sensitive, high volume)

Benefits:
  - Model changes per agent role are independently controlled
  - Rollback of a model change affects only the intended agent
  - Compliance audit can show per-role model assignment history
  - Behavioral regression testing is scoped per alias

Shared aliases are acceptable for non-production environments (sandbox, 
scratch orgs) where uniform configuration simplifies setup.
```

**Detection hint:** Look for any multi-agent design where all agents share a single model alias without mention of the change-propagation risk. Especially flag recommendations that use "centralized model management" or "single source of truth for model configuration" as justifications for sharing aliases across production agents.
