# SFAEF-020 — Design principles: the product constitution

These principles are binding. They are not branding language.

## P1 — Start with a user job

SFAEF-020-001. Every product primitive MUST be justified by a concrete user job and observed implementation need.

Do not build a generalized workflow engine, registry, or agent marketplace merely because one may be useful later. Build it only after at least two products require the same behavior and the shared abstraction reduces verified complexity.

## P2 — Evidence beats confidence

SFAEF-020-010. Confidence MUST be derived from evidence coverage, source authority, freshness, contradictions, and execution completeness—not model tone.

SFAEF-020-011. A high-confidence statement without valid evidence is a defect.

SFAEF-020-012. “Unknown” is preferable to an unsupported answer.

## P3 — Context is a budget

SFAEF-020-020. The context window MUST be treated as scarce working memory, not a document store.

SFAEF-020-021. Relevant context MUST be selected, ordered, deduplicated, measured, and released between jobs.

SFAEF-020-022. A larger context window MUST NOT be used as the primary remedy for poor selection.

## P4 — Progressive disclosure

SFAEF-020-030. Hosts SHOULD discover compact skill metadata first, load instructions only on activation, and load references/scripts only when required.

SFAEF-020-031. Product knowledge MUST be decomposed into core and conditional context packs.

## P5 — Agents are roles, not inventory

SFAEF-020-040. A host-native subagent MUST have one clear responsibility, a bounded input, a bounded output, and a reason to need isolated context.

SFAEF-020-041. Existing specialist agents SHOULD remain catalog capabilities unless isolated execution materially improves quality.

SFAEF-020-042. Do not expose dozens of overlapping agents and call that orchestration.

## P6 — Structured handoffs, never transcript passing

SFAEF-020-050. Agents MUST pass facts, evidence references, hypotheses, unknowns, and metrics—not complete hidden reasoning or raw transcripts.

SFAEF-020-051. Every handoff MUST validate against `schemas/handoff.schema.json`.

## P7 — Thin model, thick system

SFAEF-020-060. Deterministic code MUST own parsing, schema validation, identifiers, normalization, pagination, redaction, policy classification, state transitions, and hard grading.

SFAEF-020-061. Models SHOULD own interpretation, synthesis, prioritization, and explanation within those boundaries.

## P8 — Product tools are read-only

SFAEF-020-070. Ordinary product tools MUST NOT mutate Salesforce.

SFAEF-020-071. Controlled mutation MAY occur only in disposable QA setup code that is not exposed to product agents and is deleted after the scenario.

## P9 — Local project inspection is optional enrichment

SFAEF-020-080. The framework MUST NOT assume the SfSkills repository is the Salesforce project.

SFAEF-020-081. Project discovery order MUST be explicit path, active workspace, bounded roots, then standalone.

SFAEF-020-082. Multiple candidate projects MUST produce `ambiguous`, never an arbitrary selection.

## P10 — Host capability honesty

SFAEF-020-090. Each host adapter MUST declare what it can actually enforce: subagent isolation, MCP access, hooks, compaction events, local execution, and human approval.

SFAEF-020-091. A local safety guarantee MUST NOT be advertised as a cloud guarantee when the host lacks the required hook.

## P11 — Independent challenge

SFAEF-020-100. Consequential product outputs MUST receive an independent evidence review before `completed` status.

SFAEF-020-101. The reviewer MUST be able to downgrade status or confidence and MUST not merely restate the draft.

## P12 — Replay over anecdote

SFAEF-020-110. Every qualified run MUST be reproducible from a redacted run bundle or explicitly marked non-replayable with a reason.

SFAEF-020-111. Product quality MUST be measured on versioned scenarios and real host behavior, not screenshots alone.

## P13 — Safe failure

SFAEF-020-120. Every product MUST define `completed`, `partial`, `refused`, and `failed` states.

SFAEF-020-121. Silent truncation, silent substitution, silent project/org selection, and silent evidence loss are prohibited.

## P14 — Claims are data

SFAEF-020-130. Material claims MUST have stable IDs and typed support links.

SFAEF-020-131. Contradictory evidence MUST remain visible; the system must not erase it during summarization.

## P15 — Currency is a product feature

SFAEF-020-140. Salesforce platform guidance MUST carry source provenance and review dates.

SFAEF-020-141. Release-sensitive claims MUST be tested against current official sources and compatibility fixtures.

## P16 — Measure outcomes, not catalog size

SFAEF-020-150. North-star metrics MUST emphasize successful, evidenced user outcomes, time to resolution, unsupported-claim rate, and repeat use.

Skill count, agent count, and tool count are inventory metrics, not product success.

## P17 — Interoperate before replacing

SFAEF-020-160. The framework SHOULD complement Salesforce, Gearset, Copado, Elements, Salto, and other delivery systems through portable evidence and adapters rather than pretending to replace their mature pipeline, graph, or deployment capabilities immediately.

## P18 — Specifications must earn complexity

SFAEF-020-170. The specification MUST remain implementable. Every new mandatory object or layer requires a consumer, validator, and test.

A schema with no execution path is not architecture; it is backlog.
