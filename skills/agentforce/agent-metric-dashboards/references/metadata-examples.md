# Metadata Examples: Agent Metric Dashboards

The dashboard's numbers come from the Agentforce Session Tracing data model in Data Cloud. This file names the real objects and fields, gives a deployable calculated insight for the daily session tiles, the queries for the driver tiles, and the OpenTelemetry export call for external tools.

## The objects behind the tiles

Object and field API names below come from the Data Cloud DMO reference pages, read 2026-10-03.

| Tile | Object (API name) | Fields used | Notes |
|---|---|---|---|
| Sessions, end reason, channel | `ssot__AiAgentSession__dlm` | `ssot__StartTimestamp__c`, `ssot__EndTimestamp__c`, `ssot__AiAgentChannelType__c`, `ssot__AiAgentSessionEndType__c` | End type values are resolved, escalated, deflected and other |
| Turns per session, subagent mix | `ssot__AiAgentInteraction__dlm` | `ssot__AiAgentSessionId__c`, `ssot__AiAgentInteractionType__c` (for example Turn), `ssot__TopicApiName__c`, start and end timestamps | `TopicApiName` is the subagent classified for the turn |
| Action failure rate, LLM calls per turn | `ssot__AiAgentInteractionStep__dlm` | `ssot__AiAgentInteractionStepType__c` (UserInputStep, LLMExecutionStep, FunctionStep), `ssot__Name__c` (the action name for action steps), `ssot__ErrorMessageText__c` | Count LLMExecutionStep rows per interaction for "LLM calls per turn" |
| Message detail | `ssot__AiAgentInteractionMessage__dlm` | `ssot__AiAgentInteractionMessageType__c` (Input or Output), `ssot__ContentText__c` | Contains customer text; restrict access |
| Token drivers | `AiAgentGenerativeAiUsage_std__dlm` (available in 260, Spring '26, and later) | `PromptInputTokenCount__c`, `PromptCompletionTokenCount__c`, `PromptTotalTokenCount__c`, `GenAiGatewayModelName__c`, `AgentDeveloperName__c`, `IsBillableIndicator__c`, `Timestamp__c` | Token counts, not currency |

## Example 1: Daily sessions by channel and end type as a calculated insight

**File path:** `force-app/main/default/mktCalcInsightObjectDefs/Agent_Sessions_Daily.mktCalcInsightObjectDef-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MktCalcInsightObjectDef xmlns="http://soap.sforce.com/2006/04/metadata">
    <creationType>Custom</creationType>
    <description>Agent sessions per day by channel and end type, for the executive adoption and escalation tiles.</description>
    <expression>SELECT DATE_TRUNC('day', ssot__AiAgentSession__dlm.ssot__StartTimestamp__c) AS session_day__c,
ssot__AiAgentSession__dlm.ssot__AiAgentChannelType__c AS channel__c,
ssot__AiAgentSession__dlm.ssot__AiAgentSessionEndType__c AS end_type__c,
COUNT(ssot__AiAgentSession__dlm.ssot__Id__c) AS sessions__c
FROM ssot__AiAgentSession__dlm
GROUP BY DATE_TRUNC('day', ssot__AiAgentSession__dlm.ssot__StartTimestamp__c),
ssot__AiAgentSession__dlm.ssot__AiAgentChannelType__c,
ssot__AiAgentSession__dlm.ssot__AiAgentSessionEndType__c</expression>
    <masterLabel>Agent Sessions Daily</masterLabel>
    <system>Custom</system>
</MktCalcInsightObjectDef>
```

The type, folder and required fields (`creationType`, `expression`, `masterLabel`, `system`) come from the Metadata API reference for `MktCalcInsightObjectDef`, whose sample computes `COUNT(...) as count__c` from a DMO. UNVERIFIED (2026-10-03): calculated-insight SQL rules beyond that sample, including support for `DATE_TRUNC` and the dimension and measure naming conventions; validate the expression in the Calculated Insights builder before committing it.

How the tiles use it:

- **Sessions** is the sum of `sessions__c` per day.
- **Escalation rate** is escalated sessions over all sessions. Label it "Escalation rate (no control arm)" unless a holdout exists (see `SKILL.md`).
- **"Deflected" sessions** are the platform's own end-type classification. Show them next to the 72-hour repeat-contact rate, never alone; a user who gives up and a user who was helped can end the same way.

## Example 2: Driver queries

Run these in Data Cloud Query Editor or through the Data Cloud query API as the data source for driver tiles.

```sql
-- Turns per session and LLM calls per turn, last 7 days, by subagent.
SELECT i.ssot__TopicApiName__c AS subagent,
       COUNT(DISTINCT i.ssot__AiAgentSessionId__c) AS sessions,
       COUNT(DISTINCT i.ssot__Id__c) AS turns,
       SUM(CASE WHEN s.ssot__AiAgentInteractionStepType__c = 'LLMExecutionStep' THEN 1 ELSE 0 END) AS llm_calls
FROM ssot__AiAgentInteraction__dlm i
JOIN ssot__AiAgentInteractionStep__dlm s
  ON s.ssot__AiAgentInteractionId__c = i.ssot__Id__c
WHERE i.ssot__StartTimestamp__c >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY i.ssot__TopicApiName__c;

-- Action failure rate by action, sorted by rate (not volume).
SELECT ssot__Name__c AS action_name,
       COUNT(*) AS runs,
       SUM(CASE WHEN ssot__ErrorMessageText__c IS NOT NULL THEN 1 ELSE 0 END) AS failures
FROM ssot__AiAgentInteractionStep__dlm
WHERE ssot__AiAgentInteractionStepType__c = 'FunctionStep'
GROUP BY ssot__Name__c
ORDER BY failures * 1.0 / COUNT(*) DESC;

-- Token drivers per agent and model per day (Spring '26 and later).
SELECT AgentDeveloperName__c, GenAiGatewayModelName__c,
       CAST(Timestamp__c AS DATE) AS usage_day,
       SUM(PromptTotalTokenCount__c) AS total_tokens
FROM AiAgentGenerativeAiUsage_std__dlm
GROUP BY AgentDeveloperName__c, GenAiGatewayModelName__c, CAST(Timestamp__c AS DATE);
```

The object and field names are grounded in the DMO reference. UNVERIFIED (2026-10-03): the date arithmetic and casting syntax accepted by your Data Cloud query surface; adjust them to the dialect your query editor reports. Percentiles (p50, p95) are computed in the dashboard tool from per-interaction durations (`ssot__EndTimestamp__c` minus `ssot__StartTimestamp__c`), because a percentile function is not shown in any source read.

## Example 3: Export one session to an observability platform (Beta)

```bash
# One session ID per call; sessions that started within the previous 72 hours only.
curl -s "$INSTANCE_URL/services/data/v66.0/einstein/audit/otel/$SESSION_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -o "traces/$SESSION_ID.json"
```

The endpoint, the single-session limit, the 72-hour window, Connect API rate limits, OAuth through an external client app, and the requirement that Agentforce Session Tracing and Audit and Feedback be on all come from the Agentforce Developer Guide, "Export Agentforce Session Tracing Data (Beta)". The output is OTLP v1.0 ResourceSpans and needs no transformation for OTLP-compatible tools. Get the session list from a query first, then call the export once per session, and alert on exporter lag.

## package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Agent_Sessions_Daily</members>
        <name>MktCalcInsightObjectDef</name>
    </types>
    <version>66.0</version>
</Package>
```

## Deploy order and verification

1. Turn on Agentforce Session Tracing (and Audit and Feedback if you use feedback or the export) before the agent goes live. UNVERIFIED (2026-10-03): the Help article cited by earlier versions says analytics exist only for sessions captured after setup, with no backfill; that article does not fetch, so treat it as likely but unconfirmed.
2. Deploy the calculated insight to the org's Data Cloud, run it once, and confirm rows appear for yesterday.
3. Build the tiles on the insight and the driver queries; check a tile against Agentforce Analytics' own Total Session or Deflection Session report for the same day.
4. Confirm each intended reader can open the dashboard; Data Cloud access is permission-based.
