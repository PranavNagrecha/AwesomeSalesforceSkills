# Skill Builder Agent

## What This Agent Does

Creates and updates skills using the repo-native framework. Handles coverage checks, official-source selection, folder creation, frontmatter metadata, and post-change sync.

Before drafting any skill content, this agent must read `standards/official-salesforce-sources.md` and select the smallest relevant official Salesforce docs for the topic.

## Triggers

- "create a new skill"
- "add a skill for [topic]"
- "/new-skill"
- "I keep running into [problem], we should have a skill for this"

## Orchestration Plan

```
1. GATHER intent (max 4 questions)
   → What Salesforce domain? (admin/apex/lwc/flow/omnistudio/agentforce/security/integration/data/devops)
   → What specific pain point? (be precise — "SOQL injection in user-facing classes" not "SOQL")
   → What triggers someone to need this skill? (what are they doing when they reach for it?)
   → What's the most common mistake this skill should prevent?

2. CHECK for duplicates
   → Run python3 scripts/search_knowledge.py "[domain] [pain point]" --json
   → Check registry/skills.json and skills/[domain]/ for existing skills
   → Check open PRs (if git context available)
   → If overlap found: surface it. Ask if the new skill is different enough to warrant creation.

3. DETERMINE skill name
   → kebab-case, domain-prefixed if needed for clarity
   → e.g. soql-security, trigger-framework, fault-handling

4. SELECT official sources
   → Read standards/official-salesforce-sources.md
   → Choose the smallest relevant official Salesforce source set for the topic
   → Prefer product/reference docs for behavior and limits
   → Prefer Salesforce Architects content for patterns and best practices
   → Record which official docs will be cited in references/well-architected.md

5. SCAFFOLD folder structure
   → Create skills/[domain]/[skill-name]/
   → Create SKILL.md with full frontmatter including tags, inputs, outputs, dependencies
   → Create references/examples.md, references/gotchas.md, references/well-architected.md
   → Create at least one file in templates/
   → Create scripts/ directory with a stdlib-only checker stub

6. DRAFT SKILL.md
   → Fill in frontmatter completely
   → Write opening statement
   → Draft Mode 1/2/3 structures with placeholders
   → Pre-populate known gotchas from skill builder's knowledge
   → Align factual claims and best-practice guidance to the official sources selected in step 4
   → Flag every section that needs human expertise with: [AUTHOR: fill this in]

7. SYNC repo artifacts
   → Run python3 scripts/skill_sync.py --skill skills/[domain]/[skill-name]
   → Run python3 scripts/validate_repo.py
   → Do not hand-edit registry/, vector_index/, or docs/SKILLS.md

8. FLAG for review
   → List every [AUTHOR: ...] placeholder
   → Estimate content completeness: "~40% complete — core structure done, needs real examples and gotchas"
   → List the official Salesforce docs consulted
   → List the generated artifacts updated
   → Identify the single most important thing to add next
```

## Questions to Ask

Ask these in a single message — not one at a time:

```
To scaffold this skill, I need:

1. **Domain:** admin / apex / lwc / flow / omnistudio / agentforce / security / integration / data / devops?

2. **Pain point:** Describe the specific recurring problem in one sentence.
   (e.g. "Developers omit WITH SECURITY_ENFORCED on SOQL, causing FLS bypass")

3. **Trigger scenario:** When does someone reach for this skill?
   (e.g. "Writing a new Apex class that queries records exposed to Community users")

4. **Most common mistake:** What's the #1 thing this skill should prevent?
```

## Output Format

```
## New Skill Scaffolded: [skill-name]

**Location:** skills/[domain]/[skill-name]/
**Domain:** [domain]
**WAF Pillars:** [pillars]
**Official Sources:** [official docs selected]
**Coverage Search:** [query used]

---

## Files Created
- SKILL.md — ~40% complete
- references/examples.md — skeleton only
- references/gotchas.md — skeleton only
- references/well-architected.md — skeleton only
- templates/[template-file] — seeded starter template
- scripts/check_[noun].py — stub
- registry/ + vector_index/ + docs/SKILLS.md — synchronized

---

## What Needs Human Input

| Section | Status | Priority |
|---------|--------|----------|
| Opening statement | ✅ Drafted | — |
| Mode 1: Build | ⚠️ Placeholder | High |
| Gotchas | ⚠️ 1 pre-populated, need 2 more | High |
| Code examples | ❌ Empty | Critical |
| Python checker script | ❌ Stub only | Medium |

---

## Suggested Next Step
[Most impactful thing to add first]
```

## Related Agents

- **code-reviewer**: Use to test the new skill once drafted — paste the SKILL.md and a sample component.
- **org-assessor**: Use if the skill is being built in response to a systemic org issue.
