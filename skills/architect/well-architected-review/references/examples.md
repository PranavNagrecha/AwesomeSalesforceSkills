# Examples — Well-Architected Review

---

## Example 1: Full WAF Review — 5-Year-Old Sales Cloud Org

**Context:** A B2B SaaS company commissioned a WAF review of their primary Sales Cloud org after five years of organic growth. The org has 280 users, 45 custom objects, 120 active Flows, and 8 integrations. No formal architecture review had been conducted since initial implementation. The business concern was slowing release velocity and two recent incidents involving governor limit breaches.

### Summary Scorecard

| Pillar | Score | Status |
|--------|-------|--------|
| Trusted | Amber | FLS not enforced in 30% of Apex DML; MFA enabled but not enforced for all profiles |
| Easy | Red | Key Opportunity page layout has 67 fields; three custom objects abandoned with zero records |
| Adaptable | Amber | Daily API limit at 72% peak; test coverage at 76%; no sandbox refresh policy documented |

### Top 3 Findings: Trusted

1. **FLS not enforced in legacy Apex classes (High).** Fifteen Apex classes written before Spring '22 use `without sharing` or perform DML without `stripInaccessible`. Any user with a UI-level restriction can bypass it through these code paths. Recommendation: migrate classes to `with sharing` and add `stripInaccessible(AccessType.UPSERTABLE, …)` before DML.

2. **MFA enforced for admins only (High).** The MFA enforcement setting is enabled at the profile level for System Administrators but not for Sales Representatives or Integration Users. Recommendation: enforce MFA via the org-wide "Require MFA" setting so it applies to all user types, then review SSO configuration for the IdP to pass the MFA assertion.

3. **No data classification inventory (Medium).** The org stores personal data (email, phone, address) and financial data (contract values, billing amounts) with no formal classification. GDPR right-to-erasure requests are handled manually with no documented process. Recommendation: produce a data map within 60 days; implement a right-to-erasure automation using a custom object and Flow.

### Top 3 Findings: Easy

1. **Opportunity page layout unusable on mobile (Red).** The primary Opportunity layout has 67 fields in a single section. Page load time in the mobile app is 11 seconds. Sales reps report completing Opportunity updates from a laptop only, defeating the mobile investment. Recommendation: create a role-specific Lightning page with 12 key fields and defer secondary fields to a tab.

2. **Three abandoned custom objects cluttering the data model (Amber).** Objects `Training__c`, `Legacy_Event__c`, and `Old_Campaign_Tracker__c` have zero records, no active Flows referencing them, and no named owner. They appear in all object pickers and confuse new admins. Recommendation: document reason for retention or delete after confirming with business stakeholders.

3. **Quote generation is a manual copy-paste process (Amber).** Sales reps copy Opportunity line items into a spreadsheet template to produce a quote. Salesforce CPQ is licensed but unused. Recommendation: activate CPQ or implement a minimal Quote object Flow to generate PDFs; eliminate the manual step within one quarter.

### Top 3 Findings: Adaptable

1. **Daily API limit at 72% — one integration spike away from a breach (High).** The middleware platform polls three Salesforce objects every 15 minutes using REST API calls. At peak (month-end processing), API consumption reaches 72% of the daily limit. A single additional integration or a bulk data load during peak would breach the limit. Recommendation: switch polling to event-driven using Platform Events or Change Data Capture; target a steady-state API consumption below 50%.

2. **Test coverage at 76% with no assertions in 8 test classes (Amber).** Overall org test coverage meets the 75% deployment threshold but eight test classes contain no `System.assertEquals` or `System.assertNotEquals` calls. These tests provide false coverage. Recommendation: audit test classes for assertion presence; target 85% meaningful coverage within two sprints.

3. **No sandbox refresh policy (Amber).** The full sandbox was last refreshed 14 months ago. Production configuration has diverged significantly; three recent deployments required manual post-deployment steps because the sandbox did not reflect production. Recommendation: document a quarterly full sandbox refresh cadence and implement automated post-copy scripts for standard configuration (custom settings, named credentials).

---

## Example 2: Pre-Go-Live WAF Sign-off — New Service Cloud Implementation

**Context:** A financial services firm is going live with a new Service Cloud implementation for their contact centre. The project has been in build for 6 months with a third-party SI. The WAF sign-off is a contractual gate before production deployment.

### Sign-off Checklist

**Trusted: PASS with one accepted risk**
- [x] All Apex classes use `with sharing` or `inherited sharing` — confirmed via code review
- [x] Named Credentials used for all outbound callouts to the case management API — no hardcoded endpoints
- [x] MFA enforced at the org level — confirmed in Security Health Check
- [x] Case object OWD set to Private — agents see only their own cases; supervisors granted Read via role hierarchy
- [ACCEPTED RISK] Field Audit Trail not enabled — financial services compliance team has accepted a 12-month window to enable Shield; accepted risk documented and signed by CISO

**Easy: PASS**
- [x] User acceptance testing completed with 15 contact centre agents across 3 personas — sign-off obtained
- [x] Key Service Console page load time confirmed below 3 seconds in full sandbox (mirroring production hardware)
- [x] Screen Flow for case creation reviewed for accessibility — no colour-only information, all inputs labelled
- [x] Mobile not in scope — contact centre agents are desktop only; waived with stakeholder documentation

**Adaptable: CONDITIONAL PASS — one item deferred**
- [x] Test coverage for all new Apex: 89%
- [x] No hardcoded IDs in any Apex class or Flow — Custom Metadata used for all configuration values
- [x] Deployment runbook documented and executed successfully in full sandbox
- [x] Scratch org definition file present in source control
- [DEFERRED] CI/CD pipeline not in place — team is using Change Sets for this release; a Jira epic is open to migrate to a SFDX-based pipeline within 60 days of go-live. Accepted by delivery lead with target date.

**Sign-off decision: APPROVED TO GO LIVE** with two documented deferred items (Shield enablement and CI/CD pipeline), each with named owner and target date.

---

## Official Sources Used

- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Well-Architected: Easy — https://architect.salesforce.com/docs/architect/well-architected/guide/easy.html
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/docs/architect/well-architected/guide/adaptable.html
