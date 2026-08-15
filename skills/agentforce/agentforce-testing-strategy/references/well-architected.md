# Well-Architected Notes — Agentforce Testing Strategy

## Relevant Pillars

### Reliability

Without a regression suite, every prompt edit and every model version change is
an uncontrolled production experiment — and unlike code changes, model version
changes can arrive without a deployment on your side. That asymmetry is what
makes agent testing structurally different from application testing: the system
under test can change while your repository does not.

The suite's reliability job is to make behaviour changes *visible*, not to
prevent them. The two expectation families do different work:

- **Deterministic** (`topic_sequence_match`, `action_sequence_match`) — these
  are genuine invariants. A change here is always worth a human look. The
  expectation name still says *topic*: subagents were called topics before
  April 2026, and the API surface did not rename with the term.
- **Scored** (`coherence`, `completeness`, `conciseness`,
  `output_latency_milliseconds`) — these are trends. A single run tells you
  little; a sustained shift tells you a lot.

Conflating them is the most common reliability failure in this domain, because
it produces a gate that flakes, and a gate that flakes gets disabled along with
everything behind it.

### Security

Adversarial tests are the only routine, repeatable defence against prompt
injection, PII echo, and exfiltration-through-action. Every other control in the
stack — topic scope, restricted topics, action filters — is configuration whose
effectiveness is unverified until something exercises it.

Two design consequences:

1. **The adversarial suite is separate from the quality suite.** A security
   regression must never be a line item inside a report about tone. Separate
   definitions, separate reporting, separate owner.
2. **Zero-tolerance assertions live in post-processing.** Because there is no
   `not_contains` operator, the only exact way to assert "this token never
   appears" is over the JSON results. That is also where the forbidden-token list
   is reviewable as one artefact.

The test corpus is itself a security surface. Utterances are source-controlled
metadata deployed to every sandbox — treat a test file containing real customer
data as a data incident, not a hygiene problem.

### Operational Excellence

The pyramid only survives if each layer runs on the trigger that matches its
cost:

| Layer | What it proves | Trigger | Determinism |
|---|---|---|---|
| Apex action tests | Implementation, bulk-safety, security enforcement | Every PR | Full |
| Routing / action-sequence cases | Planner selects the right subagent and tool | Every PR | Full |
| Golden set with quality scores | End-to-end answer quality | Nightly | Partial |
| Adversarial set | Refusal, PII, exfiltration | Nightly + pre-release | Partial |
| Production replay | Real failures become permanent cases | Weekly harvest | N/A |

Production replay depends on Session Tracing having been enabled *before* the
conversations you want to replay — data exists only from setup onwards. That
makes enabling it a go-live prerequisite rather than an incident response.

The maintenance loop is the part that is process rather than artefact, and the
part that is skipped: weekly harvest, quarterly prune, and a triage decision on
every failure that is made by a person.

### Performance

Full LLM runs are slow and are billed as agent activity. Keeping the PR gate to
deterministic expectations is a cost control as much as a flake control. The
`output_latency_milliseconds` expectation is worth carrying on the nightly
purely as a trend: latency regressions in an agent are usually caused by
instruction bloat or an added action, both of which are invisible in any other
measurement.

---

## Architectural Tradeoffs

### Native `AiEvaluationDefinition` vs. a custom harness

| | Native | Custom harness |
|---|---|---|
| Runs against the real planner | Yes | Only via the API, reimplemented |
| Shared with Testing Center UI | Yes | No |
| Deploys and versions with the agent | Yes | Separate lifecycle |
| Rename safety | Deploy fails loudly | Silent drift |
| Expressiveness | Fixed expectation set | Anything |
| Negative assertions | Not directly | Trivial |

Native for everything it can express; a thin post-processing layer over its JSON
output for what it cannot. Building a parallel harness because of the
`not_contains` gap trades one missing operator for a whole second lifecycle.

### Small sharp suite vs. exhaustive coverage

50–200 cases is the range where one person can still hold the suite in their
head and where a nightly run finishes before anyone looks. Past that, marginal
cases add runtime and dilute attention faster than they add coverage. The
constraint is attention, not compute — an unread report has zero value
regardless of how many cases produced it.

### Pinning `subjectVersion` vs. tracking latest

Pinning gives reproducibility and is right for release qualification. Tracking
latest gives early warning and is right for the nightly — you *want* to learn
that the live agent's behaviour moved. Run both, and say which convention each
definition follows in its description so a red build is interpretable.

### Automated scoring vs. human review

Scores catch quality drift in aggregate. They do not catch brand and tone
mismatch, which is frequently the thing that matters most to the business and
which registers as "correct but wrong." A sampled human read per release, with
a named owner, is currently the only control for that dimension. Claiming
otherwise is the failure mode; budgeting for it is the design.

### Where to put PII assertions

In the definition (positive assertion on refusal language): brittle to rewording,
but visible next to the case. In post-processing (exact absence check): precise
and universal, but one step removed. Use post-processing for zero-tolerance
categories and in-definition assertions for behaviours you want documented
beside the utterance. Do not choose only one.

---

## Anti-Patterns

1. **A hand-rolled YAML harness.** It tests a reimplementation of the agent
   rather than the agent, and it drifts silently when subagents are renamed.

2. **Exact-match on prose.** Every prompt tune turns the suite red for
   non-regressions, and the team stops trusting failures within a month.

3. **Happy paths only.** The six adversarial categories are where incidents come
   from. An agent whose suite contains no expected refusal has never been tested
   for refusal.

4. **Scored expectations in a blocking gate.** Flake on day one, disabled by day
   thirty, taking the deterministic checks with it.

5. **`sf agent test run` without `--wait` in CI.** Fails open — the build is
   green because the tests have not started.

6. **Automating the regression-vs-improvement decision.** Locks the agent to the
   behaviour of the model that was current when the goldens were written.

7. **Real PII in test utterances.** The corpus is metadata: git, every sandbox,
   every clone, no retention policy.

---

## Hygiene

- Named owner for the suite; named owner for the per-release human read.
- Dashboard visible to engineering and product, not results buried in CI logs.
- Flake rate measured and kept under ~1% in the blocking gate.
- Quarterly prune; weekly production replay harvest.
- Forbidden-token check runs over utterances at commit time and over responses
  at run time.

---

## Related

- `agentforce/agent-testing-and-evaluation` — operating Testing Center and the
  `sf agent test` command surface in detail.
- `agentforce/agentforce-eval-harness` — hallucination evals, fixture format,
  and scoring rubrics.
- `agentforce/agent-action-error-handling` — the error branches that need
  dedicated test cases at both the Apex and routing layers.
- `agentforce/agentforce-pii-redaction` — source of the forbidden-token list
  used by the adversarial suite.
- `agentforce/agent-deployment-checklist` — where "suite green" and "tracing
  enabled" become blocking rows.
- `templates/agentforce/AgentEval_Fixture.md` — fixture shape.

---

## Official Sources Used

- Testing API Metadata Reference (AiEvaluationDefinition) — https://developer.salesforce.com/docs/ai/agentforce/references/testing-api/testing-metadata-reference.html
- Build Tests in Metadata API — https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-build-tests.html
- Run Agent Tests (Agentforce DX) — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-test-run.html
- Deploy and Run Tests in the Command Line — https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-cli.html
- Use Test Results to Improve Your Agent — https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-use-results.html
- agent test run (Salesforce CLI Command Reference) — https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_agent_test_run.html
- Agentforce Testing Center (Help) — https://help.salesforce.com/s/articleView?id=ai.agent_testing_center.htm&type=5
- About Agentforce Session Tracing (Help) — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_about.htm&type=5
- Create Custom Actions Using Apex InvocableMethod — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-invocablemethod.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
