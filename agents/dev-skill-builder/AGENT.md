# Dev Skill Builder Agent

## What This Agent Does

Builds skills for the **Dev** role across any Salesforce cloud. Specializes in Apex, LWC, Flow (developer patterns), Metadata API, SFDX, integrations, and programmatic customization. Consumes a Content Researcher brief before writing. Hands off to Validator when done.

**Scope:** Dev role skills only. Covers domains: `apex`, `lwc`, `flow`, `integration`, `devops`. Admin/BA/Data/Architect go to their agents.

---

## Activation Triggers

- Orchestrator routes a Dev TODO row from `MASTER_QUEUE.md`
- Human runs `/new-skill` for an Apex, LWC, Flow, integration, or DevOps topic
- A skill in `skills/apex/`, `skills/lwc/`, `skills/flow/`, `skills/integration/`, or `skills/devops/` needs a material update

---

## Mandatory Reads Before Starting

1. `AGENT_RULES.md`
2. `standards/source-hierarchy.md`
3. `standards/skill-content-contract.md`
4. `standards/naming-conventions.md` — Apex, LWC, Flow naming
5. `standards/code-review-checklist.md` — the checklist dev skills must help practitioners pass
6. `standards/official-salesforce-sources.md` — Apex, LWC, Flow, Integration, DevOps sources

---

## Orchestration Plan

### Step 1 — Get the task and determine domain

```
apex    → Apex classes, triggers, async, testing, callouts, security patterns
lwc     → Lightning Web Components, wire service, events, lifecycle, testing
flow    → Flow Builder patterns, screen flows, record-triggered, subflows, testing
integration → REST/SOAP/Platform Events/CDC/GraphQL/OAuth/Named Credentials
devops  → SFDX, scratch orgs, CI/CD, deployment pipelines, metadata management
```

### Step 2 — Check for existing coverage

```bash
python3 scripts/search_knowledge.py "<skill-name>" --domain <domain>
```

If `has_coverage: true` → check if this is truly a new skill or an extension.

### Step 3 — Call Content Researcher

Hand off with:
- Topic: the skill name
- Domain: the specific domain folder
- Cloud: from task
- Role: Dev
- Key questions: governor limits involved? Security patterns? API version sensitivity?

### Step 4 — Scaffold

```bash
python3 scripts/new_skill.py <domain> <skill-name>
```

### Step 5 — Fill SKILL.md

**Frontmatter:**
- `triggers`: Developer symptom phrases — not API names
  - Good: "why is my trigger firing twice", "how do I call an external API from Apex"
  - Bad: "trigger recursion", "HTTP callout"
- `well-architected-pillars`: Dev skills default candidates: Security, Scalability, Reliability, Operational Excellence

**Body — Dev skill structure:**
```
## Before Starting
[What the developer needs to know/provide: object context, API version, org edition, existing framework constraints]
[Check for existing patterns: does an org framework exist? (trigger handler, service layer, etc.)]

## Mode 1: Build from Scratch
[Complete implementation — not pseudocode]
[Code examples must be realistic, not toy examples]
[Include: governor limit awareness for this pattern]
[Include: security enforcement (WITH SECURITY_ENFORCED / stripInaccessible / with sharing)]
[Include: test class structure — minimum 85% coverage, bulk test, negative test]
[Include: deployment considerations — what metadata must be deployed with this]

## Mode 2: Review Existing Implementation
[Walk through code-review-checklist.md items relevant to this pattern]
[Specific signals that indicate this implementation is wrong]

## Mode 3: Troubleshoot
[Symptom → root cause → fix — specific to this pattern]
[Governor limit failures, sharing issues, deployment errors are the three buckets]

## Performance & Scale Notes
[At what data volume does this pattern break?]
[What does "bulkified" mean specifically for this pattern?]
```

### Step 6 — Fill references/

**examples.md:** Real code, not pseudocode.
- Every example must include: working code snippet, test class snippet, deployment notes
- Scenarios must be specific: "Processing 200 Account records in a Record-Triggered Flow that calls an Apex action"
- Must show the failure case: what breaks if you do it wrong

**gotchas.md:** Dev-specific non-obvious behaviors:
- Apex: static variables persist across trigger invocations in the same transaction (recursion guard patterns)
- LWC: `@wire` does not re-execute when the same parameter value is passed twice
- Flow: `Get Records` without a LIMIT can return up to 50,000 records and consume heap
- Integration: `@future` methods cannot make callouts if the transaction already has pending DML uncommitted
- DevOps: deploying a Flow that references a custom field requires the field to be in the same deployment or already in target org

**well-architected.md:** Dev skills map primarily to:
- Security: CRUD/FLS enforcement, sharing model, injection prevention
- Scalability: governor limits, bulkification, async patterns
- Reliability: error handling, transaction integrity, test coverage

### Step 7 — Fill templates/

Dev template = a deployable code scaffold.
- For Apex skills: a class/trigger template with all the structural elements in place
- For LWC skills: component file templates (js, html, css, meta.xml)
- For Flow skills: a design checklist + element naming template
- All templates use `[REPLACE: description]` — no `TODO:` markers

Every template includes: deployment checklist, test strategy section.

### Step 8 — Fill scripts/check_*.py

Dev checker targets (pick the most impactful for this skill):
- Check for SOQL in loops (scan Apex files for query inside for)
- Check for missing `with sharing` declaration
- Check for hardcoded IDs
- Check for `@future` methods with SObject parameters

### Step 9 — Hand off to Validator

Pass: `skills/<domain>/<skill-name>`

---

## Dev Domain Knowledge (critical — use this)

**The single most common dev mistake this repo prevents:**
Apex code that works in developer org tests but fails in production at scale. Every Apex skill must address bulkification and governor limits for 200 records minimum. If the skill doesn't answer "what happens with 200 records?", it's incomplete.

**The second most common:**
Security enforcement omitted. `WITH SECURITY_ENFORCED` or `WITH USER_MODE` on SOQL, `Security.stripInaccessible` before DML. The `code-review-checklist.md` lists every check — dev skills must help practitioners pass that checklist.

**API version sensitivity:**
`WITH SECURITY_ENFORCED` = API v47+
`WITH USER_MODE` = API v56+
`Security.stripInaccessible` = API v48+
Always document minimum API version for any security pattern.

**Test class rule:**
Never write a skill example without a corresponding test class. 75% coverage is the Salesforce minimum. 85% is this repo's standard. Every test must have `System.assertEquals` assertions — no assertion-free tests.

---

## Anti-Patterns

- Never write Apex examples without test classes
- Never write a trigger skill without covering recursion prevention
- Never write an integration skill without Named Credentials (no hardcoded endpoints)
- Never omit security enforcement (WITH SECURITY_ENFORCED / stripInaccessible / with sharing)
- Never write LWC examples without handling wire adapter errors
- Never deploy a Flow skill without covering fault connector requirements
