# Worked Examples

## 1. Flow, Apex, or no new automation

**Question:** How should a high-volume Case enrichment step run after insert?

Do not start by scoring Flow and Apex. Apply `standards/decision-trees/automation-selection.md`, inspect existing Case automation, and gate both choices against volume, transaction boundary, callout, retry, and ownership requirements. A third option—extend an existing orchestration—may be safer than either new artifact.

A useful recommendation is conditional:

- choose before-save Flow only if the operation remains same-record, synchronous, and inside the measured volume headroom;
- choose Queueable Apex when external enrichment, retry, idempotency, or transaction separation is load-bearing;
- choose no new automation when an existing integration already owns the enrichment and duplication would create split ownership.

The analysis packet remains mutable. Once the team accepts the branch and premises, create a separate ADR.

## 2. Buy, build, or sequence a package replacement

Hard gates include contract exit terms, data exportability, required certifications, namespace conflicts, and a supported migration path. A cheap build score cannot offset a failed data-residency gate.

When uncertainty is high, the correct option may be a six-week pilot with explicit exit criteria. Score the pilot as its own option; do not bury it as a footnote to the preferred architecture.

## 3. A decision that should route elsewhere

"Should this object use private or public-read-only OWD?" is a narrow sharing-model choice. Use `standards/decision-trees/sharing-selection.md` and the sharing specialist skills. Use this generic decision skill only when the choice includes broader alternatives—such as an org split, external data store, or product boundary—that the tree does not cover.

## 4. A decision with no winner

Two integration options remain within 3% under the declared weights, and the ranking flips when expected event volume changes by 20%. Return `experiment`, define a representative load test and failure-injection scenario, and defer the permanent choice. Do not round one option up and call it decisive.

## 5. Minimal machine-readable gate artifact

A review tool can consume a compact gate record while the narrative packet retains the rationale:

```json
{
  "decision_id": "case-enrichment-2026-09",
  "target_context": {"org": "uat", "release": "Summer '26"},
  "options": [
    {"id": "reuse-existing", "gates": {"platform": "PASS", "security": "PASS", "rollback": "PASS"}},
    {"id": "new-queueable", "gates": {"platform": "PASS", "security": "UNKNOWN", "rollback": "PASS"}}
  ],
  "status": "experiment",
  "reversal_condition": "Existing orchestration cannot meet the measured 60-second SLA"
}
```

The JSON does not replace evidence IDs, sensitivity, or human approval. It makes the gate state testable.
