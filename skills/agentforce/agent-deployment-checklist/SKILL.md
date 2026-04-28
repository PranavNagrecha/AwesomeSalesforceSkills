---
name: agent-deployment-checklist
description: "Canonical go-live checklist for Agentforce deployments with rehearsed rollback and stakeholder sign-off records. NOT for general Salesforce release management (see release-management)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Agent Deployment Checklist

A single checklist is the artifact that prevents post-deployment incidents. Organized into five blocks: functional tests green, adversarial tests green, observability live, rollback rehearsed, stakeholders signed-off.

## Adoption Signals

Every production activation; every material config change (new Invocable, new channel, new persona). Use this skill any time someone asks whether the agent is ready for production.

- Required for any change that adds a new tool to the agent's toolbox or expands record-access scope.
- Run before enabling a new channel (Service Cloud, Slack, Experience Cloud) — channel context changes the prompt-injection threat model.

## Recommended Workflow

1. Functional: ≥20 fixture conversations pass in Testing Center; per-reason-code coverage verified.
2. Security: adversarial test suite green; data classification + Trust Layer policy match the signed review.
3. Observability: dashboard deployed; alert rules active; on-call rota updated.
4. Rollback: the inverse CMDT flip has been rehearsed in staging; documented runbook exists with named owner.
5. Stakeholders: business owner, security, and SRE have signed the checklist row in the activation record (`Agent_Activation__c`).

## Key Considerations

- The checklist is an artifact, not a ritual — missing rows block activation.
- Rollback rehearsal is the most-skipped item; it's also the one that matters most in an incident.
- Stakeholder sign-off must be async-recorded (no verbal).

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

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
