---
name: customer-data-request-workflow
description: "Implement GDPR/CCPA data subject rights (access, deletion, rectification) using Salesforce Privacy Center and/or custom workflow. NOT for general backup or org-level data retention policy."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "gdpr deletion request from a customer"
  - "right to be forgotten in salesforce"
  - "data subject access request workflow"
  - "ccpa opt out implementation"
tags:
  - privacy
  - gdpr
  - ccpa
  - compliance
inputs:
  - "Request type (access/delete/correct)"
  - "subject identifiers"
  - "org regulatory scope"
outputs:
  - "Runbook"
  - "Privacy Center policy or Apex batch"
  - "audit log"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Customer Data Subject Request (DSR) Workflow

A Data Subject Request (DSR) is a regulatory workflow with strict SLAs (30–45 days depending on jurisdiction). Salesforce offers Privacy Center as a managed capability with pre-built Right to Be Forgotten, Data Portability, and Retention policies; for orgs without Privacy Center, this skill defines the equivalent Apex-based workflow and audit schema.

## When to Use

A privacy regulator or legal team hands in a request. Also for proactive rehearsals. Not for general B2B contact cleanup.

Typical trigger phrases that should route to this skill: `gdpr deletion request from a customer`, `right to be forgotten in salesforce`, `data subject access request workflow`, `ccpa opt out implementation`.

## Recommended Workflow

1. Identify scope: Contact, Lead, Case, and any custom objects referencing the individual (PersonAccount, portal Users, CampaignMember).
2. Choose mechanism: Privacy Center policy (preferred) or custom Apex batch with a hard-delete privacy service.
3. Execute in a sandbox first with a synthetic subject to prove the chain of deletion (no orphan FKs).
4. Run in production; capture a signed audit record (who requested, what was deleted, when).
5. Confirm completion to the requester within the regulatory SLA; retain the audit record per policy retention rules (typically 7 years).

## Key Considerations

- Some objects (FieldHistory, RecordAuditTrail) cannot be deleted — document the residual risk with legal.
- Backups contain subject data; coordinate with backup vendor for deletion from off-platform copies.
- Einstein and Prediction stores may cache features — include the analytics retrain step.
- Event logs / FinServ / Shield audit tables may require a separate erasure pipeline.

## Worked Examples (see `references/examples.md`)

- *GDPR delete for a Lead + converted Contact* — EU subject asks for erasure; Lead was converted 9 months ago.
- *Apex batch equivalent for orgs without Privacy Center* — Platform license, no Privacy Center.

## Common Gotchas (see `references/gotchas.md`)

- **Person Accounts complicate identity** — Contact + Account deletion breaks if PersonAccount is referenced in Orders.
- **Field History Retention** — FHRetention stores values for up to 10 years; they survive DML.
- **Missing audit** — Regulator demands proof; you cannot show what you deleted.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Running a hard `DELETE FROM Contact WHERE Email=…` query with no audit
- Using the UI 'Delete' button for high-volume DSR — not repeatable, no audit
- Ignoring analytics (CRMA) caches that retain PII in datasets

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
