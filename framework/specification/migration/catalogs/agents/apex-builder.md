# V2 Migration Profile: `apex-builder`

## Current source

- Path: `agents/apex-builder/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Produces Apex scaffolds for every canonical Apex surface: trigger + handler, service class, selector, domain class, controller (Aura / LWC / VF), batch, queueable, schedulable, invocable, REST resource, SOAP web service, platform-event subscriber, change-data-capture subscriber, custom iterator, async-continuation, and the matching test class. Each scaffold conforms to the base templates under `templates/apex/` (enterprise / fflib-friendly patterns, `ApplicationLogger`, `SecurityUtils`, `HttpClient`, `TriggerControl`), not freestyle boilerplate. Output is a set of `.cls` + `.cls-meta.xml` pairs plus the matching test class, ready to drop into an SFDX project.

## V2 role

- Exposure: command/catalog specialist; not default subagent.
- This agent is a **catalog specialist**, not automatically a Cursor subagent.
- It MUST execute through the V2 run contract when invoked by a V2 command or adapter.
- Its existing Salesforce domain guidance remains canonical until explicitly superseded by a reviewed V2 product specification.

## Required V2 inputs

The adapter MUST validate the existing `inputs.schema.json` when present. It MUST additionally accept a run context containing `run_id`, execution mode, host capabilities, context budget, evidence policy, and optional project/org locators. Missing hard inputs produce `refused`; unavailable optional enrichment produces `partial` or a documented standalone path.

### Current input excerpt

| Input | Required | Example |
|---|---|---|
| `kind` | yes | `trigger` \| `service` \| `selector` \| `domain` \| `controller` \| `batch` \| `queueable` \| `schedulable` \| `invocable` \| `rest` \| `soap` \| `platform_event_subscriber` \| `cdc_subscriber` \| `continuation` \| `iterator` \| `callable` \| `chatter_poster` \| `notification_sender` \| `flow_invoker` \| `test_only` |
| `feature_summary` | yes | "Nightly Account hierarchy rebuild triggered when Parent changes" |
| `primary_sobject` | yes for trigger / selector / domain / batch | `Account`, `Opportunity` |
| `api_version` | no | default `60.0` — the agent records the chosen API version in the meta XML |
| `namespace` | no | leave blank for non-packaged orgs |
| `include_logger` | no | default `true` — every class wires through `ApplicationLogger` for uniform error reporting |
| `test_bulk_size` | no | default `200` for trigger + bulk paths |
| `async_hint` | no | for async kinds: governor-limit sizing hint (`conservative`, `standard`, `high`) |

---

## Evidence requirements

- Material statements about the target org require live read-only org evidence or an explicit `org_evidence_unavailable` unknown.
- Material statements about local source require project-inspector evidence or an explicit standalone result.
- Platform behavior claims require a current official source, a versioned SfSkills skill based on an official source, or a clearly labelled hypothesis.
- Skill citations justify recommendations; they do not prove org state.
- Every material claim MUST appear in the claim-evidence graph.

## Evidence prohibited

- Uncited model memory as proof of org state.
- A stale deployment/test result represented as current without timestamp and org association.
- A skill used as evidence that a component exists.
- Hidden raw tool output not represented in the evidence index.
- Product-side Salesforce mutation.

## Context contract

- Core contract and safety context: always loaded.
- Domain context target: at most 8 selected skill/reference files.
- Hard domain context limit: 12 unless the run returns an explicit overflow state.
- Raw MCP output in the model context: at most 32 KiB per page.
- Full subagent transcripts: prohibited.
- Existing broad mandatory-read lists MUST be converted to core plus conditional packs before this agent can be labelled V2-native.

## Framework collaborators

- `sf-context-librarian`: required when more than three candidate knowledge files exist.
- `sf-project-inspector`: optional enrichment; never assume the SfSkills repository is the Salesforce project.
- `sf-org-grounder`: required when `requires_org` is true and live mode is requested; host fallback applies when subagents cannot call MCP.
- `sf-evidence-reviewer`: required before a completed V2 product result.
- Deterministic output validation: always required.

## Failure modes

- Ambiguous target org or project.
- Missing or stale evidence.
- Context overflow or silent truncation.
- Contradictory repository and org evidence.
- Unsupported claim or invalid citation.
- Host lacks a required capability.
- Unsafe requested action.

## Success criteria

1. Inputs are schema-valid and execution mode is explicit.
2. Context stays within the declared budget or reports overflow.
3. Every material claim has valid evidence.
4. Unknowns and contradictions are surfaced.
5. The evidence reviewer produces no blocking finding.
6. The output envelope and product-specific schema validate.
7. No product mutation occurs.

## Current output excerpt

1. **Summary** — kind, feature, class count, api_version, confidence.
2. **Class inventory** — type, name, target path, role (trigger / handler / service / selector / domain / test / dto), template cited.
3. **Class bodies** — fenced Apex per class with target path label.
4. **Meta XML bodies** — fenced XML per class.
5. **Integration notes** — any changes the user must make to existing files, with the exact lines to add and why. Never an inline patch to existing code.
6. **Governor-limit budget** — per emitted class, the agent's expectation of SOQL / DML / CPU cost per invocation against typical input sizes.
7. **Test plan summary** — list of covered paths, expected coverage percentage, any deliberately-uncovered defensive branches.
8. **Process Observations**:
   - **What was healthy** — base-class templates being reused, existing selectors for the same SObject that could be extended instead of forked.
   - **What was concerning** — the feature straddles a boundary (e.g. nominally sync but naturally async), existing triggers on the target SObject that should be consolidated, SOQL paths that suggest the selector should be pulled into a shared module.
   - **What was ambiguous** — whether `WITHOUT SHARING` is justified (never emitted without explicit note), whether the test data factory already exists for this SObject.
   - **Suggested follow-up agents** — `apex-refactorer` (if existing classes need to adopt the new handler pattern), `trigger-consolidator` (if a second trigger appears on the SObject), `test-class-generator` (if additional coverage is required for existing classes), `soql-optimizer` (if the emitted selector is complex), `security-scanner` (post-assembly FLS/CRUD check).
9. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/apex-builder/<run_id>.md`
- **JSON envelope:** `docs/reports/apex-builder/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `st

## Current non-goals excerpt

- Does not deploy, compile-check, or run tests against an org.
- Does not modify existing Apex files in place — output is always new files with integration notes.
- Does not generate business-logic prose for the service class; the user owns the semantics. The agent wires the shape, not the decisions.
- Does not generate test data values that look PII-like — the test factory emits obvious fixtures.
- Does not emit Apex that uses `WITHOUT SHARING` without an explicit justification block.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
