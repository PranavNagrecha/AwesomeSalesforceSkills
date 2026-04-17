---
name: api-versioning-strategy
description: "Design versioning for custom Apex REST endpoints: URI versioning, backward compatibility, deprecation sunset. NOT for consuming external APIs."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "apex rest versioning"
  - "deprecate salesforce api endpoint"
  - "backward compatible api"
  - "/services/apexrest version"
tags:
  - api
  - versioning
  - apex-rest
inputs:
  - "existing endpoints"
  - "consumer list"
outputs:
  - "URI versioning scheme, deprecation policy, Apex class layout"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# API Versioning Strategy

Custom Apex REST endpoints should be versioned from day one. Two accepted patterns: URI versioning (`/services/apexrest/v1/orders`) or header versioning (`Accept: application/vnd.myco.v1+json`). URI is simpler and more debuggable. This skill defines the class structure, the deprecation sunset policy, and the monitoring required to deprecate safely.

## When to Use

Before publishing a new endpoint or when breaking changes are needed on an existing one. Not for internal-only endpoints with known single consumer.

Typical trigger phrases that should route to this skill: `apex rest versioning`, `deprecate salesforce api endpoint`, `backward compatible api`, `/services/apexrest version`.

## Recommended Workflow

1. Always include a version prefix in @RestResource urlMapping, even on v1.
2. Breaking change → new version class; reuse the service layer; deprecate old via response header `Sunset: <date>`.
3. Instrument v1 request counts via Event Monitoring or a custom Log__c record to measure traffic.
4. Notify consumers 90 days before sunset; provide migration doc.
5. Remove v1 only after 0 traffic for 30 days.

## Key Considerations

- Adding a new optional field is NOT a breaking change — do not version for it.
- Renaming a field IS breaking — version.
- Error response shape changes are breaking.
- External consumers cache; give 30+ day sunset windows.

## Worked Examples (see `references/examples.md`)

- *v1 → v2 orders endpoint* — Rename `customerId` to `accountId`
- *Sunset instrumentation* — Before deleting v1

## Common Gotchas (see `references/gotchas.md`)

- **No version on v1** — First breaking change forces coordinated migration.
- **Logic in controller** — Cannot reuse across versions.
- **Silent deletion** — Consumer breaks without warning.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- No version on initial endpoint
- Breaking v1 without a v2
- Logic inline in controller

## Official Sources Used

- Apex REST & Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Connect REST API — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/
- Private Connect — https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm
- Bulk API 2.0 — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/
- Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html
