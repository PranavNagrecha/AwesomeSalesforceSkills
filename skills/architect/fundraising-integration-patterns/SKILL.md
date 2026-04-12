---
name: fundraising-integration-patterns
description: "Use this skill when connecting a Salesforce Nonprofit Cloud or NPSP org to fundraising-adjacent systems: payment gateways via Salesforce.org Elevate, wealth screening tools (iWave, DonorSearch), email marketing platforms (Marketing Cloud, Pardot), and event management platforms. Trigger keywords: payment gateway nonprofit, Elevate payment services, GiftTransaction API, wealth screening integration, iWave Salesforce, DonorSearch scores, donor email marketing sync, event registration fundraising. NOT for generic integration patterns, Salesforce Billing payment gateways (blng.PaymentGateway), or non-fundraising CRM integrations."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I connect our payment processor to Nonprofit Cloud so gift transactions are recorded automatically?"
  - "We want to pull wealth screening scores from iWave or DonorSearch into Salesforce donor records"
  - "Our email marketing platform needs to sync with Salesforce to target major gift prospects for fundraising campaigns"
  - "How should we integrate our event registration platform so ticket purchases flow into fundraising records?"
  - "Can I write a custom Apex payment gateway adapter to replace Elevate for NPSP payment processing?"
tags:
  - nonprofit-cloud
  - npsp
  - elevate
  - payment-gateway
  - wealth-screening
  - fundraising-integration
  - gift-transaction
  - donor-data
inputs:
  - "Salesforce org edition and whether Nonprofit Cloud (NPC) or legacy NPSP is installed"
  - "Target integration system type: payment gateway, wealth screener, email platform, or event platform"
  - "Existing AppExchange packages installed (iWave, DonorSearch, Luminate, etc.)"
  - "API access credentials and authentication model for the external system"
  - "Data volume expectations (gift transactions per day, constituent record count)"
outputs:
  - "Integration architecture recommendation specifying the correct Salesforce API surface for each system type"
  - "Decision guidance on Elevate vs. custom solutions with explicit scope constraints"
  - "Field mapping plan for wealth screening score storage on Contact or Account"
  - "Review checklist validating security, error handling, and data integrity requirements"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
---

# Fundraising Integration Patterns

This skill activates when a Salesforce Nonprofit Cloud or NPSP practitioner needs to connect the org to fundraising-adjacent external systems. It covers the correct integration surface for payment gateways (Salesforce.org Elevate / Connect REST API), wealth screening tools, email marketing platforms, and event management systems — and explicitly guards against using the wrong integration APIs such as blng.PaymentGateway, which is Salesforce Billing only.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org runs **Nonprofit Cloud (NPC)** with the native Fundraising data model or legacy **NPSP**. NPC exposes the `GiftTransaction` and `GiftCommitment` objects and the Salesforce.org Elevate Connect REST API endpoints; NPSP uses `npe01__OppPayment__c` and has a different Elevate integration path.
- Identify whether **Salesforce.org Elevate (Payment Services)** is already provisioned. Elevate is a separately licensed add-on; without it, no inbound payment gateway API surface exists in Nonprofit Cloud.
- Determine the authentication and data residency requirements. Payment data carries PCI scope implications; wealth screening data is PII. Both require field-level security review and Named Credential setup for external callouts.
- The most common wrong assumption practitioners make is that the `blng.PaymentGateway` Apex interface — used by **Salesforce Billing** — is applicable to NPSP or Nonprofit Cloud payment processing. It is not; that interface is part of the Billing managed package and has no footprint in the nonprofit data model.
- Platform constraints: the Elevate Connect REST API endpoint `/connect/fundraising/transactions/payment-updates` was introduced at **API version 59.0** (Spring '23+). Orgs on earlier API versions cannot call it.

---

## Core Concepts

### Salesforce.org Elevate and the Connect REST API for Payment Gateway Integration

Salesforce.org **Elevate (Payment Services)** is the endorsed integration layer between Nonprofit Cloud / NPSP orgs and payment processors such as Stripe. When a donor completes a payment via Elevate, the payment processor calls back through Salesforce.org infrastructure and the result is surfaced to the Salesforce org via the Connect REST API.

The key endpoint is:

```
POST /services/data/vXX.0/connect/fundraising/transactions/payment-updates
```

Minimum API version: **59.0** (Spring '23 / Spring '25+ is the stated support baseline for current features).

This endpoint accepts a JSON body that updates gateway and processor metadata on one or more `GiftTransaction` records. The fields that can be updated include gateway reference identifiers, processor response codes, and payment instrument metadata. The endpoint does **not** create new `GiftTransaction` records; record creation flows through the Elevate-managed gift entry process.

A parallel endpoint exists for commitments (recurring gifts):

```
POST /services/data/vXX.0/connect/fundraising/commitments/payment-updates
```

This endpoint updates payment instrument metadata for all active `GiftCommitment` records tied to a specific payment method, enabling scenarios such as card-on-file updates.

**Critical constraint:** The Elevate connector is not replaceable with custom Apex. There is no public Apex interface in Nonprofit Cloud analogous to `blng.PaymentGateway`. Custom payment adapters using Apex callouts can forward data to the Connect REST API endpoint from within Salesforce code, but the endpoint itself is the integration contract — not an overridable Apex interface.

### Wealth Screening Integration (iWave, DonorSearch, and Peer Tools)

Wealth screening tools identify high-capacity donors by analyzing public and proprietary financial data sources. Salesforce integration happens via **AppExchange managed packages** — not native Salesforce APIs.

- **iWave for Salesforce** and **DonorSearch for Salesforce** are the dominant managed packages. Each provides its own connected-app authentication, custom objects for raw screening output, and flows or Apex triggers that write summary scores to standard `Contact` or `Account` fields.
- Score results land on `Contact` fields such as `iwv__RatingScore__c` (iWave) or standard custom fields configured by the package; they do **not** write to `GiftTransaction` or `GiftEntry`.
- Bulk screening workflows submit lists of Contact or Account IDs to the vendor API and poll for results. Native integration uses the package UI; custom integrations use the vendor's REST API with Named Credentials and a scheduled Apex batch job.
- There is no native Salesforce API for wealth data. Practitioners who attempt to build their own wealth screening integration without a managed package must implement the vendor's proprietary REST API — there is no Salesforce-platform abstraction layer.

### Email Marketing Integration for Nonprofit Fundraising

The two supported Salesforce email marketing platforms for nonprofits are **Marketing Cloud** and **Marketing Cloud Account Engagement (formerly Pardot)**. A third common option in the nonprofit sector is **Luminate Online** (Blackbaud's platform), which uses a separate REST API.

- **Marketing Cloud Connect**: synchronizes `Contact`, `Lead`, and Campaign data between the core org and Marketing Cloud. For nonprofits, the typical pattern is to build a data extension from `Contact` + wealth score + giving history fields, then trigger journey entries on donation milestones or lapsed-donor thresholds.
- **Marketing Cloud Account Engagement (Pardot)**: suited to major gifts and planned giving where lead-nurture timing matters. Prospects sync bidirectionally; custom fields carry wealth screening scores and lifetime giving totals for segmentation.
- **Key data model note:** `GiftTransaction` is not natively surfaced as a Marketing Cloud synchronized object. Practitioners must expose giving totals on `Contact` or `Account` via roll-up fields or calculated fields before sync.

### Event Platform Integration

Event management platforms (Eventbrite, Cvent, Classy, Bonterra Events) use bidirectional sync patterns:

- **Inbound (event → Salesforce):** Registration and ticket purchase data arrives via the platform's webhook or REST API. The recommended landing zone is a custom intermediate object (or standard `CampaignMember`) before promoting to `GiftTransaction` if the ticket purchase constitutes a charitable contribution.
- **Outbound (Salesforce → event platform):** Segment data built from Salesforce (major donor lists, volunteer histories) is pushed to the event platform for targeted invitations. Use a scheduled data export or Platform Events-triggered outbound callout.
- **Classy and Bonterra (EveryAction)** provide purpose-built Salesforce AppExchange connectors that handle attribution linking and soft credit creation in NPSP automatically.

---

## Common Patterns

### Pattern 1: Elevate Payment Gateway Callback Processing

**When to use:** The org uses Salesforce.org Elevate for online giving and needs to reconcile payment processor outcomes (authorization, capture, decline) against `GiftTransaction` records.

**How it works:**
1. Donor completes payment on the Elevate-hosted gift form or a custom LWC that wraps the Elevate payment tokenization SDK.
2. Elevate infrastructure receives the processor response and calls the Salesforce Connect REST API on behalf of the org.
3. The `POST /connect/fundraising/transactions/payment-updates` call updates the `GiftTransaction` record with gateway reference ID, payment status, and processor metadata.
4. A Platform Event or Change Data Capture trigger on `GiftTransaction` can fire downstream automation (receipt emails, pledge fulfillment checks).

**Why not the alternative:** Building a direct Apex callout to the payment processor bypasses Elevate's PCI-compliant tokenization layer, introduces the org into PCI scope, and eliminates the audit trail that Elevate maintains. Custom Apex payment adapters using `blng.PaymentGateway` do not compile in NPSP/NPC orgs because the Billing managed package is absent.

### Pattern 2: Managed-Package Wealth Screening Batch Sync

**When to use:** The org wants to score a large constituent list against a wealth screening service and store results on `Contact` for major gift cultivation.

**How it works:**
1. Install the vendor's managed package (iWave for Salesforce or DonorSearch for Salesforce) from AppExchange.
2. Configure Named Credentials using the vendor-issued API key.
3. Use the package's bulk screening interface to submit Contact IDs to the vendor's screening queue.
4. The package's asynchronous batch job polls for results and writes scores to the designated `Contact` fields.
5. Build a list view or report on scored Contacts for gift officer assignment.

**Why not the alternative:** Calling the vendor API directly via custom Apex without the managed package requires reimplementing field mapping, error handling, rate limiting, and credential management that the package provides. The vendor also publishes schema changes in package updates; a custom implementation requires manual maintenance on every vendor API version bump.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org uses Elevate and needs to record payment outcomes on GiftTransaction | Use Connect REST API `POST /connect/fundraising/transactions/payment-updates` at API v59.0+ | This is the only supported gateway callback surface for Nonprofit Cloud |
| Org wants payment processing without Elevate license | Evaluate third-party AppExchange connectors (Classy, iATS, Stripe for Nonprofits) | Elevate is add-on licensed; alternatives exist but none use blng.PaymentGateway |
| Wealth screening scores need to land on constituent records | Install iWave or DonorSearch managed package from AppExchange | No native Salesforce API; managed packages handle auth, field mapping, and versioning |
| Email marketing to major gift prospects | Marketing Cloud Connect with Contact-level roll-up fields for giving totals | GiftTransaction not natively in MC sync; totals must be promoted to Contact/Account |
| Event ticket purchases that include charitable component | Custom intermediate object → GiftEntry promotion via Elevate batch API | Preserves audit trail; avoids direct GiftTransaction creation outside Elevate |
| Org is on Salesforce Billing (not NPSP/NPC) and needs custom payment adapter | Implement `blng.PaymentGateway` Apex interface | Correct context for blng interface; does not apply to nonprofit data model |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the integration category** — confirm which of the four types applies: payment gateway, wealth screening, email marketing, or event platform. Each has a distinct Salesforce API surface and a distinct set of wrong approaches to guard against.
2. **Verify Elevate provisioning for payment integrations** — check Setup > Installed Packages for "Elevate" or "Payment Services". If absent and the request involves payment processing, surface the licensing requirement before designing any integration; do not propose blng.PaymentGateway as an alternative.
3. **Confirm API version compatibility** — for Connect REST API usage, verify the org's default API version in Setup > API. The `/connect/fundraising/transactions/payment-updates` endpoint requires API v59.0 minimum; downgrade is not supported.
4. **Map the target fields** — for wealth screening, identify which Contact or Account fields the managed package writes to. For email marketing, identify the roll-up or formula fields that will surface GiftTransaction totals on Contact before configuring the Marketing Cloud sync.
5. **Design Named Credentials and authentication** — all outbound callouts (wealth screener API, event platform webhooks, email platform) must use Named Credentials. Do not hardcode credentials in Apex or flow variables.
6. **Implement error handling and reconciliation** — payment callback integrations must handle partial failures: a Connect REST API call that fails mid-batch leaves some GiftTransaction records without gateway metadata. Design a retry log and reconciliation report.
7. **Validate FLS and sharing rules on sensitive objects** — `GiftTransaction` contains financial PII; `Contact` wealth scores are sensitive. Confirm field-level security restricts wealth score visibility to gift officers and prevents exposure via list views or reports accessible to lower-privilege users.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Payment integration uses Connect REST API or an AppExchange connector — not `blng.PaymentGateway` or a hand-rolled Apex callout directly to the processor
- [ ] API version is 59.0 or higher if calling `/connect/fundraising/transactions/payment-updates`
- [ ] All external callouts use Named Credentials — no hardcoded API keys or passwords in Apex, flow, or custom metadata
- [ ] Wealth screening scores land on `Contact` or `Account` fields, not on `GiftTransaction`
- [ ] GiftTransaction and wealth score fields have correct FLS configured for gift officer profiles
- [ ] Error handling and retry logic is documented and tested for all async callout patterns
- [ ] Event platform records that constitute charitable contributions are promoted to GiftEntry/GiftTransaction through an auditable path, not inserted directly

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **blng.PaymentGateway is Salesforce Billing only** — The `blng.PaymentGateway` Apex interface is declared in the Salesforce Billing managed package. It has no relationship to NPSP or Nonprofit Cloud and will not compile in an org that does not have Billing installed. LLMs and practitioners who search for "Salesforce payment gateway Apex interface" frequently surface Billing documentation and attempt to apply it to nonprofit payment processing — this always fails at compile time in an NPSP/NPC org.
2. **Elevate connector is not replaceable with custom Apex** — Unlike Salesforce Billing where a custom `blng.PaymentGateway` implementation routes transactions to a new processor, Elevate has no equivalent Apex extension point. The Elevate infrastructure sits outside the org boundary and calls back via the Connect REST API. There is no way to redirect Elevate callbacks to a different Apex handler, and no supported path to substitute a different payment processor in the Elevate flow without switching to a different AppExchange connector entirely.
3. **Wealth screening scores go on Contact, not GiftTransaction** — Screening tools evaluate donor capacity, not individual transactions. Both iWave and DonorSearch write their output to `Contact` (and sometimes `Account`) fields. Practitioners who attempt to store wealth scores on `GiftTransaction` or `GiftEntry` will find no supported package field mapping for those objects; custom fields can be created there, but no vendor tooling will populate them.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration architecture recommendation | Written summary of the correct API surface, authentication model, and data flow for the specific integration type requested |
| Field mapping plan | Table of source system fields → Salesforce target fields, including the correct object (Contact vs. GiftTransaction) for each data type |
| Named Credential configuration guide | Step-by-step setup for authenticating outbound callouts to the external system |
| Error handling and retry design | Documented failure modes and reconciliation approach for async payment callbacks or batch wealth screening jobs |

---

## Related Skills

- `gift-entry-and-processing` — covers GiftTransaction and GiftEntry data model, batch gift processing, and NPSP payment processing flows; use alongside this skill when the integration feeds into gift entry
- `integration-framework-design` — use for generic Salesforce integration architecture; this skill supersedes it for fundraising-specific integration surfaces
- `billing-integration-apex` — covers the `blng.PaymentGateway` interface for Salesforce Billing; explicitly not applicable to NPSP/NPC payment processing
