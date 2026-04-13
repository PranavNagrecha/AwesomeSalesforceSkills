# CRM Analytics vs Tableau — Decision Record Template

Use this template when a formal platform decision is needed between CRM Analytics and Tableau.
Fill in all sections. This artifact is suitable for architecture review board or design authority submission.

---

## Request Summary

**Date:** (YYYY-MM-DD)

**Requestor:** (name or team)

**Business question being answered:** (What analytics capability is being built or evaluated?)

---

## Data Topology

**Primary data sources:**
- [ ] Salesforce objects only
- [ ] Salesforce objects + external data warehouse (specify: _______________)
- [ ] Salesforce objects + ERP (specify: _______________)
- [ ] Salesforce objects + other (specify: _______________)
- [ ] Non-Salesforce sources only

**Data source details:** (List the specific Salesforce objects or external systems involved)

---

## Freshness Requirement

**Required data freshness:**
- [ ] Real-time / sub-minute (current Salesforce record state)
- [ ] Near-real-time (minutes to hours)
- [ ] Daily batch
- [ ] Weekly or ad-hoc

**Notes on freshness:** (Any SLA commitments, stakeholder expectations, or downstream dependencies)

**Tableau Salesforce connector constraint check:**
If Tableau is being evaluated and near-real-time Salesforce data is required, document the constraint here:
- [ ] Confirmed: Tableau Salesforce connector is extract-only (no live query). Freshness requirement is met by scheduled extract cadence.
- [ ] Confirmed: Near-real-time requirement disqualifies Tableau's Salesforce connector. CRM Analytics required.
- [ ] N/A: Data source is not Salesforce, or data is routed through a warehouse before Tableau.

---

## Audience

**Primary analytics consumers:**
- [ ] Salesforce-licensed users working inside Lightning pages
- [ ] Salesforce-licensed users but primarily outside Lightning
- [ ] Data analysts and BI teams without Salesforce licenses
- [ ] Mixed audience (describe: _______________)
- [ ] External stakeholders (customers, partners)

**User count estimate:** (number of users by role)

---

## Security Requirements

**Row-level security model:**
- [ ] Must enforce Salesforce OWD and sharing rules (account team, territory, custom sharing)
- [ ] Custom row-level security acceptable (not tied to Salesforce sharing model)
- [ ] No row-level security required

**Sharing model enforcement check:**
If Salesforce sharing model enforcement is required, document how this will be implemented:
- CRM Analytics: dataset row-level security predicates (native enforcement)
- Tableau: custom RLS implementation (requires separate maintenance, sync risk)

**Notes:** (Any regulated data, compliance requirements, or audit considerations)

---

## License Inventory

**Existing Salesforce licenses:**

| License Type | Count | Relevant |
|---|---|---|
| Salesforce (standard user) | | |
| CRM Analytics Growth PSL | | |
| CRM Analytics Plus PSL | | |
| Einstein 1 (includes CRM Analytics) | | |

**Existing Tableau licenses:**

| License Type | Count |
|---|---|
| Tableau Creator | |
| Tableau Explorer | |
| Tableau Viewer | |
| Tableau+ (Tableau Next) | |
| Tableau Server (on-prem seats) | |

**License gap:** (Number of users needing access vs available licenses for each platform)

---

## Tableau Connector Constraint Assessment

Complete this section if Tableau is being evaluated for any Salesforce data use case.

| Constraint | Status | Impact |
|---|---|---|
| Extract-only (no live Salesforce query) | Acceptable / Disqualifying | |
| 30-day incremental refresh lookback cap | Acceptable / Disqualifying | |
| No Custom SQL in Salesforce connector | Acceptable / Workaround needed | |
| 10,000-character API query string limit | Acceptable / Workaround needed | |

**Workarounds required:** (Describe any Tableau Prep, warehouse routing, or Salesforce Reports workarounds needed)

---

## Platform Recommendation

**Recommended platform:**
- [ ] CRM Analytics
- [ ] Tableau (Desktop / Server / Cloud)
- [ ] Tableau Next (Tableau+)
- [ ] Hybrid (CRM Analytics for Salesforce-native BI + Tableau for cross-system BI)

**Primary rationale:** (2–4 sentences explaining the key factors that drove the recommendation)

**Factors favoring recommended platform:**
1.
2.
3.

**Factors considered but outweighed:**
1.
2.

---

## Agentforce / Data 360 Roadmap Check

**Does the organization have an Agentforce or Data 360 strategic roadmap?**
- [ ] Yes — Tableau Next (Tableau+) should be included in the platform evaluation as the GA Agentforce-integrated BI forward path (available June 2025)
- [ ] No — standard CRM Analytics or Tableau evaluation applies
- [ ] Unknown — confirm with stakeholders before finalizing recommendation

---

## Decision Record

**Final decision:** (CRM Analytics / Tableau / Hybrid — one line)

**Decision owner:** (name)

**Review date:** (when this decision should be revisited)

**Open items or conditions:** (any assumptions that, if changed, would change this recommendation)

---

## Checklist

- [ ] Data topology confirmed (Salesforce-only vs multi-source)
- [ ] Freshness requirement assessed against Tableau connector extract-only constraint
- [ ] 30-day incremental refresh lookback cap documented if Tableau is chosen for Salesforce data
- [ ] Row-level security model documented and platform capability confirmed
- [ ] License inventory confirmed for both platforms
- [ ] Existing Tableau investment assessed before recommending CRM Analytics for cross-system use
- [ ] Agentforce / Data 360 roadmap checked for Tableau Next relevance
- [ ] "Tableau CRM" terminology clarified if used anywhere in this document (deprecated name for CRM Analytics)
- [ ] Decision record signed off by architecture review stakeholder
