# Well-Architected Notes — Model Builder and BYOLLM

## Relevant Pillars

- **Security** — The primary pillar for this skill. Provider credentials belong in the Einstein Studio foundation model connection (Add Foundation Model takes the endpoint and authentication details), never in Apex, flows, or custom metadata. UNVERIFIED (2026-10-03): the earlier statement that BYO model keys must live in Named Credentials and External Credentials; that pattern applies to direct Apex callouts. Provider blocks in EinsteinGptSettings enforce which providers any generative AI feature may reach. The Trust Layer (a separate skill) governs how prompts and outputs are masked, scored, and logged.

- **Operational Excellence** — The second primary pillar. Updating a model configuration "can affect the performance of associated prompts"; create a new configuration and move template versions one at a time. Environment parity (sandbox to production) is a manual responsibility — teams must script or document every registration step to prevent configuration drift. Salesforce applies a default of 300 generation requests per minute per org, and provider limits apply on top; Model Activity in Einstein Studio shows inferences and errors. Deprecated models are rerouted on a published date, so retests belong in the release calendar.

- **Reliability** — External LLM availability introduces an external dependency into Agentforce and Einstein features. Provider outages, rate limit exhaustion, or credential expiry can silently degrade features that would otherwise function correctly. Reliability patterns include: monitoring provider health dashboards, keeping a prior template version on a Salesforce-managed model ready to reactivate, and documenting which templates use each configuration.

- **Performance** — Model selection directly affects latency and throughput. Frontier models (GPT-4o, Claude 3.5 Sonnet) have higher per-call latency than mid-tier models. High-concurrency Agentforce features that call external models must account for provider-side latency variance under load. Context window management (truncating unnecessary prompt content) reduces both latency and token cost.

- **Scalability** — External provider rate limits are the primary scalability ceiling for BYOLLM deployments. Token-per-minute (TPM) and requests-per-minute (RPM) limits must be sized against peak concurrent usage before going live. Salesforce-standard models do not impose the same external rate-limit constraints and may be more appropriate for high-scale, lower-complexity use cases.

---

## Architectural Tradeoffs

**BYOLLM vs. Salesforce-Standard Models:**
Using BYOLLM gives organizations control over model version, provider, and data residency, but introduces operational complexity: credential management, rate limit monitoring, sandbox-to-production deployment, and provider-side SLA dependency. Salesforce-standard models are simpler to operate but offer less control over model version cadence and data routing. Organizations with strict compliance requirements typically accept the BYOLLM operational overhead; organizations prioritizing simplicity should default to standard models.

**Shared Configuration vs. Use-Case Configurations:**
A single shared model configuration minimizes setup but means one settings change touches every template that uses it. Separate configurations per use case (summarization, drafting, classification) add setup but limit the impact of each change. Agent reasoning is out of scope either way: the platform reasoning engine uses OpenAI GPT-4o and BYO models aren't supported there.

**Credential Granularity:**
UNVERIFIED (2026-10-03): the earlier discussion of org-level versus per-user External Credential principals applies to Apex callouts. The documented foundation model connection takes one set of authentication details per foundation model; separate foundation models are the way to separate billing or keys.

---

## Anti-Patterns

1. **Storing API keys in source or metadata**: Placing provider API keys in Apex, flows, custom metadata, or custom settings. Keys there are visible to admins, copied into sandboxes, and can appear in logs. Connect providers in Einstein Studio, and keep any key a direct callout needs in a Named Credential.

2. **Updating a shared configuration without isolated testing**: Using a configuration that live templates use as the test target for a new model. Because the change reaches every associated prompt, this risks degrading all of them at once. The correct pattern is: new configuration, new template version, preview, activate, then retire the old configuration.

3. **No retrain or model version monitoring** — Registering an external model at a specific version and never reviewing whether the provider has deprecated that version or changed its capabilities. Salesforce reroutes requests from retired models to the next closest replacement on the Reroute Date, and publishes rerouting notices 30 days before retirement in the monthly Einstein Platform release notes. Assign an owner to read them and retest before each reroute date.

---

## Official Sources Used

Read for this revision (2026-10-03):

- Data Cloud guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/data_cloud.pdf. Use AI Models: Salesforce-Enabled Large Language Models, Bring Your Own Large Language Model, Add a Foundation Model (HTTPS 443, Azure deployment, fine-tuned OpenAI, Bedrock Anthropic type), Edit or Delete a Foundation Model, Monitor Model Activity, Configure and Test a Model in Model Playground (hyperparameters, data masking, edit guidance, test settings not saved), Einstein Studio Model Builder Guidelines and Limits, glossary (Model Builder).
- Quickstart Your Einstein Generative AI Solution, Spring '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf. Large Language Model Support (managed models, BYOLLM providers and models, LLM Open Connector, deprecated models and rerouting), Geo-Aware LLM Request Routing, Considerations for Einstein Generative AI (300 requests per minute), Changing LLM Configurations, Agentforce Agents considerations (GPT-4o reasoning engine; BYO not supported for agents).
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. EinsteinGptSettings (provider blocks, region fallback, beta models), GenAiPromptTemplate (primaryModel and sample value).

Listed in the original version and not re-read (Salesforce Help does not fetch; developer.salesforce.com returned 403 on 2026-10-03):

- Salesforce Help: Model Builder Overview: https://help.salesforce.com/s/articleView?id=sf.model_builder_intro.htm (Model Builder content read in the Data Cloud PDF above).
- Salesforce Developer Guide: Model Builder: https://developer.salesforce.com/docs/einstein/genai/guide/model-builder.html
- Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services Overview: https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Named Credentials: https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
