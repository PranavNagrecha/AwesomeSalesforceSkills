# AI Platform Architecture — Work Template

Use this template when working on AI platform architecture decisions for a Salesforce org.

## Scope

**Skill:** `ai-platform-architecture`

**Request summary:** (fill in what the user asked for)

---

## 1. Data Sensitivity Classification

For each planned agent role, record the data it accesses and its sensitivity tier.

| Agent Role | CRM Objects / Fields Accessed | Sensitivity Tier | Notes |
|---|---|---|---|
| (Agent name) | (Objects and fields) | Regulated / Sensitive / Internal / Public | (Any PII/PCI/PHI specifics) |
| | | | |
| | | | |

**Sensitivity tier definitions:**
- **Regulated** — PII (names, emails, SSNs, phone numbers), PCI (credit card numbers, account numbers), PHI (health data). Requires ZDR-guaranteed model.
- **Sensitive** — Internal financial data, proprietary business data, employee records without PII. Requires ZDR-confirmed model.
- **Internal** — Non-regulated org data, internal knowledge articles, operational metrics. BYOLLM may be considered after provider review.
- **Public** — Data that is publicly available or non-confidential. Least restrictive model selection.

---

## 2. Model Tier Selection

Based on sensitivity classification above, record the model tier decision for each agent.

| Agent Role | Sensitivity Tier | Model Tier Selected | Specific Model / Alias | ZDR Basis | Decision Rationale |
|---|---|---|---|---|---|
| (Agent name) | | Salesforce Default / ZDR Partner / BYOLLM | (alias name) | Salesforce contractual / Provider-confirmed / N/A | |
| | | | | | |
| | | | | | |

**ZDR Basis options:**
- **Salesforce contractual** — Salesforce holds the ZDR agreement; applies to all Salesforce Default model routes through the Einstein LLM gateway.
- **Provider-confirmed** — ZDR agreement independently confirmed with external provider (document the provider's data handling policy and contract reference).
- **N/A** — Non-sensitive data; ZDR not required (document the sensitivity basis for this determination).

---

## 3. Trust Layer Constraints Checklist

| Constraint | Status | Notes |
|---|---|---|
| Data masking enabled for applicable features | Confirmed / Not applicable / Not yet configured | |
| Context limit (65,536 tokens with masking) validated against topology | Validated / At risk / Not yet checked | |
| Audit trail enabled with retention period set | Configured / Not yet configured | Retention period: |
| ZDR confirmed for all agents with regulated data | Confirmed / Gap exists | Gap details: |
| BYOLLM agents have compensating audit logging | Confirmed / Not applicable / Gap exists | |

---

## 4. Multi-Agent Topology

**Topology pattern:** Supervisor/Specialist / Single agent / Other: ___

### Supervisor Agent

- **Agent name:**
- **Model assigned:**
- **Scope:** Intent classification and Specialist routing only
- **Topic descriptions:** (list topic names and their descriptions — must be non-overlapping)

| Topic Name | Description (from user's perspective) | Routes to Specialist |
|---|---|---|
| | | |
| | | |

### Specialist Agents

For each Specialist, complete the handoff contract:

**Specialist: ___**
- **Model assigned:**
- **Data scope:**
- **Input contract:** (what the Supervisor must pass to invoke this Specialist)
  ```
  {
    field_1: type — description
    field_2: type — description
  }
  ```
- **Output contract:** (what this Specialist returns to the Supervisor)
  ```
  {
    field_1: type — description
    field_2: type — description
  }
  ```
- **Action set:** (Apex actions, Flow actions, or MuleSoft integrations assigned)

---

## 5. Context Budget Calculation

Calculate worst-case accumulated context for the full conversation chain with masking active.

| Component | Estimated Tokens | Notes |
|---|---|---|
| Supervisor system prompt | | |
| User message history (max turns) | | |
| Specialist A output (worst case) | | |
| Specialist B output (worst case) | | |
| Specialist C output (worst case) | | |
| Supervisor synthesis prompt | | |
| Buffer | | Recommend 10% overhead |
| **Total** | | Must be < 65,536 if masking active |

**Context budget status:** Within limit / At risk (within 10%) / Exceeds limit

If exceeding or at risk, mitigation:
- [ ] Reduce grounding scope per Specialist turn
- [ ] Switch to dynamic grounding with scoped field retrieval
- [ ] Truncate conversation history after N turns
- [ ] Compact Specialist output contracts (structured summary vs. raw record)

---

## 6. Architecture Review Checklist

Work through these before marking the architecture complete:

- [ ] Data sensitivity classification documented for all agent data touchpoints
- [ ] Model tier rationale recorded for each agent role
- [ ] ZDR status independently confirmed for any BYOLLM models used with regulated data
- [ ] Supervisor/Specialist topology defined with explicit handoff contracts
- [ ] Context budget calculated and verified under 65,536 tokens for masking-active scenarios
- [ ] All Specialist topic descriptions reviewed as a set for semantic overlap
- [ ] Trust Layer data masking confirmed active for applicable features
- [ ] Audit trail enabled with retention period set before agents go live
- [ ] BYOLLM agents have compensating audit logging (if applicable)
- [ ] Each agent role uses a dedicated model alias (not shared)
- [ ] End-to-end topology tests run with realistic data including PII-format test data
- [ ] Architecture decision record created

---

## 7. Architecture Decision Record

**Decision:** (What was the key architectural decision made?)

**Context:** (What was the situation requiring this decision?)

**Options considered:**
1. (Option A — description)
2. (Option B — description)

**Decision made:** (Which option and why)

**Consequences:** (What does this decision constrain or enable going forward?)

**Compliance artifacts:** (What compliance documentation does this decision require?)

---

## Notes and Deviations

(Record any deviations from the standard patterns documented in SKILL.md and why.)
