---
name: model-builder-and-byollm
description: "Use when configuring Model Builder in Salesforce to register external LLMs or select standard models for Agentforce and Einstein features. Covers model registration, API key configuration, model aliases, and cost/performance tradeoffs. NOT for Trust Layer configuration (use agentforce-trust-layer)."
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
tags:
  - model-builder
  - byollm
  - external-llm
  - model-alias
  - agentforce
  - named-credentials
inputs:
  - Salesforce org with Einstein generative AI feature enabled (Einstein for Agentforce license or equivalent)
  - External LLM provider credentials (API key, endpoint URL) if registering a BYO model
  - Knowledge of which Agentforce or Einstein features will consume the model
  - Understanding of desired cost vs. quality tradeoff for the target use case
outputs:
  - Registered and tested LLM model configuration in Model Builder (standard or external)
  - Named Credential storing the provider API key securely
  - Model alias mapped to the chosen model and ready for use in prompt templates, copilot, and Einstein features
  - Decision guidance on model selection by use case
  - Review checklist confirming registration, alias assignment, and connectivity test passage
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Model Builder and Bring Your Own LLM (BYOLLM)

This skill activates when a practitioner needs to register an external LLM provider (OpenAI, Anthropic, Azure OpenAI, or other OpenAI-compatible endpoints) with Salesforce via Model Builder, select or change the standard model powering Einstein features, configure the model alias that features reference, test connectivity, or troubleshoot model registration failures. It covers Mode 1 (register a new external LLM), Mode 2 (review and manage current model configuration), and Mode 3 (troubleshoot model connectivity and alias failures).

---

## Before Starting

Gather this context before working on anything in this domain:

- **License and feature flag:** Model Builder and BYOLLM registration require that Einstein generative AI features are enabled in the org. Navigate to Setup > Einstein Generative AI and confirm the toggle is on. The Einstein for Agentforce or Einstein 1 license is typically required. Without the flag enabled, the Model Builder menu entry under Setup will not appear.
- **External provider prerequisites:** If registering an external LLM, you must have a valid API key from the provider (OpenAI, Anthropic, Azure OpenAI, etc.) and know the base endpoint URL. For Azure OpenAI, you also need the deployment name and API version in addition to the endpoint and key.
- **Most common wrong assumption:** Practitioners assume they can change the model behind a model alias without impact. In reality, every Agentforce agent, prompt template, and Einstein feature that references an alias immediately begins using the new model once the alias is updated. There is no gradual rollout or per-feature override — the alias change is global and instant.
- **Platform constraints:** Model Builder supports Salesforce-standard models (e.g., Salesforce-hosted versions of Llama-family models) and external models via OpenAI-compatible APIs. Not all external models support all Einstein feature types. Specifically, models that do not support function calling (tool use) cannot back agentic Agentforce actions. Confirm capability coverage before selecting a model for an agent-heavy use case.
- **Named Credential requirement:** External model API keys must be stored as Named Credentials (External Credentials) in Salesforce, not as plaintext fields in Model Builder. This is both a platform enforcement and a Trust Layer requirement — keys stored outside Named Credentials will be rejected.

---

## Core Concepts

### Model Builder and Model Aliases

Model Builder is the Salesforce UI (Setup > Model Builder) where administrators register LLM configurations and manage the model aliases that Einstein and Agentforce features use to call those models. A model alias is a logical name — such as `sfdc_ai__DefaultGPT4Omni` or a custom alias — that decouples the consuming feature from the specific underlying model.

When a prompt template or Agentforce agent is configured to use a model alias, it does not directly reference a provider or endpoint. It references the alias, and Model Builder resolves that alias to the actual registered model at runtime. This indirection is what allows an administrator to swap the underlying model without modifying every consuming feature. The downside is that alias changes are immediate and global — there is no A/B testing or canary rollout built into the alias system.

Salesforce ships a set of default aliases for standard features. Administrators can add custom aliases pointing to external models. Aliases can only point to one model at a time.

### External Model Registration (BYOLLM)

Registering an external LLM in Model Builder involves three steps:

1. **External Credential (Named Credential):** Create an External Credential in Setup > Named Credentials that stores the provider API key using a Custom authentication protocol. Add a Principal for the credential with the API key as a parameter. This credential is later referenced by the Model Builder external model configuration.
2. **Model Builder registration:** In Setup > Model Builder > Add Model, choose the appropriate provider type (OpenAI, Azure OpenAI, Anthropic, or custom OpenAI-compatible). Provide the endpoint URL, the model identifier (e.g., `gpt-4o`, `claude-3-5-sonnet-20241022`), and select the Named Credential created in step 1. Salesforce enforces that the API key travels through Named Credentials — it is never stored in plaintext in the model record.
3. **Alias assignment:** After registering the external model, create or update a model alias to point to it. Features that reference that alias will now use the external model.

For Azure OpenAI, the endpoint format is `https://<resource>.openai.azure.com/openai/deployments/<deployment-name>` and the API version must be specified (e.g., `2024-02-01`). Azure uses a different auth header (`api-key`) compared to OpenAI's bearer token; Salesforce handles this difference automatically when the provider type is set to Azure OpenAI.

### Model Selection: Cost vs. Quality Tradeoffs

Salesforce Model Builder exposes both Salesforce-standard models and externally registered models for alias assignment. Choosing the right model for a given use case requires balancing:

- **Quality:** Larger frontier models (GPT-4o, Claude 3.5 Sonnet, Llama 3.1 405B) produce better reasoning for complex agentic tasks but cost more per token and have higher latency.
- **Cost:** Smaller or mid-tier models (GPT-4o mini, Claude 3 Haiku, Llama 3.1 70B) are significantly cheaper per token and faster, making them appropriate for high-volume summarization, classification, or extraction tasks where perfect reasoning is not required.
- **Function calling support:** Agentforce agents that execute actions (call Apex, query records, update fields) require a model that supports function calling (tool use). Not all models support this; models without function calling are limited to text generation use cases (e.g., email drafting, document summarization).
- **Context window:** Use cases that pass large amounts of data (long email threads, large record sets, document chunks) require models with larger context windows. Verify the model's context limit against the prompt size estimates for the target feature.

### Testing Model Connectivity

Model Builder provides a built-in **Test Connection** capability on each registered external model. This sends a minimal API request to the provider using the configured Named Credential and endpoint, and reports success or failure. Running this test is mandatory after every registration or credential update before the model is used in a live alias.

---

## Common Patterns

### Mode 1: Registering an External LLM (BYOLLM) End-to-End

**When to use:** An organization wants to use a non-Salesforce-hosted model (e.g., their own Azure OpenAI deployment or an Anthropic API subscription) to power Agentforce agents or Einstein features, either to meet data residency requirements, control model version, or optimize cost.

**How it works:**

1. Obtain the provider API key and endpoint URL from the provider console (OpenAI Platform, Azure Portal, Anthropic Console).
2. In Salesforce Setup > Named Credentials > External Credentials, create a new External Credential:
   - Authentication Protocol: Custom
   - Add a Principal for the Org (or Per-User if user-level key isolation is needed)
   - Add a Custom Header parameter named `Authorization` with value `Bearer <API_KEY>` (for OpenAI/Anthropic) or `api-key` header with key value (for Azure OpenAI)
3. In Setup > Named Credentials, create a Named Credential that references the External Credential and points to the provider's base domain (e.g., `https://api.openai.com`).
4. Navigate to Setup > Model Builder > Add Model.
5. Select the provider type (OpenAI, Azure OpenAI, Anthropic, or OpenAI-compatible).
6. Enter the model identifier (e.g., `gpt-4o-mini` for OpenAI, `claude-3-5-haiku-20241022` for Anthropic).
7. Select the Named Credential created in step 3.
8. For Azure OpenAI, enter the full deployment endpoint and API version.
9. Save the model record.
10. Click Test Connection. Confirm success before proceeding.
11. Navigate to Model Builder > Model Aliases.
12. Create a new alias (e.g., `MyOrg_AzureGPT4o`) or update an existing alias to point to the newly registered model.
13. In any prompt template or Agentforce agent that should use this model, select the alias by name.

**Why not use Salesforce-standard models:** Standard models are governed by Salesforce's model version cadence. Organizations with strict model version pinning requirements, data processing agreements with a specific provider, or cost optimization needs at high volume benefit from controlling the model directly via BYOLLM.

### Mode 2: Reviewing Current Model Configuration

**When to use:** Before a release, during a model cost review, or when onboarding a new Agentforce feature, verify which model is behind each alias and confirm all external models are healthy.

**How it works:**

1. Navigate to Setup > Model Builder > Model Aliases. Review each alias and its current model assignment.
2. For each alias backed by an external model, open the model record and click Test Connection. Confirm the test passes.
3. Check the Named Credential associated with each external model — confirm the credential has not expired or been rotated without updating the credential record.
4. Review which Agentforce agents and prompt templates reference each alias (visible in the alias detail view if the feature is surfaced in your org version).
5. Document the alias-to-model mapping and the date of the last connectivity test.

### Mode 3: Troubleshooting Model Connectivity Failures

**When to use:** An Agentforce agent or Einstein feature fails with a model-related error, Test Connection returns an error in Model Builder, or prompt templates return generic failure responses.

**How it works:**

1. **Run Test Connection** on the failing model in Setup > Model Builder. The error message returned typically indicates whether the failure is authentication (401/403), endpoint resolution (DNS or URL misconfiguration), or rate limiting (429).
2. **401/403 errors:** Open the Named Credential and External Credential associated with the model. Verify the API key value is current — if the provider key was rotated, update the Principal parameter in the External Credential. Do not store the new key anywhere other than the External Credential.
3. **404 or endpoint errors:** For Azure OpenAI, confirm the deployment name and API version in the model endpoint URL are correct. For OpenAI-compatible endpoints, confirm the base URL includes the correct path prefix (some providers use `/v1/` and some use a different prefix).
4. **429 / rate limit errors:** The external provider's quota or rate limit is being exceeded. Review provider-side usage logs. Consider upgrading the provider tier or switching to a model with a higher rate limit for high-volume use cases.
5. **Feature errors despite passing Test Connection:** Confirm the registered model supports function calling if the failing feature is an Agentforce agent with actions. A model that passes the connectivity test but does not support tool use will fail at runtime when the agent attempts to invoke an action.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Agentforce agent with action invocations (tool use) | Choose a model with confirmed function calling support (GPT-4o, Claude 3.5 Sonnet, Llama 3.1 with tool support) | Models without function calling cannot invoke Agentforce actions at runtime |
| High-volume email or document summarization | Use a smaller, cheaper model (GPT-4o mini, Claude 3 Haiku) via a custom alias | Frontier models are unnecessary for extraction/summarization; cost savings are significant at scale |
| Data residency requirement (e.g., EU data boundary) | Register Azure OpenAI deployment in the required region via BYOLLM | Salesforce-standard models may not offer region-specific data residency; Azure OpenAI supports EU regions |
| Model version pinning required by compliance | Use BYOLLM with a specific provider model ID | Salesforce-standard models may update underlying model versions; BYOLLM gives direct version control |
| Testing a new model before production rollout | Create a new alias pointing to the test model; use it only in sandbox prompt templates | Aliases are global — never update the production alias until testing is complete |
| External model API key rotated by provider | Update the Principal parameter in the External Credential in Named Credentials — nowhere else | API keys must remain within Named Credentials; updating any other location will not take effect and may leave keys exposed |
| Organization wants Salesforce-managed model updates | Use the default Salesforce-standard model aliases | Salesforce manages the underlying model version; no provider account or key management required |
| Multiple features need different models | Create distinct aliases for each feature type (e.g., `AgentAlias` for agentic tasks, `SummaryAlias` for summarization) | One alias per use case prevents a model swap for one feature from inadvertently affecting another |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking a Model Builder / BYOLLM implementation complete:

- [ ] Einstein generative AI feature flag confirmed enabled in Setup > Einstein Generative AI
- [ ] Named Credential and External Credential created; API key stored only in the External Credential Principal — never in plaintext
- [ ] External model registered in Model Builder with correct provider type, model ID, and endpoint
- [ ] Test Connection passes on all registered external models
- [ ] Model alias created or updated and pointing to the intended model
- [ ] Model capability confirmed: function calling supported if the alias will back an Agentforce agent with actions
- [ ] Context window size verified against expected prompt sizes for the target feature
- [ ] Alias-to-model mapping documented for ops reference (which features use which alias)
- [ ] Sandbox testing completed using a separate alias before updating any production alias
- [ ] API key rotation procedure documented: who rotates, where to update (External Credential only), how to re-test

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Alias changes are global and immediate** — Updating a model alias in Model Builder affects every Agentforce agent, prompt template, and Einstein feature that references that alias, simultaneously and without warning. There is no canary rollout, feature-level override, or audit log of what changed. A model swap intended for one feature can silently degrade quality or break action invocation for unrelated features. Always create a new alias for testing and only update the shared alias after full validation.
2. **Sandbox and production model configurations are independent** — Model Builder registrations, Named Credentials, and alias configurations do not deploy automatically from sandbox to production via change sets or the Salesforce CLI. Each environment must be configured independently. Organizations that test a new external model in sandbox and then "go live" must manually replicate every Named Credential, External Credential, and model registration step in production. Scripting this with the Metadata API or Salesforce CLI (where Model Builder metadata types are supported) is strongly recommended for repeatability.
3. **API rate limits are provider-side, not Salesforce-side** — Salesforce does not enforce rate limiting on calls to external LLMs beyond what the platform's own request infrastructure imposes. If an Agentforce feature drives high query volume to an external provider, the provider's rate limits (requests-per-minute or tokens-per-minute) will cause 429 errors that surface as generic model failures in Salesforce. These failures are not visible in standard Salesforce debug logs — they require provider-side monitoring or a middleware logging layer. Monitor provider usage dashboards proactively rather than waiting for user-reported failures.
4. **Named Credential permission sets are required for external model calls** — The user or process invoking the external model must have access to the Named Credential via a Permission Set that grants Named Credential access. If this permission is missing, the model call will fail with a credential access error that may appear as a generic LLM failure rather than a permissions error. Check Permission Set assignments for Named Credential access whenever a specific user or profile reports model failures that other users do not experience.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Registered external model record | Model Builder entry linking a provider type, endpoint, model ID, and Named Credential |
| Named Credential + External Credential | Salesforce Named Credential securely storing the provider API key via External Credential Principal |
| Model alias | Logical alias name mapped to the registered model, referenced by Agentforce agents and prompt templates |
| Test Connection result | Confirmation that the model endpoint and credentials are valid and reachable from Salesforce |
| Alias-to-model mapping document | Ops reference listing each alias, its current model, and the features that consume it |

---

## Related Skills

- agentforce/agentforce-trust-layer — use when configuring data masking, audit trail, toxicity detection, and grounding rules that govern how model outputs are processed; Trust Layer sits between the model and the user
- agentforce/prompt-builder-templates — for authoring and managing the prompt templates that reference model aliases and are grounded with Salesforce data
- security/named-credentials-setup — for detailed Named Credential and External Credential configuration patterns beyond the model-registration context
