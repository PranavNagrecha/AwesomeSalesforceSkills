# LLM Anti-Patterns — Agent Metric Dashboards

---

## Anti-Pattern 1: Inventing the data source

**What the LLM generates:** a confident specification —

> Source turns from `Conversation__c`. Source latency from
> `Conversation_Turn__c.duration_ms__c`. Source token counts from the Platform
> Event ledger.

**Why it happens:** the assistant reasons correctly that a conversation is an
entity with turns, and Salesforce entities are custom objects with `__c`
suffixes. The naming is a plausible interpolation, and nothing in the request
tells it that a platform-provided data model exists.

**Correct pattern:** the source is Agentforce Session Tracing's Data Cloud data
model — `AIAgentSession`, `AIAgentSessionParticipant`, `AIAgentInteraction`,
`AIAgentInteractionMessage`, `AIAgentInteractionStep`
([Data Model for Agentforce Session
Tracing](https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_data_model.htm&type=5)).
Agentforce Observability additionally reports total sessions, deflected
sessions, and average agent latency directly.

**Detection hint:** any `__c` object name in a metrics specification for a
standard Agentforce deployment. A spec that requires building objects before it
can be implemented is a project proposal, not a dashboard design.

---

## Anti-Pattern 2: Reporting deflection with no baseline

**What the LLM generates:** "Deflection rate = conversations ending without
escalation ÷ total conversations."

**Why it happens:** it is the standard industry definition and it is arithmetically
correct. The model is answering "how is deflection computed", which is a
different question from "does this number mean the agent worked".

**Correct pattern:** deflection is a *causal* claim and therefore needs a
comparison arm. Randomise at the routing layer and report
`(rate_control − rate_treatment) / rate_control` with both arm sizes and the
period. Where a holdout is genuinely unavailable, relabel the tile "Escalation
rate (no control arm)" instead of calling it deflection.

**Detection hint:** the word "deflection" with no control arm, holdout, or
baseline anywhere in the specification.

---

## Anti-Pattern 3: Presenting deflection as unambiguously good

**What the LLM generates:** a dashboard where deflection is the headline KPI,
coloured green when it rises.

**Why it happens:** "deflection = cost saved" is the dominant framing in
contact-centre literature, and the failure mode — users abandoning — is a
behavioural nuance that does not survive summarisation.

**Correct pattern:** deflection rises when users give up, close the browser, or
cannot find the escalation path. Pair it with repeat-contact rate within 72
hours and print the interpretation rule on the dashboard: deflection up *and*
repeat contact up means users are not being helped.

**Detection hint:** deflection with no companion metric. If the dashboard cannot
distinguish "solved" from "abandoned", its headline number is green in one of
the failure modes it exists to catch.

---

## Anti-Pattern 4: A currency cost figure derived from org data

**What the LLM generates:** "Cost per conversation = tokens × $0.00X" as a
dashboard tile, sometimes with a specific model's public price.

**Why it happens:** cost-per-unit is the shape the question asks for, and
token-times-price is how it works for direct API consumption — which is the
dominant pattern in training data. The model does not have a representation of
Agentforce as licensed, Salesforce-metered consumption rather than a per-token
bill in your org.

**Correct pattern:** report measurable **drivers** — sessions, turns per session,
LLM calls per turn, actions per session — and take absolute cost from
Salesforce's consumption reporting. Reconcile monthly. A driver trend with no
dollar sign is actionable and true; a dollar figure with an assumed rate is
neither, and it is going in front of a CFO.

**Detection hint:** any currency amount on the dashboard whose derivation is
entirely inside the org.

---

## Anti-Pattern 5: Mean latency as the latency metric

**What the LLM generates:** "Average response latency" as the single latency
tile.

**Why it happens:** the mean is the default summary statistic, and Agentforce
Observability itself surfaces *average* agent latency as a headline insight — so
there is a real source that reinforces the choice.

**Correct pattern:** p50 and p95 together. Abandonment is driven by the tail, and
the mean is exactly the statistic that hides it. Also split *agent* latency from
*action* latency — a slow external callout has a different owner and a different
fix from slow planner reasoning.

**Detection hint:** no percentile anywhere in the latency section.

---

## Anti-Pattern 6: An LLM-as-judge score that is never calibrated

**What the LLM generates:** "quality score: LLM-as-judge rating on a 1–5 scale,
run nightly over a sample," with no calibration step.

**Why it happens:** LLM-as-judge is a well-known, well-documented technique and
the model reproduces the technique. Calibration is a validity concern rather than
a mechanism, and validity is not what "how do I measure quality" asks about.

**Correct pattern:** a judge score is a proxy whose relationship to human
judgement drifts as prompts and models change. Have a human rate a random sample
of ~50 sessions quarterly and report the correlation on the dashboard as a
"score reliability" figure. An unvalidated quality metric is an unmonitored
dependency of every decision made from it.

**Detection hint:** a quality metric with no human-agreement measurement and no
review cadence.

---

## Anti-Pattern 7: CSAT with no response rate

**What the LLM generates:** "CSAT: average post-conversation survey rating."

**Why it happens:** CSAT is universally reported as a bare score, so the bare
score is what the model has seen ten thousand times.

**Correct pattern:** render `n` and the response rate in the same tile. A 2.4/5
at 12% response measures the loudest 12%; at 70% it measures the population. And
sample *which* conversations get surveyed at random, rather than offering the
survey at particular exit paths, which builds the selection bias into the
instrument.

**Detection hint:** a survey-based metric with no denominator on the tile.

---

## Anti-Pattern 8: Unannotated trend charts

**What the LLM generates:** an eight-week trend line per KPI, clean and
unmarked.

**Why it happens:** a trend chart is a trend chart. Annotation is a property of
the deployment history, which is outside the frame of "design a dashboard."

**Correct pattern:** overlay three event streams — agent version activations,
prompt template activations, and model version changes. Model versions can change
with no deployment on your side, so an unannotated step change costs a week of
investigation for a cause that is not in your repository.

**Detection hint:** no release or version overlay in the chart specification.
This is the cheapest high-value addition to any agent dashboard.

---

## Anti-Pattern 9: Aggregate-only reporting

**What the LLM generates:** org-wide rates for every KPI — one number per
metric, no breakdown.

**Why it happens:** "executive dashboard" implies summarisation, and the model
optimises for the stated audience.

**Correct pattern:** the aggregate is the tile; the per-subagent breakdown
sorted **by rate, not by volume** is the row beneath it (subagents were called
*topics* before April 2026). Sorting by volume is precisely what hides a
low-traffic subagent failing 34% of the time inside a
healthy-looking 3% overall. Alert on the worst subagent rather than the average.

**Detection hint:** no dimension breakdown anywhere in the design.

---

## Anti-Pattern 10: Alert thresholds as round numbers

**What the LLM generates:** "alert when latency exceeds 5 seconds" or "alert on a
10% drop in deflection."

**Why it happens:** thresholds need numbers, no distribution is available at
design time, and round numbers read as considered.

**Correct pattern:** derive thresholds from the observed distribution once you
have four weeks of data — "p95 above the trailing 4-week p99" adapts as the
system changes. Then review at four weeks: did it fire, and was every firing
actionable? An alert with an 80% false-positive rate needs its threshold moved
or the alert deleted, and deleting it is a positive act.

**Detection hint:** a round-number threshold with no stated review date and no
named owner. Both absences predict the alert being muted within a quarter.

---

## Anti-Pattern 11: Assuming historical data exists

**What the LLM generates:** "chart the trailing 8 weeks for each KPI" as step
one, before any mention of enabling data collection.

**Why it happens:** in every other analytics context the data is already
accumulating and the dashboard is a view over it. The model has no
representation of a data model that must be switched on and records nothing
retroactively.

**Correct pattern:** Session Tracing analytics appear only for conversations
occurring **after** the data model is set up. Enabling it is a pre-activation
row on the deployment checklist. If it was missed, label the chart's start date
on the dashboard rather than letting a truncated trend imply a launch date.

**Detection hint:** a dashboard plan with no prerequisite section, or one where
the trailing window predates the tracing setup date.
