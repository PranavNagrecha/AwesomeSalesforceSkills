# Fundraising Integration Patterns — Work Template

Use this template when connecting a Salesforce Nonprofit Cloud or NPSP org to a fundraising-adjacent external system: payment gateway (via Elevate), wealth screening tool, email marketing platform, or event management platform.

## Scope

**Skill:** `fundraising-integration-patterns`

**Request summary:** (describe the specific integration the user is requesting — e.g., "connect Stripe via Elevate to record payment outcomes on GiftTransaction")

**Integration type:** (check all that apply)
- [ ] Payment gateway via Salesforce.org Elevate / Connect REST API
- [ ] Wealth screening tool (iWave, DonorSearch, or similar AppExchange package)
- [ ] Email marketing platform (Marketing Cloud Connect, Pardot/Account Engagement)
- [ ] Event platform sync (Eventbrite, Cvent, Classy, Bonterra Events)
- [ ] Other fundraising-adjacent integration (describe below)

## Context Gathered

Record answers to the Before Starting questions from SKILL.md:

- **Org type:** [ ] Nonprofit Cloud (NPC) with GiftTransaction object  [ ] Legacy NPSP with npe01__OppPayment__c
- **Elevate provisioned:** [ ] Yes — confirmed in Setup > Installed Packages  [ ] No — licensing gap to resolve first  [ ] N/A — not a payment integration
- **Target system and vendor API version:** (fill in)
- **API version in use for Salesforce REST calls:** (must be 59.0+ for Elevate Connect API)
- **Existing AppExchange packages relevant to this integration:** (list any installed; check for iWave, DonorSearch, Classy, etc.)
- **Data sensitivity classification:** [ ] Payment/PCI data  [ ] Wealth/PII data  [ ] Marketing preference data  [ ] Event registration data

## Anti-Pattern Check

Before designing anything, confirm none of these apply to the proposed solution:

- [ ] The solution does NOT use `blng.PaymentGateway` for NPSP/NPC payment integration
- [ ] The solution does NOT call a non-existent Salesforce-native wealth screening API endpoint
- [ ] The solution does NOT insert `GiftTransaction` records directly from an external system via REST API
- [ ] The solution does NOT hardcode credentials in Apex — Named Credentials are used for all callouts
- [ ] The solution does NOT assume Elevate is available without verifying it is provisioned

## Approach

**Integration pattern selected** (from SKILL.md Decision Guidance table): (fill in)

**Rationale:** (why this pattern fits the request)

**Primary Salesforce API surface:**
- [ ] Connect REST API `POST /services/data/v59.0/connect/fundraising/transactions/payment-updates`
- [ ] AppExchange managed package (specify: ____________)
- [ ] Marketing Cloud Connect synchronization
- [ ] Custom outbound callout via Named Credentials + scheduled Apex batch

## Field Mapping Plan

| External System Field | Salesforce Target Object | Salesforce Target Field | Notes |
|---|---|---|---|
| (fill in) | Contact or Account | (fill in) | Wealth scores go on Contact, not GiftTransaction |
| (fill in) | GiftTransaction | (fill in) | Gateway reference IDs only; not wealth or marketing data |
| (fill in) | (fill in) | (fill in) | |

## Authentication Design

**Named Credential name:** (e.g., `iWave_API`, `Elevate_Connect`, `MarketingCloud_API`)
**Auth type:** [ ] OAuth 2.0  [ ] API Key (stored as password in Named Credential)  [ ] Basic Auth
**Credential storage:** Named Credentials only — no plaintext in Apex or custom metadata

## Error Handling Design

**Failure modes to handle:**
1. (e.g., Connect REST API timeout on payment update batch — retry logic required)
2. (e.g., iWave rate limit hit during bulk screening — backoff and resume strategy)
3. (fill in additional failure modes)

**Retry approach:** (describe)
**Reconciliation report:** (describe how gift officers or admins will identify and correct failed records)

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them:

- [ ] Payment integration uses Connect REST API or an AppExchange connector — not `blng.PaymentGateway` or a hand-rolled Apex callout directly to the processor
- [ ] API version is 59.0 or higher if calling `/connect/fundraising/transactions/payment-updates`
- [ ] All external callouts use Named Credentials — no hardcoded API keys or passwords in Apex, flow, or custom metadata
- [ ] Wealth screening scores land on `Contact` or `Account` fields, not on `GiftTransaction`
- [ ] GiftTransaction and wealth score fields have correct FLS configured for gift officer profiles
- [ ] Error handling and retry logic is documented and tested for all async callout patterns
- [ ] Event platform records that constitute charitable contributions are promoted to GiftEntry/GiftTransaction through an auditable path, not inserted directly

## Notes

Record any deviations from the standard pattern and the reason:

(fill in — e.g., "Org cannot procure Elevate license; using Classy AppExchange connector as alternative payment integration; noted that blng.PaymentGateway is not applicable here")
