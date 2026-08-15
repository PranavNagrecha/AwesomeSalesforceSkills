# Well-Architected Notes — Agent Deployment Checklist

## Relevant Pillars

### Operational Excellence

The checklist is only a control if something enforces it. Its rows belong on a
record with a validation rule, not in a document — because the rows matter most
under release pressure, which is exactly the condition under which a document is
skipped.

Three properties distinguish this checklist from a general release checklist,
and all three come from platform behaviour rather than from process preference:

1. **Irreversibility.** A committed agent cannot be edited; every change is a
   new version. There is no "quick fix" path, so the incident plan must budget a
   full release cycle.
2. **Non-retroactivity.** Session Tracing records only conversations that occur
   after the data model is set up. Observability enabled during an incident
   produces data starting from the incident, so it is a prerequisite, not a
   response.
3. **Partial reversion.** Activating a prior agent version reverts the agent and
   nothing else that shipped with it. Rollback is therefore an inventory, not a
   single step.

The activation record turns each of these into a queryable fact. "Show every
activation last quarter where rollback was not rehearsed" is a report; the same
question against a chat history is an interview.

### Reliability

The three most common antecedents of an agent incident are all things the
checklist makes visible:

| Antecedent | Checklist row that catches it |
|---|---|
| Runtime user lacks field-level access | Invoke each action as that user in the target org |
| Rollback never exercised | Measured rehearsal with a "did not revert" inventory |
| Version pair mismatched | Both counters recorded at commit, read by the deploy script |

Rollback rehearsal is both the most-skipped row and the one that changes an
incident's shape most. It converts "we have a rollback" (a belief) into "rollback
takes 4 minutes and leaves the Apex at the new version" (two facts you can plan
around). The rehearsal's value is almost entirely in the second fact — the
duration is nice to know, the side-effect inventory is what prevents the second
incident.

Sandbox representativeness matters more for agents than for code, because agent
behaviour depends on retrieved content. A rehearsal in a sandbox with three
Knowledge articles proves the mechanics and nothing about the grounding. Record
the sandbox type and refresh age so a reviewer can weight the evidence rather
than assume it.

### Security

Deployment is where the security review becomes binding, and the review's
validity is scoped to conditions that can change without a deploy:

- **The channel set** determines the threat model. Internal console and public
  Experience Cloud site are different products from a security standpoint, and
  the difference is a toggle.
- **The action inventory** determines the blast radius. Adding one action to the
  agent's toolbox changes what an adversarial user can reach.
- **The runtime user's grants** determine what any of it can touch.

Recording all three on the activation record is what makes a later change to any
of them visibly a change to an approved condition, rather than a configuration
tweak nobody reviewed. That is the entire mechanism — approval is meaningless if
its preconditions are unrecorded.

### Performance

Two rows are performance controls in disguise. Enumerating supporting metadata
instead of wildcarding keeps the deploy inside the release window — the docs warn
that wildcards on `ApexClass`, `Flows`, and `GenAiPromptTemplates` cause very
long deployments or timeouts. And the pre-activation latency baseline is what
makes a post-release latency alert interpretable; without it, the first alert
has no comparison and gets dismissed.

---

## Architectural Tradeoffs

### Enforced record vs. lightweight document

An enforced activation record costs an object, a few fields, and a validation
rule, and it slows the first three activations while people learn it. A
document costs nothing and enforces nothing. The tradeoff resolves the moment
the first audit or post-mortem asks a question the document cannot answer —
which is a matter of when, not whether. Build the record before the first
production activation, when the cost is lowest and nobody is under pressure.

### Full-agent deploy vs. version-only deploy

Full deploy is safe everywhere and slower. Version-only is faster and fails into
an org that has never had the agent, because the full agent must be deployed
first. Two runbook shapes, chosen by target org state — not one shape with an
exception.

### Additive vs. breaking action changes

An action that adds an optional input is compatible with both agent versions, so
rollback stays a one-step operation. An action that renames a required input
makes rollback a two-artefact coordination problem under incident pressure.
Preferring additive changes is a deployment-simplicity decision that is made
weeks earlier, in the action's design.

### Retaining prior versions vs. cleaning up

Retention costs metadata clutter and a slightly confusing version list. Not
retaining costs the rollback target. Because a committed version cannot be
edited, the previous version *is* the rollback plan — keep at least two, and
make retirement an explicit decision with a date rather than a cleanup instinct.

### Sign-off breadth vs. release velocity

Three approvals (business, security, SRE) is the smallest set that covers the
three failure classes agents actually produce: wrong behaviour, disclosure, and
outage. Fewer and one class is unowned. More and the gate becomes a scheduling
problem, which produces the worst outcome — a checklist that is routinely
bypassed and therefore signals nothing.

---

## Anti-Patterns

1. **A generic release checklist relabelled.** If find-and-replacing "agent"
   with "app" leaves it coherent, it contains no agent-specific content and will
   not catch any agent-specific failure.

2. **Rollback declared complete when the agent version reverts.** Apex, fields,
   and activated prompt templates do not revert with it. A one-step rollback plan
   has not been rehearsed.

3. **Monitoring after activation.** Non-retroactive by design; the first week is
   unrecoverable and it is the week most likely to need investigating.

4. **"Alerts configured" as the monitoring evidence.** Configuration and
   function are different claims. Fire one against synthetic traffic and confirm
   receipt.

5. **Sign-off in chat.** Not queryable, not immutable, not linked to a version,
   and gone before the annual audit.

6. **A checklist that cannot block.** Enforcement is a validation rule, not a
   heading. Under pressure, an unenforced row is an unticked row.

7. **Channel addition treated as configuration.** The channel sets the threat
   model; adding one invalidates a security review conducted under different
   assumptions.

---

## Related

- `agentforce/agentforce-production-readiness-checklist` — the technical
  pre-prod verification behind these sign-off rows (cost telemetry, rate limits,
  canary, latency benchmarks).
- `agentforce/agentforce-testing-strategy` — what "suite green" means and which
  suites must pass before which gate.
- `agentforce/agentforce-pii-redaction` — the register whose review is a
  security-gate row, and why it is channel-dependent.
- `agentforce/prompt-template-versioning` — prompt templates roll back on their
  own lifecycle, not with the agent.
- `agentforce/agent-metric-dashboards` — the dashboard whose existence and named
  owner are checklist rows.
- `devops/release-management` — the surrounding release train this plugs into.

---

## Official Sources Used

- Retrieve and Deploy Agent Metadata (Agentforce DX) — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-deploy-metadata.html
- The New Agentforce Metadata and Development Lifecycle (Salesforce Developers) — https://developer.salesforce.com/blogs/2025/03/the-new-agentforce-metadata-and-development-lifecycle — the source for the **API 66.0 or later** manifest floor. The Agentforce DX guide page above does *not* state it; its example shows `<version>65.0</version>`.
- Agent Metadata (Agentforce DX) — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-metadata.html
- Agentforce Metadata Types — https://developer.salesforce.com/docs/ai/agentforce/references/agents-metadata-tooling/agents-metadata.html
- GenAiPlannerBundle (Metadata API Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiplannerbundle.htm
- Manage an Agent (Agentforce DX) — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-manage.html
- Set Up Agentforce Session Tracing (Help) — https://help.salesforce.com/s/articleView?id=ai.generative_ai_session_trace_setup.htm&type=5
- Run Agent Tests (Agentforce DX) — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-test-run.html
- Agentforce Testing Center (Help) — https://help.salesforce.com/s/articleView?id=ai.agent_testing_center.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
