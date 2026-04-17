# Codex Skill Generation Prompt

Copy everything between the START and END markers and paste it into Codex.
Replace the SKILLS TO BUILD section with the actual skills from MASTER_QUEUE.md.

---
START PROMPT
---

You are a Salesforce skill content generator. Your ONLY job is to produce raw file contents
for one or more skill packages. Do NOT scaffold, sync, validate, or commit. Another agent handles that.

## Output Format

For EVERY file across ALL skills, output a header line exactly like this:

=== FILE: skills/<domain>/<skill-name>/<path> ===

then the complete file content, then ONE blank line before the next header.

Do NOT output anything else — no commentary, no code fences wrapping the block headers, no summaries.
Start immediately with the first === FILE: ... === line.

## Skills To Build

For each skill below, produce exactly 6 files.

---

SKILL NAME:   <skill-name>
DOMAIN:       <domain>
DESCRIPTION:  <one-line description including NOT for ... clause>
NOTES:        <paste the full Notes column from MASTER_QUEUE.md here>

---

(Repeat the block above for each additional skill)

---

## The 6 Files Per Skill

### File 1: skills/<domain>/<skill-name>/SKILL.md

Frontmatter — every field required, in this exact order:

```yaml
---
name:                  <must exactly match skill-name>
description:           <copy from input — must include at least one NOT for ... clause>
category:              <must exactly match domain>
salesforce-version:    "Spring '25+"
well-architected-pillars:
  - <1-3 of: Security, Scalability, Reliability, Operational Excellence, User Experience>
tags:
  - <3-6 kebab-case strings>
triggers:
  - "<natural-language symptom phrase 10+ chars>"
  - "<another symptom phrase>"
  - "<third symptom phrase>"
inputs:
  - "<concrete thing the skill consumer must supply>"
outputs:
  - "<concrete artifact or guidance the skill produces>"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---
```

Body rules:
- Open with 2-3 sentences: when to use, what outcome it drives. No "this skill" phrasing.
- ## Before Starting — 2-3 diagnostic questions as bullet points
- ## Core Concepts — 2-4 H3 subsections grounded in the research notes
- ## Common Patterns — 2-3 H3 subsections with: When to use / How it works / Why not the alternative
- ## Recommended Workflow — 3-7 numbered steps written as directives ("do this")
- MINIMUM 300 words in the body after frontmatter
- Every claim must come from the research notes sources — do not invent governor limits, field names, or API versions

### File 2: skills/<domain>/<skill-name>/references/examples.md

Header: # Examples — <Skill Human Title>

2+ examples. Each:

## Example N: <Scenario Title>

**Scenario:** one sentence
**Problem:** what goes wrong without this guidance
**Solution:** concrete steps, SOQL, Apex snippet, or config description
**Why:** why this is correct per the research notes (cite the source)

### File 3: skills/<domain>/<skill-name>/references/gotchas.md

Header: # Gotchas — <Skill Human Title>

3+ gotchas. Each:

## Gotcha N: <Short Title>

**Behavior:** what the platform actually does (non-obvious)
**Why it surprises:** why practitioners or LLMs assume otherwise
**Mitigation:** what to do instead

### File 4: skills/<domain>/<skill-name>/references/well-architected.md

Header: # Well-Architected Notes — <Skill Human Title>

One paragraph per well-architected pillar from the frontmatter.
Each paragraph: how this skill's guidance supports the pillar specifically.

Then:

## Official Sources Used

List every URL or doc title from the research notes. Minimum 1 entry. Format:
- [Doc Title](URL) — one sentence on what it covers for this skill

DO NOT leave this section empty or delete it.

### File 5: skills/<domain>/<skill-name>/references/llm-anti-patterns.md

Header: # LLM Anti-Patterns — <Skill Human Title>

5+ anti-patterns. Each:

## Anti-Pattern N: <Short Title>

**What the LLM generates:** short wrong output (code or config)
**Why it happens:** the cognitive shortcut or training bias
**Correct pattern:** the right code or config
**Detection hint:** grep pattern or reviewer checklist item

Anti-patterns must be specific to this skill's domain.

### File 6: skills/<domain>/<skill-name>/templates/<skill-name>-template.md

A fill-in-the-blank output template. 5-8 fields with <angle bracket> placeholders.
Should produce a concrete deliverable: design decision record, config checklist, or implementation plan.

## Quality Rules

- Every factual claim traces to the research notes. Omit anything not covered there.
- Do not invent field names, limits, or API shapes not in the notes.
- SKILL.md body must be 300+ words. Count before outputting.
- llm-anti-patterns.md must have 5+ entries.
- well-architected.md must have ## Official Sources Used with at least one real URL.
- Every trigger must be 10+ characters and read like something a developer types in chat.
- description must include NOT for ... — do not remove it.

---
END PROMPT
---

## How Claude Code picks this up

1. Save the Codex output as a .md file in this folder (_codex_drops/)
   - Name it anything, e.g. batch-001.md
2. Claude Code's scheduled task will detect it within minutes and:
   - Parse the === FILE: ... === blocks
   - Scaffold any new skill directories
   - Write all files to the correct paths
   - Run skill_sync.py for each skill
   - Add query fixtures
   - Validate the repo
   - Commit and push
3. Check _codex_drops/processed/ — your file will be moved there when done
   - batch-001.md = success
   - batch-001.md.FAILED = something needs fixing (Claude Code will report what)
