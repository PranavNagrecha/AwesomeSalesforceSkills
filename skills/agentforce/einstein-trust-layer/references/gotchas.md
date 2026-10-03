# Gotchas: Einstein Trust Layer

Non-obvious Trust Layer behaviours that cause real production and compliance problems. Each gotcha names its source. "GenAI Guide" means Quickstart Your Einstein Generative AI Solution, Spring '26 (generative_ai.pdf), chapters Einstein Trust Layer, Einstein Generative AI Analytics, Prompt Builder, and Agentforce Agents. "Metadata API" means the Metadata API Developer Guide, Version 67.0.

## Gotcha 1: Data Masking Is Disabled for Agentforce Agents

**What happens:** Masking is on in Einstein Trust Layer setup, and an Agentforce agent still sends customer names and contact details to the LLM unmasked.

**When it occurs:** Any agent. The Agentforce chapter states: "Data masking through the Einstein Trust Layer is disabled to improve the performance and accuracy of agents. All data accessed by agents, including personally identifiable information (PII), is protected in transit and isn't stored or used for training purposes by external LLM providers, as part of our strict zero-data retention policy." The Trust Layer chapter adds that "LLM Data Masking isn't always available in all features."

**How to avoid:** Record masking coverage per feature before go-live. For agents, rely on access controls and ZDR, keep sensitive fields out of agent actions and grounding, and do not tell stakeholders that agent prompts are masked.

**Source:** GenAI Guide, Agentforce Agents (Einstein Trust Layer section); Large Language Model Data Masking (Important note).

---

## Gotcha 2: Zero Data Retention Is Not Masking

**What happens:** A team tells stakeholders "customer data does not leave Salesforce" because ZDR is in place.

**When it occurs:** ZDR and masking are conflated. ZDR means "data sent to the LLM from Salesforce isn't retained and is deleted after a response is sent back to Salesforce." The prompt still travels to the provider (the guide names OpenAI and Azure OpenAI) through the LLM gateway over TLS. Masking is what keeps sensitive values out of that prompt.

**How to avoid:** Document ZDR (provider retention), masking (what the provider sees), and the audit trail (your own record) as three separate controls. Note that audit and feedback data "are stored by Salesforce for 30 days for compliance purposes," in addition to your Data Cloud retention.

**Source:** GenAI Guide, Einstein Trust Layer (Zero-Data Retention Policy); Einstein Trust Layer: Designed for Trust (Response Generation; Feedback and Audit).

---

## Gotcha 3: Pattern-Based Masking Only Recognizes Listed Formats and Locales

**What happens:** Most records mask correctly, but a phone number in an unsupported format, a 15-digit card number, or a non-US national ID reaches the LLM.

**When it occurs:** Pattern-based detection depends on "how precisely the text matches the regular expression (regex) pattern, the uniqueness of the pattern, and the proximity of relevant context words." Credit cards are "16 or 17 digit." Phone formats are defined per region and language. US driver's license, ITIN, and SSN are supported in English (United States) only. "No model can guarantee 100% accuracy... cross-region and multinational use cases can affect the ability to detect specific data patterns."

**How to avoid:** Test with production-shaped records for every locale the org holds. Add field-based masking (Gotcha 4) for anything the patterns miss. Fix data quality at entry so values match their pattern.

**Source:** GenAI Guide, Einstein Trust Layer Region and Language Support (pattern tables and Important note).

---

## Gotcha 4: Field-Based Masking Covers Only Record Merge Fields and Related Lists

**What happens:** A field tagged with a data classification is masked when merged directly, but the same value returned by a Flow or Apex merge field arrives unmasked.

**When it occurs:** "Field-Based masking supports only merge fields that are referenced in record merge fields and related lists." Pattern-based masking still scans all prompt text, including Flow and Apex output, but only for its listed data types.

**How to avoid:** Turn on masking for Shield Platform Encryption, compliance categories, and sensitivity levels in Trust Layer setup, tag the fields in Object Manager, and prefer record merge fields for sensitive values. Review Flow and Apex merge fields for data the patterns cannot recognize. The skill checker flags prompt templates that use Flow or Apex data providers (`TL-PT-02`).

**Source:** GenAI Guide, Large Language Model Data Masking (Important note; Field-Based Masking); LLM Data Masking Considerations and Limitations; Select What Data To Mask, step 5.

---

## Gotcha 5: Audit Data Exists Only After Data Collection Is Turned On

**What happens:** A compliance request arrives for last quarter's AI interactions, and the GenAIGatewayRequest report is empty for that period.

**When it occurs:** "To access the data stored in Data Cloud, you'll need to turn on the Einstein generative AI data collection and storage and install the report package." Data Cloud "refreshes the data streams once every hour." UNVERIFIED (2026-10-03): that interactions before collection is turned on cannot be backfilled is inferred from the setup steps; no fetched source states it either way.

**How to avoid:** Turn on data collection and install the report package before any feature reaches production users. Check the streams are flowing (GenAI data streams with a successful last run) as part of go-live.

**Source:** GenAI Guide, Audit Trail; Generative AI Audit and Feedback Data (Data Collection and Storage in Data Cloud).

---

## Gotcha 6: Audit Data Consumes Data Cloud Credits

**What happens:** Data Cloud consumption jumps after a busy agent goes live.

**When it occurs:** Audit and feedback data "consumes Data Cloud credits for ingestion, storage, and processing." "On average, each round trip to the large language model (LLM) and back results in 24 records being ingested into Data Cloud," and ingestion volume is the main driver. Reports and dashboards also consume Data Queries usage.

**How to avoid:** Estimate credits from expected LLM calls times 24 records before go-live, set a retention period in Data Cloud that meets the compliance mandate without keeping more than needed, and delete audit data through the documented Remove Data Lake Objects process when allowed.

**Source:** GenAI Guide, Billing Considerations for Audit and Feedback; Data Collection and Storage in Data Cloud.

---

## Gotcha 7: Sandboxes Can't Test Masking Configuration, Data Cloud Grounding, or Audit Data

**What happens:** Everything passes in a sandbox, and production behaves differently once masking settings and audit reports are in play.

**When it occurs:** "Einstein Trust Layer features that require Data Cloud aren't available for testing since Data Cloud isn't supported in sandbox staging environments." Not testable there: "LLM Data Masking configuration in Einstein Trust Layer Setup," "Grounding on Objects in Data Cloud," and "Logging and reviewing audit and feedback data in Data Cloud."

**How to avoid:** Plan a controlled production verification for those three before go-live, with test records that carry each sensitive data type.

**Source:** GenAI Guide, Einstein Trust Layer Limits (Einstein Trust Layer Support in Sandbox Environments).

---

## Gotcha 8: Toxicity Scores Read in Two Directions, and False Does Not Mean Safe

**What happens:** A reviewer filters for high scores to find toxic responses and misses the safety category, or treats `isToxicityDetected = false` as clean.

**When it occurs:** "The score for the safety category ranges from 0 through 1 with 1 being the safest," with 0.5 to 1 considered safe. For all other categories, "toxicity scores of 0.5 and above" are toxic. "When the isToxicityDetected field is false, it doesn't necessarily mean there isn't toxicity." Language support for toxicity detection differs by region, and region-specific language is harder to classify.

**How to avoid:** Build the review report on DetectorType = toxicity and read each category with its own direction. Sample responses with `isToxicityDetected = false` in high-risk use cases.

**Source:** GenAI Guide, Review Toxicity Scores (note); Einstein Trust Layer Region and Language Support (Toxicity Detection).

---

## Gotcha 9: Geo-Aware Routing Falls Back to the US

**What happens:** An EU org assumes all LLM requests stay in the EU, and audit records show requests served in the US.

**When it occurs:** "If a model isn't available in a nearby region, the requests are routed to the US. You can't disable geo-aware routing and rerouting to the US when models aren't available in a nearby region." For orgs that enabled the platform on or after June 13, 2024, the Einstein generative AI region matches the Data Cloud region. Separately, EinsteinGptSettings has `disableAIProviderRegionFallback`, which "Indicates whether the fallback of Azure OpenAI requests outside the model endpoint region for your org is turned off."

**How to avoid:** Choose models available in the required region, set `disableAIProviderRegionFallback` to true when Azure OpenAI must not fall back, and use the Feedback and Audit data to confirm where requests went.

**Source:** GenAI Guide, Geo-Aware LLM Request Routing (Proximity and Routing). Metadata API, EinsteinGptSettings.

---

## Gotcha 10: The 65,536-Token Limit Is Not in the Guide

**What happens:** A team trims every prompt to a 65,536-token budget because an earlier version of this skill said masking caps the context window there.

**When it occurs:** UNVERIFIED (2026-10-03): the figure does not appear in the Generative AI guide. What the guide documents is that "When a prompt is too large for the model to use, a summary is generated automatically in the Resolution panel," and that "Data masking can affect LLM prompt grounding."

**How to avoid:** Test the largest realistic prompt with masking on, watch for the automatic summary in the Resolution panel, and size grounding from that test rather than from a fixed number.

**Source:** GenAI Guide, Work with Large Prompts; LLM Data Masking Considerations and Limitations (Considerations).
