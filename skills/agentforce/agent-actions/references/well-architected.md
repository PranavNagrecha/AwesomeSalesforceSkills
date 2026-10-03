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

Read and checked on 2026-10-03 for this revision:

- Generative AI guide, Spring '26: Agent Actions, Agent Action Assignments, Add an Action to a Topic, Create a Custom Action for Agents (settings table, Require user confirmation), Best Practices for Agent Action Instructions, Editing Standard Agent Action Reference Actions, Agent Actions and Large Language Model Use, Considerations for Custom Actions, Considerations for Agent Conversations, Agents Limits, Trust and Agents, Activate or Deactivate Your Agent, Best Practices for Writing Topic Instructions, Troubleshooting Agents: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Metadata API Developer Guide, Summer '26 (API 67.0), GenAiFunction (`isConfirmationRequired`, input and output schema properties): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide, Summer '26 (API 67.0), InvocableMethod Annotation and InvocableVariable Annotation (list inputs, error wrapping, size and order): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Object Reference, Summer '26, Task (WhatId, Subject, ActivityDate, ReminderDateTime, IsReminderSet, Status default Not Started) and Case (CaseNumber): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Agentforce Developer Guide, Create Custom Actions Using Apex InvocableMethod: https://developer.salesforce.com/docs/ai/agentforce/guide/agent-invocablemethod.html
- Agentforce Developer Guide, Agent Script Blocks (access block, agent runs in the context of a user): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html
- Agentforce Developer Guide, Enhance the Agent UI with Custom LWCs and Lightning Types: https://developer.salesforce.com/docs/ai/agentforce/guide/lightning-types.html

### Carried forward from earlier versions (not re-read on 2026-10-03)

These were not re-read for this revision. help.salesforce.com articles do not return their text to a fetch, so claims that rest only on a Help article are marked UNVERIFIED in the skill.

- Agentforce Developer Guide - https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services - https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- InvocableMethod Annotation - https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
