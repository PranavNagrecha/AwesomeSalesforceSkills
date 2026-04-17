# Well-Architected Notes — Agentforce Eval Harness

## Relevant Pillars

- **Reliability** — Agents regress silently without evals. The harness is the structural safeguard that ensures prompt/tool changes don't break previously-working behavior. Every P0 case is a regression test.
- **Operational Excellence** — Treating prompts and tool descriptions as versioned code requires a gate equivalent to Apex unit tests. The harness provides that gate, integrated into CI, diff-based, blocks on regression.

## Architectural Tradeoffs

### Human vs LLM judging

| Approach | Pro | Con |
|---|---|---|
| Human judges | High quality, context-aware | Doesn't scale past ~30 fixtures per cycle |
| LLM-as-judge | Scales to hundreds | Requires calibration; biased toward verbosity; rubric must be tight |
| Rule-based checks | Deterministic | Only works for structural assertions (tool calls, schema) |

Recommended hybrid: rule-based for tool-call correctness, LLM-as-judge for response quality, human spot-check 10% of LLM judgments to catch calibration drift.

### Fixture coverage breadth vs depth

Breadth: many fixtures covering many topics.
Depth: fewer fixtures with richer multi-turn transcripts.

Rule: start broad (1-2 P0 fixtures per topic) for launch coverage; deepen over time as production transcripts reveal ambiguity patterns.

### Baseline stability vs model refreshes

When Salesforce refreshes the underlying LLM:
- Absolute scores shift ±2-5% uniformly.
- Relative scores (PR-branch vs baseline) stay meaningful.
- Re-baseline quarterly or on confirmed model version changes.

## Anti-Patterns

1. **Launch-without-evals** — Shipping the agent, then writing evals from user complaints. Every regression costs user trust. Fix: eval-driven development; P0 fixtures before prompt stability.

2. **Single aggregate quality score** — One "85% quality" number hides dimension-specific regressions. Fix: per-dimension scoring, per-dimension PR gate.

3. **Happy-path-only fixtures** — Evals that only test successful completion miss every failure mode. Fix: 5:1 non-happy to happy case ratio.

4. **Unbounded LLM-judge spend** — Running 200 fixtures × 4 dimensions × daily burns budget fast. Fix: tier by severity; P0 on every PR, P2 weekly-sampled.

5. **Fixture set frozen after launch** — Evals pass, users fail. Fix: monthly review of production transcripts; add fixtures for new patterns.

## Official Sources Used

- Salesforce Help — Agentforce Testing Center: https://help.salesforce.com/s/articleView?id=sf.copilot_testing.htm
- Salesforce Developer — Einstein Trust Layer: https://developer.salesforce.com/docs/einstein/genai/guide/trust-layer.html
- Salesforce Architects — Evaluating AI Systems: https://architect.salesforce.com/
- Salesforce Developer — Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/
