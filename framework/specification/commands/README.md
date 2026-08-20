# Typed V2 commands

Only V2 product and framework commands are typed here. Existing 67 commands remain compatibility surfaces and are typed on touch.

| Command | Product | Purpose |
|---|---|---|
| `/sfskills-doctor` | — | Inspect local framework, host, plugin, MCP, Salesforce CLI, org aliases, index, schemas, and generated-artifact health. |
| `/sfskills-capabilities` | — | List products, modes, hosts, prerequisites, and qualification status from canonical definitions. |
| `/sfskills-explain-route` | — | Explain which product or specialist would handle a request and why, without executing it. |
| `/sfskills-replay` | — | Replay a redacted run bundle offline or validate whether live refresh is required. |
| `/sfskills-validate-run` | — | Validate schemas, evidence links, policy, status, and review integrity for a run bundle. |
| `/sfskills-qa-run` | — | Run fixture or protected scratch QA for selected products/scenarios. |
| `/triage-deployment` | `P01` | Tell me why this Salesforce deployment failed, group downstream symptoms under likely shared causes, and give me the safest remediation order. |
| `/triage-apex-tests` | `P02` | Explain why an existing Apex test run failed, identify shared root causes across methods, and propose the smallest evidence-backed fix and regression plan. |
| `/why-cant-user` | `P03` | Explain why a specific Salesforce user can or cannot see, create, edit, delete, or invoke an object, field, record, record type, or action. |
| `/plan-metadata-change` | `P04` | Before I change or retire Salesforce metadata, identify direct and transitive impact, deployment order, tests, permissions, data implications, and rollback constraints. |
| `/profile-automation` | `P05` | Show what Salesforce automation executes for an object operation, in what order, where recursion/DML/limit risk exists, and which automation should be consolidated. |
| `/review-release-readiness` | `P06` | Given a release scope, tell me whether it is ready, what blocks it, what should be tested or sequenced, and what evidence is still missing. |
| `/review-security-posture` | `P07` | Assess a Salesforce scope for evidence-backed access, code, session, integration, data, and configuration risks, prioritized by exploitability and business impact. |
| `/triage-integration` | `P08` | Correlate Salesforce and supplied integration evidence to classify an incident, identify the likely failing boundary, and propose safe verification and recovery steps. |
| `/reconcile-data-load` | `P09` | Explain whether a Salesforce data migration reconciled, where records or relationships were lost/changed, and which deterministic checks should be performed next. |
| `/assess-org-health` | `P10` | Produce an evidence-backed, prioritized Salesforce health roadmap across Trusted, Easy, and Adaptable dimensions without reducing the org to a superficial score. |
| `/review-agentforce-agent` | `P11` | Review an Agentforce agent, topics/subagents, actions, grounding, guardrails, tests, and implementation dependencies for correctness, safety, and release readiness. |
| `/compare-orgs` | `P12` | Compare two explicit Salesforce org snapshots and distinguish expected environmental differences from dangerous deployment or configuration drift. |

## API rules

- Commands validate typed input before routing or tools.
- Conditional inputs use schema alternatives rather than natural-language guessing.
- Commands do not silently select the most recent job, default org, or first project.
- Host renderings are generated adapters; JSON specs are canonical.
- Legacy commands are preserved and migrated when changed or promoted into a V2 product.


## Contract completeness

Every V2 command definition in `commands/specs/` is a host-neutral API contract. It declares:

- stable ID, aliases, product ownership, supported execution modes, and host visibility;
- typed arguments and deterministic validation rules;
- allowed terminal statuses and stable error/recovery semantics;
- required agents, evidence tools, permissions, and orchestration stages;
- independent-review requirements;
- Salesforce, local-file, and network side effects;
- fixture and live-read-only example inputs.

The generated [`API_REFERENCE.md`](API_REFERENCE.md) renders the complete contract for all 18 commands. Host-specific slash-command files are adapters and MUST preserve these semantics.

## Product command lifecycle

Product commands follow this default sequence:

```text
validate input
  -> resolve explicit targets
  -> authorize run
  -> plan bounded context
  -> collect normalized evidence
  -> synthesize findings
  -> deterministic evidence lint
  -> independent review
  -> persist replayable run bundle
```

A host may combine stages only when authority, context isolation, evidence lineage, and review independence remain equivalent and are proven in host tests.
