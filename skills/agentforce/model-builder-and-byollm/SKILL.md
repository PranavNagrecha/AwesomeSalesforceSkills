---
name: model-builder-and-byollm
description: "Use when configuring Model Builder in Salesforce to register external LLMs or select standard models for Agentforce and Einstein features. Covers model registration, API key configuration, model aliases, and cost/performance tradeoffs. NOT for deciding the model-tier or multi-agent platform strategy before you register anything — use architect/ai-platform-architecture. NOT for Trust Layer configuration — use agentforce/einstein-trust-layer."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do I connect my own OpenAI model to Salesforce"
  - "configure external LLM in Agentforce using Model Builder"
  - "register Azure OpenAI or Anthropic as LLM in Salesforce"
  - "model alias not working in Agentforce prompt template"
  - "troubleshoot external LLM connectivity failure in Model Builder"
  - "which default model should I pick for Einstein Copilot cost vs quality"
  - "add an Azure OpenAI foundation model in Einstein Studio and use it in a prompt template"
  - "block an LLM provider so no generative AI feature can call its models"
tags:
  - model-builder
  - byollm
  - external-llm
  - model-alias
  - agentforce
  - named-credentials
inputs:
  - Salesforce org with Einstein generative AI feature enabled (Einstein for Agentforce license or equivalent)
  - External LLM provider endpoint URL and authentication details if adding a BYO foundation model
  - Knowledge of which Agentforce or Einstein features will consume the model
  - Understanding of desired cost vs. quality tradeoff for the target use case
outputs:
  - Foundation model connected in Einstein Studio (Generative tab) and tested with Save & Test
  - Model configuration (hyperparameters, prompt settings) evaluated in Model Playground
  - Prompt template versions pointing at the chosen model configuration
  - Decision guidance on model selection by use case
  - Review checklist confirming connection, configuration, provider settings, and prompt retests
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Model Builder and Bring Your Own LLM (BYOLLM)

This skill activates when a practitioner needs to connect an external foundation model (Azure OpenAI, Amazon Bedrock, OpenAI, or Google Vertex) to Salesforce through Einstein Studio, choose or tune the model a prompt template uses, block providers, or troubleshoot model connections. Model Builder is "the tool in Einstein Studio used to create, connect, and edit models." It covers Mode 1 (connect a BYO foundation model), Mode 2 (review model configurations and provider settings), and Mode 3 (troubleshoot connection and quality problems).

Correction (2026-10-03): earlier versions of this skill described "Setup > Model Builder > Add Model," a Named Credential that must hold the API key, a "Test Connection" button, and global "model aliases" that Agentforce agents reference. The Data Cloud guide documents a different flow: Einstein Studio > Generative tab > Add Foundation Model, enter the endpoint and authentication details, Save & Test, then create a model configuration in Model Playground. The Generative AI guide also states that the Agentforce reasoning engine uses OpenAI GPT-4o and that "Bringing your own model isn't supported" for agents.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Feature flag:** "To add a foundation model, Einstein Generative AI must be enabled in your org." Einstein Studio is part of Data Cloud; users need Data Cloud Admin permissions to open a model from Prompt Builder's View this model link.
- **Where the model will be used:** Prompt Builder templates, the Models API, and custom apps can use BYO models. The Agentforce platform "supports OpenAI GPT-4o for reasoning engine calls... Bringing your own model isn't supported, but custom actions that execute prompt templates can use any Salesforce-managed model."
- **Endpoint prerequisites:** the endpoint URL and authentication information from the provider's dashboard; "a standard HTTPS 443 port is required." For Azure OpenAI, the deployment name; for an OpenAI fine-tuned model, answer Yes when prompted; for Amazon Bedrock, select the Anthropic model type.
- **Most common wrong assumption:** that changing a model behind a template is free. "If your model is already associated with prompts, create a new model instead. Updating model settings can affect the performance of associated prompts." Each prompt template version can hold a different model configuration, and only the active version's model is used.
- **Named Credential claim:** UNVERIFIED (2026-10-03): the earlier statement that BYO model keys must be stored in Named Credentials and are otherwise rejected was not found in a fetched source; the documented Add Foundation Model step asks for authentication details directly.

---

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Will this model power an agent's reasoning, a custom action's prompt template, or a Prompt Builder template?" | Agents don't support BYO models; custom actions with prompt templates use Salesforce-managed models (Gotcha 1) | The consuming surface for each model | Nobody buys an Azure deployment for an agent that cannot use it |
| "Which prompts already use the configuration you plan to change?" | Updating model settings affects every associated prompt; create a new configuration instead (Gotcha 2) | A list of templates per configuration | Changes roll out one template version at a time |
| "Which providers does policy allow?" | EinsteinGptSettings can block Azure OpenAI, Bedrock, OpenAI, and Vertex (Gotcha 7) | Allowed and blocked providers | Unapproved providers are blocked org-wide, not by convention |
| "Must requests stay in a region?" | Geo-aware routing falls back to the US and can't be disabled; Azure has its own fallback switch (Gotcha 8) | Region per model and the fallback setting | Residency claims match the routing |
| "What volume will this drive?" | The org default is 300 LLM generation requests per minute, plus provider limits (Gotcha 5) | Peak requests per minute per feature | Bulk flows don't hit the limit at month end |
| "What happens when the model is deprecated?" | Deprecated models are rerouted to a replacement and can't be selected in Model Playground (Gotcha 6) | An owner and a retest plan | Reroutes are tested before the reroute date |

---

## Core Concepts

### Foundation Models and Model Configurations

Einstein Studio separates the **foundation model** (the connection to a provider endpoint) from the **model configuration** (hyperparameters and prompt settings for a use case). Salesforce-managed models "are enabled by default." BYOLLM "enables you to add a foundation model hosted on an external platform and connect it with Einstein Studio." You can edit most foundation model settings "as long as the model isn't a source for other models"; otherwise delete the associated configurations first. "You can't recover a model after it's deleted."

The earlier "model alias" wording in this skill maps to the model configuration and its API name. Prompt templates store the model per version in `primaryModel` (the Metadata API sample uses `sfdc_ai__DefaultOpenAIGPT4`).

### Supported Providers and Models

Salesforce-managed models include Azure OpenAI and OpenAI GPT models (GPT-3.5 Turbo, GPT-4, GPT-4 Turbo, GPT-4o, GPT-4o Mini), text-embedding-ada-002, and Anthropic Claude 3 Haiku on Amazon Bedrock. BYOLLM "supports all the Salesforce-managed models and these additional models": Anthropic Claude 3 Opus, Claude 3 Sonnet, Claude 3.5 Sonnet, Azure OpenAI GPT-4o, Google Gemini 1.5 Pro, and OpenAI GPT-4o, using "your Azure, Bedrock, OpenAI, or Vertex account." For other providers, the guide points to the LLM Open Connector. UNVERIFIED (2026-10-03): the earlier mention of Salesforce-hosted Llama models.

### Model Playground

"Create, edit, and evaluate your model configuration in Model Playground." Hyperparameters: Temperature from 0 through 2 ("Only Anthropic models have this setting available for testing"), Frequency Penalty and Presence Penalty from -2.0 through 2.0. Prompt settings (number of responses, stop sequence, data masking) "are used only during testing. They aren't saved with your model configuration." If masking is not enabled in the playground, "org-level data masking settings are applied."

### Cost and Quality Tradeoffs

Choose smaller Salesforce-managed models (for example GPT-4o Mini) for high-volume summarization and extraction, and larger models where reasoning quality matters. "Changing the model can affect your usage," so check Einstein usage before switching. UNVERIFIED (2026-10-03): the earlier guidance that a model without function calling cannot back agent actions; the guide instead says the reasoning engine uses GPT-4o regardless.

---

## Common Patterns

### Mode 1: Connect a BYO Foundation Model End-to-End

**When to use:** An organization wants a Prompt Builder template to run on its own Azure OpenAI, Bedrock, OpenAI, or Vertex account (data processing agreement, fine-tuned model, or model choice).

**How it works:**

1. Confirm Einstein Generative AI is enabled and the provider is not blocked in EinsteinGptSettings.
2. In Einstein Studio, Generative tab, click Add Foundation Model and select the provider type.
3. Enter the endpoint name and URL (HTTPS on port 443) and the authentication details.
4. Enter the model information: the Azure deployment for Azure OpenAI, Yes for an OpenAI fine-tuned model, the Anthropic model type for Bedrock.
5. Click Save & Test, enter the exact model name, click Connect, name the model, and select the model version.
6. In Model Playground, create a model configuration: set temperature and penalties, test prompts with data masking on, and save.
7. In Prompt Builder, save a new template version that uses the configuration, preview it, and activate.

**Why not only Salesforce-managed models:** managed models are rerouted on the provider's deprecation schedule and run under Salesforce's provider agreements; BYOLLM lets you choose the account and version, at the cost of owning the connection.

### Mode 2: Review Current Model Configuration

**When to use:** Before a release, during a cost review, or when a deprecation notice arrives.

**How it works:**

1. In Einstein Studio, list foundation models and model configurations; open Model Activity for inferences and errors.
2. In Prompt Builder, list each template's active version and its model.
3. Compare against the deprecated-models table and the monthly Einstein Platform release notes.
4. Check EinsteinGptSettings provider blocks and `disableAIProviderRegionFallback` in source control.
5. Document the configuration-to-template mapping and the last test date.

### Mode 3: Troubleshoot Model Connections and Quality

**When to use:** Save & Test fails, a template errors at run time, or response quality drops.

**How it works:**

1. Re-run Save & Test on the foundation model; check the endpoint uses HTTPS on port 443 and that the authentication details are current.
2. For Azure OpenAI, confirm the deployment name; for Bedrock, the Anthropic model type.
3. Open Model Activity for error counts; check provider dashboards for throttling, and the org's 300-per-minute generation limit for bursts.
4. If quality dropped after a reroute, create a configuration on the replacement model "with the same hyperparameters as the retired model," retest in Prompt Builder, then activate a new template version.
5. If an agent is involved, remember the reasoning engine uses GPT-4o and BYO models are not used there.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Agent reasoning | Use the platform reasoning engine (GPT-4o) | BYO models aren't supported for agents |
| Custom agent action that runs a prompt template | Pick a Salesforce-managed model on the template | The guide says such actions can use any Salesforce-managed model |
| High-volume summarization in Prompt Builder | A smaller managed model such as GPT-4o Mini, or a BYO model with a negotiated rate | Usage changes with the model; test quality on samples |
| Data processing agreement with one provider | BYOLLM foundation model on that provider account | Connects your Azure, Bedrock, OpenAI, or Vertex account |
| EU residency | Models available in the region, plus `disableAIProviderRegionFallback` for Azure OpenAI | Geo-aware routing falls back to the US when no nearby model exists |
| Testing a new model | New model configuration and a new template version in a sandbox | Updating an associated configuration affects every prompt using it |
| Provider not approved by policy | Block it in EinsteinGptSettings | Blocks access to its models for all generative AI features |

---

## Recommended Workflow

1. Map each use case to its surface with the Questions table: agent reasoning (no BYO), custom action prompt template (managed models), or Prompt Builder template (managed or BYO).
2. Set provider policy first: commit EinsteinGptSettings with provider blocks and the region fallback setting (`references/metadata-examples.md`).
3. Connect the foundation model in Einstein Studio (Generative tab), Save & Test, and create a model configuration in Model Playground with masking on.
4. Point a new prompt template version at the configuration, preview, and activate; never edit a configuration that live prompts use.
5. Run `python3 scripts/check_model_builder_and_byollm.py --manifest-dir <project>` to catch templates on blocked providers or deprecated models, hard-coded provider keys, and direct provider callouts.
6. Record the configuration-to-template map, owners, and the retest plan for deprecations.

---

## Review Checklist

Run through these before marking a Model Builder / BYOLLM implementation complete:

- [ ] Einstein Generative AI enabled; Einstein Studio access (Data Cloud permissions) confirmed for admins
- [ ] Use case surface confirmed: no BYO model planned for agent reasoning
- [ ] Foundation model connected over HTTPS 443 with Save & Test passing
- [ ] Model configuration tested in Model Playground with masking on
- [ ] Prompt template versions point at the intended configuration; live configurations not edited in place
- [ ] Provider blocks and region fallback committed in EinsteinGptSettings
- [ ] Peak requests per minute checked against the 300-per-minute org default and provider limits
- [ ] Deprecation watch: owner, release-note check, and retest plan documented

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Model changes reach every associated prompt**: Correction (2026-10-03): earlier versions called these "alias changes" and said they are global and immediate with no audit log. The guide's wording is "if your model is already associated with prompts, create a new model instead. Updating model settings can affect the performance of associated prompts." Create a new configuration and move templates one version at a time.
2. **Sandbox and production model configurations are independent**: UNVERIFIED (2026-10-03): no fetched source states how foundation models and configurations move between orgs. Plan to recreate them in each org and keep the steps scripted or documented.
3. **Rate limits exist on both sides**: Correction (2026-10-03): earlier versions said Salesforce does not rate-limit external LLM calls. "Customers have a default rate limit of 300 Large Language Model (LLM) generation requests per minute at their Salesforce Organization ID level," for Prompt Builder, Einstein Studio, and the Models API. Provider quotas apply on top.
4. **Named Credential permission sets**: UNVERIFIED (2026-10-03): the earlier claim that callers need Named Credential access through a permission set applies to Apex callouts, not to the documented Einstein Studio flow, which takes authentication details in Add Foundation Model.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Foundation model connection | Einstein Studio entry with provider type, endpoint, model name, and version |
| Model configuration | Hyperparameters and prompt settings tested in Model Playground |
| Provider settings file | EinsteinGptSettings with provider blocks and region fallback |
| Template-to-configuration map | Ops reference listing each template version and its model |
| Deprecation plan | Owner, release-note cadence, and retest steps |

---

## Related Skills

- agentforce/einstein-trust-layer: use when configuring data masking, audit trail, toxicity detection, and grounding rules that govern how model outputs are processed; Trust Layer sits between the model and the user
- agentforce/prompt-builder-templates — for authoring and managing the prompt templates that reference model aliases and are grounded with Salesforce data
- integration/named-credentials-setup: for detailed Named Credential and External Credential configuration patterns beyond the model-registration context
