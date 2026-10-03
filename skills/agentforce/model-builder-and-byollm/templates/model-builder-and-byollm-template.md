# Model Builder / BYOLLM: Work Template

Use this template when connecting an external foundation model in Einstein Studio, reviewing model configurations, or troubleshooting model connections.

---

## Scope

**Skill:** `model-builder-and-byollm`

**Request summary:** (for example, "connect our Azure OpenAI gpt-4o deployment for the client-letter template")

**Mode:**
- [ ] Mode 1: Connect a BYO foundation model
- [ ] Mode 2: Review model configurations and provider settings
- [ ] Mode 3: Troubleshoot a connection or quality problem

---

## Context Gathered

| Question | Answer |
|---|---|
| Einstein generative AI enabled? | |
| Consuming surface: Prompt Builder template / Models API / custom action prompt template / agent reasoning (no BYO) | |
| Provider (Azure OpenAI / Amazon Bedrock / OpenAI / Vertex) and allowed by EinsteinGptSettings? | |
| Endpoint URL (HTTPS, port 443) | |
| Azure deployment name / OpenAI fine-tuned (yes/no) / Bedrock model type Anthropic | |
| Templates that will use the configuration | |
| Peak generation requests per minute (org default 300) | |
| Residency requirement and disableAIProviderRegionFallback value | |

---

## Connection Record (Einstein Studio, Generative tab)

| Field | Value |
|---|---|
| Foundation model name | |
| Provider type | |
| Endpoint name and URL | |
| Model name and version | |
| Save & Test result and date | |

## Model Configuration (Model Playground)

| Field | Value |
|---|---|
| Configuration name | |
| Temperature (0 to 2; Anthropic models only for testing) | |
| Frequency penalty / presence penalty (-2.0 to 2.0) | |
| Masking enabled during playground tests | |
| Template versions using it | |

---

## Troubleshooting Reference (Mode 3)

| Symptom | Likely Cause | Next Step |
|---|---|---|
| Save & Test fails | Endpoint not HTTPS on 443, wrong authentication details, or wrong Azure deployment | Fix the endpoint or details; re-run Save & Test |
| Bulk runs fail partway | Org limit of 300 generations per minute or provider quota | Throttle the job; check Model Activity and provider dashboard |
| Output changed with no edits | Model rerouted after deprecation | Build a configuration on the replacement with the same hyperparameters; retest |
| Template stops after a settings deploy | Provider blocked in EinsteinGptSettings | Move the template to an allowed provider |
| Agent ignores the BYO model | BYO models aren't supported for agents | Scope the BYO model to Prompt Builder |

---

## Review Checklist

- [ ] Consuming surface confirmed; no BYO model planned for agent reasoning
- [ ] Provider allowed and region fallback set in EinsteinGptSettings
- [ ] Foundation model connected; Save & Test passed
- [ ] Configuration tested in Model Playground with masking on
- [ ] New template version points at the configuration; live configurations not edited in place
- [ ] `scripts/check_model_builder_and_byollm.py` run with no ERROR
- [ ] Deprecation owner and retest plan recorded

---

## Notes

(free text)
