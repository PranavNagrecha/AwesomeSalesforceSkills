# Well-Architected — Apex-Defined Types

## Relevant Pillars

- **Reliability** — typed variables catch shape mismatches at edit time
  rather than at runtime.
- **Operational Excellence** — a tight, documented class is easier to
  audit than a sprawling JSON blob parsed ad-hoc in Flow.

## Architectural Tradeoffs

- **Apex-Defined Type vs JSON string:** the class is stricter and
  readable; the string is flexible but loses Flow native binding and
  pushes validation to callers.
- **Shape fidelity vs minimalism:** mirroring the upstream class 1-to-1
  is tempting but forces Flow to know fields it does not need. Model
  only what Flow consumes.
- **Shared vs per-flow types:** shared types reduce duplication but
  couple flows. If two flows diverge on shape, split rather than add
  optional fields.

## Hygiene

- Every Apex-Defined Type used by Flow has a test that JSON-round-trips
  an instance.
- Field rename / removal has a CAB note.
- No `Map<>` exposed to Flow.

## Official Sources Used

- Apex-Defined Types —
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources_variable_apex.htm
- Flow HTTP Callouts —
  https://help.salesforce.com/s/articleView?id=sf.flow_build_invocable_flow_http.htm
