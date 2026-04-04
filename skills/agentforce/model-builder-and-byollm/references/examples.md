# Examples — Model Builder and BYOLLM

## Example 1: Registering an Azure OpenAI Deployment as an External LLM

**Context:** A financial services org has a Microsoft Enterprise Agreement and an existing Azure OpenAI deployment (`gpt-4o`, deployed in the EU West region) that their security team has approved. The team wants to power Agentforce agents with this deployment rather than Salesforce-standard models, to satisfy a data residency requirement that all AI calls remain within the EU.

**Problem:** Without Model Builder BYOLLM registration, Agentforce would default to Salesforce-hosted models whose data residency may not satisfy the EU boundary requirement. The team also needs the API key stored securely — not hardcoded in any configuration field.

**Solution:**

Step 1 — Create the External Credential in Setup > Named Credentials > External Credentials:

```
Label:          AzureOpenAI_EUWest
Name:           AzureOpenAI_EUWest
Auth Protocol:  Custom
Principals:
  - Sequence Number: 1
    Name: OrgPrincipal
    Parameters:
      - Name: api-key
        Value: <paste Azure OpenAI key here>
        Sensitive: true
```

Step 2 — Create the Named Credential:

```
Label:       Azure OpenAI EU West
Name:        AzureOpenAI_EUWest_NC
URL:         https://<resource-name>.openai.azure.com
Credential:  AzureOpenAI_EUWest (External Credential from step 1)
```

Step 3 — Register the model in Setup > Model Builder > Add Model:

```
Provider Type:      Azure OpenAI
Model ID:           gpt-4o
Endpoint:           https://<resource-name>.openai.azure.com/openai/deployments/gpt-4o
API Version:        2024-02-01
Named Credential:   AzureOpenAI_EUWest_NC
```

Step 4 — Test Connection: click the Test button and confirm a success response.

Step 5 — Create a model alias `FinServ_AgentAlias` pointing to the registered Azure OpenAI model. Configure all Agentforce agents in the org to reference `FinServ_AgentAlias`.

**Why it works:** The Named Credential/External Credential pattern ensures the Azure API key never appears in plaintext in any Salesforce configuration field or log. The alias indirection means the security team can rotate the underlying model or key by updating a single record rather than touching every agent and prompt template individually.

---

## Example 2: Cost-Optimizing a High-Volume Email Summarization Feature

**Context:** A service org uses an Agentforce feature to summarize long customer email threads before presenting them to service agents. The feature runs approximately 50,000 times per day. The org is currently using the default alias backed by a frontier model (GPT-4o), and provider costs have become significant.

**Problem:** GPT-4o is priced at a premium per token. For a summarization task (no complex reasoning, no tool use, no multi-step agent behavior), the quality improvement over a smaller model does not justify the cost difference at 50,000 daily calls.

**Solution:**

Step 1 — Register a cost-optimized model. The team decides to use `gpt-4o-mini` (available on their existing OpenAI API subscription). They already have an OpenAI Named Credential in the org from a previous integration. In Model Builder, they add a new model record:

```
Provider Type:      OpenAI
Model ID:           gpt-4o-mini
Named Credential:   OpenAI_API_NC   (existing credential)
```

Step 2 — Test Connection: passes.

Step 3 — Create a new alias `SummarizationModel` pointing to `gpt-4o-mini`. This is a new alias, separate from the `DefaultAgent` alias used by complex agentic tasks. The new alias does not touch any existing alias.

Step 4 — Update the email summarization prompt template to reference `SummarizationModel` instead of the default alias.

Step 5 — Run a 500-call sample test in sandbox with the new alias and compare output quality against the frontier model results. Quality is acceptable for the summarization use case.

Step 6 — Deploy the prompt template change to production.

**Why it works:** Creating a separate alias for summarization isolates the cost optimization. The `DefaultAgent` alias powering complex agentic tasks continues to use GPT-4o unaffected. If the summarization model quality degrades, the team can update `SummarizationModel` to point to a higher-quality model without any changes to the consuming prompt template — only the alias mapping changes.

---

## Anti-Pattern: Updating the Shared Default Alias to Test a New Model

**What practitioners do:** An admin wants to try a new model (e.g., a newly released Anthropic Claude version) and directly updates the org's primary model alias to point to the new model so they can "see how it performs" in the live org.

**What goes wrong:** The alias change is global and immediate. Every Agentforce agent, prompt template, and Einstein feature that references that alias switches to the new model simultaneously — including production features used by sales reps and service agents at that moment. If the new model has different function calling behavior, lower quality on a specific task, or a different output format that downstream parsing relies on, all affected features degrade or fail at once. There is no rollback mechanism other than switching the alias back manually.

**Correct approach:** Always create a new, isolated alias (e.g., `Test_ClaudeV3`) pointing to the new model. Test this alias exclusively in sandbox using a copy of the prompt templates. Only after validation is complete — and ideally after a business hours window — update the production alias or swap features to the new alias one at a time.
