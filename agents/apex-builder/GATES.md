# Apex Builder — Gated Execution Protocol

This file defines the five gates every apex-builder run MUST pass before its output is treated as a deliverable. The structure mirrors `agents/_shared/AGENT_CONTRACT.md` but is enforced mechanically by `scripts/run_builder.py`. The AGENT.md narrative describes *what* the builder does; this file defines *how a run is graded*.

A run that skips a gate is not a run — it is a hallucination.

---

## Gate A — Input readiness (Q&A)

**Enforced by:** `scripts/run_builder.py --stage inputs`
**Pass condition:** the caller's input packet validates against `agents/apex-builder/inputs.schema.json`.

On failure the harness emits a machine-readable question block — every missing `required` field, every invalid enum, every conditional field that was triggered but not filled. The caller answers the questions as a batch. The harness re-validates.

Hard cap: **two rounds of Q&A.** After round two the harness emits the residual ambiguities as assumptions and requires an `--approved` flag on the next invocation. If the flag is absent, the run refuses with `REFUSAL_INPUT_AMBIGUOUS` — no code is written.

Inputs that require a conditional follow-up:

| Trigger | Follow-up required |
|---|---|
| `kind in {trigger, selector, domain, batch, cdc_subscriber}` | `primary_sobject` |
| `sharing_mode == without_sharing` | `business_justification` (≥40 chars) |
| `kind in {batch, queueable, schedulable, platform_event_subscriber, cdc_subscriber, continuation}` | `async_hint` (defaults applied if absent) |

---

## Gate A.5 — Requirements document

**Enforced by:** `scripts/run_builder.py --stage requirements`
**Pass condition:** the harness renders `REQUIREMENTS_TEMPLATE.md` populated from the validated inputs and writes it to `docs/reports/apex-builder/<run_id>/REQUIREMENTS.md`. The caller must explicitly approve it before Gate B runs.

Approval happens one of two ways:

1. **Interactive** — the caller reads the file, then re-invokes the harness with `--stage build --approved-requirements <path>`. The harness hashes the file; if the hash has changed since emission, the approval is rejected and the caller must regenerate.
2. **Automation** — an eval fixture or CI invocation supplies `--auto-approve-requirements` with an accompanying SHA256 in `expected_requirements_sha256`. Hash mismatch = P0 fixture fail.

The requirements document is the **anchor** for the rest of the run. Any deviation Gate C detects from the approved requirements surfaces as a finding with severity P0 and drops confidence to LOW.

---

## Gate B — Ground every symbol

**Enforced by:** `scripts/run_builder.py --stage ground`
**Pass condition:** every custom SObject, field, Apex class, Named Credential, or Connected App that the requirements document references resolves against one of:

1. A live `describe_org` / `list_custom_objects` / `get_apex_class` response cached for this run under `docs/reports/apex-builder/<run_id>/probes/`.
2. A fixture `org_stub` block (in eval mode).
3. A file that exists under `repo_path` (for intra-project references).

Any unresolved symbol is recorded in the envelope's `grounding.unresolved[]` array. **More than one unresolved symbol is a refusal (`REFUSAL_UNGROUNDED_OUTPUT`)**, not a warning. One unresolved symbol downgrades confidence to `LOW` and requires a `// UNKNOWN: …` marker in the emitted code.

Skill / template / decision-tree citations resolve here too: if a cited path does not exist, the citation is stripped and confidence drops at least one tier.

---

## Gate C — Build and self-test

**Enforced by:** `scripts/run_builder.py --stage build`
**Pass condition (HIGH):** every emitted `.cls` and `.trigger` passes `sf apex parse` with no errors, AND `sf project deploy validate` returns a successful check-only against `target_org_alias`, AND the emitted test class runs with ≥85% coverage on the new classes.

**Pass condition (MEDIUM):** parse is clean but deploy-validate is skipped (no `target_org_alias`) or coverage is 75–84%.

**Fail conditions:**

- Parse returns any error → iterate up to 3 times, feeding each error back to the generator. After the third failure, emit a skeleton with `// UNKNOWN:` markers in place of the failing region and force `confidence: LOW`.
- Deploy-validate returns compile errors from the target org (e.g., missing field the requirements claimed existed) → Gate B is retroactively failed and the run refuses with `REFUSAL_UNGROUNDED_OUTPUT`.
- Coverage < 75% → the test class is regenerated once with an explicit prompt to cover named uncovered methods; second failure forces `confidence: LOW`.

The harness keeps **every** intermediate attempt under `docs/reports/apex-builder/<run_id>/attempts/<n>/` so the iteration is auditable.

---

## Gate D — Envelope seal

**Enforced by:** `scripts/run_builder.py --stage seal`
**Pass condition:** the produced envelope validates against `agents/_shared/schemas/output-envelope.schema.json` AND every field in `citations[]` resolves to a real path / tool name AND `confidence` is computed from the Gate B + Gate C results, not self-declared.

The computed-confidence rule is:

| Gate B unresolved | Gate C parse | Gate C deploy-validate | Gate C coverage | → confidence |
|---|---|---|---|---|
| 0 | green | green | ≥85% | HIGH |
| 0 | green | skipped | ≥75% | MEDIUM |
| 1 | green | any | any | LOW |
| ≥2 | any | any | any | **REFUSAL** |
| any | red after 3 iter | any | any | LOW + skeleton-only |

Self-declared HIGH with failing Gate B or C is a structural error — the harness overwrites the claimed value with the computed value and adds a `confidence_rationale` explaining the override.

---

## Invocation summary

```bash
# Round 1: submit an input packet; harness returns the question block if incomplete
python3 scripts/run_builder.py \
    --agent apex-builder \
    --inputs path/to/inputs.json \
    --stage inputs

# Round 2 (after answering): requirements doc is rendered
python3 scripts/run_builder.py \
    --agent apex-builder \
    --inputs path/to/inputs.json \
    --stage requirements \
    --run-id <stem>

# Round 3: after the caller approves REQUIREMENTS.md
python3 scripts/run_builder.py \
    --agent apex-builder \
    --inputs path/to/inputs.json \
    --stage ground \
    --run-id <stem> \
    --approved-requirements docs/reports/apex-builder/<stem>/REQUIREMENTS.md

# Gate C: after the generator produced .cls files
python3 scripts/run_builder.py \
    --agent apex-builder \
    --inputs path/to/inputs.json \
    --stage build \
    --run-id <stem> \
    --emitted-dir docs/reports/apex-builder/<stem>/emitted/

# Gate D: seal the envelope
python3 scripts/run_builder.py \
    --agent apex-builder \
    --inputs path/to/inputs.json \
    --stage seal \
    --run-id <stem>
```

For CI / eval fixtures, `--fixture path/to/fixture.yaml` runs all five gates against a canned input packet + `org_stub`, skipping interactive prompts.

---

## What this protocol is NOT

- Not a replacement for `evals/agents/scripts/run_agent_evals.py`. That tool grades envelopes after they are produced; this one is what produces them.
- Not model-specific. Any LLM that can follow `AGENT.md` can drive the gates; the harness is the model's compiler.
- Not a deploy tool. Gate C's deploy-validate is a check-only call (`sf project deploy validate`); no metadata is written to the org.
