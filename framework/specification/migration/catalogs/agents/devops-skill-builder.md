# V2 Migration Profile: `devops-skill-builder`

## Current source

- Path: `agents/devops-skill-builder/AGENT.md`
- Class: `build`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Builds skills for the **DevOps / Release Engineering** role across any Salesforce cloud. Specializes in source control strategy, branching models, CI/CD pipelines, sandbox orchestration, deployment tooling (SFDX, Metadata API, Change Sets, DX projects, Unlocked Packages, 2GP), environment management, release management, automated testing gates, and observability for Salesforce delivery. Consumes a Content Researcher brief before writing. Hands off to the Validator when done.

## V2 role

- Exposure: maintainer-only; never product auto-route.
- This agent is a **catalog specialist**, not automatically a Cursor subagent.
- It MUST execute through the V2 run contract when invoked by a V2 command or adapter.
- Its existing Salesforce domain guidance remains canonical until explicitly superseded by a reviewed V2 product specification.

## Required V2 inputs

The adapter MUST validate the existing `inputs.schema.json` when present. It MUST additionally accept a run context containing `run_id`, execution mode, host capabilities, context budget, evidence policy, and optional project/org locators. Missing hard inputs produce `refused`; unavailable optional enrichment produces `partial` or a documented standalone path.

### Current input excerpt

_No explicit Inputs section extracted._

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

_No explicit Output Contract section extracted._

## Current non-goals excerpt

- Never write DevOps guidance that doesn't specify the source-of-truth stance
- Never produce a "Mode 1: Configure" that ends before verification of the happy path AND the rollback path
- Never assume the deploy user has System Administrator — the right answer is a least-privileged deploy user per environment
- Never leave secret-handling implicit — skills that handle credentials must name how secrets are provided
- Never recommend Change Sets for a team of more than ~5 developers without flagging the scaling cliff
- Never write pipeline templates without test stages AND destructive-change handling
- Never conflate scratch orgs with sandboxes — they behave very differently
- Never skip the "what doesn't deploy" catalog section for any skill touching deployment

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
