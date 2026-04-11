# FSC Architecture Patterns — Work Template

Use this template when designing or reviewing a Financial Services Cloud solution architecture.

---

## Scope

**Skill:** `fsc-architecture-patterns`

**Request summary:** (fill in what the user asked for)

---

## 1. Data Model Baseline

**Data model type:** [ ] Managed-package FSC (FinServ__ namespace)  [ ] Platform-native FSC (standard objects)

**How confirmed:** (e.g., checked Setup > Installed Packages — Financial Services Cloud package [present / not present])

**Installed package version (if managed):** _______________

**Decision rationale if greenfield:** (why managed-package or platform-native was chosen)

---

## 2. Compliant Data Sharing Configuration

**CDS enabled:** [ ] Yes  [ ] No  [ ] Unknown — needs verification

**FinancialAccount OWD:** [ ] Private  [ ] Read-Only  [ ] Public Read/Write  [ ] Unknown

**CDS precondition met (OWD = Private):** [ ] Yes  [ ] No — remediation required before proceeding

**Share set design:**

| Share Set Name | Object | Basis for Access | Access Level |
|---|---|---|---|
| (e.g., Advisor Financial Account Access) | FinancialAccount | Active FinancialAccountRole | Read/Write |
| | | | |

**FinancialAccountRole assignment logic:** (how roles are created, who assigns them, what triggers deactivation)

---

## 3. Integration Boundary Inventory

| External System | Direction | Pattern | System of Record | Write-Back Gating | Error Strategy | Data Freshness SLA |
|---|---|---|---|---|---|---|
| (e.g., Core Banking) | Inbound | Platform Event / Batch ETL | Core Banking | Approval required | Dead-letter queue + alert | Nightly batch |
| (e.g., Market Data Feed) | Inbound | Batch ETL | Market Data Provider | Not applicable | Email alert on job failure | Daily |
| | | | | | | |

**Synchronous callout review:** Are any integrations designed as synchronous callouts from trigger or page-load contexts?
[ ] No synchronous callouts from FSC record save events — confirmed
[ ] Synchronous callouts identified (list below — each requires redesign to async pattern):
- _______________

---

## 4. Household and Rollup Configuration

**Client grouping model:** [ ] Household Account  [ ] Relationship Group  [ ] Both

**Person Accounts enabled:** [ ] Yes (confirm this is permanent and stakeholder-approved)

**Rollup batch scheduled:** [ ] Yes  [ ] No — must be configured before go-live

**Rollup batch schedule:** (e.g., Nightly at 01:00 UTC)

**Rollup monitoring approach:** (how failures are detected and alerted)

**Data freshness SLA for household KPIs communicated to reporting team:** [ ] Yes  [ ] No

---

## 5. Scalability Assessment

| FSC Object | Projected Records (Year 1) | Projected Records (Year 3) | Key Query Pattern | Query Uses Index | Governor Limit Concern |
|---|---|---|---|---|---|
| FinancialAccount | | | Book-of-business page query | [ ] Yes  [ ] No | |
| FinancialHolding | | | Holding summary per account | [ ] Yes  [ ] No | |
| FinancialGoal | | | Goals per household | [ ] Yes  [ ] No | |

---

## 6. Well-Architected Pillar Review

| Pillar | Status | Notes |
|---|---|---|
| Security | [ ] Pass  [ ] Concern | (CDS OWD confirmed Private? External-user sharing reviewed?) |
| Scalability | [ ] Pass  [ ] Concern | (Volume projections within governor headroom?) |
| Reliability | [ ] Pass  [ ] Concern | (No synchronous callouts from save events?) |
| Operational Excellence | [ ] Pass  [ ] Concern | (Rollup batch monitoring runbook exists?) |

---

## 7. Architecture Checklist

- [ ] Data model confirmed (managed vs. platform-native); decision documented with rationale
- [ ] Compliant Data Sharing enabled if cross-team financial record visibility is required
- [ ] FinancialAccount OWD is Private where CDS is in use
- [ ] No CDS share set grants branch-wide or team-wide access beyond advisor-relationship scope
- [ ] No synchronous callouts from FSC record save or page-load events
- [ ] System of record defined per data domain; write-back to core banking is gated by approval
- [ ] Household rollup batch schedule configured and monitoring runbook written
- [ ] Person Accounts enablement confirmed as permanent with stakeholder sign-off
- [ ] External-user (Experience Cloud) sharing model reviewed independently of CDS
- [ ] Integration boundary inventory complete with direction, pattern, SOR, and error strategy

---

## 8. Deliverables

| Artifact | Status | Owner | Due Date |
|---|---|---|---|
| FSC Architecture Decision Record | [ ] Draft  [ ] Final | | |
| Sharing Model Design Document | [ ] Draft  [ ] Final | | |
| Integration Boundary Inventory | [ ] Draft  [ ] Final | | |
| Scalability Assessment | [ ] Draft  [ ] Final | | |
| Rollup Batch Operational Runbook | [ ] Draft  [ ] Final | | |

---

## Notes and Deviations

(Record any deviations from the standard FSC architecture patterns and the justification for each)
