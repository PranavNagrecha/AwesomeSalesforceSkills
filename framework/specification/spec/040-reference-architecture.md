# SFAEF-040 — Reference architecture and trust boundaries

## Architectural objective

The framework separates probabilistic reasoning from deterministic control. It does not centralize every capability in one runtime; it defines portable contracts and lets thin host adapters implement them.

## Eight planes

### 1. Experience plane

Commands, product entrypoints, reports, and developer UX.

### 2. Agent plane

Focused roles that interpret evidence and knowledge. Product agents never directly gain broader authority than their declared tools.

### 3. Context plane

Selection, ordering, budget enforcement, summaries, checkpoints, and rehydration.

### 4. Knowledge plane

SfSkills packages, references, templates, release-sensitive sources, and retrieval indexes.

### 5. Evidence plane

Normalized observations from orgs, projects, jobs, test runs, static analyzers, and supplied fixtures.

### 6. Control plane

Typed inputs, execution modes, state transitions, host capabilities, permission policy, org/project identity, and status.

### 7. Quality plane

Schema validation, evidence lint, independent review, benchmarks, security tests, and behavioral QA.

### 8. Adapter plane

Cursor, Claude Code, VS Code/Copilot, Agentforce Vibes, portable Agent Plugins, and future A2A services.

## Required components

SFAEF-040-001. A conforming implementation MUST separate canonical product contracts from host-generated artifacts.

SFAEF-040-002. Product agents MUST access Salesforce evidence only through an evidence broker or an equivalently enforced adapter.

SFAEF-040-003. The evidence broker MUST validate inputs, pin target identity, enforce permissions, normalize output, redact secrets, assign evidence IDs, and report truncation.

SFAEF-040-004. The context compiler MUST consume product policy, agent contract, selected knowledge, normalized evidence, and host budget to create a stage-specific context manifest.

SFAEF-040-005. The claim/evidence graph MUST exist outside the final prose and remain machine-validatable.

SFAEF-040-006. Independent evidence review MUST use a context isolated from the drafting agent's hidden transcript.

SFAEF-040-007. Run artifacts MUST remain replayable without requiring the original chat transcript whenever source licensing and privacy permit.

## Trust boundaries

1. **User and host** — user intent and explicit approvals.
2. **Model boundary** — model output is untrusted until validated.
3. **Knowledge boundary** — skill guidance is advisory, not proof of target state.
4. **Tool boundary** — tool output is untrusted data that may contain prompt injection, secrets, or malformed fields.
5. **Org boundary** — every Salesforce observation is bound to an org identity and time.
6. **Project boundary** — local project evidence is bound to an explicit path and digest.
7. **QA authority boundary** — scratch setup authority is separate from product authority.
8. **Host boundary** — guarantees depend on actual host capabilities.

SFAEF-040-020. Crossing a trust boundary MUST produce a typed, validated object or an explicit refusal/error.

SFAEF-040-021. No downstream component may silently upgrade advisory or inferred data to observed fact.

## Deployment topology

The core SHOULD support:

- local single-user execution;
- team/shared policy with local models or hosts;
- enterprise evidence gateway;
- offline fixture/replay execution;
- protected CI/scratch-org QA.

SFAEF-040-030. Networked deployment MUST preserve the same evidence, permission, and run contracts as local execution.
