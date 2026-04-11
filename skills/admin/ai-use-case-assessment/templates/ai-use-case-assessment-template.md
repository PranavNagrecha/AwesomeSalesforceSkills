# AI Use Case Assessment — Output Template

Use this template to record the outputs of an AI use case assessment engagement. Fill every section. Leave no placeholder text in a final deliverable.

---

## Assessment Metadata

| Field | Value |
|---|---|
| Organization | |
| Salesforce Edition | |
| Assessment Date | |
| Assessor | |
| Stakeholders Present | |
| Candidate Use Cases Evaluated | |

---

## License Inventory

Record the org's current licenses before scoring technical feasibility for any use case.

| License / Add-On | Present? (Y/N) | Notes |
|---|---|---|
| Sales Cloud | | |
| Service Cloud | | |
| Einstein for Sales add-on | | Covers Lead Scoring, Opportunity Scoring |
| Einstein for Service add-on | | Covers Work Summaries, Service Replies, Case Classification |
| Agentforce platform license | | Required for all Agentforce agents |
| Data Cloud | | Required for grounding use cases |
| CRM Analytics / Tableau CRM | | |
| Other (specify) | | |

---

## Step 1: Candidate Use Case List

List all use cases brainstormed. Decompose any strategic-level use cases into feature-level definitions before scoring.

| # | Use Case Name | Feature-Level Definition (what specific Salesforce capability) | Business Process Affected |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |

---

## Step 2: Impact-Effort Matrix

Score each use case. Impact: 1 = low business value, 2 = moderate, 3 = high. Effort: 1 = low complexity/low data requirements, 2 = moderate, 3 = high complexity or significant data prerequisites.

| # | Use Case | Impact (1-3) | Effort (1-3) | Quadrant | Impact Justification | Effort Justification |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |

**Quadrant key:**
- Quick Win: Impact 2-3, Effort 1-2
- Big Bet: Impact 2-3, Effort 2-3
- Low-Hanging Fruit: Impact 1, Effort 1
- Money Pit: Impact 1, Effort 2-3

---

## Step 3: Feasibility Scorecard

Complete for all Quick Wins and Big Bets only. Use a 1-3 scale per dimension (1 = not feasible / not ready, 2 = conditional, 3 = fully feasible / ready).

### Use Case: [Name — copy one block per use case]

**Technical Feasibility**
- Required license confirmed: Y / N
- Required add-on license confirmed: Y / N
- Feature GA (not beta): Y / N
- Integration dependencies met: Y / N
- Technical Feasibility Score (1-3): ___
- Notes:

**Operational Feasibility**
- Business process supports AI output integration: Y / N
- Human-in-the-loop review step identified: Y / N
- Team capacity to manage/monitor ongoing: Y / N
- Operational Feasibility Score (1-3): ___
- Notes:

**Data Readiness**

| Sub-Dimension | Score (1-3) | Evidence |
|---|---|---|
| Availability — data exists in org in sufficient volume | | |
| Quality — data is clean, consistent, deduplicated | | |
| Unification — data is unified across sources (Data Cloud if applicable) | | |
| Governance — data access is controlled, compliant, auditable | | |
| **Composite Data Readiness Score (sum)** | **/12** | |

Gate: Composite score < 6 = Data Blocked. Composite 6-8 = Conditional. Composite 9-12 = Ready.

**Data Readiness Status:** Ready / Conditional / Data Blocked

**Risk Profile**
- Consequence of incorrect AI output (low / medium / high):
- Regulatory or compliance exposure (Y / N; specify):
- Human oversight required for autonomous decisions (Y / N):
- Risk Profile Score (1-3 where 3 = highest risk, requires mitigation): ___
- Mitigation required:

**Overall Feasibility Verdict:** Go / Conditional Go / Blocked

---

## Step 4: Prioritized Shortlist

List approved and conditional use cases in priority order. Exclude blocked use cases.

| Priority | Use Case | Quadrant | Feasibility Verdict | Rationale | Recommended Next Skill |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

---

## Step 5: Blocked Use Cases and Remediation Requirements

| Use Case | Blocking Dimension | Blocking Score | Minimum Remediation Required | Re-Assessment Target Date |
|---|---|---|---|---|
| | | | | |

---

## Step 6: ROI Narrative

Complete for top 3-5 approved use cases only. Do not produce specific dollar amounts — document the value driver, key assumption, and payback category.

### Use Case: [Name]

- **Primary value driver:** (cost reduction / revenue increase / risk mitigation / productivity)
- **Specific mechanism:** (e.g., reduced average handle time via automated case summaries)
- **Key assumption that must hold:** (e.g., agents will adopt the feature and reduce manual summarization time)
- **Reference benchmark if available:** (e.g., Salesforce benchmark: 20-30% AHT reduction in similar orgs)
- **Payback period category:** < 6 months / 6-18 months / 18+ months
- **Risk to ROI realization:**

---

## Assessment Sign-Off

| Role | Name | Date | Signature |
|---|---|---|---|
| Business Sponsor | | | |
| IT/Salesforce Lead | | | |
| Compliance / Data Governance | | | |

---

## Handoff Notes

Record which implementation workstreams or skills each approved use case routes to next.

| Use Case | Routes To | Handoff Notes |
|---|---|---|
| | | |
