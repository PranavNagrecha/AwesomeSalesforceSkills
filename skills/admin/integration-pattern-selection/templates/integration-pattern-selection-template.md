# Integration Pattern Selection — Work Template

Use this template to document the integration pattern decision before any implementation begins.

## Scope

**Skill:** `integration-pattern-selection`

**Integration Name:** (fill in)
**Source System:** (fill in)
**Target System:** (fill in)
**Trigger Event:** (what triggers this integration)
**Business Outcome:** (what must happen as a result)

---

## Two-Axis Classification

| Axis | Answer | Notes |
|---|---|---|
| Integration Type | Process / Data / Virtual | |
| Timing | Synchronous / Asynchronous | Response needed before completing source transaction? |

---

## Secondary Constraints

| Constraint | Value | Impact |
|---|---|---|
| Volume per transaction | (records/day) | > 2,000 → Bulk API 2.0 required |
| External system latency SLA | (seconds typical / max) | > 60s → async pattern required |
| Cross-system rollback required | Yes / No | Yes → middleware orchestration required |
| Latency tolerance | Real-time / Near-real-time / Batch | |

---

## Pattern Selection

| Canonical Pattern | Applicable? | Reason |
|---|---|---|
| Remote Process Invocation — Request/Reply | | |
| Remote Process Invocation — Fire-and-Forget | | |
| Batch Data Synchronization | | |
| Remote Call-In | | |
| UI Update Based on Data Changes | | |
| Data Virtualization | | |

**Selected Pattern:** ______
**Rationale:** ______

---

## Selected Pattern Implementation Skill

| Next Skill | Why |
|---|---|
| `integration/event-driven-architecture-patterns` | For Fire-and-Forget or UI Update pattern |
| `integration/salesforce-to-salesforce-integration` | For Salesforce-to-Salesforce Remote Call-In |
| `integration/error-handling-in-integrations` | Design error recovery for the chosen pattern |
| `architect/api-led-connectivity-architecture` | Multi-system governance |

---

## Review Checklist

- [ ] Integration type classified (Process / Data / Virtual)
- [ ] Timing requirement confirmed (Sync / Async)
- [ ] Volume threshold applied (2,000 record threshold checked)
- [ ] Callout timeout risk assessed (120s limit for synchronous)
- [ ] Cross-system rollback requirement checked (middleware needed if yes)
- [ ] Canonical pattern selected with documented rationale
- [ ] Pattern decision record signed off before implementation
