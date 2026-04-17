---
name: slack-connect-patterns
description: "Use when designing, governing, or troubleshooting Slack Connect channel sharing between two independent organizations. Trigger phrases: external Slack channel collaboration, cross-org Slack channel setup, Slack Connect DLP policy, Slack partner channel governance, regulated industry Slack Connect compliance. Does NOT cover Salesforce-to-Salesforce integration, Salesforce for Slack app setup, or internal single-workspace Slack channels. NOT for Salesforce-to-Salesforce integration."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - slack
  - slack-connect
  - external-collaboration
  - dlp
  - data-governance
  - compliance
  - cross-org
inputs:
  - Slack plan tier for both the inviting and receiving organizations
  - Industry or regulatory context (e.g., HIPAA, FINRA, GDPR) if applicable
  - Number of external organizations that will share the channel
  - Intended data types and sensitivity classification for channel content
  - Partner organization contact (Slack admin email) for connection setup
outputs:
  - Slack Connect governance checklist covering plan tier, DLP approach, and retention policy
  - DLP tooling recommendation based on plan tier
  - Connection setup procedure with admin acceptance steps
  - Retention register documenting split-ownership data sovereignty acknowledgment
  - Compliance considerations for eDiscovery and message deletion asymmetry
triggers:
  - "how do I set up a Slack Connect channel with an external partner organization"
  - "we need to share a Slack channel with a vendor but they are on a different workspace"
  - "what DLP policies apply to our Slack Connect channels with external organizations"
  - "our partner deleted a message in the shared Slack channel but we can still see it"
  - "how do we export a Slack Connect channel for eDiscovery or a legal hold"
  - "what Slack plan does a company need to use Slack Connect"
  - "cross-org Slack channel compliance requirements for a regulated industry"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Slack Connect Patterns

## Overview

Slack Connect is a Slack platform feature that allows two or more independent Slack workspaces to share a channel for cross-organization human collaboration. It is entirely separate from Salesforce integrations. This skill covers the governance, security, compliance, and operational considerations for setting up and maintaining Slack Connect channels in enterprise contexts.

Slack Connect is NOT a data integration mechanism. It does not expose Salesforce APIs, sync Salesforce records, or replace middleware-based Salesforce-to-Salesforce integration. Any design that uses a Slack Connect channel to move Salesforce data between two orgs is an anti-pattern.

## Key Platform Facts

**Plan requirements:** Both the inviting workspace and the receiving workspace must be on a paid Slack plan — Pro, Business+, Enterprise Grid, or Enterprise+. Free plan workspaces cannot initiate or accept Slack Connect invitations. Both sides must independently confirm their plan status before a connection request is initiated.

**Org limit:** A single Slack Connect channel can include members from at most 250 external organizations. Invitations to a 251st organization will fail at the acceptance step without a clear error notification to the inviting admin.

**Admin dual acceptance:** The inviting organization's admin generates the invite link. The receiving organization's Slack admin (not just any member) must explicitly accept the connection request from their Slack admin console. A 14-day expiry window applies to the invite link. If not accepted within 14 days, a new link must be generated.

**Message and data ownership — split-ownership model:** In a Slack Connect channel, each organization independently retains the messages authored by its own members under its own data residency and retention policies. Organization A's retention rules apply to Organization A's members' messages. Organization B's retention rules apply to Organization B's members' messages. There is no shared, unified message store for the channel.

**Message deletion is not bilateral:** If Organization A deletes a message (manually or via a retention policy), the message disappears from Organization A's workspace but remains accessible in Organization B's workspace under Organization B's retention policy. This asymmetry is permanent and by platform design. Deletion cannot be used as a bilateral compliance control.

**eDiscovery scope:** An export from one organization's workspace captures only that organization's members' messages from the Slack Connect channel. A complete channel record for legal or regulatory purposes requires parallel exports from every participating organization, merged by timestamp. Legal teams must understand this limitation before issuing litigation holds.

## DLP Coverage by Plan Tier

Data loss prevention tooling availability depends on the Slack subscription tier of each participating organization:

| Plan | Native Slack DLP |
|---|---|
| Free | Not available |
| Pro | Not available |
| Business+ | Not available |
| Enterprise Grid | Available (PCRE rules, Admin Console > Policies > DLP) |
| Enterprise+ | Available (PCRE rules, Admin Console > Policies > DLP) |

Organizations on Pro or Business+ plans must implement DLP coverage through a third-party integration that subscribes to the Slack Events API. Common options include Nightfall AI, Symantec DLP, and Microsoft Purview DLP for Slack. Third-party DLP operates as a bot in the workspace and intercepts messages via the Events API before or after delivery.

**Scope is workspace-scoped, not channel-scoped:** Even for Enterprise Grid customers, DLP rules apply only to messages authored by that organization's own members. Organization A's DLP rules cannot inspect or act on messages sent by Organization B's members. Bilateral DLP coverage in a Slack Connect channel requires both organizations to independently configure and maintain their DLP tooling.

## Enterprise Key Management and eDiscovery

Slack's Enterprise Key Management (EKM) and native Compliance Export features are also Enterprise Grid / Enterprise+ only. EKM allows an organization to hold the encryption keys for their Slack data. In Slack Connect channels, EKM applies only to the EKM-enabled organization's portion of the channel data — it does not encrypt the partner's messages.

## Operational Governance Requirements

**Plan tier monitoring:** A partner organization's downgrade from Enterprise Grid to Business+ silently removes the native DLP coverage without notifying either organization. Regulated use cases should include a contractual notification clause and a quarterly plan-tier review for all Slack Connect channel partners.

**Channel creation discipline:** Converting an existing internal channel to a Slack Connect channel exposes full prior message history to all external members upon joining. All new external collaboration should begin in a dedicated, freshly created channel with no prior history. Internal discussions about the partner relationship should remain in a separate private channel.

**Retention policy documentation:** Even if matching retention policies are contractually agreed upon between organizations, the asymmetric deletion behavior must be documented in the organization's data governance register and acknowledged by the compliance or legal function.

## Recommended Workflow

1. **Confirm plan eligibility for both organizations.** Before creating a channel or sending an invite, verify that both the inviting and receiving workspaces are on paid Slack plans. Request written confirmation from the partner's Slack admin.

2. **Classify the channel's intended content and determine DLP requirements.** Identify the sensitivity of the data that will flow through the channel. Map that classification to the applicable regulatory regime (HIPAA, GDPR, FINRA, SOX, etc.) and determine whether native or third-party DLP is required. If the inviting or receiving org is on Pro or Business+, third-party DLP must be configured before the first message is sent.

3. **Create a new, empty channel dedicated to the external collaboration.** Never convert an existing internal channel. Name the channel to clearly indicate it is externally shared (e.g., `ext-partnerco-project`).

4. **Configure DLP on both sides before sharing the channel.** Coordinate with the partner organization to confirm their DLP approach. Document both organizations' DLP tooling choices and configuration dates in the governance register.

5. **Generate the Slack Connect invite and send directly to the partner's Slack admin.** Follow up within 5 business days to confirm receipt. Monitor for the 14-day expiry and regenerate if needed.

6. **Document the split-ownership data sovereignty model.** Record in the governance register: both organizations' retention policies, the asymmetric deletion behavior, eDiscovery export procedure, and the 250-org channel limit relative to current participant count.

7. **Establish a quarterly review cadence.** Review partner plan tiers, confirm DLP controls remain active, and confirm retention policies on both sides continue to match contractual commitments. Update the governance register after each review.

## Official Sources Used

- Slack Connect guide: Work with external organizations — https://slack.com/help/articles/360035280511
- How data management features apply to Slack Connect — https://slack.com/help/articles/360035622694
- Slack data loss prevention — https://slack.com/help/articles/1500001560242
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
