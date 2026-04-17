---
name: shield-kms-byok-setup
description: "Configure Shield Platform Encryption with customer-supplied (BYOK) or customer-held (Cache-Only Key Service) tenant secrets, rotate them, and recover. NOT for Classic Encryption or field masking."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "shield byok setup"
  - "cache only key service"
  - "rotate tenant secret"
  - "customer managed keys salesforce"
tags:
  - shield
  - encryption
  - byok
  - kms
inputs:
  - "KMS (AWS KMS / Azure Key Vault) endpoint"
  - "key material"
  - "org Shield license"
outputs:
  - "Tenant secret rotation policy"
  - "CMK setup runbook"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Shield Platform Encryption — BYOK / KMS Setup

Shield BYOK lets you upload your own 256-bit tenant secret; Cache-Only Key Service keeps the key in your own KMS, fetched by Salesforce on demand. Both require Shield Platform Encryption and careful operational processes: rotation, destroy tests, and KMS availability SLOs.

## When to Use

Regulated data (HIPAA, PCI, regulated financial records) where compliance mandates customer-controlled keys. Not for general PII that Classic Encryption or field-level security already protects.

Typical trigger phrases that should route to this skill: `shield byok setup`, `cache only key service`, `rotate tenant secret`, `customer managed keys salesforce`.

## Recommended Workflow

1. Enable Shield Platform Encryption and identify fields/files/chatter that require probabilistic vs. deterministic encryption.
2. Generate a 256-bit key in your KMS; for BYOK, derive and upload; for Cache-Only, configure named credential + callback.
3. Rotate tenant secret quarterly via Setup → Platform Encryption → Key Management.
4. Run a destroy-key test in a sandbox to prove you can revoke access (records become unreadable).
5. Document KMS availability SLO — if your KMS is down, Salesforce cannot decrypt in the Cache-Only flow.

## Key Considerations

- BYOK key material never leaves Salesforce after upload; Cache-Only keys never enter Salesforce's durable storage.
- Deterministic encryption is required for filter equals queries — trades strength for functionality.
- Rotation re-encrypts newly written data only; historical data stays under the previous tenant secret until you run Encryption Key Rotation batch.
- Cache-Only: callback latency adds to every decrypt; measure in load tests.

## Worked Examples (see `references/examples.md`)

- *BYOK tenant secret upload* — Healthcare provider, HIPAA.
- *Cache-Only Key Service with AWS* — Financial services firm refuses to upload key material.

## Common Gotchas (see `references/gotchas.md`)

- **Destroy-key not tested** — On a real incident nobody can prove revocation works.
- **KMS outage = decrypt failure** — User pages go blank; agents cannot read records.
- **Mix of deterministic and probabilistic** — SOQL filter on a field silently fails to return results.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Using default tenant secret indefinitely
- Encrypting a field and then using SOQL LIKE on it
- No runbook for KMS outage

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
