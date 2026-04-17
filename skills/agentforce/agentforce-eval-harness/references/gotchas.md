# Gotchas — Agentforce Eval Harness

Non-obvious platform behaviors that cause production problems.

## Gotcha 1: Non-determinism in LLM responses breaks exact-match assertions

**What happens:** Case passes once, fails next run. Agent response varies because of temperature / sampling.

**When it occurs:** Assertions that require exact-text match with the reference answer.

**How to avoid:** Score via rubric + LLM-judge, not exact match. Exact-match only works for deterministic side-effects (tool-call names + args).

---

## Gotcha 2: LLM judges are biased toward longer responses

**What happens:** LLM judge scores verbose responses higher than concise-and-correct ones.

**When it occurs:** Rubric doesn't explicitly reward brevity or penalize redundancy.

**How to avoid:** Rubric clause: "A shorter response that's correct scores higher than a long response that adds filler. Penalize filler explicitly." Calibrate against human judgment regularly.

---

## Gotcha 3: Baseline scores drift when the underlying model version changes

**What happens:** Agentforce platform updates the underlying model. All baseline scores shift +/- 5% overnight.

**When it occurs:** Salesforce model refresh (quarterly or irregular).

**How to avoid:** Monitor per-run score distribution. If absolute scores drift beyond noise (~2-3%), re-baseline with sign-off rather than blocking every PR.

---

## Gotcha 4: Fixture set becomes stale; users move on

**What happens:** Evals all pass, but production logs show users asking questions the fixtures don't cover.

**When it occurs:** Fixture set frozen at launch; not updated quarterly.

**How to avoid:** Monthly review of production transcripts → add new fixtures for new patterns. Retire fixtures that don't correspond to real user behavior.

---

## Gotcha 5: Running evals in production data contamination risk

**What happens:** Eval run creates real records in the org. Production data gets polluted with test cases.

**When it occurs:** Running evals against a shared org instead of a dedicated eval sandbox.

**How to avoid:** Eval sandbox is a hard requirement. Never run evals in production. Partial-copy sandbox refreshed nightly if your fixtures depend on specific record shapes.

---

## Gotcha 6: Tool-call capture depends on observability being enabled

**What happens:** Tool-call assertions can't be verified — the log is empty.

**When it occurs:** Agentforce observability (event monitoring) not enabled on the eval org.

**How to avoid:** Enable event monitoring + AI audit events on the eval org. Verify tool-call logs exist before authoring tool-call-dependent fixtures.

---

## Gotcha 7: LLM-as-judge API cost scales with fixture count

**What happens:** 200 fixtures × 4 dimensions × daily runs = significant LLM spend.

**When it occurs:** No cost budgeting on the eval pipeline.

**How to avoid:** Tier runs: P0 cases on every PR, P1 daily, P2 weekly. Sample P2 for spot-checks. Budget LLM spend per team.

---

## Gotcha 8: Reference answers become out-of-date when APIs change

**What happens:** Reference answer cites "order number A7842 placed March 3" but the test record was updated to a different date.

**When it occurs:** Reference answers embed test-data values that aren't kept in sync.

**How to avoid:** Reference answers use placeholders that the harness substitutes at runtime: `{{testOrder.orderNumber}}`, `{{testOrder.placedDate}}`. The harness resolves placeholders from a test-data manifest.

---

## Gotcha 9: Same fixture passes in isolation but fails in suite

**What happens:** Fixture runs solo with 100% pass rate. When run as part of a 40-fixture suite, it fails intermittently.

**When it occurs:** Eval state bleeds across fixtures — session variables, test records, or cached state from prior runs.

**How to avoid:** Each fixture starts with a clean session and fresh test data. Teardown in between fixtures; don't rely on alphabetical ordering for isolation.

---

## Gotcha 10: "Judge the agent" vs "judge the LLM"

**What happens:** Evals measure the base LLM's quality, not the agent's. When the LLM provider ships a better version, scores go up even if the agent design is still wrong.

**When it occurs:** Fixtures that exercise general reasoning instead of the agent's specific topic coverage.

**How to avoid:** Fixtures should test the agent's business logic: correct tool selection, grounded responses in the agent's domain, appropriate refusals. Not "what's 2+2".
