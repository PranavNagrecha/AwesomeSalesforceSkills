# Gotchas — Agentforce Testing Strategy

---

## 1. `sf agent test run` is asynchronous by default — CI reports green before the tests finish

**What happens:** the CI step runs `sf agent test run --api-name X`, the command
exits 0 immediately, and the pipeline goes green. The tests have not run yet.
The command's actual output was a *second* command to resume and view results.

**When it occurs:** the first CI wiring, every time.

**The documented behaviour:** the tests run asynchronously by default; the
command outputs the `agent test resume` command that you then run to view
results. To run synchronously, use `--wait` with a number of minutes.
— [Run Agent Tests](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-test-run.html)

**How to avoid:** always pass `--wait` in CI, sized generously — full LLM runs
are slow and a timeout on `--wait` is a build failure, not a test failure.
Combine with `--result-format junit --output-dir …` so the pipeline has an
artefact to parse rather than terminal text to scrape.

---

## 2. There is no `not_contains` operator

**What happens:** the team writes the zero-tolerance PII assertion as a
`string_comparison` with an invented `not_contains` operator. It fails to
deploy, or silently never matches.

**The documented operator set:** `equals`, `contains`, `startswith`, `endswith`,
`greater_than`, `less_than`, `greater_than_or_equal`, `less_than_or_equal`.
— [Testing API metadata reference](https://developer.salesforce.com/docs/ai/agentforce/references/testing-api/testing-metadata-reference.html)

**How to avoid:** express negatives outside the definition. Run with
`--result-format json` and assert absence in a post-processing step over the
results file. This is strictly better anyway: the forbidden-token list becomes a
single reviewable file rather than being spread across dozens of test cases, and
it can be applied to *every* case at once rather than only the ones somebody
remembered to guard.

---

## 3. Quality expectations take no `expectedValue` — supplying one is a category error

**What happens:** an author writes
`<expectation><name>coherence</name><expectedValue>true</expectedValue></expectation>`
and is surprised that the result is not a pass/fail.

**The documented behaviour:** `coherence`, `completeness`, `conciseness`, and
`output_latency_milliseconds` are quality checks that need no `expectedValue` —
they produce a score. `topic_sequence_match`, `action_sequence_match`, and
`bot_response_rating` take an expected value.
— [Testing API metadata reference](https://developer.salesforce.com/docs/ai/agentforce/references/testing-api/testing-metadata-reference.html)

**How to avoid:** treat the two families differently in reporting. Match
expectations are pass/fail and belong in the PR gate. Score expectations are
trends and belong on a dashboard with a threshold you tune — putting a raw score
in a blocking gate produces flake on day one.

---

## 4. Omitting `subjectVersion` silently retargets the suite

**What happens:** a suite passes on Monday and fails on Wednesday with no code
change. Somebody activated a new agent version in between.

**The documented behaviour:** `subjectVersion` is optional and *"defaults to
latest active if omitted"*.
— [Testing API metadata reference](https://developer.salesforce.com/docs/ai/agentforce/references/testing-api/testing-metadata-reference.html)

**How to avoid:** omit it deliberately for the nightly suite — you *want* the
nightly to track whatever is live. Pin it for a release-qualification run, where
the whole point is reproducibility against a specific version. Record which
convention each definition follows in its `<description>`.

---

## 5. Renaming a subagent breaks every `topic_sequence_match` at deploy time, not run time

**What happens:** `Billing` is renamed to `Billing_And_Payments` in the agent.
Fifty test cases still name `Billing`. The failure surfaces as fifty red tests
that look like a routing regression.

**When it occurs:** any subagent rename, which teams treat as cosmetic.
(*Subagent* is the April 2026 rename of *topic*; the `topic_sequence_match`
expectation name kept the old word.)

**How to avoid:** grep the evaluation definitions for the old name as part of the
rename, and treat subagent API names as a published interface. This is the same
discipline as renaming a prompt template — see
`agentforce/agentforce-prompt-versioning`. The saving grace is that the tests
*do* fail loudly rather than passing vacuously.

---

## 6. Apex tests at 100% coverage prove nothing about action invocation

**What happens:** every action has a green `@IsTest` class. In production the
agent never calls one of them, or calls it with the wrong input, because the
`@InvocableVariable` description was too vague for the planner to fill it
correctly.

**When it occurs:** whenever the test strategy is written by someone thinking in
Apex rather than in planner behaviour.

**The mechanism:** an Apex test calls the static method directly. That path
bypasses subagent assignment, planner action selection, and natural-language input
extraction — the three things that determine whether the action is ever used.
Descriptions on `@InvocableMethod` and `@InvocableVariable` are what the agent
reads to understand how to use the action
([Create Custom Actions Using Apex
InvocableMethod](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-invocablemethod.html)).

**How to avoid:** require one `action_sequence_match` case per custom action, in
addition to the Apex test. Make it a checklist row, because no tool will tell
you it is missing.

---

## 7. Exact-match assertions on prose make the suite a liability

**What happens:** a prompt tune improves ten answers and turns forty tests red.
The team spends a day updating expected strings, then starts skipping the suite
before merging.

**How to avoid:** assert decisions exactly (`topic_sequence_match`,
`action_sequence_match`), facts by `contains` on a short stable token (an order
number, a status word), and style by score. Never assert a full sentence. The
diagnostic question for any assertion: *"if this fails, do I know something is
broken?"* If the honest answer is "it might just be worded differently," it is
not an assertion, it is a tripwire.

---

## 8. Tone and brand drift are invisible to every automated check

**What happens:** a model update keeps routing and actions perfectly correct
while shifting register — the agent becomes chattier, or starts using
exclamation marks, or drops the formal address the brand requires in a
particular market. Every test is green.

**When it occurs:** model version changes, which happen without a deployment on
your side.

**How to avoid:** the `conciseness` and `coherence` scores catch some of this as
a trend, not as a gate. The rest needs a human: sample twenty responses per
release and read them. Put it on the release checklist with a named owner. The
honest framing is that this is a dimension where full automation is not
currently available, and a suite that pretends otherwise will miss it.

---

## 9. A flaky suite is worse than no suite

**What happens:** the golden suite fails 3–8 cases per night, always different
ones. Within a month, "the agent tests are flaky" is the standing explanation
for every red build and genuine regressions are ignored.

**When it occurs:** free-text scoring in a blocking gate; goldens dependent on
data that changes (today's date, a record another test mutates); non-deterministic
grounding.

**How to avoid:**

- Keep the blocking gate to deterministic expectations only.
- Isolate test data. A golden that reads a record another suite writes is not a
  golden.
- Measure the flake rate explicitly — rerun failures once, log the rerun rate,
  and treat a rate above ~1% as a bug in the suite. If you cannot bring it down,
  move those cases out of the gate and onto the dashboard.

---

## 10. Corpus grows, nobody prunes, signal drops

**What happens:** 400 goldens accumulated over a year. Runtime is 90 minutes,
forty cases test a subagent that was retired, and nobody can say which cases
matter.

**How to avoid:** keep the suite deliberately small — 50–200 cases is the range
where the whole thing is still legible to one person. Quarterly, drop cases for
retired behaviour and cases that have never failed *and* duplicate another
case's coverage. A case that has never failed is not automatically dead weight —
it may be guarding something important — but a case that has never failed and
tests the same path as three others is.

---

## 11. Real PII in test utterances

**What happens:** a production replay case is committed verbatim, complete with
a customer's email address. It is now in git, in every sandbox, and in every
developer's local clone, under a retention policy nobody set.

**When it occurs:** the harvest step in production replay, which is exactly when
the data is most convenient.

**How to avoid:** sanitise *and verify* — run the forbidden-token check over
candidate utterances before commit, not only over responses. Use reserved
synthetic values (`999-xx-xxxx`, `4111 1111 1111 1111`, `example.com` addresses)
so a false positive later is unambiguous. Add the check to the pre-commit hook,
because this leak is introduced by the person building the safety net.

---

## 12. "Regression" that is an improvement, auto-reverted

**What happens:** an updated model answers a case better than before. The
golden's expected substring was worded for the old answer. The nightly goes red,
and an automated policy reverts the model pin.

**How to avoid:** triage is a human step with three outcomes — revert, update the
expectation, or add a case. Never automate the disposition. Keep a short
"known divergences" list with an owner and an expiry so a deliberate acceptance
does not silently become permanent blindness.

---

## 13. Testing in an org whose data does not resemble production

**What happens:** the suite passes in a developer sandbox where the resort has
three rooms and every order is fulfilled. In production, grounding returns
different content, actions hit records in states the tests never produced, and
routing shifts because the retrieved context differs.

**How to avoid:** run the qualification suite in a Partial or Full sandbox
refreshed recently enough to be representative, and state the refresh age in the
release record. Agent behaviour depends on retrieved content, so "the code is
identical" is not sufficient grounds to expect identical behaviour across orgs.

---

## 14. Session-tracing data only exists from the moment you enable it

**What happens:** an incident occurs, the team goes to replay the conversation
that caused it, and there is nothing there — tracing was enabled last week.

**The documented behaviour:** analytics and insights appear only for
conversations occurring **after** the Session Tracing Data Model is set up.
Setup lives under Einstein Audit, Analytics, and Monitoring Setup, and users
need the Data Cloud User permission set to see the results
([Set Up Agentforce Session
Tracing](https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_setup.htm&type=5)).

**How to avoid:** enabling tracing is a go-live prerequisite, not a
post-incident action — it is a row on the deployment checklist
(`agentforce/agent-deployment-checklist`) for exactly this reason. Production
replay as a testing practice is only available to teams that switched it on
before they needed it.
