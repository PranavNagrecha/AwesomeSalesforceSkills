# Agentforce Builder — Gated Execution Protocol

This file defines the five gates every agentforce-builder run MUST pass before its output is treated as a deliverable. Enforced mechanically by `scripts/run_builder.py` via `scripts/builder_plugins/agentforce.py`. The AGENT.md narrative describes *what* the builder does; this file defines *how a run is graded*.

A run that skips a gate is not a run — it is a hallucination.

---

## Gate A — Input readiness (Q&A)

**Enforced by:** `scripts/run_builder.py --stage inputs`
**Pass condition:** inputs validate against `agents/agentforce-builder/inputs.schema.json` AND `feature_summary` ≥10 words AND the conditional in `AgentforceBuilderPlugin.additional_input_checks` passes:

| Trigger | Follow-up required |
|---|---|
| `emit_agent_spec == true` | `agent_name` |

Hard cap: two rounds of Q&A. Missing after round two ⇒ `REFUSAL_INPUT_AMBIGUOUS`.

---

## Gate A.5 — Requirements document

**Enforced by:** `scripts/run_builder.py --stage requirements`
**Pass condition:** the harness renders `REQUIREMENTS_TEMPLATE.md` from the validated inputs (via `AgentforceBuilderPlugin.requirements_template_vars`) and writes it to `docs/reports/agentforce-builder/<run_id>/REQUIREMENTS.md`. Explicit approval (hashed) is required before Gate B runs.

---

## Gate B — Ground every symbol

**Enforced by:** `scripts/run_builder.py --stage ground`
**Pass condition:** `primary_object`, every `referenced_field`, the action class name (must NOT already exist in the target org under this name), and every template + skill citation resolve against stub / repo. More than one unresolved symbol ⇒ `REFUSAL_UNGROUNDED_OUTPUT`.

---

## Gate C — Build and self-test

**Enforced by:** `scripts/run_builder.py --stage build` via `AgentforceBuilderPlugin.static_check` + `AgentforceBuilderPlugin.live_check`.

**Static check:**

- **Apex action class (`*.cls`, not ending `Test.cls`):**
    - Class declaration present; balanced braces/parens.
    - `@InvocableMethod` annotation is present.
    - Method signature matches `public static List<Response> <name>(List<Request> requests)`.
    - Inner `class Request` and `class Response` are both defined.
    - At least one `@InvocableVariable` annotation — Request/Response fields must be documented so the planner can reason about them.
- **Apex test class (`*Test.cls`):**
    - `@IsTest` annotation is present.
- **Agent spec JSON (optional, when `emit_agent_spec=true`):**
    - Parses as JSON.
    - `agent.{name,label,description,persona,topics,guardrails.trustLayer,evaluation.{testUtterances,minAccuracy}}` all present.
    - `agent.topics` is a non-empty array; each topic has a `name` and a non-empty `actions` array.
    - `agent.guardrails.trustLayer` includes `maskPII`, `blockToxicity`, `preventPromptInjection`.

**Live check:** `sf project deploy validate --target-org <alias>` over the emitted `.cls` files (with generated `-meta.xml`). The `.json` spec is NOT metadata and is never deployed.

**Confidence tiers:** HIGH iff static green + live green + coverage ≥85%; MEDIUM iff static green + live skipped + coverage ≥75%; LOW otherwise.

---

## Gate D — Envelope seal

**Enforced by:** `scripts/run_builder.py --stage seal`
**Pass condition:** envelope validates against the shared schema; every citation resolves; confidence is computed from the earlier gates, not self-declared.

---

## What this protocol is NOT

- Not an agent simulator. `/review-agentforce-action` grades the action's topic placement and eval cases after the fact; this builder produces it.
- Not a deploy tool. Gate C's deploy-validate is check-only.
