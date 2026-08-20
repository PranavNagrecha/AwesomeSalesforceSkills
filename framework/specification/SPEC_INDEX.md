# Specification index

## Normative reading order

| Order | Document | Purpose |
|---:|---|---|
| 1 | `spec/000-status-and-conformance.md` | Authority, conformance profiles, change control |
| 2 | `spec/010-vision-and-scope.md` | User promise and product boundaries |
| 3 | `spec/020-design-principles.md` | Binding design constitution |
| 4 | `spec/030-product-model.md` | What counts as a product |
| 5 | `spec/040-reference-architecture.md` | Planes, components, trust boundaries |
| 6 | `spec/050-runtime-and-state-machine.md` | Execution lifecycle and status semantics |
| 7 | `spec/060-knowledge-plane.md` | Skill discovery, selection, provenance, freshness |
| 8 | `spec/070-agent-and-delegation-model.md` | Agent taxonomy and structured delegation |
| 9 | `spec/080-context-engine.md` | Budgets, selection, compaction, rehydration |
| 10 | `spec/090-evidence-and-claim-model.md` | Evidence graph and confidence |
| 11 | `spec/100-tool-and-mcp-broker.md` | Tool mediation and upstream integration |
| 12 | `spec/110-security-and-authority.md` | Permissions, identity, injection, authority separation |
| 13 | `spec/120-output-and-user-experience.md` | Result anatomy and honest states |
| 14 | `spec/130-observability-and-replay.md` | Run bundles, telemetry, privacy |
| 15 | `spec/140-quality-and-evaluation.md` | Deterministic and behavioral quality gates |
| 16 | `spec/150-real-org-qa.md` | Persistent org and disposable scratch-org QA |
| 17 | `spec/160-host-adapters-and-portability.md` | Cursor, Claude, Copilot, Vibes, open protocols |
| 18 | `spec/170-knowledge-freshness.md` | Release-sensitive source governance |
| 19 | `spec/180-data-privacy-and-retention.md` | Data classes and retention |
| 20 | `spec/190-release-and-conformance.md` | Versioning and release gates |
| 21 | `spec/200-governance-and-contribution.md` | Ownership, ADRs, contribution quality |
| 22 | `spec/210-commercial-and-ecosystem-strategy.md` | Packaging and sustainable product options |
| 23 | `spec/220-roadmap-and-exit-criteria.md` | Milestones and measurable exit conditions |

## Normative versus informative

The numbered `spec/` documents and JSON Schemas are normative. Product, agent, command, MCP, policy, and QA files are normative for their specific artifact unless marked `example` or `research`. The `research/` directory is informative and records the evidence behind product decisions.

## Requirement language

`MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` have their ordinary standards meaning. Each testable normative statement has a stable requirement ID.

## Traceability

`implementation/requirements.csv` is generated from the specification. Cursor must map every applicable requirement to implementation files, tests, and review evidence. A requirement is not complete because a file with a similar name exists.

## Product and implementation maps

| Directory / file | Role |
|---|---|
| `architecture/` | Informative diagrams and implementation-oriented views of the normative architecture |
| `products/definitions/` | Canonical machine-readable product contracts |
| `products/P*.md` | Complete human product specifications |
| `agents/definitions/` | Canonical V2 agent contracts |
| `agents/core/`, `agents/product/` | Human agent contracts and prompting philosophy |
| `commands/specs/` | Typed command API contracts |
| `mcp/tool-specs/` | Typed, read-only normalized evidence-tool contracts |
| `context/context-packs/` | Product-specific context-selection policies |
| `security/` | Authority, shell/MCP policy, threat model, and sensitive-data rules |
| `qa/scenarios/` | Known-truth finding/evidence labels, not prose snapshots |
| `adapters/` | Host capability and packaging requirements |
| `reference-kernel/` | Tested behavioral oracle for deterministic core controls |
| `reference-components/` | Integrable implementations of high-risk focused components |
| `migration/catalogs/` | Complete uploaded-baseline inventory and V2 dispositions |
| `strategy/`, `adoption/` | Market category, wedge, distribution, packaging, and product metrics |
| `review/` | Product-owner scorecard, defect taxonomy, and iteration protocol |
| `implementation/CURSOR_BUILD_SFSAEF_V2.md` | The one master Cursor implementation prompt |
| `implementation/REVIEW_RETURN_CONTRACT.md` | Exact implementation evidence required back from Cursor |

## Generated catalogs

`catalogs/` is generated from canonical definitions and includes product, agent, command, evidence-tool, context, scenario, source, and requirement references. Generated catalogs are for navigation and review; they are not independently editable contracts.

## Conformance evidence

A claim of framework conformance requires all of the following:

1. requirement traceability to code, tests, and review evidence;
2. schema-valid canonical artifacts and generated-adapter drift checks;
3. product-specific deterministic and behavioral qualification;
4. actual host capability evidence for host-dependent behavior;
5. explicit Salesforce target identity and product-read-only authority;
6. replayable, redacted run artifacts or a declared reason replay is impossible;
7. a reconstructable Cursor return ZIP matching the supplied contract.

Run `python3 -B scripts/run_all_checks.py` to validate the specification package itself. This validates design integrity, not implementation completeness.

