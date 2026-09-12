# Milestone M3 — acceptance report

**Milestone:** M3 — Validation, intake and routing
**Build:** `case-onboarding` (`.sfskills/builds/case-onboarding/`), `build_mode: design-only`
**Verified by:** `milestone-verifier`, run `2026-09-12T06-05-00Z`
**Verdict: `not-ready`** — a recommendation to the human, not a decision. G3 stays with a named person.

**Goal (from `plan.json`):** *Given a case arriving on any of the three channels (Q15), when it is
created, then it has an owner from the assignment rule, the customer has an acknowledgement carrying
the case number sent from support@, and no validation rule blocked the API-created record.*

**Why `not-ready`**, three independent reasons, any one of which is sufficient under
`agents/milestone-verifier/AGENT.md` Step 9:

1. **A step is blocked.** `M3-S05` (Omni-Channel) is `blocked` with a recorded reason and stays
   blocked. § 3 of `standards/build-orchestration.md` permits a human to approve a milestone over a
   blocked-with-a-reason step; it does not permit this agent to call that milestone ready.
2. **A declared milestone acceptance test fails.** `check_custom_permissions.py --manifest-dir
   artefacts --strict` exits **1** against a declared `exit 0` (finding **F-29**).
3. **The step manifests disagree on the API version** — 62.0 on `M3-S01`/`M3-S02`, 67.0 on
   `M3-S03`/`M3-S04` (finding **F-31**, G3 decision item 6).

Approving G3 anyway is a legitimate outcome. It accepts, explicitly: no Omni-Channel push in this
phase; a milestone test whose exit code is red; and a build that deploys at a version no step-level
manifest agrees on. Each is set out below so the decision is a decision.

---

## 1. Blocked step, stated first

| Step | Status | Recorded reason |
|---|---|---|
| `M3-S05` — Omni-Channel push for Tier 1: service channel, routing configuration, presence configuration and statuses | `blocked` | `deferred: Q32, Q33, Q34, Q35` |

`plan.json` `steps[M3-S05].inputs.note` records why the step was blocked rather than planned around:
all four clarifications that decide an Omni-Channel configuration were deferred at G1 — Q32 (objects
pushed, capacity release), Q33 (agent capacity and per-case weight), Q34 (routing model and
tie-breaker), Q35 (push timeout) — and `skills/admin/omni-channel-routing-setup` documents a default
for only one of the four (a service-channel capacity weight, `SKILL.md:177`). `runs[]` is empty; there
is no `artefacts/M3-S05/` directory and no `tests/M3-S05/`.

### What M3-S05's absence leaves unverified

Stated explicitly, because silence here would read as coverage:

1. **No Case work is pushed to anyone.** The three queues exist (`M2-S04`) and the assignment rule
   fills them (`M3-S04`), but nothing pulls from them. Tier 1's interim surface is the Tier 1 General
   queue list view — which is `M5-S01`, a step in a milestone that has not started. Between G3 and
   M5, Tier 1 has no worklist artefact in this build at all.
2. **REQ-022's push half is undelivered.** `traceability.md` maps REQ-022 (*"Tier 1 … should get work
   pushed to them when they are available"*, Q29) to `M2-S04` / `Queue:Tier_1_General`. The queue
   half is built and accepted at M2. The *push* half has no artefact in any milestone, and the RTM
   does not show a gap because the row already resolves against the queue.
3. **Six ERROR-class routing assertions never ran.** `M3-S05`'s declared build-scope test
   `check_omni_channel_routing_setup.py --manifest-dir artefacts` was not executed (no artefacts to
   execute it against). E1 channel-with-no-routing-config, E2 channel-to-presence-status, E3 routing
   config with nobody to route to, E4 missing `relatedEntityType`, E5 routing model or priority,
   E6 zero capacity are all unasserted for this build.
4. **The milestone `manifest` test's Omni-Channel clause passes vacuously.** Its declared text is
   *"Every settings file, rule set, template **and Omni-Channel component** in M3 appears in the
   milestone package.xml with a file behind it."* It is consistent because M3 contains zero
   Omni-Channel components — not because any were checked.
5. **The `Case.OwnerId` writer model is untested against a second writer.**
   `artefacts/M3-S04/owner-writer-map.md` names three by-design writers: the assignment rule (built),
   Omni-Channel push (`M3-S05`, blocked), the escalation rule (`M4-S04`, pending). "The assignment
   rule is the sole authoritative writer at creation" (Q27) is currently true only because the other
   two do not exist. The interaction M4's own manual test asks about cannot be exercised at G3.
6. **Q32–Q35 remain open with no owner or due date on file.** M3's own manual acceptance test asks
   the support manager to fix exactly that at this gate. It is the one M3 manual line whose whole
   purpose is the blocked step.

---

## 2. Steps, statuses and artefacts

Preceding gate `milestone:M2` is **approved** (2026-09-12T03:10:35Z, dry-run operator). Precondition
satisfied.

| Step | Type | Status | Deployable artefacts | Notes on disk |
|---|---|---|---|---|
| `M3-S01` | validation | `documented` | `ValidationRule:Case.Priority_Required_On_Agent_Save`, `ValidationRule:Case.Origin_Must_Be_Known` | `validation-bypass-note.md`, `deploy-order.md` |
| `M3-S02` | ui | `documented` | `EmailFolder:case_intake`, `EmailTemplate:case_intake/Case_Acknowledgement`, `EmailTemplate:case_intake/Case_Escalated_To_Tier2` | `sender-identity-note.md`, `deploy-order.md` |
| `M3-S03` | routing | `documented` | `Settings:Case` | `email-to-case-routing-addresses.md`, `web-to-case-form-contract.md`, `deploy-order.md` |
| `M3-S04` | routing | `documented` | `AssignmentRules:Case`, `AutoResponseRules:Case` | `owner-writer-map.md`, `deploy-order.md` |
| `M3-S05` | routing | **`blocked`** | — | — |

`M3-S03` carries **two build rounds**. Round 1 (`envelopes/M3-S03/2026-09-12T04-16-16Z.json`) was
rejected by the operator's validate-only run against `sfskills-dev`; the step was reset
`built → failed → pending` and rebuilt (`…/2026-09-12T04-39-20Z.json`) with exactly four
operator-proven changes and nothing else — F-25 `systemUserEmail`, F-26 `newEntityRecordType`
object-qualified on both addresses, F-27 `casePriority` on both addresses, and `package.xml`
62.0 → 67.0. SHA-256 before/after hashes for every file are in `artefacts/M3-S03/deploy-order.md` § 0;
`web-to-case-form-contract.md` is unchanged. The rebuilt artefacts were re-tested
(`…/04-53-23Z.json`, step-tester, exit 0) and re-documented (`…/05-05-00Z.json`).

---

## 3. Cross-step reference resolution

Every reference class in `agents/milestone-verifier/AGENT.md` Step 3 that M3 actually exercises was
resolved against the inventory built from M1, M2 and M3. **41 references, 41 resolved, 0 unresolved,
0 unclassifiable.**

Inventory built from the accepted milestones and this one: 1 object, 3 custom fields, 3 `CaseOrigin`
picklist values, 2 record types, 2 business processes, 3 queues, 3 groups, 5 permission sets, 3 PSGs,
1 custom permission, 3 profiles, 2 layouts, 1 compact layout, 1 email folder, 2 email templates.

| Reference class | Read from | Resolved in M3 | Resolved in M1/M2 | Unresolved |
|---|---|---|---|---|
| Validation-rule field references | `errorConditionFormula` tokens + `errorDisplayField` on both `.validationRule` files | 3 `Origin` picklist values | `Origin`, `Priority` (standard Case fields, M1-S01's object), `$Permission.Bypass_Case_Intake_Validation` (M2-S01) | 0 |
| Assignment-rule criteria and targets | every `criteriaItems/field` and `assignedTo` in `Case.assignmentRules-meta.xml` | 2 `Case.Origin` criteria values | `Case.Origin`; queues `Billing`, `Tier_1_General` ×2 (M2-S04) | 0 |
| Auto-response rule | `Case.autoResponseRules-meta.xml` `ruleEntry` | template `case_intake/Case_Acknowledgement` (M3-S02, folder-qualified); 3 `Case.Origin` criteria values | `Case.Origin` | 0 |
| Case settings → routing | `settings/Case.settings-meta.xml` `emailToCase` / `webToCase` | — | 3 `caseOrigin` values, 2 `newEntityRecordType`, `defaultCaseOwner` | 0 |
| Permission-set grants | `fieldPermissions` / `objectPermissions` | M3 adds none | (asserted at M2) | 0 |
| Flow field references | — | M3 contains no Flow | — | n/a |
| Entitlement-process milestones | — | M3 contains none (M4) | — | n/a |
| Layout and path assignments | — | M3 contains none (M1-S02) | — | n/a |

### The five cross-step checks the gate asked for, each with its result

| # | Check | Result |
|---|---|---|
| 1 | Routing-address `caseOrigin` values ⊆ M1-S01's `CaseOrigin` value set | **PASS.** `Email-Support`, `Email-Billing` (`emailToCase`) and `Web` (`webToCase`) all resolve to `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml`. No fourth value anywhere. |
| 2 | Assignment-rule queue names ⊆ M2-S04 queues | **PASS.** `Billing`, `Tier_1_General`, `Tier_1_General`. All three `assignedToType` are `Queue`; `Tier_2_Engineering` is defined and deliberately unused at intake (it is M4-S04's escalation target). |
| 3 | Auto-response template = M3-S02's folder-qualified template | **PASS.** `<template>case_intake/Case_Acknowledgement</template>` matches `artefacts/M3-S02/email/case_intake/Case_Acknowledgement.email-meta.xml` exactly, folder-qualified. `Case_Escalated_To_Tier2` is correctly *not* referenced here — it is M4-S04's `assignedToTemplate`. |
| 4 | `newEntityRecordType` values ⊆ M1-S01 record types | **PASS.** `Case.Support` → `recordTypes/Support.recordType-meta.xml`; `Case.Billing` → `recordTypes/Billing.recordType-meta.xml`. Both in the object-qualified form F-26 proved the org requires; the bare form is absent. |
| 5 | No `senderEmail`/`replyToEmail` equals a routing address | **PASS for the elements named.** Routing addresses are `support@acme.example`, `billing@acme.example`. `senderEmail` = `replyToEmail` = `support-noreply@acme.example`; `systemUserEmail` is the same non-routing address. **One adjacent hit the sweep did surface:** `artefacts/M2-S04/queues/Billing.queue-meta.xml` `<email>billing@acme.example</email>` **is** a routing address. Already on file as `decisions.md` **D-M2S04-04** / **O-M3S04-02**; latent, because no assignment-notification `<template>` is written on the `Billing` entry. Carried to G3 rather than raised as new. |

**What the grep-based check does not cover, stated so the boundary is visible:** it resolves names
against the artefact tree, not against an org. It cannot see whether a name that resolves here also
exists in the target org, and it cannot see a Setup-only object that no metadata type represents —
which is exactly the class F-28 (`OrgWideEmailAddress`) and F-32 (the permission-set *assignment*)
fall into. Both are carried as gate prerequisites, not as resolution failures.

---

## 4. Deployment order

Sequence under test: objects → fields → picklists → record types → layouts → permission sets →
sharing → automation → routing → SLA. Recorded positions taken from the doc keeper's workbook rows.

| Order | Component | Step | Recorded position | Agrees with type? |
|---|---|---|---|---|
| 1 | `ValidationRule:Case.Priority_Required_On_Agent_Save` / `…Origin_Must_Be_Known` | M3-S01 | *no slot* for `validation` in the ten-position sequence; placed by the step's own chain (`workbook/05-validation-rules.md`) | **Gap reported, not a contradiction** — same treatment `BusinessProcess` (`CWB-OBJ-002`) and `CustomPermission` (`CWB-PERM-001`) already get. Real constraint — after the Case object, its fields and `$Permission`'s `CustomPermission` — is satisfied by M1 and M2. |
| 2 | `EmailFolder:case_intake` | M3-S02 | *no slot*; position 1 of 3 inside the step | OK — the folder is the templates' namespace. |
| 3–4 | the two `EmailTemplate`s | M3-S02 | positions 2 and 3 of 3, order between them free | OK. |
| 5 | `Settings:Case` | M3-S03 | 9 of 10 (routing) | OK. Prerequisites `CaseOrigin` + record types (M1-S01) and `Queue:Tier_1_General` (M2-S04) both sit in accepted milestones. |
| 6 | `AssignmentRules:Case` | M3-S04 | 9 of 10 (routing), position 1 inside the step | OK. |
| 7 | `AutoResponseRules:Case` | M3-S04 | 9 of 10 (routing), position 2 inside the step | OK — it needs both the active assignment rule (same step, ahead of it) and M3-S02's template (earlier step). |

**Verdict: no ordering contradiction, and no dependency running backwards through the sequence.**
Two checks the playbook names specifically: no permission set in M3 grants a field defined later
(M3 writes no permission sets at all), and no automation arrives before the routing it triggers —
`AutoResponseRules` is behind both of its prerequisites. Live corroboration: mock-deploy Run 6
assembled M1 + M2 + M3-S01…S04 into one request and validated **42 of 42 components**, with the sole
error being F-28's org-side sender address, not an ordering rejection.

---

## 5. Merged manifest

**Path:** `reports/MILESTONE-M3-package.xml` — **6 types, 8 members.**

| Type | Members | From |
|---|---|---|
| `AssignmentRules` | `Case` | M3-S04 |
| `AutoResponseRules` | `Case` | M3-S04 |
| `EmailFolder` | `case_intake` | M3-S02 |
| `EmailTemplate` | `case_intake/Case_Acknowledgement`, `case_intake/Case_Escalated_To_Tier2` | M3-S02 |
| `Settings` | `Case` | M3-S03 |
| `ValidationRule` | `Case.Origin_Must_Be_Known`, `Case.Priority_Required_On_Agent_Save` | M3-S01 |

- **Member collisions across steps: none.** No member is declared by two steps.
- **Members without a file: none.** All 8 resolve to a file on disk.
- **Files reaching no `<types>` block: none deployable.** The nine `.md` notes
  (`deploy-order.md` ×4, `validation-bypass-note.md`, `sender-identity-note.md`,
  `email-to-case-routing-addresses.md`, `web-to-case-form-contract.md`, `owner-writer-map.md`) are
  build documentation, correctly excluded. The two `.email` body files travel with their
  `.email-meta.xml` as one component each.
- **Version conflict — reported, not silently resolved (F-31).** `M3-S01` and `M3-S02` declare
  `62.0`; `M3-S03` and `M3-S04` declare `67.0`. The merged file carries `67.0` and an XML comment
  naming the disagreement. This is not a coin flip: mock-deploy Run 4 probes (a) and (b) proved
  `newEntityRecordType` is **rejected** at 62.0 and 63.0 and accepted from 64.0, so 62.0 is not a
  live option for this milestone, and 67.0 is the version Runs 5 and 6 actually used. It is still a
  decision a human owns, and it is G3 decision item 6.

`agents/milestone-verifier/AGENT.md`'s refusal table lists an API-version disagreement between step
manifests under `REFUSAL_NEEDS_HUMAN_REVIEW`. This run did **not** refuse: Step 5 of the same
playbook gives an explicit in-report handling for exactly this case ("keep one `<version>` element
and report a conflict rather than picking a winner"), and refusing the whole run would have
suppressed the five other decision items G3 needs. The disagreement is escalated to the human as an
item, which is what the refusal code exists to achieve.

---

## 6. Milestone acceptance tests

Run verbatim from the build directory, `skills` symlink resolving as declared. No `sf` command was
run; `mock_deploy.py` was not run. Captures in `tests/M3/`.

| # | Type | Command / assertion | Expected | Actual | Result |
|---|---|---|---|---|---|
| M3-T1 | checker | `python3 skills/admin/validation-rules/scripts/check_validation_rules.py --manifest-dir artefacts --strict` | exit 0 | exit **0** — `{"score": 100, "findings": [], "summary": "Scanned 2 validation rule(s) across 3 file(s); 0 finding(s) detected.", "blocking": 0}` | **PASS** |
| M3-T2 | checker | `python3 skills/admin/custom-permissions/scripts/check_custom_permissions.py --manifest-dir artefacts --strict` | exit 0 | exit **1** — `0 error(s), 1 warning(s)`; `CP-DESC-02 'Bypass_Case_Intake_Validation' has a 250-character description … approaching the 255-character limit.` then `--strict: failing on warnings.` | **FAIL — F-29** |
| M3-T3 | manifest | Every settings file, rule set, template and Omni-Channel component in M3 appears in the milestone `package.xml` with a file behind it | consistent | 8/8 members two-way consistent; 0 orphan members; 0 unmanifested deployable files. Omni-Channel clause vacuous (§ 1). | **PASS, with the vacuity noted** |
| M3-T4 | checker | `python3 skills/admin/case-management-setup/scripts/check_case_management_setup.py --manifest-dir artefacts` | exit 0 | exit **0** — `No case management setup issues found.` | **PASS** |
| M3-T5 | manual | M3-S05 blocked: support manager acknowledges no Omni-Channel push this phase, Tier 1 works the M5-S01 list view in the interim, and Q32–Q35 have a named owner and due date | ticked at the gate | not ticked | **carried to § 8, line 8** |

M3-T2's own declared description quotes a prior green run of the identical command. That run is not
reproducible today, and the reason is recorded below, not guessed at.

The positive half of M3-T2 still holds and was read off the same stdout: `Custom permissions defined:
1`, `Permission sets / profiles parsed: 8`, `Distinct permissions referenced: 1`, coverage row
`Bypass_Case_Intake_Validation  2  permission set 'Case_Intake_Integration'` — the two consumers are
M3-S01's two validation rules, so the cross-step assertion the test was declared for **passes on its
merits**. Only the exit code is red.

---

## 7. Findings

Ids continue from F-28 (`reports/MOCK-DEPLOY-M3.md` Run 6). Findings F-01…F-28 are unchanged by this
run; F-24 through F-27 remain closed, F-28 remains open as a G3 prerequisite.

### F-29 — HIGH — declared milestone test M3-T2 fails on a description-length advisory about an already-accepted M2 artefact

`check_custom_permissions.py --manifest-dir artefacts --strict` exits 1. The only finding is
`CP-DESC-02`, a **WARN**: `artefacts/M2-S01/customPermissions/Bypass_Case_Intake_Validation.customPermission-meta.xml`
carries a 250-character `<description>` against a 200-character advisory threshold and a documented
255-character platform limit (api_meta L46651). `--strict` makes every WARN blocking, so a style
advisory about an M2 artefact fails an M3 milestone test.

**Provenance, traced rather than assumed.** `CP-DESC-02` did not exist when this test's description
was written: `git log -S"CP-DESC-02"` places it in commit **f5c7ce8ea**, *"fix(admin):
description-length rules in custom-permissions (255, api_meta L46651) …"* — the skill-hardening wave
that closed mock-deploy F-15. `MILESTONE-M2-REPORT-v2.md` F-16 anticipated this in as many words:
it listed "the 250-character `CustomPermission` description … which **no checker reads**". One now
does.

**This is not a metadata defect.** 250 < 255, and the file validated live in mock-deploy Runs 2, 3, 5
and 6. Nothing about the deploy is at risk.

**Three remedies, and the trade each makes.**

| Remedy | Cost |
|---|---|
| (a) Shorten M2-S01's `<description>` below 200 characters and re-run M3-T2 | Touches an artefact inside an **accepted** milestone. One string, no functional change, and it closes M2's own half-open F-16 headroom item at the same time. Requires re-running M2's tests to keep that milestone's record honest. |
| (b) `amend-step --prose-only` is not available — M3-T2 is a *milestone* test, not a step test, and `set-plan` is refused while the build is `building`. Restating the expected value would need a plan-level change this layer has no writer for. | Blocked by § 2 of `standards/build-orchestration.md`. Not a real option today. |
| (c) Fix the checker's exit policy — make `CP-DESC-02` advisory even under `--strict`, or give `--strict` severity scoping | Exactly the remedy already applied one milestone ago to `check_access_model.py` (commit **214da9abd**, *"exits 1 on blocking findings only; --strict"*), for the identical failure shape on the identical artefact. F-17 said these checkers should decide this once rather than per plan; this is the third checker in the same family to hit it. |

**Recommendation: (a) now, (c) as the durable fix.** (a) unblocks the gate today with a one-line edit
whose blast radius is a description string; (c) is the layer the problem actually lives at, and
leaving it unfixed guarantees a fourth instance. Do not drop `--strict` from M3-T2: it was declared
to make an *unresolvable-consumer-reference* WARN blocking, which is the assertion this test exists
for, and removing it would silently retire that assertion to fix an unrelated advisory.

### F-30 — MEDIUM — M3-S02's sender note and M3-S04's built metadata state different acknowledgement senders; manual test B06 is not tickable as written

`artefacts/M3-S02/sender-identity-note.md` § 1 records the acknowledgement's sender as
**`support@acme.example`**, and its § 5 G3 checklist asks the human to tick *"The acknowledgement's
sender is `support@acme.example` for both channels"*. The metadata that actually sets the sender —
`artefacts/M3-S04/autoResponseRules/Case.autoResponseRules-meta.xml` — ships
**`support-noreply@acme.example`**, per the operator's pre-gate amendment (D-M3S04-01).

Manual test B06, carried from `tests/M3-S02/results.json`, is written against the note's reading
(*"…states the self-addressed-loop risk that arises because support@ is both sender and inbound
routing address"*). Against the milestone's own metadata that risk does not arise, because the
sender is not a routing address. B06 is therefore **not tickable as written** — the same class of
defect `D-M3S04-02` already records for W02 on M3-S04, and it is not a test failure: the note is
internally consistent and § 2 of it records both readings honestly. The step simply predates the
operator's decision.

**Recommendation:** fold into G3 decision item 1. Whichever reading the gate affirms, one of the two
artefacts must then be corrected — the note if the gate confirms `support-noreply@`, the auto-response
element if it overturns to `support@` — and B06 re-worded to the reading that survives. Do not tick
B06 as it stands.

### F-31 — MEDIUM — step manifests disagree on the API version; the build has no plan-level version

Covered in § 5 and raised as G3 decision item 6. Already on file as `decisions.md` **O-M3S03-01**
with a `build-planner` v6 remedy (a plan-level `api_version`, or a documented floor every step's
`package.xml` is generated against). Elevated here because O-M3S03-01 is a backlog item and this is
the first gate at which the skew is *inside a single milestone's merged manifest*.

### F-32 — HIGH — the Web-to-Case channel's dependence on the bypass grant is documented but reaches no checklist

`artefacts/M3-S03/deploy-order.md` § 6 records it plainly: both intake channels rely on
`Bypass_Case_Intake_Validation` to get past M3-S01's rules, the Permission Set that carries it
(`Case_Intake_Integration`, M2-S01) must be **assigned** to the identity Email-to-Case and
Web-to-Case actually save as, and "assignment is an org action, outside this build". The file then
says what happens if that identity cannot hold it: *"every intake save fails … a rejection the
submitter never sees, because the web form still returns its `retURL` success page."*

After the F-26/F-27 rebuild the exposure is now **narrower and sharper than § 6 states**, and § 0 of
the same file says so: email cases arrive with `Origin` stamped *and* `Priority` `Medium`, so neither
rule fires on that channel. Web cases arrive with `Origin` = `Web` stamped but **`Priority` blank** —
`WebToCaseSettings` has no priority element (three children, api_meta L112128 ff.). So at the end of
M3, with M4 not built, **`Priority_Required_On_Agent_Save` fires on every Web-to-Case submission
(~60/day) unless the web save identity holds the bypass**, and the customer sees a success page
either way.

M4-S03's before-save flow is the other thing that would close it — before-save record-triggered flows
run ahead of custom validation rules — but that step is `pending` and is itself subject to G3
decision item 2.

Not a metadata defect and not new information; it appears in no `skipped_manual[]` line in any
`tests/<step>/results.json`, so nothing currently puts it in front of the human at G3. **Elevated to
the checklist (§ 8, line 9) and to the go/no-go list.**

### F-33 — LOW — `M3-S03/deploy-order.md` § 6 is stale against § 0 of the same file

§ 6 opens *"Both intake channels create Cases with `Priority` blank (§ 4)"*. § 0 of the same file,
written by the rebuild, states the opposite for the email channel: *"Email-originated cases now
arrive with `Priority` already set to `Medium` … M3-S01's `Priority_Required_On_Agent_Save` plus
`Bypass_Case_Intake_Validation` is now load-bearing for the **web** channel only."* § 4's
`casePriority` row was struck through and updated; § 6's opening sentence was not. § 6 is the section
headed *"Confirm before the first real submission in each org"* — the half a human acts on.

**Recommendation:** one-sentence correction to § 6 when the step is next touched. No rebuild, no
status change. Recorded so the next reader does not carry the wrong scope into the org.

### Carried, not re-raised

| Item | Where it lives | Status at this gate |
|---|---|---|
| **F-28** — `support-noreply@acme.example` is not a verified `OrgWideEmailAddress` in `sfskills-dev` | `MOCK-DEPLOY-M3.md` Run 6; `D-M3S04-03` | Open. G3 decision item 4. |
| **D-M2S04-04 / O-M3S04-02** — `Queue:Billing`'s `<email>` is the `billing@` routing address | `decisions.md` | Latent: no assignment-notification template is written. Carried, per O-M3S04-02's own remedy. |
| **O-M3S02-03** — `deploy-order.md` undeclared in `outputs[]` on M3-S01…S04 (and M1-S01, M1-S02, M2-S02) | `decisions.md` | Open by design; `amend-step` cannot fix a `documented` step. Planner-template remedy recorded. |
| **O-M3S04-03** — `check_rtm.py` derives two component keys per rule file, producing 2 explained orphan WARNs | `decisions.md`; `traceability.md` | Open as a skill-depth candidate. RTM itself: 37 rows, 0 coverage gaps, 0 errors. |
| **O-M3S04-01** — Q24's "Run assignment rules" checkbox | `decisions.md`; `D-M1S02-03` | Open. G3 decision item 5. |

---

## 8. The six G3 decision items

Presented together, because they interact: items 1, 2 and 3 each change an artefact if decided one
way, items 4 and 5 are org actions no artefact can carry, and item 6 governs the manifest all of them
deploy through.

### Item 1 — D-M3S02-04: the acknowledgement's sender identity. Confirm or overturn.

**What is on the table.** `plan.json` Q22 says the acknowledgement is sent *"from
`support@acme.example` … per the answer key: support@ (a live routing address) itself sends the
acknowledgement."* `answers-key.md`'s Acknowledgement row says it is sent from `support@acme.example`
*"(an org-wide email address, **never the Email-to-Case routing address itself**)"*. The two describe
one address in mutually exclusive terms.

**What is built.** The operator pre-resolved it for `M3-S04` only, by amendment to the step's `notes`
(2026-09-12T05:12:42Z): `senderEmail` = `replyToEmail` = `support-noreply@acme.example`, a
non-routing address matching M3-S03's `systemUserEmail`.

**Recommendation: CONFIRM the operator's pre-resolution.** Three reasons, in order of weight.
(i) Two independent skills state the prohibition and neither states the opposite —
`email-templates-and-alerts/references/metadata-and-sender-identity.md` ("must **not** be the
Email-to-Case routing address, or the acknowledgement re-enters Email-to-Case and loops") and
`email-to-case-configuration/references/gotchas.md` #3, with `assignment-rules/references/gotchas.md`
#6 a third. The answer key's "never the routing address itself" reading has **no citation in either
cited skill**; Q22's reading has two prohibitions against it. (ii) `answers-key.md`'s own "Mailbox
ownership" row confirms IT holds forwarding rules on `support@`, which is the exact precondition
gotcha 3's unbounded loop needs. (iii) The volume makes the failure mode expensive: ~400 email cases
a day through `support@`.

**What confirming costs, stated so it is not a free tick.** `replyToEmail` mirrors `senderEmail`
(D-M3S04-04), so a customer who hits *Reply* on the acknowledgement writes to a mailbox that does not
feed Email-to-Case and **that reply does not thread onto the case**. Replies to the *original*
Email-to-Case thread are unaffected (thread token in subject and body, M3-S03). If that is
unacceptable, the fix is `replyToEmail` = `support@acme.example` with `senderEmail` left at
`support-noreply@` — a third option neither D-M3S02-04 nor D-M3S04-04 names, and the one that buys
threading without reintroducing the loop, since the loop is a *From*-address mechanism.

**If overturned to Q22's reading:** only `senderEmail` (and possibly `replyToEmail`) in
`artefacts/M3-S04/autoResponseRules/Case.autoResponseRules-meta.xml` changes — `deploy-order.md` § 0
confirms nothing else in the step depends on it — and the Q68 sandbox loop test becomes a release
blocker rather than a confirmation.

**Either way**, F-30 must be closed: `sender-identity-note.md` § 1/§ 5 and the B06 checklist line
have to be reworded to whichever reading survives.

### Item 2 — D-M3S03-02: `casePriority` = `Medium` on email cases vs. M4-S03's null guard.

**What happened.** The as-built file left `casePriority` unset on purpose so M4-S03's before-save flow
— specified to write `Case.Priority` "guarded so it writes only into a null value" — would still fire
for email cases. The org refused the file: Run 4 probe (d) returned `EmailToCaseRoutingAddress[support@acme.example]:
Missing casePriority`. The rebuild set `Medium` on both addresses, which is the value the skill's own
worked example carries, not an answered clarification.

**Consequence.** M4-S03's null guard is dead on the email channel; it still fires for web, because
`WebToCaseSettings` has no priority element. The two intake channels now derive `Priority`
differently. The operator has already amended M4-S03's `notes` via `amend-step --prose-only`
(`steps[M4-S03].amendments[0]`) so its builder will not discover this cold — but the amendment records
the consequence, it does not make the choice.

**Recommendation: option (2) — have M4-S03 derive `Priority` from `Severity__c` / `Support_Tier__c`
and unconditionally overwrite for email-originated cases.** It is the reading Q16 supports (*"priority
must be set from what the form or email tells us"*), it makes the two channels behave alike, and
option (1) — accepting `Medium` as the email channel's intake priority — quietly hands ~400 cases a
day the same priority regardless of what the customer wrote, which the first-response SLA and the
8-business-hour escalation clock both read. Choosing (2) also has a bearing on item 3 and on F-32:
once M4-S03 stamps `Priority` before save, the web channel's dependence on the bypass grant is
closed by the flow rather than by a permission-set assignment.

**If (1) is chosen instead**, say so in the requirement record and re-word M4-S03's specification —
leaving the plan's "null-guarded" wording standing over a guard that cannot fire is how the next
reader inherits a false statement.

### Item 3 — D-M3S04-02: Account-support-tier routing is omitted. Which queue for Premier?

**The mismatch.** `steps[M3-S04].title` and the W02 manual test both say the rule routes on
`Case.Origin` **and** the Account support tier. The built rule routes on `Case.Origin` only; no
`criteriaItems` anywhere names `Account.Support_Tier__c`.

**Why the builder did not write it,** two independent reasons either of which stands alone:
(i) **no target** — Q25 names `Account.Support_Tier__c` as a field available at save, but no
clarification, no line of `requirement.md` and no `answers-key.md` row says which queue a `Premier`
case should go to instead of the Origin-derived one; the requirement gives Premier a faster **SLA**
(4 business hours, M4-S02), not a different owner. (ii) **no grounded notation** — no file under
`skills/` documents a `criteriaItems/field` on a *related* object inside a Case assignment rule.
Guessing `Account.Support_Tier__c` or `Case.Account.Support_Tier__c` is the same class of guessed
value shape that produced F-26 (`Support` where the org required `Case.Support`) and cost a rebuild.

**Recommendation: option (b) — correct the title and W02 to Origin-only.** Nothing in the requirement
asks for tier-based *routing*; it asks for tier-based *SLA*, which M4-S02 delivers. Adding a Premier
queue would create a fourth work pool with no staffing answer behind it (Q8 splits 18 users 12/4/2
with no Premier team), and would need a live org to confirm the cross-object notation before a single
line could be written honestly. Correcting the title is the cheaper true statement.

**If option (a) is chosen** — a human names the tier→queue mapping — then the step is rebuilt
(`documented → running`), and the cross-object `criteriaItems` notation must be confirmed against a
live org first, not inferred. Note that `Account.Support_Tier__c` already exists in the tree
(`artefacts/M1-S01/objects/Account/fields/Support_Tier__c.field-meta.xml`), so the field is not the
blocker; the notation and the destination are.

**Either way, W02 must not be ticked as written.** It asserts behaviour the artefact does not have.

### Item 4 — F-28: the org-wide email address is a deploy prerequisite.

`sfskills-dev` carries no `OrgWideEmailAddress` record at all (`SELECT Address FROM
OrgWideEmailAddress` → 0 rows), and there is no metadata type for one — `admin/email-templates-and-alerts`
§ "Org-wide email address (the sender)" documents it as Setup-only and requiring verification. Run 6
therefore failed on one component of 42: `AutoResponseRule Case.Case_Acknowledgement:
support-noreply@acme.example is an invalid From email address.` The assignment rule validated cleanly
in the same request.

**This is an org prerequisite, not a metadata defect.** No file this build can emit substitutes for a
verified org-wide address, and the value is the one the operator chose at item 1.

**Recommendation: accept as a named G3 prerequisite with an owner and a date, and do not rebuild.**
Concretely: before `AutoResponseRules:Case` is deployed to **any** org, a human provisions and
verifies the address chosen at item 1 as an `OrgWideEmailAddress` in that org. Two consequences to
record with the acceptance: (i) the same address is M3-S03's `systemUserEmail` (D-M3S03-01), so one
mailbox unblocks both, and (ii) the whole M3 manifest is deployable **today** except this one
component — so a partial validation run is available if the address is not ready (Run 6's
per-component table is the evidence).

If item 1 is overturned to `support@acme.example`, F-28 dissolves for the sender — `support@` is a
live routing address and already exists — but the loop risk returns and Q68's sandbox test becomes
the blocker instead. The two are a trade, not independent.

### Item 5 — O-M3S04-01: Q24's "Run assignment rules" checkbox is declared by no step.

Q24 requires the "Assign using active assignment rule" checkbox **defaulted on** for the Case
layouts, because ~20 cases a day are logged by hand. `D-M1S02-03` recorded at M1 that M1-S02's layouts
carry `<showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>` and nothing that
pre-checks it, because no element in the cited skill's inventory does so. The consequence is now
concrete rather than hypothetical: `owner-writer-map.md` § 5 states that without the default, "~20
cases a day are owned by their creator and get no acknowledgement" — both the assignment rule and the
auto-response rule fire only when the box is ticked.

It is a Setup-level layout property no step's `outputs[]` can add. `metadata-builder` could not write
it at M1-S02 and cannot write it at M3-S04.

**Recommendation: accept the narrowing at the gate, with the process control written down.** ~20
cases a day against ~480 is the smallest of the three exposures on this list, and the remedy is a
one-line habit: agents tick the box. Record it as an agent-training line in the M5 UAT script rather
than a metadata change. **Do not** route it to a Setup step until someone has established whether a
`Layout` element that defaults the checkbox on exists in the Metadata API guide — this build did not
establish that, and `skills/admin/record-types-and-page-layouts` should be deepened if it turns out
one does.

**What accepting costs:** the ~20 hand-logged cases a day are the population the acknowledgement is
*least* needed for (the agent is on the phone with the customer) and *most* needed for on ownership
(they sit with their creator rather than a queue). Flag it in the M5 sandbox proof as a named negative
case, not a background assumption.

### Item 6 — O-M3S03-01: the build deploys at 67.0 while M1/M2 manifests say 62.0.

`newEntityRecordType` is rejected at 62.0 and 63.0 and accepted from 64.0 (Run 4 probes a–c, proven
live; UNVERIFIED in `admin/case-management-setup` gotcha 9, which instructs the element but names
neither the floor nor the object-qualified form). M3-S03's rebuild pinned `package.xml` at 67.0 — the
org's own version, and the version M4's Apex steps already target. `artefacts/M1-S01/package.xml`,
every `M2-*` manifest, and M3-S01/M3-S02 still read 62.0. `reports/MILESTONE-M1-package.xml` and
`MILESTONE-M2-package.xml` both read 62.0.

`scripts/mock_deploy.py` computes the deployed version as the **highest** across the selected steps
(its own fix, landed with this rebuild), which is why Runs 5 and 6 validated cleanly at 67.0. A real
pipeline that pins a version per package rather than computing a request-wide maximum would fail
exactly the way `mock_deploy.py` did before that fix.

**Recommendation: (i) accept 67.0 as this build's version and say so at the gate; (ii) do not rewrite
the M1/M2 step manifests or their merged manifests — they are accepted artefacts and the deployed
version is a request-level property, not a per-file one; (iii) adopt O-M3S03-01's planner v6 remedy —
a plan-level `api_version` field, or a documented floor every `metadata-builder` step's `package.xml`
is generated against; (iv) until (iii) lands, anyone deploying this build for real passes an explicit
`--api-version 67.0` rather than trusting any single step's `package.xml`.**

Note the interaction with item 1: if the gate overturns to `support@`, nothing about the version
changes — F-26's floor is set by `newEntityRecordType`, which is not in play in either reading.

---

## 9. Manual checklist for G3

Collected from every `skipped_manual[]` in `tests/M3-S0{1,2,3,4}/results.json`, plus M3's own manual
acceptance test, plus the two prerequisites this run elevated. Each line names its source, what the
human does, and what counts as a tick.

| # | From | What the human does | Ticks when |
|---|---|---|---|
| 1 | M3-S01 (W01) | Read both `.validationRule` files | Each `errorConditionFormula` opens with `NOT($Permission.Bypass_Case_Intake_Validation)` (Q56); emptiness is tested with `ISBLANK(TEXT(<picklist>))` not `ISPICKVAL(<picklist>, "")` alone; only component fields are named, never a compound address field (Q59); the error message is final text an agent can act on, not a placeholder (Q93). *Verifier note: all four hold on disk; this is a read, not a re-derivation.* |
| 2 | M3-S02 (B06) | Read `sender-identity-note.md` and the two `.email` bodies | **NOT TICKABLE AS WRITTEN — see F-30.** The line asserts the sender is `support@acme.example` and that the loop risk arises because support@ is both sender and routing address; the built metadata sends from `support-noreply@acme.example`. Re-word to whichever reading item 1 settles, then tick. The half that *is* tickable now: neither `.email` body hardcodes a recipient address. |
| 3 | M3-S03 | Read `settings/Case.settings-meta.xml` | Both routing addresses carry their own `caseOrigin` (`Email-Support`, `Email-Billing`) and no `caseOwner`; `unauthorizedSenderAction` is `Bounce`; `overEmailLimitAction` is `Requeue`; `saveEmailHeaders` true on both; the `webToCase` block carries `enableWebToCase` true and a `caseOrigin` that is a live M1-S01 value, with `defaultResponseTemplate` deliberately unset. *Verifier note: every clause confirmed on disk. `casePriority` and `newEntityRecordType` are now also present — added by the F-26/F-27 rebuild after this line was written, and covered by item 2 rather than by this tick.* |
| 4 | M3-S03 | Read `web-to-case-form-contract.md` | It states whether the form posts directly to Web-to-Case or through middleware, the `Origin` value each path stamps, and that the HTML form is not metadata and is authored outside this build. *Verifier note: the file states the two paths and says the choice is still open (Q66) rather than assuming one — read that as the tick condition, not as a gap.* |
| 5 | M3-S04 (W02) | Read `Case.assignmentRules-meta.xml` | **NOT TICKABLE AS WRITTEN — see G3 item 3 / D-M3S04-02.** The line asserts routing on `Case.Origin` **and** the Account support tier; the rule routes on Origin only. The rest of the line *is* satisfied: the last entry is a catch-all with no `criteriaItems` and no `booleanFilter` assigned to `Tier_1_General`, and every `assignedTo` names a queue that exists under `artefacts/M2-S04/queues/`. |
| 6 | M3-S04 | Read `Case.autoResponseRules-meta.xml` | Exactly one acknowledgement entry can match any given case — no second entry, no parallel Flow email alert on the same event — and its `template` names M3-S02's Classic template, folder-qualified. *Verifier note: one `autoResponseRule`, one `ruleEntry`, `template` = `case_intake/Case_Acknowledgement`. Confirmed; this one is a clean tick.* |
| 7 | M3-S04 / item 1 | Decide D-M3S02-04 on the record | The gate record names the acknowledgement sender explicitly, and says whether the reply-threading cost (D-M3S04-04) is accepted or a third option is taken. |
| 8 | M3 milestone test | Support manager acknowledges the M3-S05 gap | The record states that no Omni-Channel push is built this phase, that Tier 1 works the Tier 1 General queue list view (M5-S01) in the interim, and that **Q32, Q33, Q34 and Q35 each have a named owner and a due date.** |
| 9 | **Elevated — F-32** | Confirm the bypass grant reaches the web intake identity | Someone confirms that the identity Web-to-Case saves as can hold the `Case_Intake_Integration` Permission Set and has been assigned it — **or** the gate records that Web-to-Case intake is knowingly at risk until M4-S03's before-save flow stamps `Priority`. Failure here is silent: the form still returns its `retURL` success page. |
| 10 | **Elevated — F-28 / item 4** | Name an owner and a date for the org-wide address | A human is named to provision and verify the acknowledgement sender as an `OrgWideEmailAddress` in each target org before `AutoResponseRules:Case` deploys there. |

No line on this list states an outcome the human cannot observe. Lines 2 and 5 state an outcome the
**artefact** cannot satisfy, which is a different defect and is called out in place.

---

## 10. Requirement closure

M3 carries eight requirements. Per `traceability.md` (37 rows, 0 coverage gaps, 0 errors, 2 explained
orphan WARNs — O-M3S04-03):

| REQ | Step | Artefact | Machine half | Manual half |
|---|---|---|---|---|
| REQ-030 | M3-S01 | `ValidationRule:Case.Priority_Required_On_Agent_Save` | pass | outstanding (TC-M3S01-01) |
| REQ-031 | M3-S01 | `ValidationRule:Case.Origin_Must_Be_Known` | pass | outstanding (TC-M3S01-03) |
| REQ-032 | M3-S02 | `EmailTemplate:case_intake/Case_Acknowledgement` | pass | outstanding (TC-M3S02-01) |
| REQ-033 | M3-S02 | `EmailTemplate:case_intake/Case_Escalated_To_Tier2` | pass | closed at checker level (M3-S02-T1) |
| REQ-034 | M3-S03 | `Settings:Case` (routing addresses) | pass | outstanding (TC-M3S03-01) |
| REQ-035 | M3-S03 | `Settings:Case` (Web-to-Case) | pass | outstanding (TC-M3S03-02) |
| REQ-036 | M3-S04 | `AssignmentRules:Case` | pass | **outstanding and not tickable as written** (W02) |
| REQ-037 | M3-S04 | `AutoResponseRules:Case` | pass (one org caveat, F-28) | outstanding, on-disk consistent |

**Closed by this milestone at the metadata level: eight of eight.** **Closed at the UAT level: one**
(REQ-033). The remaining seven sit `In UAT` and close at M5's sandbox proof, which is where the
requirement's own *"we must be able to prove it works in a sandbox before customers see it"* is
honoured.

**Not closed, and not visible as a gap in the RTM:** REQ-022's push half (§ 1.2). The row resolves
against `Queue:Tier_1_General` from M2, so the matrix reads green while the capability it names is
unbuilt. That is a property of how the row was written, not a checker failure — recorded here because
the RTM's own green is the thing a reader would otherwise trust.

---

## 11. Optional validate-only command

**OPTIONAL, AND RUN BY A HUMAN. This agent did not run it, ran no `sf` command of any kind, ran no
`mock_deploy.py`, and deployed nothing.**

For a **sandbox** target — a dry run that compiles and validates without saving:

```bash
sf project deploy start \
  --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M3-package.xml \
  --dry-run --target-org <alias>
```

For a **production** target the command is different, and naming the wrong one sends you into an
error that has nothing to do with this build:

```bash
sf project deploy validate \
  --manifest .sfskills/builds/case-onboarding/reports/MILESTONE-M3-package.xml \
  --target-org <prod-alias>
```

Salesforce documents `deploy validate` as production-only; it requires Apex tests and returns a job
id for a later `sf project deploy quick`.

**Two things to know before running either.** (i) Expect **one component to fail** —
`AutoResponseRule Case.Case_Acknowledgement` — until the org-wide address from item 4 is provisioned
and verified in the target org (F-28). Everything else validated at 42/42 in mock-deploy Run 6.
(ii) `routingAddresses` is a **full-replacement list** — `artefacts/M3-S03/deploy-order.md` § 7:
retrieve `Settings:Case` from the target org *first*, because removing an address from this list
deletes it from the org and `emailServicesAddress` / `isVerified` cannot be restored by re-adding the
element.

---

## 12. Gate

The verdict was recorded with the single plan write this agent makes:

```bash
python3 scripts/build_plan.py set-milestone .sfskills/builds/case-onboarding/plan.json M3 \
  --status rejected --report-path reports/MILESTONE-M3-REPORT.md
```

`--status rejected` is the bookkeeping projection of a `not-ready` verdict. It is a statement about
what the checks found — a blocked step, a red milestone test, a manifest version conflict — **not** a
rejection of the milestone. `milestones[].status` and `report_path` are plan bookkeeping; the gate
record stays empty until a human writes it.

The gate command, for a human to run. **This agent did not run it and has no authority to:**

```bash
python3 scripts/build_plan.py gate .sfskills/builds/case-onboarding/plan.json milestone:M3 approve \
  --by "<name>"
```

§ 3 of `standards/build-orchestration.md` will check three conditions before writing it: the `plan`
gate is approved (it is), `milestone:M2` is approved (it is, 2026-09-12T03:10:35Z), and every step in
M3 is `documented` **or** blocked with a recorded reason (M3-S01…S04 are documented; M3-S05 is blocked
with `deferred: Q32, Q33, Q34, Q35`). The command will therefore be accepted.

**Approving anyway accepts the gap.** Specifically: no Omni-Channel push in this phase and the five
consequences in § 1; a declared milestone acceptance test that exits 1 (F-29); and a merged manifest
at an API version no step-level manifest in M1 or M2 agrees with (F-31). To reject instead:

```bash
python3 scripts/build_plan.py gate .sfskills/builds/case-onboarding/plan.json milestone:M3 reject \
  --by "<name>"
```

---

## 13. Files this run wrote

| Path | What |
|---|---|
| `reports/MILESTONE-M3-REPORT.md` | this report — written, not rendered (§ 2 of the standard) |
| `reports/MILESTONE-M3-package.xml` | merged milestone manifest, 6 types / 8 members, version conflict in a comment |
| `tests/M3/check_validation_rules.{stdout,stderr,exit}` | M3-T1 capture |
| `tests/M3/check_custom_permissions.{stdout,stderr,exit}` | M3-T2 capture (the failing one) |
| `tests/M3/check_case_management_setup.{stdout,stderr,exit}` | M3-T4 capture |
| `envelopes/M3/2026-09-12T06-05-00Z.{json,md}` | this run's envelope and its markdown twin |

Nothing else was touched. No artefact, test result or document written by another agent in the loop
was edited, moved or deleted. No step status was changed. No gate record was written. `plan.json` was
touched only by the one `set-milestone` subcommand above.

---
---

# Re-verification — 2026-09-12 (run `2026-09-12T07-20-00Z`)

**Nothing above this line has been rewritten.** The original report stands as written, including the
parts this section corrects. It records what was true at run `2026-09-12T06-05-00Z`; this section
records what changed and what did not.

**Trigger:** commit **`fec2a222b`** — *"`*-DESC-02` description-headroom findings are INFO in all five
access/object checkers (never fail, even under `--strict`) … DESC-01 over-limit stays ERROR"* —
landed after the first run, closing **F-29 at the source**.

**Verdict: still `not-ready`, now resting on exactly one ground — the blocked step `M3-S05`.**
`set-milestone` stays at `rejected`. Reasoning in § R5, including why `ready-with-findings` is not
available here and what would make it available.

---

## R1. Re-run tests

Re-run verbatim from the build directory. Captures in `tests/M3/*.v2.{stdout,stderr,exit}`.

| Id | Command | Expected | v1 exit | v2 exit | Change |
|---|---|---|---|---|---|
| M3-T1 | `check_validation_rules.py --manifest-dir artefacts --strict` | exit 0 | 0 | **0** | none — `score 100`, 0 findings, `blocking 0` |
| M3-T2 | `check_custom_permissions.py --manifest-dir artefacts --strict` | exit 0 | **1** | **0** | **F-29 CLOSED** |
| M3-T3 | `manifest` (two-way) | consistent | consistent | **consistent** | none — re-merged and compared; the membership block is byte-identical to the file on disk |
| M3-T4 | `check_case_management_setup.py --manifest-dir artefacts` | exit 0 | 0 | **0** | none — `No case management setup issues found.` |
| M3-T5 | `manual` (M3-S05 acknowledgement) | ticked at the gate | not ticked | not ticked | none |

**M3-T2's new output**, in full where it matters:

```
Summary: 0 error(s), 0 warning(s), 1 info.
```
```
INFO:
  CP-DESC-02 'Bypass_Case_Intake_Validation' has a 250-character description
  (M2-S01/customPermissions/...); approaching the 255-character limit.
  Headroom only -- never fails the run, even under --strict.
```

**All five declared milestone tests now stand at their declared outcome. 4 of 4 executable/structural
tests pass; 0 fail.**

### The fix was verified, not taken on trust

A checker that stops failing is indistinguishable from a checker that stopped checking, so both halves
were reproduced on a scratchpad copy of `artefacts/` — never on the build.

| Negative control | Command | Result |
|---|---|---|
| **The assertion M3-T2 was declared for still bites.** `$Permission.Bypass_Case_Intake_Validation` → `$Permission.Bypass_Ghost` in `Origin_Must_Be_Known` | `check_custom_permissions.py --manifest-dir artefacts --strict` | **exit 1** — `WARN: 'Bypass_Ghost' is referenced by 1 consumer location(s) but is not defined in the tree`, then `--strict: failing on warnings.` The same command without `--strict`: **exit 0**. |
| **The real limit still blocks.** Description padded to 271 characters | `check_custom_permissions.py --manifest-dir artefacts` (no `--strict`) | **exit 1** — `ERROR: CP-DESC-01 … the Metadata API field limit is 255 characters (api_meta.txt L46651-46652) and the deploy will be rejected.` |

So `fec2a222b` reclassified the headroom advisory and nothing else: the unresolvable-consumer
assertion `--strict` was declared for is intact and still exit-1, and the over-limit guard still
fails *without* `--strict`. **F-29's recommendation (c) — fix the exit policy at the checker rather
than shorten a string in an accepted milestone — was the remedy taken, and it is the right one.**
Recommendation (a), editing M2-S01's description, is now unnecessary and should **not** be done: it
would touch an accepted milestone's artefact to silence a line that is already INFO.

`decisions.md` **F-16** (M2, "headroom half open") is closed by the same commit for the same reason.

---

## R2. What did not change

Re-checked rather than assumed. `find artefacts -newer reports/MILESTONE-M3-REPORT.md` returns
nothing: no artefact was modified after the first report was written.

- **Reference resolution** — 41/41 resolved, 0 unresolved, 0 unclassifiable. All five
  operator-named cross-checks still pass. Unchanged.
- **Deployment order** — no contradiction, no backwards dependency. Unchanged.
- **Merged manifest** — 6 types, 8 members, 0 collisions, 0 members without a file, 0 unmanifested
  deployable files. Re-merged and compared: identical. `reports/MILESTONE-M3-package.xml` was **not**
  rewritten.
- **Requirement closure** — 8/8 at metadata level, 1 at UAT level, 7 `In UAT`. Unchanged.
- **F-30, F-31, F-32, F-33** — all still open. See § R4.
- **`M3-S05`** — still `blocked`, `deferred: Q32, Q33, Q34, Q35`. Everything in § 1 of the original
  report, including the six things its absence leaves unverified, stands unaltered.

---

## R3. The six G3 decisions, now taken

Recorded from the coordinator. Each is the operator's, not this agent's.

| # | Item | Decision taken | Matches this report's recommendation? |
|---|---|---|---|
| 1 | D-M3S02-04 sender identity | `senderEmail` confirmed `support-noreply@acme.example`; **`replyToEmail` unchanged** (also `support-noreply@`) | Recommendation **confirmed**. My suggested third option **rejected — correctly. See § R3.1.** |
| 2 | D-M3S03-02 `casePriority` vs the M4-S03 null guard | option **(2)** — M4-S03 derives `Priority` from `Severity__c`/`Support_Tier__c` and overwrites | matches |
| 3 | D-M3S04-02 Premier routing | option **(b)** — correct the title and W02 to Origin-only | matches. **Executability caveat: F-34, § R4.** |
| 4 | F-28 org-wide address | accepted as a named G3 prerequisite, no rebuild | matches |
| 5 | O-M3S04-01 Q24 checkbox | narrowing accepted | matches |
| 6 | O-M3S03-01 API version | 67.0 accepted, planner v6 `api_version` adopted | matches |

### R3.1 — Correction: my "third option" on `replyToEmail` was wrong, and the skill already said so

The original report offered, under decision item 1, *"a third option neither decision names:
`replyToEmail = support@acme.example` with `senderEmail` left at `support-noreply@` — buys threading
without reintroducing the loop, since the loop is a From-address mechanism."*

**That is false, on two counts, and both were available to me when I wrote it.**

1. **The skill names `replyToEmail` in the loop pattern explicitly.**
   `skills/admin/assignment-rules/references/gotchas.md` Gotcha 6 opens: *"An `autoResponseRules` rule
   entry's `senderEmail` **(or `replyToEmail`)** is set to the same address as an Email-to-Case routing
   address's `emailAddress`."* That clause was committed in `0c6a13440` at 2026-09-11 23:48, roughly
   six hours before my run. The loop is **not** a From-address-only mechanism: an out-of-office or
   bounce auto-reply is addressed to Reply-To, so `replyToEmail = support@` puts mail back on the
   routing address by exactly the route Gotcha 6 describes. The checker agrees —
   `check_assignment_rules.py` rule `AR-LOOP-01` *"cross-references every `autoResponseRules`
   `senderEmail` against every `routingAddresses/emailAddress`"* and `AR-SENDER-01` treats
   `senderEmail`/`replyToEmail` as one class.
2. **"Neither decision names it" was wrong about a decision I had read.** `decisions.md`
   **D-M3S04-04** names it and rejects it: *"Alternative not chosen here: setting `replyToEmail` to
   `support@acme.example` so replies thread onto the case. Not written, because that is the routing
   address `D-M3S04-01`'s value was chosen specifically to avoid naming in this element."*

I presented as a novel third way something the build had already considered and rejected on grounds
the cited skill states in one sentence. The operator caught it. **`artefacts/M3-S04/autoResponseRules/Case.autoResponseRules-meta.xml`
is correct exactly as built** — `senderEmail` and `replyToEmail` both `support-noreply@acme.example` —
and the reply-threading cost recorded in D-M3S04-04 is a consequence to accept, not a defect to
engineer around. Nothing in the artefacts changes.

---

## R4. Findings after re-verification

| Id | Was | Now |
|---|---|---|
| **F-29** | P0 — M3-T2 exits 1 | **CLOSED at source** by `fec2a222b`, remedy (c). Verified by re-run plus two negative controls (§ R1). |
| **F-30** | P2 — sender note vs. metadata disagree; B06 not tickable | **Open, and now actionable rather than blocked.** Decision 1 settles which side is wrong: `artefacts/M3-S02/sender-identity-note.md` § 1 and § 5 must be corrected to `support-noreply@acme.example`, and B06 re-worded to match. The auto-response metadata is correct and must not be touched. Not this agent's write — `build-doc-keeper` owns the note, and B06's text is an `acceptance_tests[].description` that `amend-step --prose-only` can carry. |
| **F-31** | P2 — API version conflict | **Open as a recorded fact, closed as a decision.** 67.0 accepted; planner v6 `api_version` adopted. The merged manifest's comment already states this. **Correction to my own framing: this was never a Step 9 verdict trigger** — see § R5. |
| **F-32** | P1 — Web-to-Case bypass grant on no checklist | **Open, and decision 2 does not close it yet.** Option (2) makes M4-S03's flow the mechanism that stamps `Priority` before the validation rule runs — but M4-S03 is `pending` and unbuilt. Until it exists, Web-to-Case (~60/day) still depends on the bypass grant reaching the web save identity. **Checklist line 9 stands and must be ticked or explicitly accepted at G3.** |
| **F-33** | INFO — stale § 6 sentence in `M3-S03/deploy-order.md` | Open. Unchanged. One-sentence fix when the step is next touched. |
| **F-34** | — | **NEW, P2. See below.** |

### F-34 — P2 — decision 3 is only half-writable: `M3-S04`'s title cannot be corrected while the step is `documented`

Decision 3 takes option (b): *correct the step's title and W02 to Origin-only*. Checked against the
writer rather than assumed:

- **W02's text is writable now.** It is an `acceptance_tests[].description`, and
  `amend-step --prose-only` accepts `notes` and `acceptance_tests` *"at any status except `running`"*,
  with an already-approved step gate no obstacle.
- **The title is not.** `title` is an amendable field only under full `amend-step`, which is *"refused
  unless … the step's own status is `pending` or `blocked`"*. `M3-S04` is `documented`. `--prose-only`
  does **not** include `title` in its allowlist (`--file` may then hold *"only notes,
  acceptance_tests"*). Confirmed from `build_plan.py amend-step --help`, not only from the standard.

So the half of decision 3 that removes the false claim from the *test* can be executed today; the half
that removes it from the *step title* cannot, short of rebuilding a correct step for no build reason.
This is the same shape as `O-M3S02-03` (undeclared `deploy-order.md` on five steps, unfixable because
`amend-step` will not touch a documented step).

**Recommendation, and it is a recommendation — this agent makes no `plan.json` write but the one
`set-milestone` call.** Do all three, in this order:
1. `amend-step --prose-only` on `M3-S04` to re-word W02 to Origin-only, citing D-M3S04-02 option (b).
   That is the artefact a human ticks at the gate, so it is the one that has to be true.
2. Record in `decisions.md` that `steps[M3-S04].title` still names Account-support-tier routing, is
   known wrong, and is unfixable in place — the same treatment `O-M3S02-03` gives its analogue. Do
   **not** rebuild `M3-S04` to fix a title.
3. Add to the planner v6 backlog, beside `api_version`: **`title` belongs in `--prose-only`'s
   allowlist.** A title is prose about a step; it decides no output, no checker and no edge, and
   D-M3S04-02 is now the second case where a decided correction cannot be written because a
   text-only field sits behind a structural gate.

---

## R5. Verdict, and why `ready-with-findings` is not available

**`not-ready`.** Recorded with `set-milestone --status rejected`.

**A correction to the original report's own framing.** § "Why `not-ready`" gave three grounds. Only
two of them are in the Step 9 enum — *"at least one unresolved reference, ordering contradiction,
failing test, **or blocked step**"*. The API-version conflict (F-31) was a finding I escalated, not a
verdict trigger, and listing it as a third ground overstated it. Of the two real grounds, the failing
test is now gone. **The verdict rests on the blocked step alone.**

**Why that alone is enough, and why it is not this agent's call to soften.** Step 1 of the playbook is
explicit about the one verifiable-but-incomplete state: *"Verify it, list every blocked step and its
reason at the top of the report, and the verdict is `not-ready` — the decision to accept a milestone
with a known gap belongs to the human at the gate, and it is only a decision if the report puts the
gap in front of them."* Returning `ready-with-findings` over a blocked step would fold that decision
into a verdict line and quietly make it for the human, which is the one thing this agent exists not
to do. Both earlier milestones returned `ready-with-findings`; neither had a blocked step. M3 is the
first that does.

**What the verdict is not.** `rejected` is bookkeeping about what the checks found. It is not a
judgement on the build. On the merits: four of five steps built, tested and documented; every
declared test at its declared outcome; 41/41 references resolved; no ordering contradiction; a clean
merged manifest; and 42 of 42 components validated live in mock-deploy Run 6 bar one org-side sender
address. **Absent `M3-S05`, this milestone would return `ready-with-findings`.**

**The gate is fully approvable and the path is clear.** § 3's three conditions are all met, so
`gate milestone:M3 approve` will be accepted. Every one of the six G3 decisions is taken. What a
human signs at G3 now:

| What approving accepts | Status |
|---|---|
| No Omni-Channel push this phase; the six consequences in § 1 of the original report | the blocked step — decided by accepting it |
| Q32–Q35 get a named owner and a due date at this gate | checklist line 8, must be done at the gate |
| Web-to-Case depends on the bypass grant until M4-S03 exists (F-32) | checklist line 9, tick or explicitly accept |
| `support-noreply@acme.example` provisioned as a verified `OrgWideEmailAddress` before `AutoResponseRules:Case` deploys (F-28) | checklist line 10, named prerequisite |
| API 67.0 as this build's version, M1/M2 manifests left at 62.0 (F-31) | decided, decision 6 |
| B06 and W02 corrected before they are ticked (F-30, F-34) | decided; two of three writes executable today |

Nothing on that list is a surprise, and nothing on it is this agent's to sign.

---

## R6. Files this re-verification wrote

| Path | What |
|---|---|
| `reports/MILESTONE-M3-REPORT.md` | **this section appended**; everything above the double rule is unmodified |
| `tests/M3/*.v2.{stdout,stderr,exit}` | the three re-run checker captures |
| `envelopes/M3/2026-09-12T07-20-00Z.{json,md}` | this run's envelope and markdown twin |

`reports/MILESTONE-M3-package.xml` was re-derived, compared and **not rewritten** — it was already
correct. No artefact, test result or document written by another agent was edited, moved or deleted.
No step status changed. No gate record written. No `amend-step` run — F-34's three writes are
recommendations for their owners. `plan.json` touched only by the one `set-milestone` subcommand. No
`sf` command, no `mock_deploy.py`, no org contact, nothing deployed. The two negative controls ran on
a scratchpad copy of `artefacts/`, never on the build.
