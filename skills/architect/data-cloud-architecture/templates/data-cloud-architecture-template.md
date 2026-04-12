# Data Cloud Architecture — Decision Template

Use this template when designing or reviewing a Data Cloud implementation architecture.
Complete all sections before finalizing the architecture.

---

## 1. Scope

**Project / Initiative:** (fill in)

**Data Cloud edition:** (Starter / Growth / Plus)

**Multi-BU deployment?** Yes / No — if Yes, document BU isolation requirements below.

**Go-live target date:** (fill in)

---

## 2. Data Sources

List every data source being onboarded to Data Cloud.

| Source Name | Source System | Primary Key | Email Available? | Phone Available? | Proprietary ID Available? | Expected Volume (records) | Refresh Frequency |
|---|---|---|---|---|---|---|---|
| (e.g.) Salesforce CRM Contacts | Sales Cloud | Contact ID | Yes | Yes | No | 500,000 | Real-time CDC |
| (e.g.) Shopify Customers | Shopify | Shopify Customer ID | Yes | No | Yes (Shopify ID) | 1,200,000 | Daily batch |
| | | | | | | | |

---

## 3. DMO Mapping Plan

For each source, document the planned DMO mappings. Mark identity-resolution-eligible mappings explicitly.

| Source Name | Source Field | DMO Name | DMO Field | Identity-Resolution-Eligible? |
|---|---|---|---|---|
| (e.g.) CRM Contacts | Contact.Email | ContactPointEmail | emailAddress | YES |
| (e.g.) CRM Contacts | Contact.Phone | ContactPointPhone | telephoneNumber | YES |
| (e.g.) CRM Contacts | Contact.FirstName | Individual | firstName | No |
| (e.g.) Shopify Customers | customer.email | ContactPointEmail | emailAddress | YES |
| (e.g.) Shopify Customers | customer.id | PartyIdentification | partyIdentificationNumber | YES |
| (e.g.) Shopify Customers | "ShopifyCustomerID" (constant) | PartyIdentification | partyIdentificationType | YES |

**Identity Resolution Eligibility Check:** Every source intended to contribute to Unified Profiles must have at least one row in this table with "YES" in the last column. Sources with no eligible mapping will ingest but will not appear in Unified Individual clusters.

---

## 4. Identity Resolution Ruleset Design

### Match Rules

| Rule # | Rule Name | Match Type | DMO | Field | Filter Condition | Priority |
|---|---|---|---|---|---|---|
| 1 | Email Exact Match | Exact | ContactPointEmail | emailAddress | None | Primary |
| 2 | Loyalty ID Match | Exact | PartyIdentification | partyIdentificationNumber | partyIdentificationType = 'LoyaltyMemberNumber' | Secondary |
| 3 | Phone Normalized Match | Normalized | ContactPointPhone | telephoneNumber | None | Tertiary |

**Transitive matching risk assessment:** Describe any secondary rules that could create unexpectedly large clusters.

(fill in)

### Reconciliation Rules

| Unified Individual Field | Reconciliation Rule | Rationale | Source Priority Order (if applicable) |
|---|---|---|---|
| emailAddress | Most Recent | Email addresses change; most recent source is authoritative | — |
| firstName / lastName | Most Recent | Names may be updated; recent source preferred | — |
| loyaltyTier | Source Priority | Loyalty program is the system of record for tier | 1. Loyalty Program, 2. CRM |
| postalCode | Most Recent | Address changes; most recent source preferred | — |

---

## 5. Segmentation Strategy

For each planned segment, classify the filter attributes and document data freshness requirements.

| Segment Name | Filter Attributes | Attribute Type (DMO / CI / Streaming) | CI Refresh Schedule (if CI) | Time-Sensitivity Requirement | Acceptable? |
|---|---|---|---|---|---|
| (e.g.) High-Intent Browsers | pageViewsLast30Min > 0 | Streaming Insight | N/A | < 30 minutes | Yes |
| (e.g.) Loyal Gold Members | loyaltyTier = 'Gold' | DMO attribute | N/A | 24 hours | Yes |
| (e.g.) High Spenders Q1 | totalPurchaseQ1 > 500 | Calculated Insight | Daily 2AM | 24 hours | Yes |

---

## 6. Activation Target Plan

| Target Name | Channel Type | Platform | Authentication Method | Connection Status | Last Verified | Token Expiry | Pre-Flight Test Date |
|---|---|---|---|---|---|---|---|
| (e.g.) Meta Ads Production | Ad Platform | Meta | OAuth | (to be confirmed) | — | 60 days from auth | — |
| (e.g.) SFTP Export | File-Based | SFTP | Username/Key | (to be confirmed) | — | N/A | — |
| (e.g.) Marketing Cloud BU1 | Salesforce Platform | MC | Connected App | (to be confirmed) | — | N/A | — |

**Pre-flight rule:** All targets must show "Connected" status and have a recorded pre-flight test date before any production segment is published.

---

## 7. Architecture Decision Record

Document key architecture decisions and the rationale for each.

### ADR-001: Primary Identity Match Key

**Decision:** (e.g.) Use email address as the primary identity resolution match key.

**Options considered:** Email exact match / Loyalty ID exact match / Fuzzy name match

**Rationale:** (fill in)

**Tradeoffs accepted:** (fill in — e.g., records without email will not be resolved)

---

### ADR-002: Calculated Insights vs Streaming Insights

**Decision:** (fill in — which use cases use CI vs Streaming Insight)

**Rationale:** (fill in)

---

### ADR-003: Activation Target Authentication Strategy

**Decision:** (fill in — when targets are authenticated relative to go-live)

**Rationale:** (fill in)

---

## 8. Identity Resolution Coverage Validation

After identity resolution runs:

| Metric | Expected | Actual | Delta | Action Required? |
|---|---|---|---|---|
| Total source records (all sources) | (fill in) | (fill in) | — | — |
| Unified Individual count | (fill in — target coverage %) | (fill in) | — | — |
| Cluster size distribution (max cluster size) | < 20 records | (fill in) | — | — |
| Sources with 0 contributing records | 0 | (fill in) | — | — |

---

## 9. Review Checklist

Complete before marking the architecture design approved:

- [ ] Every data source intended to contribute to unified profiles has at least one ContactPointEmail, ContactPointPhone, or PartyIdentification DMO mapping
- [ ] Identity resolution match rule hierarchy is documented (primary → secondary) with precision/recall tradeoffs noted
- [ ] Transitive matching risk assessed for each match rule combination
- [ ] Reconciliation rule chosen and justified for each Unified Individual attribute
- [ ] All activation targets listed with authentication method and pre-flight test plan
- [ ] Segment filters classified as DMO / CI / Streaming Insight with data freshness SLA documented
- [ ] Privacy/consent review completed for any cross-BU or cross-brand identity resolution
- [ ] Architecture Decision Records (ADRs) written for primary identity key, insight type, and activation strategy

---

## 10. Notes and Deviations

Record any deviations from the standard architecture pattern and the business or technical reason for each.

(fill in)
