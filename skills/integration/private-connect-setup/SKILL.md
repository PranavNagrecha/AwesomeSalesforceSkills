---
name: private-connect-setup
description: "Configure Private Connect between Salesforce and AWS/Azure for traffic to stay on private networks. NOT for standard internet callouts."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
triggers:
  - "private connect aws salesforce"
  - "privatelink salesforce"
  - "private network callout"
  - "hyperforce private connect"
tags:
  - private-connect
  - hyperforce
  - privatelink
inputs:
  - "cloud provider + VPC/VNet"
  - "endpoints to connect"
outputs:
  - "Private Connect config + Named Credential + verification plan"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Private Connect Setup

Private Connect (Hyperforce only) peers your Salesforce org with your AWS VPC or Azure VNet so callouts and incoming traffic never traverse the public internet. It is configured via Setup → Private Connect with a peering ID from your cloud provider.

## When to Use

Hyperforce orgs where compliance/latency requires private networking to partner endpoints.

Typical trigger phrases that should route to this skill: `private connect aws salesforce`, `privatelink salesforce`, `private network callout`, `hyperforce private connect`.

## Recommended Workflow

1. Confirm org is on Hyperforce; Private Connect is not available on First-Generation infrastructure.
2. Create a VPC Endpoint Service (AWS) or Private Link Service (Azure) in your cloud; share the service name.
3. Setup → Private Connect → Add Outbound (or Inbound) connection; Salesforce provisions peering.
4. Update Named Credentials to use the private DNS entry provided.
5. Verify with a probe callout and confirm tcpdump shows traffic on private link only.

## Key Considerations

- Billed separately; usage-based.
- Regional — connection must match the Salesforce POD region.
- DNS resolution inside Salesforce uses the private endpoint, but you must ensure your own VPC routes back.
- Private Connect does not bypass IP allow-lists; they are independent controls.

## Worked Examples (see `references/examples.md`)

- *Snowflake private* — SFDC → Snowflake BYOC
- *Partner inbound* — Bank callback

## Common Gotchas (see `references/gotchas.md`)

- **Region mismatch** — Setup step fails with 'region not supported'.
- **DNS resolution** — Callout resolves to public IP.
- **Billing surprise** — Charges not expected.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Assuming all orgs can use Private Connect
- Skipping DNS override
- No probe verification

## Official Sources Used

- Apex REST & Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Connect REST API — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/
- Private Connect — https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm
- Bulk API 2.0 — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/
- Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
