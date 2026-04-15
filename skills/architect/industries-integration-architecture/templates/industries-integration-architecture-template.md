# Industries Integration Architecture — Work Template

Use this template when designing or reviewing the integration layer between a Salesforce Industries cloud and a vertical backend system.

## Scope

**Skill:** `industries-integration-architecture`

**Request summary:** (fill in what the user asked for)

**Industries vertical in scope:** [ ] Insurance Cloud  [ ] Communications Cloud  [ ] Energy & Utilities Cloud

**External backend system(s):**
- System name:
- Type: [ ] Policy Administration System  [ ] BSS/OSS  [ ] CIS  [ ] Other:
- Integration endpoint(s) available:

---

## System-of-Record Boundary Decision

Complete this table before any integration design work. Every data domain must have exactly one authoritative system.

| Data Domain | Examples | Authoritative System | Salesforce Role |
|---|---|---|---|
| Policy state / coverage | premiums, coverage limits, effective dates | [ ] External PAS  [ ] Salesforce | [ ] System of record  [ ] Read-only projection |
| Rate plans / tariffs | rate codes, tariff definitions, pricing tiers | [ ] External CIS/BSS  [ ] Salesforce | [ ] System of record  [ ] Read-only projection |
| Order fulfillment status | provisioning state, activation status | [ ] External BSS/OSS  [ ] Salesforce | [ ] System of record  [ ] Read-only projection |
| Customer engagement records | cases, interaction summaries, service requests | [ ] External system  [ ] Salesforce | [ ] System of record  [ ] Engagement layer |
| Billing/account balance | outstanding balance, payment history | [ ] External CIS/billing  [ ] Salesforce | [ ] System of record  [ ] Read-only projection |

**Decision notes:** (record any disputed domains and how they were resolved)

---

## Context Gathered

Answer these before designing the integration:

- **Industries cloud licensed:** (Insurance / Communications / E&U)
- **OmniStudio enabled and licensed:** [ ] Yes  [ ] No
- **Named Credentials configured for external system:** [ ] Yes  [ ] No  [ ] To be created
- **External system authentication method:** [ ] OAuth 2.0 client_credentials  [ ] API Key  [ ] mTLS  [ ] Other:
- **Expected external system response time (p99):** (seconds) — if > 5s, async pattern required
- **For Communications Cloud:** TM Forum API Access Mode: [ ] Direct Access  [ ] MuleSoft Gateway (deprecated — flag for migration)
- **For E&U:** CIS-to-Salesforce sync: [ ] One-way inbound  [ ] Bidirectional (anti-pattern — flag for review)

---

## Integration Pattern Selected

**Read path pattern:**

[ ] Integration Procedure HTTP Action (synchronous, < 5s external response)
[ ] Integration Procedure → Apex Action → Async Apex (long-running external calls)
[ ] Local Salesforce SOQL (data pre-synced from external system — preferred for reference data)

**Write path pattern:**

[ ] Integration Procedure HTTP Action → external system write endpoint (Salesforce creates engagement artifact only)
[ ] Platform Event → Apex subscriber → external system callout
[ ] ServiceOrder record → external system reads and fulfills (E&U pattern)

**For Communications Cloud BSS/OSS:**

[ ] Direct TM Forum API Access via Named Credential
[ ] MuleSoft Gateway — MIGRATION REQUIRED before Winter '27

**Rationale for pattern selected:** (why this pattern, what alternatives were considered)

---

## Integration Procedure Design (Read Path)

**IP Name:** `<Vertical>_<DataDomain>_Read`

| Step | Element Type | Description |
|---|---|---|
| 1 | HTTP Action | GET `callout:<NamedCredential>/<endpoint-path>` — retrieve from external system |
| 2 | DataRaptor Transform | Map external JSON response → OmniScript data JSON keys |
| 3 | Set Values (error) | If HTTP status != 200: set `output:error` with user-facing message |

**Named Credential used:** (name)
**Response fields mapped:** (list key fields extracted from external response)
**Error handling:** (what the OmniScript displays if external system is unavailable)

---

## Integration Procedure Design (Write Path)

**IP Name:** `<Vertical>_<DataDomain>_Write`

| Step | Element Type | Description |
|---|---|---|
| 1 | HTTP Action | PUT/POST `callout:<NamedCredential>/<endpoint-path>` — submit change to external system |
| 2 | DataRaptor Extract | Create/update Salesforce engagement artifact (Interaction__c, Case, ServiceOrder) |
| 3 | Set Values (error) | If HTTP status != 200: surface error to OmniScript, do not create engagement artifact |

**External system write endpoint:** (endpoint path)
**Idempotency confirmed:** [ ] Yes — external endpoint accepts duplicate requests safely  [ ] No — requires deduplication key
**Salesforce artifact created on success:** (object and fields stored)

---

## Deployment Checklist

Before deploying to production:

- [ ] Named Credential(s) for all external endpoints configured in target org
- [ ] External Credential with OAuth 2.0 scope reviewed and confirmed against required endpoints
- [ ] Integration Procedure + dependent DataRaptors + Named Credential in single deployment package
- [ ] IP version numbers match OmniScript element references in deployment package
- [ ] FLS Read-Only configured on all CIS/PAS-sourced fields for all applicable profiles
- [ ] Error handling IP elements tested with simulated external system timeout
- [ ] For Communications Cloud: Direct TM Forum API Access confirmed (not MuleSoft Gateway)
- [ ] For E&U: CIS rate sync one-way confirmed; no Salesforce → CIS write path exists

---

## Review Checklist

Run through these before marking the integration design complete:

- [ ] System-of-record boundary table completed and reviewed with stakeholders
- [ ] No dual-write pattern: Salesforce does not write operational data back to PAS/BSS/CIS
- [ ] All HTTP Action endpoints use Named Credentials — no hardcoded URLs or credentials
- [ ] Error handling elements present on all read-path and write-path IPs
- [ ] Long-running callouts (> 5s) delegated to async patterns
- [ ] Communications Cloud: no new MuleSoft Gateway usage introduced
- [ ] E&U: CIS rate plan fields locked read-only via FLS post-sync
- [ ] Deployment manifest includes all dependent OmniStudio artifacts

---

## Notes

(Record any deviations from the standard pattern, stakeholder decisions, or known risks)
