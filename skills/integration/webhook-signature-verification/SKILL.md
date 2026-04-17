---
name: webhook-signature-verification
description: "Accept inbound webhooks (Stripe, GitHub, Slack, partner) and verify HMAC signatures in Apex REST. NOT for outbound webhooks."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "webhook hmac verification apex"
  - "stripe webhook salesforce"
  - "verify signature inbound callout"
  - "hmac sha256 apex"
tags:
  - webhook
  - hmac
  - signature
  - apex-rest
inputs:
  - "webhook provider HMAC spec"
  - "shared secret location"
outputs:
  - "@RestResource endpoint with signature verification"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Webhook Signature Verification

Inbound webhooks are unauthenticated by default — anyone with your endpoint URL can POST. HMAC signature verification with a shared secret is the industry-standard defense. This skill implements Stripe-style HMAC SHA-256 verification with timing-safe comparison in Apex and uses Protected Custom Metadata for the secret.

## When to Use

Any inbound webhook from an external SaaS (Stripe, GitHub, Twilio, Slack, Zapier).

Typical trigger phrases that should route to this skill: `webhook hmac verification apex`, `stripe webhook salesforce`, `verify signature inbound callout`, `hmac sha256 apex`.

## Recommended Workflow

1. Store the shared secret in Protected Custom Metadata (`Webhook_Secret__mdt.Value__c`) or a Named Credential with a dummy endpoint.
2. @RestResource endpoint reads `Request.headers.get('X-Provider-Signature')`.
3. Compute HMAC SHA-256 using `Crypto.generateMac('HmacSHA256', body, secret)`; hex-encode.
4. Timing-safe compare (constant-time loop) — equality op in Apex is not documented as timing-safe.
5. Reject with 401 on mismatch; never log the body on reject (avoid replay disclosure).

## Key Considerations

- Always compare hashes constant-time to prevent timing attacks.
- Include a timestamp in the signed payload and reject if older than 5 minutes (replay protection).
- Use Protected Custom Metadata for the secret — not a Custom Setting, which is readable by any user with read.
- Webhook endpoints should be public sites (no authentication) — that's normal; the signature is the auth.

## Worked Examples (see `references/examples.md`)

- *Stripe webhook* — Payment success
- *Replay protection* — Attacker replays yesterday's valid event

## Common Gotchas (see `references/gotchas.md`)

- **Non-constant-time compare** — Timing attack leaks signature.
- **Secret in plain CMDT** — Any reader sees it.
- **Missing replay defense** — Replayed events processed twice.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- No signature check ('trust by URL obscurity')
- Secret in Custom Setting
- Logging raw body on failure

## Official Sources Used

- Apex REST & Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Connect REST API — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/
- Private Connect — https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm
- Bulk API 2.0 — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/
- Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
