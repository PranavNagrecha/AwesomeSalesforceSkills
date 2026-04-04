# Well-Architected Notes — Custom Agent Actions Apex

## Relevant Pillars

- **Security** — Agent actions execute in a specific user context (logged-in user for Employee Agents, service agent user for Service Agents). Using `with sharing` and `WITH USER_MODE` ensures data is scoped to the appropriate user context rather than exposing all records. Callout authentication must use Named Credentials — never hardcoded credentials.
- **Reliability** — Structured error outputs (success/errorMessage pattern) rather than exceptions give the agent a reliable signal to respond to failures. Unhandled exceptions produce generic error messages and prevent the agent from surfacing useful information to the user.
- **Operational Excellence** — Descriptive labels and descriptions on every `@InvocableMethod` and `@InvocableVariable` are operationally essential — they directly influence the agent's invocation accuracy at runtime.

## Architectural Tradeoffs

**Single-responsibility actions vs multi-step actions:** The Atlas Reasoning Engine decides which action to invoke based on the description. A multi-step action with a vague description will be invoked incorrectly. Single-responsibility actions with precise descriptions are more reliably invoked. Accept the trade-off of more actions in exchange for more predictable agent behavior.

**Synchronous action vs async job with tracking ID:** Agentforce actions are synchronous. A long-running operation (e.g., document generation, batch data processing) will time out. The architectural pattern is to launch a Queueable job and return a tracking ID immediately. The agent then has a "check status" action to poll for results. This adds action complexity but is required for any operation > a few seconds.

## Anti-Patterns

1. **Throwing exceptions from action methods** — an unhandled exception in an @InvocableMethod produces a generic "action failed" signal to the agent. The agent cannot surface the error to the user and cannot retry with different inputs. Always return structured output with `success = false` and `errorMessage = <specific message>`.
2. **Blank label and description on @InvocableMethod** — the Atlas Reasoning Engine uses the label and description as the action's tool card. A blank description means the agent has no basis for deciding when to invoke the action, leading to random invocations or no invocations.
3. **Monolithic action that performs multiple operations** — combining "create case, assign to queue, send notification email, and update account status" in one action is impossible for the LLM to invoke correctly when only one step is needed. Single-responsibility actions compose correctly; monolithic actions invoke unpredictably.

## Official Sources Used

- Agentforce Developer Guide (@InvocableMethod for agents) — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Apex Developer Guide (InvocableMethod Annotation) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
