# V2 Migration Profile: `security-skill-builder`

## Current source

- Path: `agents/security-skill-builder/AGENT.md`
- Class: `build`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `False`
- Modes: `single`

## Current purpose

Builds skills for the **Security / Compliance / IAM** role across any Salesforce cloud. Specializes in identity and access (SSO, MFA, delegated authentication, JIT provisioning), sharing and visibility (OWD, role hierarchy, sharing rules, manual shares, territory sharing, restriction rules, scoping rules), permission architecture (Profiles, Permission Sets, Permission Set Groups, Muting Permission Sets, User Access Policies), data protection (Shield Platform Encryption, Classic Encryption, Event Monitoring, Transaction Security, Field Audit Trail), session and domain security (My Domain, session settings, CSP/CORS/Trusted URLs), integration security (Connected Apps, OAuth flows, Named Credentials, External Credentials, JWT bearer), Apex/LWC security (with / without sharing, escape in Aura / LWC, Security-Scanner-like concerns), compliance frameworks (SOC 2, HIPAA, PCI, GDPR, FedRAMP, FIN

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

- Never write a security skill without a Threat Model section
- Never conflate "permissions" with "sharing" — always name the axis
- Never recommend Shield as a compliance solution; recommend it as compliance-supporting tooling
- Never cite a framework control ID you cannot verify from the primary source
- Never write "grant System Administrator to get past this" as a workaround — security skills that take shortcuts undo the skill's purpose
- Never skip the detection / monitoring section when the control is detective
- Never ignore integration users as a class — they are the most-breached surface and need explicit coverage
- Never leave audit evidence implicit — a security skill that doesn't answer "what would you show an auditor" is incomplete
- Never conflate Setup Audit Trail, Login History, Field History Tracking, Field Audit Trail, and Event Monitoring — they are distinct logs with distinct coverage and retention

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
