# Well-Architected Notes — Agent Actions

## Relevant Pillars

- **Reliability** - stable names, schemas, and result handling improve tool selection and recovery.
- **Security** - side-effecting actions need confirmation and least-privilege boundaries.
- **Operational Excellence** - a smaller, clearer action set is easier to review and evolve.

## Architectural Tradeoffs

- **Many actions vs few clear actions:** more actions feel powerful, but reduce tool selection quality when they overlap.
- **Flow action vs Apex action:** Flow is easier to own declaratively, while Apex gives tighter service contracts and control.
- **Throwing exceptions vs structured results:** exceptions are simple for developers, but structured results are usually safer for conversational recovery.

## Anti-Patterns

1. **Generic catch-all actions** - they blur business capabilities and degrade selection quality.
2. **Prompt-based mutation behavior** - generation and operational side effects become dangerously mixed.
3. **No confirmation design for destructive work** - the agent can move too quickly from intent to side effect.

## Official Sources Used

- Agentforce Developer Guide - https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services - https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- InvocableMethod Annotation - https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
