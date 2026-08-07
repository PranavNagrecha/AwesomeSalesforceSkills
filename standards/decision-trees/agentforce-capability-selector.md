# Decision Tree — Agentforce Capability Selection

Which Salesforce AI capability fits the use case?
**Agentforce Agent · Einstein Copilot · Prompt Builder · Einstein Next Best Action · Einstein Bots (legacy) · Model Builder (BYOLLM) · Einstein Discovery · None-of-the-above**

Use this tree BEFORE picking an Agentforce-category skill. Salesforce has multiple overlapping AI products; routing wrong at this layer wastes weeks.

---

## Strategic defaults

1. **New conversational AI work** → Agentforce Agent (successor to Einstein Copilot).
2. **Prompt-driven generation embedded in existing UI** (draft email, summarize record) → Prompt Builder.
3. **Rules-driven recommendation surfaced on page layouts / flows** → Einstein Next Best Action.
4. **Custom model trained on Salesforce data** → Einstein Discovery or Model Builder.
5. **Hosted LLM from a specific vendor with Salesforce grounding** → Model Builder (BYOLLM) + Agentforce.
6. **Existing Einstein Bots investment with low conversation volume** → migrate to Agentforce (`einstein-bots-to-agentforce-migration`).

---

## Decision tree

```
START: User wants an AI capability.

Q1. Is the interaction CONVERSATIONAL (multi-turn natural language)?
    ├── Yes  → Q2
    └── No   → Q4

Q2. Is the conversation with an END USER (customer, agent, internal user)?
    ├── Yes  → Q3
    └── No — it's an internal system dialog → Reconsider; probably not AI

Q3. Does the agent need to TAKE ACTIONS (create records, call APIs, update data)?
    ├── Yes  → Agentforce Agent + Actions (Apex / Flow / External Service)
    └── No, read-only Q&A → Agentforce Agent + Retrieval (Data Cloud vector search)

Q4. Does the user need GENERATED CONTENT inline in the Salesforce UI?
    ├── Yes, draft text / summary / explanation → Prompt Builder template
    ├── Yes, decision / recommendation         → Einstein Next Best Action
    └── No                                      → Q5

Q5. Do we need a PREDICTIVE MODEL (score, probability, classification)?
    ├── Yes, trained on Salesforce data only   → Einstein Discovery (CRM Analytics)
    ├── Yes, need custom model                 → Model Builder (BYOLLM or train-in-place)
    └── No                                      → Q6

Q6. Are we migrating FROM existing AI?
    ├── From Einstein Bots                     → einstein-bots-to-agentforce-migration
    ├── From Einstein Copilot                  → Agentforce (same engine, renamed)
    └── From third-party agent                 → Agentforce with BYOLLM if model is differentiating
```

---

## Capability-by-capability detail

### Agentforce Agent

- **Best for:** multi-turn natural-language interactions that combine Q&A, data lookup, and record actions.
- **Key dependency:** Agentforce license + Einstein Trust Layer enabled.
- **Design surface:** Topics, Actions, Prompt Templates (as grounded generation), Retrieval (as grounded data).
- **Skill pack:** `agentforce-agent-creation`, `agent-topic-design`, `agent-actions`, `agentforce-multi-turn-patterns`, `agentforce-tool-use-patterns`.

### Einstein Copilot

- Rebranded as "Agentforce Assistant" in recent releases. For new work, use Agentforce.
- Existing deployments continue to run; treat as equivalent to Agentforce Agent with internal-user-only posture.

### Prompt Builder

- **Best for:** single-turn generation embedded in standard UI surfaces (Lightning App Pages, Flow Builder, Action Dialogs).
- **Not conversational** — one prompt in, one response out.
- **Strongest when grounded** — attach record fields or related records as inputs; the template substitutes them into the prompt.
- **Skill:** `prompt-builder-templates`.

### Einstein Next Best Action

- **Best for:** rules-driven recommendations surfaced inline (e.g., "offer this upsell when MRR > $X and churn-risk < Y").
- **Not generative** — no LLM call per invocation. Scoring uses Predictive Intelligence / Decision Tables.
- **Use when:** the recommendation logic is deterministic enough to be expressed as business rules.
- **Skill:** `einstein-next-best-action`.

### Einstein Discovery

- **Best for:** supervised models trained on Salesforce data (churn prediction, deal-scoring, cycle-time forecasting).
- **Not a conversation** — outputs scores and explanations, typically consumed in reports / dashboards / records.
- **Skill:** `einstein-discovery-development`.

### Model Builder (BYOLLM)

- **Best for:** bringing a third-party LLM (Anthropic Claude, OpenAI GPT, AWS Bedrock, Google Vertex) into the Salesforce security perimeter.
- **Composes with** Agentforce: use BYOLLM as the reasoning model, keep Agentforce's Trust Layer + Actions framework.
- **Skill:** `model-builder-and-byollm`.

### Einstein Bots (legacy)

- Scripted, not LLM-based.
- **Don't build new bots here.** Migrate to Agentforce.
- **Skill:** `einstein-bots-to-agentforce-migration`.

---

## Cross-capability guidance

### When a use case spans multiple capabilities

| Use case | Primary | Secondary |
|---|---|---|
| Conversational agent that drafts emails | Agentforce | Prompt Builder (as action) |
| Conversational agent with churn-risk scoring | Agentforce | Einstein Discovery (as action) |
| Inline record summarizer | Prompt Builder | — |
| Inline "next best offer" recommendation | Next Best Action | Einstein Discovery (scoring) |
| Partner-provided LLM powering conversations | Agentforce + BYOLLM | — |

### Latency + cost implications

- **Agentforce Agent:** LLM per turn, +1 per tool call. Per-conversation cost bounded by turn count.
- **Prompt Builder:** single LLM call per invocation. Predictable cost.
- **Next Best Action:** no LLM; near-zero per-call cost.
- **Einstein Discovery:** inference cost per prediction; can be bulked.

### Security / Trust Layer

All generative capabilities (Agentforce, Prompt Builder, BYOLLM-routed) flow through Einstein Trust Layer, which handles:
- PII masking before prompt submission
- Zero-data-retention with the LLM provider
- Toxicity / bias detection on responses
- Prompt-injection defense

Predictive capabilities (Next Best Action, Einstein Discovery) don't use the Trust Layer — they don't call external LLMs.

---

## Skills to activate after this tree

| Branch | Activate skill |
|---|---|
| Agentforce Agent | `skills/agentforce/agentforce-agent-creation` |
| Agent topic design | `skills/agentforce/agent-topic-design` |
| Agent actions (Apex) | `skills/agentforce/agent-actions` + `skills/agentforce/custom-agent-actions-apex` |
| Multi-turn design | `skills/agentforce/agentforce-multi-turn-patterns` |
| Tool selection | `skills/agentforce/agentforce-tool-use-patterns` |
| Evaluation | `skills/agentforce/agentforce-eval-harness` |
| Guardrails | `skills/agentforce/agentforce-guardrails` |
| Observability | `skills/agentforce/agentforce-observability` |
| Prompt Builder | `skills/agentforce/prompt-builder-templates` |
| Next Best Action | `skills/agentforce/einstein-next-best-action` |
| BYOLLM | `skills/agentforce/model-builder-and-byollm` |
| Einstein Discovery | `skills/agentforce/einstein-discovery-development` |
| Migration from Bots | `skills/agentforce/einstein-bots-to-agentforce-migration` |

---

## Official Sources Used

- Salesforce Help — Agentforce Overview: https://help.salesforce.com/s/articleView?id=sf.copilot_landing.htm
- Salesforce Help — Einstein Platform: https://help.salesforce.com/s/articleView?id=sf.einstein_platform.htm
- Salesforce Developer — Einstein Trust Layer: https://developer.salesforce.com/docs/einstein/genai/guide/trust-layer.html
- Salesforce Architects — AI Architecture Patterns: https://architect.salesforce.com/
