# Cursor Test Script

Use this file to test whether Cursor follows the repo-native skill framework correctly.

Recommended setup:
- Open this repo in Cursor
- Use Agent / Composer mode with terminal access enabled
- Start with Test 1 before letting it edit files
- If you want a disposable run, do it in a separate clone or branch

---

## Test 1: Read-Only Framework Audit

Paste this into Cursor first:

```text
You are working inside the SfSkills repository.

Task: do a read-only audit of the skill framework before making any edits.

Follow the repo instructions exactly:
1. Read AGENT_RULES.md
2. Read CLAUDE.md
3. Read SKILL-AUTHORING-STANDARD.md
4. Run:
   python3 scripts/search_knowledge.py "integration http callout retries" --domain integration --json
5. Tell me:
   - whether this topic is already covered well enough by an existing skill
   - which existing skills partially overlap
   - which official Salesforce sources you would use
   - whether a new skill is justified

Do not edit any files yet.
Do not hand-wave. Use the actual repo files and actual command output.
```

Expected result:
- Cursor reads the rule files first
- Cursor runs `search_knowledge.py`
- Cursor references real overlapping skills such as `admin/connected-apps-and-auth` or `omnistudio/integration-procedures` if relevant
- Cursor names official docs before proposing edits
- Cursor does not change files

---

## Test 2: End-to-End New Skill Creation

If Test 1 looks good, paste this:

```text
You are working inside the SfSkills repository.

Create a new skill for this topic:

- Domain: integration
- Skill name: http-callout-resilience
- Pain point: teams build outbound integrations that have weak timeout, retry, idempotency, and error-handling design
- Trigger scenario: reviewing or building Apex- or Flow-driven outbound HTTP callouts to external systems
- Most common mistake to prevent: retrying unsafe operations without idempotency or clear failure handling

Requirements:
1. Follow AGENT_RULES.md, CLAUDE.md, and SKILL-AUTHORING-STANDARD.md exactly
2. Use SKILL.md frontmatter as the canonical metadata source
3. Run local coverage search before creating the skill
4. Use the smallest relevant official Salesforce source set from standards/official-salesforce-sources.md
5. Create the full skill package under skills/integration/http-callout-resilience/
6. Include:
   - SKILL.md
   - references/examples.md
   - references/gotchas.md
   - references/well-architected.md
   - at least one template file
   - at least one stdlib-only checker script
7. Add complete frontmatter, including:
   - tags
   - inputs
   - outputs
   - dependencies
8. Add an Official Sources Used section
9. Run:
   - python3 scripts/skill_sync.py --skill skills/integration/http-callout-resilience
   - python3 scripts/validate_repo.py
10. Do not hand-edit generated files in registry/, vector_index/, or docs/SKILLS.md

When done, report:
- the search query you used
- the official sources selected
- every file you created or changed
- whether validation passed
- whether the new skill appeared in docs/SKILLS.md and registry/skills.json
```

Expected result:
- Cursor searches first instead of jumping straight into file creation
- Cursor uses official docs such as:
  - REST API Developer Guide
  - Integration Patterns
  - Apex Developer Guide
  - Salesforce Well-Architected Overview
- Cursor creates a standards-compliant skill package
- Cursor runs sync and validation
- Cursor updates generated artifacts through the scripts, not manually

---

## Test 3: Spot-Check The Result

After Cursor finishes Test 2, use this verification prompt:

```text
Audit the new skill you just created.

Check:
1. skills/integration/http-callout-resilience/SKILL.md
2. skills/integration/http-callout-resilience/references/well-architected.md
3. docs/SKILLS.md
4. registry/skills.json

Tell me:
- whether the frontmatter is complete
- whether Official Sources Used is present
- whether the generated catalog includes the new skill
- whether anything still violates AGENT_RULES.md or SKILL-AUTHORING-STANDARD.md

Do not make more edits unless you find a real standards violation.
```

Success criteria:
- `python3 scripts/validate_repo.py` passes
- the skill package has all required files
- `SKILL.md` frontmatter includes `tags`, `inputs`, `outputs`, and `dependencies`
- `references/well-architected.md` includes `## Official Sources Used`
- `docs/SKILLS.md` lists the new skill
- `registry/skills.json` contains the new normalized record

---

## Cleanup Prompt

If you only wanted a disposable test, paste this after you are done:

```text
Remove the test skill at skills/integration/http-callout-resilience/.

Then run:
- python3 scripts/skill_sync.py --all
- python3 scripts/validate_repo.py

Report every file removed or regenerated.
Do not leave stale generated artifacts behind.
```
