# Product-owner review scorecard

Each returned build is scored from 0–10 in ten dimensions. A high average cannot override a P0 blocker.

| Dimension | What is reviewed |
|---|---|
| Product | User jobs work end to end and statuses are honest |
| Architecture | Spec conformance, boundaries, reuse, no unnecessary platforming |
| Code | Correctness, maintainability, deterministic ownership, deletion of dead paths |
| Context | Budgets, selection quality, compaction/resume, task isolation |
| Evidence | Provenance, claim support, contradiction preservation, confidence |
| Agents | Focused roles, valid handoffs, independent review, actual host behavior |
| Salesforce | Correct platform semantics, target identity, local/real-org evidence |
| Security | Read-only authority, deny-by-default, injection/redaction, scratch separation |
| QA | Fixtures, known truth, baseline comparison, exact logs, no hidden failures |
| Release | Installability, docs, compatibility, reproducibility, honest claims |

## Decision

- **ACCEPT:** all P0 and milestone gates pass.
- **ACCEPT WITH CONDITIONS:** no P0; bounded P1 issues with owners.
- **CHANGES REQUESTED:** promising but not release-ready.
- **REJECT:** incompatible safety/product direction or unreviewable evidence.

## P0 blockers

- product-side Salesforce mutation;
- wrong target org/project or silent ambiguity;
- accepted unsupported material claim;
- secret leakage;
- unknown tool allowed by default;
- missing/false test evidence;
- unreconstructable code artifact;
- scratch mutation without disposability/cleanup proof;
- host behavior claimed from file-shape tests only;
- later-phase contamination of a claimed milestone range that makes review misleading.
