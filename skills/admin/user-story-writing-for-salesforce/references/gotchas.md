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

---

## Gotcha 10: Trigger Event Left Implicit

**What happens:** The story names the persona and the outcome but never says what starts the work — "As a Support Agent, I want High-priority Cases to get a follow-up Task, so that nothing sits untouched." Created? Updated? Every save? The build agent has to guess which record event the automation should key on, and guesses wrong roughly as often as it guesses right.

**When it occurs:** The BA is confident about the *before* (persona) and the *after* (outcome) but never wrote down the *when*. It reads as complete because both ends are strong.

**How to avoid:** Name the record event or user action in business terms in the `I want` clause itself — "when a Case's Priority becomes High," "when a rep clicks Generate Quote," "on the nightly batch." That is a business fact, not an implementation choice, so naming it does not violate INVEST-Negotiable — it is *which Flow trigger type* (create vs. update vs. both) that stays for the build agent to pick.

---

## Gotcha 11: `Then` Clause Names No Concrete Salesforce State

**What happens:** The AC reads "Then the case gets handled" or "Then it's tracked properly." UAT can't script it, test-class-generator can't pick an assertion, and the story passes review because it *looks* like a Given/When/Then.

**When it occurs:** The BA wrote the shape of an AC (Given/When/Then keywords present) without forcing the Then to name a field, a record, an error string, or a queue — the same gap Gotcha 7 covers for a story with zero AC, one level down, inside an AC that technically exists.

**How to avoid:** Every `Then` must name something a query or a screenshot could confirm: a field and its value, a record that now exists (or doesn't), the exact error message text, or the queue/user that now owns the record. If the Then can't be finished with "...and here's how I'd check that in the sandbox," it isn't done yet.

---

## Gotcha 12: Data Volume Never Named, Sizing Guessed

**What happens:** A story sizes to M on the heuristic table, ships, and then times out or throws a limit exception the first time someone runs it through Data Loader on 5,000 records instead of the one record the BA and the build agent both pictured while writing and sizing it.

**When it occurs:** Nobody asked "one record or a bulk load?" during refinement, so the complexity call was made against an assumed volume of one. `admin/acceptance-criteria-given-when-then` gotcha 1 has the governor-limit mechanics (why 200 is the number that matters); this skill's job is upstream of that — naming the volume before the AC author or the sizing heuristic has to guess it.

**How to avoid:** Ask for the expected volume — daily average and worst case — before sizing. If the answer is "could be bulk-loaded," flag it in `notes` so `admin/acceptance-criteria-given-when-then` knows to add a bulk-path scenario, and size with that volume in mind rather than the single-record demo case.

---

## Gotcha 13: Story Collides With Automation Already On The Object

**What happens:** A new record-triggered story ships cleanly in isolation, then fires in a different order than an existing flow on the same object once both are live — a field the new story depends on hasn't been set yet by the other automation, or vice versa. Nobody sees it until production, because sandbox testing only ever exercised the new story alone.

**When it occurs:** The BA (and the build agent after them) treated the object as a blank slate. Salesforce record-triggered flows on the same object and the same save event actually run in an explicit sequence — `triggerOrder`, an integer from 1 to 2,000 set on the flow (api_meta L68438) — so a second flow added without checking what's already there is entering a race whether anyone names it or not.

**How to avoid:** Ask what automation already exists on the object before drafting. If the story is adding a second flow (or a validation rule, or a trigger) that touches the same save event as something already live, say so explicitly in `dependencies[]` or `notes` so the build agent sets `triggerOrder` deliberately instead of accepting whatever default the org assigns.

---

## Gotcha 14: No Named Sandbox Or Verification Precondition

**What happens:** A story ships with clean Given/When/Then criteria that nobody has actually run anywhere. At UAT, the tester discovers the queue named in the AC doesn't exist in that sandbox, or the persona's permission set was never assigned there — and the defect gets logged against the build when the real gap is upstream, in this skill's output.

**When it occurs:** The BA treats "testable in a sandbox" (INVEST-Testable) as satisfied by the AC's *shape* (Given/When/Then present) rather than by anyone having confirmed the *preconditions* — the queue, the PSG assignment, the seed record — actually exist somewhere.

**How to avoid:** Name the sandbox the story will be proven in and list what has to exist there first (queue, PSG assignment, seed data) in `notes`. This is a handoff, not new work — `admin/uat-and-acceptance-criteria` owns the full pre-UAT environment checklist; this skill only has to say enough that the UAT plan isn't starting from zero.
