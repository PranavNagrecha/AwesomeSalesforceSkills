---
name: user-story-writing-for-salesforce
description: "Use this skill when authoring INVEST-compliant Salesforce user stories from gathered requirements: shaping the As-A/I-Want/So-That stem, writing Given-When-Then acceptance criteria, sizing complexity (S/M/L/XL), splitting stories that are too large for a sprint, and emitting handoff metadata that names the next downstream agent. Trigger keywords: user story, INVEST, story splitting, story sizing, As-A I-Want So-That, story handoff, recommended_agents, backlog item shape. NOT for requirements elicitation or stakeholder interviews (use admin/requirements-gathering-for-sf). NOT for the Given-When-Then technique itself in depth (use admin/acceptance-criteria-given-when-then). NOT for UAT test case design (use admin/uat-test-case-design). NOT for backlog prioritization (use admin/moscow-prioritization-for-sf-backlog)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
  - Reliability
triggers:
  - "how do I write a Salesforce user story that an admin or developer can actually pick up"
  - "my user stories are too big to finish in a sprint, how do I split them"
  - "what is the canonical As-A I-Want So-That format for a Salesforce backlog item"
  - "how do I add Given-When-Then acceptance criteria to a story"
  - "what handoff metadata should a story carry so the right downstream agent picks it up"
  - "how do I size a Salesforce user story when complexity is unclear"
  - "how do I check that my user stories pass the INVEST test"
  - "user stories isn't working"
tags:
  - user-stories
  - invest
  - story-splitting
  - story-sizing
  - acceptance-criteria
  - agile-handoff
  - backlog-shape
inputs:
  - "Gathered requirement, feature description, or epic narrative to be reshaped into stories"
  - "Target persona(s) — Salesforce profile, permission set, or role of the end user"
  - "Known platform constraints (object volume, integration deps, sharing model) that affect splitting"
  - "Available downstream agents in the chain (e.g. object-designer, flow-builder, lwc-builder, permission-set-architect)"
outputs:
  - "Set of INVEST-compliant Salesforce user stories in canonical As-A/I-Want/So-That + Given-When-Then markdown"
  - "Handoff JSON for each story with story_id, title, as_a, i_want, so_that, acceptance_criteria[], complexity, recommended_agents[], recommended_skills[], dependencies[], notes"
  - "Story-split rationale when an oversize story is broken into 2+ children"
  - "Complexity sizing per story (S / M / L / XL) with the heuristic that drove the score"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-12
---

# User Story Writing For Salesforce

This skill activates after requirements have been gathered and the BA must reshape raw business needs into INVEST-compliant Salesforce user stories that downstream admin/dev agents can pick up without re-asking the user. It owns the *shape* of a story (stem, acceptance criteria, sizing, splitting, handoff metadata) — not the elicitation upstream and not the UAT/build/prioritization downstream.

---

## Before Starting

Gather this context before drafting stories:

- **Has elicitation actually happened?** A story without a real persona, real workflow, and real business outcome is a stub. If the requirement is still vague, return to `admin/requirements-gathering-for-sf` before writing stories.
- **Who is the persona, in Salesforce terms?** "User" is not a persona. The persona must resolve to a profile, permission set, or role (e.g. *Inside Sales Rep with Sales User profile*). Stories without a Salesforce-grounded persona break sharing and FLS reasoning during build.
- **Is there an existing story or epic this overlaps?** Duplicate stories pollute the backlog, race for the same record, and waste sprint capacity. Search the existing backlog before drafting a new story.
- **What downstream agents are available in the chain?** The `recommended_agents[]` handoff field only works if you know which agents the org runs (e.g. `object-designer`, `flow-builder`, `lwc-builder`, `permission-set-architect`). If unknown, default to `["object-designer", "permission-set-architect"]` and flag in `notes`.

---

## Questions to Ask Before Configuring

Ask these before drafting a single stem. Each traces to a numbered gotcha in `references/gotchas.md`; skipping one produces a story that reads cleanly and still sends the build agent back to ask the question that should have been answered here.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Who is the persona, and which Salesforce profile or permission set do they actually hold?" | A persona that isn't grounded in a profile/PSG breaks sharing and FLS reasoning the moment a build agent tries to act on it (Gotcha 2) | A named profile/PSG that `object-designer` and `permission-set-architect` can build against without re-asking | The FLS and record-access model actually matches whoever triggers the story, instead of the build team assuming a default persona |
| "What Salesforce event or user action starts this — a record being created or updated, a button click, a scheduled time, or an inbound message from another system?" | An undeclared trigger forces the build agent to guess between record-create, record-update, or both, and a wrong guess isn't caught until UAT (Gotcha 10) | A trigger named in business terms, precise enough to build against without naming a Flow trigger type | The automation fires on the event the business actually meant, not on the closest one the build agent could infer |
| "What is the one observable thing — a field value, a created record, an error message, a queue/owner change — that proves this worked?" | A `Then` that names no concrete state can't drive a query, a UAT step, or an Apex assertion (Gotcha 11) | A `Then` clause finished enough that "here's how I'd check that in the sandbox" has a real answer | The acceptance criterion is falsifiable — a tester can fail it, not just eyeball it |
| "Roughly how many records does this touch at once — one, a bulk load, or every record on the object?" | Complexity is sized against an assumed volume; an unstated volume defaults to "one," and the story breaks the first time it meets a real load (Gotcha 12) | An explicit volume that lets S/M/L/XL sizing be honest and tells `admin/acceptance-criteria-given-when-then` whether a bulk-path scenario is required | The story is sized for the volume it will actually see, not the volume it was demoed at |
| "What should happen when this fails, is denied, or gets bad input — not just when it works?" | A story with only a happy-path AC ships a feature nobody has thought the failure of through (Gotcha 8) | At least one negative-path Given/When/Then before the story leaves refinement | The feature has a defined failure behavior instead of an unhandled case discovered in production |
| "What automation already runs on this object, and could this story's trigger fire alongside it?" | Record-triggered flows on the same object and save event run in an explicit order (`triggerOrder`, 1–2,000 — api_meta L68438); adding a second one without checking what's already there enters an unnamed race (Gotcha 13) | A short inventory of existing automation on the object, and a flag in `dependencies[]` if this story adds a second flow on the same event | The build agent sets the run order on purpose instead of accepting whatever the org defaults to |
| "Which sandbox will prove this story, and what has to exist there first?" | An AC nobody has run in a sandbox is a hypothesis; the gap surfaces as a UAT defect charged against the build instead of against this handoff (Gotcha 14) | A named sandbox plus the preconditions (queue, PSG assignment, seed record) a tester needs, captured in `notes` | `admin/uat-and-acceptance-criteria` starts its plan from a known environment instead of reconstructing one during UAT |

What a proper set of answers adds up to: every story names who can act, what starts it, what proves it, how big it might get, what happens when it fails, what it might collide with, and where it gets proven — so the handoff JSON is a fact sheet the next agent builds from, not a set of guesses it has to fill in first.

---

## Core Concepts

### The INVEST Checklist

Every story must pass INVEST before it leaves the BA's hands. Salesforce-specific reading:

- **I — Independent.** The story does not block on another incomplete story. Salesforce dependency hotspots: page layout depends on record type, validation rule depends on field, sharing rule depends on OWD. If the story has a hard dependency, list it in `dependencies[]` and consider whether it can be split or reordered.
- **N — Negotiable.** Implementation detail (Flow vs Apex, screen vs record-triggered) is *not* fixed in the story body. The story states the *what*, the build agent picks the *how*. A story that names "use a Record-Triggered Flow with a fast field update" is over-specified.
- **V — Valuable.** The `So That` must name a concrete business outcome (revenue, time saved, error reduced, compliance met). "So that the system works" or "so that data is captured" are not valuable.
- **E — Estimable.** The build team can size it. If complexity is unknowable because the persona, object, or trigger condition is missing, the story is not estimable and must go back to refinement.
- **S — Small.** Fits in a single sprint with capacity to spare. The complexity heuristic below makes this concrete.
- **T — Testable.** Acceptance criteria are boolean pass/fail. Each Given-When-Then must be runnable in a sandbox without interpretation.

### The As-A / I-Want / So-That Stem

The canonical Salesforce shape:

```
As a [Salesforce-grounded persona — profile, permission set, or role],
I want [observable capability tied to a specific object/feature area],
So that [business outcome — revenue, time, error, compliance].
```

Anti-patterns to reject on sight:
- "As a user, I want…" — no persona.
- "As an admin, I want to add a field…" — describes the *implementation*, not the user need.
- "I want the system to automatically…" — system actions are not user wants; reshape as the persona who benefits.
- "So that the system works correctly" — not a business value statement.

### Given-When-Then Acceptance Criteria

This skill uses Given-When-Then but does **not** teach it in depth (that's `admin/acceptance-criteria-given-when-then`). The minimum bar here:

- Every story has **at least one** Given-When-Then block.
- Each block is structured: `Given <context>`, `When <action>`, `Then <observable Salesforce outcome>`.
- Observable outcome = a UI element, field value, error message, record state, or notification — not a database write or class invocation.
- Cover **happy path + at least one sad path** (validation failure, permission denial, null/empty case).

### Complexity Sizing — S / M / L / XL

Use this heuristic when sizing — not story points, not Fibonacci, just a 4-bucket size that downstream agents can consume:

| Size | Heuristic | Typical example |
|---|---|---|
| **S** | Single object, single field/perm change, no automation, no UI work. | Add a required field; grant a permission set. |
| **M** | Single object with one declarative automation (validation rule, simple flow), or one record page tweak. | Auto-set a field via flow; restrict edit via VR. |
| **L** | Multi-object, multi-step flow, or 1 LWC; may touch sharing or page layouts; single integration touchpoint. | Lead-to-Opportunity conversion flow with related records. |
| **XL** | Spans multiple personas, multi-system integration, or requires Apex/LWC + sharing redesign. **An XL must be split** before it leaves refinement. | Quote-to-cash refactor; new approval routing across regions. |

XL stories are not committed — they are split. See the next section.

### Story Splitting Techniques

When a story is XL (or arguably L but unclear), apply one of these splits in order of preference:

1. **By workflow steps.** "Convert lead → create opportunity → notify rep" → 3 stories.
2. **By business rule.** "Approval required for discount > 10% AND deal > $100k" → 2 stories, one rule per story.
3. **By data variation.** "Works for Direct, Partner, and Channel deals" → 3 stories, one record type at a time.
4. **By persona.** "Reps see X; managers see Y; execs see Z" → 3 stories per persona.
5. **By happy path / sad path.** Ship the happy path first, then layer error/exception/edge stories.

Each child story still has to pass INVEST on its own. A split that produces children that can't be demoed independently is the wrong split.

### Handoff Metadata — The JSON Shape

Every story emits a handoff JSON. Downstream agents (`object-designer`, `flow-builder`, `lwc-builder`, `permission-set-architect`) read this to pick up work without re-asking the user:

```json
{
  "story_id": "US-LEAD-042",
  "title": "Auto-assign hot leads to inside sales queue",
  "as_a": "Marketing Operations Specialist with the Marketing Ops profile",
  "i_want": "incoming Leads with Score >= 80 to land in the Inside Sales queue automatically",
  "so_that": "high-intent leads are followed up within the 5-minute SLA window",
  "acceptance_criteria": [
    "Given a Lead with Score >= 80, When it is created, Then OwnerId is set to the Inside Sales queue.",
    "Given a Lead with Score < 80, When it is created, Then OwnerId remains the original creator.",
    "Given a Lead update where Score crosses from 79 to 80, When saved, Then OwnerId reassigns to Inside Sales queue."
  ],
  "complexity": "M",
  "recommended_agents": ["flow-builder", "permission-set-architect"],
  "recommended_skills": ["flow/record-triggered-flow-patterns", "admin/queue-design"],
  "dependencies": ["US-LEAD-040 (Lead Score field exists)"],
  "notes": "Confirm queue membership before flow build. No Apex required at this size."
}
```

Field rules:
- `recommended_agents[]` — **required, non-empty**. Names the next agent(s) in the chain. If unsure, default to `["object-designer"]` and flag in `notes`.
- `recommended_skills[]` — pointers into the SfSkills repo (e.g. `flow/record-triggered-flow-patterns`). Optional but strongly preferred.
- `dependencies[]` — story IDs or named prerequisites (field exists, queue exists, integration live).
- `complexity` — exactly one of `S | M | L | XL`. XL means *not committable* — split first.

### From Story To The Smallest Deployable Artefact

A well-written story maps to real Salesforce metadata even though the story body itself must stay Negotiable — this skill does not write the metadata, it writes the story so the mapping is unambiguous once a build agent (`object-designer`, `flow-builder`, `permission-set-architect`) picks it up. The smallest case is a single validation rule:

**Story:** As an Inside Sales Rep with the Sales User profile, I want a save on an Opportunity to fail when Amount is blank and Stage is "Closed Won", so that revenue reporting never shows a $0 closed deal.

**AC:** *Given* an Opportunity with StageName = "Closed Won" and Amount blank, *When* the rep saves, *Then* the save fails with the error "Amount is required before marking an Opportunity Closed Won." **Complexity:** S.

The Metadata API's `ValidationRule` fields are `errorConditionFormula` (required) and `errorMessage` (required, ≤255 characters — api_meta L45385, L45402), declared inside the parent object's `CustomObject` metadata (sample definition at api_meta L45418). The smallest deployable excerpt a build agent produces from this story is:

```xml
<!-- excerpt: a validationRules entry inside the Opportunity object's CustomObject metadata -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <validationRules>
        <fullName>Closed_Won_Requires_Amount</fullName>
        <active>true</active>
        <errorConditionFormula>AND(ISPICKVAL(StageName, "Closed Won"), ISBLANK(Amount))</errorConditionFormula>
        <errorMessage>Amount is required before marking an Opportunity Closed Won.</errorMessage>
    </validationRules>
</CustomObject>
```

The story's `Then` text and the metadata's `errorMessage` are the same string — that identity is what makes the AC testable rather than aspirational: the failure a tester sees in the sandbox and the failure named in the story are one fact, not two independent descriptions that can drift apart. `references/metadata-examples.md` works this story fully (INVEST check, checker run) alongside a permission-set-plus-group example and a record-triggered-flow example at larger sizes.

---

## Common Patterns

### Pattern: Reshape a Vague Requirement Into a Story

**When to use:** A stakeholder has said "we need lead routing." That's an epic, not a story.

**How it works:**
1. Identify the persona — who actually performs (or benefits from) the work daily?
2. Identify the trigger — what record event or user action starts the workflow?
3. Identify the outcome — what observable state confirms it worked?
4. Draft the As-A / I-Want / So-That stem.
5. Add 3+ Given-When-Then criteria — happy + sad + edge.
6. Size with the S/M/L/XL heuristic; split if XL.
7. Emit the handoff JSON with `recommended_agents[]` populated.

**Why not skip steps:** A story with no Given-When-Then is a wish, not a backlog item. Build agents will refuse to pick it up.

### Pattern: Split an XL Story

**When to use:** Sizing came back XL, or the team can't agree on size (which usually means it's XL with hidden scope).

**How it works:**
1. Pick the split axis (workflow, rule, data, persona, happy/sad).
2. Draft each child story with its own stem + Given-When-Then.
3. Verify each child passes INVEST independently.
4. Order the children: happy path first, sad path last; high-value first when possible.
5. Add cross-references in `dependencies[]`.
6. Replace the parent story with a tracker/epic; do not commit it.

**Why not just commit the XL:** XL stories drag across sprints, block dependent work, and demo poorly. The split is the correctness step.

### Pattern: Emit Handoff JSON Alongside Markdown

**When to use:** Always. The markdown is for humans; the JSON is for the next agent.

**How it works:**
1. Write the story as markdown for backlog tools (Jira, ADO, GitHub Issues).
2. Below the markdown, emit the JSON block in a fenced code block.
3. Populate `recommended_agents[]` from the chain available in the org.
4. Validate the JSON with `scripts/check_invest.py` (this skill's checker) before finalizing.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Persona is "user" or "admin" | Reject and ask BA to ground in a Salesforce profile/perm set/role | Generic personas break sharing and FLS reasoning |
| Story body names Flow vs Apex | Reject — that's a build-time decision | Violates INVEST-Negotiable |
| Acceptance criteria test the UI ("the button is blue") | Rewrite to test behavior ("clicking Save creates the record") | UI is Salesforce's responsibility; ACs test outcomes |
| Story has only happy-path AC | Add at least one sad path before sizing | Half-tested stories regress in UAT |
| Story sizes to XL | Split before committing | XL is uncommittable by definition |
| Story depends on another in-flight story | Add to `dependencies[]`; consider reordering | Independent-I in INVEST |
| Story mixes "the user does X" and "the system does Y" | Split by action source | Mixing actors hides automation triggers |
| `recommended_agents[]` is unknown | Default to `["object-designer"]` and flag in `notes` | Empty handoff metadata breaks the chain |

---

## Recommended Workflow

Step-by-step instructions an AI agent or BA follows when this skill activates:

1. **Confirm prerequisites** — verify requirements were gathered (skill: `admin/requirements-gathering-for-sf`). If not, route there first.
2. **Draft the stem** — As-A (Salesforce-grounded persona), I-Want (observable capability), So-That (business outcome). Reject generic personas and "the system" wants.
3. **Author Given-When-Then ACs** — 1 happy path minimum, 1+ sad path, edge cases as applicable. Each AC must be boolean-testable in a sandbox.
4. **Size with S/M/L/XL** — apply the heuristic table. XL means not committable.
5. **Split if needed** — pick a split axis, draft child stories, verify each child passes INVEST independently.
6. **Emit handoff JSON** — populate `recommended_agents[]`, `recommended_skills[]`, `dependencies[]`, `complexity`, `notes`. Validate with `scripts/check_invest.py`.
7. **Run review checklist** — INVEST pass, persona grounded, AC count > 0, complexity present, handoff JSON valid.

---

## Review Checklist

- [ ] Every story has a Salesforce-grounded persona (profile / permission set / role) — not "user" or "admin"
- [ ] Every `So That` names a concrete business outcome (revenue, time, error, compliance)
- [ ] Every story has at least one Given-When-Then acceptance criterion
- [ ] At least one sad path AC is present per story
- [ ] No story body names a specific Flow type, Apex class, or LWC component (Negotiable)
- [ ] Complexity is exactly one of S / M / L / XL
- [ ] No story is committed at XL — XL is split first
- [ ] Handoff JSON is present, valid, and `recommended_agents[]` is non-empty
- [ ] Dependencies on other stories are explicit in `dependencies[]`
- [ ] Story word count is reasonable (under ~250 words for the body); if it isn't, split

---

## Salesforce-Specific Gotchas

1. **Page-layout and record-type chains** — A story to "show a new field on the layout" is not Independent if the field doesn't exist yet. The build order is field → layout → validation rule. Surface this in `dependencies[]` or split the parent.
2. **Sharing-rule stories that look small** — "Managers can see their team's Cases" sounds S, but if OWD is Public Read/Write, the answer is "they already can" and the real story is OWD tightening. Sizing without checking OWD produces wrong-sized stories.
3. **Persona drift between stem and AC** — Stem says "Sales Rep" but the AC tests "Sales Manager can approve." That's two stories; split by persona.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Story markdown | Human-readable As-A / I-Want / So-That + Given-When-Then ACs, sized S/M/L/XL |
| Handoff JSON | Machine-readable shape consumed by `object-designer`, `flow-builder`, `lwc-builder`, `permission-set-architect` |
| Split rationale | When an XL is split into children, a short note explaining the split axis chosen |
| INVEST self-check report | Output of `scripts/check_invest.py` confirming the story passes structural lints |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You need a full worked example at each size — a validation rule (S), a permission set + permission set group (S/M), and a record-triggered flow (M) — each with the INVEST check, the Given/When/Then criteria, the metadata artefacts implied, and the `check_invest.py` run |
| `references/examples.md` | You want three complete story-plus-handoff-JSON examples (a mobile declarative story, an Apex-required integration story, and an XL parent split into three children) and the "As A User" anti-pattern spelled out |
| `references/gotchas.md` | Before sizing or drafting AC — 14 failure modes with what happens / when it occurs / how to avoid |
| `references/well-architected.md` | You are justifying story-shape depth to a delivery lead, or need the source behind a platform claim (`## Official Sources Used`) |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated stories before they reach a build agent |
| `templates/story-shape.md` | Starting a new story — copy the canonical markdown + JSON shape, fill it in, then lint |
| `templates/user-story-writing-for-salesforce-template.md` | Starting a working session — records the context gathered and which pattern applies |
| `scripts/check_invest.py` | Before every handoff — lints a story document or a folder of them; `--file` for one, `--manifest-dir` for a folder, `--strict` to also fail on WARN findings |

---

## Related Skills

- `admin/requirements-gathering-for-sf` — runs upstream; produces the raw needs this skill reshapes
- `admin/acceptance-criteria-given-when-then` — owns the GWT technique in depth; this skill only enforces presence
- `admin/uat-test-case-design` — runs downstream; turns ACs into UAT scripts after build
- `admin/uat-and-acceptance-criteria` — owns the pre-UAT environment checklist and plan; this skill's sandbox-precondition question (Gotcha 14) only has to name what that checklist needs, not reproduce it
- `admin/moscow-prioritization-for-sf-backlog` — runs alongside; orders the stories this skill produces
- `agents/object-designer/AGENT.md`, `agents/flow-builder/AGENT.md`, `agents/lwc-builder/AGENT.md`, `agents/permission-set-architect/AGENT.md` — common downstream consumers of the handoff JSON
