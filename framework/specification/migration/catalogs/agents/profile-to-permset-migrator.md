# V2 Migration Profile: `profile-to-permset-migrator`

## Current source

- Path: `agents/profile-to-permset-migrator/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.1.0`
- Requires org: `True`
- Modes: `single`

## Current purpose

Given one profile (or a set of profiles scoped by name filter) in the target org, decomposes the profile into a Permission Set + Permission Set Group layout that minimizes the profile to its mandatory residue (license assignment, default record type, default app, page layout assignments, login IP ranges, login hours, session settings) and moves every migratable permission — object CRUD, field-level security, system permissions, Apex class access, VF page access, tab settings, app access, custom permissions, named credential access, external data source access, and Custom Metadata Type access — into named PSes that can be reused across personas. Output is a PSG composition plan, metadata-XML stubs for the new PSes, a mapping of which users currently hold this profile, and a phased cutover plan consistent with Salesforce's ongoing deprecation of permissions-on-profiles.

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
| `profile_name` | yes (unless `profile_name_filter` is set) | `Sales User` |
| `profile_name_filter` | alt | `Custom:*` — handle a batch of profiles matching a wildcard |
| `target_org_alias` | yes |
| `reuse_psg` | no | name of an existing PSG to extend rather than create; if unset, the agent proposes a new PSG |
| `minimum_access_shape` | no | `standard-user` (default) \| `minimum-access` (leaner residue) \| `custom-residue` — guides how aggressive the stripping is |
| `integration_mode` | no | `true` if the profile is an integration user profile; changes the decomposition (no PSG, single dedicated PS) |

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

1. **Summary** — profile, user population count, proposed PSG composition, new PS count, reused PS count, confidence.
2. **Permission decomposition table** — permission × current profile value × target PS × category.
3. **PSG composition** — ordered child list + muting PS list.
4. **PS metadata stubs** — fenced XML per PS with target path.
5. **Residual profile plan** — what to strip, what to keep, diff block.
6. **Cutover plan** — 5 phases with dates, pilot population, metrics.
7. **User population summary** — count, active / inactive split, grouping hints (e.g. 40 users all in the same territory).
8. **Rollback plan**.
9. **Process Observations**:
   - **What was healthy** — existing Feature PSes reusable, minimum-access baseline already in place, users already on PSG supplements.
   - **What was concerning** — users assigned to the profile who are on different licenses (requires splitting into multiple PSGs), custom profiles with >100 system permissions (legacy drift), profile-embedded Custom Metadata access that other profiles implicitly depend on.
   - **What was ambiguous** — session settings that might be profile-scoped vs org-wide (User Access Policy migration candidates), profiles whose IP ranges are "temporary."
   - **Suggested follow-up agents** — `permission-set-architect` (if the resulting PSG composition hits anti-patterns), `audit-router --domain sharing` (profile residuals touching OWD/sharing), `security-scanner` (post-migration FLS sanity check).
10. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/profile-to-permset-migrator/<run_id>.md`
- **JSON envelope:** `docs/reports/profile-to-permset-migrator/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Each entry MUST name one of: `object-crud`, `fls`, `system-permissions`, `apex-class-access`, `vf-page-access`, `tab-settings`, `app-access`, `custom-permissions`, `named-credentials`, `residue`. 

## Current non-goals excerpt

- Does not assign PSes or PSGs to users.
- Does not deploy metadata.
- Does not retire the profile.
- Does not modify user records (license changes, profile field).
- Does not design User Access Policies — that's out of scope; the agent flags candidates.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
