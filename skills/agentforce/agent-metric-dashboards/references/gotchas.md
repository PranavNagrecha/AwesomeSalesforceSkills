# Gotchas — Agent Metric Dashboards

---

## 1. Session tracing has no history before you enabled it

**What happens:** the dashboard is built in week six. The trend chart starts in
week five, because that is when somebody enabled Session Tracing. The
launch-period data everyone wants to compare against does not exist.

**The documented behaviour:** analytics and insights show up only for
conversations occurring **after** the Session Tracing Data Model is set up
([Set Up Agentforce Session
Tracing](https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_setup.htm&type=5)).

**How to avoid:** enabling tracing is a pre-activation checklist row, not a
dashboard task — see `agentforce/agent-deployment-checklist`. If it was missed,
say so on the dashboard ("data from 2026-07-08") rather than letting a truncated
trend imply the agent launched then.

---

## 2. Readers see an empty dashboard without the Data Cloud User permission set

**What happens:** the dashboard works for the person who built it and shows
nothing for the executives it was built for. It looks like a data problem.

**How to avoid:** the Data Cloud User permission set must be assigned to
everyone who should have access to Agentforce Observability output. Put it in
the permission set group that goes with the agent's rollout, and verify with an
actual reader before the first review meeting rather than after.

---

## 3. Deflection rises when the agent gets worse

**What happens:** deflection climbs from 58% to 71% over a month. Everyone is
pleased. CSAT is falling and repeat contacts are up 40%.

**Why:** deflection counts sessions that ended without an escalation. A user who
gave up, closed the browser, or could not find the escalation path is
indistinguishable from a user who was helped. The metric improves under a
specific mode of failure.

**How to avoid:** never render deflection alone. Pair it with repeat-contact
rate within 72 hours — a behavioural signal that does not depend on anyone
answering a survey — and print the interpretation rule on the dashboard itself.
The person reading the tile will not consult a wiki.

---

## 4. Deflection with no control arm measures the world, not the agent

**What happens:** deflection improves 8 points. Marketing ran a campaign that
shifted the question mix toward simple queries. Nothing about the agent changed.

**How to avoid:** randomise at the routing layer — a fraction of inbound goes to
an agent-disabled queue — and report the difference between arms. Where a
holdout is genuinely unavailable, relabel the tile "Escalation rate (no control
arm)". Renaming is honest, costs nothing, and stops the number entering a board
deck as causal evidence.

---

## 5. Before/after comparisons confound everything that changed in between

**What happens:** "escalation was 40% before the agent and is 30% now, so the
agent deflects 25%." In between: a new self-service portal, a pricing change,
and a seasonal peak.

**How to avoid:** a concurrent control arm experiences the same world in the
same period; a historical baseline does not. If only a historical baseline
exists, state the confounds explicitly next to the number. A caveat in a
footnote is a caveat nobody reads.

---

## 6. CSAT without a response rate is a measurement of the loudest 12%

**What happens:** CSAT reads 2.4/5 and a remediation project is funded. The
response rate is 12% and skewed toward users who reached a specific frustrating
exit path.

**How to avoid:** render `n` and the response rate in the same tile as the
score — not below it, not in a tooltip. Add one complete, non-opt-in signal
alongside: platform metric scores from session tracing are computed for every
session rather than the ones someone chose to rate. Randomise *which*
conversations get surveyed rather than offering the survey at particular exits.

---

## 7. Currency-denominated cost tiles are usually invented

**What happens:** a "cost per conversation: $0.42" tile. Nobody can explain where
$0.42 comes from, and it turns out to be a token estimate multiplied by a public
price for a model the org may not be using.

**Why it happens:** Agentforce consumption is licensed and metered by Salesforce,
not exposed as a queryable per-token cost inside your org. Any currency figure
computed from org data alone contains an assumed rate.

**How to avoid:** report the **drivers** you can measure — sessions, turns per
session, LLM calls per turn, actions per session — and take absolute cost from
Salesforce's consumption reporting. Reconcile the two monthly. A driver trend
with no dollar sign is more useful than a dollar figure with an invented rate,
because it is actionable and it is true.

---

## 8. A model version change moves every metric with no deployment on your side

**What happens:** latency, verbosity, and quality scores all shift overnight. Git
shows no changes. The team spends two days looking for a cause in their own
code.

**How to avoid:** annotate the trend charts with three event streams — agent
version activations, prompt template activations, and model version changes.
Without annotation, a step change costs a week of investigation; with it, the
cause is a glance. This is also the argument for pinning model versions on
critical topics where reproducibility matters more than improvements — see
`agentforce/agentforce-prompt-versioning`.

---

## 9. Latency averages hide the experience that drives abandonment

**What happens:** average latency is 1.8s and looks fine. The p95 is 11s, and
the 5% of users who hit it are the ones abandoning.

**How to avoid:** report p50 and p95 side by side, never the mean alone.
Agentforce Observability surfaces average agent latency as a headline insight,
which is useful for a trend and insufficient as the only latency tile. Turn-level
data from `AIAgentInteraction` supports percentiles; compute them.

Also separate *agent* latency from *action* latency. A slow external callout
inside one action is a different problem, with a different owner, from slow
planner reasoning — and only the second one is fixed by touching the agent.

---

## 10. Platform-scored quality metrics drift from human judgement

**What happens:** the quality score is stable at 0.86 for six months while
supervisors report the agent's answers have got worse.

**How to avoid:** calibrate on a cadence. Have a human independently rate a
random sample of 50 sessions quarterly, and correlate against the platform
score. If correlation falls, the score is measuring something that used to be
quality and no longer is. Report the correlation on the dashboard as a
"score reliability" figure — a quality metric whose validity is unmeasured is
itself an unmonitored dependency.

---

## 11. The OTel export is one session per call, within 72 hours

**What happens:** an exporter is built assuming a range query. It cannot be —
the endpoint takes a single session id — and it silently loses data whenever it
falls more than three days behind.

**The documented constraints:** the export endpoint is
`GET /services/data/v66.0/einstein/audit/otel/{session-id}`; bulk queries are
unsupported; the API returns sessions started within the previous 72 hours;
standard Connect API rate limits apply; and it is a Beta feature
([Export Agentforce Session Tracing
Data](https://developer.salesforce.com/docs/ai/agentforce/guide/otel-api.html)).

**How to avoid:** alert on **exporter lag**, not only on exporter errors — a
stalled exporter that returns 200s loses data permanently once the window
passes. Sample rather than exporting everything, and keep the Salesforce-native
dashboard authoritative while the export remains Beta.

---

## 12. Alert thresholds nobody tuned become alerts nobody reads

**What happens:** an alert fires weekly for three months. By month two the
channel is muted. In month four a real regression fires into a muted channel.

**How to avoid:** every alert has a named owner and a review at four weeks
asking two questions — did it fire, and was every firing actionable? An alert
that fired ten times and was actionable twice has an 80% false-positive rate and
needs its threshold moved or the alert deleted. Deleting a bad alert is a
positive act, not an admission of failure.

Start thresholds from the observed distribution rather than from a round number.
"p95 latency above the trailing 4-week p99" is tunable and self-adjusting;
"latency above 5 seconds" is a guess that will be wrong in both directions.

---

## 13. Aggregating across subagents hides the one that is broken

**What happens:** overall action failure rate is 3%, comfortably inside target.
One subagent's rate is 34% and it handles 8% of traffic. (*Subagent* is the
April 2026 rename of *topic*; nothing about the behaviour changed.)

**How to avoid:** the executive tile is the aggregate; the row beneath it is
always the per-subagent breakdown, sorted by rate rather than by volume. Sorting
by volume is what hides small-but-broken. Alert on the *worst* subagent, not on
the average — the average is a summary for humans, and the worst is the thing
that needs action.

---

## 14. The weekly digest becomes noise within a month

**What happens:** an automated weekly email with fourteen numbers. By week five
nobody opens it.

**How to avoid:** the digest reports **changes**, not levels — "deflection −6
points vs prior week; repeat contact +11%" — and includes nothing that did not
move materially. A digest with three lines that all matter is read; one with
fourteen lines of which two matter is not. Include the annotation stream so the
reader can see whether a release happened in the same week.
