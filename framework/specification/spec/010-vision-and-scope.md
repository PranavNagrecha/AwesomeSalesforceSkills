# SFAEF-010 — Vision, user promise, and product scope

## Vision

Build the default engineering intelligence layer for Salesforce work performed by humans and AI agents.

The framework should make a general-purpose model behave less like a fast autocomplete system and more like a senior Salesforce delivery team that:

- understands platform-specific failure modes;
- checks the actual org, project, job, and source rather than guessing;
- separates observed fact from inference and advice;
- uses the smallest relevant context;
- obtains independent review before presenting consequential conclusions;
- produces evidence that can be inspected, replayed, and compared;
- is safe in customer environments by default;
- improves through known-truth evaluation rather than prompt folklore.

## User promise

SFAEF-010-001. The framework MUST answer Salesforce engineering questions with explicit evidence, unknowns, and confidence rationale.

SFAEF-010-002. It MUST remain useful in standalone, local-project, live-read-only, and scratch-QA modes.

SFAEF-010-003. Optional enrichment MUST never be represented as a mandatory prerequisite unless the product cannot logically operate without it.

SFAEF-010-004. A missing local Salesforce project MUST NOT prevent deployment or test-result diagnosis when sufficient job evidence exists.

SFAEF-010-005. A missing org MUST produce a truthful reduced mode, partial result, or refusal—not fabricated org state.

SFAEF-010-006. The same core product contract MUST be portable across hosts even when host capabilities differ.

## Primary users

1. **Salesforce developers** — Apex, LWC, SOQL, tests, integrations, deployments.
2. **Admins and declarative builders** — Flow, permissions, data model, reports, routing, configuration.
3. **Architects and technical leads** — impact analysis, automation architecture, security, org health, release decisions.
4. **Consultants and system integrators** — fast discovery, evidence packets, cross-client consistency, knowledge capture.
5. **DevOps and release teams** — failed deployment/test diagnosis, readiness, environment comparison, auditability.
6. **Agentforce builders** — agent metadata, actions, tests, traces, security, and release quality.
7. **Maintainers and contributors** — currency, source governance, evals, skill quality, adapter compatibility.

## Jobs to be done

The framework is organized around jobs, not inventory:

- “Tell me why this deployment failed and what to do first.”
- “Why are these Apex tests failing together?”
- “Why can this user not see or edit this record/field/action?”
- “What breaks if we change or remove this component?”
- “What actually executes in this transaction, and where is the risk?”
- “Are we ready to release?”
- “What changed between these orgs?”
- “What is the likely cause of this integration incident?”
- “Did this migration reconcile correctly?”
- “Is this Agentforce agent/action safe, testable, and deployable?”

## In scope for V2

SFAEF-010-020. V2 MUST provide a host-native Cursor product and preserve/strengthen Claude compatibility.

SFAEF-010-021. V2 MUST provide the six flagship products defined in `products/README.md`, with at least the first three behaviorally qualified before a 1.0 claim.

SFAEF-010-022. V2 MUST provide a deterministic core for contracts, context, evidence, policy, state, redaction, telemetry, and review packaging.

SFAEF-010-023. V2 MUST provide read-only Salesforce evidence tools for the shipped products.

SFAEF-010-024. V2 MUST provide a protected scratch-org behavioral QA lane.

SFAEF-010-025. V2 MUST provide a public, reproducible benchmark format even when some datasets remain private.

## Explicitly outside ordinary product execution

- Automatic production deployment or quick deploy.
- Customer-org DML, metadata mutation, permission changes, or anonymous Apex.
- Hidden autonomous background execution.
- Unreviewed self-modification of skills, policies, or eval labels.
- Claims that a model is “accurate” without a published dataset, date, host/model version, and scoring method.
- A forced rewrite of all existing commands, agents, or decision trees solely for architectural cleanliness.

## Long-term scope

Future versions may support approved changes through a separate action broker with human approval, least privilege, dry-run, rollback, and policy evidence. That capability is not implied by V2 and cannot be smuggled into read-only tools.
