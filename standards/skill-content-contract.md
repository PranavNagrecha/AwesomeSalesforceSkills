# Skill Content Contract

This file defines what "done" means for a skill — beyond what `validate_repo.py` can check mechanically.

`validate_repo.py` enforces structure: frontmatter keys, word count, file existence, query fixtures.
This contract enforces quality: content depth, source grounding, contradiction surfacing, and agent usability.

Every agent that builds or reviews a skill must pass both gates.
A skill that passes `validate_repo.py` but fails this contract is NOT shippable.

---

## Why This Exists

An agent can produce a 300-word SKILL.md that passes all schema checks and still be:
- Factually wrong (training data, not official sources)
- Too shallow to be useful (restates the obvious, skips the hard parts)
- Contradictory with other skills in the repo
- Accurate today but stale after the next Salesforce release
- Structured correctly but unusable by the AI tools this repo serves

This contract closes those gaps.

---

## The Five Quality Gates

Every skill must pass all five before it is committed.

```
Gate 1: Source Grounding   — Every factual claim has a sourced tier tag
Gate 2: Content Depth      — Each file meets its minimum depth requirements
Gate 3: Agent Usability    — An AI can follow the skill without asking the user for clarification
Gate 4: Contradiction Check — Conflicts with other skills and between sources are surfaced
Gate 5: Freshness          — Claims are version-aware and stale-risk items are flagged
```

---

## Gate 1: Source Grounding

**Rule:** Every factual claim about Salesforce platform behavior, limits, APIs, or security model must be traceable to a source from `standards/source-hierarchy.md`.

**What counts as a factual claim:**
- Any specific number (limit, threshold, count, timeout)
- Any "X is required" or "X is not allowed" statement
- Any API behavior description
- Any security enforcement rule
- Any "Salesforce recommends" statement

**What does NOT need a tag:**
- Generally known statements ("Apex runs in transactions")
- Claims immediately followed by a clickable official URL
- Structural framing ("This skill covers three modes...")

**Enforcement:**
- Inline tag required: `[T1]`, `[T2]`, `[T3: source-name]` (see `source-hierarchy.md`)
- A claim with no tag and no URL is a contract violation
- A claim tagged `[T3]` with no named source is a contract violation
- A claim tagged `[T4]` anywhere in SKILL.md body is a contract violation — Tier 4 belongs only in research notes, never in shipped skill content

---

## Gate 2: Content Depth — Per-File Requirements

### SKILL.md

| Section | Minimum Requirement |
|---------|-------------------|
| `description` | One sentence. Must include: when to use (trigger scenario), 2+ keyword phrases, at least one explicit "NOT for..." exclusion. |
| `triggers` | 3+ entries. Must be symptom phrases a practitioner would actually type ("how do I..." / "why is X happening..."). Not feature names. Minimum 10 characters each. |
| `inputs` | List what the agent/user must provide before this skill executes. At least 1 entry. Vague inputs like "context" are not acceptable. |
| `outputs` | Concrete artifacts: "deployment-ready trigger handler", "field creation checklist", "reviewed permission set design". Not vague like "guidance". |
| Body | 300+ words (enforced by validate_repo.py). Must be structured with headers. Must be followable by an AI agent without ambiguity. |
| Modes | At least 2 operational modes: Build (create from scratch), Review (assess existing), Troubleshoot (diagnose problems). Not all skills need all three — omit with a comment explaining why. |
| Gather section | List the specific questions or context the skill needs before it can give useful output. An AI that skips this section gives generic answers. |
| Gotcha references | SKILL.md body must reference `references/gotchas.md` at least once. The skill body is not the place to bury non-obvious behaviors. |

**SKILL.md body anti-patterns (contract violations):**
- "Salesforce recommends..." with no source tag
- "It depends on your org setup" with no follow-up questions to resolve the dependency
- Steps that say "configure the settings" without specifying which settings
- Mode 1 that only describes what to do, not how to handle the common failure cases
- Triggers that are feature names: "custom field creation" instead of "how do I add a new field to an object"

---

### references/examples.md

| Requirement | Detail |
|------------|--------|
| Minimum examples | 2 complete examples |
| Example structure | Each example must have: **Scenario** (real business context), **Problem** (what the practitioner is trying to solve), **Solution** (exact steps or code), **Why it works** (ties back to platform behavior), **Source** (Tier tag for the solution) |
| Scenario realism | No placeholder scenarios. "A retail company needed to..." is not acceptable. Use specific, named contexts: "An org with 500k Account records needs..." |
| Solution completeness | A solution that says "configure the field" without specifying the field type, API name format, and FLS steps is not a complete solution |
| Failure example | At least one example must show what goes wrong when the skill is applied incorrectly, and how to recover |

**examples.md anti-patterns:**
- "Example 1: Basic usage" with generic placeholder content
- Solution that assumes things not in the Scenario
- "See the official docs for more details" as the solution

---

### references/gotchas.md

| Requirement | Detail |
|------------|--------|
| Minimum gotchas | 3 entries |
| Gotcha structure | Each gotcha must have: **What happens** (the symptom), **Why** (the platform mechanism that causes it), **How to avoid** (specific prevention), **Source** (Tier tag) |
| Non-obviousness | Gotchas must be non-obvious. "Don't put SOQL in a loop" is a governor limits gotcha, not a skill-specific gotcha. Every gotcha in this file should be something a practitioner would not know without experience. |
| Contradiction surfacing | When sources disagree on this topic (see `source-hierarchy.md` Rule 5), the disagreement is documented HERE using the Tier 3 disagreement format, not buried in SKILL.md |
| Stale-risk items | Gotchas that are likely to change with Salesforce releases must include `[STALE-RISK: describe what to check]` |

**gotchas.md anti-patterns:**
- Gotchas that restate the SKILL.md body
- Gotchas without a "how to avoid" section
- Unattributed "I've seen this happen" anecdotes
- Source disagreements hidden in SKILL.md instead of surfaced here

---

### references/well-architected.md

| Requirement | Detail |
|------------|--------|
| WAF pillar mapping | At least 1 pillar addressed with specific guidance (not just naming the pillar) |
| Official Sources Used | At least 1 Tier 1 URL. Pre-seeded sources from `new_skill.py` must not be deleted — add usage context to them. |
| Contradiction log | If any source conflicts were found during skill research, they must be documented here: what the conflict is, which tier won, and why. |
| Pillar specificity | "This skill touches Security" is not acceptable. The WAF entry must explain HOW and WHY this skill is relevant to that pillar and what practitioners should watch for. |

---

### scripts/check_*.py

| Requirement | Detail |
|------------|--------|
| Stdlib only | No pip dependencies. Must run with `python3 scripts/check_<noun>.py` on any machine with Python 3.8+. |
| Real checks | Must implement actual validation logic. A stub that always passes is a contract violation. |
| Target | Must check for the single most common mistake this skill prevents. One focused check is better than five shallow checks. |
| Exit code | Exit 0 on pass, exit 1 on failure with a human-readable message explaining what to fix. |
| Runnable | Must be runnable standalone. Must accept a path argument or operate on a known relative path. |

---

### templates/<skill-name>-template.md

| Requirement | Detail |
|------------|--------|
| Immediately usable | The template is what an AI produces for the user. It must be fill-in-the-blank, not a meta-template with instructions to the author. |
| Completeness | Covers the most common use case in the skill's Mode 1 (Build). |
| No TODOs | All `TODO:` markers removed. Placeholders use `[REPLACE: description]` format so an AI knows exactly what to substitute. |
| Includes validation section | Every template must include a section the practitioner uses to verify the output is correct. |

---

## Gate 3: Agent Usability

A skill that passes Gates 1 and 2 structurally may still be unusable by an AI agent if it requires implicit knowledge.

**Test:** Can an AI follow this skill from start to finish, for the first time, in an unfamiliar org, and produce a correct output?

**Required for agent usability:**

1. **Gather section is complete.** The skill lists every piece of information it needs before giving advice. An AI that skips the gather phase gives generic, often wrong output. Each input in the gather section must explain WHY it matters, not just what it is.

2. **Decision branches are explicit.** If the skill has different paths based on context ("if the org uses X, do Y; if not, do Z"), every branch is documented. No implicit "you'll figure it out from context."

3. **Failure modes are covered.** Every mode (Build, Review, Troubleshoot) includes at least one "what to do when this goes wrong" path. An AI that has no failure path will hallucinate a recovery.

4. **Cross-skill references are explicit.** If this skill depends on or leads to another skill, it says so: "After completing this skill, use `skills/admin/permission-set-architecture` to configure access." Implicit dependencies break agent chains.

5. **Outputs are concrete.** "Provides guidance" is not an output. The skill must describe what the practitioner has in their hands when the skill is done: a named artifact, a reviewed checklist, a code block, a decision record.

---

## Gate 4: Contradiction Check

Before a skill is committed, the skill builder must check for contradictions with existing skills.

**Check 1: Within-skill contradictions**
- Does SKILL.md body contradict gotchas.md?
- Does examples.md assume different behavior than SKILL.md states?
- Does well-architected.md recommend something SKILL.md warns against?

**Check 2: Cross-skill contradictions**
Run:
```bash
python3 scripts/search_knowledge.py "<skill topic>" --domain <domain>
```
Read the top 3 results. For each overlapping skill:
- Does the new skill recommend something an existing skill warns against?
- Does the new skill define a term differently than an existing skill?
- Do the two skills give different answers to the same practitioner question?

**If a contradiction is found:**
- If the new skill is correct and the existing skill is wrong: update the existing skill. Do not ship two conflicting answers.
- If both are correct for different contexts: make the context explicit in both skills. Add a cross-reference.
- If it cannot be resolved without human judgment: mark `[CONTRADICTED: skill/path]` and add to the skill's `well-architected.md` contradiction log. Do not silently ship the conflict.

**Contradiction log format (in well-architected.md):**
```markdown
## Contradiction Log

### [Topic] — Conflict with [other-skill]
**This skill says:** ...
**[other-skill] says:** ...
**Context where this skill applies:** ...
**Context where [other-skill] applies:** ...
**Resolution status:** Resolved / Needs human review
```

---

## Gate 5: Freshness

Every skill is written at a point in time. Salesforce ships 3 major releases per year. A skill can be structurally perfect and factually wrong after a release.

**Required freshness markers:**

1. **`updated` frontmatter field** is set to the date the skill content was last verified, not just last modified. Changing a template does not update the content verification date.

2. **Version-specific claims use release qualifiers:** "As of Spring '25, the limit is..." not "The limit is..." for anything that has changed across releases.

3. **Deprecated features are marked:** If a skill covers a feature that is deprecated or being retired, say so at the top: `> ⚠ [Feature] is deprecated as of [release]. This skill covers current behavior. Migration guidance is in [other skill or section].`

4. **`[STALE-RISK]` tags on volatile claims:** Any claim about a limit, feature availability, or recommended approach that is likely to change in the next 1-2 releases must be tagged `[STALE-RISK: what to check when reviewing]`.

5. **Currency Monitor responsibility:** Skills flagged by Currency Monitor as potentially stale must have all `[STALE-RISK]` items reviewed and either confirmed current or updated before the flag is cleared.

---

## Contract Violation Severity

Not all violations are equal. The Validator uses this to decide whether to block or warn.

| Violation | Severity | Action |
|-----------|----------|--------|
| Factual claim with no source tag or URL | HIGH | Block commit |
| Tier 4 content in SKILL.md body | HIGH | Block commit |
| examples.md has fewer than 2 complete examples | HIGH | Block commit |
| gotchas.md has fewer than 3 entries | HIGH | Block commit |
| Cross-skill contradiction not documented | HIGH | Block commit |
| Skill body has no decision branches for known variants | MEDIUM | Warn, fix before next release |
| `[STALE-RISK]` tag missing on known volatile claim | MEDIUM | Warn, fix before next release |
| Template has unresolved `TODO:` markers | MEDIUM | Warn, fix before next release |
| Gather section is missing | MEDIUM | Warn, fix before next release |
| check_*.py is a stub (always passes) | MEDIUM | Warn, fix before next release |
| Contradiction log in well-architected.md is absent when conflicts exist | HIGH | Block commit |
| WAF section names a pillar without explaining applicability | LOW | Log, fix opportunistically |

---

## Relationship to Other Standards Files

| File | Relationship |
|------|-------------|
| `AGENT_RULES.md` | Defines workflow steps. This file defines quality within those steps. |
| `standards/official-salesforce-sources.md` | Lists which URLs to use. This file defines how to tag and use them. |
| `standards/source-hierarchy.md` | Defines tier system and contradiction rules. This file enforces those rules in skill content. |
| `standards/well-architected-mapping.md` | Defines the 6 WAF pillars. This file requires skills to apply them specifically, not generically. |
| `config/skill-frontmatter.schema.json` | Validates structure. This file validates quality within that structure. |
| `scripts/validate_repo.py` | Enforces structural gates. This contract enforces quality gates that scripts cannot check. |
