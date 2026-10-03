---
name: salesforce-decision-analysis
description: "Structure and evaluate a consequential Salesforce choice before the team commits: frame the decision, separate hard constraints from preferences, compare viable options with evidence, test score sensitivity, and recommend a reversible next step. Trigger keywords: compare Salesforce options, evaluate alternatives, make a platform decision, decision matrix, weighted decision. NOT for documenting an already accepted choice — use architect/architecture-decision-records. NOT for a narrow technology branch already covered by a canonical decision tree — apply that tree first."
category: architect
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
  - Scalability
  - User Experience
  - Operational Excellence
triggers:
  - "help us choose between several Salesforce implementation options"
  - "build an evidence-based Salesforce decision matrix with tradeoffs"
  - "compare buy build configure and no-change approaches for this requirement"
  - "which Salesforce option is safest under our org and delivery constraints"
  - "stress-test this architecture recommendation before we record an ADR"
tags:
  - decision-analysis
  - option-assessment
  - architecture
  - tradeoffs
  - evidence
  - reversibility
inputs:
  - "Decision question and measurable business outcome"
  - "Target org, project, workload, release, and authority context when they affect feasibility"
  - "Hard constraints, non-goals, decision deadline, and known options"
  - "Evidence available for product behavior, cost, risk, delivery, and operations"
outputs:
  - "Decision packet with scope, evidence ledger, viable options, hard-gate results, weighted comparison, sensitivity analysis, and risks"
  - "Recommendation with confidence, unresolved unknowns, validation actions, and conditions that would change the recommendation"
  - "ADR-ready handoff after a human accepts the decision"
dependencies:
  - architect/solution-design-patterns
  - architect/architecture-decision-records
  - architect/well-architected-review
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-09-01
---

# Salesforce Decision Analysis

Use this skill before committing to a non-trivial Salesforce product, architecture, automation, integration, security, data, or delivery choice. Its job is to make the decision **auditable and testable**, not to manufacture certainty or replace the specialist skill that supplies domain evidence.

---

## Decision Packet Contract

A complete packet contains each element below. Keep raw research outside the packet and link to stable evidence IDs or URLs.

| Element | Required content | Failure prevented |
|---|---|---|
| Decision frame | One question, one measurable outcome, in-scope and out-of-scope boundaries | Solving adjacent problems instead of the stated one |
| Target context | Org/project/workload/release identity, or an explicit `not required` | Treating release- or org-dependent behavior as universal |
| Constraints | Hard gates separated from preferences | Allowing a high weighted score to hide an infeasible option |
| Evidence ledger | Facts, recommendations, assumptions, unknowns, source tier, observed date | Laundering opinions into facts |
| Viable options | At least two options a competent team could choose; include standard/reuse/no-change when credible | Comparing a favorite to strawmen |
| Criteria model | Criterion definition, measurement, direction, weight, and rationale | Arbitrary weights and double-counting |
| Comparison | Hard-gate result, score, evidence, uncertainty, and tradeoff for every option/criterion | Unsupported scoring |
| Sensitivity | Weight or score changes that would alter the winner | False precision from one weighting scheme |
| Risk and reversibility | Failure modes, blast radius, lock-in, exit cost, rollback or experiment | Ignoring asymmetric downside |
| Recommendation | Preferred option, confidence, conditions, validation step, and decision owner | A recommendation with no action or accountability |

---

## Evidence States

Classify every material statement before scoring it.

| State | Meaning | How it may influence the decision |
|---|---|---|
| `fact` | Directly supported by identified org/project evidence or a source appropriate to the claim | May support a hard gate or a score |
| `recommendation` | A documented pattern or expert judgment, not a platform guarantee | May shape criteria; never becomes a hard gate without policy ownership |
| `assumption` | Plausible but not yet verified | Score with uncertainty and add a validation action |
| `unknown` | Evidence is absent, contradictory, stale, or inaccessible | Do not assign a favorable score; expose the decision risk |

For release-sensitive claims, record the Salesforce release or API version and the date observed. For org-specific claims, record the exact org or snapshot identity. Never use a source URL as proof that the target org has a licensed or enabled capability.

---

## Hard Gates Before Weighted Scoring

A weighted matrix answers **which feasible option best fits the preferences**. It cannot make an infeasible option viable.

Evaluate gates first:

1. **Platform feasibility** — supported metadata/API/runtime behavior for the stated release.
2. **License and entitlement** — confirmed availability for the target edition, add-ons, user licenses, and contractual constraints.
3. **Security and compliance** — data classification, least privilege, residency, audit, encryption, and segregation requirements.
4. **Authority and environment** — whether the requested operation is permitted for this run and target.
5. **Non-functional minimums** — required throughput, latency, availability, recovery, scale, and supportability.
6. **Delivery boundary** — package ownership, deployment path, testability, and rollback feasibility.

Use `PASS`, `FAIL`, or `UNKNOWN`. A `FAIL` eliminates the option. An `UNKNOWN` keeps it provisional and caps confidence until validated.

---

## Constructing Real Options

Options must differ in a load-bearing choice, not just naming. Consider these families where relevant:

| Family | Candidate option |
|---|---|
| Standard | Native Salesforce capability with configuration only |
| Reuse | Extend an existing component, package, automation, service, or data product |
| Configure | Add declarative metadata while preserving the current architecture |
| Build | Add custom Apex, LWC, integration, or external service behavior |
| Buy | Adopt a managed package or licensed Salesforce product |
| Sequence | Run a bounded pilot, defer, or stage the capability behind an experiment |
| No change | Retain the current state and accept the documented cost/risk |

Do not force all families into every decision. Include only options that survive an initial plausibility check, and explain why other obvious families were excluded.

---

## Criteria and Weighting

Start from the business outcome and hard constraints. Then map criteria to Salesforce Well-Architected concerns without counting the same effect twice.

| Criterion | Evidence question | Typical measurement |
|---|---|---|
| Outcome fit | Does the option satisfy the acceptance criteria? | Coverage of required scenarios |
| Trust | What access, data exposure, compliance, and failure risk does it create? | Control gaps and residual risk |
| Reliability | How does it fail, recover, retry, and avoid duplicate work? | Failure modes, RTO/RPO, idempotency |
| Scale and performance | Does it fit data volume, concurrency, limits, and latency? | Headroom and measured/estimated load |
| User and operator effort | How difficult is it to use, support, diagnose, and change? | Steps, roles, observability, runbooks |
| Delivery | Can it be built, tested, deployed, and rolled back safely? | Dependencies, lead time, test surface |
| Cost and lock-in | What recurring, implementation, migration, and exit costs exist? | Total cost range and switching cost |

Weight rules:

- Make weights sum to 100 and record who approved them.
- Explain each weight in relation to the outcome; do not default to equal weights silently.
- Keep mutually dependent criteria separate only when each has a distinct measurement.
- Use a consistent score scale, normally 1–5, with anchors defined before options are scored.
- Attach evidence and uncertainty to every score. A bare number is not a finding.
- Avoid decimal precision that exceeds the evidence quality.

A practical 1–5 anchor:

| Score | Meaning |
|---:|---|
| 1 | Fails most of the criterion or creates an unacceptable tradeoff |
| 2 | Partially fits; substantial remediation or risk remains |
| 3 | Meets the minimum with material tradeoffs |
| 4 | Strong fit with manageable tradeoffs |
| 5 | Best-supported fit; do not use when evidence is incomplete |

---

## Sensitivity and Uncertainty

Run at least two challenges:

1. **Weight sensitivity** — increase the two most debatable weights and reduce the current winner's strongest criterion. Record whether the ranking changes.
2. **Evidence sensitivity** — replace each load-bearing assumption with a conservative value. Record whether the recommendation changes or becomes conditional.

Also state the smallest plausible change that would reverse the recommendation. When several options remain close, recommend a time-boxed experiment instead of declaring a false winner.

---

## Risk and Reversibility

For every viable option, record:

- failure mode and user/business impact;
- blast radius and affected systems/personas;
- detectability and time to detect;
- rollback, compensating action, or exit path;
- irreversible decisions, data migrations, contract terms, and namespace/package lock-in;
- evidence needed before execution.

Prefer the smallest reversible step when evidence is weak and the cost of being wrong is high. Reversibility is not automatically superior: a temporary workaround that creates hidden operational debt may score worse than a deliberate durable change.

---

## Recommended Workflow

1. **Frame and route** one decision question and measurable outcome. Separate constraints, preferences, non-goals, deadline, and owner; then apply the narrowest canonical decision tree or specialist skill and record its branch or gap.
2. **Gather evidence and options** using `standards/source-hierarchy.md`, target-org/project evidence when applicable, and a claim ledger. Generate genuinely viable options independently before ranking, including standard, reuse, and no-change options when credible.
3. **Apply hard gates** and remove failed options. Keep `UNKNOWN` gates visible and cap confidence until their validation action completes.
4. **Define and score criteria** with pre-declared anchors, owner-approved weights, evidence, and uncertainty. Never let a weighted score override feasibility.
5. **Challenge the result** with weight/evidence sensitivity, risk asymmetry, reversibility, and a pre-mortem. Prefer a bounded experiment when the winner is unstable.
6. **Recommend and hand off** an option, experiment, defer, or no-change posture with confidence, unresolved unknowns, validation actions, and reversal conditions. After human acceptance, hand the result to `architect/architecture-decision-records`; do not treat the mutable analysis packet as the frozen ADR.

---

## Decision Statuses

| Status | Use it when |
|---|---|
| `recommend` | Evidence supports one option and no load-bearing gate is unknown |
| `conditional-recommend` | One option leads, but named assumptions or gates must be verified |
| `experiment` | Options remain close or a reversible test can resolve the main uncertainty |
| `defer` | The decision deadline or dependency makes a responsible choice premature |
| `no-change` | The current state is deliberately retained after comparing its costs and risks |
| `refuse` | The requested decision would violate policy, authority, law, or a non-negotiable control |

---

## Review Checklist

- [ ] One decision question and one measurable outcome are stated
- [ ] Target org/project/release context is pinned or explicitly not required
- [ ] Constraints are separated from weighted preferences
- [ ] At least two genuinely viable options are compared
- [ ] Standard, reuse, experiment, and no-change options were considered where credible
- [ ] Every hard gate is `PASS`, `FAIL`, or `UNKNOWN`
- [ ] Criteria have definitions, anchors, weights, rationales, and no obvious double-counting
- [ ] Every score links to evidence and carries an uncertainty note
- [ ] Weight and evidence sensitivity were tested
- [ ] Risks, blast radius, reversibility, and exit costs are explicit
- [ ] Recommendation names conditions that would change it
- [ ] Accepted outcome is handed to an ADR rather than silently treated as final

---

## Output Artifacts

| Artifact | Purpose |
|---|---|
| `decision-analysis.md` | Human-readable decision packet using the bundled template |
| `decision-analysis.json` | Optional structured representation for automation and MCP consumers |
| `evidence-ledger` | Stable claim-to-source mapping with freshness and uncertainty |
| `validation-actions` | Ordered checks that resolve remaining assumptions before commitment |
| `adr-handoff` | Concise accepted decision, premises, alternatives, consequences, and review trigger |

Validate a packet with:

```bash
python3 skills/architect/salesforce-decision-analysis/scripts/check_salesforce_decision_analysis.py --input path/to/decision-analysis.md
```

---

## Related Skills

- `architect/solution-design-patterns` — supply the domain design patterns and platform tradeoffs used as evidence.
- `architect/architecture-decision-records` — freeze the accepted choice and premises after human approval.
- `architect/well-architected-review` — evaluate an implementation or workload, not a single pre-commitment choice.
- `standards/decision-trees/` — apply narrow canonical routing before inventing a generic matrix.
- Specialist decision skills — use the product-specific decision skill when the repository already owns the exact branch.

See `references/examples.md`, `references/gotchas.md`, `references/llm-anti-patterns.md`, and `references/well-architected.md` for worked packets and review guidance.
