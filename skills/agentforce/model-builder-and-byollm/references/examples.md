# Examples: Model Builder and BYOLLM

Steps follow the Data Cloud guide (Bring Your Own Large Language Model; Add a Foundation Model; Configure and Test a Model in Model Playground) and the Generative AI guide (Large Language Model Support; Changing LLM Configurations; Agentforce Agents considerations), Summer '26. Correction (2026-10-03): earlier versions of these examples used "Setup > Model Builder > Add Model," a Named Credential field, a Test Connection button, and aliases that Agentforce agents reference. Those are replaced with the documented flow, and the agent example is corrected because agents don't use BYO models.

## Example 1: Connecting an Azure OpenAI Deployment for a Prompt Builder Template

**Context:** A financial services org has an approved Azure OpenAI `gpt-4o` deployment in an EU region and wants its client-letter prompt template to run on it.

**Problem:** The first plan was to point the service agent at the deployment. The guide says the agent reasoning engine uses OpenAI GPT-4o and that bringing your own model isn't supported for agents, so the BYO model is scoped to Prompt Builder.

**Solution (configuration procedure):**

1. Confirm Einstein Generative AI is enabled and that Azure OpenAI is not blocked in EinsteinGptSettings.
2. Einstein Studio > Generative tab > Add Foundation Model > Azure OpenAI.
3. Endpoint name `AzureOpenAI_EUWest`; URL `https://<resource>.openai.azure.com` (HTTPS on port 443).
4. Authentication details from the Azure portal; model information: the Azure deployment name `gpt-4o`.
5. Save & Test, enter the exact model name, Connect, name it `AzureOpenAI_EUWest_GPT4o`, and select the model version.
6. Model Playground > Create model: select the foundation model, keep penalties at 0, enable data masking in prompt settings, and test three real prompts.
7. Save the configuration as `ClientLetters_AzureEU`.
8. In Prompt Builder, open the client-letter template, Save As > Save as a New Version, select `ClientLetters_AzureEU` in the model configuration panel, preview, and activate.
9. Set `disableAIProviderRegionFallback` to true in EinsteinGptSettings so Azure OpenAI requests do not fall back outside the endpoint region. File `force-app/main/default/settings/EinsteinGpt.settings-meta.xml` (full policy file in `references/metadata-examples.md`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EinsteinGptSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <disableAIProvAzureOpenAI>false</disableAIProvAzureOpenAI>
    <disableAIProviderRegionFallback>true</disableAIProviderRegionFallback>
    <enableEinsteinGptPlatform>true</enableEinsteinGptPlatform>
</EinsteinGptSettings>
```

**Why it works:** The connection lives in Einstein Studio, the configuration is tested before use, and the change reaches users only when a new template version is activated. UNVERIFIED (2026-10-03): the authentication fields shown for Azure OpenAI in Add Foundation Model were not listed in the fetched guide; follow the screen.

---

## Example 2: Cutting Cost on a High-Volume Summarization Template

**Context:** An email-thread summarization template runs about 50,000 times a day on GPT-4o.

**Problem:** Summarization does not need GPT-4o's reasoning, and "Changing the model can affect your usage."

**Solution:**

1. GPT-4o Mini is a Salesforce-managed model, so no BYO connection is needed.
2. In Prompt Builder, Save As > Save as a New Version of the summarization template, choose GPT-4o Mini in the model configuration panel, and keep the original version active.
3. Preview the new version on a sample of 50 real threads and compare against the active version.
4. Check the volume against the org's default 300 generation requests per minute; schedule the batch flow to stay under it.
5. Activate the new version when quality is acceptable. Rolling back means activating the previous version.

A retrieved template then shows two versions with different models, only one of them active (excerpt; the full file shape is in `references/metadata-examples.md`):

```xml
<!-- excerpt of GenAiPromptTemplate: two templateVersions, one active -->
<GenAiPromptTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <activeVersionIdentifier>summary_v2</activeVersionIdentifier>
    <templateVersions>
        <primaryModel>sfdc_ai__DefaultOpenAIGPT4</primaryModel>
        <status>Published</status>
        <versionIdentifier>summary_v1</versionIdentifier>
    </templateVersions>
    <templateVersions>
        <primaryModel>REPLACE_WITH_GPT4O_MINI_API_NAME</primaryModel>
        <status>Published</status>
        <versionIdentifier>summary_v2</versionIdentifier>
    </templateVersions>
</GenAiPromptTemplate>
```

UNVERIFIED (2026-10-03): the API name for GPT-4o Mini is not listed in a fetched source; copy it from a retrieved template after selecting the model in Prompt Builder.

**Why it works:** Each template version carries its own model, only the active version's model is used, and the previous version stays available for an instant rollback.

---

## Anti-Pattern: Editing the Shared Configuration to Try a New Model

**What practitioners do:** An admin opens the model configuration used by several templates and switches its settings to try a newer model.

**What goes wrong:** "Updating model settings can affect the performance of associated prompts," so every template on that configuration changes at once.

**Correct approach:** Create a new configuration in Model Playground, attach it to a new version of one template, test, and activate template by template.
