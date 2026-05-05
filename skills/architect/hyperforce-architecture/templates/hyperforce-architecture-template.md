# Hyperforce Architecture — Work Template

Use this template when planning, executing, or auditing a Hyperforce migration.

## Scope

**Skill:** `architect/hyperforce-architecture`

**Request summary:** _(Salesforce-initiated migration / customer-elected new region / feature-blocked migration / post-migration audit)_

## Pre-Migration Discovery

| Question | Answer |
|---|---|
| Current infrastructure (First-Gen / Hyperforce) | _(per Setup → Company Information + Trust site)_ |
| Current instance | _(naX, csX, euX, etc.)_ |
| Migration trigger | Salesforce-initiated / customer-elected / feature-blocked |
| Proposed cutover window | _(date/time, read-only duration)_ |
| Source of the trigger | _(notification email, contract change, feature backlog)_ |

## Region Selection

| Question | Answer |
|---|---|
| Data-residency obligations | _(GDPR, India DPDPA, AU Privacy Act, none, etc.)_ |
| Candidate regions | _(US-East, US-West, EU-Frankfurt, EU-Paris, India, etc.)_ |
| Selected region | _(name + cloud provider)_ |
| Pairing region for failover | _(name + residency posture during failover)_ |
| Sovereignty obligation distinct from residency? | yes / no — if yes, residency alone is insufficient |
| Government Cloud / FedRAMP required? | yes / no — if yes, this is NOT a Hyperforce migration |

## IP Allowlist Inventory

Inventory every system that pins to First-Gen IP ranges:

| Owner | System | Current pinning (CIDR) | Hyperforce update plan | Land-by date | Status |
|---|---|---|---|---|---|
| Network ops | Corporate firewall outbound | _(CIDR list)_ | _(new CIDRs)_ | T-14 | _(open / done)_ |
| Identity | Okta / Azure AD ACS allowlist | _(CIDR list)_ | _(new CIDRs)_ | T-14 | |
| Setup | Network Access (Login IP Ranges) | _(CIDR list)_ | _(new CIDRs)_ | T-7 | |
| Integration | Middleware (MuleSoft / Boomi / etc.) | _(CIDR list)_ | _(new CIDRs)_ | T-14 | |
| Partner | Marketing Cloud / MCAE / partner org | _(CIDR list)_ | partner ticket | T-21 | |
| Other | _(custom firewall / vendor allowlist)_ | | | | |

## Hard-Coded URL Inventory

Search repos, runbooks, partner docs for:

- [ ] `na\d+\.salesforce\.com` references replaced with `*.my.salesforce.com`
- [ ] `cs\d+\.salesforce\.com` references replaced
- [ ] `eu\d+\.salesforce\.com`, `ap\d+\.salesforce\.com`, `um\d+\.salesforce\.com` references replaced
- [ ] OAuth issuer URLs reviewed for instance dependencies

## Validation Test Plan

| Test | Owner | Pass criteria | Run window | Status |
|---|---|---|---|---|
| OAuth web-server flow from identity provider | identity team | `200 OK` token issued | 0:00–0:30 post-cutover | |
| Bulk API ingest from middleware | integration | sample job ingests N records | 0:30–1:00 | |
| Scheduled Apex jobs run on schedule | platform | next scheduled run completes | 1:00–4:00 | |
| LWC custom record page loads in Lightning | UX | < 2s render | 0:00–0:30 | |
| IP-pinned restricted profile login | security | login succeeds | 0:30–1:00 | |
| Marketing Cloud / partner-org sync | marketing | sample records sync | 1:00–4:00 | |
| Salesforce Connect external object retrieval | integration | sample external query returns | 1:00–2:00 | |
| TLS handshake from legacy SOAP partners | integration | no handshake failures in SIEM | 0:00–4:00 | |

## Communication Plan

- [ ] T-30 day announcement (users + downstream consumers)
- [ ] T-14 day reminder
- [ ] T-7 day reminder + final allowlist confirmation
- [ ] T-1 day reminder
- [ ] Cutover-window in-app banner
- [ ] Post-cutover all-clear notification

## Architecture Decision Record (post-cutover)

- Documented infrastructure baseline: _(region, cloud provider, pairing region)_
- Updated HA/DR architecture reference: _(link)_
- Updated integration catalog: _(link)_
- Hyperforce-only feature backlog re-sequenced: _(list)_
- Sandbox migration window: _(date)_
- Lessons learned captured: _(link to retrospective)_

## Notes

_(deviations, escalations, partner coordination history)_
