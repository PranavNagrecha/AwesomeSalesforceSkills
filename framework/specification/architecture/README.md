# Architecture map

The numbered `spec/` documents are normative. The files in this directory explain the same architecture as implementable flows and boundaries.

- `000-system-map.md` — product planes and component ownership.
- `010-product-execution-sequence.md` — end-to-end run sequence.
- `020-data-and-control-flow.md` — typed objects crossing component boundaries.
- `030-trust-boundaries.md` — threat-aware authority and data boundaries.
- `040-deployment-topologies.md` — local, team, enterprise, offline, and QA modes.
- `050-framework-kernel.md` — minimum deterministic kernel and what remains model-driven.
- `060-context-lifecycle.md` — context selection, checkpoints, compaction, and second-task isolation.
- `070-evidence-graph.md` — evidence, claims, contradictions, review, and rendering.

If an architecture explanation conflicts with a numbered requirement or schema, the numbered requirement or schema wins.
