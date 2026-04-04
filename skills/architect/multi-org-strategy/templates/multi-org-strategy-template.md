# Multi-Org Strategy Assessment Template

Complete this template before finalizing or approving a multi-org Salesforce architecture. Every section marked **[REQUIRED]** must be filled in. Sections marked **[IF APPLICABLE]** should be completed if the scenario applies.

---

## 1. Multi-Org Justification **[REQUIRED]**

*Salesforce strongly recommends single-org architecture. A multi-org design requires an explicit, documented justification.*

**Primary justification for multiple production orgs:**

> [Describe the specific requirement that a single Salesforce org cannot satisfy. Examples: "EU data residency regulation requires personal data for EU-resident customers to remain in EU data centers and the current US org does not meet this requirement." or "Acquired company (AcquiCo) runs an independent Salesforce org during a 24-month integration and migration plan."]

**Why cannot a single org with standard isolation features satisfy this requirement?**

> [Explain why Sharing Rules, Permission Sets, Business Units, or other within-org features are insufficient. If you cannot answer this, reconsider the multi-org decision.]

**Is this a permanent or transitional multi-org state?**

- [ ] Permanent — the orgs will remain separate indefinitely
- [ ] Transitional — consolidation is planned; target date: ___________

**Architecture Decision Record (ADR) reference:**

> [Link or document ID for the ADR that records this decision]

---

## 2. Org Inventory **[REQUIRED]**

*List every production Salesforce org in scope. Do not include sandboxes.*

| Org Name | Org ID (18-char) | Region / Data Center | Primary Business Domain | System of Record For | License Types |
|---|---|---|---|---|---|
| [e.g., Global Hub Org] | [e.g., 00D000000000001AAA] | [e.g., US-East (Hyperforce)] | [e.g., Global CRM, Pipeline Reporting] | [e.g., Accounts, Opportunities (US+APAC)] | [e.g., Sales Cloud Enterprise x 500] |
| [Org 2] | | | | | |
| [Org 3] | | | | | |

**Total production org count:** ___

---

## 3. Data Sharing Matrix **[REQUIRED]**

*For each pair of orgs that exchange data, define the direction, data type, frequency, and method. Leave pairs blank if they do not exchange data.*

| Source Org | Target Org | Data Type / Object(s) | Direction | Frequency | Integration Method | Contains PII? |
|---|---|---|---|---|---|---|
| [e.g., EU Spoke] | [e.g., US Hub] | [e.g., Aggregate pipeline totals (no personal fields)] | One-way: EU → US | [e.g., Nightly] | [e.g., Scheduled Apex + REST API] | No |
| [e.g., US Hub] | [e.g., EU Spoke] | [e.g., Product catalog, Price Book entries] | One-way: US → EU | [e.g., Nightly] | [e.g., Bulk API 2.0 batch job] | No |
| | | | | | | |

**Cross-org SOQL:** Not available natively. All cross-org data access uses API callouts or Salesforce Connect External Objects.

---

## 4. Integration Pattern Per Org Pair **[REQUIRED]**

*For each org pair with data exchange, specify the integration design.*

### Org Pair: [Source Org Name] → [Target Org Name]

**Integration method:**
- [ ] REST API (Apex callout via Named Credential)
- [ ] Bulk API 2.0 (scheduled Apex batch or external ETL/iPaaS)
- [ ] Salesforce Connect — External Objects (OData adapter for on-demand lookup)
- [ ] Platform Events (event-driven decoupled delivery)
- [ ] MuleSoft or external middleware
- [ ] Other: ___________

**Named Credential name in calling org:** ___________

**Connected App name in target org:** ___________

**OAuth flow used:**
- [ ] JWT Bearer (server-to-server — recommended for automated integrations)
- [ ] Web Server Flow (user-authorized — for user-context integrations)
- [ ] Other: ___________

**Upsert / deduplication key (external ID field):** ___________

**Error handling and retry strategy:**

> [Describe what happens when the integration fails. Is there a retry mechanism? Dead-letter queue? Alert notification?]

**Volume estimate:** _____ records per run; _____ runs per day

**Governor limit assessment:**
- Calling org callouts per transaction: _____ (limit: 100)
- Target org daily API calls consumed: _____ (budget: check org edition limits)

**Salesforce-to-Salesforce in use for this pair?**
- [ ] No
- [ ] Yes — **LEGACY FLAG**: S2S must be migrated to REST API + Named Credentials. Migration target date: ___________

---

## 5. SSO Configuration **[REQUIRED if users access more than one org]**

**Identity Provider (IdP):** ___________  (e.g., Okta, Azure AD, Ping Identity)

**SSO protocol:** [ ] SAML 2.0  [ ] OIDC  [ ] Other: ___________

**Per-org SSO configuration:**

| Org Name | Entity ID (Issuer) | ACS URL | IdP Application Name | SSO Status |
|---|---|---|---|---|
| [Org 1] | [e.g., https://mycompany.my.salesforce.com] | [e.g., https://mycompany.my.salesforce.com?so=00Dxxx] | [e.g., Salesforce-Prod-US] | [ ] Active  [ ] Pending |
| [Org 2] | | | | [ ] Active  [ ] Pending |

**User provisioning method:**
- [ ] SCIM from IdP (recommended — automates create/deactivate across all orgs)
- [ ] Manual admin provisioning in each org
- [ ] Just-in-Time (JIT) SAML provisioning

**Deactivation process:**

> [Describe how a user is deactivated across all orgs when they leave. If SCIM is not in use, document the manual checklist and who is responsible.]

---

## 6. License Summary **[REQUIRED]**

*Licenses are not shared across orgs. Each production org requires its own license allocation.*

| Org Name | License Type | Count | Annual Cost (if known) | Notes |
|---|---|---|---|---|
| [Org 1] | [e.g., Sales Cloud Enterprise] | [e.g., 500] | | |
| [Org 2] | | | | |
| **Total** | | | | |

**Users with access to more than one production org:**

| User Group | Org 1 Access | Org 2 Access | License Seats Required | Notes |
|---|---|---|---|---|
| [e.g., Global Executives] | [e.g., Read-only dashboard] | [e.g., Full CRM access] | [e.g., 2 seats × 20 users = 40 total] | |

---

## 7. Risk Assessment **[REQUIRED]**

| Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation |
|---|---|---|---|
| User not deactivated in all orgs after termination | M | H | SCIM provisioning from IdP; include in offboarding SLA |
| Cross-org integration hits API limit in target org | M | H | Bulk API 2.0 for high-volume; API usage alerts on target org |
| Hard-coded org ID breaks after environment change | M | M | Named Credentials for endpoints; Custom Metadata for routing config |
| Salesforce-to-Salesforce connection breaks (if in use) | H | M | Migrate S2S to REST API + Named Credentials (see integration plan) |
| External Object OData source unavailable | L | M | Graceful degradation on pages; monitoring alert on OData endpoint health |
| License seat gap: user needs access to new org | M | L | License review checklist in onboarding process for multi-org users |
| Deployment coordination failure across orgs | M | M | Coordinated release schedule; separate release pipelines with integration test gate |
| SSO misconfiguration locks users out of an org | L | H | SSO bypass admin account per org; tested SSO rollback procedure |

**Additional org-specific risks:**

> [Add any risks specific to your org topology or data classification]

---

## 8. Governance and Maintenance **[IF APPLICABLE]**

**Owner of this architecture document:** ___________

**Review frequency:** ___________  (recommended: quarterly for active multi-org architectures)

**Integration monitoring tool / dashboard:** ___________

**Runbook location (cross-org integration failure procedures):** ___________

**Org consolidation plan (if transitional):**

> [If the multi-org state is temporary, document the consolidation plan, target date, and owner. Include the criteria that trigger the migration.]

---

## 9. Checklist Sign-Off **[REQUIRED]**

- [ ] Multi-org justification documented and approved
- [ ] Salesforce-to-Salesforce is not used for any new integrations
- [ ] All cross-org callouts use Named Credentials (no literal URLs or hard-coded secrets in code)
- [ ] Connected App OAuth scopes are scoped to minimum required permissions
- [ ] SSO configured via external IdP for all orgs with user-facing access
- [ ] SCIM or documented manual process covers user deactivation across all orgs
- [ ] License allocation confirmed with Salesforce Account team
- [ ] Governor limit budget modeled for peak integration load on both calling and target orgs
- [ ] Integration error handling and retry strategy defined for each org pair
- [ ] Org inventory and data sharing matrix reviewed and approved by architecture lead

**Architecture lead sign-off:** ___________  Date: ___________
