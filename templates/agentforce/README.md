# Agentforce shared templates

| File | What it scaffolds |
|---|---|
| `AgentSkeleton.json` | Agent definition — persona, model, topics, fallback, guardrails, evaluation |
| `AgentActionSkeleton.cls` | Canonical Apex `@InvocableMethod` action (one verb, bulk-safe, error-surfacing) |
| `AgentTopic_Template.md` | Topic discovery / anti-scope / test utterance template |

## Design rules baked into the templates

1. **One action = one verb.** The `AgentActionSkeleton` is deliberately
   single-purpose. Multi-verb "kitchen sink" actions confuse the planner.
2. **Every input/output typed and documented.** `@InvocableVariable label` and
   `description` are read by the planner — they are not decorative.
3. **Bulk API.** Actions always take `List<Request>` and return `List<Response>`.
4. **Errors are loud.** Failures are captured in `Response.success = false` +
   `errorMessage` so the planner can replan.
5. **Trust Layer respected.** The agent definition enables PII masking,
   toxicity blocking, and prompt-injection prevention by default.
6. **Evaluation is part of the spec.** `testUtterances` + `minAccuracy`
   thresholds are declared in the agent definition, not an afterthought.

## Relationship to the Apex templates

`AgentActionSkeleton.cls` uses `ApplicationLogger.error(...)` — deploy
`templates/apex/ApplicationLogger.cls` + `Application_Log__c` first.
