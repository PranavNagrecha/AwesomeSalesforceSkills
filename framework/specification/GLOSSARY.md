# Glossary

**Adapter** — Host-specific translation of portable framework contracts into Cursor, Claude Code, VS Code/Copilot, Agentforce Vibes, or another environment.

**Behaviorally qualified** — A product that passes known-truth scenarios using the actual host, selected skill contents, normalized evidence path, and disposable Salesforce QA environment where applicable.

**Claim** — A material statement in a product result with a stable ID and typed support relationships to evidence.

**Context checkpoint** — Minimal persisted state needed to resume after compaction or a host restart without replaying the full conversation.

**Context manifest** — Ordered list of control instructions, selected knowledge, evidence summaries, and output reserve assembled for one execution stage.

**Evidence** — A normalized observation with provenance, source type, timestamp, org/project association, integrity digest, and visibility classification.

**Evidence broker** — Deterministic policy and normalization layer between agents and upstream MCP/CLI/API tools.

**Host capability** — A feature a host can actually provide, such as isolated subagents, MCP access, shell hooks, compaction notification, or human approval.

**Knowledge plane** — Existing SfSkills packages, official references, release notes, templates, and source governance.

**Material claim** — A claim that affects diagnosis, risk, priority, safety, or recommended action.

**Product tool** — Read-only evidence operation available during ordinary user execution.

**QA setup authority** — Separate, guarded code allowed to mutate only disposable scratch-org scenarios; never available as a model tool.

**Run bundle** — Redacted, replayable local artifact containing inputs, plans, context manifests, normalized evidence, handoffs, claims, review, telemetry, and output.

**SFAEF** — Salesforce AI Engineering Framework specification namespace.

**Standalone mode** — Execution without a local Salesforce project or live org, using knowledge and supplied fixtures only.

**Structured handoff** — Validated facts, evidence references, hypotheses, unknowns, and metrics passed between roles without a full transcript.
