# Data Cloud Identity Resolution — Configuration Design Template

Use this template when designing, documenting, or reviewing a Data Cloud identity resolution ruleset configuration. Fill in every section before creating any rulesets in the org.

---

## Org Context

**Data Cloud Org ID:** _______________

**Existing rulesets (MUST audit before proceeding):**

| Ruleset Name | Ruleset ID | Created By | Purpose | Status |
|---|---|---|---|---|
| [e.g., Starter Data Bundle Ruleset] | [e.g., STRT] | [Auto-created] | [Starter bundle] | [Active] |
| | | | | |

**Slots consumed:** ___ / 2

**Remaining slots available:** ___

> If 0 slots remain, stop here and escalate before proceeding.

---

## Business Requirement

**What business problem does this ruleset solve?**

[Describe the identity resolution use case: e.g., "Unify CRM Contacts with commerce platform customers to enable single-view segmentation and activation across channels."]

**Downstream consumers of Unified Individual profiles:**

- [ ] Segmentation (segments referencing Unified Individual attributes)
- [ ] Activation targets (connected advertising or engagement platforms)
- [ ] Agentforce grounding (AI agent reads Unified Individual for context)
- [ ] Data actions (triggered from segments or events)
- [ ] CRM Analytics / Tableau (reporting on unified profiles)
- [ ] Other: _______________

**Real-time resolution required?**

- [ ] Yes — downstream use case requires resolution within minutes of ingestion event
- [ ] No — nightly or scheduled batch resolution is acceptable

> If "Yes", all match rules MUST use Exact or Exact Normalized type only. Fuzzy and full address Normalized are batch-only.

---

## Ruleset Design

### Ruleset Metadata

**Ruleset Name:** _______________

**Ruleset ID (4-character, PERMANENT, cannot be changed after creation):**

Proposed ID: `____` 

Naming rationale: [Explain why this 4-character ID was chosen. E.g., `EMLP` = Email Primary.]

**Data Space:** _______________

**Run Schedule:** [e.g., Daily at 02:00 UTC]

---

### Source Data Streams Contributing to This Ruleset

| Source System | Data Stream Name | Individual DMO Fields Mapped | Contact Point DMOs Mapped |
|---|---|---|---|
| [e.g., Salesforce CRM] | [e.g., CRM_Contacts] | [Individual Id, First Name, Last Name] | [Contact Point Email: Email Address] |
| [e.g., Commerce Platform] | [e.g., Commerce_Customers] | [Individual Id, First Name, Last Name] | [Contact Point Email: Email Address, Contact Point Phone: Phone Number] |
| | | | |

---

### Match Rules

List all match rules in evaluation order. Rules are combined with OR logic — any single rule firing creates a merge.

| Rule # | Type | DMO | Field | Notes |
|---|---|---|---|---|
| 1 | [Exact / Fuzzy / Normalized / Compound] | [e.g., Contact Point Email] | [e.g., Email Address] | [e.g., handles mixed-case email] |
| 2 | | | | |
| 3 | | | | |

**For each Compound rule, list its component fields:**

Compound Rule # ___ components:

| Component Field # | DMO | Field | Match Type |
|---|---|---|---|
| 1 | [e.g., Individual] | [e.g., First Name] | [Exact / Fuzzy] |
| 2 | [e.g., Individual] | [e.g., Last Name] | [Exact] |
| 3 | [e.g., Contact Point Address] | [e.g., Postal Code] | [Exact] |

**Real-time safety check:**

- [ ] All match rules are Exact or Exact Normalized (real-time safe)
- [ ] Ruleset contains Fuzzy or full Address Normalized rules (batch-only — document and accept)

---

### Reconciliation Rules

For each Unified Individual attribute that will be populated, define the reconciliation strategy.

| Attribute | Reconciliation Type | Source Priority Ranking (if applicable) | Rationale |
|---|---|---|---|
| First Name | [Most Recent / Source Priority / Most Frequent] | [1. CRM, 2. Commerce] | [CRM has legal name] |
| Last Name | | | |
| Email Address | | | |
| Phone Number | | | |
| Mailing Street | | | |
| Mailing City | | | |
| Mailing State | | | |
| Mailing Postal Code | | | |
| [Custom attribute] | | | |

> Note: Changing any reconciliation rule after the ruleset has run triggers a full cluster re-run, not incremental update.

---

## Risk Acknowledgements

Before creating the ruleset, confirm all of the following:

- [ ] Ruleset ID `____` has been chosen as if permanent (it is)
- [ ] Org slot consumption confirmed: this creation will leave ___ / 2 slots used
- [ ] Real-time match rule safety confirmed (see above)
- [ ] Reconciliation rule changes will require a full re-run — first-time configuration is correct
- [ ] Maximum 4 manual runs per ruleset per 24-hour window — testing plan stays within this limit
- [ ] All source data streams have Individual DMO and at least one Contact Point DMO field mapped

---

## Post-Run Validation

Complete this section after the first ruleset run.

**Run completion date/time:** _______________

**Pre-resolution Individual count:** _______________

**Post-resolution Unified Individual count:** _______________

**Expected merge rate:** _______________% (estimate from business knowledge)

**Actual merge rate:** _______________% (Unified Individuals / pre-resolution Individuals)

**Cluster quality spot check (sample 50 clusters):**

| Cluster ID (sample) | Source Records Count | All Same Real Person? | Notes |
|---|---|---|---|
| | | [Yes / No / Uncertain] | |
| | | | |

**False positive rate (estimated from spot check):** ____%

**False negative count (known duplicates NOT merged):** ____

**Action taken if false positive rate > 5%:** [e.g., added Compound rule to tighten match criteria]

---

## Architecture Decision Record Entry

Complete and file this in the org's architecture decision log after the ruleset is created.

**Decision date:** _______________

**Decision owner:** _______________

**Ruleset ID:** `____`

**Slot consumption after this decision:** ___ / 2

**Match rule rationale summary:** [1–2 sentences]

**Reconciliation rule rationale summary:** [1–2 sentences]

**Known constraints accepted:**
- [ ] Fuzzy rules are batch-only
- [ ] Reconciliation rule changes require full re-run
- [ ] No additional rulesets can be created if both slots are now consumed

**Related skills referenced:** `admin/data-cloud-identity-resolution`, `data/data-cloud-data-streams`
