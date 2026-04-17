---
name: mutual-tls-callouts
description: "Configure mTLS for Apex callouts using Named Credentials with client certificate authentication. NOT for standard TLS or API key auth."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "mtls salesforce callout"
  - "client certificate apex"
  - "mutual tls named credential"
  - "jks keystore apex"
tags:
  - mtls
  - callout
  - named-credential
inputs:
  - "partner's required cert details"
  - "current Apex HttpClient"
outputs:
  - "Named Credential + uploaded certificate + callout snippet"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Mutual TLS Callouts

Mutual TLS requires both sides to present certificates. Salesforce supports mTLS callouts via a client certificate stored in Setup → Certificate and Key Management, referenced from a Named Credential. This skill sets up the cert, the Named Credential, and a minimal Apex caller that proves the connection before shipping.

## When to Use

Partner APIs that mandate mTLS (banks, healthcare EDI, some government systems).

Typical trigger phrases that should route to this skill: `mtls salesforce callout`, `client certificate apex`, `mutual tls named credential`, `jks keystore apex`.

## Recommended Workflow

1. Generate a client keypair (or receive partner-signed cert) and import via Setup → Certificate and Key Management.
2. Create Named Credential referencing the certificate; set endpoint + authentication protocol 'Per User' or 'Named Principal'.
3. Write a small Apex probe: `HttpRequest req; req.setEndpoint('callout:MyPartner/health'); new Http().send(req);` and assert 200.
4. Schedule a daily probe job with alerting; cert expiry surfaces 30+ days ahead.
5. Rotate certificate annually or per partner policy.

## Key Considerations

- Self-signed certs are fine for dev but production requires partner-signed.
- `Certificate expiration` surprises pages; monitor `Certificate.ValidTo`.
- Named Credential is the only supported place to reference client cert — do not try to ship JKS in Apex.
- CSR generation happens in Salesforce; private key never leaves.

## Worked Examples (see `references/examples.md`)

- *Bank ACH partner* — Daily batch callout
- *Expiry monitor* — Prevent cert outage

## Common Gotchas (see `references/gotchas.md`)

- **CSR generated externally** — Private key material uploaded; weaker security.
- **Missing intermediate chain** — Handshake fails.
- **No expiry alert** — Outage Friday night.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Generating CSR externally
- Missing intermediate chain
- No expiry monitor

## Official Sources Used

- Apex REST & Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Connect REST API — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/
- Private Connect — https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm
- Bulk API 2.0 — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/
- Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
