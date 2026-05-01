# Azure Salesforce Integration — Work Template

Use this template when designing or reviewing a Salesforce↔Azure integration.

## Scope

**Skill:** `azure-salesforce-patterns`

**Request summary:** (one line — what the user asked for)

## Direction & Synchrony

- [ ] Direction: ☐ Salesforce → Azure   ☐ Azure → Salesforce   ☐ Bidirectional
- [ ] Synchrony: ☐ Sync (response needed before commit)   ☐ Async
- [ ] Volume estimate: _______ events/day, peak _______ events/min
- [ ] Latency budget: _______ seconds end-to-end

## Path Selected

Pick exactly one and explain why the others were ruled out:

- [ ] Pattern A — **Service Bus Connector** (async, no middleware)
- [ ] Pattern B — **Apex / Flow → Function via Named Credential** (sync)
- [ ] Pattern C — **Data Cloud Azure Blob ingestion** (lake → analytics)
- [ ] Pattern D — **Azure AD SSO + SCIM** (identity, not data)
- [ ] Pattern E (fallback) — **Power Platform Salesforce connector** (citizen automation)

**Why this path:** _________________________________________________

## Auth Model

- [ ] Service Bus: ☐ SAS connection string  ☐ Managed identity
- [ ] Functions/APIM: ☐ OAuth 2.0 client-credentials (preferred)  ☐ Function Key (low-stakes only, no PII)
- [ ] Data Cloud: ☐ Azure service principal scoped to one container
- [ ] SSO: ☐ SAML 2.0 (gallery app)  ☐ OIDC via Auth Provider
- [ ] All secrets live in **Named Credential + External Credential** (no hard-coded keys, no Function Key in Custom Metadata)

## Reliability

- [ ] DLQ behavior defined
- [ ] Retry / replay window agreed on
- [ ] If Service Bus listener: Platform Event channel is **High Volume** (immutable choice — verify before deploy)
- [ ] If Power Platform: dedicated connection + service account reserved
- [ ] If Data Cloud Blob: producer uses immutable file naming (date+UUID), append-only

## Network

- [ ] Public endpoint acceptable, OR Private Link required (and supported in target region)
- [ ] If Private Link: confirm Salesforce-side Private Connect availability and AAD/APIM Private Endpoint setup

## Licensing & Quota

- [ ] Service Bus tier matches volume (Standard / Premium)
- [ ] Data Cloud edition present (if Pattern C)
- [ ] Power Platform per-flow plan reserved (if Pattern E and tenant is busy)
- [ ] Connected App Refresh-Token Policy = "Refresh token is valid until revoked" (server-to-server flows)

## Risks Closed

- [ ] PII path uses OAuth/AAD, not Function Key
- [ ] SCIM mapping locked to lifecycle attributes only (no Profile / Permission Set drift)
- [ ] DLQ replay does not flood the Salesforce-side listener (rate limit upstream)

## Notes

(Record any deviations from the patterns in SKILL.md and why.)
