---
name: agent-deployment-checklist
description: "Canonical go-live checklist for Agentforce deployments with rehearsed rollback and stakeholder sign-off records. NOT for the technical pre-prod verification behind those sign-off rows — cost telemetry, rate limits, canary rollout, latency benchmarks — use agentforce/agentforce-production-readiness-checklist. NOT for general Salesforce release management — use devops/release-management."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "is my agent ready for production"
  - "agentforce go-live checklist"
  - "what sign-offs does agent deploy need"
  - "agent rollback rehearsal"
tags:
  - agentforce
  - deployment
  - checklist
  - go-live
inputs:
  - "Agent configuration export"
  - "test results"
  - "runbooks"
outputs:
  - "Signed checklist"
  - "activation record"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Agent Deployment Checklist

A single checklist is the artifact that prevents post-deployment incidents. Organized into five blocks: functional tests green, adversarial tests green, observability live, rollback rehearsed, stakeholders signed-off.

## Adoption Signals

Every production activation; every material config change (new Invocable, new channel, new persona). Use this skill any time someone asks whether the agent is ready for production.

- Required for any change that adds a new tool to the agent's toolbox or expands record-access scope.
- Run before enabling a new channel (Service Cloud, Slack, Experience Cloud) — channel context changes the prompt-injection threat model.

## What Makes Agent Deployment Different

Three platform behaviours, none of which apply to an ordinary Salesforce
release, and all of which are documented in
[Retrieve and Deploy Agent Metadata](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-deploy-metadata.html):

1. **A committed agent cannot be edited.** *"You can't edit a committed agent.
   Instead, create and edit a new version."* There is no quick-fix path — a
   hotfix costs a full release cycle, so plan the incident response accordingly.
2. **Two version counters must be paired by hand.** Saves increment
   `AiAuthoringBundle`; commits increment `Bot`/`BotVersion`. If you save more
   than you commit they diverge and you must specify both numbers explicitly.
3. **Observability is not retroactive.** Session Tracing records only
   conversations occurring after the data model is set up, so it is a
   pre-activation prerequisite rather than an incident response.

Also: the manifest needs **API version 66.0 or later** for `GenAiPlannerBundle`
and the new agent metadata types — sourced from
[The New Agentforce Metadata and Development Lifecycle](https://developer.salesforce.com/blogs/2025/03/the-new-agentforce-metadata-and-development-lifecycle),
not from the *Retrieve and Deploy Agent Metadata* guide page cited above, whose
own example shows `<version>65.0</version>`. Wildcards on `ApexClass`/`Flows`/
`GenAiPromptTemplates` cause deploy timeouts, deploying a lone `BotVersion`
requires the full agent to be present already, and retrieved agent metadata must
not be hand-edited.

## Recommended Workflow

1. **Functional.** `sf agent test run --wait` green on the routing, golden, and
   adversarial `AiEvaluationDefinition` suites. Record the run id on the
   activation record.
2. **Security.** Adversarial suite green; PII classification register reviewed
   against the *channel set this activation covers*. A channel is part of the
   approved condition, not a later configuration tweak.
3. **Runtime user.** Verify the agent user in the target org for Apex class
   access, object CRUD, **field-level** access, Flow and Named Credential
   access, record sharing, and the Data Cloud User permission set. Confirm by
   invoking each action once as that user — the only check that covers CRUD,
   FLS, and sharing together. This is the most common cause of "deploy
   succeeded, agent broken."
4. **Observability.** Session Tracing and the Session Tracing Data Model enabled
   *before* activation, proven with synthetic traffic that appears in the trace
   data. Alert rules fired at least once and receipt confirmed by the on-call
   person.
5. **Rollback.** Rehearsed in a Partial or Full sandbox with a recorded refresh
   age. Capture the measured duration **and** the inventory of what did *not*
   revert — Apex, custom fields, and activated prompt templates stay at the new
   version.
6. **Sign-off.** Business owner, security, and SRE lookups populated on
   `Agent_Activation__c`, with a validation rule that blocks save when any gate
   result is null.

## Key Considerations

- The checklist is enforced by a validation rule on the activation record, not
  by a document. A checklist that cannot block is a memory aid, and memory aids
  fail under exactly the pressure that makes the rows matter.
- Rollback reverts the agent and nothing that shipped with it. Prefer additive
  action changes so the rollback surface stays one artefact wide.
- Retaining the prior version *is* the rollback plan, because a committed
  version cannot be edited. Retire old versions on a date, not on instinct.
- Sign-off must be queryable, immutable, and linked to a specific version. Chat
  is none of the three.

## Worked Examples (see `references/examples.md`)

- *Rollback rehearsal* — Agent v2 activation.
- *Stakeholder sign-off record* — Quarterly audit.

## Common Gotchas (see `references/gotchas.md`)

- **Staging differs from prod** — Rehearsal green, prod rollback fails.
- **Alert rules not enabled until after go-live** — First incident is observed by a customer.
- **Sign-off via Slack, no record** — Post-mortem cannot reconstruct the decision chain.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Verbal sign-offs.
- Skipping rollback rehearsal because 'the change is small'.
- Dashboards deployed post-activation.

## Official Sources Used

- Retrieve and Deploy Agent Metadata — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-deploy-metadata.html
- Agentforce Metadata Types — https://developer.salesforce.com/docs/ai/agentforce/references/agents-metadata-tooling/agents-metadata.html
- Manage an Agent (Agentforce DX) — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-manage.html
- Set Up Agentforce Session Tracing — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_setup.htm&type=5
- Run Agent Tests (Agentforce DX) — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-test-run.html
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=ai.agent_testing_center.htm&type=5
