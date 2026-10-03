# Gotchas: Model Builder and BYOLLM

Non-obvious behaviours that waste a BYO model purchase, break prompts in production, or route requests where policy says they must not go. Each gotcha names its source. "Data Cloud Guide" means the Data Cloud guide, Summer '26 (data_cloud.pdf), chapter Use AI Models (Bring Your Own Large Language Model; Configure and Test a Model in Model Playground). "GenAI Guide" means Quickstart Your Einstein Generative AI Solution, Spring '26 (generative_ai.pdf). "Metadata API" means the Metadata API Developer Guide, Version 67.0.

## Gotcha 1: Agents Don't Use BYO Models

**What happens:** A team connects its Azure OpenAI deployment to "power the service agent" and the agent's behaviour does not change.

**When it occurs:** "The Agentforce platform supports OpenAI GPT-4o for reasoning engine calls. Agent actions can make calls to other predefined LLMs. Bringing your own model isn't supported, but custom actions that execute prompt templates can use any Salesforce-managed model." The same is repeated under Considerations for Custom Actions.

**How to avoid:** Use BYOLLM for Prompt Builder templates, the Models API, and custom apps. For agents, tune topics, actions, and prompt templates instead, and pick Salesforce-managed models for custom actions that run templates.

**Source:** GenAI Guide, Agentforce Agents considerations; Considerations for Custom Actions.

---

## Gotcha 2: Editing a Model Configuration Changes Every Prompt That Uses It

**What happens:** An admin raises the temperature on a configuration to improve one template, and three other templates start producing looser output.

**When it occurs:** "If your model is already associated with prompts, create a new model instead. Updating model settings can affect the performance of associated prompts." In Prompt Builder, "Each version of a prompt template can contain a different model configuration. Only the configuration model in the activated version is used," and activated versions are immutable. Correction (2026-10-03): earlier versions described this as a global "alias" switch with no audit log; the guide does not use the alias term.

**How to avoid:** Create a new configuration for any change, point a new template version at it, preview, and activate template by template.

**Source:** Data Cloud Guide, Edit a Model Configuration. GenAI Guide, Changing LLM Configurations.

---

## Gotcha 3: A Foundation Model in Use Can't Be Edited, and Deletion Is Permanent

**What happens:** An admin tries to change the endpoint of a connected model and the edit is blocked, or deletes the model to start again and loses it.

**When it occurs:** "You can edit most of your foundation model settings as long as the model isn't a source for other models. If it's used as a source, you must first delete all associated model configurations." "You can't recover a model after it's deleted."

**How to avoid:** For an endpoint or credential change on a model in use, add a new foundation model, build configurations on it, move template versions, then retire the old one.

**Source:** Data Cloud Guide, Edit or Delete a Foundation Model.

---

## Gotcha 4: The Endpoint Must Be HTTPS on Port 443, and Each Provider Needs Its Own Details

**What happens:** Save & Test fails against a gateway on a custom port, or an Azure model connects to the wrong deployment.

**When it occurs:** "To connect to a remote model endpoint, a standard HTTPS 443 port is required." "If you're connecting an Azure Open AI model, enter the Azure deployment." "If you're connecting an OpenAI fine-tuned model, select Yes when prompted during setup." "For Amazon Bedrock, use Anthropic" as the model type.

**How to avoid:** Front any internal gateway with HTTPS on 443. Copy the Azure deployment name from the Azure OpenAI dashboard, and record each provider's details in the runbook. The skill checker flags LLM endpoints in metadata that use HTTP or another port (`MB-HTTPS-01`).

**Source:** Data Cloud Guide, Add a Foundation Model (step 4).

---

## Gotcha 5: The Org Has a 300-Request-Per-Minute Generation Limit, Plus Provider Limits

**What happens:** A batch flow that drafts emails for thousands of records starts failing partway through.

**When it occurs:** "Customers have a default rate limit of 300 Large Language Model (LLM) generation requests per minute at their Salesforce Organization ID level. These generations can be triggered from Prompt Builder, Einstein Studio, or Models API (REST, Apex)." A BYO provider's own quota applies on top. Correction (2026-10-03): earlier versions said Salesforce does not rate-limit external LLM calls.

**How to avoid:** Size bulk jobs below 300 generations per minute, throttle flows, and watch provider usage. Ask the account executive for a limit increase when volume needs it. Use Model Activity in Einstein Studio to see inference and error trends.

**Source:** GenAI Guide, Considerations for Einstein Generative AI (Rate Limits). Data Cloud Guide, Monitor Model Activity.

---

## Gotcha 6: Deprecated Models Are Rerouted, and Can't Be Picked in Model Playground

**What happens:** Output style changes overnight on a template nobody touched.

**When it occurs:** "After the model is no longer available, Salesforce reroutes requests to the next closest replacement model on the Reroute Date." "When configuring a model in Einstein Studio Model Playground, deprecated models can't be selected." Rerouting notices are published "30 days prior to the model's retirement date." The guide lists GPT-4 32k, Azure GPT-3.5 Turbo 16k, and GPT-3.5 Turbo 16k as deprecated.

**How to avoid:** Assign an owner to read the monthly Einstein Platform release notes. On a deprecation notice, create a configuration on the replacement "with the same hyperparameters as the retired model," retest templates (and agents end to end), then activate new versions before the reroute date.

**Source:** GenAI Guide, Large Language Model Support (Deprecated Models; Prepare for Model Deprecation and Rerouting).

---

## Gotcha 7: Blocking a Provider Blocks It for Every Generative AI Feature

**What happens:** Security blocks OpenAI in a settings deployment, and an existing template that runs on an OpenAI model stops working.

**When it occurs:** EinsteinGptSettings has `disableAIProvOpenAI`, `disableAIProvAzureOpenAI`, `disableAIProvAWSBedrock`, and `disableAIProvVertexGemini`, each meaning the provider "is turned off and access to its models are blocked." UNVERIFIED (2026-10-03): which standard features depend on which provider is not listed in the fetched sources.

**How to avoid:** Before blocking, list every template version's model and move affected templates to an allowed provider. The checker flags templates whose model names a blocked provider (`MB-PROV-01`).

**Source:** Metadata API, EinsteinGptSettings.

---

## Gotcha 8: Geo-Aware Routing Falls Back to the US

**What happens:** An EU org's audit data shows requests served from a US region.

**When it occurs:** "If a model isn't available in a nearby region, the requests are routed to the US. You can't disable geo-aware routing and rerouting to the US when models aren't available in a nearby region." For orgs that enabled the platform on or after June 13, 2024, the generative AI region matches the Data Cloud region. Separately, `disableAIProviderRegionFallback` "Indicates whether the fallback of Azure OpenAI requests outside the model endpoint region for your org is turned off."

**How to avoid:** Choose models available in the required region, set `disableAIProviderRegionFallback` to true when Azure OpenAI must stay in region, and confirm routing in the audit and feedback data.

**Source:** GenAI Guide, Geo-Aware LLM Request Routing. Metadata API, EinsteinGptSettings.

---

## Gotcha 9: Playground Settings Are Not Saved With the Configuration

**What happens:** A configuration that looked safe in Model Playground with masking on behaves differently in production.

**When it occurs:** Playground prompt settings (responses per prompt, stop sequence, masking) "are used only during testing. They aren't saved with your model configuration." "If you don't enable masking in Model Playground, org-level data masking settings are applied." Temperature ranges 0 through 2, and "Only Anthropic models have this setting available for testing."

**How to avoid:** Treat the playground as a test bench. Confirm org-level masking in Einstein Trust Layer setup, and verify the final behaviour in Prompt Builder preview with the template version that will go live.

**Source:** Data Cloud Guide, Create a Model Configuration; Data Masking; Test Your Prompt.
