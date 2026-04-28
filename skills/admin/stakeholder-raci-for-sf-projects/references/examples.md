# Examples — Stakeholder RACI for Salesforce Projects

Three worked RACI matrices spanning the most common Salesforce project shapes. Each example uses the canonical decision categories (data model, automation tier, security, integration, deployment, license/edition) as rows and the canonical stakeholder roster as columns. Cells use R / A / C / I.

Roster legend (column headers below):

- **BSP** — Business sponsor
- **PO** — Process owner
- **DS** — Data steward
- **SA** — Security architect
- **IA** — Integration architect
- **AL** — CRM admin lead
- **RM** — Release manager
- **AX** — AppExchange owner
- **CO** — Compliance officer
- **EU** — End-user representative

---

## Example 1: Greenfield Sales Cloud Implementation

**Context:** A 600-seat industrial-distribution company is rolling out Sales Cloud for the first time. Single org, no prior Salesforce footprint, one inbound integration from an ERP for Account/Product master, no managed packages beyond standard CPQ which is deferred to phase 2.

**Problem without this skill:** The CRO is set up as A on every row in the SI's default RACI deck. By week 4 the CRO is the bottleneck on every field decision and the project slips. The integration team works around the CRO by inventing custom external IDs without the data steward's input — the second integration in phase 2 cannot reuse them.

**Solution: filled RACI**

| Decision category | BSP | PO | DS | SA | IA | AL | RM | AX | CO | EU |
|---|---|---|---|---|---|---|---|---|---|---|
| Data model change | I | A | C | C | C | R | I | — | I | C |
| Automation tier | I | C | I | I | C | A | C | — | I | C |
| Security model | I | C | C | A | C | R | I | — | C | I |
| Integration boundary (ERP feed) | I | C | C | C | A | R | C | — | I | I |
| Deployment | I | I | I | I | I | C | A | — | I | I |
| License + edition | A | C | I | C | I | C | I | — | I | I |

**Escalation rules (excerpt):**

- *Data model change (A = PO):* Escalates to BSP if the change breaks the published As-Is/To-Be process or if PO and DS disagree, time-box 5 business days.
- *Automation tier (A = AL):* Escalates to IA if the answer per `automation-selection.md` is Apex or Platform Events, time-box 3 business days.
- *Security model (A = SA):* Escalates to BSP if the requested security model would block a documented business process, time-box 3 business days.
- *Integration boundary (A = IA):* Escalates to BSP if the chosen pattern requires a license tier upgrade or new MuleSoft entitlement, time-box 5 business days.
- *Deployment (A = RM):* Escalates to BSP if a change request bypasses the sandbox path, time-box 1 business day.
- *License + edition (A = BSP):* Escalates to steerco for any tier change, time-box 10 business days.

**Why it works:** Sponsor's A is constrained to scope/budget/license — where they actually have authority. Process owner holds A on data model because they own the business semantics. Admin lead holds A on day-to-day automation but escalates to the integration architect when the decision tree points at code. Each A has a time-boxed escalation, so blocks surface within a sprint.

---

## Example 2: Regulated Industry — Health Cloud / HIPAA

**Context:** A regional health system implementing Health Cloud with PHI in custom objects, an inbound HL7 feed via MuleSoft, and a Health Cloud-licensed call center. PHI access is auditable; retention is 7 years; the compliance officer is the named HIPAA Privacy Officer.

**Problem without this skill:** The SI defaults to compliance as C on every row "to keep them in the loop." During UAT the privacy officer flags four PHI exposures (two in reports, one in a list view, one in a data export pattern). Remediation costs three sprints and delays go-live.

**Solution: filled RACI** (compliance promoted to A on regulatory-control rows; data model and security split into PHI vs. non-PHI sub-rows)

| Decision category | BSP | PO | DS | SA | IA | AL | RM | AX | CO | EU |
|---|---|---|---|---|---|---|---|---|---|---|
| Data model — non-PHI | I | A | C | C | C | R | I | — | I | C |
| Data model — PHI objects/fields | I | C | C | C | I | R | I | — | A | C |
| Automation tier | I | C | I | C | C | A | C | — | C | C |
| Security model — non-PHI | I | C | C | A | C | R | I | — | C | I |
| Security model — PHI access (FLS, sharing, profiles) | I | C | C | C | I | R | I | — | A | I |
| Integration boundary (HL7 feed) | I | C | C | C | A | R | C | — | C | I |
| Deployment | I | I | I | I | I | C | A | — | C | I |
| License + edition | A | C | I | C | I | C | I | — | C | I |
| Audit trail / retention | I | C | C | C | I | C | I | — | A | I |
| BAA + data subject rights | A | C | C | C | C | I | I | — | C | I |

**Escalation rules (excerpt):**

- *PHI data model (A = CO):* Escalates to BSP if a clinical workflow is blocked by a privacy control, time-box 5 business days; CO has veto on PHI exposure regardless of business pressure.
- *PHI security model (A = CO):* Same as above; SA implements but CO decides.
- *Audit trail / retention (A = CO):* No escalation — this is regulatory, not negotiable. CO decision is final.
- *BAA (A = BSP):* Legal and procurement are C; vendor cannot start work without BAA executed.

**Why it works:** The compliance officer holds A on rows that audit will care about. Security architect still implements, but does not decide on PHI. The regulatory-control rows are explicitly separated from non-regulated rows so the matrix doesn't become "compliance approves everything," which would cause its own bottleneck.

---

## Example 3: M&A Multi-Org Integration

**Context:** Acquirer ("Org A") and target ("Org B") each have a mature Salesforce org. Decision needed: federate (keep both orgs, sync via Pub/Sub), consolidate (migrate Org B into Org A), or coexist (separate orgs indefinitely with light reporting bridge). Both have CPQ; Org A also has FSL; Org B has Marketing Cloud Account Engagement.

**Problem without this skill:** Naming a single sponsor (the acquirer's CRO) too early causes Org B's stakeholders to disengage from steerco. Org B's data steward stops attending working sessions. Three months in, Org B's CRM admin lead leaves; nobody is left who knows why Org B's custom objects exist.

**Solution: filled RACI** (split A on day-to-day decisions per legacy org; steerco-as-A pattern on org-strategy)

| Decision category | BSP-A | BSP-B | Steerco | PO-A | PO-B | DS (master) | SA | IA | AL-A | AL-B | RM | AX-A | AX-B | CO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Org strategy (federate / consolidate / coexist) | C | C | A | I | I | C | C | C | I | I | I | I | I | C |
| Data model — Org A | I | I | I | A | I | C | C | C | R | I | I | C | I | I |
| Data model — Org B | I | I | I | I | A | C | C | C | I | R | I | I | C | I |
| Master data model (post-merge) | I | I | C | C | C | A | C | C | C | C | I | C | C | C |
| Automation tier — Org A | I | I | I | C | I | I | I | C | A | I | C | I | I | I |
| Automation tier — Org B | I | I | I | I | C | I | I | C | I | A | C | I | I | I |
| Security model — Org A | I | I | I | C | I | C | A | C | R | I | I | I | I | C |
| Security model — Org B | I | I | I | I | C | C | A | C | I | R | I | I | I | C |
| Cross-org integration (Pub/Sub topology) | I | I | C | C | C | C | C | A | C | C | C | I | I | C |
| Deployment | I | I | I | I | I | I | I | I | C | C | A | I | I | I |
| License + edition | C | C | A | C | C | I | C | I | C | C | I | C | C | I |
| Managed-package strategy (CPQ consolidation) | C | C | C | C | C | C | C | C | C | C | I | A | A | I |

(Joint A on the bottom row is intentional — both AppExchange owners must agree before a single CPQ instance ships; if they cannot agree, the row escalates to steerco.)

**Escalation rules (excerpt):**

- *Org strategy (A = Steerco):* Single decision, time-box 30 days post deal-close; if no quorum, BSP-A and BSP-B negotiate directly with CIO arbitration.
- *Master data model (A = DS-master):* Escalates to steerco if a master rule breaks a legal-entity reporting requirement, time-box 5 business days.
- *Cross-org integration (A = IA):* Escalates to steerco if the chosen pattern requires per-message PII, time-box 5 business days.
- *Managed-package strategy (joint A = AX-A and AX-B):* If joint A cannot agree within 10 business days, escalates to steerco with both vendors' input gathered.

**Why it works:** The split-A pattern reflects the actual organizational state — both companies still exist as legal entities until merger close. The "DS-master" role is created explicitly to hold A on the post-merger model, which is a known gap in most M&A RACIs. Steerco-as-A on org strategy gives both sponsors a vote without making either subordinate.

---

## Anti-Pattern: The "Sponsor as Universal A"

**What practitioners do:** Hand the sponsor a RACI where they hold A on every row, on the theory that "the sponsor is accountable for the project."

**What goes wrong:** Sponsors do not have time to decide on field-level changes. By week 4 the project has a single bottleneck and an A who is not informed enough to decide. The CRM admin lead starts deciding without authority; the project ships with decisions nobody can defend in audit.

**Correct approach:** Sponsor's A is scope, budget, license tier, and go/no-go. Operational A flows down to the role with the proximate domain expertise — process owner for data model, security architect for security, integration architect for integration boundary, admin lead for day-to-day automation. The sponsor is I (informed) on the operational rows.
