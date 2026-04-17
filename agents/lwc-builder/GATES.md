# LWC Builder — Gated Execution Protocol

This file defines the five gates every lwc-builder run MUST pass before its output is treated as a deliverable. The structure mirrors `agents/_shared/AGENT_CONTRACT.md` but is enforced mechanically by `scripts/run_builder.py` via `scripts/builder_plugins/lwc.py`. The AGENT.md narrative describes *what* the builder does; this file defines *how a run is graded*.

A run that skips a gate is not a run — it is a hallucination.

---

## Gate A — Input readiness (Q&A)

**Enforced by:** `scripts/run_builder.py --stage inputs`
**Pass condition:** the caller's input packet validates against `agents/lwc-builder/inputs.schema.json` AND every agent-specific conditional (implemented in `LwcBuilderPlugin.additional_input_checks`) is satisfied AND `feature_summary` has ≥10 words.

Inputs that require a conditional follow-up:

| Trigger | Follow-up required |
|---|---|
| `data_shape in {record-form, list-view, search}` | `target_objects` (≥1 SObject) |
| `emit_controller == true` | `controller_class_name`, `controller_methods` (≥1) |
| `binding_kind == record-page` | `public_api` must include `recordId` |

On failure the harness emits a machine-readable question block. The caller answers the questions as a batch. The harness re-validates.

Hard cap: **two rounds of Q&A.** After round two the harness emits the residual ambiguities as assumptions and requires an `--approved` flag on the next invocation. If the flag is absent, the run refuses with `REFUSAL_INPUT_AMBIGUOUS` — no code is written.

---

## Gate A.5 — Requirements document

**Enforced by:** `scripts/run_builder.py --stage requirements`
**Pass condition:** the harness renders `REQUIREMENTS_TEMPLATE.md` populated from the validated inputs (via `LwcBuilderPlugin.requirements_template_vars`) and writes it to `docs/reports/lwc-builder/<run_id>/REQUIREMENTS.md`. The caller must explicitly approve it before Gate B runs.

Approval happens one of two ways:

1. **Interactive** — the caller reads the file, then re-invokes the harness with `--stage build --approved-requirements <path>`. The harness hashes the file; if the hash has changed since emission, the approval is rejected and the caller must regenerate.
2. **Automation** — an eval fixture or CI invocation supplies `--auto-approve-requirements` with an accompanying SHA256 in `expected_requirements_sha256`. Hash mismatch = P0 fixture fail.

The requirements document is the **anchor** for the rest of the run. Any deviation Gate C detects from the approved requirements surfaces as a finding with severity P0 and drops confidence to LOW.

---

## Gate B — Ground every symbol

**Enforced by:** `scripts/run_builder.py --stage ground`
**Pass condition:** every `target_object`, `referenced_field`, template path, and skill citation the requirements document references resolves against one of:

1. A live `describe_org` / `describe_sobject` response cached for this run under `docs/reports/lwc-builder/<run_id>/probes/`.
2. A fixture `org_stub` block (in eval mode).
3. A file that exists under the repo (for template + skill paths).

Any unresolved symbol is recorded in the envelope's `grounding.unresolved[]` array. **More than one unresolved symbol is a refusal (`REFUSAL_UNGROUNDED_OUTPUT`)**, not a warning. One unresolved symbol downgrades confidence to `LOW` and requires a `// UNKNOWN: …` marker in the emitted code.

Skill / template / decision-tree citations are resolved here too: if a cited path does not exist, the citation is stripped and confidence drops at least one tier.

---

## Gate C — Build and self-test

**Enforced by:** `scripts/run_builder.py --stage build` via `LwcBuilderPlugin.static_check` + `LwcBuilderPlugin.live_check`.

**Static check (always runs):**

- Every bundle dir must contain matching `<bundle>.js`, `<bundle>.html`, and `<bundle>.js-meta.xml`.
- `<bundle>.js` must import `LightningElement` from `lwc`, must extend `LightningElement`, must `export default class`, must have balanced braces/parens, must NOT use raw `alert(…)` (use `LightningAlert` / `ShowToastEvent`).
- `<bundle>.html` must contain a root `<template>`; no `onclick` on non-interactive elements (`div`/`span`).
- `<bundle>.js-meta.xml` must parse as XML with root `<LightningComponentBundle>`.
- When `emit_controller=true`: every emitted `.cls` must have a class declaration AND at least one `@AuraEnabled` annotation (unless the class name ends in `Test.cls`).

**Live check (when `target_org_alias` is supplied):**

`sf project deploy validate --target-org <alias> --source-dir <tmp>/force-app --json --wait 10` runs against a temp SFDX project that mirrors the emitted bundle under `force-app/main/default/lwc/<bundleName>/` and copies any `.cls` files into `force-app/main/default/classes/` with generated `-meta.xml` siblings.

**Pass condition (HIGH):** zero static errors AND `success: true` from deploy-validate with zero component errors.

**Pass condition (MEDIUM):** zero static errors AND deploy-validate skipped (no `target_org_alias` supplied or sf CLI not on PATH).

**Fail conditions:**

- Any static error → iterate up to 3 times, feeding each error back to the generator. After the third failure, force `confidence: LOW` and emit skeleton-only.
- Deploy-validate returns `success: false` (missing fields, missing Apex controllers, bad wire adapter imports) → Gate B is retroactively failed and the run refuses with `REFUSAL_UNGROUNDED_OUTPUT`.
- Top-level sf CLI error (non-zero status with no `result`) → Gate C fails; the CLI error message is surfaced as a single error row.

The harness keeps **every** intermediate attempt under `docs/reports/lwc-builder/<run_id>/attempts/<n>/` so the iteration is auditable.

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

Self-declared HIGH with failing Gate B or C is a structural error — the harness overwrites the claimed value with the computed value and adds a `confidence_rationale` explaining the override.

---

## Invocation summary

```bash
# Round 1: submit an input packet; harness returns the question block if incomplete
python3 scripts/run_builder.py \
    --agent lwc-builder \
    --inputs path/to/inputs.json \
    --stage inputs

# Round 2: requirements doc is rendered
python3 scripts/run_builder.py \
    --agent lwc-builder \
    --inputs path/to/inputs.json \
    --stage requirements \
    --run-id <stem>

# Round 3: after the caller approves REQUIREMENTS.md
python3 scripts/run_builder.py \
    --agent lwc-builder \
    --inputs path/to/inputs.json \
    --stage ground \
    --run-id <stem> \
    --approved-requirements docs/reports/lwc-builder/<stem>/REQUIREMENTS.md

# Gate C: after the generator produced the LWC bundle
python3 scripts/run_builder.py \
    --agent lwc-builder \
    --inputs path/to/inputs.json \
    --stage build \
    --run-id <stem> \
    --emitted-dir docs/reports/lwc-builder/<stem>/emitted/

# Gate D: seal the envelope
python3 scripts/run_builder.py \
    --agent lwc-builder \
    --inputs path/to/inputs.json \
    --stage seal \
    --run-id <stem>
```

For CI / eval fixtures, `--fixture path/to/fixture.yaml --emitted-dir <...>` runs all five gates against a canned input packet + `org_stub`, skipping interactive prompts.

---

## What this protocol is NOT

- Not a replacement for `evals/agents/scripts/run_agent_evals.py`. That tool grades envelopes after they are produced; this one is what produces them.
- Not a Jest runner — Jest is part of the local dev loop (`npm test -- <bundle>`) but not a Gate C requirement because scratch orgs don't run it. If `include_tests=true` the emitted `__tests__/<bundle>.test.js` is checked for presence, not executed.
- Not a deploy tool. Gate C's deploy-validate is a check-only call (`sf project deploy validate`); no metadata is written to the org.
