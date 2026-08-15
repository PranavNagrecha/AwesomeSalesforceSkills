# Well-Architected Notes — Agent Metric Dashboards

## Relevant Pillars

### Operational Excellence

A KPI dashboard's job is not to display numbers — it is to make a wrong
conclusion hard to reach. Two design properties do most of that work:

- **Every metric carries its confound next to it.** Deflection next to
  repeat-contact rate; CSAT next to response rate; aggregate next to the
  per-subagent breakdown (subagents were called *topics* before April 2026). A
  reader who has to open a second view to interpret the first will not.
- **Every trend carries its event stream.** Agent version activations, prompt
  template activations, and model version changes overlaid on the chart. Model
  versions can move with no deployment on your side, so an unannotated step
  change is a week of investigation for a cause that is not in the repository.

The prerequisite that makes all of it possible is non-negotiable and
non-retroactive: Session Tracing and its data model must be enabled before the
conversations you want to measure occur. That places dashboard enablement on the
**deployment** checklist, not on the analytics backlog.

### Performance

The dashboard is the primary detector for two regressions that no test catches:
latency drift and reasoning-cost drift. Both are usually caused by configuration
rather than code — an added instruction, an extra action in a subagent, a grounding
source that returns more content.

`LLM calls per turn` is the highest-signal tile in this pillar. It is
observable, it moves for reasons you control, and a step change on the day of a
release is a one-glance diagnosis. Percentiles matter more than means: p95 is
where abandonment lives, and the mean is precisely the statistic that hides it.
Separate agent latency from action latency, because they have different owners
and different fixes.

### Cost Optimization

Agentforce consumption is licensed and metered by Salesforce rather than exposed
as a queryable per-token cost in your org. The honest architecture splits the
question:

| Side | Source | On the dashboard? |
|---|---|---|
| Drivers — sessions, turns/session, LLM calls/turn, actions/session | Session tracing | Yes, as trends |
| Rate per unit | Contract / consumption reporting | No — reconcile monthly |

Decomposing total work as `sessions × turns/session × LLM-calls/turn` is what
makes a spike diagnosable. Demand growth, conversational inefficiency, and
reasoning bloat are three different problems with three different owners, and
the aggregate figure distinguishes none of them.

Reporting a currency figure derived entirely from org data means reporting an
assumed rate as a measurement. In front of a CFO that is worse than reporting
nothing.

### Reliability

Metric validity is itself a dependency that can fail silently. Two cases:

- **Deflection is a proxy that inverts.** It rises when users abandon. A
  dashboard that reports it alone is green during one of the failures it exists
  to detect.
- **Platform-scored or LLM-judged quality drifts from human judgement.** The
  score stays stable while the thing it measures changes underneath it.

Both are addressed the same way — by measuring the measurement. Repeat-contact
rate validates deflection because it is behavioural and complete. A quarterly
human rating of ~50 random sessions validates the quality score, and its
correlation belongs on the dashboard as a "score reliability" figure.

---

## Architectural Tradeoffs

### Native dashboard vs. exported telemetry

| | Salesforce-native | OTel export to an external platform |
|---|---|---|
| Setup cost | Low | Integration, auth, exporter ops |
| Joins to org data | Native | Requires re-import |
| Fits existing observability estate | No | Yes |
| Bulk retrieval | Native | **One session per request** |
| Retention for export | N/A | **72-hour window** |
| Maturity | GA | Beta at time of writing |

The export endpoint is
`GET /services/data/v66.0/einstein/audit/otel/{session-id}`, single-session
only, limited to sessions started in the previous 72 hours, and subject to
standard Connect API rate limits
([Export Agentforce Session Tracing
Data](https://developer.salesforce.com/docs/ai/agentforce/guide/otel-api.html)).

Those constraints make "export everything" impractical at volume. Sample
stratified across subagents, alert on **exporter lag** rather than only on
errors — a stalled exporter returning 200s loses data permanently once the
window passes — and keep the native dashboard authoritative while the export is
Beta.

### Holdout arm vs. shipping to everyone

A holdout costs a slice of the agent's benefit for the duration of the
experiment and is the only way to make a causal deflection claim. Four weeks of
50/50 is usually enough and is a fixed, bounded cost. Without it, the metric
measures the world.

Where a holdout is genuinely unavailable — a single small queue, a regulatory
requirement — the correct response is to rename the tile, not to caveat it. A
tile called "Escalation rate (no control arm)" cannot be misquoted as
deflection; a tile called "Deflection" with a footnote will be.

### Opt-in survey vs. behavioural signal

Surveys give you the user's stated experience and a biased sample. Behavioural
signals — repeat contact, abandonment, session length — are complete and
indirect. Run both, but weight decisions toward the behavioural signal, because
its denominator is the whole population.

Randomised survey sampling is the cheap correction and worth doing.
Post-stratification weighting is not: it requires untestable assumptions about
non-respondents and produces a number that looks more authoritative than the raw
one while being less defensible.

### Aggregate simplicity vs. dimensional truth

Executives want one number; one number hides the broken subagent. The resolution
is layered rather than either/or — aggregate tile, per-subagent row sorted by
rate, alert on the worst. Sorting by volume is the specific mistake that
recreates the problem inside the breakdown.

### Alert sensitivity vs. alert survival

Every false positive spends credibility. An alert with an 80% false-positive
rate is muted within a quarter, and the mute takes the true positives with it.
Derive thresholds from the observed distribution rather than from round numbers,
give every alert a named owner and a four-week review, and treat deleting a bad
alert as a positive act.

---

## Anti-Patterns

1. **A specification against invented objects.** `Conversation__c` and a token
   ledger are a data-engineering project, not a dashboard. The real source is
   the Session Tracing data model.

2. **Deflection alone.** Rises when users give up; needs both a control arm for
   causality and repeat-contact rate for interpretation.

3. **Currency cost derived from org data.** Contains an assumed rate presented
   as a measurement.

4. **Mean latency.** Hides the tail that drives abandonment.

5. **Uncalibrated quality scores.** An unvalidated proxy silently becomes an
   unmonitored dependency of every decision made from it.

6. **Unannotated trends.** Model version changes arrive without a deployment;
   without an overlay, every step change is an investigation.

7. **Assuming history exists.** Tracing records nothing before it was enabled,
   which makes dashboard enablement a go-live prerequisite.

---

## Hygiene

- Named owner for the dashboard; named owner for each alert.
- Weekly digest reports **changes**, not levels, and omits anything that did not
  move materially.
- Alert review at four weeks: did it fire, was every firing actionable.
- Quarterly human calibration of the quality score; correlation published.
- Data Cloud User permission set verified against a real reader before the first
  review meeting.

---

## Related

- `agentforce/agentforce-observability` — the platform's own session tracing,
  Agent Analytics, and health monitoring, which this dashboard sits on top of.
- `agentforce/agentforce-eval-harness` — offline scoring of answer quality, the
  input to the quality KPI.
- `agentforce/agent-deployment-checklist` — where "tracing enabled before
  activation" and "dashboard has a named owner" become blocking rows.
- `agentforce/agentforce-prompt-versioning` — the activation events that
  annotate the trend charts.
- `admin/reports-and-dashboards-fundamentals` — the reporting mechanics, once
  the data model question is settled.

---

## Official Sources Used

- About Agentforce Session Tracing (Help) — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_about.htm&type=5
- Set Up Agentforce Session Tracing (Help) — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_setup.htm&type=5
- Data Model for Agentforce Session Tracing (Help) — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_data_model.htm&type=5
- Get Insights from Agent Session Tracing Data (Help) — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_use.htm&type=5
- Export Agentforce Session Tracing Data (OTel API) — https://developer.salesforce.com/docs/ai/agentforce/guide/otel-api.html
- Data Model and Calculated Fields for Agent Analytics (Help) — https://help.salesforce.com/s/articleView?id=ai.generative_ai_agent_analytics_data_model.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
