# Cold-start log — "Original Lead Source" client request

Task: client asked for a custom Opportunity field carrying Lead Source at conversion, protected
from later overwrite. No org access, no deploys. Working purely from the SfSkills repo as a
toolkit. Times are wall-clock, approximate (single-threaded session, no parallel branches).

---

## 12:04 — Start. Read CLAUDE.md (already in system context) + AGENT_RULES.md

- Read (via Read tool): `/Users/pranavnagrecha/VS Code/Personal/SfSkills/AGENT_RULES.md` (full file).
- Decision point: CLAUDE.md's "Required Workflow For Skill Creation Or Skill Update" is scoped to
  *authoring/modifying skills in this repo*. The client's ask is a Salesforce configuration task —
  i.e. a job for a **run-time agent** (per CLAUDE.md's "Run-time agents (68)" section and
  AGENT_RULES.md's "Run-time Agents" section), not a skill-authoring job. Chose to treat this as a
  run-time consulting task: search local coverage, find the owning skill/agent, apply it, never
  deploy, cite everything, per `agents/_shared/AGENT_CONTRACT.md`'s spirit even though (as it turned
  out) no single named agent owns this exact task.

## 12:04–12:05 — Verify retrieval index, read agent roster

- Ran: `python3 scripts/bootstrap.py --verify-only` → exit 1. Failure was "67 slash commands
  installed, 90 in commands/" — a **slash-command install drift**, unrelated to skill content or
  the lexical index. The retrieval self-test inside the same run passed ('trigger recursion' ->
  apex/recursive-trigger-prevention). Per prior project memory ("No false alarms" — don't flag stale
  artifacts or missing hooks, agents self-correct), treated this as a known, non-blocking repo-drift
  issue and proceeded — `search_knowledge.py` does not depend on installed slash commands.
- Read: `agents/_shared/RUNTIME_VS_BUILD.md` (full) — roster of 68 run-time agents + which slash
  command / tier each belongs to.

## 12:05–12:06 — Search local knowledge

- Ran: `python3 scripts/search_knowledge.py "lead conversion field mapping opportunity custom field" --json`
  → exit 0, `has_coverage: true`. Top hits: `skills/admin/lead-management-and-conversion/SKILL.md`
  and its `references/examples.md`, `references/metadata-examples.md`.
- Ran: `python3 scripts/search_knowledge.py "lead source opportunity original lead source" --json`
  → exit 0, `has_coverage: true`. Same skill surfaced again, plus
  `skills/admin/marketing-reporting-requirements` (not used further — that skill is about defining
  marketing KPIs generally, not this specific mechanism).
- **No contradiction here** — both queries converged cleanly on one skill package. No new skill
  needed; this was squarely covered.

## 12:06 — Identify the right agent (or lack of one)

- Ran: `grep -rn "lead-management-and-conversion" agents/_shared/SKILL_MAP.md agents/*/AGENT.md`
  → three agents cite it: `assignment-and-auto-response-rules-designer`, `lead-routing-rules-designer`,
  `path-designer`. None of the three fits (they're about routing/assignment/paths, not
  field-survives-conversion design).
- Read: `agents/object-designer/AGENT.md` (full) — closest-sounding candidate ("/design-object").
  **Ruled it out**: `requires_org: true`, Step 1 of its Plan mandatorily probes a live org
  (`list_custom_objects`, `tooling_query`) and its own refusal table fires
  `REFUSAL_MISSING_ORG` when no `target_org_alias` is supplied — which is my situation. It's also
  scoped to *designing a whole object*, not one field + one Setup nuance.
- **This is the one place I was genuinely unsure what to do next.** No run-time agent in the
  68-agent roster owns "one custom field + a conversion-safety nuance." Decision: don't force-fit an
  ill-matching agent just to have a named one (the repo's own AGENT_RULES.md Step 6 explicitly warns
  against exactly this — "forcing a skill into an agent that does not need it dilutes... worse than
  leaving it uncited"). Instead, apply the on-point skill directly, in the same evidence-grounded,
  cited, no-deploy, confidence-scored shape the repo's AGENT_CONTRACT prescribes for its agents, and
  say explicitly in the final deliverable that this is what I did and why. This is a genuine gap in
  the run-time roster, not a wrong turn on my part — noted as a Process Observation in the
  deliverable rather than silently routed around.

## 12:06–12:08 — Read the source skill in full

Read (full files):
- `skills/admin/lead-management-and-conversion/SKILL.md`
- `skills/admin/lead-management-and-conversion/references/examples.md`
- `skills/admin/lead-management-and-conversion/references/gotchas.md`
- `skills/admin/lead-management-and-conversion/references/metadata-examples.md`

Key finding that reframed the task: the client's literal request ("map Lead Source to a new field
via conversion mapping") doesn't correspond to a real mechanism. `LeadConvertSettings.objectMapping`
"carries **custom** fields only" — Lead Source is a *standard* field, pre-mapped, and that mapping
"cannot be removed, only supplemented." Also learned: `LeadSource` is one global picklist shared by
`Account.AccountSource` / `Contact.LeadSource` / `Lead.LeadSource` / `Opportunity.LeadSource` — so
Opportunity.LeadSource is *already* populated automatically at conversion; the real gap is that nothing
stops someone editing it afterward. This is the single biggest thing that shaped the final design —
without reading gotchas.md and metadata-examples.md in full I would have designed the wrong
mechanism (a Setup field-mapping change that Setup doesn't offer for a standard source field).

- Read: `skills/apex/lead-conversion-customization/SKILL.md` (first ~90 lines) — confirmed via its
  own scope-exclusion line ("NOT for configuring lead conversion field mapping in Setup UI... use
  admin/lead-management-and-conversion") that the admin skill, not this Apex one, is authoritative
  here, and that staying declarative (no Apex) is consistent with both skills' stated boundaries.

## 12:08 — Confirm the automation choice against the decision tree

- Ran: `sed -n '1,120p' standards/decision-trees/automation-selection.md` — Q1 ("A record change")
  → Q2 ("touch only fields on the record itself... under ~10s") → **Before-save record-triggered
  Flow**. Matches the design exactly; cited directly rather than asserted from general knowledge, per
  AGENT_RULES.md's rule to read the relevant tree before picking a technology.
- Ran: `grep -n "before-save..." standards/decision-trees/flow-pattern-selector.md` — one hit,
  confirmed before-save is the documented pattern name used elsewhere in the repo too.
- Read: `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` (full) — canonical shape to adapt
  rather than hand-inventing Flow XML from memory, per CLAUDE.md's Shared Templates Layer rule
  ("reference the canonical template ... do NOT re-invent it inline").

## 12:08–12:09 — Field metadata shape

- Ran: `grep -n "^##|<type>" skills/admin/custom-field-creation/references/metadata-examples.md`
  and read lines 73–115 (the "Required text field" example) — used as the basis for the
  `Original_Lead_Source__c` field XML (description vs. inlineHelpText distinction, `trackHistory`'s
  dependency on the object having `enableHistory` on — flagged as an unverified org-side dependency
  in the deliverable rather than assumed true).

## 12:09–12:13 — Write the deliverable (scratchpad only — never touched the SfSkills repo's own tree)

Created (all under this session's scratchpad, `deliverable/`):
- `force-app/main/default/objects/Opportunity/fields/Original_Lead_Source__c.field-meta.xml`
- `force-app/main/default/flows/Opportunity_Capture_Original_Lead_Source.flow-meta.xml`
  — one self-caught error: first draft used `<operator>NotEqualTo</operator>` against an empty
  `<stringValue>` to express "is not null" on the Flow start filters. That's not the platform's
  documented null-check idiom (Flow Builder's own null checks use `IsNull` with a boolean
  right-hand value, as the repo's own `RecordTriggered_Skeleton.flow-meta.xml` decision element
  does). Corrected both filters to `IsNull` / `booleanValue` before finalizing — caught by
  re-reading my own draft against the template I'd just read, not by any external check.
- `force-app/main/default/package.xml`
- `README.md` — full design doc: mechanism explanation (why the literal ask needed reframing),
  field + flow design and rationale, three questions I answered on the client's behalf (with
  confidence levels, since no one was reachable to confirm), a sandbox test plan adapted from the
  skill's own §8 verification-query pattern, a review checklist, Process Observations, and a
  Citations block in the shape `AGENT_CONTRACT.md` requires of a real run-time agent, even though no
  single named agent executed this.

Deliberately did **not** write anything into the SfSkills repository itself (no `skills/`,
`registry/`, `agents/`, or `docs/` file touched) — this is a client engagement using the repo as a
reference library, not a change to the library, and no run-time agent may "mutate files outside the
paths the user supplied" (`AGENT_RULES.md`, Run-time Agents rules) — no client org/project path was
supplied, so the only safe place to write a deliverable is the session scratchpad.

## 12:13 — Stop point

Process reached a natural stopping point: the design is complete, cited, and internally consistent;
every ambiguity was either resolved (with a recorded, client-plausible answer) or explicitly flagged
as a follow-up. No org access to go further (can't actually deploy, can't run the skill's own
`check_lead_management_and_conversion.py` checker meaningfully since it validates a manifest
directory against org context I don't have, can't run a live sandbox test). This is the natural end
of what a no-org-access, no-deploy engagement can produce.

---

## Places I was unsure, summarized

1. **Which run-time agent owns this?** — None does cleanly. Resolved by applying the source skill
   directly rather than forcing a mismatched agent (see 12:06 entry). Recorded as a Process
   Observation / roster gap rather than hidden.
2. **Scope of the snapshot (every Opportunity vs. conversion-only)?** — No declarative signal exists
   on Opportunity to distinguish "created by Lead conversion" from "created directly." Resolved by
   choosing the simpler, more consistent "every Opportunity" behavior and documenting it as a
   MEDIUM-confidence answer-on-the-client's-behalf, not a silent default.
3. **Text vs. picklist for the new field?** — Resolved using the source skill's own Gotcha 5
   (picklist value-set drift) as the deciding factor; documented as HIGH confidence.

## Contradictions noticed between documents

- `bootstrap.py --verify-only`'s slash-command-count failure vs. the retrieval self-test passing in
  the same run — not a real contradiction once read carefully (two different checks in one script),
  but worth naming because the exit code alone (1) would have wrongly suggested the whole toolkit
  was unusable.
- `skills/admin/lead-management-and-conversion/SKILL.md`'s own "UNVERIFIED (2026-09-05)" marker on
  whether `shouldLeadConvertRequireValidation` defaults true or false — not load-bearing for this
  task (this deliverable doesn't touch `LeadConfigSettings`), so noted here but not chased further.

## Five things that most helped

1. `search_knowledge.py` converging immediately and unambiguously on one skill package — no
   duplicate-candidate ambiguity, no guessing.
2. `references/metadata-examples.md`'s explicit statement that `objectMapping` is custom-fields-only
   plus the LeadSource-is-a-shared-global-picklist note — without this the deliverable would have
   proposed a Setup mapping that doesn't exist for a standard field.
3. `standards/decision-trees/automation-selection.md` giving a citable, deterministic answer (Q1→Q2)
   instead of me asserting "use a Flow" from general Salesforce knowledge.
4. `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` as a copy-adapt base — caught my own
   null-check mistake by comparison.
5. The skill's own "Questions to Ask Before Configuring" table as a *format* to reuse for the
   narrower questions this specific task actually raised, even though most of its rows didn't apply.

## Five things that most hindered / cost the most time

1. No run-time agent in the 68-agent roster actually owns "one field + one conversion nuance" —
   time spent reading `object-designer/AGENT.md` in full before ruling it out on `requires_org` and
   scope grounds.
2. `bootstrap.py`'s hard "BOOTSTRAP FAILED" exit code on a slash-command drift that had nothing to do
   with the actual task — a more precise message would have said sooner "retrieval is fine, only
   command installation is stale."
3. No org access meant every field-level dependency (whether Field History Tracking is already on,
   whether the 20-tracked-field cap has room, current live behavior of `LeadConfigSettings`) had to
   be flagged as "verify in target org" rather than resolved — inherent to the task's constraints,
   not a repo problem, but it's the main reason confidence is HIGH-not-VERIFIED throughout.
4. Determining the correct Flow null-check idiom (`IsNull`/boolean vs. comparing to an empty string)
   required cross-checking the template rather than trusting first instinct.
5. The repo's own workflow section (CLAUDE.md "Required Workflow For Skill Creation Or Skill
   Updates") is written for *building the library*, not *using it on a client engagement*, and
   nothing in CLAUDE.md names which document to read for the latter case — the run-time-agent path
   had to be inferred from the "Run-time agents (68)" and "Agent Expectations" sections rather than
   being pointed to directly for a request shaped like this one.
