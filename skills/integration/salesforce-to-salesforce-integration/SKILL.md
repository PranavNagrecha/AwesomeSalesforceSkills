---
name: salesforce-to-salesforce-integration
description: "Use this skill to implement Salesforce-to-Salesforce integration patterns — covering the native S2S feature, API-based cross-org sync, Platform Event bridging, and Salesforce Connect Cross-Org adapter. Trigger keywords: Salesforce to Salesforce integration, cross-org data sharing, S2S feature, cross-org Platform Events, Salesforce Connect cross-org. NOT for multi-org strategy or architecture decisions (use architect/multi-org-strategy), single-org data sharing, or external (non-Salesforce) system integration."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "need to share records between two Salesforce orgs — which pattern should be used"
  - "legacy S2S Connection feature is enabled and team needs to understand its constraints"
  - "need to sync Account or Contact records across multiple Salesforce orgs via API"
  - "Platform Events need to be forwarded from one Salesforce org to another"
  - "team evaluating Salesforce Connect cross-org adapter vs REST API sync for cross-org integration"
tags:
  - integration
  - cross-org
  - salesforce-to-salesforce
  - platform-events
  - salesforce-to-salesforce-integration
inputs:
  - "Source org and target org details (sandbox or production)"
  - "Objects and fields to share or sync"
  - "Sync direction: one-way or bidirectional"
  - "Volume and frequency requirements"
outputs:
  - "Cross-org integration pattern decision and implementation guidance"
  - "S2S feature constraint analysis if applicable"
  - "API-based sync or Platform Event bridge configuration guidance"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-14
---

# Salesforce-to-Salesforce Integration

This skill activates when a developer or integration architect needs to implement data sharing or process integration between two Salesforce orgs. It covers the full spectrum of cross-org integration patterns — from the native S2S feature (with its severe constraints) to modern API-based sync, Platform Event bridging, and Salesforce Connect cross-org access.

---

## Before Starting

Gather this context before working on anything in this domain:

- The native Salesforce-to-Salesforce (S2S) feature using PartnerNetworkConnection is irreversible — once enabled, it cannot be deactivated. Confirm this is intentional before enabling.
- The S2S feature consumes SOAP API call limits on BOTH the publishing and subscribing org simultaneously. For high-volume scenarios, this makes S2S unsuitable.
- Modern cross-org integration patterns should prefer: Salesforce Connect Cross-Org adapter (read-only real-time access), Platform Events with Pub/Sub API (async event bridging), REST API callouts (bidirectional sync), or MuleSoft (enterprise-scale orchestration).
- The most common wrong assumption: practitioners treat native S2S as the default cross-org sharing mechanism without knowing it is a legacy SOAP-based feature with irreversible activation.

---

## Core Concepts

### Native S2S Feature (Legacy — Use With Caution)

The native S2S feature uses PartnerNetworkConnection and PartnerNetworkRecordConnection objects:
- Enables record sharing between two orgs via SOAP API under the covers
- Once enabled: **CANNOT be deactivated** — this is a permanent org change
- Consumes SOAP API call limits on both orgs simultaneously — unsuitable for high-volume scenarios
- Limited to specific standard objects; custom object sharing requires additional configuration
- Record updates propagate asynchronously with no guaranteed delivery confirmation

Use cases for native S2S: low-volume bidirectional sharing between partner orgs where the irreversibility is accepted and volume is very low.

### API-Based Cross-Org Sync

The modern approach for cross-org record synchronization:
- Source org uses a Connected App + OAuth2 to authenticate to target org
- REST API or SOAP API callouts from Apex Queueable/Batch jobs push records to target
- Target org uses REST API to accept inbound record creation/updates
- Bulk API 2.0 for high-volume scenarios

This pattern requires: Named Credential in source org pointing to target org, Connected App in target org, and a sync job design (trigger-based or scheduled batch).

### Platform Event Bridging

For event-driven cross-org integration:
- Source org publishes a Platform Event; target org subscribes via Pub/Sub API (gRPC)
- One-way event delivery: source fires events, target receives and processes
- Replay ID for recovery from delivery interruptions
- Cannot be used for bidirectional event streams on the same channel

### Salesforce Connect Cross-Org Adapter

For read-only real-time access to another org's data without creating a local copy:
- Creates External Objects in the consuming org backed by the source org's data
- Data is queried on demand from the source org — not stored locally
- Supports SOQL against External Objects
- No data replication; always real-time read from source
- Write operations require API callouts — External Objects support limited write-back

---

## Common Patterns

### Pattern: REST API Cross-Org Sync with Named Credential

**When to use:** Bidirectional record sync between two Salesforce orgs where volume is moderate (below 2,000 records per job run) and latency is near-real-time.

**How it works:**
1. Create a Connected App in the target org with OAuth2 credentials
2. Create a Named Credential in the source org pointing to the target org's instance URL
3. Source org Apex Queueable calls REST API endpoint on target org using Named Credential
4. Target org exposes a REST Apex endpoint or uses the standard REST API for record creation
5. Include idempotency key (external ID or unique hash) to prevent duplicate creation on retry

### Pattern: Platform Event Bridge via Pub/Sub API

**When to use:** Async event propagation from one org to another where events trigger processes in the target org.

**How it works:**
1. Source org Apex publishes Platform Events when specific records change
2. Target org subscribes to source org's Pub/Sub API gRPC endpoint using OAuth2 authentication
3. Target org processes events via a long-running subscription service or middleware
4. Replay ID stored on target side to enable recovery from disconnects

---

## Decision Guidance

| Scenario | Recommended Pattern | Reason |
|---|---|---|
| Low-volume bidirectional record sharing between partner orgs | API-based sync with REST API | More control and visibility than native S2S; reversible |
| Native S2S feature already enabled | Document constraints; plan migration to API-based | S2S cannot be reversed; manage within its limits |
| Read-only access to another org's data without copying | Salesforce Connect Cross-Org | Real-time, no replication, External Objects pattern |
| Async event notification to another org | Platform Event bridge via Pub/Sub API | Loose coupling; replay support |
| High-volume batch sync (100K+ records) | Bulk API 2.0 cross-org | REST API per-transaction limits; Bulk API required at scale |
| Enterprise-grade multi-org orchestration | MuleSoft with Anypoint Salesforce Connector | Retry, transformation, monitoring beyond native capabilities |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Confirm whether the native S2S feature is already enabled — query PartnerNetworkConnection in both orgs. If enabled, document the existing configuration and its constraints before designing changes.
2. If S2S is not yet enabled, strongly recommend NOT enabling it — modern patterns provide more control. Document the recommendation.
3. Select the appropriate cross-org pattern using the decision table above based on volume, direction, and latency requirements.
4. For API-based sync: set up Connected App in target org and Named Credential in source org; design the sync job with idempotency keys to prevent duplicate records.
5. For Platform Event bridging: confirm Pub/Sub API access and design the subscription service with Replay ID storage for recovery.
6. For Salesforce Connect: provision the External Data Source in the consuming org and confirm the source org's Connected App has the required OAuth scopes.
7. Design error handling: cross-org calls fail silently if the target org is down or rate-limited — implement retry logic and alerting.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Native S2S feature status checked in both orgs (enabled or not)
- [ ] If S2S already enabled: constraints documented (SOAP API limits, irreversibility)
- [ ] Cross-org pattern selected based on volume, direction, and latency
- [ ] Named Credential and Connected App configured for API-based patterns
- [ ] Idempotency key designed for REST API sync patterns
- [ ] Error handling and retry strategy defined for cross-org call failures
- [ ] Pub/Sub API Replay ID storage designed if Platform Event bridging used

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Native S2S cannot be deactivated once enabled** — The Salesforce-to-Salesforce feature is permanently enabled once activated in an org. There is no "disable" option in the Setup UI or via API. Orgs that enabled S2S experimentally cannot remove it. Always confirm business intent before enabling.
2. **S2S consumes SOAP API call limits on both publishing and subscribing orgs** — Each S2S record share counts as a SOAP API call in both the publishing org AND the subscribing org. High-volume scenarios rapidly exhaust API limits on both sides simultaneously, causing failures in both orgs.
3. **Salesforce Connect External Objects don't support all SOQL features** — SOQL against Salesforce Connect External Objects has limitations: no OFFSET in queries, limited aggregate functions, and some relationship queries are not supported. Designs that assume External Objects behave identically to native Salesforce objects will encounter runtime errors.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Cross-org integration pattern decision | Selected pattern with rationale, constraints, and implementation approach |
| Connected App and Named Credential setup guide | Configuration steps for API-based cross-org patterns |
| Error handling design | Retry strategy and monitoring design for cross-org integration failures |

---

## Related Skills

- `architect/multi-org-strategy` — upstream skill for multi-org architecture decisions
- `admin/integration-pattern-selection` — upstream skill to select the integration pattern
- `integration/error-handling-in-integrations` — design error recovery for cross-org failures
