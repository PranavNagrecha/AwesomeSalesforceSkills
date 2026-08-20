# V2 Migration Profile: `security-scanner`

## Current source

- Path: `agents/security-scanner/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Walks a `force-app/` tree and flags CRUD/FLS violations, sharing leaks, hardcoded secrets, missing `with sharing` declarations, and callouts that bypass Named Credentials. Cross-references every finding with the canonical fix in `templates/apex/SecurityUtils.cls` and the sharing decision tree. Returns a severity-ranked report with remediation code.

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
| `scope_path` | yes | `force-app/main/default/` |
| `target_org_alias` | no | enables `validate_against_org` lookups |
| `severity_threshold` | no (default `P2`) | `P1` to hide low-severity findings |

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

1. **Summary** — files scanned, findings by severity, confidence.
2. **Findings table** — file, line, severity, code (e.g. `no-flsd-on-dml`), one-liner.
3. **Per-finding fix** — each P0 and P1 gets a before/after code block citing the specific `SecurityUtils`/`HttpClient`/decision-tree fix.
4. **Hardcoded-secret summary** — list of files and lines; remediation is always "move to Custom Metadata or Named Credentials + rotate the secret immediately".
5. **Citations** — skill ids, template paths, decision-tree branches.
6. **Process Observations** — the `process_observations` field in the envelope MUST be populated whenever the scan reveals patterns worth flagging beyond raw findings. Bucket signals into:
   - **Healthy** — e.g. `SecurityUtils` consistently invoked across the codebase, Named Credentials used uniformly, all `without sharing` declarations carry `// reason:` comments.
   - **Concerning** — e.g. mixed sharing posture across handlers for the same SObject, repeated `escapeSingleQuotes`-only patterns, secret-shaped values found in Custom Metadata XML, REST endpoints lacking permission gates.
   - **Ambiguous** — e.g. `without sharing` with a comment that doesn't actually justify the choice; SOQL using `USER_MODE` but downstream DML in `SYSTEM_MODE`; class with mixed Setup + non-Setup DML where `runAs` boundary is unclear.
   - **Suggested follow-ups** — recommend (do not auto-chain) `/refactor-apex` for `SecurityUtils` rollout, `/audit-router --domain sharing` for OWD/role decisions, `/architect-perms` for permission-set redesign when REST/Aura endpoints have no gate.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/security-scanner/<run_id>.md`
- **JSON envelope:** `docs/reports/security-scanner/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. The dimensions that MUST appear in either `dimensio

## Current non-goals excerpt

- Does not modify any file.
- Does not write secrets to disk or to the output.
- Does not deploy Named Credentials — produces the spec; user deploys.
- Does not run PMD or other static analyzers — uses only its own rules + the skill library.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
