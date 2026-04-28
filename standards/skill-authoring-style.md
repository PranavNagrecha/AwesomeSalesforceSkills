# Skill Authoring Style Guide

This file defines **how** a skill should be written — voice, structural patterns, and pattern consistency across the library. It is the canonical reference for SKILL.md and skill-local references files.

## Relationship to Other Standards

| File | Answers |
|---|---|
| `standards/skill-content-contract.md` | **What** a skill must say (factual claims, source grounding, depth, contradiction surfacing, freshness) |
| `standards/source-hierarchy.md` | **Which sources** a claim can come from (Tier 1–4 ladder, contradiction resolution) |
| `standards/naming-conventions.md` | **What identifiers** look like (Apex, LWC, custom objects, Flows, etc.) |
| **THIS FILE** (`skill-authoring-style.md`) | **How** the skill expresses itself — structural patterns, voice, when to use code vs. tables vs. prose |
| `config/skill-frontmatter.schema.json` + `scripts/validate_repo.py` | Mechanical structure (frontmatter keys, file existence, word count) |

A skill that passes `skill-content-contract.md` (says the right things) but fails this guide (says them as 600 words of prose where a 6-row table would do) is shippable but suboptimal — and an agent loading 800 such skills into context pays for the difference.

## Why This Exists

The Tessl PR (#1) and a survey of 800+ existing skills surfaced four authoring techniques that compress and sharpen SKILL.md content for LLM consumption without losing meaning. They were not codified anywhere, and skill-builder agents were producing verbose prose by default. This guide makes the techniques first-class so the next 800 skills don't repeat the gap.

---

## § 1. Scope

Applies to:
- `skills/<domain>/<slug>/SKILL.md` — the canonical entry point
- `skills/<domain>/<slug>/references/*.md` — examples, gotchas, well-architected, llm-anti-patterns
- `skills/<domain>/<slug>/templates/*.md` — skill-local fill-in templates

Does **not** apply to:
- Generated artifacts (`registry/`, `vector_index/`, `docs/SKILLS.md`)
- Cross-skill canonical templates (`templates/`) — those are code/scaffold, not skill content
- Agent definitions (`agents/<slug>/AGENT.md`) — see `agents/_shared/AGENT_CONTRACT.md`

---

## § 2. Voice Principles

Four short rules. The rest of the guide is mechanics; these are the disposition.

### 2.1 Trust the model on Salesforce primitives
Don't re-explain what an OWD is, what a trigger is, what a Lightning Component is, what `WITH SECURITY_ENFORCED` does, what an apex governor limit is. The audience is an LLM that already knows the platform. Re-explaining costs tokens and signals to the reader that the skill doesn't trust them.

**Test**: would a Salesforce-certified developer skim past this paragraph as obvious? If yes, cut it. The skill is not Trailhead.

**Counter-rule**: do explain *non-obvious* platform behavior — that's what `references/gotchas.md` is for. The line is between "documented obvious behavior" (cut) and "documented surprising behavior" (keep).

### 2.2 Lead with the executable artifact
Code, table, or copy-paste snippet first; prose second. Prose explains *why*; the artifact shows *what*. A reader landing on a section should hit something they can use within the first ~5 lines, not a paragraph of setup.

### 2.3 Frontmatter `description` is the sole trigger surface
`description` is what retrieval ranks on and what an agent reads to decide whether to activate. Do not write a body section ("When To Use", "When This Skill Applies", "Use Cases") that paraphrases it. If the description is wrong, fix the description — don't compensate in the body.

### 2.4 DRY between SKILL.md and references/
Each reference file (`examples.md`, `gotchas.md`, `well-architected.md`, `llm-anti-patterns.md`) has an authoritative scope. SKILL.md gets a one-line summary plus a link, never the full content. If you need to repeat content, the split is wrong — promote it up or push it down, but don't duplicate.

---

## § 3. Structural Patterns

Four techniques. Apply them where the data naturally fits — see § 4 for category-specific expectations.

### 3.1 Executable Code Blocks

**When to use**:
- The skill describes a code-shipping pattern (Apex class, LWC component, Flow XML, integration callout, sfdx command sequence)
- A reader needs to copy and adapt, not learn

**Format requirements**:
- Full class/component/script — not pseudocode, not snippets that omit imports
- Realistic identifiers (`AccountTriggerHandler`, not `MyClass`)
- Working syntax that would compile/parse (no `// TODO: implement` placeholders in the SKILL.md version — those go in `templates/`)
- Language fence specified (` ```apex `, ` ```js `, ` ```html `, ` ```xml `, ` ```bash `)

**Reference exemplars** (verified):
- [skills/lwc/lwc-async-patterns/SKILL.md:48](../skills/lwc/lwc-async-patterns/SKILL.md) — async/await imperative Apex pattern with try/catch/finally
- [skills/integration/soap-api-patterns/SKILL.md:85](../skills/integration/soap-api-patterns/SKILL.md) — full SOAP login envelope
- [skills/devops/org-shape-and-scratch-definition/SKILL.md:88](../skills/devops/org-shape-and-scratch-definition/SKILL.md) — deployable scratch-org JSON

**Anti-pattern**: pseudocode that obscures the real implementation:
```
// In your handler, check the trigger context and call the appropriate method
```
This does not help an LLM emit working code. Show the actual `if (Trigger.isBefore && Trigger.isInsert) { ... }` block.

### 3.2 Comparison Tables

**When to use**: ≥3 parallel concepts (channels, options, action types, edition tiers) currently described in separate prose subsections, or about to be.

**Format requirements**:
- 4–6 columns max — beyond that, the table is unreadable on most screens and the data is probably better as a bulleted decision tree
- Columns named for **decision criteria**, not just labels — `License Needed`, `Key Limit`, `When to Use` beat `Description`, `Notes`, `Details`
- Bold the row label (first cell) so scanning works: `| **Send Email** | ... |`

**Reference exemplars** (verified):
- [skills/lwc/lwc-toast-and-notifications/SKILL.md:74](../skills/lwc/lwc-toast-and-notifications/SKILL.md) — ShowToastEvent parameter table
- [skills/architect/org-edition-and-feature-licensing/SKILL.md:63](../skills/architect/org-edition-and-feature-licensing/SKILL.md) — edition hierarchy with `Key Characteristics` column
- [skills/integration/soap-api-patterns/SKILL.md:65](../skills/integration/soap-api-patterns/SKILL.md) — Enterprise vs Partner WSDL with 6 rows × 2 columns

**Anti-pattern**: a 4-row "table" with one column called "Notes" that contains the entire prose paragraph. If two columns hold all the meaning, it's a table; if one column does, it's a list with extra punctuation.

### 3.3 Field-Mapping Tables

**When to use**: any action, component, event, or API call with named input fields whose values matter to the caller (Flow actions, LWC custom events, integration call params, sfdx flag matrices).

**Format**: three columns, fixed names:

```markdown
| Input Field | Value | Notes |
|---|---|---|
| `Recipient IDs` | `{!recipientCollection}` | Text Collection of 15/18-char User IDs only |
```

The third column ("Notes") is where gotchas, format constraints, and silent-failure modes live — and is the column an LLM most wants when wiring up the call.

**Reference exemplars**:
- [skills/lwc/lwc-custom-event-patterns/SKILL.md](../skills/lwc/lwc-custom-event-patterns/SKILL.md) — multi-row event-flag table covering `bubbles`, `composed`, `cancelable`
- The post-PR [skills/flow/flow-email-and-notifications/SKILL.md](../skills/flow/flow-email-and-notifications/SKILL.md) — Send Custom Notification + Send Email field mappings

**Anti-pattern**: numbered prose steps that bury field names: *"Set the Recipient IDs input to a Text Collection of User IDs (must be 15 or 18 chars), then set the Title to..."*. The named fields disappear into a paragraph; the LLM has to parse it back into a table internally to use it.

### 3.4 Copy-Paste Metadata Snippets

**When to use**: any skill whose end state requires a metadata file (Custom Notification Type, Permission Set, Org Shape JSON, sfdx project config, named credential XML, agentforce topic JSON).

**Format requirements**:
- Open with an SFDX path comment so the reader knows where the file lives:
  ```xml
  <!-- force-app/main/default/notificationtypes/Case_Escalation.notiftype-meta.xml -->
  ```
- Include the full envelope (XML declaration, root element with namespace), not a fragment
- Use realistic API names following [`naming-conventions.md`](naming-conventions.md)
- Deployable as-is — a reader should be able to drop the file into a project and `sf project deploy start` without edits beyond renaming

**Reference exemplars**:
- [skills/devops/org-shape-and-scratch-definition/SKILL.md:88](../skills/devops/org-shape-and-scratch-definition/SKILL.md) — full `project-scratch-def.json` with sourceOrg + features + settings
- The post-PR [skills/flow/flow-email-and-notifications/SKILL.md](../skills/flow/flow-email-and-notifications/SKILL.md) — `CustomNotificationType` metadata XML

**Anti-pattern**: describing the metadata in prose ("create a Custom Notification Type record in Setup with mobile and desktop enabled"). Setup-driven authoring is fine for an end user; it's the wrong shape for an LLM that may be operating against a deployable project.

---

## § 4. Per-Category Expectations

Different skill categories have different shapes. This matrix scopes the four techniques per category — apply judgment within these defaults.

| Category | Code blocks | Comparison tables | Field-map tables | Metadata snippets |
|---|---|---|---|---|
| `apex` | **Required** | If parallel concepts | If method/handler params | If `cmdt` or custom-object scaffold |
| `lwc` | **Required** | If parallel concepts | If event/wire/api params | Optional |
| `flow` | Optional (Flow XML) | If multi-channel/element | **Required for action skills** | If Custom Notification, Email Alert, etc. |
| `integration` | **Required** (transport-level) | If multi-API choice | If endpoint/header params | If named credential / external service config |
| `devops` | **Required** (sfdx, CI YAML, package.xml) | If tool/strategy comparison | Optional | **Required** (project config, scratch def, etc.) |
| `omnistudio` | If DataRaptor JSON | If element comparison | If element params | **Required** for OmniScript / FlexCard |
| `agentforce` | **Required** (Action Apex/JSON) | If action types | **Required** for action inputs | **Required** for `genAiPlanner` / topic |
| `admin` | Not required | If config option comparison | If permission set / profile field listing | If permset/profile XML |
| `security` | Optional | If policy comparison | Optional | If permset / restriction-rule XML |
| `data` | If migration script | If pattern comparison | If load template | Optional |
| `architect` | **Not required** | **Required** for any tradeoff decision | Not applicable | Not applicable |

**Reading the matrix**:
- **Required** — at least one instance must be present in the SKILL.md body for skills in this category, or the skill is incomplete.
- **If [condition]** — present when the named condition holds; absent when it doesn't is fine.
- **Optional** — apply judgment.
- **Not required / Not applicable** — explicitly exempt; do not synthesize a code block to satisfy a perceived rule.

---

## § 5. Domain Mismatch — Analytical Skills

Audit, assess, review, governance, and diagnostic skills are **guidance, not implementation**. They are explicitly exempt from "code required" rules in § 4. Forcing executable code into an architecture-decision skill produces inappropriate scaffolding.

These skills still benefit from comparison tables (decision frameworks rendered as tables are easier to apply than as prose), but should not invent code blocks to satisfy a perceived requirement.

**Cited exemplars** (these correctly omit code):
- [skills/architect/org-edition-and-feature-licensing/SKILL.md](../skills/architect/org-edition-and-feature-licensing/SKILL.md) — evaluation framework
- [skills/architect/multi-channel-service-architecture/SKILL.md](../skills/architect/multi-channel-service-architecture/SKILL.md) — design framework
- [skills/data/data-reconciliation-patterns/SKILL.md](../skills/data/data-reconciliation-patterns/SKILL.md) — diagnostic ladder
- [skills/lwc/lwc-debugging-devtools/SKILL.md](../skills/lwc/lwc-debugging-devtools/SKILL.md) — runtime diagnosis
- [skills/lwc/lwc-accessibility/SKILL.md](../skills/lwc/lwc-accessibility/SKILL.md) — UX review (note: § 6 still flags one anti-pattern in this skill — the prose-vs-table issue is independent of code-vs-no-code)

If a skill's job is to *recommend a path* rather than *produce an artifact*, code is wrong. A comparison table or decision matrix is right.

---

## § 6. Anti-Patterns

Concrete remediation pointers. Each anti-pattern names a real example so authors can see it in the wild.

### 6.1 Duplicating `description` as a "When To Use" body section
The frontmatter `description` is the trigger surface. A body section that paraphrases it is dead weight. **Remediation**: cut the body section; if the description doesn't capture the triggers well, fix it.

### 6.2 Parallel concepts in 4 prose subsections instead of one table
**Example**: [skills/lwc/lwc-accessibility/SKILL.md](../skills/lwc/lwc-accessibility/SKILL.md) Core Concepts (lines 50–67) — four accessibility principles in paragraphs.
**Remediation**: collapse into a table with columns like `Principle | Implementation Choice | When to Use | Why Not Alternative`.

### 6.3 Per-step explanations on a numbered list whose headers already convey meaning
**Example**: [skills/data/data-reconciliation-patterns/SKILL.md](../skills/data/data-reconciliation-patterns/SKILL.md) lines 56–74 — "the three levels of reconciliation form a diagnostic ladder" with a paragraph per level.
**Remediation**: keep the ordered list; cut the per-item explanatory paragraph; if the levels need more depth, push it to `references/gotchas.md` or a per-level subsection below.

### 6.4 Inline pillar mapping when `references/well-architected.md` exists
Every skill has a `references/well-architected.md`. SKILL.md should reference it, not duplicate it. **Remediation**: replace inline "Well-Architected Pillar Mapping" sections with a one-line link.

### 6.5 Pseudocode that obscures the real implementation
Showing *"// validate the input then call the API"* helps no one. **Remediation**: show real code (per § 3.1), or remove the block and describe the algorithm in prose.

### 6.6 Same gotcha verbatim in SKILL.md and `references/gotchas.md`
Each gotcha has one home. **Remediation**: SKILL.md gets a one-line summary table or a link; `references/gotchas.md` gets the deep version. Pick one direction; never both.

### 6.7 Numbered prose steps that bury field/parameter names
**Pattern**: "Set the X to Y, then the A to B, then add a fault path that..." for an action with named inputs.
**Remediation**: convert to a § 3.3 field-mapping table.

### 6.8 Setup-only metadata creation when an XML snippet would deploy
**Pattern**: "In Setup, navigate to X, click New, fill in fields A, B, C..."
**Remediation**: include the deployable metadata XML (per § 3.4) alongside the Setup path. Some readers want the click trail; LLMs writing code want the file.

---

## § 7. Pre-Submit Checklist

Five questions to ask before running `skill_sync.py`. If any answer is "no" without a justification noted in the skill, fix it first.

1. **Could any prose section be a table?** (§ 3.2 / § 3.3)
2. **Is there pattern prose where executable code would fit?** (§ 3.1)
3. **Is content duplicated between `SKILL.md` and `references/`?** (§ 2.4)
4. **Does the skill explain Salesforce primitives the model already knows?** (§ 2.1)
5. **Does the frontmatter `description` make a "When To Use" section unnecessary?** (§ 2.3)

For deployable-metadata skills, add:

6. **Is there a copy-paste metadata snippet, or only Setup-path prose?** (§ 3.4)

---

## § 8. Enforcement

### 8.1 Manual (now)
- This guide is referenced from `AGENT_RULES.md` and `AGENTS.md`. Every skill-builder agent (`agents/*-skill-builder/AGENT.md`) lists it in Mandatory Reads. Every PR review and `/review` agent run applies it.
- The `/new-skill` command (`commands/new-skill.md`) instructs authors to satisfy the checklist in § 7 before sync.

### 8.2 Automated (implemented, ERROR-level)
`validate_skill_authoring_style()` in [`pipelines/validators.py`](../pipelines/validators.py) is called from `validate_one_skill()` in [`scripts/validate_repo.py`](../scripts/validate_repo.py) and emits **ERROR-level** findings for the high-confidence duplication anti-patterns from § 6:

| Check | Anti-pattern | Detection |
|---|---|---|
| `## When To Use` body section | § 6.1 — duplicates frontmatter `description` | Line-prefix regex on H2 headings (case-insensitive) — H3 sub-headings exempt |
| `## Well-Architected Pillars` body section | § 6.4 — duplicates `references/well-architected.md` | Line-prefix regex + non-empty WAF reference |
| Verbatim ≥120-char prose paragraph in both files | § 6.6 — same gotcha in two places | Set intersection of normalized paragraphs; code fences and URL-citation bullets exempt |

These checks **block CI**. The corpus was retrofitted to clear every flagged warning before the WARN→ERROR promotion, so a hit now means a real regression — a new skill (or an edit) reintroduced one of the three duplication anti-patterns. Per-category shape rules (Apex/LWC needing fenced code, action skills needing field-mapping tables) are deliberately not implemented yet because the heuristics are fuzzier and false-positives across 900+ skills are expensive to triage.

### 8.3 Retrofit policy
Existing skills are **not retroactively in violation**. The guide is forward-looking — applied to:
1. All new skills going forward
2. Any existing skill being materially edited (a typo fix doesn't count; a new pattern or restructure does)
3. Selected high-value retrofit batches when the validator gains the rules

Mass mechanical retrofit across all 800+ skills is explicitly out of scope. The forward-leverage from styled-by-default new skills > token wins from a retrofit blast.

---

## § 9. Index of Cited Exemplars

| Technique | Skill | Section / Line |
|---|---|---|
| Executable code (Apex/JS) | [skills/lwc/lwc-async-patterns](../skills/lwc/lwc-async-patterns/SKILL.md) | line 48 — async/await imperative Apex |
| Executable code (XML transport) | [skills/integration/soap-api-patterns](../skills/integration/soap-api-patterns/SKILL.md) | line 85 — SOAP login envelope |
| Executable code (deployable JSON) | [skills/devops/org-shape-and-scratch-definition](../skills/devops/org-shape-and-scratch-definition/SKILL.md) | line 88 — scratch org JSON |
| Comparison table (component params) | [skills/lwc/lwc-toast-and-notifications](../skills/lwc/lwc-toast-and-notifications/SKILL.md) | line 74 — ShowToastEvent params |
| Comparison table (edition tiers) | [skills/architect/org-edition-and-feature-licensing](../skills/architect/org-edition-and-feature-licensing/SKILL.md) | line 63 — edition hierarchy |
| Comparison table (API contracts) | [skills/integration/soap-api-patterns](../skills/integration/soap-api-patterns/SKILL.md) | line 65 — Enterprise vs Partner WSDL |
| Field-mapping table (events) | [skills/lwc/lwc-custom-event-patterns](../skills/lwc/lwc-custom-event-patterns/SKILL.md) | event-flag tables |
| Metadata snippet (sfdx config) | [skills/devops/org-shape-and-scratch-definition](../skills/devops/org-shape-and-scratch-definition/SKILL.md) | line 88 — scratch-def JSON |
| Domain-mismatch (no code required) | [skills/architect/multi-channel-service-architecture](../skills/architect/multi-channel-service-architecture/SKILL.md) | full file — design framework |
| Domain-mismatch (no code required) | [skills/data/data-reconciliation-patterns](../skills/data/data-reconciliation-patterns/SKILL.md) | full file — diagnostic ladder |

---

## Maintenance

- This guide is human-maintained. Do not auto-generate.
- When a new exemplar emerges (a skill that demonstrates a technique exceptionally well), add it to § 9 and link it from the relevant § 3 subsection.
- When a category's expectations shift (e.g., a new domain folder is added under `skills/`), update the § 4 matrix.
- The validator rules in § 8.2 were promoted to ERROR after the corpus was retrofitted clean. If a future rule expansion needs calibration, ship it as WARN first and promote only after the warning count reaches zero.
