# Model Builder / BYOLLM — Work Template

Use this template when registering an external LLM, reviewing model configuration, or troubleshooting model connectivity in a Salesforce org.

---

## Scope

**Skill:** `model-builder-and-byollm`

**Request summary:** (fill in what the user asked for — e.g., "register Azure OpenAI gpt-4o-mini for use in Agentforce", "troubleshoot 401 errors on existing OpenAI model registration")

**Mode:**
- [ ] Mode 1 — Register a new external LLM (BYOLLM)
- [ ] Mode 2 — Review / audit current model configuration
- [ ] Mode 3 — Troubleshoot model connectivity or alias failure

---

## Context Gathered

Answer these before proceeding:

| Question | Answer |
|---|---|
| Einstein generative AI feature flag enabled? | |
| License type (Einstein for Agentforce, Einstein 1, other)? | |
| Provider (OpenAI / Azure OpenAI / Anthropic / custom)? | |
| Model ID (e.g., gpt-4o-mini, claude-3-5-haiku-20241022)? | |
| Provider endpoint URL (full base URL or deployment URL for Azure)? | |
| For Azure: deployment name, API version? | |
| Named Credential already exists? (yes / no / unknown) | |
| Use case type (agentic with actions / summarization / classification / other)? | |
| Function calling required? (yes if agent with actions) | |
| Approximate daily call volume? | |
| Sandbox or production? | |

---

## Pre-Work Checklist (Mode 1 — New Registration)

- [ ] API key obtained from provider console and ready to paste into External Credential
- [ ] Endpoint URL confirmed (especially for Azure: full deployment endpoint + API version)
- [ ] Function calling support confirmed in provider docs for the chosen model ID
- [ ] Context window size verified against expected prompt sizes
- [ ] External Credential created (Auth Protocol: Custom, Principal with API key parameter)
- [ ] Named Credential created pointing to External Credential and correct base domain
- [ ] Permission Set granting Named Credential access assigned to relevant users / integration user

---

## Model Registration Details

Fill in during Setup > Model Builder:

| Field | Value |
|---|---|
| Provider Type | |
| Model ID | |
| Endpoint URL | |
| Named Credential | |
| Azure API Version (if applicable) | |
| Alias name (new or existing) | |
| Features / agents referencing this alias | |

---

## Test Connection Result

- [ ] Test Connection: PASSED / FAILED
- Error message (if failed): ___________________________________
- Date tested: _______________________________________________

---

## Troubleshooting Reference (Mode 3)

| Symptom | Most Likely Cause | Next Step |
|---|---|---|
| Test Connection returns 401 | API key expired or incorrect in External Credential | Update External Credential Principal; re-test |
| Test Connection returns 404 | Endpoint URL or deployment name incorrect | Verify URL in provider console; update model record |
| Test Connection returns 429 | Provider rate limit exceeded | Check provider usage dashboard; upgrade tier |
| Test passes but agent actions fail | Model does not support function calling | Swap to a model with confirmed function calling support |
| Specific users fail, others succeed | Named Credential Permission Set not assigned | Check and assign Permission Set for Named Credential |
| All features break after alias update | Wrong model assigned to alias | Update alias to correct model; review blast radius |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Mode 1 — Full BYOLLM registration (External Credential → Named Credential → Model Builder → Alias)
- [ ] Mode 2 — Audit: review all aliases, test all external models, document mapping
- [ ] Mode 3 — Troubleshoot: start with Test Connection error message, then check credential, endpoint, rate limits, function calling

---

## Review Checklist

Copy and tick off as you complete each item:

- [ ] Einstein generative AI feature flag confirmed enabled
- [ ] Named Credential and External Credential created; API key stored only in External Credential Principal
- [ ] External model registered in Model Builder (correct provider type, model ID, endpoint)
- [ ] Test Connection passes on all registered external models
- [ ] Model alias created/updated and pointing to the correct model
- [ ] Function calling support confirmed if alias backs an Agentforce agent with actions
- [ ] Context window verified against expected prompt sizes
- [ ] Alias-to-model mapping documented
- [ ] Sandbox testing completed before any production alias update
- [ ] API key rotation procedure documented

---

## Notes

Record deviations from the standard pattern, unusual provider behavior, or decisions made during implementation:

(free text)
