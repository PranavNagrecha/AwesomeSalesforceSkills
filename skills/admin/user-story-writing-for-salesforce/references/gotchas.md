# Gotchas — User Story Writing For Salesforce

Non-obvious pitfalls when writing Salesforce user stories. These mistakes pass casual review but cause real downstream rework.

---

## Gotcha 1: Story Too Big To Demo In A Single Sprint

**What happens:** Story sizes to L, gets committed, drags into the next sprint, dependent stories block, and the demo at sprint review is "we'll show it next time."

**When it occurs:** Sizing the story by *implementation hours* rather than by the S/M/L/XL heuristic. A "small Apex class plus a few flow steps" sounds small but is actually L because of multi-object touch.

**How to avoid:** Apply the heuristic table strictly. If the story touches more than one object, has more than one automation, or spans more than one persona, it is at minimum L. Any L story that sounds suspicious — split it. Any XL — split, do not commit.

---

## Gotcha 2: Missing Persona ("As A User…")

**What happens:** The story has no Salesforce-grounded persona. Build agent has to call the BA back to ask "which profile? which permission set?" — wasting the handoff.

**When it occurs:** The BA defaults to "user" or "admin" because the actual persona is fuzzy. Often it means stakeholder discovery wasn't completed.

**How to avoid:** Reject any story whose `As A` clause does not name a profile, permission set, or role. If the BA insists "everyone uses it," the story is likely an org-wide setting (OWD, password policy, login IP range) and not a user story at all — handle it differently.

---

## Gotcha 3: Business Value Missing From `So That`

**What happens:** The `So That` says "so that the system works" or "so that data is captured." The story passes shallow review but fails INVEST-Valuable. The team can't tell if it's worth the sprint slot.

**When it occurs:** The BA wrote the story from the *system's* perspective ("so that data flows") rather than the *persona's* perspective.

**How to avoid:** Force the `So That` to name a measurable business outcome — revenue captured, time saved (with a number), errors reduced, compliance met, customer experience improved. If it can't be measured, it isn't valuable. "So that nurture campaigns launch within 24h of every field touch" passes; "so that meetings are tracked" fails.

---

## Gotcha 4: Acceptance Criteria That Test The UI, Not The Behavior

**What happens:** AC says "the Save button is blue and 200px wide." Build team paints a button. UAT passes. Production breaks because nobody tested the *save action*.

**When it occurs:** BA confuses look-and-feel with behavior. Often happens when stakeholders share screenshots during elicitation.

**How to avoid:** Every AC must test an *observable Salesforce outcome*: a record was created, a field was set, a validation error fired, a queue received the case, a notification was sent. UI styling is Salesforce's responsibility. If a styling concern is genuine (accessibility, branding), file it as a separate UI/UX story explicitly.

---

## Gotcha 5: Stories That Mix System Actions With User Actions

**What happens:** Story says "the rep saves the record AND the system auto-routes it AND the manager gets emailed." Three actors, three actions, one story. Sizing comes back wrong, the AC has to interleave actor switches, and demoing it requires three logins.

**When it occurs:** The BA captured the whole workflow as a single story instead of splitting by actor or by step.

**How to avoid:** Split. One story per actor or per workflow step. Use the workflow-step or persona-split technique from SKILL.md. The combined story almost always sizes XL once you count the test paths.

---

## Gotcha 6: Story Reads "The System Shall…"

**What happens:** Story is written in waterfall requirement language: "The system shall validate that…" There's no persona, no business value, no demo path. It looks rigorous but isn't a user story.

**When it occurs:** BA was trained on classic SRS / shall-statements and never reset for agile.

**How to avoid:** Replace every "the system shall" with "as a [persona], I want [observable behavior]." If the rule has no human stakeholder, it's probably a *system constraint*, not a story — track it as a non-functional requirement against the parent epic.

---

## Gotcha 7: AC Count Of Zero ("It's Obvious")

**What happens:** Story has the stem but no acceptance criteria — "it's obvious, just implement it." Build team interprets it three different ways. UAT fails because nobody agrees what "done" means.

**When it occurs:** Late-sprint refinement, or the BA was rushed.

**How to avoid:** Hard rule — every story has at least one Given-When-Then. The lint script `scripts/check_invest.py` enforces this. If you genuinely can't write an AC, you don't yet know the requirement well enough to commit the story.

---

## Gotcha 8: Sad Path Missing

**What happens:** Story has a beautiful happy-path AC and ships. Two weeks later, a rep enters bad data and the flow throws a runtime error with no user-friendly message. Hotfix story added to backlog.

**When it occurs:** BA wrote ACs for the success case only. "What does the rep see when this fails?" was never asked.

**How to avoid:** Require at least one sad-path AC per story (validation failure, permission denial, null/empty case, integration timeout). The lint will flag a story with only happy-path AC patterns.

---

## Gotcha 9: Handoff JSON `recommended_agents[]` Empty Or Missing

**What happens:** Story is committed, but the next agent in the chain has no signal it should pick it up. Story sits in the backlog. Sprint slips.

**When it occurs:** BA wrote the markdown story but skipped the JSON block. Or wrote the JSON but left `recommended_agents` as `[]` to "let the build team decide."

**How to avoid:** `recommended_agents[]` is **required and non-empty**. If genuinely unclear, default to `["object-designer"]` and note it in `notes`. The lint enforces presence; agent runners enforce non-empty.
