# Normative requirement catalog

Generated from numbered specifications. Implementation status belongs in the repository traceability working copy, not this immutable source catalog.

| Requirement | Level | Source | Line | Statement |
|---|---|---|---|---|
| SFAEF-000-001 | MUST | spec/000-status-and-conformance.md | 9 | The numbered specification under `spec/` MUST be the normative product source of truth. |
| SFAEF-000-002 | MUST | spec/000-status-and-conformance.md | 11 | JSON Schemas under `schemas/` MUST be the normative machine contract for the object they describe. |
| SFAEF-000-003 | MUST NOT | spec/000-status-and-conformance.md | 13 | Product, agent, command, and MCP files MAY add detail but MUST NOT contradict the numbered specification or schemas. |
| SFAEF-000-004 | MUST NOT | spec/000-status-and-conformance.md | 15 | Generated catalogs and host packages MUST be derived artifacts. They MUST NOT become independently hand-maintained sources of truth. |
| SFAEF-000-005 | NORMATIVE | spec/000-status-and-conformance.md | 17 | Existing SfSkills skill packages remain the canonical Salesforce knowledge units until individually superseded through the repository’s existing source-governance process. |
| SFAEF-000-010 | NORMATIVE | spec/000-status-and-conformance.md | 21 | Each normative requirement has a stable ID in the form `SFAEF-<document>-<number>`. |
| SFAEF-000-011 | MUST | spec/000-status-and-conformance.md | 23 | A conforming implementation MUST maintain a requirement traceability matrix linking each applicable requirement to code, tests, documentation, and review evidence. |
| SFAEF-000-012 | MUST | spec/000-status-and-conformance.md | 25 | “Not applicable” MUST include a reason and may be rejected during product-owner review. |
| SFAEF-000-013 | NORMATIVE | spec/000-status-and-conformance.md | 27 | A requirement cannot be marked complete solely because a file exists. Completion requires behavior and evidence. |
| SFAEF-000-030 | MUST | spec/000-status-and-conformance.md | 78 | Material changes to trust boundaries, evidence precedence, context limits, product mutation, or QA truth criteria MUST include an ADR. |
| SFAEF-000-031 | MUST | spec/000-status-and-conformance.md | 80 | Specification changes MUST include a changelog entry, affected requirement IDs, migration notes, and test updates. |
| SFAEF-000-032 | MUST | spec/000-status-and-conformance.md | 82 | A generated artifact drift check MUST fail when tracked generated output does not match canonical source. |
| SFAEF-000-033 | MAY | spec/000-status-and-conformance.md | 84 | The product owner may reject technically passing work when the behavior violates the product intent, hides uncertainty, or creates a misleading user experience. |
| SFAEF-010-001 | MUST | spec/010-vision-and-scope.md | 20 | The framework MUST answer Salesforce engineering questions with explicit evidence, unknowns, and confidence rationale. |
| SFAEF-010-002 | MUST | spec/010-vision-and-scope.md | 22 | It MUST remain useful in standalone, local-project, live-read-only, and scratch-QA modes. |
| SFAEF-010-003 | MUST | spec/010-vision-and-scope.md | 24 | Optional enrichment MUST never be represented as a mandatory prerequisite unless the product cannot logically operate without it. |
| SFAEF-010-004 | MUST NOT | spec/010-vision-and-scope.md | 26 | A missing local Salesforce project MUST NOT prevent deployment or test-result diagnosis when sufficient job evidence exists. |
| SFAEF-010-005 | MUST | spec/010-vision-and-scope.md | 28 | A missing org MUST produce a truthful reduced mode, partial result, or refusal—not fabricated org state. |
| SFAEF-010-006 | MUST | spec/010-vision-and-scope.md | 30 | The same core product contract MUST be portable across hosts even when host capabilities differ. |
| SFAEF-010-020 | MUST | spec/010-vision-and-scope.md | 59 | V2 MUST provide a host-native Cursor product and preserve/strengthen Claude compatibility. |
| SFAEF-010-021 | MUST | spec/010-vision-and-scope.md | 61 | V2 MUST provide the six flagship products defined in `products/README.md`, with at least the first three behaviorally qualified before a 1.0 claim. |
| SFAEF-010-022 | MUST | spec/010-vision-and-scope.md | 63 | V2 MUST provide a deterministic core for contracts, context, evidence, policy, state, redaction, telemetry, and review packaging. |
| SFAEF-010-023 | MUST | spec/010-vision-and-scope.md | 65 | V2 MUST provide read-only Salesforce evidence tools for the shipped products. |
| SFAEF-010-024 | MUST | spec/010-vision-and-scope.md | 67 | V2 MUST provide a protected scratch-org behavioral QA lane. |
| SFAEF-010-025 | MUST | spec/010-vision-and-scope.md | 69 | V2 MUST provide a public, reproducible benchmark format even when some datasets remain private. |
| SFAEF-020-001 | MUST | spec/020-design-principles.md | 7 | Every product primitive MUST be justified by a concrete user job and observed implementation need. |
| SFAEF-020-010 | MUST | spec/020-design-principles.md | 13 | Confidence MUST be derived from evidence coverage, source authority, freshness, contradictions, and execution completeness—not model tone. |
| SFAEF-020-011 | NORMATIVE | spec/020-design-principles.md | 15 | A high-confidence statement without valid evidence is a defect. |
| SFAEF-020-012 | NORMATIVE | spec/020-design-principles.md | 17 | “Unknown” is preferable to an unsupported answer. |
| SFAEF-020-020 | MUST | spec/020-design-principles.md | 21 | The context window MUST be treated as scarce working memory, not a document store. |
| SFAEF-020-021 | MUST | spec/020-design-principles.md | 23 | Relevant context MUST be selected, ordered, deduplicated, measured, and released between jobs. |
| SFAEF-020-022 | MUST NOT | spec/020-design-principles.md | 25 | A larger context window MUST NOT be used as the primary remedy for poor selection. |
| SFAEF-020-030 | SHOULD | spec/020-design-principles.md | 29 | Hosts SHOULD discover compact skill metadata first, load instructions only on activation, and load references/scripts only when required. |
| SFAEF-020-031 | MUST | spec/020-design-principles.md | 31 | Product knowledge MUST be decomposed into core and conditional context packs. |
| SFAEF-020-040 | MUST | spec/020-design-principles.md | 35 | A host-native subagent MUST have one clear responsibility, a bounded input, a bounded output, and a reason to need isolated context. |
| SFAEF-020-041 | SHOULD | spec/020-design-principles.md | 37 | Existing specialist agents SHOULD remain catalog capabilities unless isolated execution materially improves quality. |
| SFAEF-020-042 | NORMATIVE | spec/020-design-principles.md | 39 | Do not expose dozens of overlapping agents and call that orchestration. |
| SFAEF-020-050 | MUST | spec/020-design-principles.md | 43 | Agents MUST pass facts, evidence references, hypotheses, unknowns, and metrics—not complete hidden reasoning or raw transcripts. |
| SFAEF-020-051 | MUST | spec/020-design-principles.md | 45 | Every handoff MUST validate against `schemas/handoff.schema.json`. |
| SFAEF-020-060 | MUST | spec/020-design-principles.md | 49 | Deterministic code MUST own parsing, schema validation, identifiers, normalization, pagination, redaction, policy classification, state transitions, and hard grading. |
| SFAEF-020-061 | SHOULD | spec/020-design-principles.md | 51 | Models SHOULD own interpretation, synthesis, prioritization, and explanation within those boundaries. |
| SFAEF-020-070 | MUST NOT | spec/020-design-principles.md | 55 | Ordinary product tools MUST NOT mutate Salesforce. |
| SFAEF-020-071 | MAY | spec/020-design-principles.md | 57 | Controlled mutation MAY occur only in disposable QA setup code that is not exposed to product agents and is deleted after the scenario. |
| SFAEF-020-080 | MUST NOT | spec/020-design-principles.md | 61 | The framework MUST NOT assume the SfSkills repository is the Salesforce project. |
| SFAEF-020-081 | MUST | spec/020-design-principles.md | 63 | Project discovery order MUST be explicit path, active workspace, bounded roots, then standalone. |
| SFAEF-020-082 | MUST | spec/020-design-principles.md | 65 | Multiple candidate projects MUST produce `ambiguous`, never an arbitrary selection. |
| SFAEF-020-090 | MUST | spec/020-design-principles.md | 69 | Each host adapter MUST declare what it can actually enforce: subagent isolation, MCP access, hooks, compaction events, local execution, and human approval. |
| SFAEF-020-091 | MUST NOT | spec/020-design-principles.md | 71 | A local safety guarantee MUST NOT be advertised as a cloud guarantee when the host lacks the required hook. |
| SFAEF-020-100 | MUST | spec/020-design-principles.md | 75 | Consequential product outputs MUST receive an independent evidence review before `completed` status. |
| SFAEF-020-101 | MUST NOT | spec/020-design-principles.md | 77 | The reviewer MUST be able to downgrade status or confidence and MUST not merely restate the draft. |
| SFAEF-020-110 | MUST | spec/020-design-principles.md | 81 | Every qualified run MUST be reproducible from a redacted run bundle or explicitly marked non-replayable with a reason. |
| SFAEF-020-111 | MUST | spec/020-design-principles.md | 83 | Product quality MUST be measured on versioned scenarios and real host behavior, not screenshots alone. |
| SFAEF-020-120 | MUST | spec/020-design-principles.md | 87 | Every product MUST define `completed`, `partial`, `refused`, and `failed` states. |
| SFAEF-020-121 | NORMATIVE | spec/020-design-principles.md | 89 | Silent truncation, silent substitution, silent project/org selection, and silent evidence loss are prohibited. |
| SFAEF-020-130 | MUST | spec/020-design-principles.md | 93 | Material claims MUST have stable IDs and typed support links. |
| SFAEF-020-131 | MUST NOT | spec/020-design-principles.md | 95 | Contradictory evidence MUST remain visible; the system must not erase it during summarization. |
| SFAEF-020-140 | MUST | spec/020-design-principles.md | 99 | Salesforce platform guidance MUST carry source provenance and review dates. |
| SFAEF-020-141 | MUST | spec/020-design-principles.md | 101 | Release-sensitive claims MUST be tested against current official sources and compatibility fixtures. |
| SFAEF-020-150 | MUST | spec/020-design-principles.md | 105 | North-star metrics MUST emphasize successful, evidenced user outcomes, time to resolution, unsupported-claim rate, and repeat use. |
| SFAEF-020-160 | SHOULD | spec/020-design-principles.md | 111 | The framework SHOULD complement Salesforce, Gearset, Copado, Elements, Salto, and other delivery systems through portable evidence and adapters rather than pretending to replace their mature pipeline, graph, or deployment capabilities immediately. |
| SFAEF-020-170 | MUST | spec/020-design-principles.md | 115 | The specification MUST remain implementable. Every new mandatory object or layer requires a consumer, validator, and test. |
| SFAEF-030-001 | MUST | spec/030-product-model.md | 22 | Every shipped product MUST conform to `schemas/product.schema.json` and have a human specification under `products/`. |
| SFAEF-030-010 | MUST | spec/030-product-model.md | 44 | The mode MUST be recorded in the run envelope. |
| SFAEF-030-011 | MUST | spec/030-product-model.md | 46 | A product MUST state which findings are unavailable in each reduced mode. |
| SFAEF-030-020 | SHOULD | spec/030-product-model.md | 65 | Local installation SHOULD produce useful fixture output before Salesforce authentication is required. |
| SFAEF-030-021 | MUST | spec/030-product-model.md | 67 | `sfskills-doctor` MUST explain missing dependencies and how they affect capabilities. |
| SFAEF-030-022 | SHOULD | spec/030-product-model.md | 69 | The first useful product run SHOULD require no more than one command and one primary input artifact or job ID. |
| SFAEF-030-023 | MUST NOT | spec/030-product-model.md | 71 | The framework MUST not ask users to choose among dozens of agents. |
| SFAEF-030-030 | MUST NOT | spec/030-product-model.md | 80 | `completed` MUST NOT be used when the evidence reviewer has a blocking finding. |
| SFAEF-030-031 | MUST | spec/030-product-model.md | 82 | `partial` MUST enumerate impact by dimension rather than merely lowering confidence. |
| SFAEF-040-001 | MUST | spec/040-reference-architecture.md | 43 | A conforming implementation MUST separate canonical product contracts from host-generated artifacts. |
| SFAEF-040-002 | MUST | spec/040-reference-architecture.md | 45 | Product agents MUST access Salesforce evidence only through an evidence broker or an equivalently enforced adapter. |
| SFAEF-040-003 | MUST | spec/040-reference-architecture.md | 47 | The evidence broker MUST validate inputs, pin target identity, enforce permissions, normalize output, redact secrets, assign evidence IDs, and report truncation. |
| SFAEF-040-004 | MUST | spec/040-reference-architecture.md | 49 | The context compiler MUST consume product policy, agent contract, selected knowledge, normalized evidence, and host budget to create a stage-specific context manifest. |
| SFAEF-040-005 | MUST | spec/040-reference-architecture.md | 51 | The claim/evidence graph MUST exist outside the final prose and remain machine-validatable. |
| SFAEF-040-006 | MUST | spec/040-reference-architecture.md | 53 | Independent evidence review MUST use a context isolated from the drafting agent's hidden transcript. |
| SFAEF-040-007 | MUST | spec/040-reference-architecture.md | 55 | Run artifacts MUST remain replayable without requiring the original chat transcript whenever source licensing and privacy permit. |
| SFAEF-040-020 | MUST | spec/040-reference-architecture.md | 68 | Crossing a trust boundary MUST produce a typed, validated object or an explicit refusal/error. |
| SFAEF-040-021 | MAY | spec/040-reference-architecture.md | 70 | No downstream component may silently upgrade advisory or inferred data to observed fact. |
| SFAEF-040-030 | MUST | spec/040-reference-architecture.md | 82 | Networked deployment MUST preserve the same evidence, permission, and run contracts as local execution. |
| SFAEF-050-001 | MUST | spec/050-runtime-and-state-machine.md | 23 | Every product invocation MUST create a run ID before tool use. |
| SFAEF-050-002 | MUST | spec/050-runtime-and-state-machine.md | 25 | Every state transition MUST be recorded with time, actor, reason, and previous state. |
| SFAEF-050-003 | MUST | spec/050-runtime-and-state-machine.md | 27 | Invalid transitions MUST fail deterministically. |
| SFAEF-050-004 | MUST | spec/050-runtime-and-state-machine.md | 29 | Input validation MUST occur before agent delegation or Salesforce access. |
| SFAEF-050-005 | MUST | spec/050-runtime-and-state-machine.md | 31 | Preflight MUST resolve host capability, product version, requested execution mode, project selection, org identity, index state, and permission policy. |
| SFAEF-050-006 | MUST | spec/050-runtime-and-state-machine.md | 33 | Planning MUST declare stages, agents, tools, evidence needs, context budgets, optional enrichments, and stop conditions. |
| SFAEF-050-007 | MUST NOT | spec/050-runtime-and-state-machine.md | 35 | A plan MUST NOT silently add tools or permissions after execution begins. |
| SFAEF-050-008 | MUST | spec/050-runtime-and-state-machine.md | 37 | A product MAY re-plan when evidence invalidates the initial plan, but the delta and reason MUST be recorded. |
| SFAEF-050-009 | MUST | spec/050-runtime-and-state-machine.md | 39 | Retry behavior MUST be limited to declared transient failures, bounded, and recorded. |
| SFAEF-050-010 | MUST NOT | spec/050-runtime-and-state-machine.md | 41 | A human approval request MUST include the exact requested action, target identity, authority, and consequence. V2 diagnostic products MUST not request approval for Salesforce mutation because mutation is out of scope. |
| SFAEF-050-020 | NORMATIVE | spec/050-runtime-and-state-machine.md | 45 | `completed` requires valid output, no blocking evidence-review finding, no undisclosed hard prerequisite failure, and no silent truncation. |
| SFAEF-050-021 | NORMATIVE | spec/050-runtime-and-state-machine.md | 47 | `partial` requires useful validated output and an explicit impact statement for every missing, stale, contradictory, or truncated dimension. |
| SFAEF-050-022 | NORMATIVE | spec/050-runtime-and-state-machine.md | 49 | `refused` is required for unsafe requests, ambiguous target identity that cannot be resolved safely, prohibited authority, or missing mandatory user input. |
| SFAEF-050-023 | MUST | spec/050-runtime-and-state-machine.md | 51 | `failed` is reserved for unexpected system/tool failure after safe handling; it MUST include a sanitized error class and retry guidance. |
| SFAEF-050-030 | SHOULD | spec/050-runtime-and-state-machine.md | 55 | Replaying a run with the same immutable fixture evidence and product version SHOULD produce structurally equivalent claims and status. |
| SFAEF-050-031 | MUST | spec/050-runtime-and-state-machine.md | 57 | Resumption MUST validate product version, schema version, target identity, evidence freshness, and policy version before continuing. |
| SFAEF-050-032 | MUST NOT | spec/050-runtime-and-state-machine.md | 59 | A resumed run MUST not inherit a previous run's org, project, evidence, or unverified memory by default. |
| SFAEF-060-001 | MUST | spec/060-knowledge-plane.md | 9 | Discovery MUST begin from compact metadata or bounded domain routers. |
| SFAEF-060-002 | MUST | spec/060-knowledge-plane.md | 11 | Full `SKILL.md` content MUST be loaded only after selection. |
| SFAEF-060-003 | MUST | spec/060-knowledge-plane.md | 13 | References, scripts, and assets MUST be loaded only when the active stage requires them. |
| SFAEF-060-004 | MUST NOT | spec/060-knowledge-plane.md | 15 | The default host package MUST NOT expose all 1,034 packages as always-on rules or unbounded top-level instructions. |
| SFAEF-060-010 | MUST | spec/060-knowledge-plane.md | 29 | Selection MUST be deterministic for required core items. |
| SFAEF-060-011 | MUST | spec/060-knowledge-plane.md | 31 | Model-assisted ranking MAY be used for conditional items, but hard limits and allowlists MUST remain deterministic. |
| SFAEF-060-012 | SHOULD | spec/060-knowledge-plane.md | 33 | Duplicate or semantically overlapping items SHOULD be collapsed or ranked, not loaded without explanation. |
| SFAEF-060-020 | MAY | spec/060-knowledge-plane.md | 37 | A skill citation MAY support a recommendation or platform-behavior claim. |
| SFAEF-060-021 | MUST NOT | spec/060-knowledge-plane.md | 39 | A skill citation MUST NOT support a claim that a target org, user, component, record, or job has a specific state. |
| SFAEF-060-030 | MUST | spec/060-knowledge-plane.md | 43 | Release-sensitive knowledge MUST carry an official-source reference and last-reviewed date. |
| SFAEF-060-031 | MUST | spec/060-knowledge-plane.md | 45 | A source freshness policy MUST classify knowledge as current, review-due, stale, superseded, or historical. |
| SFAEF-060-032 | MAY | spec/060-knowledge-plane.md | 47 | Stale knowledge MAY be used only with an explicit warning unless a product policy prohibits it. |
| SFAEF-060-040 | NORMATIVE | spec/060-knowledge-plane.md | 51 | Existing packages remain canonical knowledge during migration. |
| SFAEF-060-041 | MUST | spec/060-knowledge-plane.md | 53 | Broad agent mandatory-read lists MUST be converted to core and conditional context packs before the agent is labelled V2-native. |
| SFAEF-060-042 | MUST NOT | spec/060-knowledge-plane.md | 55 | Existing indexes and routers MAY remain compatibility surfaces, but missing-index state MUST be explicit and must not masquerade as zero results. |
| SFAEF-070-001 | MUST | spec/070-agent-and-delegation-model.md | 13 | A host-native subagent MUST have a clear isolated-context benefit: noisy exploration, tool-specific evidence gathering, independent review, or specialized synthesis. |
| SFAEF-070-002 | SHOULD | spec/070-agent-and-delegation-model.md | 15 | A one-step formatting or deterministic task SHOULD remain code, a skill, or a command rather than a subagent. |
| SFAEF-070-003 | MUST | spec/070-agent-and-delegation-model.md | 17 | Default host packages MUST expose a small curated set of proven subagents, not the full catalog. |
| SFAEF-070-010 | MUST NOT | spec/070-agent-and-delegation-model.md | 34 | Agents MUST NOT acquire tools outside the active run plan. |
| SFAEF-070-011 | MUST NOT | spec/070-agent-and-delegation-model.md | 36 | Agents MUST NOT infer permission from a natural-language prompt. |
| SFAEF-070-012 | MUST | spec/070-agent-and-delegation-model.md | 38 | Product agents MUST distinguish observations, inferences, recommendations, and unknowns. |
| SFAEF-070-020 | MUST | spec/070-agent-and-delegation-model.md | 42 | Every cross-agent handoff MUST validate against `handoff.schema.json`. |
| SFAEF-070-021 | MUST | spec/070-agent-and-delegation-model.md | 44 | A handoff MUST contain only task, facts, evidence references, hypotheses, unknowns, requested next action, and context metrics. |
| SFAEF-070-022 | MUST NOT | spec/070-agent-and-delegation-model.md | 46 | Full transcripts, hidden reasoning, credentials, and unbounded raw tool output MUST NOT be transferred. |
| SFAEF-070-023 | MUST NOT | spec/070-agent-and-delegation-model.md | 48 | Receiving agents MUST validate referenced evidence and MUST not trust a sending agent's confidence without support. |
| SFAEF-070-030 | MUST | spec/070-agent-and-delegation-model.md | 52 | The evidence reviewer MUST receive the draft claims, evidence index, product policy, and output schema—but not the drafting agent's hidden transcript. |
| SFAEF-070-031 | MUST | spec/070-agent-and-delegation-model.md | 54 | The reviewer MUST be able to block completion, downgrade claims, require unknowns, and flag unsafe recommendations. |
| SFAEF-070-032 | NORMATIVE | spec/070-agent-and-delegation-model.md | 56 | Reviewer agreement alone is not proof; deterministic evidence lint remains mandatory. |
| SFAEF-080-001 | MUST | spec/080-context-engine.md | 27 | Every stage MUST have a context manifest. |
| SFAEF-080-002 | MUST | spec/080-context-engine.md | 29 | Every context item MUST include source, reason, priority, estimated cost, digest, and stage. |
| SFAEF-080-003 | MUST | spec/080-context-engine.md | 31 | Required control context MUST be loaded before optional knowledge. |
| SFAEF-080-004 | MUST | spec/080-context-engine.md | 33 | Evidence summaries MUST preserve IDs, counts, severity, timestamps, target identity, and contradiction links. |
| SFAEF-080-005 | MUST | spec/080-context-engine.md | 35 | Silent truncation is prohibited. Truncation MUST include original count/bytes, retained count/bytes, strategy, and continuation token when available. |
| SFAEF-080-006 | MUST | spec/080-context-engine.md | 37 | Context selection MUST be stable for equivalent inputs and versions, subject to documented model ranking only for conditional tie-breaking. |
| SFAEF-080-007 | MUST | spec/080-context-engine.md | 39 | A second unrelated user task MUST start a new run context unless the user explicitly links it to the current run. |
| SFAEF-080-020 | SHOULD | spec/080-context-engine.md | 43 | Before host compaction where observable, the framework SHOULD write a context checkpoint containing run state, target identities, selected knowledge, evidence IDs, claims, unknowns, policy version, and next stage. |
| SFAEF-080-021 | MUST NOT | spec/080-context-engine.md | 45 | A checkpoint MUST NOT contain complete raw transcripts or secrets. |
| SFAEF-080-022 | MUST | spec/080-context-engine.md | 47 | After compaction, the runtime MUST rehydrate from the checkpoint and evidence store, then validate continuity before continuing. |
| SFAEF-080-023 | SHOULD | spec/080-context-engine.md | 49 | If the host does not expose compaction events, the runtime SHOULD checkpoint at deterministic stage boundaries. |
| SFAEF-080-030 | MUST | spec/080-context-engine.md | 53 | Every flagship product MUST test irrelevant distractors, oversized evidence, duplicate symptoms, contradictory evidence, long first task followed by a second task, and checkpoint/resume. |
| SFAEF-080-031 | MUST | spec/080-context-engine.md | 55 | Context efficiency MUST be reported with quality; lower context is not a success if required finding recall drops. |
| SFAEF-090-001 | MUST | spec/090-evidence-and-claim-model.md | 34 | Every material claim MUST have a stable claim ID, type, text, status, support links, and confidence rationale. |
| SFAEF-090-002 | MUST | spec/090-evidence-and-claim-model.md | 36 | Support links MUST declare `supports`, `contradicts`, `contextualizes`, or `derived_from`. |
| SFAEF-090-003 | MUST | spec/090-evidence-and-claim-model.md | 38 | A claim with no valid support MUST be removed, labelled hypothesis, or included as an explicit unknown/question. |
| SFAEF-090-004 | MUST | spec/090-evidence-and-claim-model.md | 40 | Contradictory evidence MUST remain in the graph and affect status/confidence. |
| SFAEF-090-005 | MUST | spec/090-evidence-and-claim-model.md | 42 | Recommendations MUST link to the findings and constraints they address. |
| SFAEF-090-010 | MUST NOT | spec/090-evidence-and-claim-model.md | 58 | Confidence MUST NOT be generated solely from model self-assessment. |
| SFAEF-090-011 | MUST | spec/090-evidence-and-claim-model.md | 60 | Confidence labels MUST be accompanied by a machine-readable rationale. |
| SFAEF-090-012 | NORMATIVE | spec/090-evidence-and-claim-model.md | 62 | High confidence requires direct or authoritative support for every load-bearing claim and no unresolved blocking contradiction. |
| SFAEF-090-020 | MUST | spec/090-evidence-and-claim-model.md | 66 | Tool, metadata, source-comment, log, and record content MUST be treated as untrusted data. |
| SFAEF-090-021 | MUST | spec/090-evidence-and-claim-model.md | 68 | Instructions embedded in evidence MUST never modify policy, permissions, product contract, or system behavior. |
| SFAEF-090-022 | SHOULD | spec/090-evidence-and-claim-model.md | 70 | Evidence renderers SHOULD distinguish data from instructions using structured serialization and explicit delimiters. |
| SFAEF-100-001 | MUST | spec/100-tool-and-mcp-broker.md | 9 | Every product tool MUST have a typed specification, input/output validation, permission class, timeout, result bound, and tests. |
| SFAEF-100-002 | MUST | spec/100-tool-and-mcp-broker.md | 11 | Unknown tools MUST be denied by default in product mode. |
| SFAEF-100-003 | MUST NOT | spec/100-tool-and-mcp-broker.md | 13 | Tool annotations MAY inform UX but MUST NOT be treated as enforcement. |
| SFAEF-100-004 | MUST | spec/100-tool-and-mcp-broker.md | 15 | The broker MUST pin an explicit org identity for a run. `ALLOW_ALL_ORGS` and silent most-recent/default-job behavior are prohibited in product mode. |
| SFAEF-100-005 | MAY | spec/100-tool-and-mcp-broker.md | 17 | Dynamic default-org tokens MAY be used only after the resolved identity is shown and recorded; fixed aliases/usernames are preferred for consequential runs. |
| SFAEF-100-006 | MUST | spec/100-tool-and-mcp-broker.md | 19 | Upstream toolsets MUST be minimized. Enabling `all` is prohibited for the default product configuration. |
| SFAEF-100-007 | MUST | spec/100-tool-and-mcp-broker.md | 21 | Results MUST be normalized, redacted, bounded, assigned stable evidence IDs, and linked to the upstream tool/version. |
| SFAEF-100-008 | MUST NOT | spec/100-tool-and-mcp-broker.md | 23 | Long operations MUST use explicit continuation/resume objects; agents MUST not poll without bounded policy. |
| SFAEF-100-009 | MUST | spec/100-tool-and-mcp-broker.md | 25 | Tool errors MUST be classified as input, auth, target mismatch, unavailable, timeout, rate, malformed upstream, policy, or unexpected. |
| SFAEF-100-020 | SHOULD | spec/100-tool-and-mcp-broker.md | 31 | A tool that triggers a test or validation job is not observational and requires a separate authority profile. V2 flagship user products SHOULD retrieve existing results; controlled QA setup may initiate tests in disposable orgs outside the product broker. |
| SFAEF-100-030 | NORMATIVE | spec/100-tool-and-mcp-broker.md | 35 | Prefer official Salesforce DX MCP or CLI for canonical Salesforce operations. |
| SFAEF-100-031 | NORMATIVE | spec/100-tool-and-mcp-broker.md | 37 | Add SfSkills-specific wrappers only when they provide stable normalization, evidence semantics, bounded output, policy enforcement, or product-level aggregation. |
| SFAEF-100-032 | SHOULD | spec/100-tool-and-mcp-broker.md | 39 | Deterministic local analysis SHOULD use the underlying CLI/library directly when MCP adds no user or host value. |
| SFAEF-110-001 | MUST | spec/110-security-and-authority.md | 13 | Every run MUST declare exactly one authority profile and a target identity scope. |
| SFAEF-110-002 | MUST NOT | spec/110-security-and-authority.md | 15 | Product agents MUST not elevate authority, change org allowlists, or invoke QA setup code. |
| SFAEF-110-003 | MUST | spec/110-security-and-authority.md | 17 | Product policy MUST be deny-by-default for unknown MCP tools and shell commands. |
| SFAEF-110-004 | MUST | spec/110-security-and-authority.md | 19 | Shell classification MUST parse command structure and reject compound/nested execution, not rely only on substrings. |
| SFAEF-110-005 | MUST | spec/110-security-and-authority.md | 21 | Credentials, access tokens, auth URLs, session IDs, private keys, and sensitive values MUST be redacted before persistence or model exposure. |
| SFAEF-110-006 | MUST | spec/110-security-and-authority.md | 23 | The run MUST display and record the selected org and project before consequential evidence gathering. |
| SFAEF-110-007 | MUST | spec/110-security-and-authority.md | 25 | Multiple project or org candidates MUST produce an ambiguity state rather than an arbitrary selection. |
| SFAEF-110-008 | MUST | spec/110-security-and-authority.md | 27 | Host capability gaps MUST downgrade the guarantee. If an MCP hook is unavailable in cloud execution, documentation and status MUST say so. |
| SFAEF-110-020 | NORMATIVE | spec/110-security-and-authority.md | 31 | Tool output, metadata descriptions, source comments, logs, record values, and retrieved documents are untrusted. |
| SFAEF-110-021 | MUST | spec/110-security-and-authority.md | 33 | Evidence must never be able to override system policy, request new tools, modify schemas, or change review criteria. |
| SFAEF-110-022 | MUST | spec/110-security-and-authority.md | 35 | The framework MUST test direct and indirect prompt injection carried in Salesforce text fields, Apex comments, logs, filenames, and MCP error text. |
| SFAEF-110-030 | SHOULD | spec/110-security-and-authority.md | 39 | Host packages and review artifacts SHOULD include manifests and checksums. |
| SFAEF-110-031 | MUST | spec/110-security-and-authority.md | 41 | Generated plugin output MUST be deterministic and drift-checked. |
| SFAEF-110-032 | MUST NOT | spec/110-security-and-authority.md | 43 | Dependencies and external executables MUST be version-recorded; install helpers MUST not silently replace unrelated files. |
| SFAEF-110-040 | MUST | spec/110-security-and-authority.md | 47 | Scratch setup MUST verify Dev Hub identity, scratch-org type, expiration, and a scenario marker before mutation. |
| SFAEF-110-041 | MUST | spec/110-security-and-authority.md | 49 | Cleanup MUST run unconditionally and produce deletion evidence. |
| SFAEF-110-042 | MUST | spec/110-security-and-authority.md | 51 | A failure to prove disposability MUST stop the scenario before mutation. |
| SFAEF-120-001 | MUST | spec/120-output-and-user-experience.md | 22 | Human-readable output MUST be rendered from validated structured output. |
| SFAEF-120-002 | MUST | spec/120-output-and-user-experience.md | 24 | Material findings MUST show claim IDs and evidence references in a discoverable form. |
| SFAEF-120-003 | MUST | spec/120-output-and-user-experience.md | 26 | The result MUST separate observed fact, inference, recommendation, and unknown. |
| SFAEF-120-004 | MUST | spec/120-output-and-user-experience.md | 28 | The result MUST state execution mode and target org/project/job identities. |
| SFAEF-120-005 | MUST | spec/120-output-and-user-experience.md | 30 | Partial results MUST explain what is unavailable and how it affects conclusions. |
| SFAEF-120-006 | MUST NOT | spec/120-output-and-user-experience.md | 32 | Safe verification commands MAY be displayed but MUST NOT be executed unless the product contract explicitly permits the read-only operation. |
| SFAEF-120-007 | MUST NOT | spec/120-output-and-user-experience.md | 34 | Destructive or mutating commands MUST NOT be presented as an automatic next step. If mentioned for human workflow context, they MUST be clearly marked outside product authority. |
| SFAEF-120-008 | MUST | spec/120-output-and-user-experience.md | 36 | Output MUST avoid false precision, generic filler, and long unprioritized checklists. |
| SFAEF-120-009 | SHOULD | spec/120-output-and-user-experience.md | 38 | The user SHOULD be able to request `why`, `show evidence`, `compare`, or `replay` without re-running all upstream tools when evidence remains valid. |
| SFAEF-120-020 | MUST | spec/120-output-and-user-experience.md | 42 | Core results MUST be representable as Markdown and JSON. |
| SFAEF-120-021 | MUST NOT | spec/120-output-and-user-experience.md | 44 | Severity, confidence, and status MUST not rely on color alone. |
| SFAEF-120-022 | MUST NOT | spec/120-output-and-user-experience.md | 46 | Host-specific rich UI MAY enhance but must not hide required information. |
| SFAEF-130-001 | MUST | spec/130-observability-and-replay.md | 20 | Local run artifacts MUST be gitignored by default. |
| SFAEF-130-002 | MUST | spec/130-observability-and-replay.md | 22 | Telemetry MUST distinguish local product telemetry from any upstream host/vendor telemetry. |
| SFAEF-130-003 | MUST | spec/130-observability-and-replay.md | 24 | Product telemetry MUST be opt-in beyond essential local diagnostics unless the owner explicitly chooses another policy. |
| SFAEF-130-004 | MUST | spec/130-observability-and-replay.md | 26 | A run MUST record model, host, adapter, product, schema, policy, and upstream-tool versions when available. |
| SFAEF-130-005 | MUST NOT | spec/130-observability-and-replay.md | 28 | Raw secret-bearing payloads MUST not be persisted. |
| SFAEF-130-006 | MUST | spec/130-observability-and-replay.md | 30 | Evidence required for replay MUST include a digest; external pointers MUST include freshness and availability notes. |
| SFAEF-130-007 | MUST NOT | spec/130-observability-and-replay.md | 32 | Replay MUST not call live tools unless explicitly requested; fixture replay is the default. |
| SFAEF-130-008 | MUST | spec/130-observability-and-replay.md | 34 | A non-replayable run MUST state why and which assertions cannot be reverified. |
| SFAEF-130-020 | MUST NOT | spec/130-observability-and-replay.md | 48 | Metrics MUST NOT record hidden chain-of-thought. |
| SFAEF-140-001 | MUST | spec/140-quality-and-evaluation.md | 18 | CI gates MUST be deterministic and credential-free unless explicitly run in a protected environment. |
| SFAEF-140-002 | MUST NOT | spec/140-quality-and-evaluation.md | 20 | Model-based judging MUST not be the sole gate for safety, evidence validity, required facts, or schema compliance. |
| SFAEF-140-003 | MUST | spec/140-quality-and-evaluation.md | 22 | Known-truth labels MUST be versioned, reviewable, and independent of the prompt being evaluated. |
| SFAEF-140-004 | MUST | spec/140-quality-and-evaluation.md | 24 | Scenarios MUST score required finding recall, unsupported claim rate, evidence-reference validity, harmful recommendation rate, status correctness, and context efficiency. |
| SFAEF-140-005 | SHOULD NOT | spec/140-quality-and-evaluation.md | 26 | Exact prose matching SHOULD NOT be the primary behavioral criterion. |
| SFAEF-140-006 | MUST | spec/140-quality-and-evaluation.md | 28 | Every reported quality number MUST include dataset/scenario version, sample size, run date, host/model version, scoring method, and confidence/uncertainty where appropriate. |
| SFAEF-140-007 | MUST | spec/140-quality-and-evaluation.md | 30 | Flagship products MUST be compared with the same host/model without SfSkills. |
| SFAEF-140-008 | MUST | spec/140-quality-and-evaluation.md | 32 | Tests MUST include missing evidence, contradictory evidence, stale evidence, malformed upstream data, auth failure, target mismatch, secret-shaped data, and unsafe requests. |
| SFAEF-140-009 | MUST | spec/140-quality-and-evaluation.md | 34 | Reviewer tests MUST include deliberately persuasive but unsupported drafts. |
| SFAEF-150-001 | MUST | spec/150-real-org-qa.md | 19 | Product agents and product MCP tools MUST remain read-only in all lanes. |
| SFAEF-150-002 | MUST | spec/150-real-org-qa.md | 21 | Scratch mutation MUST be performed only by versioned QA setup scripts under `qa-scratch-setup` authority. |
| SFAEF-150-003 | MUST | spec/150-real-org-qa.md | 23 | Setup scripts MUST verify a disposable scratch-org marker and refuse any other org. |
| SFAEF-150-004 | MUST | spec/150-real-org-qa.md | 25 | Cleanup MUST execute even when setup, product, or grading fails. |
| SFAEF-150-005 | MUST | spec/150-real-org-qa.md | 27 | Artifacts MUST record Dev Hub identifier in redacted form, scratch alias/username hash, creation/deletion timestamps, scenario version, Salesforce API/release version, CLI/MCP version, host/model version, and result IDs. |
| SFAEF-150-006 | MUST | spec/150-real-org-qa.md | 29 | Ground truth MUST use stable finding IDs and required evidence facts, not exact expected prose. |
| SFAEF-150-007 | MUST | spec/150-real-org-qa.md | 31 | Real-org execution MUST scan artifacts for secrets before upload. |
| SFAEF-150-008 | MUST | spec/150-real-org-qa.md | 33 | A live test not run MUST be reported as `not_run`, never inferred from fixtures. |
| SFAEF-160-001 | MUST | spec/160-host-adapters-and-portability.md | 9 | Every adapter MUST publish a host-capability record. |
| SFAEF-160-002 | MUST | spec/160-host-adapters-and-portability.md | 11 | Unsupported guarantees MUST cause a documented fallback or capability-limited status. |
| SFAEF-160-003 | MUST | spec/160-host-adapters-and-portability.md | 13 | Host artifacts MUST be generated from canonical framework definitions where practical. |
| SFAEF-160-004 | MUST | spec/160-host-adapters-and-portability.md | 15 | Adapter tests MUST verify discovery, invocation, tool access, output, and safety in the actual host—not only file shape. |
| SFAEF-160-020 | MUST NOT | spec/160-host-adapters-and-portability.md | 39 | A2A MUST NOT be used merely to wrap in-process subagents. |
| SFAEF-160-021 | NORMATIVE | spec/160-host-adapters-and-portability.md | 41 | Future A2A exposure requires agent identity, authorization, agent-card capability scope, task lifecycle, evidence-transfer rules, retention, and compatibility tests. |
| SFAEF-170-001 | MUST | spec/170-knowledge-freshness.md | 13 | Every release-sensitive skill or product rule MUST record source URL/reference, retrieved date, reviewed date, applicable Salesforce/API/host version, and owner. |
| SFAEF-170-002 | MUST NOT | spec/170-knowledge-freshness.md | 15 | Automated source monitors MAY detect changes but MUST not silently rewrite canonical guidance. |
| SFAEF-170-003 | MUST | spec/170-knowledge-freshness.md | 17 | A source change MUST create a review item linked to affected skills, products, tools, scenarios, and adapters. |
| SFAEF-170-004 | SHOULD | spec/170-knowledge-freshness.md | 19 | Current official documentation SHOULD be stored as links/digests or permitted snapshots according to licensing; do not copy restricted content wholesale. |
| SFAEF-170-005 | MUST | spec/170-knowledge-freshness.md | 21 | Freshness jobs MUST distinguish source unavailable, changed, reviewed-no-impact, update-required, and superseded. |
| SFAEF-170-006 | SHOULD | spec/170-knowledge-freshness.md | 23 | Salesforce seasonal release checks SHOULD run against affected flagship scenarios before compatibility is claimed. |
| SFAEF-180-001 | MUST | spec/180-data-privacy-and-retention.md | 15 | Every evidence item MUST carry a data classification. |
| SFAEF-180-002 | MUST | spec/180-data-privacy-and-retention.md | 17 | Credential-secret data MUST never be persisted or sent to the model. |
| SFAEF-180-003 | SHOULD | spec/180-data-privacy-and-retention.md | 19 | Org-business-data SHOULD be minimized and replaced with schema/count/hashed examples when content is not necessary. |
| SFAEF-180-004 | MUST | spec/180-data-privacy-and-retention.md | 21 | Default run retention MUST be local and bounded; users must be able to delete a run bundle completely. |
| SFAEF-180-005 | MUST | spec/180-data-privacy-and-retention.md | 23 | Remote telemetry or hosted review MUST be opt-in and disclose fields, purpose, processor, and retention. |
| SFAEF-180-006 | NORMATIVE | spec/180-data-privacy-and-retention.md | 25 | Cross-org evidence reuse is prohibited unless evidence is explicitly sanitized and reclassified. |
| SFAEF-180-007 | MUST | spec/180-data-privacy-and-retention.md | 27 | Benchmark artifacts MUST be scanned for secrets, customer identifiers, and proprietary data before contribution. |
| SFAEF-180-008 | MUST | spec/180-data-privacy-and-retention.md | 29 | Redaction MUST preserve enough structure to debug behavior and prove that the secret was removed. |
| SFAEF-190-001 | MUST | spec/190-release-and-conformance.md | 13 | Every run MUST record all available versions. |
| SFAEF-190-002 | NORMATIVE | spec/190-release-and-conformance.md | 15 | Breaking schema or semantic changes require a major version or explicit migration layer. |
| SFAEF-190-003 | MUST | spec/190-release-and-conformance.md | 17 | Generated adapters MUST declare the canonical definitions they were built from. |
| SFAEF-190-010 | MUST | spec/190-release-and-conformance.md | 30 | A V2 release candidate MUST include a valid requirement traceability matrix. |
| SFAEF-190-011 | MUST | spec/190-release-and-conformance.md | 32 | All P0 tests and applicable product thresholds MUST pass. |
| SFAEF-190-012 | MUST | spec/190-release-and-conformance.md | 34 | Any unrun live/host test MUST be explicit and blocks the corresponding qualification label. |
| SFAEF-190-013 | MUST | spec/190-release-and-conformance.md | 36 | The release bundle MUST be reproducible, checksum-protected, secret-scanned, and built from a clean commit. |
| SFAEF-190-014 | MUST | spec/190-release-and-conformance.md | 38 | Documentation MUST state actual host, Salesforce, model, and QA dates. |
| SFAEF-190-015 | MUST NOT | spec/190-release-and-conformance.md | 40 | Public claims MUST not exceed the weakest proven conformance profile. |
| SFAEF-190-020 | MUST | spec/190-release-and-conformance.md | 44 | Existing SfSkills users must retain a documented legacy path during V2 adoption. |
| SFAEF-190-021 | NORMATIVE | spec/190-release-and-conformance.md | 46 | Deprecation requires telemetry or evidence of low use where available, a replacement, migration instructions, and at least one compatibility release unless safety requires immediate removal. |
| SFAEF-200-001 | MUST | spec/200-governance-and-contribution.md | 9 | Material architectural decisions MUST be recorded as ADRs. |
| SFAEF-200-002 | MUST | spec/200-governance-and-contribution.md | 11 | A contribution that changes product behavior MUST identify affected requirements and scenarios. |
| SFAEF-200-003 | NORMATIVE | spec/200-governance-and-contribution.md | 13 | New skills require source governance and anti-pattern depth; new products require a user job, evidence path, output contract, and evaluation plan. |
| SFAEF-200-004 | NORMATIVE | spec/200-governance-and-contribution.md | 15 | New subagents require proof that isolated context improves quality or control. |
| SFAEF-200-005 | NORMATIVE | spec/200-governance-and-contribution.md | 17 | New MCP tools require threat analysis, permission class, bounded output, normalization, and adversarial tests. |
| SFAEF-200-006 | NORMATIVE | spec/200-governance-and-contribution.md | 19 | New schemas require an active consumer, validator, and compatibility plan. |
| SFAEF-200-007 | MUST | spec/200-governance-and-contribution.md | 21 | Scenario labels must be reviewed independently of the implementation under test. |
| SFAEF-210-001 | MUST | spec/210-commercial-and-ecosystem-strategy.md | 7 | A local user MUST be able to install, run a fixture, inspect evidence, and understand product limitations without a paid service. |
| SFAEF-210-002 | SHOULD | spec/210-commercial-and-ecosystem-strategy.md | 9 | Core result formats and benchmark methodology SHOULD remain portable and inspectable. |
| SFAEF-210-010 | MUST NOT | spec/210-commercial-and-ecosystem-strategy.md | 15 | Paid services MUST not weaken local safety or hide the basis of product claims. |
| SFAEF-210-011 | SHOULD | spec/210-commercial-and-ecosystem-strategy.md | 17 | Enterprise features SHOULD extend identity, collaboration, scale, support, and compliance rather than make local diagnoses intentionally unreliable. |
| SFAEF-210-020 | SHOULD | spec/210-commercial-and-ecosystem-strategy.md | 21 | Integrations with Salesforce, Gearset, Copado, Flosum, Provar, Elements, Salto, and other systems SHOULD use documented APIs/exports and preserve provenance. |
| SFAEF-210-021 | SHOULD | spec/210-commercial-and-ecosystem-strategy.md | 23 | SfSkills SHOULD publish a stable evidence/run export so other tools can consume findings without adopting the entire runtime. |
| SFAEF-210-022 | MUST | spec/210-commercial-and-ecosystem-strategy.md | 25 | A partner adapter MUST declare which product guarantees it enforces and pass conformance tests. |
| SFAEF-210-030 | NORMATIVE | spec/210-commercial-and-ecosystem-strategy.md | 29 | Public marketplace publication, open-standard branding, or claims of open-source compatibility require an explicit license ADR. |
| SFAEF-220-001 | MAY | spec/220-roadmap-and-exit-criteria.md | 65 | A milestone may continue autonomously only when its deterministic gates pass and no P0 safety ambiguity exists. |
| SFAEF-220-002 | MUST | spec/220-roadmap-and-exit-criteria.md | 67 | A P0 failure, credential ambiguity, non-disposable org uncertainty, or specification contradiction MUST stop execution and produce a failure review package. |
| SFAEF-220-003 | MUST | spec/220-roadmap-and-exit-criteria.md | 69 | Local commits and milestone tags MUST isolate review ranges even when one branch carries the full build. |
