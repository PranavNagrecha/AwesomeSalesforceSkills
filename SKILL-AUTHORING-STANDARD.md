# Skill Authoring Standard

This is the authoritative guide for writing skills in this library. Every skill must conform to this standard before it is merged.

Read this before writing any SKILL.md. No exceptions.

---

## The One Rule

**Every word in SKILL.md must help a practitioner do the work faster or avoid a mistake.** If a sentence doesn't do one of those two things, cut it.

---

## Folder Structure

Every skill lives in `skills/[domain]/[skill-name]/` and contains exactly:

```
skill-name/
├── SKILL.md                      ← Master doc. Max 10KB.
├── references/
│   ├── examples.md               ← Real code with inline explanations
│   ├── gotchas.md                ← Mistakes + how to avoid them
│   └── well-architected.md       ← WAF pillar mapping
├── templates/
│   └── [name].[cls|html|xml|json|md] ← Copy-paste boilerplate or planning template
└── scripts/
    └── check_[noun].py           ← stdlib-only analysis tool
```

Nothing else. Don't add files that aren't in this structure.

Generated machine artifacts live outside skill folders in `registry/`, `vector_index/`, and `docs/SKILLS.md`.

---

## Official Source Requirement

Before creating a new skill, run `python3 scripts/search_knowledge.py "<topic>"` to check current local coverage.

Before writing or materially revising a skill, read the relevant entries in `standards/official-salesforce-sources.md`.

Rules:
- Official Salesforce docs are the primary authority for product behavior, limits, APIs, metadata semantics, and security requirements.
- Salesforce Architects content is the primary authority for architecture patterns, anti-patterns, and Well-Architected best practices.
- Local RAG content and project notes can add practical nuance, but they do not replace official behavior claims.
- Do not quote or paste large chunks of documentation into the skill. Convert the validated guidance into concise practitioner instructions.
- Skills should record the official sources actually used in `references/well-architected.md` under `## Official Sources Used`.

---

## SKILL.md Format

### Frontmatter (required, exact keys)

```yaml
---
name: skill-name                            # kebab-case, matches folder name
description: "One sentence. What triggers this skill. What it does NOT cover."
category: admin | apex | lwc | flow | omnistudio | agentforce | security | integration | data | devops
salesforce-version: "Spring '25+"           # Earliest version this applies to
well-architected-pillars:
  - Security
  - Performance
  - Scalability
  - Reliability
  - User Experience
  - Operational Excellence
tags:
  - tag-one
  - tag-two
inputs:
  - input needed from the user, codebase, or org context
outputs:
  - artifact or guidance the skill produces
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: YYYY-MM-DD
---
```

All keys are required. No extras.

Generated-only fields such as `id`, `file_location`, `content_hash`, `chunk_ids`, `vector_embedding`, and `indexed_at` belong in generated registry and retrieval artifacts, not in `SKILL.md` frontmatter.

## Repo Sync Requirement

After adding or materially updating any skill:

```bash
python3 scripts/skill_sync.py --skill skills/[domain]/[skill-name]
python3 scripts/validate_repo.py
```

These commands update and validate:
- `registry/skills.json`
- `registry/skills/*.json`
- `registry/knowledge-map.json`
- `vector_index/chunks.jsonl`
- `vector_index/lexical.sqlite`
- `vector_index/manifest.json`
- `docs/SKILLS.md`

### Opening Statement (required)

First line after frontmatter must follow this pattern:

```
You are a Salesforce expert in [specific domain]. Your goal is [specific measurable outcome].
```

Examples of **good** opening statements:
- "You are a Salesforce expert in Apex trigger design. Your goal is to ensure triggers are bulkified, testable, and follow a single-trigger-per-object pattern."
- "You are a Salesforce expert in Flow security. Your goal is to identify record access violations and fault-handling gaps before they reach production."

Examples of **bad** opening statements:
- "This skill helps with Apex." ← too vague
- "You can use this for many things." ← zero value

### Before Starting (required)

```markdown
## Before Starting
Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- [list only what this specific skill actually needs]
```

Don't list generic questions. Only list what *this skill* specifically requires.

### How This Skill Works (required)

Exactly three modes. No more, no fewer.

```markdown
## How This Skill Works

### Mode 1: Build from Scratch
[When to use: greenfield, new component, starting from requirements]
[Step-by-step what the skill does]

### Mode 2: Review Existing
[When to use: PR review, inherited code, audit]
[Step-by-step what the skill does]

### Mode 3: Troubleshoot
[When to use: bug, unexpected behaviour, governor limit hit]
[Step-by-step what the skill does]
```

### Core Content (required, domain-specific name)

Name this section after the domain. Examples:
- `## Apex Trigger Patterns`
- `## Flow Fault Handling Rules`
- `## FLS Enforcement Approaches`

Use tables for structured comparisons. Use checklists for processes. Use code blocks for examples — but keep them short here; heavy examples go in `references/examples.md`.

**Tone:** Practitioner voice. Direct. No hedging. "Always do X" not "You might want to consider X."

### Salesforce-Specific Gotchas (required)

```markdown
## Salesforce-Specific Gotchas

- **[Gotcha name]**: [What happens] → [How to avoid it]
```

Minimum 3. Maximum 8. These must be real gotchas from real projects, not textbook warnings.

### Proactive Triggers (required)

```markdown
## Proactive Triggers

Surface these WITHOUT being asked:
- **[Condition]** → Flag [specific issue] because [specific consequence]
- **[Condition]** → Flag [specific issue] because [specific consequence]
```

Minimum 4, maximum 6. These are the things an experienced practitioner notices immediately that a junior misses. Be specific — "If you see a SOQL query inside a for loop" not "If performance looks bad."

### Output Artifacts (required)

```markdown
## Output Artifacts

| When you ask for...         | You get...                                      |
|-----------------------------|-------------------------------------------------|
| Code review                 | Annotated findings with WAF pillar tags         |
| Boilerplate                 | Ready-to-deploy template with inline comments   |
| Troubleshooting             | Root cause + remediation steps                  |
```

Every row must be specific. "Help" is not a valid entry.

### Related Skills (required)

```markdown
## Related Skills

- **[skill-name]**: Use when [specific scenario]. NOT for [specific disambiguation].
- **[skill-name]**: Use when [specific scenario]. NOT for [specific disambiguation].
```

The NOT clause is as important as the use case. It prevents skill confusion.

---

## references/examples.md Standard

- Real code only. No pseudocode.
- Every example has a header: `## Example: [What It Demonstrates]`
- Every example has inline comments explaining non-obvious lines
- Bad examples are as valuable as good ones — show both with clear labels
- Minimum 2 examples per skill
- For admin or process-heavy skills where deployable code is not the main deliverable, examples may use realistic metadata, JSON, CLI, or Markdown operating artifacts instead of Apex or LWC source files.

```markdown
## Example: Bulkified Trigger Handler

**✅ Correct Pattern**
\```apex
// Handler class separates trigger logic from DML — makes unit testing possible
public class AccountTriggerHandler {
    public static void onBeforeInsert(List<Account> newAccounts) {
        // Process in bulk — never one record at a time
        for (Account acc : newAccounts) {
            acc.Name = acc.Name.trim();
        }
    }
}
\```

**❌ Anti-Pattern**
\```apex
// This fires a SOQL query per record — hits limits at 101 records
trigger AccountTrigger on Account (before insert) {
    for (Account acc : Trigger.new) {
        List<Account> existing = [SELECT Id FROM Account WHERE Name = :acc.Name];
    }
}
\```
```

---

## references/gotchas.md Standard

Format every gotcha as:

```markdown
## [Gotcha Name]

**What happens:** [Describe the failure mode precisely]

**When it bites you:** [Specific scenario — batch size, sharing model, async context, etc.]

**How to avoid it:** [Specific fix — not "be careful"]

**Example:**
\```apex
// [code showing the problem or the fix]
\```
```

---

## references/well-architected.md Standard

Map the skill to WAF pillars. Be honest — not every skill touches every pillar.

```markdown
# Well-Architected Mapping: [Skill Name]

## Pillars Addressed

### Security
[How this skill's patterns address the Security pillar]
- [Specific WAF check or principle]

### Performance
[How this skill's patterns address the Performance pillar]
- [Specific WAF check or principle]

## Pillars Not Addressed
- **User Experience** — [Why this skill doesn't directly affect UX]

## Official Sources Used

- [Official Salesforce source] — [What it validated]
- [Official Salesforce Architects source] — [What it validated]
```

Use the smallest relevant set of official sources. The purpose is traceability and disciplined source selection, not link spam.

---

## templates/ Standard

- One file per common scenario, not one mega-template
- File named descriptively: `trigger_handler.cls`, not `template1.cls`
- Every non-obvious line commented when the template is code or metadata
- `TODO:` markers where the implementer must fill in business logic or process decisions
- For admin/process-heavy skills, a Markdown planning template is acceptable when the main artifact is a runbook, checklist, or decision record rather than deployable metadata
- Otherwise the template must be deployable with minimal modification — not a sketch

---

## scripts/ Standard

```python
#!/usr/bin/env python3
"""
check_[noun].py — [One-line description of what it checks]

Usage:
    python check_[noun].py --file path/to/file.cls
    python check_[noun].py --dir path/to/dir/

Output: JSON with keys: score (0-100), findings (list), summary (str)
"""
import argparse
import json
import sys
# stdlib only — no pip imports
```

Rules:
- Zero pip dependencies (stdlib only). If you need a third-party lib, document it in a `requirements.txt` in the script's folder and mark the skill as requiring it.
- Must run standalone: `python scripts/check_x.py --help` works with no setup
- Output is always JSON: `{"score": 85, "findings": [...], "summary": "..."}`
- Include `if __name__ == "__main__": sys.exit(main())`
- Score 0-100. 100 = perfect. Deduct points per finding severity: Critical -20, High -10, Medium -5, Low -1, Review -0

---

## Size Limits

| File | Max Size |
|------|----------|
| SKILL.md | 10KB |
| references/examples.md | 20KB |
| references/gotchas.md | 15KB |
| references/well-architected.md | 5KB |
| Any single template file | 10KB |
| Any single script | 15KB |

If SKILL.md is approaching 10KB, move content to references/.

---

## Review Checklist Before Merging

- [ ] Frontmatter complete with all required keys
- [ ] `tags`, `inputs`, `outputs`, and `dependencies` are present in frontmatter
- [ ] Opening statement follows the pattern
- [ ] `salesforce-context.md` check present in Before Starting
- [ ] All three modes present and specific
- [ ] Core content uses tables/checklists, not prose walls
- [ ] Minimum 3 gotchas, each with a fix
- [ ] Minimum 4 proactive triggers, each specific
- [ ] Output artifacts table is complete
- [ ] Related Skills has NOT clauses
- [ ] `references/examples.md` has at least 2 real code examples
- [ ] `references/well-architected.md` maps to at least 1 WAF pillar
- [ ] `python3 scripts/search_knowledge.py "<topic>"` was used to check existing local coverage before creating the skill
- [ ] Relevant official sources from `standards/official-salesforce-sources.md` were checked before drafting
- [ ] `references/well-architected.md` includes `## Official Sources Used`
- [ ] At least 1 boilerplate template in `templates/`
- [ ] SKILL.md is under 10KB
- [ ] No pip dependencies in scripts (or documented if unavoidable)
- [ ] Script produces JSON output
- [ ] No cross-skill dependencies introduced
- [ ] `python3 scripts/skill_sync.py` was run
- [ ] `python3 scripts/validate_repo.py` passes

---

## What Bad Looks Like

**Bad:** "Consider using `WITH SECURITY_ENFORCED` in your SOQL queries to enforce field-level security."

**Good:** "Always use `WITH SECURITY_ENFORCED` on all SOQL queries in Apex classes that handle user-initiated requests. Exception: queries inside `without sharing` system-context classes where you've explicitly documented why. Omitting it on a query against a sensitive object (e.g. `Financial_Account__c`) is a Critical security finding."

The difference: the good version tells you exactly what to do, when the exception applies, and what the consequence is.
