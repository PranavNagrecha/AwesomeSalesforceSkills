# Salesforce User Story — Canonical Shape

Use this template every time a Salesforce user story is authored. Two parts:
1. Markdown story (for humans, backlog tools, sprint reviews).
2. Handoff JSON (for the next agent in the chain).

Both are required. The lint script `scripts/check_invest.py` validates both.

---

## Part 1: Markdown Story

```markdown
## US-<DOMAIN>-<NUMBER> — <Short Title (under 70 chars)>

**As a** <Salesforce-grounded persona — profile / permission set / role>,
**I want** <observable capability tied to a specific object or feature>,
**So that** <concrete business outcome — revenue, time saved, error reduced, compliance>.

**Acceptance Criteria:**

- *Given* <context>,
  *When* <action>,
  *Then* <observable Salesforce outcome>.

- *Given* <sad-path context>,
  *When* <action>,
  *Then* <error / blocked outcome — at least one sad path required>.

- *Given* <edge-case context>,
  *When* <action>,
  *Then* <observable outcome>.

**Complexity:** S | M | L | XL

**Notes:** <optional — assumptions, callouts, things the build agent should know>
```

### Rules for the markdown

- **As a** must name a Salesforce profile, permission set, or role. Not "user", not "admin", not "the system."
- **I want** must name an object or feature area, observable to the persona.
- **So that** must name a measurable business outcome.
- **At least one** Given-When-Then is required.
- **At least one** sad-path AC is required (validation failure, permission denial, null/empty case, integration timeout).
- **Complexity** is exactly one of `S | M | L | XL`. XL means *not committable* — split first.
- The body must **not** prescribe Flow vs Apex vs LWC — that's the build agent's call per the decision trees.

---

## Part 2: Handoff JSON

Emit immediately after the markdown story, in a fenced ```json block.

```json
{
  "story_id": "US-<DOMAIN>-<NUMBER>",
  "title": "<Short title — same as markdown header>",
  "as_a": "<verbatim from markdown stem>",
  "i_want": "<verbatim from markdown stem>",
  "so_that": "<verbatim from markdown stem>",
  "acceptance_criteria": [
    "Given <ctx>, When <action>, Then <outcome>.",
    "Given <sad-path ctx>, When <action>, Then <error outcome>."
  ],
  "complexity": "S",
  "recommended_agents": ["object-designer"],
  "recommended_skills": ["admin/object-creation-and-design"],
  "dependencies": [],
  "notes": "<optional context for the build agent>"
}
```

### JSON field rules

| Field | Required | Rules |
|---|---|---|
| `story_id` | yes | Stable ID, kebab-or-dash form (e.g. `US-LEAD-042`) |
| `title` | yes | Matches the markdown header text |
| `as_a` | yes | Salesforce-grounded persona |
| `i_want` | yes | Observable capability |
| `so_that` | yes | Measurable business outcome |
| `acceptance_criteria` | yes | Array of strings, each in Given-When-Then form, at least one entry, at least one sad path |
| `complexity` | yes | Exactly one of `"S"`, `"M"`, `"L"`, `"XL"` |
| `recommended_agents` | yes, **non-empty** | Array of agent names from the available chain (e.g. `object-designer`, `flow-builder`, `lwc-builder`, `permission-set-architect`) |
| `recommended_skills` | optional but preferred | Array of `<domain>/<skill>` paths from the SfSkills repo |
| `dependencies` | optional | Array of prerequisite story IDs or named preconditions |
| `notes` | optional | Free-text for the build agent |

---

## Complexity Sizing Heuristic

| Size | Heuristic | Example |
|---|---|---|
| **S** | Single object, single field/perm change, no automation, no UI work | Add a required field; grant a permission set |
| **M** | Single object + one declarative automation, or one record-page tweak | Auto-set field via flow; restrict edit via VR |
| **L** | Multi-object, multi-step flow, or 1 LWC; may touch sharing/page layouts; single integration | Lead-to-Opportunity conversion flow with related records |
| **XL** | Multiple personas, multi-system integration, or Apex/LWC + sharing redesign | **Split before commit** |

---

## Splitting Techniques (apply if XL or borderline-L)

1. **By workflow steps** — break a multi-stage workflow into one story per stage.
2. **By business rule** — one rule per story.
3. **By data variation** — one story per record type / segment.
4. **By persona** — one story per actor.
5. **By happy path / sad path** — happy first, then layer error/exception/edge stories.

Each child must independently pass INVEST.

---

## INVEST Self-Check (run before commit)

- [ ] **I**ndependent — story does not block on another in-flight story (or `dependencies[]` lists them)
- [ ] **N**egotiable — body does not prescribe Flow/Apex/LWC choice
- [ ] **V**aluable — `So That` names a measurable outcome
- [ ] **E**stimable — complexity is one of S/M/L/XL and reasonable
- [ ] **S**mall — fits a single sprint (XL is split, never committed)
- [ ] **T**estable — every AC is boolean pass/fail in a sandbox

Lint with `python3 scripts/check_invest.py path/to/story.md`. Exit 0 = pass, 1 = fail.
