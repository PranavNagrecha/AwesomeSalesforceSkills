# V2 Migration Profile: `experience-cloud-admin-designer`

## Current source

- Path: `agents/experience-cloud-admin-designer/AGENT.md`
- Class: `runtime`
- Status: `stable`
- Version: `1.0.0`
- Requires org: `True`
- Modes: `design, audit`

## Current purpose

Two modes:

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
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes |
| `site_template` | design | `customer-account-portal` \| `customer-service` \| `partner-central` \| `help-center` \| `build-your-own` \| `lwr-build-your-own` \| `b2b-commerce` |
| `audience_model` | design | `external-customers` \| `external-partners` \| `public-with-login` \| `guest-only` \| `multi-audience` |
| `expected_member_count` | design | integer |
| `license_type` | design | `customer-community` \| `customer-community-plus` \| `partner-community` \| `external-apps` \| `external-apps-plus` |
| `site_name` | audit | the site's developer name |
| `audit_scope` | audit | `site:<name>` \| `org` |

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

Design mode:

1. **Summary** — template, audience model, license, expected member count, confidence.
2. **Audience design table**.
3. **PSG composition per audience** — child PS list + muting PSes.
4. **Sharing model table** — object × mechanism × rationale.
5. **Guest user posture** — CRUD/FLS table + Guest User Sharing Rules + rate-limit/reCAPTCHA notes.
6. **Moderation + CMS + SEO plan**.
7. **Login experience design**.
8. **Metadata stubs** — fenced XML per audience, PS, PSG, sharing set, guest profile.
9. **Cutover checklist**.
10. **Process Observations**:
    - **What was healthy** — existing Feature PSes reusable across audiences, clean license alignment, existing SSO tenant.
    - **What was concerning** — site template choices that will limit future requirements (Aura where LWR is warranted), sharing sets that imply Contact-Account chains the customer data doesn't always populate, moderation coverage gaps.
    - **What was ambiguous** — self-registration target profile when multiple audiences could accept new members, CMS workspace ownership.
    - **Suggested follow-up agents** — `permission-set-architect` (PSG review), `audit-router --domain sharing` (external sharing verification), `audit-router --domain my_domain_session_security` (login posture), `lwc-builder` (site-specific components), `security-scanner` (guest-user code review).
11. **Citations**.

Audit mode:

1. **Summary** — site(s) audited, P0/P1/P2 counts.
2. **Findings table** — site × finding × severity × evidence × remediation.
3. **Guest posture report** per site.
4. **Sharing set integrity report** — objects × sharing mechanism × estimated record reachable count × anomalies.
5. **Dead config report** — orphan audiences, PSGs with 0 assignees, CMS workspaces with 0 published items.
6. **Process Observations** — as above.
7. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/experience-cloud-admin-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/experience-cloud-admin-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.m

## Current non-goals excerpt

- Does not activate or publish the site.
- Does not deploy metadata.
- Does not create user records.
- Does not publish CMS content or push branding assets.
- Does not configure the SSO IDP — only the SP-side Salesforce configuration.
- Does not manage B2B Commerce catalog / pricing — that's a separate Commerce-admin stack.
- Does not auto-chain.

## Migration acceptance test

The migration is complete only when a fixture run, a long-context distractor run, an unavailable-evidence run, a safety/refusal run, and an evidence-review run all pass. Agents that can affect security, deployments, data, or generated code require a real host smoke test and the applicable real-org QA lane before release.
