# Examples — Agent Metric Dashboards

Every metric below is sourced from a real place. The most common failure in this
domain is a dashboard specification that invents a `Conversation__c` object and
a token ledger the org does not have, and is therefore never built.

The real source is **Agentforce Session Tracing**, whose data model is a
collection of Data Cloud DLOs and DMOs — including `AIAgentSession`
(session-level detail), `AIAgentSessionParticipant` (who was on the session —
Contact, Lead, or Account), `AIAgentInteraction` (turn-by-turn), and
`AIAgentInteractionMessage` (message detail)
([Data Model for Agentforce Session
Tracing](https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_data_model.htm&type=5)).
Tracing captures turns, messages, LLM calls, actions, metric scores, and
feedback.

**Prerequisite that gates everything here:** Session Tracing and the Session
Tracing Data Model are enabled under Setup → Einstein Audit, Analytics, and
Monitoring Setup, and analytics appear **only for conversations that occur
after** setup. Readers need the Data Cloud User permission set. If tracing was
switched on last week, the dashboard's history starts last week.

---

## Example 1 — WRONG vs RIGHT: where the numbers come from

### WRONG — a specification against objects that do not exist

> Source adoption and turns from `Conversation__c`. Source latency from
> `Conversation_Turn__c.duration_ms__c`. Source tokens from the Platform Event
> ledger.

Nothing here is standard. Every name is a custom object somebody would first
have to build, and the "token ledger" implies a per-call token count that is not
exposed as a standard field. The specification reads like a plan and is actually
a request for a data-engineering project, which is why dashboards written this
way do not get built.

### RIGHT — name the real source, then say what to derive

| KPI | Real source | Derivation |
|---|---|---|
| Sessions | `AIAgentSession` | Count of sessions in period |
| Turns per session | `AIAgentInteraction` | Interactions ÷ sessions |
| Deflected sessions | Agentforce Observability | Reported directly as a key insight |
| Average latency | Agentforce Observability | Reported directly as a key insight |
| Escalation rate | `AIAgentInteraction` action data | Sessions whose action sequence includes the escalation/transfer action ÷ sessions |
| Action failure rate | `AIAgentInteractionStep` | Steps with an error ÷ steps, grouped by action |
| Quality score | Session tracing metric scores | Platform-scored metrics, joined per session |
| Feedback | Session tracing feedback signals | Thumbs / survey per session |

Agentforce Observability reports total sessions, deflected sessions, and average
agent latency as first-class insights, so those three need no derivation at all —
which is the point of checking what the platform gives you before designing a
pipeline.

**What is not on this list:** a per-conversation cost in currency. See Example 5
for what to do instead of inventing one.

---

## Example 2 — Deflection without a baseline is a vanity metric

### Context

A service org deploys an agent on the "billing" queue. After a month the agent
handles 62% of conversations without an escalation. Leadership is told
deflection is 62%.

### Problem

62% of *what*? Some of those conversations would never have become a case
anyway — a customer asking "what are your opening hours" was always going to
self-serve. Some of the escalations that did happen would have been resolved by
the old IVR. The number measures the agent's behaviour, not its effect.

Worse, it moves for reasons unrelated to the agent. Marketing runs a campaign,
the question mix shifts toward simple queries, and deflection "improves" 8
points with no change to the agent.

### Solution — a holdout, with the arithmetic written down

Split at the routing layer, not by self-selection:

```text
Queue A (agent enabled)   50% of inbound, randomised at routing
Queue B (agent disabled)  50% of inbound, same routing rules otherwise

Period: 4 weeks minimum, or until each arm has >=1,000 conversations.

Escalation rate A = escalated_A / total_A
Escalation rate B = escalated_B / total_B

DEFLECTION = (rate_B - rate_A) / rate_B

Report with the arm sizes and the period. A deflection figure without
both is not interpretable.
```

### Why randomised routing and not "before vs after"

A before/after comparison confounds the agent with everything else that changed
in the same period — seasonality, a product launch, a pricing change, a
different set of customers. The holdout controls all of it simultaneously
because both arms experience the same world.

### When a holdout is not available

Sometimes it genuinely is not — a single small queue, or a regulatory
requirement to offer the agent to everyone. Then say so, and report the
*uncontrolled* number with that caveat attached to the number itself, not in a
footnote. Label the tile "Escalation rate (no control arm)" rather than
"Deflection". Renaming the tile is the honest move and it costs nothing.

---

## Example 3 — The escalation-rate trap: "no escalation" is not "success"

### Context

Deflection is 71% and rising. CSAT is 2.9/5 and falling.

### Problem

Deflection counts conversations that ended without an escalation. A user who
gave up and closed the browser produces exactly the same signal as a user whose
problem was solved. So does a user who could not find the escalation path. The
metric rises when the agent gets *worse* in a specific way, which makes it
actively dangerous as a solo KPI.

### Solution — triangulate with three signals that fail differently

```text
TILE 1  Deflection            (agent handled it — or user gave up)
TILE 2  Repeat contact 72h    (same participant, new session, same subagent)
TILE 3  Explicit feedback     (thumbs / survey, with response rate shown)

RULE ON THE DASHBOARD ITSELF:
  Deflection up + repeat-contact up  = users are giving up, not being helped.
  Deflection up + repeat-contact flat + feedback flat = genuine improvement.
  Deflection down + repeat-contact down = agent escalating more, appropriately.
```

Repeat contact is the highest-value companion metric because it is behavioural
rather than declared: it does not depend on anyone answering a survey, and a
user who was not actually helped comes back. Compute it by joining
`AIAgentSessionParticipant` to itself on the participant within a 72-hour window
and comparing the subagent (subagents were called *topics* before April 2026 —
a naming change only).

### Print the interpretation rule on the dashboard

Not in a wiki. The person reading the tile at 8am is not going to look it up,
and a deflection number without its companion is how the wrong conclusion gets
into a board deck.

---

## Example 4 — CSAT response bias, and the correction that is worth making

### Context

Post-conversation survey shows 2.4/5. The team concludes the agent is failing.

### Problem

Opt-in surveys are answered disproportionately by people with a strong opinion,
and negative opinions are stronger. A 12% response rate skewed toward the
frustrated tail measures the tail, not the population.

### Solution — show the response rate next to the score, always

```text
CSAT  2.4 / 5      n = 412      response rate 12%
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                   Never render the score without these.
```

Then add one signal that is not opt-in:

- **Platform metric scores** from session tracing, which are computed for every
  session rather than for the ones a user chose to rate.
- **Repeat contact rate**, which is behavioural and complete.

### The correction worth doing, and the one that is not

Worth doing: **randomised sampling**. Ask 20% of conversations, chosen at
random, instead of offering the survey to everyone who reaches a particular exit
path. It removes the path-based selection and costs nothing but configuration.

Not worth doing: **post-stratification weighting** by inferred sentiment. It
requires assumptions about non-respondents that you cannot test, and it produces
a number that looks authoritative and is not. If the response rate is 12%, say
12% and put a complete metric next to it.

---

## Example 5 — Cost: what is measurable, and how to avoid inventing what is not

### Context

The CFO asks for cost per conversation.

### Problem

Agentforce consumption is licensed and metered by Salesforce, not billed to you
as a per-token line item you can query in your org. A dashboard tile computing
`tokens × price` requires a token count and a price, and inventing either
produces a number that is confidently wrong — the worst possible artefact to put
in front of a CFO.

### Solution — measure the drivers you *can* see, and get the rate from billing

Split the question into two halves and be explicit about where each comes from:

```text
DRIVER SIDE  (from session tracing — measurable in your org)
  Sessions per week                      AIAgentSession
  Turns per session                      AIAgentInteraction / AIAgentSession
  LLM calls per turn                     session tracing LLM call records
  Actions per session                    AIAgentInteractionStep

RATE SIDE    (from your Salesforce contract / consumption reporting)
  Consumption rate per unit              <- NOT derivable from org data

COST TREND = driver trend x rate.
Report the DRIVER trend on the dashboard. Report absolute cost from the
consumption reporting Salesforce provides, and reconcile the two monthly.
```

### Why "LLM calls per turn" is the tile that earns its place

It is the closest thing to an intensity metric that you can actually observe,
and it is the one that moves for reasons you control. A subagent instruction
rewrite that adds a reasoning step increases LLM calls per turn without changing
session count. That is exactly the regression a cost dashboard should catch, and
it is visible without knowing the price of anything.

### The decomposition that makes a cost spike diagnosable

```text
Total work = sessions x turns/session x LLM-calls/turn

  sessions up, rest flat        -> demand grew. Usually good.
  turns/session up              -> agent needs more back-and-forth. Investigate.
  LLM-calls/turn up             -> reasoning got more expensive. Almost always
                                   a config change; correlate with the release.
```

Annotate the chart with agent-version and prompt-template activation dates. A
step change in LLM calls per turn on the day of a release is a one-glance
diagnosis; the same jump on an unannotated chart is a week of investigation.

---

## Example 6 — Exporting to an external observability platform

### Context

The org already runs Datadog. Leadership wants agent health on the same board as
the rest of the estate rather than in a separate Salesforce dashboard.

### Solution — the OpenTelemetry export endpoint

Session tracing data can be exported in OpenTelemetry (OTLP) format:

```http
GET /services/data/v66.0/einstein/audit/otel/{session-id}
```

The response conforms to the OTLP specification and returns the session's turns,
messages, LLM calls, action executions, metric scores, and feedback pre-joined
as `ResourceSpans`
([Export Agentforce Session Tracing
Data](https://developer.salesforce.com/docs/ai/agentforce/guide/otel-api.html)).

### The four constraints that shape the integration

1. **One session per request.** Bulk queries are not supported, so the exporter
   is a per-session fetch driven by a list of session ids — not a range query.
2. **72-hour window.** The API returns sessions started in the previous 72
   hours. An exporter that falls behind by four days loses that data
   permanently; alert on exporter lag, not just on exporter errors.
3. **Prerequisites.** Agentforce enabled, Data Cloud enabled, Session Tracing
   data collection activated in Setup, Audit and Feedback enabled, and OAuth 2.0
   via an external client app.
4. **Beta.** Subject to Beta Services Terms at the time of writing — design the
   integration so that the Salesforce-native dashboard remains authoritative and
   the export is a convenience, not the other way around.

Standard Connect API rate limits apply, which for a high-volume agent is the
binding constraint on how much you can export. Sample rather than exporting
every session: a stratified sample across subagents gives you the diagnostic
value at a fraction of the call volume.

---

## Anti-Pattern — one number, no denominator, no annotation

**What practitioners do:** a single large tile reading **"Deflection: 68%"**,
green, top-left of the executive dashboard.

**What goes wrong:** the number is uninterpretable and unfalsifiable. There is no
baseline, so 68% could be excellent or a regression from 74%. There is no
denominator, so it might be 68% of forty conversations. There are no
annotations, so a step change caused by a subagent rewrite looks identical to one
caused by a seasonal shift in question mix. And because deflection rises when
users give up, the tile is green in one of the failure modes it is supposed to
detect.

**Correct approach:** every KPI tile carries four things — the value, the
denominator, the comparison (prior period or control arm), and a version
annotation on the trend line. Where the metric has a known confound, print the
companion metric next to it rather than in a different section. A dashboard's job
is to make a wrong conclusion hard to reach, and a single number with no context
makes it easy.
