---
name: agent-security-review
description: "Pre-production security checklist for Agentforce deployments: agent run-as permission scope, grounding-source data classification, action write-scope, audit trail. NOT for the full go-live readiness gate covering cost telemetry, rate limits, rollout and rollback — use agentforce/agentforce-production-readiness-checklist. NOT for a general org security review — use security/security-health-check."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "agent go-live security checklist"
  - "review what data the agent can see"
  - "does the agent leak pii"
  - "quarterly agentforce audit"
  - "review the agent user's permissions before go-live"
  - "check which records my Agentforce agent can see"
tags:
  - agentforce
  - security
  - review
  - checklist
inputs:
  - "Agent configuration export"
  - "persona + channel map"
  - "data classification"
outputs:
  - "Signed-off review doc"
  - "remediation ticket list"
dependencies: []
version: 1.1.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Agent Security Review

Agentforce agents touch user PII, internal data, and external APIs with the permissions of whatever user invokes them. A structured review covers four axes: (1) least-privilege user, (2) data classification of every grounding source, (3) action write-scope, (4) audit trail completeness.

## Questions to Ask Before Configuring

Ask these before the review starts. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which user does each agent run as, and who else can open it?" | The agent user determines access; employee-agent access is a permission that drifts (Gotchas 1, 11) | The agent user, its permission sets, and the groups granted `agentAccesses` | Access that is provably narrow, re-checked by query each release |
| "Which fields are regulated, and does any grounding path select them?" | Trust Layer masking is disabled for agents, so exclusion is the only control (Gotcha 4) | A regulated-field list checked against field permissions and selector projections | A guarantee that no prompt can contain those values |
| "Which subagents act on a customer's own records, and how is the customer verified?" | Without rule expressions, unverified users reach those subagents (Gotcha 7) | The verification action, its variable, and the gated subagents | Identity checks enforced by the planner, not by instructions |
| "What API version is each action class, and does it declare sharing and access mode?" | API 67.0 changed the defaults (Gotcha 5) | A table of class, version, sharing keyword and access mode | Consistent enforcement that does not depend on save version |
| "What must be kept for audit, for how long, and how is it deleted?" | Builder event logs last 7 days; audit data holds full prompts and responses (Gotcha 2) | A retention and deletion decision per data class | Answerable incident and subject-access requests |
| "Which retrievers and data spaces does the agent use?" | Retriever access follows Data Cloud permissions, not CRM sharing (Gotcha 8) | The retriever list with its permission sets and data-category scoping | Grounding that cannot surface content the CRM model hides |

## Recommended Workflow

1. Export the agent: subagent instructions (subagents were called topics before April 2026), Invocable actions, grounding DMOs/sObjects, channel configs. Checksum and archive.
2. Map the agent's run-as user to a dedicated permission set; verify no profile-level permissions leak through.
3. Classify every grounding source: public, internal, confidential, regulated. Keep confidential and regulated fields out of the agent user's field permissions and out of every grounding selector. Trust Layer data masking is disabled for agents, so it is not a control here (Generative AI guide, Trust and Agents; this corrects the earlier instruction to mask at the Trust Layer).
4. Enumerate Invocable write scope: which sObjects/fields can be created/updated/deleted. Apply FLS + CRUD checks in Apex; tighten or split the user. Record each action class's API version, because API 67.0 changed the default access mode and sharing behaviour. Confirm sensitive subagents are gated by rule expressions in the planner bundle (`references/metadata-examples.md`, Example 4).
5. Verify audit trail: every Invocable logs to a custom audit object you define (for example `Agent_Audit__c`); generative AI audit data collection is on if prompts and responses must be kept, and its deletion path is documented; where Event Monitoring is licensed, `EventLogFile` data (ApexExecution, ContentTransfer) is retrieved into the SIEM.
6. Store the evidence: the permission sets, the effective-access query results and the planner-bundle findings live beside the agent metadata so the next review is a diff.

## Key Considerations

- Service agents run as their agent user, which "determines what your agent can access and do" (Generative AI guide). UNVERIFIED (2026-10-03): the earlier statement that the default run-as is the invoking user; it may describe employee agents, which the guide says act on behalf of users. Either way, review the identity that actually executes each action, and never test with an admin.
- Data Cloud grounding can pull data the CRM user cannot see: access to retrievers and their data is controlled by Data Cloud permission sets, not CRM sharing. Review data spaces and retriever permissions separately.
- Invocables bypass `with sharing` if written as `without sharing` — audit every action class's sharing declaration.
- Audit trail must include prompt + response for forensic replay; conversation storage has retention implications (GDPR).

## Worked Examples (see `references/examples.md`)

- *Write-scope tightening* — Service agent can 'Update any Case field' via a generic UpdateRecord action.
- *Regulated-field masking* — RAG grounding includes Contact.Social_Security_Number__c.

## Common Gotchas (see `references/gotchas.md`)

- **Agent run-as has View All** — Agent sees cross-owner records even when user shouldn't.
- **Conversation retention unset** — GDPR subject request cannot locate conversation logs.
- **Shield Event Monitoring not streamed** — Agent anomaly is invisible to SOC.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Running the agent as the invoking user by default — privileged reviewers leak permissions upward.
- Generic 'UpdateRecord' actions — any field becomes attack surface.
- Skipping DMO classification — grounding becomes a data-leak vector.

## Official Sources Used

See `references/well-architected.md` for the sources read for this revision.
