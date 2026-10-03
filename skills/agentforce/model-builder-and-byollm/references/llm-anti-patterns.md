# LLM Anti-Patterns: Model Builder and BYOLLM

Mistakes AI assistants make when advising on Einstein Studio foundation models, model configurations, and provider settings, with the correct move for each. Correction (2026-10-03): the previous version of this file was built on a "Setup > Model Builder > Add Model" flow with Named Credentials, a Test Connection button, global model aliases, and function-calling requirements for agents. The Data Cloud and Generative AI guides document a different model, reflected below.

## Anti-Pattern 1: Planning a BYO Model for Agent Reasoning

**What the LLM generates:** "Register your Azure OpenAI deployment and point the Agentforce agent at it."

**Why it happens:** Models generalize BYOLLM to every generative feature.

**Correct pattern:**

```
"The Agentforce platform supports OpenAI GPT-4o for reasoning engine calls...
Bringing your own model isn't supported, but custom actions that execute prompt
templates can use any Salesforce-managed model." (GenAI guide)

- BYOLLM: Prompt Builder templates, Models API, custom apps.
- Agents: tune topics, actions, and prompt templates; use Salesforce-managed
  models in custom actions that run templates.
```

**Detection hint:** A plan that connects a BYO model "for the agent."

---

## Anti-Pattern 2: Editing a Live Model Configuration

**What the LLM generates:** "Open the model configuration and raise the temperature to 0.9; all templates will pick it up."

**Why it happens:** One central change looks efficient.

**Correct pattern:**

```
"If your model is already associated with prompts, create a new model instead.
Updating model settings can affect the performance of associated prompts."

1. Create a new configuration in Model Playground.
2. Save a new prompt template version that uses it, preview, activate.
3. Repeat per template; retire the old configuration when nothing uses it.
```

**Detection hint:** "Update the model" or "change the alias" for a configuration that templates already use.

---

## Anti-Pattern 3: Hard-Coding Provider Keys in Apex, Flows, or Custom Metadata

**What the LLM generates:** An Apex class with `req.setHeader('api-key', 'abc123...')` calling the provider directly.

**Why it happens:** Direct callouts are the familiar integration pattern.

**Correct pattern:**

```
Connect the provider in Einstein Studio (Add Foundation Model takes the endpoint
and authentication details) and call it through Prompt Builder or the Models API.
A direct Apex callout to a provider is not an Einstein generative AI feature,
and "Einstein Trust Layer capabilities apply only to Einstein Generative AI features."

If a callout is truly required, keep the secret in a Named Credential or
External Credential, never in source.
```

**Detection hint:** Provider key prefixes (for example `sk-`) or `api-key` headers with literal values in source. The checker reports `MB-KEY-01` and `MB-DIRECT-01`.

---

## Anti-Pattern 4: Assuming Sandbox and Production Share Model Configuration

**What the LLM generates:** "Test the new model in the sandbox; once it works it will be live in production."

**Why it happens:** Models assume configuration replicates.

**Correct pattern:**

```
UNVERIFIED (2026-10-03): no fetched source describes how foundation models and
model configurations move between orgs. Treat each org as separate:
- Recreate the foundation model and configuration in production.
- Re-run Save & Test and the playground tests there.
- Deploy prompt templates whose primaryModel matches the production configuration.
```

**Detection hint:** A go-live plan with no production connection step.

---

## Anti-Pattern 5: Ignoring Either Side's Rate Limit

**What the LLM generates:** "Salesforce doesn't throttle LLM calls; only the provider does."

**Why it happens:** Older guidance said so.

**Correct pattern:**

```
Salesforce: "a default rate limit of 300 Large Language Model (LLM) generation
requests per minute at their Salesforce Organization ID level" (Prompt Builder,
Einstein Studio, Models API).
Provider: the account's own requests and tokens per minute.

Size bulk jobs to the lower of the two and monitor Model Activity.
```

**Detection hint:** A bulk generation design with no requests-per-minute estimate.

---

## Anti-Pattern 6: Blocking a Provider Without Moving Its Templates

**What the LLM generates:** "Set disableAIProvOpenAI to true to meet policy."

**Why it happens:** The setting looks self-contained.

**Correct pattern:**

```
Blocking a provider blocks access to its models org-wide (EinsteinGptSettings).
Before deploying the block:
1. List every active template version's primaryModel.
2. Move templates on the blocked provider to an allowed model.
3. Deploy the block, then preview the moved templates.
```

**Detection hint:** A provider block in a settings deployment with no template inventory. The checker reports `MB-PROV-01`.

---

## Anti-Pattern 7: Claiming Data Residency From Model Choice Alone

**What the LLM generates:** "Pick the EU Azure deployment and all requests stay in the EU."

**Why it happens:** Region of the endpoint is taken as region of every request.

**Correct pattern:**

```
Geo-aware routing sends requests to the US when a model isn't available nearby,
and that rerouting can't be disabled. For Azure OpenAI, set
disableAIProviderRegionFallback to true to stop fallback outside the endpoint
region. Verify where requests went in the audit and feedback data.
```

**Detection hint:** A residency statement with no mention of fallback.
