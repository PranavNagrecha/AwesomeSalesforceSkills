# LLM Anti-Patterns — Model Builder and BYOLLM

Common mistakes AI coding assistants make when generating or advising on Salesforce Model Builder and Bring Your Own LLM configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Updating a Shared Alias Without Impact Assessment

**What the LLM generates:** "Update the default model alias to point to the new GPT-4o model" without warning about the blast radius.

**Why it happens:** LLMs treat alias updates as simple configuration changes. Training data does not emphasize that alias changes are global and immediate with no canary rollout.

**Correct pattern:**

```
Updating a model alias in Model Builder immediately affects EVERY Agentforce
agent, prompt template, and Einstein feature that references that alias —
simultaneously and without warning. There is no canary rollout, feature-level
override, or undo mechanism.

Safe model swap workflow:
1. Create a NEW alias pointing to the new model (e.g., "MyOrg_GPT4o_Test").
2. Update a SANDBOX prompt template or agent to use the new alias.
3. Test thoroughly.
4. Only update the shared production alias after full validation.
```

**Detection hint:** If the advice updates an existing production alias directly without creating a test alias first, all consuming features may be affected simultaneously.

---

## Anti-Pattern 2: Storing API Keys Outside Named Credentials

**What the LLM generates:** "Enter the API key in the Model Builder registration form" or "Store the API key in a Custom Setting."

**Why it happens:** LLMs generate the simplest credential configuration path. Training data from other platforms does not enforce the Named Credential requirement.

**Correct pattern:**

```
External model API keys MUST be stored as Named Credentials (External
Credentials) in Salesforce. Keys stored outside Named Credentials will be
rejected by the platform.

Correct setup:
1. Create an External Credential with a Principal storing the API key.
2. Create a Named Credential referencing the External Credential.
3. Select the Named Credential in Model Builder during model registration.
4. Never store the key in Custom Settings, Custom Metadata, or plaintext.
```

**Detection hint:** If the advice stores an API key anywhere other than an External Credential Principal, it violates platform requirements and Trust Layer enforcement.

---

## Anti-Pattern 3: Selecting a Model Without Function Calling for Agentforce Actions

**What the LLM generates:** "Register Claude 3 Haiku as the model for your Agentforce agent to save costs" without checking whether the model supports function calling.

**Why it happens:** LLMs optimize for cost when asked about model selection. They do not consistently verify whether the selected model supports the tool-use capability required for Agentforce action invocation.

**Correct pattern:**

```
Agentforce agents that execute actions (call Apex, query records, update fields)
require a model that supports function calling (tool use). Models without this
capability can only generate text — they cannot invoke agent actions at runtime.

Before selecting a model for an agent-heavy use case:
- Confirm the model explicitly supports function calling / tool use.
- Models with confirmed support: GPT-4o, Claude 3.5 Sonnet, Llama 3.1 (with
  tool support enabled).
- Test the agent's action invocation in preview BEFORE switching the alias.
```

**Detection hint:** If the advice selects a model for an Agentforce agent without verifying function calling support, the agent will fail at runtime when attempting to invoke actions.

---

## Anti-Pattern 4: Assuming Sandbox and Production Share Model Configuration

**What the LLM generates:** "Test the model in sandbox and it will deploy to production with your change set."

**Why it happens:** LLMs assume Salesforce metadata deployment patterns apply uniformly. Model Builder registrations, Named Credentials, and alias configurations do NOT deploy automatically via change sets or the Salesforce CLI in all cases.

**Correct pattern:**

```
Sandbox and production Model Builder configurations are INDEPENDENT. Each
environment must be configured separately:
- Named Credential and External Credential (with API key)
- Model registration in Model Builder
- Model alias creation and assignment

Organizations testing a new model in sandbox must manually replicate every
configuration step in production. Script this with Metadata API or Salesforce
CLI where supported for repeatability.
```

**Detection hint:** If the advice implies sandbox model configurations deploy to production automatically, the production environment will have no model configuration after deployment.

---

## Anti-Pattern 5: Ignoring Provider-Side Rate Limits

**What the LLM generates:** Model registration advice with no mention of provider rate limits or monitoring.

**Why it happens:** LLMs focus on Salesforce-side configuration. Provider-side rate limits (requests-per-minute, tokens-per-minute) are outside the Salesforce platform and training data does not consistently cover cross-platform capacity planning.

**Correct pattern:**

```
Salesforce does not enforce rate limiting on calls to external LLMs. If an
Agentforce feature drives high volume to an external provider, the provider's
rate limits cause 429 errors that surface as GENERIC model failures in
Salesforce. These failures are NOT visible in standard Salesforce debug logs.

Before going live:
- Check the provider's rate limit tier for your API key.
- Estimate peak concurrent agent sessions multiplied by calls per session.
- Monitor the provider usage dashboard proactively.
- Consider upgrading the provider tier for production workloads.
```

**Detection hint:** If the advice registers an external model without discussing provider rate limits and monitoring, production failures from 429 errors will appear as unexplained model failures.

---

## Anti-Pattern 6: Missing Named Credential Permission Set Assignment

**What the LLM generates:** Model registration steps without mentioning that calling users need Named Credential access via a Permission Set.

**Why it happens:** LLMs cover the admin configuration steps but miss the user-facing permission requirement. Named Credential access is a Permission Set assignment, not a profile default.

**Correct pattern:**

```
The user or process invoking the external model must have access to the Named
Credential via a Permission Set. Without this, the model call fails with a
credential access error that may appear as a generic LLM failure.

After registering a model:
1. Create or update a Permission Set that grants access to the Named Credential.
2. Assign the Permission Set to all users and integration users that will
   invoke the model (directly or via Agentforce agents).
3. If only certain users report model failures, check Named Credential
   Permission Set assignments first.
```

**Detection hint:** If the advice completes model registration without assigning Named Credential access via Permission Sets, specific users will get model failures that others do not experience.
