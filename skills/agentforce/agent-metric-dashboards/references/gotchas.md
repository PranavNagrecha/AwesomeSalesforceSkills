# Gotchas: Agent Metric Dashboards

Platform facts carry a cited source. Measurement-design lessons (deflection, baselines, CSAT, alerting) are reasoning about the data rather than Salesforce behaviour; each says which platform fact it builds on and marks the rest UNVERIFIED where a claim needs a source.

---

## Gotcha 1: Session tracing history starts when you turn it on

**What happens:** The dashboard is built in week six and its trend starts in week five, because that is when someone enabled tracing. The launch period everyone wants to compare against is missing.

**When it occurs:** Tracing is treated as a dashboard task instead of a go-live task.

**How to avoid:** Make enabling Agentforce Session Tracing a pre-activation checklist row (`agentforce/agent-deployment-checklist`). If it was missed, print the data start date on the dashboard rather than letting a truncated trend imply a launch date.

**Source:** Agentforce Developer Guide, Export Agentforce Session Tracing Data (Beta): tracing is a setting under Setup > Einstein Audit, Analytics, and Monitoring Setup. UNVERIFIED (2026-10-03): the earlier statement, sourced to a Help article that does not fetch, that analytics appear only for conversations after setup with no backfill.

---

## Gotcha 2: Readers see an empty dashboard without Data Cloud access

**What happens:** The dashboard works for its builder and shows nothing for the executives it was built for.

**When it occurs:** Readers lack the Data Cloud permissions the underlying reports need.

**How to avoid:** Add the required Data Cloud permission set to the rollout's permission set group and verify with a real reader before the first review. Share the report folder too: the standard Copilot dashboards live in the Copilot for Salesforce Apps folder, which must be shared for others to see them.

**Source:** Generative AI guide (Spring '26), Agentforce Analytics ("Agentforce Analytics uses Data Cloud data"; share the Copilot for Salesforce Apps folder so other people can see the reports). UNVERIFIED (2026-10-03): the specific permission set name "Data Cloud User" from the earlier version.

---

## Gotcha 3: "Deflected" rises when the agent gets worse

**What happens:** Deflection climbs from 58 to 71 percent in a month while CSAT falls and repeat contacts rise 40 percent.

**When it occurs:** Deflection is rendered alone.

**How to avoid:** Pair deflection with the 72-hour repeat-contact rate on the same tile, and print the interpretation rule on the tile. A user who gave up and a user who was helped can produce the same session ending.

**Source:** Data Cloud DMO reference, AI Agent Session DMO: `ssot__AiAgentSessionEndType__c` is "the reason the session ended. Possible values are resolved, escalated, deflected, and other." The interpretation risk is analysis, not a documented behaviour.

---

## Gotcha 4: Deflection with no control arm measures the world, not the agent

**What happens:** Deflection improves 8 points after a marketing campaign shifted the question mix. Nothing about the agent changed.

**When it occurs:** There is no randomized holdout.

**How to avoid:** Randomize at the routing layer, sending a fraction of inbound to an agent-disabled path, and report the difference between arms. Without a holdout, relabel the tile "Escalation rate (no control arm)".

**Source:** Measurement design. UNVERIFIED (2026-10-03): no Salesforce source covers holdout design for agents.

---

## Gotcha 5: Before-and-after comparisons confound everything that changed in between

**What happens:** "Escalation was 40 percent before the agent and 30 percent now" ignores a new portal, a pricing change and a seasonal peak.

**When it occurs:** A historical baseline stands in for a control.

**How to avoid:** Prefer a concurrent control arm. If only a historical baseline exists, list the confounds next to the number, not in a footnote.

**Source:** Measurement design. UNVERIFIED (2026-10-03): not a Salesforce behaviour claim.

---

## Gotcha 6: Thumbs-up rates and CSAT measure the people who answered

**What happens:** Satisfaction reads poorly and a remediation project is funded; the response rate was 12 percent and skewed toward one frustrating exit path.

**When it occurs:** A satisfaction score is shown without its sample size and response rate.

**How to avoid:** Show `n` and the response rate in the same tile. Add one complete signal computed for every session, such as end type or platform metric scores.

**Source:** Generative AI guide, Agentforce Analytics Reports: Satisfaction Rate is "Percentage of thumbs up out of all implicit feedback given", and Implicit Feedback Over Time counts thumbs up and down per day; Utterance Analysis needs Feedback turned on. The bias argument is analysis.

---

## Gotcha 7: Currency cost tiles are usually invented, but token counts are now real

**What happens:** A "cost per conversation: $0.42" tile that nobody can trace, built from a guessed price.

**When it occurs:** A currency rate is assumed from public model prices.

**How to avoid:** Report drivers: sessions, turns per session, LLM calls per turn and tokens. Take absolute cost from Salesforce consumption reporting (Digital Wallet) and reconcile monthly.

**Correction:** the earlier text said no per-token data is queryable. In Spring '26 and later, the AI Agent Generative AI Usage DMO (`AiAgentGenerativeAiUsage_std__dlm`) holds prompt input, completion and total token counts per request, with model, agent and billable flags. It still holds no currency rate.

**Source:** Data Cloud DMO reference, Ai Agent Generative Ai Usage DMO (available in 260 and later); Generative AI guide, Generative AI Billable Usage Types (usage is monitored in Digital Wallet; credits are units times the rate-card multiplier).

---

## Gotcha 8: A model change moves every metric with no deployment on your side

**What happens:** Latency, verbosity and quality shift overnight and Git shows no change.

**When it occurs:** Trend charts carry no annotations.

**How to avoid:** Annotate trends with agent version activations, prompt template activations and model changes. Track `GenAiGatewayModelName__c` from the usage DMO as its own series so a model switch is visible.

**Source:** Data Cloud DMO reference, Ai Agent Generative Ai Usage DMO (`GenAiGatewayModelName__c`, `ModelProviderModelName__c`). UNVERIFIED (2026-10-03): how often or with what notice underlying models change.

---

## Gotcha 9: Average latency hides the tail that drives abandonment

**What happens:** Average latency is 1.8 seconds while p95 is 11 seconds, and the slow 5 percent abandon.

**When it occurs:** The standard Latency report (an average) is the only latency tile.

**How to avoid:** Compute p50 and p95 from per-interaction start and end timestamps. Separate agent latency from action latency using step timestamps, because the owners and fixes differ.

**Source:** Generative AI guide, Agentforce Analytics Reports (Latency: "Average duration in seconds between the moment a request is submitted and the delivery of its corresponding response"); Data Cloud DMO reference, AI Agent Interaction and Interaction Step DMOs (start and end timestamps).

---

## Gotcha 10: Platform-scored quality drifts from human judgement

**What happens:** A quality score holds steady for six months while supervisors say answers got worse.

**When it occurs:** The score is never compared with human ratings.

**How to avoid:** Have a person rate a random sample of sessions each quarter and report the correlation with the platform score as "score reliability".

**Source:** Measurement design. Related platform fact: Testing API results "may change" because of continuous improvements to the testing service (Agentforce Developer Guide, Considerations for the Testing API).

---

## Gotcha 11: The OTel export is one session per call, within 72 hours

**What happens:** An exporter built for range queries cannot work, and it loses data permanently when it falls more than three days behind.

**When it occurs:** The export is designed like a bulk extract.

**How to avoid:** Get session IDs from a query, export them one by one, and alert on exporter lag as well as errors. Keep the Salesforce-native dashboard authoritative while the API is Beta.

**Source:** Agentforce Developer Guide, Export Agentforce Session Tracing Data (Beta): `GET /services/data/v66.0/einstein/audit/otel/{session-id}`; single-session queries only; sessions started within the previous 72 hours; Connect API rate limits apply.

---

## Gotcha 12: Untuned alert thresholds become alerts nobody reads

**What happens:** An alert fires weekly, the channel is muted, and a real regression later fires into silence.

**When it occurs:** Thresholds are round numbers with no owner.

**How to avoid:** Give every alert an owner and a four-week review: did it fire, and was each firing actionable? Derive thresholds from the observed distribution.

**Source:** Operational practice. UNVERIFIED (2026-10-03): not a Salesforce behaviour claim.

---

## Gotcha 13: Aggregating across subagents hides the broken one

**What happens:** The overall action failure rate is 3 percent; one subagent's is 34 percent on 8 percent of traffic.

**When it occurs:** Only the aggregate is shown, or the breakdown is sorted by volume.

**How to avoid:** Put the per-subagent breakdown under every aggregate, sorted by rate, and alert on the worst subagent.

**Source:** Data Cloud DMO reference, AI Agent Interaction DMO (`ssot__TopicApiName__c`, the subagent classified per interaction) and Interaction Step DMO (`ssot__ErrorMessageText__c`). The standard Topics Usage and Actions Usage reports also break down by subagent and action (Generative AI guide, Agentforce Service Agent Reports).

---

## Gotcha 14: A weekly digest of levels becomes noise

**What happens:** A fourteen-number email nobody opens by week five.

**When it occurs:** The digest reports levels, not changes.

**How to avoid:** Report only material changes against the prior week, with the annotation stream beside them.

**Source:** Operational practice. UNVERIFIED (2026-10-03): not a Salesforce behaviour claim.

---

## Gotcha 15: Agent Analytics costs Data Cloud credits and is unavailable in some setups

**What happens:** Credit consumption rises after analytics is turned on, or analytics never appears for an agent.

**When it occurs:** Analytics is enabled without a credit plan, or the agent uses a Data Cloud One companion org or data space.

**How to avoid:** Budget the credits, and check the Data Cloud topology before promising dashboards. To stop processing, turn off Agent Analytics in the Einstein Feedback section of Setup.

**Source:** Generative AI guide, Agentforce Analytics: it "consumes credits used for billing based on your usage"; "Agent Analytics isn't available on Data Cloud One companion orgs or when Data Cloud One is selected as the data space for an agent."

---

## Gotcha 16: Builder event logs are not a reporting source

**What happens:** A team builds a monthly report from Agent Builder event logs and finds only a week of data, with conversation text hidden.

**When it occurs:** Event logs are mistaken for analytics.

**How to avoid:** Use event logs for debugging only. They store information for 7 days, and without enhanced event logs the conversation data is replaced with "Sensitive data not available". Report from the session tracing DMOs.

**Source:** Generative AI guide, Enable Enhanced Event Logs.
