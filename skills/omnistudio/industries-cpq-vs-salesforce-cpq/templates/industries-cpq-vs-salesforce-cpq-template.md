# CPQ Selection and Migration Decision Framework

Use this template to document a CPQ product selection or migration planning engagement.
Fill all sections before presenting recommendations to stakeholders.

---

## Engagement Context

**Org name / customer:** _______________

**Date:** _______________

**Scope:** (check one)
- [ ] New CPQ selection — no CPQ currently deployed
- [ ] Migration from Salesforce CPQ managed package to Revenue Cloud
- [ ] Migration from Vlocity CPQ to native Industries CPQ
- [ ] Coexistence architecture review
- [ ] Cross-product migration assessment (Industries CPQ ↔ Revenue Cloud)

---

## 1. Industry Vertical and Business Model

| Question | Answer |
|---|---|
| Primary industry vertical | _____ (telco / energy / insurance / media / high-tech / manufacturing / other) |
| Selling motion | _____ (B2C catalog / B2B enterprise / partner channel / self-service portal) |
| Average product catalog size | _____ (number of SKUs or catalog items) |
| Bundle depth (max nesting levels) | _____ |
| Attribute-based pricing required? | Yes / No |
| Guided selling UI required? | Yes / No |

**Vertical-to-product mapping:**
- Telco, Energy, Media, Insurance → Industries CPQ is the standard product
- High-tech, Manufacturing, SaaS → Revenue Cloud (native) is the standard product

---

## 2. Current CPQ State Audit

| Item | Details |
|---|---|
| Salesforce CPQ managed package version (if deployed) | _____ |
| Vlocity CPQ / Industries CPQ version (if deployed) | _____ |
| OmniStudio licensed and deployed? | Yes / No |
| Industry cloud licensed? (Communications, Energy, etc.) | Yes — specify: _____ / No |
| Number of active products in CPQ | _____ |
| Number of custom fields on SBQQ__Quote__c / QuoteLine__c | _____ |
| Apex plugin implementations (list interfaces used) | _____ |
| External integrations referencing SBQQ__ objects | _____ |

---

## 3. Required CPQ Capabilities

For each capability, mark which product satisfies it natively:

| Capability | Required? | Industries CPQ | Salesforce CPQ | Revenue Cloud |
|---|---|---|---|---|
| Attribute-based product configuration | | Native | Requires customization | Partial (LWC configurator) |
| Multi-level bundling (3+ levels) | | Native | Limited | Supported |
| Calculation Procedure pricing engine | | Native | Not available | Not available |
| OmniScript guided selling | | Native | Not available | Not available |
| Standard QLE quote line editor | | Not available | Native | Native (redesigned) |
| Discount approval chains | | Via OmniStudio flows | Native | Native |
| Contract lifecycle management | | Via asset management | Via CPQ contracts | Native (CLM included) |
| Subscription billing | | Via industry assets | Salesforce Billing add-on | Native billing included |
| Partner community quoting | | Varies by cloud | Native | Verify in current release notes |
| DataPacks deployment tooling | | Required | Not applicable | Not applicable |
| Standard Metadata API deployment | | Partial | Full | Full |

**Notes on gaps:** _______________

---

## 4. Decision

**Recommended CPQ product:** _____ (Industries CPQ / Revenue Cloud / Keep Salesforce CPQ + plan migration)

**Decision rationale:**
1. _______________
2. _______________
3. _______________

**Alternatives considered and rejected:**
- _______________

**Licensing prerequisites confirmed:**
- [ ] Industries cloud license confirmed (if recommending Industries CPQ)
- [ ] Revenue Cloud license confirmed (if recommending Revenue Cloud)
- [ ] OmniStudio license confirmed (if recommending Industries CPQ)

---

## 5. Migration Path (if applicable)

### Source → Target

**Source:** _____ (Vlocity CPQ / Salesforce CPQ managed package)
**Target:** _____ (Native Industries CPQ / Revenue Cloud)

### Migration Steps

| Step | Description | Owner | Target Date |
|---|---|---|---|
| 1 | Audit source CPQ configuration | | |
| 2 | Map source objects/components to target equivalents | | |
| 3 | Namespace migration (if Vlocity → native OmniStudio) | | |
| 4 | Migrate product catalog | | |
| 5 | Migrate open quotes / active carts | | |
| 6 | Migrate contracts and assets | | |
| 7 | Regression test pricing and guided-selling flows | | |
| 8 | Cutover and decommission source CPQ | | |

### Migration Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| SBQQ__ namespace references in custom Apex | | | Remap before cutover |
| %vlocity_namespace% tokens in DataPacks | | | Run namespace migration step |
| Apex plugin interfaces not available in target | | | Redesign as native rules |
| Feature parity gap in target product | | | Verify against current release notes |
| Open quote data loss during cutover | | | Freeze open quotes; migrate manually |

---

## 6. Coexistence Plan (if both products will run simultaneously)

**Coexistence duration:** _____ (months)

**Consolidation target date:** _____

**Shared object surface:**
- Account: shared by both CPQ products
- Opportunity: shared; record type determines which CPQ flow launches
- Quote objects: NOT shared (SBQQ__Quote__c vs Industries CPQ Order)
- Custom reporting summary object: _____ (name)

**Governance:**
- [ ] Separate release trains for each CPQ product documented
- [ ] CPQ-specific permission sets control user access
- [ ] No shared custom objects between the two CPQ namespaces

---

## 7. Sign-Off

| Role | Name | Date |
|---|---|---|
| Solution Architect | | |
| Salesforce CPQ SME | | |
| Industries CPQ SME | | |
| Business Sponsor | | |
