# Milestone scorecard

Scores support judgment; blockers override averages.

| Dimension | Weight | 10 means |
|---|---:|---|
| Product outcome | 15 | User job is completed end-to-end and materially useful |
| Architecture | 10 | Contracts and ownership are coherent, minimal, and implemented |
| Code quality | 10 | Clear, tested, maintainable, deterministic where required |
| Context | 10 | Relevant, bounded, measured, compaction/second-task resilient |
| Evidence | 15 | Material claims resolve to correct provenance; contradictions preserved |
| Safety | 15 | Deny-by-default, correct target, no mutation/secrets/bypasses |
| QA truth | 10 | Appropriate fixture/host/live/scratch lanes actually ran |
| UX/install | 5 | First value is simple and errors are actionable |
| Regression | 5 | Existing paths remain valid or migration is explicit |
| Review integrity | 5 | Exact code/tests/runs are reconstructable and truthful |

## Severity

### P0 — merge/release blocker

- prohibited product mutation;
- credential/customer data exposure;
- wrong org/project/job selection;
- material unsupported claim accepted in release scenario;
- missing or fabricated review evidence;
- required tests failed;
- scratch QA targets a non-disposable org or lacks cleanup proof;
- security-critical hook/broker fails open contrary to claim.

### P1 — milestone blocker

- product path not proven in actual shipped host;
- command/subagent/MCP wiring fails;
- context hard limit or transcript handoff violation;
- independent reviewer is not actually invoked;
- fixture/replay path fails;
- target/status/truncation semantics wrong;
- generated plugin/install path invalid;
- required scenario recall below milestone threshold.

### P2 — follow-up before broader qualification

- weak UX, latency, docs, or context selection;
- limited optional enrichment;
- noncritical host parity gap;
- missing optional scenario or comparison;
- maintainability debt with a bounded correction.

### P3 — backlog

Polish or expansion that does not affect the current product promise, safety, evidence truth, or release gate.
