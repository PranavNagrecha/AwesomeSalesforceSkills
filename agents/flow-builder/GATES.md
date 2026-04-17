# Flow Builder — Gated Execution Protocol

This file defines the five gates every flow-builder run MUST pass before its output is treated as a deliverable. The structure mirrors `agents/_shared/AGENT_CONTRACT.md` but is enforced mechanically by `scripts/run_builder.py` via `scripts/builder_plugins/flow.py`. The AGENT.md narrative describes *what* the builder does; this file defines *how a run is graded*.

A run that skips a gate is not a run — it is a hallucination.

---

## Gate A — Input readiness (Q&A)

**Enforced by:** `scripts/run_builder.py --stage inputs`
**Pass condition:** the caller's input packet validates against `agents/flow-builder/inputs.schema.json` AND every agent-specific conditional (implemented in `FlowBuilderPlugin.additional_input_checks`) is satisfied AND `feature_summary` has ≥10 words.

Inputs that require a conditional follow-up:

| Trigger | Follow-up required |
|---|---|
| `flow_type in {record-triggered, platform-event-triggered}` | `trigger_sobject` |
| `flow_type == record-triggered` | `record_trigger_type` (Create/Update/CreateAndUpdate/Delete) |

On failure the harness emits a machine-readable question block. The caller answers the questions as a batch. The harness re-validates.

Hard cap: **two rounds of Q&A.** After round two the harness emits the residual ambiguities as assumptions and requires an `--approved` flag on the next invocation. If the flag is absent, the run refuses with `REFUSAL_INPUT_AMBIGUOUS` — no XML is written.

---

## Gate A.5 — Requirements document

**Enforced by:** `scripts/run_builder.py --stage requirements`
**Pass condition:** the harness renders `REQUIREMENTS_TEMPLATE.md` populated from the validated inputs (via `FlowBuilderPlugin.requirements_template_vars`) and writes it to `docs/reports/flow-builder/<run_id>/REQUIREMENTS.md`. The caller must explicitly approve it before Gate B runs.

Approval happens one of two ways:

1. **Interactive** — the caller reads the file, then re-invokes the harness with `--stage build --approved-requirements <path>`. The harness hashes the file; if the hash has changed since emission, the approval is rejected and the caller must regenerate.
2. **Automation** — an eval fixture or CI invocation supplies `--auto-approve-requirements`.

The requirements document is the **anchor** for the rest of the run. Any deviation Gate C detects from the approved requirements surfaces as a finding with severity P0 and drops confidence to LOW.

---

## Gate B — Ground every symbol

**Enforced by:** `scripts/run_builder.py --stage ground`
**Pass condition:** every `trigger_sobject`, `referenced_field`, subflow developer name, template path, and skill citation the requirements document references resolves against one of:

1. A live `describe_org` / `describe_sobject` response cached for this run under `docs/reports/flow-builder/<run_id>/probes/`.
2. A fixture `org_stub` block (in eval mode).
3. A file that exists under the repo (for template + skill paths).

Any unresolved symbol is recorded in the envelope's `grounding.unresolved[]` array. **More than one unresolved symbol is a refusal (`REFUSAL_UNGROUNDED_OUTPUT`)**, not a warning. One unresolved symbol downgrades confidence to `LOW` and requires an `// UNKNOWN: …` marker in a description field.

---

## Gate C — Build and self-test

**Enforced by:** `scripts/run_builder.py --stage build` via `FlowBuilderPlugin.static_check` + `FlowBuilderPlugin.live_check`.

**Static check (always runs):**

- Every emitted `.flow-meta.xml` must parse as well-formed XML with root `<Flow>`.
- `<processType>` must be present and non-empty.
- `<apiVersion>` must match the `\d{2}\.0` pattern.
- `<status>` must be one of `Active`, `Draft`, `Obsolete`, `InvalidDraft`.
- When the flow is record-triggered (AutoLaunchedFlow + `<recordTriggerType>`): `<start>` must contain `<object>` and `<triggerType>`.
- Every `<recordCreates>`, `<recordUpdates>`, `<recordDeletes>`, `<recordLookups>`, `<actionCalls>` MUST declare a `<faultConnector>`. Unhandled failure paths are a hard static error.

**Live check (when `target_org_alias` is supplied):**

`sf project deploy validate --target-org <alias> --source-dir <tmp>/force-app --json --wait 10` runs against a temp SFDX project that places each emitted flow under `force-app/main/default/flows/`. The Flow compiler enforces SObject + field correctness, subflow resolution, and API-version compatibility.

**Pass condition (HIGH):** zero static errors AND `success: true` from deploy-validate with zero component errors.

**Pass condition (MEDIUM):** zero static errors AND deploy-validate skipped.

**Fail conditions:**

- Any static error → iterate up to 3 times, feeding each error back to the generator. After the third failure, force `confidence: LOW` and emit skeleton-only.
- Deploy-validate returns `success: false` (missing fields, invalid subflow reference) → Gate B is retroactively failed and the run refuses with `REFUSAL_UNGROUNDED_OUTPUT`.
- Top-level sf CLI error → Gate C fails; the CLI error message is surfaced.

The harness keeps every intermediate attempt under `docs/reports/flow-builder/<run_id>/attempts/<n>/` so the iteration is auditable.

---

## Gate D — Envelope seal

**Enforced by:** `scripts/run_builder.py --stage seal`
**Pass condition:** the produced envelope validates against `agents/_shared/schemas/output-envelope.schema.json` AND every field in `citations[]` resolves to a real path / tool name AND `confidence` is computed from the Gate B + Gate C results, not self-declared.

The computed-confidence rule is:

| Gate B unresolved | Gate C static | Gate C live | → confidence |
|---|---|---|---|
| 0 | green | green | HIGH |
| 0 | green | skipped | MEDIUM |
| 1 | green | any | LOW |
| ≥2 | any | any | **REFUSAL** |
| any | red after 3 iter | any | LOW + skeleton-only |

Self-declared HIGH with failing Gate B or C is a structural error — the harness overwrites the claimed value with the computed value.

---

## Invocation summary

```bash
python3 scripts/run_builder.py --agent flow-builder \
    --fixture evals/agents/fixtures/flow-builder/<case>.yaml \
    --emitted-dir <path-to-emitted-flows>
```

---

## What this protocol is NOT

- Not a Flow Trigger Explorer replacement. Gate C doesn't enumerate every record-triggered flow on the SObject — that's `/analyze-flow`'s job.
- Not a deploy tool. Gate C's deploy-validate is a check-only call.
