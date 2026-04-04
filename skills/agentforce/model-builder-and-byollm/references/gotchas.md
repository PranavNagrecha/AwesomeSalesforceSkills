# Gotchas — Model Builder and BYOLLM

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Alias Changes Are Global, Immediate, and Silent

**What happens:** When an administrator updates a model alias in Model Builder to point to a different model, the change takes effect instantly for every Agentforce agent, prompt template, and Einstein feature that references that alias — across all active sessions and users. There is no feature-level override, gradual rollout, or built-in audit notification. Features that were working correctly can degrade or break within seconds of an alias update if the new model has different capabilities (e.g., no function calling) or different output format expectations.

**When it occurs:** Any time a shared model alias is updated — whether for testing, cost optimization, or a model version upgrade — in a production org where multiple features reference the same alias.

**How to avoid:** Never test new models by updating a shared production alias. Create a purpose-specific alias (e.g., `Test_NewModel_Sandbox`) for testing. In sandbox, clone the relevant prompt templates to use the test alias. Only merge the alias change to production after thorough validation, and schedule the change during a low-usage window. Document all aliases and their consuming features in an ops reference before making any change.

---

## Gotcha 2: Sandbox and Production Model Configurations Are Not Automatically Synced

**What happens:** Model Builder registrations, Named Credentials, External Credentials, and model alias configurations are environment-specific. They do not flow from sandbox to production via standard change sets, and the Metadata API coverage for Model Builder metadata types (such as `AIModel` and `GenAiModelDefinition`) is still maturing. Teams that carefully test a BYOLLM configuration in sandbox and then attempt to "promote" it to production often discover they must manually replicate every step — External Credential, Named Credential, model record, alias — in the production org. If any step is missed or misconfigured, the production deployment silently falls back to a default model or fails at runtime.

**When it occurs:** Every sandbox-to-production promotion of any Model Builder configuration. Also occurs when refreshing a sandbox — the model configuration in the refreshed sandbox does not reflect production's current state.

**How to avoid:** Treat Model Builder configuration as infrastructure-as-code. Document every Named Credential, External Credential, model ID, endpoint, and alias in a version-controlled runbook. Where the Salesforce CLI supports the relevant metadata types (`sf project deploy`), use it. Where it does not, follow the documented manual runbook exactly. After every production deployment, run Test Connection on all external model records and verify alias assignments.

---

## Gotcha 3: External Provider Rate Limits Surface as Generic Salesforce Errors

**What happens:** Salesforce does not enforce rate limiting on outbound calls to external LLM providers. When an external provider's rate limit (requests-per-minute or tokens-per-minute) is exceeded, the provider returns HTTP 429 responses. Salesforce surfaces these as generic "model request failed" or "LLM unavailable" errors in Agentforce and Einstein features — with no indication in standard Salesforce debug logs that the root cause is a provider-side rate limit. Support and development teams often spend significant time investigating Salesforce configuration before checking provider-side logs.

**When it occurs:** Any high-volume use case (e.g., batch summarization, high-concurrency Agentforce agents) where the per-minute call volume to an external provider exceeds the tier limits on the provider subscription. Rate limits can also be hit suddenly after an org-wide feature rollout increases concurrent usage.

**How to avoid:** Before going live with a high-volume external model use case, determine the provider tier's rate limits (RPM and TPM) and estimate peak call volume. Upgrade the provider tier proactively rather than reactively. Set up provider-side usage dashboards and alerts (OpenAI Usage Dashboard, Azure Monitor, Anthropic Console) to detect rate limit approaches before they impact users. If rate limits cannot be raised sufficiently, consider using Salesforce-standard models for high-volume features (no external rate limits) and reserving the BYOLLM model for lower-volume, higher-quality tasks.

---

## Gotcha 4: Named Credential Permission Sets Must Be Explicitly Assigned

**What happens:** The user context or running process that invokes an external model via Model Builder must have access to the underlying Named Credential granted via a Permission Set. If the Permission Set granting Named Credential access is not assigned to the relevant user, profile, or integration user, the outbound model call fails with a credential access error. This error typically surfaces as a generic LLM call failure in Agentforce rather than a clear permissions error, making it difficult to diagnose without checking Permission Set assignments first.

**When it occurs:** When a Named Credential is newly created for an external model registration but the Permission Set granting access to that credential is not added to all users or profiles that will invoke Agentforce features backed by that model. Also occurs after a sandbox refresh if Permission Set assignments are not replicated.

**How to avoid:** After creating any Named Credential for Model Builder use, immediately verify that the Permission Set granting access to that credential is assigned to the relevant users, integration users, and Agentforce running user profiles. Document this as a step in the BYOLLM deployment runbook and check it first whenever a specific user reports model failures that other users do not experience.

---

## Gotcha 5: Model Capability Mismatch for Agentforce Actions (Function Calling)

**What happens:** Agentforce agents with actions (Apex invocable actions, Flow actions, external service calls) require the backing model to support function calling (also called tool use). If an administrator assigns a model alias to a model that does not support function calling — for example, a text-completion-only model or an older base model — the agent will appear to work in simple Q&A scenarios but will fail with a runtime error when it attempts to invoke any action. The error message is often not specific about function calling support as the root cause.

**When it occurs:** When selecting an external model for a BYOLLM registration without confirming function calling support in the provider's documentation. Also occurs when a provider deprecates or changes a model's capabilities without notice.

**How to avoid:** Before assigning a model to an alias used by any Agentforce agent with actions, confirm in the provider's documentation that the model supports function calling / tool use. For OpenAI models, this is documented per model in the OpenAI model capabilities page. For Anthropic, all Claude 3+ models support tool use. For Azure OpenAI, function calling support depends on the specific deployment version. Run a Model Builder Test Connection and also run a brief manual agent test that triggers an action before considering the configuration production-ready.
