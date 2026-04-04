# Einstein Trust Layer — Configuration and Review Template

Use this template when configuring, validating, or reviewing Einstein Trust Layer security controls for a Salesforce org.

## Scope

**Org:** (name and type: Production / Full Sandbox / Partial Sandbox)

**Einstein features in scope:** (list: Agentforce, Copilot, Service Replies, Work Summaries, Prompt Builder features, etc.)

**Compliance requirements driving this review:** (e.g., GDPR, HIPAA, PCI-DSS, internal data governance policy)

**Review type:** (Initial setup / Periodic audit / Pre-deployment validation / Incident investigation)

---

## Prerequisites Check

| Prerequisite | Status | Notes |
|---|---|---|
| Data 360 provisioned in org | Yes / No | Required for audit trail |
| Einstein Generative AI enabled (Einstein Setup) | Yes / No | Master toggle must be On |
| Applicable Einstein feature licenses confirmed | Yes / No | Confirm feature entitlement |

---

## Trust Layer Component Status

### Zero Data Retention

| Item | Status | Notes |
|---|---|---|
| ZDR agreement confirmed with external LLM providers | Confirmed / Unknown | Verify in Trust Layer setup |
| External LLM providers in use | (list providers, e.g., OpenAI) | |
| Data passing through LLM gateway is TLS-encrypted in transit | Confirmed / Unknown | |

### Data Masking

| Item | Status | Notes |
|---|---|---|
| Data masking toggled On | Yes / No | Setup > Einstein Setup > Trust Layer |
| Sensitive data categories configured | (list selected: Names, Emails, Phones, SSNs, Credit Cards) | |
| Features where masking is confirmed active | (list features) | Note: not all features support masking |
| Prompt Builder preview tested with PII record | Yes / No | Placeholders must appear in preview output |
| Context window budget assessed (limit: 65,536 tokens with masking) | Yes / No | |
| Estimated max token count for largest grounded prompt | (number) | Must be under 65,536 |

### Toxicity Detection

| Item | Status | Notes |
|---|---|---|
| Toxicity detection active | Yes / No | Active by default when Trust Layer is enabled |
| Baseline toxicity scores reviewed in audit trail | Yes / No | Review for false positive patterns |
| Prompts with elevated false-positive risk identified | Yes / No | (e.g., medical, legal, or security-domain language) |

### Grounding Controls

| Item | Status | Notes |
|---|---|---|
| Grounding mode documented for each feature | (client-side / server-side / dynamic per feature) | |
| Permission model enforced for grounded data retrieval | Confirmed / Not verified | LLM access respects running user's permissions |
| Prompt defense instructions present in templates | Yes / No | Reduces injection risk and hallucination |
| Dynamic grounding data volume bounded | Yes / No | Prevents context window overflow |

### Audit Trail

| Item | Status | Notes |
|---|---|---|
| Audit trail enabled | Yes / No | Must be explicitly activated |
| Retention period configured | (period, e.g., 12 months) | Align to compliance policy |
| Audit trail activation date | (date) | Interactions before this date are not logged |
| Audit trail records accessible in Data 360 | Yes / No | |
| Reports/dashboards configured for ongoing monitoring | Yes / No | |

---

## Prompt Template Validation

For each prompt template in scope, complete this table:

| Template Name | Feature | PII Fields Grounded | Masking Verified in Preview | Max Token Count (with masking) | Status |
|---|---|---|---|---|---|
| (template name) | (feature) | (field list) | Yes / No | (number) | Pass / Fail / Needs Review |

---

## Risk Summary

| Risk Area | Finding | Severity | Recommended Action |
|---|---|---|---|
| Data masking coverage gap (agents) | (finding) | High / Medium / Low | (action) |
| Audit trail not retroactive for prior period | (finding) | High / Medium / Low | (action) |
| Token budget headroom | (finding) | High / Medium / Low | (action) |
| Invalid-format PII masking gap | (finding) | High / Medium / Low | (action) |
| EU data residency compliance | (finding) | High / Medium / Low | (action) |

---

## Sign-Off Checklist

- [ ] All Trust Layer components verified against this template
- [ ] Data masking tested with production-representative PII records
- [ ] Audit trail enabled and retention period set before feature goes live
- [ ] Token budget documented and validated with masking active
- [ ] Compliance team reviewed and accepted residual risks
- [ ] Configuration documented and stored in org change management system

**Reviewed by:** (name)
**Date:** (YYYY-MM-DD)
**Org:** (org name)
