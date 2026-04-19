# Capability Matrix — Advisory vs Harness mode per builder agent

Every builder agent can be invoked two ways. The matrix below tells you **what you lose** when you use chat / MCP instead of the CLI harness.

## Why this exists

The Cursor 2026-04-19 review (see `feedback/FEEDBACK_LOG.md`) flagged that users can't tell at a glance which guarantees they get from which path. This doc closes that gap.

## Two invocation paths

### Advisory mode
- **How:** a human (or AI IDE) reads `agents/<id>/AGENT.md` directly, possibly via MCP `get_agent("<id>")`, and asks the model to follow it.
- **Enforced by:** the model's diligence. No code-level gate.
- **Output:** a report in chat, optionally persisted via `--no-persist=false` discipline.

### Harness mode
- **How:** `python3 scripts/run_builder.py --agent <id> --inputs inputs.json [--approved-requirements REQUIREMENTS.md]`
- **Enforced by:** `scripts/run_builder.py` + the agent's plugin under `scripts/builder_plugins/<id>.py`.
- **Output:** a sealed envelope JSON + human-readable report, plus (if live org available) a `sf project deploy validate` result.

---

## Capability matrix (builder agents)

| Agent | Gate A: input schema | Gate A.5: requirements approval | Gate B: grounding | Gate C static | Gate C live-org validate | Gate D: envelope seal | Limit-smell / bulkification static checks | Automation-graph preflight | Flow Test emission |
|---|---|---|---|---|---|---|---|---|---|
| `flow-builder` (Advisory) | advisory only | advisory only | advisory only | advisory only | advisory only | advisory only | advisory only | **DOCUMENTED** Step 0 (2026-04-19) | advisory only |
| `flow-builder` (Harness) | ✅ plugin + schema | ✅ requires `REQUIREMENTS.md` | ✅ SObject+fields describe | ✅ XML + fault-connector checks | ✅ if `target_org_alias` | ✅ | ✅ **NEW** loop-with-DML / nested-loops / N+1 subflow (2026-04-19) | advisory only (probe is documented, not plugin-enforced yet) | DEFER (2026-Q3) |
| `apex-builder` (Advisory) | advisory | advisory | advisory | advisory | advisory | advisory | advisory | advisory | n/a |
| `apex-builder` (Harness) | ✅ | ✅ | ✅ class+field grounding | ✅ Apex parser, test-coverage | ✅ if org | ✅ | partial (no SOQL-in-loop detector yet — DEFER) | advisory | n/a |
| `lwc-builder` (Advisory) | advisory | advisory | advisory | advisory | advisory | advisory | advisory | n/a | n/a |
| `lwc-builder` (Harness) | ✅ | ✅ | ✅ | ✅ | ✅ if org | ✅ | advisory | n/a | n/a |
| `agentforce-builder` (Advisory) | advisory | advisory | advisory | advisory | advisory | advisory | advisory | n/a | n/a |
| `agentforce-builder` (Harness) | ✅ | ✅ | ✅ | ✅ | ✅ if org | ✅ | advisory | n/a | n/a |
| `integration-catalog-builder` (Advisory) | advisory | advisory | advisory | advisory | advisory | advisory | n/a | n/a | n/a |
| `integration-catalog-builder` (Harness) | ✅ | ✅ | ✅ NC grounding | ✅ JSON schema | ✅ NC resolve | ✅ | n/a | n/a | n/a |
| `changeset-builder` (Advisory) | advisory | advisory | advisory | advisory | advisory | advisory | n/a | n/a | n/a |
| `changeset-builder` (Harness) | ✅ | ✅ | ✅ component grounding | ✅ | ✅ if org | ✅ | n/a | n/a | n/a |
| `pb-to-flow` (Advisory) | advisory | advisory | advisory | advisory | advisory | advisory | n/a | **partial — uses automation-graph probe implicitly for source discovery** | n/a |
| `pb-to-flow` (Harness) | ✅ | ✅ | ✅ | ✅ | ✅ if org | ✅ | n/a | ✅ (discovery step) | n/a |
| **All 6 skill-builders** | Advisory + Harness both use the same 5-gate protocol; Advisory is effectively equivalent because the plugin runs as a library module. No meaningful delta. | | | | | | | | |

Legend: ✅ = code-enforced; advisory = documented in AGENT.md, relies on the model. Empty = not applicable.

---

## What Advisory mode loses

The most commonly-cited gaps when users skip the harness:

1. **Input-readiness gate.** Advisory can run with a 3-word `feature_summary`; Gate A refuses.
2. **Requirements approval.** Advisory generates directly; harness requires a human-approved `REQUIREMENTS.md` with a matching hash.
3. **Grounding.** Advisory trusts the model to check field/object existence; harness verifies against live describe.
4. **Static checks.** Advisory's XML / Apex / JSON can be shaped but unvalidated; harness parses and enforces.
5. **Live-org validate.** Advisory can claim "will compile in your org"; harness runs `sf project deploy validate` and uses the result.
6. **Envelope seal.** Advisory produces free-form output; harness produces a sealed JSON envelope matching `output-envelope.schema.json`.

**If you're shipping to production, use the harness.** If you're sketching / exploring / teaching, Advisory is fine.

---

## Where to add next

(per `feedback/FEEDBACK_LOG.md#2026-04-19`)

- Wire the automation-graph probe as an **optional** Gate B.5 in `flow-builder` and `apex-builder`. Status: probe doc shipped 2026-04-19; plugin wiring DEFERRED until real-user signal on thresholds.
- Extend the limit-smell pattern to `apex-builder`: SOQL-in-loop, DML-in-loop, missing `Database.setSavepoint()` on multi-object transactions. Status: DEFERRED (next sprint).
- Flow Test metadata emission in `flow-builder` Harness. Status: DEFERRED until Summer '26 release notes confirm stable API.

---

## How to cite this matrix

If your AGENT.md references a mode-specific capability, link here. The top of each builder's AGENT.md gets a one-line banner:

> **Advisory vs Harness mode:** this agent runs both ways — see `agents/_shared/CAPABILITY_MATRIX.md` for what each mode enforces.
