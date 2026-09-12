# Decisions log

Append-only. Written by the build doc keeper.

Entry shape follows `skills/devops/development-documentation-standards` § "Org-level design
standards" — one central location, and an entry that records the date, the step, the agent that
made the call, **the alternative it rejected** and **the source it was grounded in**, rather than a
sentence asserting the outcome. Append-only: an earlier entry is never rewritten, and a reversal is
a new entry naming the one it supersedes.

---

## D-M1S01-01 — Status values per Support Process are a DEFAULT, not a decision

- **Date:** 2026-09-06
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-05T19-40-00Z`)
- **Kind:** design trade-off, recorded by the owning agent as a default
- **What was recorded:** `Support Process` exposes `New` (default), `Escalated`, `Closed`;
  `Billing Process` exposes `New` (default), `Closed`. The builder's envelope files this under
  `source: "skill worked example (default, not a plan decision)"` — the plan settled *that* two
  processes exist, never *which* values each exposes.
- **Alternative rejected:** adding Status values, or deploying a `StandardValueSet:CaseStatus` file
  alongside the two processes. Rejected because assumption **A28** fixes the processes as subsets of
  the CaseStatus value set the org already has, and instructs the builder to block the step rather
  than invent a value if one is missing.
- **Grounded in:** `skills/admin/record-types-and-page-layouts/references/metadata-examples.md`,
  which quotes the Object Reference on `Case.Status` — "such as New, Closed, or Escalated". Those
  three names were the entire vocabulary available. The Escalated/no-Escalated split is grounded in
  `requirement.md` L13–L16 (untouched cases escalate to Tier 2, 4 engineers) against L8 (finance
  queries worked by 2 finance staff): engineering escalation is a support-side state.
- **Why it is a default and not a decision:** Q1's answer says the two record types differ "on
  Status/Reason" and enumerates no values; A28 records the same gap. The split above is the smallest
  one consistent with the requirement, not a customer-confirmed one.
- **Open item:** retrieve `StandardValueSet:CaseStatus` from the target org and confirm `New`,
  `Escalated` and `Closed` are live values before deploy; confirm the split with the process owner.
  `Case.Reason` is named in Q1's answer and is deliberately **not** configured — no clarification
  enumerates a Reason value, so no `picklistValues` block for it was written.
- **Evidence:** `artefacts/M1-S01/record-type-decision.md` § 2;
  `envelopes/M1-S01/2026-09-05T19-40-00Z.json` → `extensions.decision_record[8]`.

## D-M1S01-02 — `Case.Severity__c` ships with one value, `Severity 1`

- **Date:** 2026-09-06
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-05T19-40-00Z`)
- **Kind:** design trade-off — an ambiguity recorded rather than filled
- **What was recorded:** the restricted picklist carries exactly one value, `Severity 1`.
- **Alternative rejected:** writing the obvious rest of the scale (Severity 2, 3, 4). Rejected
  because no clarification enumerates them and `agents/metadata-builder/AGENT.md` forbids inventing
  a picklist value; a plausible scale would look confirmed while being the agent's own.
- **Grounded in:** `requirement.md` L18 — "Severity 1 outages are 24/7 and never pause" — which is
  the only severity level any source names. Q38's answer repeats it and adds no others.
- **Consumer:** `M4-S04`'s escalation entry with `businessHoursSource: None` selects on this field,
  so the value name is load-bearing downstream.
- **Open item:** confirm the full severity scale with the customer before deploy.
- **Evidence:** `artefacts/M1-S01/objects/Case/fields/Severity__c.field-meta.xml` (the rationale is
  in the field's own `<description>`); `artefacts/M1-S01/record-type-decision.md` § 6.

## D-M1S01-03 — Business-process `fullName` is "Support Process"; the file stem is `Support_Process`

- **Date:** 2026-09-06
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-05T19-40-00Z`)
- **Kind:** design trade-off, raised by the owning agent as a naming divergence
- **What was recorded:** three different spellings of the same two components are all correct in
  their own place, and none of them can be normalised away:

  | Where | Form used | Why |
  |---|---|---|
  | file path | `businessProcesses/Support_Process.businessProcess-meta.xml` | the path the step's `outputs[]` declares |
  | inside the file, and inside each `RecordType` | `Support Process` — bare, with a space | the `<fullName>` and the `<businessProcess>` reference |
  | `package.xml` | `Case.Support Process` — object-qualified | the manifest member form |

- **Alternative rejected:** renaming the process to `Support_Process` so all three agree. Rejected
  because the name with the space is what `RecordType.businessProcess` resolves against at deploy
  time and what the manifest member names; changing it to match a file name would change the
  deployed component.
- **Grounded in:** `skills/admin/record-types-and-page-layouts/references/metadata-examples.md`
  ("Where the files live" — bare name inside the record type, object-qualified in the manifest);
  confirmed on disk by the tester's `tests/M1-S01/manifest.stdout`, which resolved
  `BusinessProcess 'Case.Support Process'` ↔ the `Support_Process...` file in both directions with
  0 findings.
- **Consequence for the traceability matrix:** `check_rtm.py --manifest-dir artefacts/M1-S01`
  indexes each component twice — once from `package.xml` (member form) and once from the file stem —
  and reports the file-stem keys `BusinessProcess:Support_Process`,
  `BusinessProcess:Billing_Process` and `CompactLayout:Case.Case_Intake` as orphans, because the
  matrix rows name the `fullName` / manifest form the Metadata API actually uses. The WARN is the
  divergence above surfacing in a second tool, not a gap in the matrix.
- **Open item for the planner:** the owning agent asked for the step's `outputs[]` file name and the
  process name to be reconciled at v6. There is no spelling that satisfies both; the reconciliation
  is a decision about which one the plan states, not a rename.
- **Evidence:** `envelopes/M1-S01/2026-09-05T19-40-00Z.json` → `process_observations[2]` and
  `extensions.open_items_for_the_human[2]`; `artefacts/M1-S01/deploy-order.md` § "Manifest member
  forms used".

## D-M1S01-04 — `Account.Region__c` and `Account.Support_Tier__c` carry no field default

- **Date:** 2026-09-06
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-05T19-40-00Z`)
- **Kind:** design trade-off
- **What was recorded:** neither restricted picklist declares a default value. `Region__c` offers
  `EMEA` and `US`; `Support_Tier__c` offers `Premier` and `Standard`.
- **Alternative rejected:** defaulting `Region__c` to `US`, which is what Q40's answer ("unknown
  accounts default to US") reads like at first glance. Rejected because stamping `US` as a *field*
  default makes an account whose region nobody knows indistinguishable from a genuine US account,
  and the fallback then has nothing to detect. The fallback belongs to the calendar-stamping flow
  (`M4-S03`), where a blank Region is the trigger condition.
- **Also rejected:** defaulting `Support_Tier__c` to `Standard`. The contracted tier is a
  contractual fact about the account; a default would silently assert one.
- **Grounded in:** Q40's answer (the fallback is the flow's, per its `answer_shape`: "the before-save
  Flow logic that stamps `Case.BusinessHoursId`, and its fallback when the region is unknowable")
  and Q38's answer (Premier 4 business hours / Standard 1 business day, per contract).
- **Evidence:** the `<description>` on each field file states the reason in place;
  `artefacts/M1-S01/record-type-decision.md` § 6, closing paragraph.


## D-M1S02-01 — The two layouts' field set is a builder DEFAULT assembled from three sources

- **Date:** 2026-09-06
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-06T04-05-00Z`)
- **Kind:** design trade-off, recorded by the owning agent as a default
- **What was recorded:** both layouts carry two sections — `Case Information` (`customLabel` true)
  and `System Information` (`customLabel` false), each `TwoColumnsTopToBottom` with two
  `layoutColumns`. The field set is `Subject`, `Priority`, `Origin`, `CaseNumber` (Readonly),
  `Status`, `OwnerId` on both, plus `Severity__c` on Support only (D-M1S02-02), with `CreatedById`
  and `LastModifiedById` Readonly in `System Information`. Eight fields on Billing, nine on Support
  (`tests/M1-S02/manual-evidence.stdout`, § "fields present on each layout").
- **How the set was assembled** — three sources, none of them a customer field list:
  1. the **structure** of the cited skill's own layout example
     (`record-types-and-page-layouts/references/metadata-examples.md`, "Page layout with two
     sections and one required field") — section shape, `style`, and the three `show*` elements;
  2. **M1-S01's compact layout**, whose field order is `CaseNumber`, `Status`, `Priority`, `Origin`,
     `Severity__c` (workbook row `CWB-OBJ-006`);
  3. **assumption A13** — every field a validation rule attaches its error to must be present on
     both layouts. `M3-S01` declares `Priority_Required_On_Agent_Save` and `Origin_Must_Be_Known`,
     so `Priority` and `Origin` are on both layouts by requirement, not by taste.
- **Alternative rejected:** waiting for a customer-supplied field list. No answered clarification
  supplies one — the builder's own observation is that no clarification matching `layout|Subject|field`
  yields a field set — and blocking the step on a list nobody has been asked for would strand the
  milestone on a question that was never posed. **Also rejected:** copying the skill example's field
  members wholesale, because its members are that example's content rather than this build's.
- **Grounded in:** `skills/admin/record-types-and-page-layouts/references/metadata-examples.md`
  (element inventory and the two-section example); `artefacts/M1-S01/objects/Case/compactLayouts/Case_Intake.compactLayout-meta.xml`;
  `plan.json` → `assumptions[A13]`, whose `steps[]` names `M1-S02` and `M3-S01`.
- **Open item:** confirm the field set with the CRM admin lead before deploy. It is the smallest set
  consistent with A13 and with M1-S01's compact layout, not a confirmed one.
- **Evidence:** `envelopes/M1-S02/2026-09-06T04-05-00Z.json` → `extensions.decision_record[5]`,
  `[6]` and `[7]`, and `process_observations[3]` (ambiguous, medium).

## D-M1S02-02 — `Case.Severity__c` is placed on the Support layout only

- **Date:** 2026-09-06
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-06T04-05-00Z`)
- **Kind:** design trade-off
- **What was recorded:** `Severity__c` appears once, in the `Case Information` section of
  `Case-Case Support Layout`, and nowhere on `Case-Case Billing Layout`. Confirmed on disk by the
  tester: Support carries nine fields including `Severity__c`, Billing carries the same eight
  without it (`tests/M1-S02/manual-evidence.stdout`).
- **Alternative rejected:** placing it on both layouts for symmetry. Rejected because assumption
  **A26** settles that the two record types are genuinely different processes, and the field's own
  requirement is support-side: `requirement.md` L18 — "Severity 1 outages are 24/7 and never
  pause" — is the only source that names a severity at all, and it names an outage. No source
  attaches a severity to a finance query.
- **Grounded in:** `plan.json` → `assumptions[A26]`; `requirement.md` L18; `decisions.md`
  D-M1S01-02, which records that the field ships with the single value `Severity 1`.
- **Live carry-forward for `M3-S01`:** if a Case validation rule attaches its error to
  `Severity__c`, assumption **A13** fails on the Billing layout, because the field is not there to
  display it. Neither rule `M3-S01` declares today
  (`Priority_Required_On_Agent_Save`, `Origin_Must_Be_Known`) targets `Severity__c`, so A13 holds as
  built — a third rule on that field would break it. Raised by `step-tester`
  (`envelopes/M1-S02/2026-09-06T04-45-00Z.md` § "Manual checklist", Half 2) and carried into the
  UAT case compiled in this run.
- **Evidence:** `envelopes/M1-S02/2026-09-06T04-05-00Z.json` → `extensions.decision_record[6]`;
  `artefacts/M1-S02/layouts/Case-Case Support Layout.layout-meta.xml`.

## D-M1S02-03 — Q24 is answered in half: the assignment-rule checkbox is SHOWN, not pre-checked

- **Date:** 2026-09-06
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-06T04-05-00Z`)
- **Kind:** skill gap, recorded per `standards/build-orchestration.md` § 8
- **What was recorded:** both layouts carry
  `<showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>` and nothing else bearing on
  the assignment-rule checkbox. Q24's answer asks for that checkbox **"defaulted on" for the Case
  layouts**, because roughly 20 cases a day are logged by hand (`requirement.md` L7).
- **Alternative rejected:** writing an element that pre-selects the checkbox. The cited skill's
  element inventory carries `showRunAssignmentRulesCheckbox` at
  `record-types-and-page-layouts/references/metadata-examples.md` L198 and documents it at L210 as
  governing **where the checkbox may appear** ("`showRunAssignmentRulesCheckbox` only on Case, Lead,
  and Account"). No element that pre-checks it appears anywhere in that inventory. Inventing one is
  what `agents/metadata-builder/AGENT.md` refuses to do, and what § 8 calls the signal to deepen a
  skill rather than licence to freestyle.
- **Consequence:** half of an **answered blocking** clarification is unbuilt, and the unbuilt half is
  not refutable from the artefacts either — nothing on disk can prove or disprove a default-on state
  that no element expresses. It is visible only in `artefacts/M1-S02/deploy-order.md`, in the two
  M1-S02 envelopes, and here.
- **Decision required at the M1 gate — a human's, not this agent's:** accept the narrowing (the
  checkbox is visible and each hand-logged case is ticked by the agent), or route the remaining half
  to a recorded Setup step. `step-tester` raised the same fork
  (`envelopes/M1-S02/2026-09-06T04-45-00Z.md` § Process Observations, Ambiguous).
- **Skill-gap signal:** deepen `skills/admin/record-types-and-page-layouts` with the `Layout` element
  that selects the assignment-rule checkbox by default, **if one exists** in the Metadata API guide.
  Whether it exists was not established by this build.
- **Evidence:** `envelopes/M1-S02/2026-09-06T04-05-00Z.json` → `dimensions_skipped[0]`
  (`question-coverage`, state `partial`) and `process_observations[2]` (concerning, medium);
  `artefacts/M1-S02/deploy-order.md` § "Elements this step could NOT ground".

## D-M1S02-04 — `AccountId` / `ContactId`, `quickActionList` and `relatedLists` omitted as ungrounded

- **Date:** 2026-09-06
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-06T04-05-00Z`)
- **Kind:** design trade-off — an omission recorded rather than an absence left to be noticed
- **What was recorded:** neither layout carries an `AccountId` or `ContactId` lookup, a
  `quickActionList`, or any `relatedLists` block.
- **Alternative rejected:** adding them because they are conventional on a Case page. Rejected on two
  distinct grounds: (a) no cited source for this step names either lookup as a Case layout field and
  no clarification answer supplies a field list, so they would be the agent's own; (b) the skill
  example's quick-action and related-list members (`LogACall`, `FeedItem.TextPost`,
  `RelatedActivityList`, the `TASK.*` retrieval aliases) are that example's content, and
  `metadata-examples.md` warns that `relatedLists/fields` for standard fields use **retrieval
  aliases** rather than API names — hand-writing them is exactly the failure mode it names.
- **Tension recorded rather than resolved:** the requirement is account-centric — Premier versus
  Standard tiers are read from `Account.Support_Tier__c` (M1-S01, row `CWB-OBJ-009`) and drive
  `M4-S02`'s entitlement selection — so a reviewer who expects Account on the intake page will find
  it absent. Adding it is one `layoutItems` block per layout, and it is a human's call.
- **Grounded in:** `envelopes/M1-S02/2026-09-06T04-05-00Z.json` →
  `extensions.elements_not_grounded_and_not_written[1]` and `[2]`;
  `artefacts/M1-S02/deploy-order.md` § "Elements this step could NOT ground".

## D-M1S02-05 — Rebuild #2: three layout-required Case fields added and `Status` made `behavior=Required`

- **Date:** 2026-09-09
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-09T19-38-37Z`), claimed by `build-step-runner`
  (run `2026-09-09T19-42-25Z`) through the `documented → running` transition
  `standards/build-orchestration.md` § 4 allows for a rebuild
- **Kind:** deviation — the artefacts now carry four things the step's `inputs{}` never asked for,
  and the reason for each is the platform's rather than the requirement's. It is also the closing
  record for a skill gap that every gate in the loop passed.
- **What was recorded:** both Case layouts were re-emitted. `SuppliedEmail`, `Description` and
  `ContactId` were added as `layoutItems` (written `behavior=Edit`), and the `Status` item moved
  from `behavior=Edit` to `behavior=Required`. Support went from nine fields to twelve, Billing from
  eight to eleven (`tests/M1-S02/manual-evidence.stdout`, § "fields present on each layout").
- **Why the step was built a second time:** `reports/MOCK-DEPLOY-M1.md` — `sf project deploy start
  --dry-run` against `sfskills-dev` on 2026-09-05. Run 1 validated 10 of 12 components; both layouts
  failed with `Layout must contain an item for required layout field: ContactId`. Runs 2–5 surfaced
  `Description`, then `SuppliedEmail`, then `Field:Status must be Required` — one message per run,
  because the platform reports one field at a time. Findings **F-09** and **F-10**.
- **Why build #1 missed it, and why that was not a builder error:** four platform rules that no
  cited source carried, and no declared checker encoded. Build #1's own `deploy-order.md` said so in
  as many words — it omitted `ContactId` because "no cited source for this step names either lookup
  as a Case layout field" (D-M1S02-04), and it set no `behavior=Required` on the strength of Q5
  (D-M1S02-01). Q5's answer is right for `Priority`, `Origin` and `Subject` and does not reach
  `Status`, which is a deploy precondition rather than a data-quality control.
- **Source the rebuild rests on — the library, fixed first:**
  `skills/admin/record-types-and-page-layouts` **v1.2.0** (2026-09-09) now carries the deployable
  Case layout in `references/metadata-examples.md` ("Page layout with two sections, the
  layout-required Case fields, and one design-required field"), the `## Layout-required standard
  fields` section behind it, gotchas **#12** and **#13**, and checker rules **RL-REQ-01** (a Case
  layout with no `layoutItems` entry for `ContactId` / `Description` / `SuppliedEmail`) and
  **RL-REQ-02** (a Case layout whose `Status` item is missing or is not `behavior=Required`), both
  ERROR. `standards/build-orchestration.md` § 8 makes deepening the skill the remedy for a knowledge
  gap; this is that remedy landing.
- **Alternative rejected — editing build #1's layouts in place.** Refused rather than deferred:
  `agents/metadata-builder`'s contract forbids it and § 8 makes the skill, not the artefact, the
  place a knowledge gap is closed. The skill was deepened, then the step was re-run against it
  through the ordinary runner path.
- **Alternative rejected — adding the three fields at build #1 time on the builder's own judgment.**
  That is the freestyle the contract forbids, and it would have produced the right file for the
  wrong reason: nothing available to build #1 distinguished a conventional Case field from a
  platform-required one, so the same judgment would equally have added `AccountId`, which the
  platform does **not** require and which is still correctly absent.
- **What this entry supersedes:** the `ContactId` half of **D-M1S02-04** (`AccountId` / `ContactId`
  omitted as ungrounded) — `ContactId` is now present, and not for the requirement's reason but
  because the platform requires it there; and the "no field carries `behavior=Required`" reading in
  **D-M1S02-01**, whose Q5 grounding stands for `Priority`, `Origin` and `Subject` and never covered
  `Status`. The `AccountId` half of D-M1S02-04, and D-M1S02-02 and D-M1S02-03 in full, are unchanged.
- **What did not change:** the field set otherwise, including `Severity__c` on Support only
  (D-M1S02-02); both layouts' `<showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>`;
  the two `layoutSections` and their `style`; and `package.xml`, because the rebuild added items
  inside two existing components rather than a component.
- **Evidence the fix is the org's answer and not the agent's:** the item set and behaviors of both
  rebuilt layouts are identical to the scratch copies that validated 12/12 in mock-deploy run 5,
  committed at `reports/mock-deploy-fixes/`. Mock deploy #2 (2026-09-09) then validated the rebuilt
  artefacts **unmodified**: 12 of 12 components, `checkOnly: true`, 0 errors.
- **Checker evidence, before and after** — same command, verbatim, from the build directory:
  `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py
  --manifest-dir artefacts/M1-S02`. Against build #1's layouts it exits **1** with four ERRORs
  (RL-REQ-01 ×2, RL-REQ-02 ×2); against rebuild #2's it exits **0** with `0 finding(s)`. Both exits
  come from the same command and the same plan — only the skill changed.
- **Still open after this entry, and untouched by it:** Q24's "defaulted on" half remains unwritten
  and uninventable (D-M1S02-03 — v1.2.0 addressed F-09/F-10 and added no element that pre-checks the
  box), and `AccountId` remains absent because no source names it and the platform does not require
  it (D-M1S02-04).
- **Grounded in:** `reports/MOCK-DEPLOY-M1.md` (Findings F-09/F-10; § "Mock deploy #2");
  `artefacts/M1-S02/deploy-order.md` § "Rebuild #2 — why this step was built a second time";
  `envelopes/M1-S02/2026-09-09T19-38-37Z.json` (builder), `…/2026-09-09T19-42-25Z.json` (runner),
  `…/2026-09-09T19-50-27Z.json` (tester); `tests/M1-S02/results.json`;
  `skills/admin/record-types-and-page-layouts` v1.2.0.

## D-M2S01-01 — The consumer list in the custom permission's description is read from `M3-S01`'s declared outputs

- **Date:** 2026-09-06
- **Step:** `M2-S01` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-06T07-00-00Z`)
- **Kind:** design trade-off, recorded by the owning agent as an answer taken from a downstream step
- **What was recorded:** the `<description>` on
  `customPermissions/Bypass_Case_Intake_Validation.customPermission-meta.xml` names its two consumers
  by API name — `Case.Priority_Required_On_Agent_Save` and `Case.Origin_Must_Be_Known` — and says they
  belong to `M3-S01`. The skill's Questions-to-Ask row "Which contexts read it — validation rule,
  formula, Flow, Apex, LWC, component visibility?" was answered "validation rule only" from
  `plan.json` `steps[M3-S01].outputs[]` and its `inputs.note`, not from any clarification answer.
- **Alternative rejected:** leaving the description as an unnamed org-wide off switch ("bypasses Case
  validation"). Rejected because a bypass whose scope is not enumerated cannot be reviewed later —
  a reader cannot tell whether a third rule was added under it, and `custom-permissions` treats the
  named-rules form as the reviewable one.
- **Also rejected:** waiting for a clarification that names the rules. None of the plan's 97 questions
  does; Q56 names the mechanism (a Custom Permission on an integration permission set) and stops there.
- **What this makes fragile, stated rather than hidden:** the description is now a claim about a step
  that has not run. If `M3-S01` renames either rule or adds a third, the description is stale and
  **nothing detects it** — `check_custom_permissions.py` reads the grant, not the description text.
- **Grounded in:** `skills/admin/custom-permissions/references/metadata-examples.md` § 2 (bypass shape,
  description names the consumers); `plan.json` `steps[M3-S01].outputs[]`;
  `envelopes/M2-S01/2026-09-06T07-00-00Z.json` → `extensions.decision_record[1]` and `[5]`.

## D-M2S01-02 — `ApiEnabled` is deliberately NOT granted by this permission set

- **Date:** 2026-09-06
- **Step:** `M2-S01` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-06T07-00-00Z`)
- **Kind:** design trade-off — an omission recorded rather than an absence left to be noticed
- **What was recorded:** `Case_Intake_Integration` carries no `<userPermissions>` block at all, and
  specifically no `ApiEnabled`. The Email-to-Case / Web-to-Case identity plainly needs API access; this
  build does not model where it comes from.
- **Alternative rejected:** granting `ApiEnabled` here because the population is an integration
  identity and it is the obvious thing it needs. Rejected on two independent grounds, either of which
  is sufficient: (a) nothing in `requirement.md` or any answered clarification says whether API access
  arrives through this permission set, another one, or the identity's own base access — so the grant
  would be the agent's own; (b) `ApiEnabled` is in `check_access_model.py`'s `DANGEROUS_PERMISSIONS`
  set, so adding it would fail the step's second declared acceptance test, and it would also break the
  step's `manual` test, which requires this set to grant the custom permission **and nothing else**.
- **Consequence, stated for the gate:** the permission set as built is not sufficient on its own to let
  the integration identity create Cases through the API. A human granting that access does it somewhere
  this build does not model, and no artefact here will show it missing.
- **Grounded in:** `skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py`
  (`DANGEROUS_PERMISSIONS`); `plan.json` `steps[M2-S01].acceptance_tests[1]` and `[4]`;
  `artefacts/M2-S01/deploy-order.md` § "Elements this step could NOT ground";
  `envelopes/M2-S01/2026-09-06T07-00-00Z.json` → `process_observations[4]` (ambiguous, low).

## D-M2S01-03 — The grant is permanent, and needs no step-up activation: two skill DEFAULTS, not answers

- **Date:** 2026-09-06
- **Step:** `M2-S01` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-06T07-00-00Z`)
- **Kind:** design trade-off, recorded by the owning agent as a default
- **What was recorded:** two of the fourteen deduplicated Questions-to-Ask rows for this step were
  answered from the cited skill's own documented default rather than from `plan.json`, because neither
  question exists among the plan's 97:
  1. *"Is the grant permanent, or should it expire?"* → **permanent**. The population is a standing
     automated-process identity, not a data-fix window, which is the case
     `admin/permission-set-expiration` and the skill's `Temp_<Purpose>` route exist for. Note the
     mechanical fact underneath: no expiry is expressible in this build's artefacts anyway —
     an expiration rides on `PermissionSetAssignment`, which is record data.
  2. *"Does any permission need step-up activation?"* → **no**;
     `<hasActivationRequired>false</hasActivationRequired>`, which is what the cited skill's § 1 and
     § 2 examples carry "on purpose" and what its § 3 note requires of anything destined for a PSG —
     relevant because `M2-S02` owns the PSGs.
- **Alternative rejected:** blocking the step until the two questions are asked. Rejected because
  neither is a *gap in a skill* — both skills document a default — and blocking a step on a question
  nobody was asked strands a milestone. Recorded as a default so the gate can overturn either one.
- **Why this is filed as one entry and not two:** they are the same dimension in the builder's own
  record — `dimensions_skipped[0]`, `question-coverage`, state `partial`, `confidence_impact: LOW` —
  and they are the reason that run's confidence is MEDIUM rather than HIGH.
- **Grounded in:** `skills/admin/custom-permissions` Questions-to-Ask (expiry row);
  `skills/admin/permission-set-architecture/references/metadata-examples.md` § 1 and its § 3 note;
  `envelopes/M2-S01/2026-09-06T07-00-00Z.json` → `dimensions_skipped[0]`,
  `extensions.decision_record[6]` and `[11]`.

## D-M2S01-04 — The permission set keeps the name the plan declared, against the template's form

- **Date:** 2026-09-06
- **Step:** `M2-S01` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-06T07-00-00Z`)
- **Kind:** deviation from a template, recorded rather than corrected
- **What was recorded:** the permission set is `Case_Intake_Integration`.
  `templates/admin/permission-set-patterns.md` gives integration bundles the form
  `Integration_<System>_Bundle` and feature sets the form `Feat_<Feature>`, so the built name matches
  neither.
- **Alternative rejected:** renaming it to `Integration_Case_Intake_Bundle` to match the template.
  Rejected because `plan.json` declares the output path
  `artefacts/M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml`, and a declared
  output path is not the owning agent's to rename: `standards/build-orchestration.md` § 5 makes
  `check-outputs` confirm exactly the paths the plan declared, so a rename would have left the step
  unable to reach `built`.
- **The load-bearing detail:** the step's `templates[]` is **empty**. No template was cited on this
  step, so there was no cited authority to weigh the declared path against — the divergence is visible
  only because the builder went looking. Two agents have now raised it and neither could adjudicate it
  (`metadata-builder` `process_observations[3]`, `step-tester` `process_observations` → ambiguous).
- **Decision required at the M2 gate — a human's, not this agent's:** accept `Case_Intake_Integration`
  as the build's name, or re-plan the output path at v6 and let the template form win. Deciding it now
  is cheap; deciding it after `M2-S02` and `M2-S03` have added five more permission sets in whatever
  form they declare is a convention argument across eight files.
- **Grounded in:** `templates/admin/permission-set-patterns.md`; `plan.json`
  `steps[M2-S01].outputs[1]` and `steps[M2-S01].templates` (empty);
  `artefacts/M2-S01/deploy-order.md` § "Elements this step could NOT ground";
  `envelopes/M2-S01/2026-09-06T07-00-00Z.json` → `process_observations[3]`.

## D-M2S01-05 — Correction of record: `deploy-order.md`'s "reports an INFO" sentence is false

- **Date:** 2026-09-06
- **Step:** `M2-S01` (`access`)
- **Agent:** raised by `step-tester` (run `2026-09-06T07-30-00Z`) against
  `metadata-builder`'s `artefacts/M2-S01/deploy-order.md`
- **Kind:** deviation — a built artefact's own text disagrees with the run it describes
- **What was recorded:** `artefacts/M2-S01/deploy-order.md` states, under "`check_custom_permissions.py`
  cannot see that dependency at this scope", that with no validation rule in the scanned tree "the
  checker reports `Consumers: 0` and an INFO, and exits 0". The first and third clauses are right; the
  middle one is false. The run printed `Summary: 0 error(s), 0 warning(s), 0 info.`
  (`tests/M2-S01/check_custom_permissions.stdout.txt`).
- **Why no INFO fires:** `check_custom_permissions.py` L301–308 raises its INFO for a permission that is
  **defined but ungranted**. `Bypass_Case_Intake_Validation` **is** granted — by
  `Case_Intake_Integration` — so the condition is not met. A zero-consumer permission is not the same
  thing as an ungranted one, and the sentence conflates them.
- **Alternative rejected:** editing `deploy-order.md` to fix the sentence. Refused, not deferred:
  `agents/build-doc-keeper/AGENT.md` — "Does not build, edit, move or delete artefacts. It opens them
  read-only for the `target_value` cell". The correction is recorded here and in workbook row
  `CWB-OTHER-007`, and the artefact is left byte-identical.
- **What is NOT wrong:** the plan's own acceptance-test description states the counterfactual correctly
  ("removing the grant entirely still exits 0 with an INFO" — that is the ungranted case, and it is
  accurate). Only the `deploy-order.md` restatement drifts. The conclusion both documents draw — that
  exit 0 says nothing about the consumer side — stands on its own and is unaffected.
- **Remedy owner:** `metadata-builder`, on any re-run of this step. Until then this entry is the record.
- **Grounded in:** `tests/M2-S01/check_custom_permissions.stdout.txt`;
  `skills/admin/custom-permissions/scripts/check_custom_permissions.py` L301–308;
  `envelopes/M2-S01/2026-09-06T07-30-00Z.json` → `process_observations[3]` (concerning, low);
  `plan.json` `steps[M2-S01].acceptance_tests[0].description`.

## D-M1S01-05 — Rebuild #2: every business-process `fullName` is now its file stem

- **Date:** 2026-09-09
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-09T19-42-00Z`), claimed by `build-step-runner`
  (`2026-09-09T19-45-00Z`) and re-tested by `step-tester` (`2026-09-09T19-52-47Z`)
- **Kind:** deviation — the step was rebuilt away from what rebuild #1 produced, for a reason that
  did not exist when rebuild #1 ran
- **Why the rebuild happened:** `reports/MOCK-DEPLOY-M1.md` finding **F-11** (HIGH). A real
  `sf project deploy start --source-dir force-app --dry-run` against `sfskills-dev` rejected this
  step's business processes: the CLI derives the `package.xml` member from the **file stem**
  (`Support_Process`), the file's `<fullName>` said `Support Process`, and the member therefore
  matched nothing —
  `An object 'Case.Support_Process' of type BusinessProcess was named in package.xml, but was not found in zipped directory`.
  Every declared gate in the loop had been green on those artefacts.
- **What changed** — six files, and nothing else:

  | File | Change |
  |---|---|
  | `objects/Case/businessProcesses/Support_Process.businessProcess-meta.xml` | `<fullName>` `Support Process` → `Support_Process` |
  | `objects/Case/businessProcesses/Billing_Process.businessProcess-meta.xml` | `<fullName>` `Billing Process` → `Billing_Process` |
  | `objects/Case/recordTypes/Support.recordType-meta.xml` | `<businessProcess>` → `Support_Process` (bare stem) |
  | `objects/Case/recordTypes/Billing.recordType-meta.xml` | `<businessProcess>` → `Billing_Process` |
  | `package.xml` | `BusinessProcess` members → `Case.Support_Process`, `Case.Billing_Process` |
  | `deploy-order.md` | the two member-name cells, plus a **Rebuild history** section |

  The other seven declared outputs — the Private OWD on `Case.object-meta.xml`, the `CaseOrigin`
  value set, the compact layout, the three fields and `record-type-decision.md` — are byte-identical
  to rebuild #1 and still carry their 2026-09-05 mtimes.
- **Alternative rejected:** renaming the *files* to `Support Process.businessProcess-meta.xml` so the
  stem matched the spaced `fullName` instead. Rejected because `plan.json` `steps[M1-S01].outputs[]`
  declares the underscore paths, so `check-outputs` would have failed the step, and because a file
  name carrying a space is not what the DX source-format convention produces. F-11 itself states the
  direction: "the planner must pick one at v6 (**stem form, since it deploys**)."
- **Also rejected:** leaving the artefacts alone and recording F-11 as a deploy-time caveat.
  Rejected because the finding is not a caveat — the component does not deploy at all.
- **Grounded in:** `skills/admin/case-management-setup` **v1.2.0**,
  `references/metadata-examples.md` § 2.1 ("File stem = fullName"), which states the rule, quotes the
  same CLI error, and records the dry run it was verified by; and the org validation itself,
  `reports/MOCK-DEPLOY-M1.md` § "Mock deploy #2" — the rebuilt artefacts copied **without any edits**
  into a source tree validated **12/12 components, `checkOnly: true`, 0 errors**.
- **Now enforced rather than remembered:** the same skill's checker carries **CMS-STEM-01** (a
  decomposed `*.businessProcess-meta.xml` / `*.recordType-meta.xml` stem must equal its `<fullName>`,
  and no `<fullName>` may hold a space) and **CMS-STEM-02** (a record type's `<businessProcess>` must
  name an existing process file stem). Against the pre-rebuild copy still committed at
  `examples/builds/case-onboarding/artefacts/M1-S01` the checker emits **4 `ERROR:` lines** and exits
  1; against these artefacts it exits 0. The tester ran that negative control deliberately, so the
  green is earned rather than fail-open (`envelopes/M1-S01/2026-09-09T19-52-47Z.md` § "Observation
  only").
- **What it supersedes:** **D-M1S01-03**, on one row of its three-spellings table only. The
  `fullName` row — "inside the file, and inside each `RecordType`: `Support Process`, bare, with a
  space" — is no longer true; it now reads `Support_Process`. The manifest row still stands:
  `package.xml` names the member object-qualified (`Case.Support_Process`) and a file stem cannot
  carry the dot, so the two index keys `check_rtm.py` builds still differ and the same three orphan
  WARNs persist. D-M1S01-03 is not rewritten — this entry names it, per the append-only rule.
- **Open item for the planner, unclosed and not closable here:** `plan.json`
  `steps[M1-S01].inputs.business_processes` still reads `["Support Process", "Billing Process"]`
  while `outputs[]`, the six rebuilt files and the manifest are all stem form. Nothing downstream
  reads that string, so no test can fail on it. It is a **v6 planner item** —
  `standards/build-orchestration.md` § 2 gives `build_plan.py` sole authority over plan state and
  `agents/build-doc-keeper/AGENT.md` forbids this agent touching `plan.json` beyond its own status
  transition. Filed below as **O-M1S01-01**.
- **What the gate should see:** milestone **M1 is already `accepted`**, and the acceptance report and
  gate notes behind that approval describe artefacts that have since changed. `milestone-verifier`
  has to re-run across every step in M1, not just this one
  (`envelopes/M1-S01/2026-09-09T19-45-00Z.md` § Process observations, third Concerning bullet).
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § "Rebuild history";
  `envelopes/M1-S01/2026-09-09T19-42-00Z.json` (builder), `2026-09-09T19-45-00Z.json` (runner),
  `2026-09-09T19-52-47Z.json` (tester); `tests/M1-S01/results.json` (`"passed": true`, 6 ran,
  0 failed, 2 manual).

---

# Open items for the planner — plan-verifier v5 non-blocking warnings

Recorded here, not fixed here: `standards/build-orchestration.md` § 2 makes `build_plan.py` the
single writer of plan state and `agents/build-doc-keeper/AGENT.md` forbids this agent touching
`plan.json` beyond its own status transition and run record. These are step-note corrections a
re-plan makes, and both concern steps that are not yet built.

Source: `envelopes/verification/2026-09-06T02-10-00Z.md`, plan v5, grounding lens. Both warnings are
non-blocking: the plan is `approved` and the conclusions the notes support survive; it is the stated
reasons that are false.

## W01 — the "no fenced XML" claim on `M3-S04` and `M5-S05` is factually stale

- **Date:** 2026-09-06 · **Recorded by:** `build-doc-keeper` from the plan verifier's v5 envelope
- Both step notes say `skills/admin/case-management-setup` "carries no fenced XML anywhere under
  `references/`, `SKILL.md` or `templates/`", and use that to justify leaving the skill out of
  `skills[]`. The verifier counted **6** fenced XML blocks in that skill's
  `references/metadata-examples.md`, and `M3-S03`'s note *in the same plan* says so.
- **Live consequence on `M5-S05`:** its `acceptance_tests[5]` grades the manifest against that
  file's § 5 no-wildcard-on-feature-settings rule, which the one cited skill
  (`admin/change-management-and-deployment`) does not document. The verifier reproduced
  `check_deployment_manifest.py` scoring a manifest with `<members>*</members>` under `Settings`
  identically to the correct one (`score 95`, one SharingRules WARN, exit 0), so nothing but the
  manual tick catches a wildcard that will not deploy.
- **Verifier's remedy:** delete both sentences; on `M5-S05` also add `admin/case-management-setup`
  to `skills[]`. `M3-S04`'s real reason — the deployable rule shapes come from `admin/assignment-rules`
  — stands on its own.

## W02 — the "`check_queues.py` does not recurse" claim on `M3-S05` and `M5-S01` is factually stale

- **Date:** 2026-09-06 · **Recorded by:** `build-doc-keeper` from the plan verifier's v5 envelope
- Both notes state the checker does not recurse, `M3-S05` adding that at `artefacts/` it "finds no
  queue files at all". The verifier read `check_queues.py:94` —
  `candidates.extend(sorted(p for p in base.rglob(dir_name) if p.is_dir()))` — and ran it at
  `--manifest-dir artefacts`: **`Queues found (3)`** plus three public groups, exit 0. `M2-S04`'s
  own note in this plan states the correct behaviour.
- Both conclusions survive on other grounds: the checker lints queue and group files and resolves no
  reference from a `queueRoutingConfig` or a `listView` to them, so it cannot carry either assertion
  at any scope. It is the stated reason that is wrong.
- **Verifier's remedy:** reword both notes to that real reason.

## W03 — assumption A1 does not list `M1-S01`

Recorded in `traceability.md` § "Assumption linkage — A1 now reaches M1-S01", where row `REQ-010`
carries the Private Case OWD against deferred Q13. The planner's fix at v6 is to add `M1-S01` to
`A1.steps[]` and record Q13 in `M1-S01.inputs{}`. Left here as a pointer so the two documents do not
carry two versions of the same open item.

---

# Open items for the planner — raised by the M1-S02 build and test runs

The section above collects `plan-verifier` v5 warnings. The two below were raised by
`metadata-builder` and `step-tester` while `M1-S02` was built and tested, and are recorded here for
the same reason: both are plan-file text or plan-file declarations, and
`standards/build-orchestration.md` § 2 gives `set-plan` sole authority over them. Neither blocks the
step — `M1-S02` passed every executable test it declares.

**Amended 2026-09-09 by the rebuild #2 documentation pass.** A third item, **O-M1S02-03**, is added
below, and **O-M1S02-01 is now moot** — the checker prints exactly the `0 finding(s)` its plan
description predicted, because both layouts now mark a field `behavior=Required`. The entry is left
standing rather than deleted: it records why the description was false for three days, and the
re-plan that closes it should close it as observed-correct rather than as reworded.

## O-M1S02-01 — the checker test's `description` predicting `0 finding(s)` is stale

- **Date:** 2026-09-06 · **Recorded by:** `build-doc-keeper` from the M1-S02 builder and tester
  envelopes, re-run in this documentation pass
- `plan.json` → `steps[M1-S02].acceptance_tests[0].description` states that against a fixture holding
  exactly the two layouts, the checker prints
  `Scanned 2 metadata file(s): 0 record type(s), 2 layout(s); 0 finding(s)`.
- The real run against the real artefacts prints **`2 finding(s) detected.`** at `score 100`, both
  `INFO`: `layout 'Case-Case Billing Layout' marks no field behavior=Required` and the same for
  the Support layout (`tests/M1-S02/check_record_type_layouts.stdout`).
- **The declared `expected` still holds** — `exit 0`, because `check_record_type_layouts.py`
  promotes `INFO` to a non-zero exit only under `--strict`, which the plan does not declare. It is
  the sentence supporting the expectation that is false, not the expectation.
- The two findings are check 4 firing exactly as **Q5's answer requires**: `Priority` and `Origin`
  are enforced at field or validation-rule level rather than by layout, because Email-to-Case and
  Web-to-Case create through the API where layout `Required` does not bind
  (`record-types-and-page-layouts/references/gotchas.md` #11). Silencing them would mean adding a
  layout-level `Required` that Q5 rules out, so the artefacts are correct and the description is
  what needs the edit.
- **Remedy at v6:** reword the description to `2 finding(s), both INFO — check 4, which Q5's answer
  predicts`. Raised by `metadata-builder` (`process_observations[1]`, concerning/low) and confirmed
  independently by `step-tester` (Process Observations → Concerning, first bullet).

## O-M1S02-02 — `deploy-order.md` is undeclared in `outputs[]` on BOTH M1 steps

- **Date:** 2026-09-06 · **Recorded by:** `build-doc-keeper`
- `agents/metadata-builder/AGENT.md` Step 7 writes `artefacts/<step-id>/deploy-order.md` on every
  run, and neither `M1-S01` nor `M1-S02` declares it in `outputs[]`. The consequence is identical on
  both: `check-outputs` never confirms the file (it only ever confirms paths the plan declared), and
  the always-on `manifest` test excludes it by name as "not a source-format metadata file". Two of
  two M1 steps, so this is a plan-wide pattern rather than a one-step slip.
- M1-S01's instance is already recorded as a per-row gap in workbook row `CWB-OTHER-002`
  ("Verified by: **nothing**"); M1-S02's is recorded in `CWB-OTHER-005` in the same words. This entry
  is the pattern the two rows share, filed once for the planner rather than a third time per row.
- **Why it matters beyond the two rows:** `agents/build-doc-keeper/AGENT.md` Step 10 builds
  `M5-S04`'s **build-wide deploy order** from exactly these per-step `deploy-order.md` files. The
  compile run therefore depends on a set of files that no gate in the loop confirms exists.
- **Remedy at v6:** declare `artefacts/<step-id>/deploy-order.md` in `outputs[]` on every
  `metadata-builder`-owned step. Raised by `metadata-builder` on both steps
  (`extensions.artefacts[…].declared: false`) and by `step-tester` on M1-S02 (Process Observations →
  Ambiguous, third bullet).

## O-M1S02-03 — F-09 and F-10 are closed at the skill; M1's report and gate notes predate the rebuild

- **Date:** 2026-09-09 · **Recorded by:** `build-doc-keeper`, from the three rebuild #2 envelopes and
  `reports/MOCK-DEPLOY-M1.md` § "Mock deploy #2"
- **F-09 and F-10 are closed, and closed at the source.** Both were HIGH findings from the M1 mock
  deploy: a Case layout must carry `ContactId`, `Description` and `SuppliedEmail`, and `Status` must
  be `behavior=Required`. The remedy landed in the library —
  `skills/admin/record-types-and-page-layouts` v1.2.0 carries the deployable Case layout example, the
  `## Layout-required standard fields` section, gotchas #12 and #13, and ERROR rules **RL-REQ-01** and
  **RL-REQ-02**. The same declared checker command now exits **1** against build #1's layouts and **0**
  against rebuild #2's, and mock deploy #2 validated the rebuilt artefacts **unmodified** at 12 of 12
  components. The build record of the change is `decisions.md` **D-M1S02-05**. Nothing is left open on
  either finding at the artefact or the skill.
- **What is not closed is the paperwork above the step.** `milestone:M1` was approved on 2026-09-06
  against build #1's layouts. `reports/MILESTONE-M1-REPORT.md` describes those layouts, its go/no-go
  section rests on them, and the `milestone:M1` gate note records a human's decision taken on them.
  Both M1 steps have since been rebuilt — `M1-S02` for F-09/F-10 and `M1-S01` for F-11 — so the
  accepted milestone no longer describes the artefacts on disk.
- **Who fixes what, and who may not.** The gate note is a written record of a human's decision and is
  **not** rewritable by any agent, exactly as `O-M2S01-01` concluded for the `step:M2-S01` note. The
  milestone report is `milestone-verifier`'s and no other writer touches it
  (`standards/build-orchestration.md` § 2). The remedy is therefore a **re-verification** of M1 once
  `M1-S01` has been documented, producing a report that describes the rebuilt artefacts and states
  which parts of the 2026-09-06 acceptance still stand. This documentation pass can record the
  divergence; it cannot resolve it.
- **Why it is filed for the planner and not only for the verifier.** Re-verifying an `accepted`
  milestone is not a transition the step status machine covers, and `gate milestone:M1` is already
  `approved` — so whether M1 is re-verified in place, re-gated, or accepted with a recorded delta is a
  plan-level decision. The two conditions that make it safe to take are both now true: F-09/F-10 are
  closed at the skill, and M1-S02 is documented against rebuild #2.
- **Sequencing, so the re-verification is not run twice.** `M1-S01` was at `tested` when this entry
  was written, with its own documentation pass in flight in a second session — its two
  `BusinessProcess` traceability cells were amended to the post-F-11 stem form during this run
  (`traceability.md` § "Linter result — after the M1-S02 rebuild"). Let that pass reach `documented`,
  then run `milestone-verifier` on M1 **once**. Two sessions were writing this build directory
  concurrently, which is itself worth knowing before anyone reads a single linter figure as the
  state of the build.

---

# Open items for the planner — raised by the M2-S01 documentation run

Same standing as the two sections above and for the same reason: these are plan-file text and
plan-file records, and `standards/build-orchestration.md` § 2 gives `build_plan.py` sole authority over
them. Neither blocks the step — `M2-S01` passed every executable test it declares.

## O-M2S01-01 — F-01's remedy names `M2-S01`, but `layoutAssignments` is `M2-S03`'s in plan v5

- **Date:** 2026-09-06 · **Recorded by:** `build-doc-keeper`, from the M2-S01 builder envelope and
  reproduced against the plan in this pass
- `reports/MILESTONE-M1-REPORT.md` finding **F-01** — the HIGH finding the M1 gate was really for —
  explains that every record-type-to-layout check in `check_record_type_layouts.py` reads from
  `layoutAssignments`, that `collect()` populates them only from `Profile` and `PermissionSet` roots,
  and then says: "`layoutAssignments` lives only on `Profile`, which is **`M2-S01`**'s." The go/no-go
  list at § 11 repeats the pointer.
- **In plan version 5 it is not.** `M2-S01` declares four outputs — one `CustomPermission`, one
  `PermissionSet`, `package.xml`, `deploy-order.md` — and no `Profile`. The profiles are **`M2-S03`**,
  "Minimal base profiles carrying only default app, default record type and layout assignment", whose
  declared outputs are `artefacts/M2-S03/profiles/Acme Support Tier 1.profile-meta.xml`,
  `.../Acme Support Tier 2.profile-meta.xml` and `.../Acme Billing.profile-meta.xml`.
- **The stale pointer has been copied forward twice more, into places a re-plan does not reach.** Both
  are gate records in `plan.json.human_gates[]`, rendered into `PLAN.md`: the `milestone:M1` approval
  note reads "F-01 (layout↔record-type assertion needs Profile layoutAssignments — **M2-S01**) carried
  to M2", and the `step:M2-S01` gate note opens "**Profiles step.** Approved for the dry run so F-01
  … can be closed at M2 scope." The step that gate approves builds no profile, so the reason recorded
  for approving it is not a reason about that step.
- **Nothing is broken by this.** `M2-S01` built what plan v5 asked for, and `M2-S03` will build the
  profiles. The defect is navigational: a reader closing F-01 goes to the wrong step, finds no
  `layoutAssignments`, and has no way to tell whether the remedy was dropped or renumbered. That is the
  same class of defect as F-01 itself — a document asserting a check that was not where it said.
- **Remedy at v6:** repoint F-01's remedy and its § 11 go/no-go line to `M2-S03`. The two gate notes are
  written records of a human's decision and are **not** rewritable by anyone; the correction belongs in
  the M2 milestone report, which should state that the `step:M2-S01` note describes `M2-S03`'s content.
- **Already partly mitigated in the artefacts:** `artefacts/M2-S01/deploy-order.md` carries a whole
  section — "Record types and page layouts: what this step does NOT carry" — that names `M2-S03`, gives
  the exact `Case.Support` / `Case.Billing` and `Case-Case Support Layout` / `Case-Case Billing Layout`
  member forms the profiles must reuse, and states that `check_record_type_layouts.py` still has zero
  `layoutAssignments` to resolve anywhere under `artefacts/` until `M2-S03` deploys. The builder wrote
  that section for exactly this reason.

---

# Open items for the planner — raised by the M1-S01 rebuild #2 documentation run

Same standing as the three sections above: plan-file text and plan-file declarations, which
`standards/build-orchestration.md` § 2 puts under `build_plan.py`'s sole authority. None of the three
blocks the step — `M1-S01` passed every executable test it declares, twice.

## F-11 is closed at the skill; its planner half is not

**Closed.** The rule F-11 discovered is library content now, not a report footnote:
`skills/admin/case-management-setup` **v1.2.0** states it at `references/metadata-examples.md` § 2.1
and enforces it as **CMS-STEM-01 / CMS-STEM-02**, which fire on the pre-rebuild artefacts (4 `ERROR:`
lines, exit 1) and are silent on the rebuilt ones. The artefacts themselves are fixed and validated:
`reports/MOCK-DEPLOY-M1.md` § "Mock deploy #2" records 12/12 components validating with **no edits**
applied to the build's own files. That is the loop working as `standards/build-orchestration.md` § 8
describes — a defect found by reality became a checker, and the rebuild was gated by the checker.

**Not closed:** the three items below.

## O-M1S01-01 — `steps[M1-S01].inputs.business_processes` still holds the spaced form

- **Date:** 2026-09-09 · **Recorded by:** `build-doc-keeper` from the builder, runner and tester
  envelopes of rebuild #2, all three of which raise it independently
- `inputs.business_processes` reads `["Support Process", "Billing Process"]`. `outputs[]` has always
  declared the stem-form paths, and since rebuild #2 the files, the `<fullName>` values, the record
  types' references and the manifest members are all stem form too. The divergence is now between a
  step's inputs and its own outputs.
- **Nothing detects it.** No test reads that string, so the step is green with it wrong; it is
  documentation of an earlier intent rather than a value anything consumes.
- **Remedy at v6:** set `inputs.business_processes` to `["Support_Process", "Billing_Process"]`,
  which is the direction F-11 itself names ("stem form, since it deploys"). Raised by
  `metadata-builder` (Process observations → Ambiguous), `build-step-runner` (same), `step-tester`
  (same) and `artefacts/M1-S01/deploy-order.md` § "Rebuild history" → "Open item for the planner".
- **A second edit in the same file, while it is open:** the step's `inputs.note` (B01) still says
  "members object-qualified (`Case.Support Process`)". The object-qualification half is right; the
  spelling is not.

## O-M1S01-02 — manual test 1's counter-example is stale after rebuild #2

- **Date:** 2026-09-09 · **Recorded by:** `build-doc-keeper` from `step-tester`
  (`envelopes/M1-S01/2026-09-09T19-52-47Z.md` § "Manual checklist", caveat under item 1, and
  Process Observations → Ambiguous)
- `plan.json` `steps[M1-S01].acceptance_tests[6].description` reads: "…each record type's
  `<businessProcess>` carries the BARE process name **(not `Case.Support Process`)**…". The same
  string is copied into `tests/M1-S01/results.json` `skipped_manual[0]`, which is where a tester at
  the gate will actually read it.
- **The assertion still holds; the parenthetical does not.** It was written to exclude one wrong
  shape — object-qualified where bare is required. After rebuild #2 the string it names is wrong on
  **two** counts at once (object-qualified *and* spaced), and the shape it was meant to exclude —
  `Case.Support_Process` inside a record type — is no longer the string it prints. A tester who
  applies it literally is checking for something nobody would now write.
- **Why it matters more than the wording:** `TC-M1S01-01` was ticked at the **M1 gate against
  rebuild #1**, and the M1 milestone is already `accepted`. The gate record therefore attests to a
  reading of a test whose text no longer matches the artefacts it was ticked over.
- **Remedy at v6:** reword the counter-example to `(not Case.Support_Process)` — the bare-vs-qualified
  distinction it was written for, spelled the way the components are now spelled. `results.json` is a
  test artefact and regenerates from the plan on the next test run, so the plan is the only edit.
  Neither this agent nor the tester edits acceptance-test descriptions.

## O-M1S01-03 — the `CompactLayout` member form has still never been read by a deploy

- **Date:** 2026-09-09 · **Recorded by:** `build-doc-keeper` from `step-tester`
  (`envelopes/M1-S01/2026-09-09T19-52-47Z.md` § Process Observations → Concerning, first bullet)
- `artefacts/M1-S01/package.xml` declares the bare member `Case_Intake` under `CompactLayout`. That
  form comes from `skills/admin/list-views-and-compact-layouts/references/metadata-examples.md`,
  whose "Where the files live" table says "compact layout name" in prose while its own sample manifest
  uses `*` — so no non-wildcard example existed to copy. `artefacts/M1-S01/deploy-order.md` calls it
  "the thinnest grounding in this manifest" in its own words.
- **Neither mock deploy tested it.** Both runs used `--source-dir force-app --dry-run`, so the CLI
  derived the components from the source tree and never opened this `package.xml` — and what it
  derived was the **object-qualified** `CompactLayout Case.Case_Intake`
  (`reports/MOCK-DEPLOY-M1.md` § "Mock deploy #2", component list). The build's manifest says one
  thing, the only deploy that has ever run said another, and nothing has compared them.
- **This is the same shape as F-11 and one type over.** F-11 was a member the CLI could not resolve,
  found only by a real validation; the always-on `manifest` test cannot catch either, because it
  checks the manifest against the files in the build and both sides here agree with each other.
- **Remedy:** one `sf project deploy validate --manifest artefacts/M1-S01/package.xml` against a
  sandbox — the command `deploy-order.md` already prints for the human — or a retrieve that shows the
  member form the org emits. Not a plan edit and not this agent's to run: no agent in this loop
  contacts an org. Until then the member form is unverified and the row that carries it
  (`CWB-OTHER-001`) says so.
- **CLOSED — 2026-09-12, by D-M1S01-06.** A manifest-driven mock deploy (not `--source-dir`) finally
  read this `package.xml` and confirmed the ambiguity the hard way: `reports/MOCK-DEPLOY-M1.md`
  § "Mock deploy #3" — finding **F-13** — rejected the bare `Case_Intake` member. Rebuild #3 fixed it
  to the object-qualified `Case.Case_Intake`, `admin/list-views-and-compact-layouts` v1.2.0 now
  enforces the form as a checker rule, and § "Mock deploy #4" validates the corrected manifest
  directly: 12 components, 0 errors. See D-M1S01-06 below for the full record.

---

## D-M1S01-06 — Rebuild #3: the `CompactLayout` manifest member is now object-qualified

- **Date:** 2026-09-12
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-15-00Z`), claimed by `build-step-runner`
  (`2026-09-12T00:11:57Z`) and re-tested by `step-tester` (`2026-09-12T00-21-00Z`)
- **Kind:** deviation — the step was rebuilt a third time, for a finding **O-M1S01-03** had already
  named as unresolved and F-11's own shape had already anticipated ("the same shape as F-11, one
  metadata type over")
- **Why the rebuild happened:** `reports/MOCK-DEPLOY-M1.md` finding **F-13** (confirmed, not
  theoretical). Unlike the two prior mock deploys, "Mock deploy #3" ran manifest-driven
  (`sf project deploy start --manifest reports/MILESTONE-M1-package.xml --dry-run`) instead of
  `--source-dir`, and the CLI rejected the merged M1 manifest: "An object 'Case_Intake' of type
  CompactLayout was named in package.xml, but was not found in zipped directory." The manifest
  carried the bare member `Case_Intake` under `<name>CompactLayout</name>` —
  `admin/list-views-and-compact-layouts`'s prescribed form at the time this step was first built —
  while the CLI resolves compact layouts as object-qualified `Case.Case_Intake`, exactly what mock
  deploy #2's `--source-dir` run had silently derived instead of reading. `--source-dir` never
  surfaces this class of defect, because it derives the member list from the files on disk rather
  than from `package.xml`; a manifest-driven deploy is what finally read the file this build actually
  ships.
- **What changed** — one file, one member string, and nothing else:

  | File | Change |
  |---|---|
  | `package.xml` | `CompactLayout` member `Case_Intake` → `Case.Case_Intake` |
  | `deploy-order.md` | the **Rebuild history** § "Rebuild #3" entry recording this change |

  The other eleven declared outputs — `Case.object-meta.xml`, the `CaseOrigin` value set, both
  `businessProcess-meta.xml` files, both `recordType-meta.xml` files, the compact layout file itself,
  the three `CustomField` files and `record-type-decision.md` — are byte-identical to rebuild #2
  (verified by SHA-256 before/after this pass, per the builder's own run record;
  `.sfskills/` is gitignored so a `git diff` cannot be used as the check).
- **Alternative rejected:** treating F-13 as a deploy-time caveat rather than a defect. Rejected for
  the same reason F-11 was: the finding is not a caveat, the component does not resolve under a
  manifest-driven deploy at all, and `reports/MOCK-DEPLOY-M1.md` § "Mock deploy #3" reproduces the
  CLI's own rejection rather than a theoretical read of the skill's prose.
- **Grounded in:** `skills/admin/list-views-and-compact-layouts` **v1.2.0**,
  `references/gotchas.md` ("Manifest member form (CL-MEM-01 .. CL-MEM-02)"), which states the rule
  the skill's prior version left ambiguous (its "Where the files live" table said "compact layout
  name" while its own sample manifest used only `*`, so no non-wildcard example existed to copy —
  the exact gap `O-M1S01-03` and `artefacts/M1-S01/deploy-order.md` both named as "the thinnest
  grounding in this manifest"); and the org validation itself, `reports/MOCK-DEPLOY-M1.md`
  § "Mock deploy #4" — the rebuilt manifest read directly by the CLI (`--manifest`, not
  `--source-dir`) validated **12 components, 0 errors, `checkOnly: true`**.
- **Now enforced rather than remembered:** the same skill's checker carries **CL-MEM-01** (ERROR — a
  bare `CompactLayout` / `ListView` member whose file exists in the scanned tree must be
  object-qualified) and **CL-MEM-02** (WARN — an undeclared compact layout file). Against this step's
  `package.xml` before the rebuild, `check_list_views_and_compact_layouts.py` printed one
  `ERROR CL-MEM-01` finding and exited 1; against the rebuilt manifest it exits 0, and the step's
  `step-tester` run recorded "CL-MEM-01 clean" as new coverage the previous test run did not have
  (`envelopes/M1-S01/2026-09-12T00-21-00Z.md`).
- **What it closes:** **O-M1S01-03**, in full — the member form is no longer "unresolved in both
  directions": a manifest-driven deploy has now read it, and it matches the object-qualified form
  the source-format deploy always derived. The workbook rows that named the ambiguity
  (`CWB-OTHER-001`, `CWB-OBJ-006`) and the traceability row that named the member by its bare form
  (`REQ-006`) are amended in this same documentation pass.
- **What it does not touch:** `D-M1S01-03`'s standing `BusinessProcess` orphan explanation and
  `O-M1S01-01` / `O-M1S01-02` (the plan-file staleness rebuild #2 opened) are unrelated findings on
  unrelated components; neither is affected by this rebuild.
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § "Rebuild history" → "Rebuild #3";
  `artefacts/M1-S01/package.xml`; `reports/MOCK-DEPLOY-M1.md` §§ "Mock deploy #3" and "Mock deploy
  #4"; `envelopes/M1-S01/2026-09-12T00-15-00Z.json` (builder), `running.json` (runner claim),
  `2026-09-12T00-21-00Z.json` (tester); `tests/M1-S01/results.json` (`"passed": true`, 6 ran, 0
  failed, 2 manual).

---

## D-M2S02-01 — CRUD levels per object were read from `requirement.md`, not invented

- **Date:** 2026-09-11
- **Step:** `M2-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-05-00Z`)
- **Kind:** design trade-off, recorded by the owning agent as a source substitution
- **What was recorded:** `Case_Agent_Core`'s five `objectPermissions` blocks carry `allowCreate` /
  `allowDelete` / `allowEdit` / `allowRead` at: Case create/read/edit, no delete; Account, Contact,
  Entitlement read only; EmailMessage create + read.
- **Alternative rejected:** blocking the step until a clarification names the CRUD level per
  object. Rejected because Q9 already answers the **object list** ("Case, Account, Contact,
  EmailMessage, Entitlement, plus the Case record types, layouts and the Service app") and no
  clarification asks the level question separately — the deduplicated Questions-to-Ask row "Which
  objects does this capability touch, and at what CRUD level?" has an `answer_shape` a plan answer
  could have filled, and none does.
- **Grounded in:** `requirement.md` L7 ("Agents also log about 20 cases a day by hand") and L19
  ("Replies to customers go from support@ … and from billing@ for finance cases") — read together,
  the population creates and edits Cases and drafts EmailMessage records, and nothing in the
  requirement or any answered clarification grants a delete on any of the five objects.
- **Why this is a default and not a decision:** the builder's own decision record names the source
  as `requirement.md` explicitly, distinct from the eleven rows in the same table sourced to a
  clarification id — see `envelopes/M2-S02/2026-09-12T00-05-00Z.json` →
  `extensions.decision_record[3]`, `question`: "Which objects does this capability touch, and at
  what CRUD level?", `source`: "requirement.md (agents log about 20 cases a day by hand and reply
  to customers; nothing in the requirement or the answers grants a delete)". This is also one of
  the three rows the builder's own confidence rationale names as MEDIUM, not HIGH:
  `dimensions_skipped[0]` (`question-coverage`, `state: partial`, `confidence_impact: MEDIUM`).
- **Evidence:** `artefacts/M2-S02/permissionsets/Case_Agent_Core.permissionset-meta.xml`;
  `envelopes/M2-S02/2026-09-12T00-05-00Z.md` § 4 "Decision record", row 3; `…json` →
  `extensions.decision_record[3]` and `dimensions_skipped[0]`.

## D-M2S02-02 — No permission-set expiry, and no step-up activation: two skill DEFAULTs

- **Date:** 2026-09-11
- **Step:** `M2-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-05-00Z`)
- **Kind:** design trade-off, recorded by the owning agent as a default
- **What was recorded:** none of the four permission sets or three groups carries an expiry —
  there is no `PermissionSetAssignment` metadata in this step at all, because assignment is record
  data — and `<hasActivationRequired>false</hasActivationRequired>` is written on all seven files.
- **Alternative rejected:** blocking the step until a clarification answers "Should any of this
  expire?" and "Does any permission need step-up activation?". Rejected for the same reason
  `D-M2S01-03` gave on `M2-S01`: neither question is a *gap in a skill* — both skills document a
  default — and blocking a step on a question nobody was asked strands the milestone. The same
  pattern repeating on a second access step is itself worth noting, not just the individual calls.
- **Grounded in:** `skills/admin/permission-set-architecture` — the expiry default (steady-state
  personas, not time-boxed elevations, are the case `admin/permission-set-expiration` and the
  `Temp_<Purpose>` route exist for) and § 1's note that `hasActivationRequired` stays `false` for
  anything destined for a PSG, because group membership itself removes the session-activation
  requirement.
- **Why this is filed as one entry and not two:** they are the same dimension in the builder's own
  record — `dimensions_skipped[0]`, `question-coverage`, `state: partial` — alongside the CRUD-level
  default in `D-M2S02-01`, and together are the reason that run's confidence is MEDIUM.
- **Evidence:** `artefacts/M2-S02/permissionsets/*.permissionset-meta.xml` (all four,
  `<hasActivationRequired>false</hasActivationRequired>`); `artefacts/M2-S02/permissionsetgroups/*.permissionsetgroup-meta.xml`
  (all three, same element); `envelopes/M2-S02/2026-09-12T00-05-00Z.json` →
  `extensions.decision_record[7]` and `[8]`, `dimensions_skipped[0]`.

## D-M2S02-03 — No `userPermissions` on any set: `TransferAnyCase` is UNVERIFIED, so it was omitted

- **Date:** 2026-09-11
- **Step:** `M2-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-05-00Z`)
- **Kind:** design trade-off — an omission recorded rather than an absence left to be noticed
- **What was recorded:** none of the four permission sets carries a `<userPermissions>` block of
  any kind.
- **Alternative rejected:** granting `TransferAnyCase` to Tier 2, on the theory that an engineer
  taking an escalated case plausibly needs to transfer ownership. Rejected because the one
  Case-relevant system permission named anywhere in the cited skills —
  `skills/admin/permission-set-architecture/references/metadata-examples.md` § 2 — is marked
  **`UNVERIFIED (2026-09-04)`**, with the skill's own worked example using `TransferAnyLead`
  instead. `agents/metadata-builder/AGENT.md` and rule 1 of `agents/_shared/AGENT_CONTRACT.md`
  ("Skill-first, never freestyle") both forbid writing an element the cited skill flags as unverified
  rather than as a documented fact, and no clarification asks for a system permission either.
- **Grounded in:** `skills/admin/permission-set-architecture/references/metadata-examples.md` § 2
  (the `UNVERIFIED` marker); `artefacts/M2-S02/deploy-order.md` § "Elements this step could NOT
  ground".
- **Consequence, stated for the gate:** if Tier 2 turns out to need case transfer beyond plain
  ownership reassignment through the UI, that is a new grant to design against a verified source —
  not a guess this build should have made.
- **Skill-gap signal, per `standards/build-orchestration.md` § 8:** verify whether `TransferAnyCase`
  is a real system permission and, if so, add it to `permission-set-architecture`'s element
  inventory undated. Until it is verified, no build in this repo should write it.
- **Evidence:** `artefacts/M2-S02/deploy-order.md` § "Elements this step could NOT ground";
  `envelopes/M2-S02/2026-09-12T00-05-00Z.json` → `dimensions_skipped[1]` (`element-grounding`,
  `state: partial`, `confidence_impact: NONE`).

## D-M2S02-04 — No `viewAllFields` on any `objectPermissions` block: target API is 62.0

- **Date:** 2026-09-11
- **Step:** `M2-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-05-00Z`)
- **Kind:** design trade-off — a version-gated omission
- **What was recorded:** none of `Case_Agent_Core`'s five `objectPermissions` blocks carries a
  `<viewAllFields>` element. The six `PermissionSetObjectPermissions` fields the cited guide marks
  Required are present explicitly on every block instead.
- **Alternative rejected:** writing `viewAllFields` for read-simplicity on the read-only objects
  (Account, Contact, Entitlement). Rejected because `permission-set-architecture/references/metadata-examples.md`
  dates that element **API 63.0+**, and this manifest's `<version>` is `62.0` — the same version
  every other manifest in this build has defaulted to (`decisions.md` M1 report finding **F-06**,
  restated on `CWB-OTHER-001`, `-004`, `-006` and now `-008`). The cited reference's own
  object-access worked example omits the element for exactly this reason.
- **Grounded in:** `skills/admin/permission-set-architecture/references/metadata-examples.md`
  (the API 63.0+ date on `viewAllFields`); `artefacts/M2-S02/package.xml` (`<version>62.0</version>`).
- **Open item, stated rather than hidden:** if this build's target API version is later raised to
  63.0+ (no clarification or plan field sets one; it is a build-wide default, same as `D-M1S01`'s
  and `D-M2S01-04`'s siblings), `viewAllFields` becomes available and the read-only blocks in this
  set are the ones a re-plan would revisit first.
- **Evidence:** `artefacts/M2-S02/package.xml`; `artefacts/M2-S02/deploy-order.md` § "Decisions
  worth reading before deploy", item 2; `envelopes/M2-S02/2026-09-12T00-05-00Z.json` →
  `extensions.decision_record` (element-grounding notes) and `citations` (`permission-set-architecture/references/metadata-examples.md`,
  "used_for" naming the API 63.0+ date).

## D-M2S02-05 — `Case_Tier1` and `Case_Tier2` are identical: two declared outputs, not a collapse decision

- **Date:** 2026-09-11
- **Step:** `M2-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-05-00Z`), raised again by `build-step-runner`
  (run `2026-09-12T00-10-00Z`) and by `step-tester` (run `2026-09-12T00-14-33Z`) — three independent
  agents recorded the same observation without adjudicating it
- **Kind:** design trade-off, recorded rather than resolved
- **What was recorded:** `Case_Tier1.permissionset-meta.xml` and `Case_Tier2.permissionset-meta.xml`
  are byte-identical in every grant-bearing element: one `fieldPermissions` (`Case.Severity__c`,
  editable + readable) and one `recordTypeVisibilities` (`Case.Support`, visible). Only the file
  name, the `<label>` and the `<description>` differ.
- **Why two sets were written rather than one:** `plan.json` `steps[M2-S02].outputs[]` declares
  both `artefacts/M2-S02/permissionsets/Case_Tier1.permissionset-meta.xml` and
  `…/Case_Tier2.permissionset-meta.xml` as separate paths. A builder collapsing a declared output
  into a shared file would leave one of the two paths unwritten, which `check-outputs` fails —
  exactly the same constraint `D-M2S01-04` records for not renaming `Case_Intake_Integration`
  against the template form.
- **Alternative rejected:** granting Tier 2 something Tier 1 lacks so the two sets would earn their
  separate existence. Rejected because no answered clarification supplies one — the requirement's
  Tier 1/Tier 2 distinction is **routing** (Tier 1 is pushed work, Tier 2 pulls from a list,
  `requirement.md` L12–L14) and **escalation** (untouched for 8 business hours escalates to Tier 2,
  L16), both Omni-Channel / queue / EscalationRules concerns scheduled at `M2-S04`, `M3` and `M4` —
  not an access distinction this step could invent.
- **Why the near-clone checker is silent:** `check_permission_set_group_composition.py`'s
  near-clone heuristic requires 4+ shared permission sets to fire; this build has two, so the
  checker's silence is a size threshold, not a clean bill of health — the observation is the
  builder's own note, not a checker finding.
- **What this is NOT deciding:** collapsing `Case_Tier1` and `Case_Tier2` into one shared set (with
  `PSG_Tier1_Prod` and `PSG_Tier2_Prod` composing the same member set, or a single PSG holding both
  teams) is a real option, and it is **deferred to a v6 planner decision**, not applied here. This
  agent does not amend `outputs[]`, and `agents/metadata-builder/AGENT.md` does not collapse a
  declared output on its own judgment.
- **Grounded in:** `requirement.md` L12–L16; `skills/admin/permission-set-group-composition/scripts/check_permission_set_group_composition.py`
  (the 4+ near-clone threshold); `plan.json` `steps[M2-S02].outputs[1]` and `[2]`.
- **Evidence:** `artefacts/M2-S02/permissionsets/Case_Tier1.permissionset-meta.xml` and
  `Case_Tier2.permissionset-meta.xml` (diffed, identical grant elements);
  `envelopes/M2-S02/2026-09-12T00-05-00Z.json` → `process_observations[2]` (concerning, medium);
  `envelopes/M2-S02/2026-09-12T00-10-00Z.json` → `process_observations` (ambiguous, low);
  `envelopes/M2-S02/2026-09-12T00-14-33Z.json` → not adjudicated, reported only.

## D-M2S02-06 — Billing's read-only `Severity__c` access is a builder reading, not a hardcoded assumption

- **Date:** 2026-09-11
- **Step:** `M2-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-05-00Z`)
- **Kind:** design trade-off, recorded by the owning agent as an inference from the requirement
- **What was recorded:** `Case_Billing.permissionset-meta.xml` carries **no `fieldPermissions`
  element at all**. Billing's field-level access to `Case.Severity__c` is therefore whatever
  `Case_Agent_Core` grants through composition (`readable=true`, `editable=false`) — nothing in
  `Case_Billing` itself grants or denies it.
- **Alternative rejected:** writing an explicit `fieldPermissions` block on `Case_Billing` that
  denies edit, to make the restriction visible in the file that is "about" Billing. Rejected because
  a permission set can only grant, never deny (`skills/admin/permission-sets-vs-profiles` — grants
  are additive; an explicit deny is not an expressible `fieldPermissions` state), so the only way to
  keep Billing off the edit grant is to not write it anywhere Billing's effective access is composed
  from — which is what the builder did.
- **Why this is a reading and not an answered clarification:** no clarification asks "may Billing
  edit `Case.Severity__c`?" The builder's own decision record, question "Which field-level grants
  does each persona need?", reads: "Everyone reads `Case.Severity__c`, `Account.Region__c` and
  `Account.Support_Tier__c`; the two support tiers also edit `Severity__c`" — Billing is the persona
  named as reading but not named among "the two support tiers" who edit it.
- **Grounded in:** `requirement.md` L18 — "Severity 1 outages are 24/7 and never pause" — the only
  sentence in the entire requirement that names a severity at all, and it names an outage, not a
  finance query; and `decisions.md` **D-M1S02-02**, which records the same reading already applied
  once, to keep `Severity__c` off the Billing page layout entirely.
- **Evidence:** `artefacts/M2-S02/permissionsets/Case_Billing.permissionset-meta.xml` (no
  `fieldPermissions` element); `artefacts/M2-S02/permissionsets/Case_Agent_Core.permissionset-meta.xml`
  (`Case.Severity__c`, `readable=true`, `editable=false`); `envelopes/M2-S02/2026-09-12T00-05-00Z.json`
  → `extensions.decision_record[12]` and `process_observations` (ambiguous, low, domain `access`).

## D-M2S02-07 — Rebuild #2: `<description>` trimmed on all four permission sets, cause F-15

- **Date:** 2026-09-12
- **Step:** `M2-S02` (`access`), rebuild #2 (`documented → running → built → tested`)
- **Agent:** `metadata-builder` (run `2026-09-12T01-20-00Z`), retested by `step-tester` (run
  `2026-09-12T01-26-00Z`)
- **Kind:** deviation — a rebuild triggered by an org-boundary finding, not a plan change
- **What was recorded:** `reports/MOCK-DEPLOY-M2.md` run 1 rejected all four `PermissionSet` files
  in this step with `Description: data value too large … (max length=255)`; the three
  `PermissionSetGroup` files cascaded as a consequence of the four failed member sets, not because
  any PSG description was itself too long. This rebuild rewrote only the `<description>` element of
  `Case_Agent_Core.permissionset-meta.xml` (419→192 chars), `Case_Tier1.permissionset-meta.xml`
  (290→193), `Case_Tier2.permissionset-meta.xml` (456→199) and `Case_Billing.permissionset-meta.xml`
  (380→183). Every other element on all four files — `label`, `hasActivationRequired`,
  `objectPermissions`, `fieldPermissions`, `tabSettings`, `recordTypeVisibilities`,
  `applicationVisibilities` — is byte-identical to the first pass; SHA-256 hashes proving only
  `<description>` changed are in `artefacts/M2-S02/deploy-order.md` § "Rebuild #2 — descriptions".
  No `PermissionSetGroup` file needed editing: all three descriptions (187 / 194 / 132 chars) were
  already under the new 200-char WARN line.
- **Alternative rejected:** leaving the long rationale inline and instead having the org accept a
  truncated description. Rejected because `PermissionSet.description` is a hard 255-char Metadata
  API ceiling, not a display truncation — a description over the limit fails the deploy outright, so
  the rationale had to move somewhere else rather than be shortened lossily in place. The fuller
  narrative moved to `artefacts/M2-S02/deploy-order.md` § "Rebuild #2 — descriptions", one entry per
  component, so nothing that made the first pass reviewable was lost.
- **Grounded in:** `admin/permission-set-architecture` v1.2.0, which added PSA-DESC-01 (ERROR, >255
  chars) and PSA-DESC-02 (WARN, >200 chars) after this finding; `admin/permission-set-group-composition`
  v1.1.0's matching PSGC-DESC-01/02; `admin/permission-sets-vs-profiles` v1.2.0's PSVP-DESC-01; and
  the org's own validation in `reports/MOCK-DEPLOY-M2.md` run 2, which re-ran the same six steps and
  succeeded (30 components, 0 errors) after the rebuild.
- **Evidence:** `envelopes/M2-S02/2026-09-12T01-20-00Z.md` (metadata-builder rebuild envelope, SHA-256
  table); `envelopes/M2-S02/2026-09-12T01-25-00Z.md` (build-step-runner, `built`);
  `envelopes/M2-S02/2026-09-12T01-26-00Z.md` (step-tester retest, all three checkers + xml + manifest
  pass, `tested`); `artefacts/M2-S02/deploy-order.md` § "Rebuild #2 — descriptions";
  `reports/MOCK-DEPLOY-M2.md` runs 1–2.

---

# Open items for the planner — raised by the M2-S02 documentation run

Same standing as the sections above and for the same reason: these are plan-file text and
plan-file declarations, and `standards/build-orchestration.md` § 2 gives `build_plan.py` sole
authority over them. None blocks the step — `M2-S02` passed every executable test it declares, and
it declares no `manual` test at all.

## O-M2S02-01 — `deploy-order.md` is undeclared in `outputs[]` on `M2-S02` too — a regression, not a repeat

- **Date:** 2026-09-11 · **Recorded by:** `build-doc-keeper`, from the M2-S02 builder and runner
  envelopes
- `M2-S02`'s `outputs[]` declares `package.xml` and the seven metadata files but not
  `artefacts/M2-S02/deploy-order.md`, even though `agents/metadata-builder/AGENT.md` writes that
  file on every run. `check-outputs` therefore confirms eight of the nine files this step actually
  produced, and the always-on `manifest` test excludes the ninth by name as "not a source-format
  metadata file" — the identical mechanics `O-M1S02-02` recorded for both M1 steps.
- **Why this one is a regression and not a third repeat of the same slip.** `M2-S01` was the first
  step in this build to declare `deploy-order.md` in `outputs[]` (`CWB-OTHER-007`; `decisions.md`
  narrative on that row), closing the gap for that step. `M2-S02` is the next `metadata-builder`
  step after it and does not carry the fix forward — the plan's declared outputs for `M2-S02` were
  written without it, not because the builder omitted something it was asked to declare.
- **Now four of four `metadata-builder`-owned metadata steps in this build have produced a
  `deploy-order.md`; two of the four (`M1-S01`, `M1-S02`) never declared it, one (`M2-S01`) declared
  it, and this one (`M2-S02`) does not.** The pattern is not monotonic, which is itself worth a
  planner's attention: fixing it once on `M2-S01` did not become a habit the rest of the plan
  inherited.
- **Why it matters beyond this row:** `agents/build-doc-keeper/AGENT.md` Step 10 builds `M5-S04`'s
  build-wide deploy order from exactly these per-step `deploy-order.md` files. The compile run
  therefore still depends on a set of files only some of which any gate in the loop confirms exist.
- **Remedy at v6:** declare `artefacts/<step-id>/deploy-order.md` in `outputs[]` on **every**
  `metadata-builder`-owned step, not case by case as each gap is found. Raised by `metadata-builder`
  (`process_observations`, concerning/low) and by `build-step-runner` (`process_observations`,
  concerning/low) independently.
- **Evidence:** `envelopes/M2-S02/2026-09-12T00-05-00Z.json` → `extensions.artefacts[8].declared:
  false`; `envelopes/M2-S02/2026-09-12T00-10-00Z.json` → `process_observations` (concerning, low);
  `plan.json` `steps[M2-S02].outputs[]`; workbook `CWB-OTHER-009`.

## O-M2S02-02 — `Case_Tier1` and `Case_Tier2` are identical: flagged for the v6 collapse decision

- **Date:** 2026-09-11 · **Recorded by:** `build-doc-keeper`, from the M2-S02 decision record
  (`D-M2S02-05` above)
- Full reasoning is in `D-M2S02-05`; this entry is the planner-facing pointer `decisions.md`'s other
  open-item sections keep alongside a decision when the decision itself says a plan change is the
  remedy. The concrete question for a v6 re-plan: collapse `Case_Tier1` and `Case_Tier2` into one
  permission set composed into both `PSG_Tier1_Prod` and `PSG_Tier2_Prod`, or leave the two
  declared outputs as they are and accept that they will diverge only if a future requirement gives
  one team an access the other lacks.
- **Not a defect to fix by re-running this step.** `M2-S02` built exactly what `outputs[]`
  declares, and both files pass every check declared against them. This is scope for the planner,
  not a correction for the builder.
- **Evidence:** `decisions.md` D-M2S02-05; `artefacts/M2-S02/permissionsets/Case_Tier1.permissionset-meta.xml`,
  `Case_Tier2.permissionset-meta.xml`.

## O-M2S02-03 — assumption A1 does not list `M2-S02`, though this step's `recordTypeVisibilities` are shaped by it

- **Date:** 2026-09-11 · **Recorded by:** `build-doc-keeper`, extending the same gap `traceability.md`
  § "Assumption linkage — A1 now reaches M1-S01" already records for `M1-S01`
- `plan.json` → `assumptions[A1].steps[]` reads `["M2-S05"]` only. `Case_Tier1` and `Case_Tier2`
  grant `recordTypeVisibilities` for `Case.Support` and withhold `Case.Billing`; `Case_Billing`
  grants `Case.Billing` and withholds `Case.Support` — exactly the conservative reading A1 states,
  and `artefacts/M2-S02/deploy-order.md` names A1 explicitly as the reason. Neither `M1-S01` (the
  OWD) nor `M2-S02` (these `recordTypeVisibilities`) appears in `A1.steps[]`, though both carry
  artefacts A1 shaped.
- **Not the same mechanism as record access, and the row text says so:** `recordTypeVisibilities`
  governs which record type a user may select when creating or editing a Case, not whether they may
  open one that already exists. The mechanism that actually makes A1 true — the Private OWD plus
  `M2-S05`'s sharing rule — is unaffected by this gap; only the assumption's own bookkeeping is
  incomplete.
- **Remedy at v6:** add `M1-S01` and `M2-S02` to `A1.steps[]`. Until then, `M5-S04`'s compile run —
  which builds the assumptions section from `assumptions[].steps[]` "rather than from step-note
  prose" per its own acceptance test — will not show either step as a carrier of A1, even though
  both this file and `traceability.md` do.
- **Evidence:** `plan.json` `assumptions[A1]`; `artefacts/M2-S02/deploy-order.md` § "Decisions worth
  reading before deploy", item 6; `traceability.md` § "What M2-S02 rests on".

## O-M2S02-04 — F-15 CLOSED at the skills; the plan's own step tests now carry DESC rules their description text does not mention

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the rebuild #2 envelopes and a
  direct read of `plan.json` `steps[M2-S02].acceptance_tests[]`
- **F-15 status: CLOSED at the skill level.** `admin/permission-set-architecture` v1.2.0
  (PSA-DESC-01 ERROR / PSA-DESC-02 WARN), `admin/permission-set-group-composition` v1.1.0
  (PSGC-DESC-01 / PSGC-DESC-02) and `admin/permission-sets-vs-profiles` v1.2.0 (PSVP-DESC-01) all
  now enforce the 255-char Metadata API ceiling on `description`, with a 200-char WARN as headroom.
  `reports/MOCK-DEPLOY-M2.md` run 2 confirms the org side: the same six steps that failed in run 1
  now validate at 30/30, 0 errors. `D-M2S02-07` carries the full rebuild record.
- **What is not closed — a drift this rebuild exposed but did not fix.** None of the five
  `acceptance_tests[]` declared on `M2-S02` in `plan.json` mentions the DESC rule at all in its
  `description` field: the `permission-set-architecture` test's description enumerates
  fieldPermissions edit-without-read, the objectPermissions chain, the sharing-bypass WARN and PSG
  membership checks; the `permission-set-group-composition` and `permission-sets-vs-profiles` test
  descriptions read the same as before the skills gained the DESC rule. The **command** each test
  declares is unchanged and did exercise the new rule (it is the same checker, now a version newer),
  so the test still passed correctly — but a reader of `PLAN.md` checking what `exit 0` proves would
  not learn that a description-length ERROR is now one of the things it rules out.
- **Not a defect in this step or this rebuild.** The tests still ran the right commands and got the
  right answer; the gap is that a test's `description` field is authored prose, not derived from the
  checker's rule set, so a skill version bump that adds a new ERROR/WARN pair does not by itself
  update every plan that already cites the checker.
- **Remedy at v6:** either regenerate the affected `acceptance_tests[].description` strings from the
  checkers' current rule sets at re-plan time, or add one sentence to each of the three descriptions
  naming the DESC rule explicitly, the same way `O-M2S04-01` already flags a stale WARN count in a
  different step's test description.
- **Evidence:** `plan.json` `steps[M2-S02].acceptance_tests[0..2].description` (no `DESC` or
  `description-length` token in any of the three); `envelopes/M2-S02/2026-09-12T01-20-00Z.md`
  (metadata-builder rebuild, decision-record row 2); `reports/MOCK-DEPLOY-M2.md` runs 1–2;
  `decisions.md` D-M2S02-07.

---

## D-M2S04-01 — `<doesIncludeBosses>` is absent from all three `Queue` files and a skill DEFAULT `true` on all three `Group` files

- **Date:** 2026-09-12
- **Step:** `M2-S04` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-48-00Z`)
- **Kind:** design trade-off, version-gated — the same shape as `D-M2S02-04`, one skill and one
  manifest version later
- **What was recorded:** none of `Tier_1_General`, `Tier_2_Engineering` or `Billing` carries a
  `<doesIncludeBosses>` element. All three of `Support_Tier_1`, `Support_Tier_2` and `Billing_Team`
  carry `<doesIncludeBosses>true</doesIncludeBosses>`.
- **Alternative rejected:** writing `<doesIncludeBosses>` on the three `Queue` files too, for
  symmetry with the groups. Rejected because `skills/admin/queues-and-public-groups/references/metadata-examples.md`
  dates that element on `Queue` at **API 67.0+**, and this manifest's `<version>` is `62.0` — the
  same default every manifest in this build carries (M1 report finding **F-06**). Writing it would
  be an element the target API version does not carry.
- **Why `true` on the groups is a default and not an answered decision:** no clarification asks
  whether managers above the members should see queue-owned records. The cited skill says to "leave
  it `true` unless managers must not see queue-owned records", so `true` is written and labelled a
  default here — the same posture `D-M2S02-02` records for two other defaults on `M2-S02`.
- **Grounded in:** `skills/admin/queues-and-public-groups/references/metadata-examples.md` (the API
  67.0+ date on `Queue.doesIncludeBosses`, and the group-level default with no version gate);
  `artefacts/M2-S04/package.xml` (`<version>62.0</version>`).
- **Open item, stated rather than hidden:** Grant Access Using Hierarchies for *queue-owned* records
  therefore falls to the org's own setting at API 62.0; if that visibility must be explicit on the
  queue itself, the manifest has to move to 67.0 first. If Q13's deferred finance-visibility
  question resolves toward record-level separation, `Billing_Team`'s `true` is the file to revisit.
- **Evidence:** `artefacts/M2-S04/queues/*.queue-meta.xml` (no `doesIncludeBosses` on any);
  `artefacts/M2-S04/groups/*.group-meta.xml` (all three `true`); `artefacts/M2-S04/deploy-order.md`
  § "Decisions worth reading before deploy", items 1–2; `envelopes/M2-S04/2026-09-12T00-48-00Z.json`
  → `extensions.decision_record[5]`.

## D-M2S04-02 — Tier 2's queue mailbox address is ungrounded: omitted, not invented

- **Date:** 2026-09-12
- **Step:** `M2-S04` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-48-00Z`)
- **Kind:** design trade-off — an ambiguity recorded rather than filled
- **What was recorded:** `Tier_2_Engineering.queue-meta.xml` carries no `<email>` element at all;
  `<doesSendEmailToMembers>false</doesSendEmailToMembers>` stands alone.
- **Alternative rejected:** inventing an address such as `tier2@acme.example` to satisfy Q88's
  posture ("a shared mailbox per queue"). Rejected because no clarification, and no line of
  `requirement.md`, names a Tier 2 mailbox — the two addresses on file
  (`support@acme.example`, `billing@acme.example`) are the general and finance intake addresses and
  neither is Tier 2's. An invented address would look grounded while routing real notifications
  nowhere, which `agents/metadata-builder/AGENT.md` refuses to do.
- **Consequence, stated for the gate:** `check_queues.py --manifest-dir artefacts/M2-S04` now prints
  **two** WARNs (`No <email> configured` on both Tier 1 General and Tier 2 Engineering), one more
  than the step's own `acceptance_tests[0].description` predicts — see **O-M2S04-01** below. The
  manual test asserting "Tier_2_Engineering carries the Tier 2 shared mailbox" (`W02 1 of 3`) does
  not hold on this artefact — see **O-M2S04-02** below.
- **Grounded in:** `requirement.md` (no Tier 2 address anywhere); `plan.json` clarification `Q88`
  (posture only, no value); `artefacts/M2-S04/deploy-order.md` § "Elements this step could NOT
  ground", item 2.
- **Skill-gap signal:** none — this is a missing **answer**, not a missing **skill fact**. The
  remedy is a clarification naming the address, not a skill edit.
- **Evidence:** `artefacts/M2-S04/queues/Tier_2_Engineering.queue-meta.xml`;
  `tests/M2-S04/check_queues_stdout.txt`; `tests/M2-S04/results.json` → `skipped_manual[1]`;
  `envelopes/M2-S04/2026-09-12T00-48-00Z.json` → `extensions.ungrounded[0]`.

## D-M2S04-03 — Role developer names for `queueMembers/roles` are ungrounded: membership is public-group-only, not "role and public group"

- **Date:** 2026-09-12
- **Step:** `M2-S04` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-48-00Z`)
- **Kind:** design trade-off — an answered clarification built in half, the same shape `D-M1S02-03`
  records for Q24
- **What was recorded:** none of the three queue files carries a `<roles>` or
  `<roleAndSubordinatesInternal>` membership entry. Membership is carried entirely by the three
  public groups.
- **What Q29 actually asks for:** "by role **and** public group, no named users." The public-group
  half is written; the role half is not.
- **Alternative rejected:** inventing a role developer name (for example
  `Support_Manager_Tier_1`) so the queue file matches Q29's answer literally. Rejected because **no
  role developer name exists anywhere in this build** — not in `requirement.md`, not in any of the
  97 clarifications, not in an upstream step's artefacts — and `skills/admin/queues-and-public-groups`
  is explicit that role members deploy by role developer name, so writing one would mean inventing
  the name of a role hierarchy nobody has described.
- **Consequence, stated for the gate:** if the org's role hierarchy is meant to feed these queues
  directly (rather than through the public groups alone), that is a change to all three queue files,
  and it needs the role developer names answered first.
- **Grounded in:** `plan.json` clarification `Q29` ("by role and public group, no named users");
  `artefacts/M2-S04/deploy-order.md` § "Elements this step could NOT ground", item 1.
- **Evidence:** `artefacts/M2-S04/queues/*.queue-meta.xml` (no `<roles>` element on any);
  `envelopes/M2-S04/2026-09-12T00-48-00Z.json` → `extensions.ungrounded[1]`,
  `extensions.decision_record[0]`.

## D-M2S04-04 — The Billing queue's notification address is also the Email-to-Case intake address: a recorded loop risk, not a defect

- **Date:** 2026-09-12
- **Step:** `M2-S04` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-48-00Z`)
- **Kind:** design trade-off — a risk recorded rather than silently carried
- **What was recorded:** `Billing.queue-meta.xml` carries `<email>billing@acme.example</email>`.
  `requirement.md` L8 also names `billing@acme.example` as the address Finance queries arrive at —
  the same address `M3-S03` (Email-to-Case routing, `pending`) will configure as an inbound intake
  address.
- **Why the value is grounded and written anyway:** Q88's answer says Billing "wants the queue
  address emailed", and `billing@acme.example` is the only Billing address named anywhere in
  `requirement.md` — there is no second, unambiguously-different address to prefer.
  `agents/metadata-builder/AGENT.md` does not treat "this value is also used elsewhere" as a reason
  to omit an otherwise-grounded value.
- **The risk, stated in full:** a queue-assignment notification sent to an address that Email-to-Case
  also reads as an intake mailbox can create a new Case, which lands back in the Billing queue, which
  sends another notification — the same class of loop the answer key flags for the auto-response
  sender ("an org-wide email address, never the Email-to-Case routing address itself"), here on the
  queue-notification side instead.
- **Alternative rejected:** withholding the `<email>` element until a second, dedicated notification
  address is answered. Rejected because Q88 is an answered, non-deferred question with exactly one
  grounded value, and withholding a grounded answer to pre-empt an unconfirmed risk is not this
  agent's call to make — the risk is recorded for the gate instead.
- **What closes this, and who owns it:** `M3-S03` configures the Email-to-Case routing address for
  `billing@acme.example`; the sandbox loop test Q68 already requires (per the answer key) is where
  this specific risk must be exercised — send a queue-assignment notification and a fresh inbound
  case to the same address in the same sandbox and confirm no chain forms. If it fires, the recorded
  remedy is a separate, monitored alias for queue notification rather than the intake address itself.
- **Grounded in:** `requirement.md` L8, L19; `plan.json` clarification `Q88`; `artefacts/M2-S04/deploy-order.md`
  § "Decisions worth reading before deploy", item 4.
- **Evidence:** `artefacts/M2-S04/queues/Billing.queue-meta.xml`;
  `envelopes/M2-S04/2026-09-12T00-48-00Z.json` → `process_observations[2]` (concerning, medium).

## D-M2S04-05 — `Tier_1_General` ships with no `<queueRoutingConfig>`: a deliberate forward reference, against the cited reference's own deploy order

- **Date:** 2026-09-12
- **Step:** `M2-S04` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T00-48-00Z`)
- **Kind:** design trade-off — a plan-level ordering conflict named rather than silently absorbed
- **What was recorded:** `Tier_1_General.queue-meta.xml` carries no `<queueRoutingConfig>` element.
- **Alternative rejected:** writing `<queueRoutingConfig>Tier_1_Push</queueRoutingConfig>` now, ahead
  of the component it names. Rejected because `Tier_1_Push` is `M3-S05`'s declared output and
  `M3-S05` `depends_on` `M2-S04` — at this step's build time that component does not exist anywhere
  in `artefacts/`, and naming it would be a dangling reference no deploy could resolve.
- **The ordering conflict this exposes, named rather than fixed here:**
  `skills/admin/queues-and-public-groups/references/metadata-examples.md` says to deploy the routing
  configuration **before** the queue, and warns that omitting it "means the queue is never pushed" on
  an Omni-Channel org. `plan.json` orders the two the other way round — `M2-S04` before `M3-S05` —
  which is the opposite of the cited reference's own stated order.
- **Concrete, bounded consequence:** `Tier_1_General` is a list-view queue until the element is
  added. The second pass is either (a) deploy `M3-S05`'s `queueRoutingConfig` and then re-deploy this
  file with the element added (alphabetically after `queueMembers`, before `queueSobject`), or
  (b) deploy `M2-S04` and `M3-S05` in one request with the element present from the start.
- **Why this is filed here and not fixed in the plan:** `standards/build-orchestration.md` § 2 gives
  `build_plan.py` sole authority over `plan.json`'s step order, and this agent does not touch it
  beyond its own status transition. The remedy is a v6 planner decision — either re-sequence
  `M3-S05` ahead of `M2-S04`, or accept the documented second pass. See **O-M2S04-03** below for the
  planner-facing pointer.
- **Grounded in:** `skills/admin/queues-and-public-groups/references/metadata-examples.md`;
  `plan.json` milestone/step order (`M2-S04` before `M3-S05`); `artefacts/M2-S04/deploy-order.md`
  § "One forward reference, deliberately not written".
- **Evidence:** `artefacts/M2-S04/queues/Tier_1_General.queue-meta.xml` (no `queueRoutingConfig`);
  `envelopes/M2-S04/2026-09-12T00-48-00Z.json` → `process_observations[3]` (concerning, low).

## D-M2S04-06 — Queue and Group rows are filed under Section 6 (Automation), against the step's own declared type

- **Date:** 2026-09-12
- **Step:** `M2-S04` (`access`)
- **Agent:** `build-doc-keeper` (this run) — a documentation-placement decision, not a metadata one
- **Kind:** design trade-off, recorded by this agent because it is the one making the placement call
- **What was recorded:** the six `Queue` and `Group` rows below (`CWB-AUT-001`–`006`) are written to
  `workbook/06-automation.md` under **Section 6 — Automation**, not to Section 3 or 4.
- **Why this is not the literal reading of `agents/build-doc-keeper/AGENT.md` Step 4:** the step's
  own `type` is `access`, and Step 4's table maps `access` to "3 — Profiles + Permission Sets + PSGs,
  and 4 — Sharing Settings for sharing artefacts." A `Queue` or `Group` is neither.
- **Why Section 6 was chosen instead:** three independent sources agree the content is routing/work-
  distribution infrastructure, not access:
  1. `standards/build-orchestration.md` § 4's own step-type table files `Queue` / routing metadata
     under **`routing`**, not `access` — and the same document's Step 4 mapping (via
     `agents/build-doc-keeper/AGENT.md`) sends `routing` artefacts to "6 — Automation, with queue,
     routing and Email-to-Case / Web-to-Case artefacts named in `target_value`", naming queues
     explicitly.
  2. `skills/admin/configuration-workbook-authoring/references/worked-examples.md` (row
     `CWB-AUT-102`) already files a queue-routing target under the `CWB-AUT-` (Automation) row
     prefix in its own worked example — a queue assignment target is precedent-filed as Automation
     in this skill's own canonical example, not as an access artefact.
  3. `metadata-builder`'s own envelope flags the same tension unresolved
     (`process_observations`, ambiguous, low): "the step's type is `access` while
     `standards/build-orchestration.md` section 4 files Queue metadata under routing … the type and
     the artefact column disagree."
- **What this is NOT doing:** overriding the plan's declared step `type` — `plan.json` still records
  `M2-S04.type = "access"`, and this agent does not touch `plan.json` beyond its own status
  transition. This is a **workbook-section** placement only, made because Step 4's own table gives
  no section that fits a `Queue`/`Group` artefact under `access`, and "the default matters" clause
  in the same AGENT.md section directs an unfitting artefact to be documented with a flag rather than
  force-fit or dropped.
- **What is NOT changed:** the deploy-position **sequence** these rows carry (Step 5) still uses
  `routing`'s position in the ten-slot order (objects → fields → picklists → record types → layouts →
  permission sets → sharing → automation → **routing** → SLA), not `automation`'s — the workbook
  *section* and the deploy *sequence position* are tracked separately in these rows for exactly this
  reason.
- **Alternative rejected:** filing the six rows under Section 3/4 as Step 4's table literally
  states. Rejected because a Section 3 row under the heading "Profiles + Permission Sets + PSGs"
  naming a `Queue` would misdescribe the artefact to any reader who has not also read this entry —
  the same reasoning the M2-S02 workbook file gives for filing a `CustomPermission` in Section 3
  rather than Section 5 (a **content** judgment, stated rather than silently applied).
- **Alternative rejected:** creating a **Section 9 — Routing** file instead of Section 6. Rejected
  because Step 4's own table names Section 6 (Automation) as the destination for `routing`-typed
  artefacts explicitly — there is no Section 9 in Step 4's map, and
  `skills/admin/configuration-workbook-authoring` Concept 2 fixes the workbook at ten canonical
  sections, none of which is "Routing" on its own.
- **Decision required at the M2 gate — a human's, not this agent's:** accept this placement, or
  direct a v6 fix to Step 4's table itself (adding an explicit `access`-vs-artefact-content override
  clause) so the next `routing`-shaped step filed under a non-`routing` `type` does not need a
  per-run judgment call recorded here.
- **Grounded in:** `standards/build-orchestration.md` § 4 (step-type table, artefact map);
  `agents/build-doc-keeper/AGENT.md` Step 4 (routing row, the default-matters clause) and Step 5
  (deploy-position sequence); `skills/admin/configuration-workbook-authoring/references/worked-examples.md`
  row `CWB-AUT-102`; `envelopes/M2-S04/2026-09-12T00-48-00Z.json` → `process_observations` (the
  `plan-shape` ambiguous entry).
- **Evidence:** `workbook/06-automation.md` (new file, this run); `plan.json` `steps[M2-S04].type =
  "access"` (unchanged).

---

# Open items for the planner — raised by the M2-S04 build and test runs

Same standing as every section above: plan-file text and plan-file declarations, and
`standards/build-orchestration.md` § 2 gives `build_plan.py` sole authority over them. None blocks
the step — `M2-S04` passed every executable test it declares.

## O-M2S04-01 — `acceptance_tests[0].description` predicts "Warnings found (1)"; the real run prints "Warnings found (2)"

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the `metadata-builder` and
  `step-tester` envelopes, which raised it independently
- `plan.json` → `steps[M2-S04].acceptance_tests[0].description` states that a fixture run over
  exactly this step's six files "printed 'Warnings found (1)'" naming only the Tier 1 General
  no-email WARN. The real run against the real artefacts prints **`Warnings found (2)`**: Tier 1
  General **and** Tier 2 Engineering both lack `<email>` (`tests/M2-S04/check_queues_stdout.txt`).
- **Why the description is stale rather than wrong about the pass condition:** the description was
  evidently written from a fixture in which Tier 2 carried an address; it does not — see
  **D-M2S04-02**. The declared `expected` ("exit 0, with the Tier 1 General no-email WARN as the
  documented outcome") still holds, because `--strict` is not passed and exit 0 is unaffected by an
  extra WARN. Only the count and the named queue in the description's prose are stale.
- **Remedy at v6:** reword the description to name both queues and "Warnings found (2)", or answer
  Tier 2's mailbox address so the second WARN goes away and the original description becomes true
  again. Either remedy also closes **O-M2S04-02** below, because both stale spots trace to the same
  missing answer.
- **Evidence:** `envelopes/M2-S04/2026-09-12T00-48-00Z.json` → `dimensions_skipped[0]`; `envelopes/M2-S04/2026-09-12T01-00-21Z.json`
  → `process_observations` (concerning, medium, domain `plan-artefact-consistency`);
  `tests/M2-S04/check_queues_stdout.txt`.

## O-M2S04-02 — Manual test W02 (1 of 3)'s criterion does not match `Tier_2_Engineering`'s artefact

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the `step-tester` envelope
- `plan.json` → `steps[M2-S04].acceptance_tests[4]` (`W02 1 of 3`) asserts, as its Given/When/Then:
  "…Tier_2_Engineering carries the Tier 2 shared mailbox." The artefact,
  `Tier_2_Engineering.queue-meta.xml`, carries **no `<email>` element at all** — there is no mailbox
  address on the file for the criterion to be true of.
- **Not a defect in the artefact or in the test run.** The artefact is correct given what was
  grounded (**D-M2S04-02**): Q88 answers a *posture* ("a shared mailbox") for Tier 2 with no address,
  and `agents/metadata-builder/AGENT.md` will not invent one. The test criterion is the one that
  states a fact ("carries the Tier 2 shared mailbox") that nothing in this build ever grounded.
- **Disposition, explicit rather than silently ticked:** `tests/M2-S04/results.json` →
  `skipped_manual[1]` records this as file-checkable evidence of a **mismatch**, not as a pass or a
  fail — the criterion is not tickable as written, and it is not the artefact's job to make it true.
  Flagged for human adjudication at the **M2 gate**, staged as `TC-M2S04-02`'s `known_mismatch` field
  in this run's staged UAT case pack (`scratchpad`, not a build-directory artefact — see this run's
  envelope, `extensions.uat_staging`).
- **Remedy at v6, either one closes it:** (a) answer Tier 2's mailbox address, rebuild the step, and
  the criterion becomes true of the artefact; or (b) reword the criterion to assert what Tier 2 was
  actually decided to carry — no address, `doesSendEmailToMembers=false`, "nobody is notified; the
  record is visible in the queue list view" (the notification-matrix row the cited skill documents
  for that state).
- **Grounded in:** `plan.json` `steps[M2-S04].acceptance_tests[4]`;
  `artefacts/M2-S04/queues/Tier_2_Engineering.queue-meta.xml`; `tests/M2-S04/results.json` →
  `skipped_manual[1]`; `envelopes/M2-S04/2026-09-12T01-00-21Z.json` → `process_observations`
  (concerning, medium, domain `acceptance-criteria-accuracy`).

## O-M2S04-03 — Two plan-level orderings this step's own artefacts flag, neither fixable here

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the `metadata-builder` envelope
  and `artefacts/M2-S04/deploy-order.md`
- **`M3-S05` (Omni-Channel routing for Tier 1) is sequenced after `M2-S04`, against the cited
  reference's own deploy order.** Full record: **D-M2S04-05**. The remedy is a v6 re-sequence of
  `M3-S05` ahead of `M2-S04`, or an accepted two-pass deploy for `Tier_1_General`.
- **The step's `type` (`access`) disagrees with `standards/build-orchestration.md`'s own artefact
  table (`routing`).** Full record: **D-M2S04-06**, which is also why this file's workbook rows for
  `M2-S04` are filed under Section 6 rather than Section 3/4. The remedy is a v6 addition to Step 4's
  mapping table (an explicit content-based override clause) rather than a per-step judgment call.
- **Neither is a defect in `M2-S04`'s own artefacts or tests.** Both are named here because
  `standards/build-orchestration.md` § 2 gives `build_plan.py` sole authority over `plan.json`'s
  step order and step `type` fields, and this agent touches neither beyond its own status
  transition.

## O-M2S04-04 — Correction of record: the data-skew checker's exit-1 gap this step's envelope named is now closed

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, confirmed by re-running the declared
  command against these artefacts in this documentation pass
- `metadata-builder`'s envelope (`dimensions_skipped[1]`) recorded that
  `check_data_skew_and_sharing_performance.py --manifest-dir artefacts/M2-S04` exited **1** on three
  findings it then classified as INFO ("Group X is deployed but no sharing rule in this manifest
  references it") — flagged as a checker gap because `queueMembers/publicGroups` was invisible to
  that checker's group-use scan, and no artefact fix was available inside this step's own outputs.
- **Fixed today, in this same session.** Commit `d7cc43e04` ("data-skew-and-sharing-performance
  checker — ERROR-only exit, `--strict`, queue-referenced groups count as used") landed after that
  envelope was written. Re-running the identical command in this documentation pass —
  `python3 skills/admin/data-skew-and-sharing-performance/scripts/check_data_skew_and_sharing_performance.py
  --manifest-dir artefacts/M2-S04` — now exits **0**: `3 finding(s): 0 error, 3 warn, 0 info`, all
  three re-worded as `WARN: Group '<name>' … is referenced by 1 reference(s) (queue … (queueMembers/publicGroups)) …
  but Group metadata never carries members … Pair this deploy with a GroupMember load step`. The
  checker now **counts a `queueMembers/publicGroups` reference as use**, which is exactly the gap
  the builder's envelope named, and the three findings are reclassified from a false "unused" INFO
  to an accurate "used but unmigrated" WARN — the same fact `deploy-order.md` § "Decisions worth
  reading before deploy" item 7 already states in prose ("Group membership is not in this deploy").
- **What this does and does not change about `M2-S04`'s own record.** The step was already `tested`
  and `check_data_skew_and_sharing_performance.py` was never one of its declared `acceptance_tests`
  — this checker's exit code has never gated this step's status, before or after the fix. Nothing in
  `tests/M2-S04/results.json` changes. This entry corrects the *checker-gap* framing in the
  builder's `dimensions_skipped[1]`, which is now stale: the checker no longer needs "teaching" that
  `queueMembers/publicGroups` is a use of a `Group` (its own retry hint), because that is exactly
  what version 1.1.1 now does.
- **Grounded in:** commit `d7cc43e04d6816f3cec882e3ead7782fb5de06d2`;
  `skills/admin/data-skew-and-sharing-performance/scripts/check_data_skew_and_sharing_performance.py`
  (version 1.1.1); re-run output captured in this documentation pass, 2026-09-12.
- **Evidence:** `envelopes/M2-S04/2026-09-12T00-48-00Z.json` → `dimensions_skipped[1]`
  (`checker-pass`, `state: partial`, now superseded by this entry for the exit-code half only — the
  "no artefact fix exists inside this step" reasoning still stands, because a `GroupMember` load
  remains post-deploy data regardless of the checker's exit code).

---

## D-M2S03-01 — `layoutAssignments` on a record type the same profile marks `visible=false`: grounding gap, settled positively by mock deploy run 2

- **Date:** 2026-09-12
- **Step:** `M2-S03` (`access`)
- **Agent:** `metadata-builder` (build run `2026-09-12T00:44:16Z`, rebuild run `2026-09-12T01:16:41Z`); settled by `build-doc-keeper` reading `reports/MOCK-DEPLOY-M2.md` in this documentation pass
- **Kind:** design trade-off — an ungrounded element pairing, closed by org validation rather than by a cited skill
- **What was recorded:** `artefacts/M2-S03/deploy-order.md` § "Elements this step could NOT ground" named this pairing **UNGROUNDED, and the highest-value thing for the M2 mock deploy to settle**: whether a `layoutAssignments` entry is accepted for a record type the same profile marks `<visible>false</visible>` on. All three profiles carry exactly this shape — for example `Acme Support Tier 1` assigns `Case-Case Billing Layout` to `Case.Billing` while its own `recordTypeVisibilities` marks `Case.Billing` `visible=false`.
- **What settled it:** `reports/MOCK-DEPLOY-M2.md` "Run 2" (2026-09-11) validated all three profiles — unchanged on this pairing between run 1 and run 2, only the `<description>` element differed (`D-M2S03-06` below) — with **0 errors**, alongside the other 27 M1/M2 components. No error named a `layoutAssignments`/`recordTypeVisibilities` conflict on any of the three files.
- **Alternative rejected:** dropping the non-persona record type's `layoutAssignments` block pre-emptively, which `deploy-order.md` itself named as the remedy "if the deploy rejects it." Not applied, because the deploy accepted the pairing as built.
- **What remains open:** neither cited skill (`admin/permission-sets-vs-profiles`, `admin/record-types-and-page-layouts`) documents this pairing as valid — the settlement rests on one successful org validation, not on library content. Skill-gap signal per `standards/build-orchestration.md` § 8: record the accepted pairing in `record-types-and-page-layouts`' element inventory so a future build does not re-open the same question from zero.
- **Grounded in:** `reports/MOCK-DEPLOY-M2.md` § "Run 2"; `artefacts/M2-S03/deploy-order.md` § "Elements this step could NOT ground", item 3.
- **Evidence:** `artefacts/M2-S03/profiles/Acme Support Tier 1.profile-meta.xml`, `Acme Support Tier 2.profile-meta.xml`, `Acme Billing.profile-meta.xml` (all three carry the pairing); `reports/MOCK-DEPLOY-M2.md`.

## D-M2S03-02 — Alphabetical element order inside `<Profile>`: an ungrounded choice, also settled positively by mock deploy run 2

- **Date:** 2026-09-12
- **Step:** `M2-S03` (`access`)
- **Agent:** `metadata-builder`; settled by `build-doc-keeper` in this documentation pass
- **Kind:** design trade-off — an ungrounded formatting choice, closed by org validation
- **What was recorded:** `deploy-order.md` named the element order inside each `Profile` root (`applicationVisibilities`, `custom`, `description`, `layoutAssignments`, `recordTypeVisibilities`, `userLicense`) as a builder choice that neither cited skill's own worked example follows consistently, and stated at build time that "no mock deploy in this build has exercised a Profile."
- **What settled it:** `reports/MOCK-DEPLOY-M2.md` "Run 2" validated all three profiles, written in exactly this order, with 0 errors. The Metadata API accepted the ordering as deployed.
- **Alternative rejected:** none attempted — the open question was whether element order is enforced at all on a `Profile`, and the deploy result answers it for this shape without a second ordering ever having been tried.
- **What remains open:** this is one successful case, not a documented Metadata API guarantee, and neither cited skill states whether `Profile` element order is enforced in general — the gap in the library still stands even though this build's own question is settled.
- **Grounded in:** `reports/MOCK-DEPLOY-M2.md` § "Run 2"; `artefacts/M2-S03/deploy-order.md` § "Elements this step could NOT ground", item 2.
- **Evidence:** `artefacts/M2-S03/profiles/*.profile-meta.xml`; `reports/MOCK-DEPLOY-M2.md`.

## D-M2S03-03 — `personAccountDefault` omitted: Person Accounts was never asked about, and the mock deploy does not settle it

- **Date:** 2026-09-12
- **Step:** `M2-S03` (`access`)
- **Agent:** `metadata-builder`
- **Kind:** design trade-off — an omission recorded rather than an absence left to be noticed
- **What was recorded:** none of the three profiles carries a `<personAccountDefault>` element. Both cited skills document the element; `admin/record-types-and-page-layouts` calls Person Account record types "a separate model" and carries the Questions-to-Ask row "Are Person Accounts enabled on this org?" (SKILL.md line 62).
- **Alternative rejected:** writing the element on the assumption Person Accounts is off. Rejected because no answered clarification and no line of `requirement.md` says either way — an assumed value here would be the agent's own, not a grounded one.
- **Why the mock deploy does not close this one, unlike `D-M2S03-01`/`-02`:** a successful deploy that omits an optional element says nothing about whether the org the element would matter in actually has Person Accounts enabled. This is a missing **answer**, not a pairing the platform could confirm or reject by accepting the file.
- **Grounded in:** `skills/admin/record-types-and-page-layouts/SKILL.md` line 62 (Questions-to-Ask); `artefacts/M2-S03/deploy-order.md` § "Elements this step could NOT ground", item 1.
- **Evidence:** `artefacts/M2-S03/profiles/*.profile-meta.xml` (no `personAccountDefault` on any). See also **O-M2S03-02** below, which files this alongside the same skill's twin unanswered question on managed packages.

## D-M2S03-04 — Q11's "clone Standard User" is superseded at API 60+ by Minimum Access seeding

- **Date:** 2026-09-12
- **Step:** `M2-S03` (`access`)
- **Agent:** `metadata-builder`
- **Kind:** deviation from an answered clarification, recorded as a case where the grounded platform behaviour is better than the literal instruction
- **What was recorded:** Q11's answer reads "Clone Standard User into custom profiles before any deploy is attempted." `skills/admin/permission-sets-vs-profiles/references/gotchas.md` ("Profile Deployment Overlays; It Does Not Replace") states that deploying a profile name that does not already exist in the target org, with no source profile to clone from, seeds it from **Minimum Access - Salesforce** at API 60.0 and later — not from a Standard User clone, which was the pre-60.0 behaviour. This manifest's `<version>` is `62.0`.
- **What Q11's answer actually turns on:** `<custom>true</custom>`, which all three files carry regardless of which base the org seeds from. There is no metadata element that names a clone lineage — profile inheritance from another profile is not something the Metadata API sets.
- **Alternative rejected:** none was available to try — Q11's literal instruction is not expressible as a metadata element at this API version, so there was nothing to write differently to honour it more closely.
- **Grounded in:** `skills/admin/permission-sets-vs-profiles/references/gotchas.md` ("Profile Deployment Overlays; It Does Not Replace", and its companion "Cloned Profiles Are Not Clean Slates," which is the reason the grounded outcome is judged cleaner than the literal one); `artefacts/M2-S03/deploy-order.md` § "Elements this step could NOT ground", item 4.
- **Decision required at the M2 gate — a human's, not this agent's:** accept that Q11's answer is satisfied by `<custom>true</custom>` and superseded on the clone-lineage half by platform behaviour, or treat the divergence as something a re-plan should restate.
- **Evidence:** `artefacts/M2-S03/profiles/*.profile-meta.xml` (`<custom>true</custom>` on all three, no clone-lineage element anywhere); `artefacts/M2-S03/deploy-order.md`.

## D-M2S03-05 — A profile deploy overlays an existing org profile of the same name; it does not replace it

- **Date:** 2026-09-12
- **Step:** `M2-S03` (`access`)
- **Agent:** `metadata-builder`
- **Kind:** design trade-off — a platform-behaviour risk recorded rather than silently carried
- **What was recorded:** if the target org already holds a profile named `Acme Support Tier 1`, `Acme Support Tier 2` or `Acme Billing`, deploying these three files overlays the existing profile rather than resetting it — whatever that profile already grants survives the deploy, because a profile deploy is not a strip.
- **Alternative rejected:** none — this is documented platform behaviour (the same gotcha `D-M2S03-04` cites), not a design choice this step could make differently, and no artefact-level fix exists inside `artefacts/M2-S03/` for it.
- **Grounded in:** `skills/admin/permission-sets-vs-profiles/references/gotchas.md` ("Profile Deployment Overlays; It Does Not Replace"); `artefacts/M2-S03/deploy-order.md` § "Elements this step could NOT ground", item 4.
- **Consequence, stated for the gate:** a human should confirm, before deploying, whether any of the three profile names already exists in the target org; if one does, its current grants are inherited into the deploy rather than reset to what these three files alone describe.
- **Evidence:** `artefacts/M2-S03/deploy-order.md`.

## D-M2S03-06 — Rebuild #2: description-length fix for mock-deploy finding F-15

- **Date:** 2026-09-12
- **Step:** `M2-S03` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T01:16:41Z`), claimed by `build-step-runner` (run `2026-09-12T01-17-55Z`, executed inline per the operator's narrow-scope instruction) and re-tested by `step-tester` (run `2026-09-12T01-23-34Z`)
- **Kind:** deviation — the step was rebuilt after a real org rejection, for a rule no checker enforced at build #1 time
- **Why the rebuild happened:** `reports/MOCK-DEPLOY-M2.md` "Run 1" (**F-15**, HIGH). All three `Profile` files were rejected by the org with `Description: data value too large … (max length=255)` — descriptions of 280, 279 and 407 characters, following the cited skills' own examples, which at that time carried no length rule. `check_access_model.py --manifest-dir artefacts/M2-S03` had exited 0 on the pre-rebuild files, because the checker carried no description-length rule yet.
- **What changed — one element, three files, nothing else:** only the `<description>` element of each profile was rewritten, to 152, 152 and 147 characters respectively (all under the new 200-char WARN line, not merely the 255-char ERROR line). Every other element in all three files is byte-identical before and after, confirmed by SHA-256 of the whole file plus a line diff (`envelopes/M2-S03/2026-09-12T01-17-55Z.md` § "Byte-identity proof"). The rationale each old description carried was not discarded — it already duplicated `deploy-order.md`'s own "Decisions worth reading before deploy" section and is now recorded once, in that file's new "Rebuild #2 — descriptions" section.
- **Source the rebuild rests on:** `skills/admin/permission-sets-vs-profiles` v1.2.0 (2026-09-11) added the Metadata API's 255-character `Profile.description` / `PermissionSet.description` ceiling to `references/metadata-examples.md` § "Description length," and `check_access_model.py` gained **PSVP-DESC-01** (ERROR, ≥255 chars) and **PSVP-DESC-02** (WARN, ≥200 chars, headroom). Reproducing the fixed checker against the rejected originals returns exit 1 with three `PSVP-DESC-01` findings; against the rebuilt files it returns exit 0 with none.
- **Alternative rejected:** editing the deployed org copy or leaving the finding as a deploy-time caveat. Refused rather than deferred, the same reasoning `D-M1S02-05` and `D-M1S01-05` give for their own rebuilds: `standards/build-orchestration.md` § 8 makes deepening the skill the remedy for a knowledge gap, and the step was re-run through the ordinary runner path against the fixed skill.
- **What this closes:** mock-deploy finding **F-15**, confirmed by the org itself — `reports/MOCK-DEPLOY-M2.md` "Run 2" validates all three rebuilt profiles (plus the four `M2-S02` permission sets rebuilt for the same finding) with 0 errors.
- **Grounded in:** `reports/MOCK-DEPLOY-M2.md` §§ "Run 1" and "Run 2"; `skills/admin/permission-sets-vs-profiles` v1.2.0; `artefacts/M2-S03/deploy-order.md` § "Rebuild #2 — descriptions"; `envelopes/M2-S03/2026-09-12T01-17-55Z.json`.
- **Evidence:** `artefacts/M2-S03/profiles/*.profile-meta.xml`; `tests/M2-S03/results.json` (`"passed": true`, 4 ran, 0 failed, 0 manual — the re-test after this rebuild).

## D-M2S03-07 — M1 finding F-01 is CLOSED by this step; the M1 reports' pointer correction is now moot rather than merely wrong

- **Date:** 2026-09-12
- **Step:** `M2-S03` (`access`)
- **Agent:** `build-doc-keeper` (this run), reading `reports/MILESTONE-M1-REPORT.md`, `reports/MILESTONE-M1-REPORT-v2.md`, `tests/M2-S03/results.json` and `envelopes/M2-S03/2026-09-12T01-23-34Z.md`
- **Kind:** deviation — a finding both M1 reports carried as open is resolved by a later step's own artefacts, not by an edit to either report
- **What was recorded:** `reports/MILESTONE-M1-REPORT.md` ("v1") named **F-01** (HIGH) — "the record-type ↔ layout binding is asserted nowhere in M1, including by M1's own milestone test" — and pointed its remedy at `M2-S01`. `reports/MILESTONE-M1-REPORT-v2.md` corrected the pointer to `M2-S03` (the step that actually declares `Profile` outputs) but still recorded F-01 itself as **open**, because no `Profile` file existed yet to carry `layoutAssignments`. `decisions.md` **O-M2S01-01** records the same pointer correction from the build side.
- **What closes it now:** with `M2-S03` `tested`, `check_record_type_layouts.py --manifest-dir artefacts --strict` resolves **9 `layoutAssignments` references and 12 record-type references** across the whole build tree and exits 0 with 0 findings (`tests/M2-S03/results.json`; `envelopes/M2-S03/2026-09-12T01-23-34Z.md`) — a negative fixture with one dangling reference exits 1 under the same flag. The assertion F-01 said was never made anywhere in the tree is now actually made, and it passes.
- **What this does NOT do:** rewrite either M1 report or the `milestone:M1` / `step:M2-S01` gate notes. Both reports are `milestone-verifier`'s and no other writer touches them (`standards/build-orchestration.md` § 2); the gate notes are written records of a human decision and are not rewritable by any agent (the same rule `O-M1S02-03` and `O-M2S01-01` both state). This agent does not touch `plan.json` beyond its own status transition either.
- **Why `O-M2S01-01`'s own remedy is now moot, not merely satisfied:** that entry asked for F-01's *pointer* to be corrected from `M2-S01` to `M2-S03` in a future milestone report. The finding it was pointing at is no longer open at all, so re-pointing a still-open finding is not the applicable fix any more — the next re-verification should record F-01 **CLOSED**, sourced to this step, rather than re-pointed.
- **What remains for the planner/verifier:** `milestone:M1` was approved against pre-rebuild artefacts and is already flagged stale for an unrelated reason (`O-M1S02-03`, rebuild #2/#3). This entry adds that the same re-verification, whenever it runs, should also record F-01's closure — one re-verification, two things for it to state.
- **Grounded in:** `reports/MILESTONE-M1-REPORT.md` § 10 (F-01); `reports/MILESTONE-M1-REPORT-v2.md` § 10 (F-01, `O-M2S01-01` row); `decisions.md` **O-M2S01-01**; `artefacts/M2-S03/deploy-order.md` (opening line, "This step closes M1 finding F-01").
- **Evidence:** `tests/M2-S03/results.json`; `envelopes/M2-S03/2026-09-12T01-23-34Z.md` § "Checker output (verbatim)".

---

# Open items for the planner — raised by the M2-S03 documentation run

Same standing as every section above: plan-file text and plan-file declarations, and
`standards/build-orchestration.md` § 2 gives `build_plan.py` sole authority over them. None blocks
the step — `M2-S03` passed every executable test it declares, twice (before and after Rebuild #2).

## O-M2S03-01 — `acceptance_tests[1]`'s description predicts "Scanned 14 metadata file(s)"; the real run prints 15

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the `metadata-builder` rebuild
  envelope and the `step-tester` re-test envelope, which report it independently
- `plan.json` → `steps[M2-S03].acceptance_tests[1].description` states that the build-scope run
  "printed 'Scanned 14 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s) detected.'"
  Both `envelopes/M2-S03/2026-09-12T01-17-55Z.md` and `envelopes/M2-S03/2026-09-12T01-23-34Z.md`
  record the same command printing **`Scanned 15 metadata file(s)`** against the same tree.
- **The declared `expected` still holds** — exit 0, 0 findings — because the count is in the
  description's descriptive prose, not in the pass condition `--strict` enforces. Only the number is
  stale.
- **Not reconciled here:** this run does not attempt to identify which specific file changed the
  scanned count between whenever the description was authored and now — the description predates
  this step's own build, and re-deriving its history is a v6 planner task, not a documentation one.
- **Remedy at v6:** reword the description to "15".
- **Evidence:** `plan.json` `steps[M2-S03].acceptance_tests[1].description`;
  `envelopes/M2-S03/2026-09-12T01-17-55Z.md`; `envelopes/M2-S03/2026-09-12T01-23-34Z.md`.

## O-M2S03-02 — Two Questions-to-Ask rows go unanswered by any clarification: managed packages and Person Accounts

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, cross-checking both cited skills'
  Questions-to-Ask sections against all 97 entries in `plan.json.clarifications[]`
- `skills/admin/permission-sets-vs-profiles` SKILL.md carries "Does a managed package require this
  profile to be assigned?" (line 61); `skills/admin/record-types-and-page-layouts` SKILL.md carries
  "Are Person Accounts enabled on this org?" (line 62). Neither question is answered by any
  clarification in this plan — `Q12` (employees only, no customer portal in this phase) is the
  nearest adjacent answer and settles neither.
- **Consequence:** the three profiles were built on the unstated assumption that no managed package
  forces a profile assignment and that Person Accounts is not enabled (`decisions.md` **D-M2S03-03**
  records the Person Accounts half; no `<licensePermission>`-style managed-package exception exists
  on any of the three files either).
- **Remedy at v6:** add both questions to a future clarification round, or record a confirmed
  "neither applies" as an assumption if the target org is known.
- **Grounded in:** `skills/admin/permission-sets-vs-profiles/SKILL.md` line 61;
  `skills/admin/record-types-and-page-layouts/SKILL.md` line 62; `plan.json.clarifications[]` (all
  97 checked, none answers either question).
- **Evidence:** `artefacts/M2-S03/profiles/*.profile-meta.xml` (no managed-package exception note, no
  `personAccountDefault`, on any of the three).

## O-M2S03-03 — Assumption A1 still does not list `M2-S03`, though this step's `recordTypeVisibilities`/`layoutAssignments` split is shaped by it

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, extending the same gap already recorded
  for `M1-S01` (`decisions.md` **W03**) and `M2-S02` (**O-M2S02-03**)
- `plan.json` → `assumptions[A1].steps[]` reads `["M2-S05"]` only. All three of this step's profiles
  carry the conservative reading A1 states: `Acme Billing` marks `Case.Support` `visible=false`,
  `Acme Support Tier 1`/`Tier 2` mark `Case.Billing` `visible=false` — the same mirror-image
  default/visibility split `traceability.md` rows `REQ-018`–`020` already record for
  `Case_Tier1`/`Case_Tier2`/`Case_Billing`, one layer up the access stack.
- **Not the mechanism that makes A1 true**, the same caveat `traceability.md`'s M1-S01 and M2-S02
  sections both already state: the actual restriction is the Private OWD (`M1-S01`) plus `M2-S05`'s
  sharing rule; `recordTypeVisibilities` and `layoutAssignments` govern selection and layout, not
  whether an existing record can be opened.
- **Remedy at v6:** add `M2-S03` to `A1.steps[]` — the third instance of the same open item, after
  `M1-S01` and `M2-S02`.
- **Evidence:** `plan.json` `assumptions[A1]`; `artefacts/M2-S03/profiles/*.profile-meta.xml`
  (`recordTypeVisibilities` blocks); `artefacts/M2-S03/deploy-order.md` § "Decisions worth reading
  before deploy", item 2.

---

## D-M2S05-01 — No sharing rule targets Billing; Billing reaches its own cases as queue owner, a different mechanism, reconcile at the gate

- **Date:** 2026-09-12
- **Step:** `M2-S05` (`access`)
- **Agent:** `metadata-builder` (build run `2026-09-12T01:24:36Z`); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a deliberate absence, named rather than left to be noticed
- **What was recorded:** `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml` carries exactly
  one `sharingCriteriaRules` block, targeting `Support_Tier_2` on `RecordTypeId equals Support`. No
  rule names `Billing_Team` or the Billing record type. This is not an oversight: Billing's own
  access to Billing cases is **queue ownership**, through the `Billing` queue `M2-S04` built —
  `Case_Intake_Integration` (M2-S01) creates the case, `M3-S04`'s assignment rules (pending) transfer
  ownership to the `Billing` queue, and queue-owned records are visible to queue members without any
  sharing rule.
- **Alternative rejected:** writing a second criteria rule sharing Billing-record-type cases to
  `Billing_Team`. Rejected because it would be redundant with the ownership path Billing already has,
  and because `requirement.md` and the 97 clarifications describe Billing's access as *doing the
  work*, not as needing visibility into cases it does not own — the same gap a second finance
  reviewer or a manager would create, which is not asked for anywhere on file.
- **What remains open, for the planner, before G3:** the requirement's Billing sentences (L8, L19)
  and Q1's answer are all served by two different mechanisms across two different steps (`M2-S04`
  ownership, `M2-S05`'s deliberate absence of a rule), and nothing in `plan.json` states the two are
  meant to compose into one coherent answer for Billing. Recorded as **O-M2S05-01** below.
- **Grounded in:** `artefacts/M2-S05/deploy-order.md` § "Elements this step could NOT ground", item 1;
  `artefacts/M2-S05/case-visibility-model.md` § "How each team actually reaches a case".
- **Evidence:** `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml` (one rule, no Billing
  reference outside the free-text `<description>`); `artefacts/M2-S04/queues/Billing.queue-meta.xml`.

## D-M2S05-02 — `package.xml` manifests the rule under the container form; the cited skill recommends the rule-type form

- **Date:** 2026-09-12
- **Step:** `M2-S05` (`access`)
- **Agent:** `metadata-builder`
- **Kind:** design trade-off — a real divergence from the cited skill's own worked example, driven by
  this step's own declared acceptance test
- **What was recorded:** `artefacts/M2-S05/package.xml` names `<members>Case</members>` under
  `<name>SharingRules</name>` — the container form. `skills/admin/sharing-and-visibility/references/
  metadata-examples.md` § 6 states plainly: "`SharingRules` itself does not support the wildcard and
  is not what you address. Manifest the concrete rule types: `SharingCriteriaRule` and
  `SharingOwnerRule`, with members shaped `Object.RuleName`" — which here would be
  `<members>Case.Support_Cases_To_Tier_2</members>` under `<name>SharingCriteriaRule</name>`.
- **Why the container form was written anyway:** this step's declared `manifest` acceptance test
  names "`SharingRules:Case` as its own `<name>` block", and `step-tester` derives the member from
  the artefact's file name (`sharingRules/Case.sharingRules-meta.xml` → type `SharingRules`, member
  `Case`) rather than from its `<fullName>`. Writing the rule-type form would leave the file uncovered
  by the declared test *and* declare a manifest member with no file the tester's derivation logic
  would find.
- **Alternative rejected:** writing the rule-type form and amending the step's `manifest` test
  description to match. Not applied in this pass — amending a step's declared `acceptance_tests[]`
  is `build_plan.py amend-step`'s job, scoped to a `pending`/`blocked` step, and `M2-S05` is `tested`
  (moving to `documented` in this pass), so the amendment window for this step has closed per
  `standards/build-orchestration.md` § 2.
- **What settles it either way:** `reports/MOCK-DEPLOY-M2.md` Run 3 validated the artefact **as
  built** (32/32 components, 0 errors) — both forms are known to deploy; the question is manifest
  style and which form the tester's derivation logic expects, not deployability.
- **Two other skills in the library already manifest the container form** with an object as the
  member (`admin/experience-cloud-guest-access`, `admin/data-skew-and-sharing-performance`), so this
  step is not inventing a form nobody else in the library uses — it is following the more common
  precedent over the one skill that documents the alternative explicitly.
- **Grounded in:** `skills/admin/sharing-and-visibility/references/metadata-examples.md` § 6;
  `artefacts/M2-S05/deploy-order.md` § "Decisions worth reading before deploy", item 1.
- **Evidence:** `artefacts/M2-S05/package.xml`; `reports/MOCK-DEPLOY-M2.md` § "Run 3".

## D-M2S05-03 — `RecordTypeId` criteria value in bare developer-name form: UNVERIFIED in the skill, validated by the org in Run 3

- **Date:** 2026-09-12
- **Step:** `M2-S05` (`access`)
- **Agent:** `metadata-builder`; settled by `build-doc-keeper` reading `reports/MOCK-DEPLOY-M2.md` in
  this documentation pass
- **Kind:** design trade-off — an ungrounded value format, closed by org validation rather than by a
  cited skill
- **What was recorded:** `artefacts/M2-S05/deploy-order.md` named the `criteriaItems.value` format
  (`Support`, the record type's bare developer name) as **UNVERIFIED**, carrying forward the same
  marker `admin/duplicate-management/references/metadata-examples.md` states verbatim for the same
  field on a different type: whether `RecordTypeId` accepts the developer name or requires an
  18-character Id "is not established by the Metadata API guide." The builder's envelope named this
  as "the single most likely thing in this step to come back from a mock deploy."
- **What settled it:** `reports/MOCK-DEPLOY-M2.md` "Run 3" (2026-09-11) validated the artefact as
  built — 32 components, 0 errors — with `criteriaItems` reading `RecordTypeId equals Support` in
  bare developer-name form. The value format the builder marked as its likeliest failure did not
  fail validation.
- **Alternative rejected:** none attempted — the open question was which format the platform accepts,
  and the deploy result answers it for this shape without a second format ever having been tried.
- **What remains open:** one successful case is not a documented Metadata API guarantee; the
  underlying gap in `admin/duplicate-management`'s own gotcha still stands for the field in general,
  even though this build's own question is settled. Skill-gap signal per
  `standards/build-orchestration.md` § 8: the settlement is worth recording in
  `admin/sharing-and-visibility`'s own element inventory so a future build does not re-open the same
  question from zero.
- **Grounded in:** `reports/MOCK-DEPLOY-M2.md` § "Run 3"; `artefacts/M2-S05/deploy-order.md` §
  "Decisions worth reading before deploy", item 3.
- **Evidence:** `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml`;
  `reports/MOCK-DEPLOY-M2.md`.

## D-M2S05-04 — `doesIncludeBosses` on `Support_Tier_2` widens this grant up any future role hierarchy

- **Date:** 2026-09-12
- **Step:** `M2-S05` (`access`)
- **Agent:** `metadata-builder`
- **Kind:** design trade-off — a platform-behaviour risk recorded rather than silently carried
- **What was recorded:** `Support_Tier_2` (`M2-S04`) carries `<doesIncludeBosses>true</doesIncludeBosses>`
  as a skill default, not an answered clarification. The gotcha this rests on: the field "is set once
  on the group and applies retroactively to every rule that ever targets it" — so this step's `Edit`
  grant to `Support_Tier_2` will travel up any role hierarchy loaded later, without this rule ever
  being touched again.
- **Why this is recorded on `M2-S05` and not only on `M2-S04`:** `M2-S04` recorded the field's default
  on the group itself (`decisions.md` D-M2S04-01); this entry is the consequence of that default for
  a rule built a step later, against a group that already existed. Nobody sits above a Tier 2 engineer
  in this build today, because no role exists yet (`case-visibility-model.md` § "Role hierarchy
  assumptions": "None are made"), so the effect is inert now and stops being inert the day a
  hierarchy is loaded.
- **Alternative rejected:** none — changing `doesIncludeBosses` is `M2-S04`'s file, not this step's,
  and no clarification asks whether the Tier 2 grant should or should not travel up a future
  hierarchy.
- **What remains open:** if Tier 2's Support-case access must not travel up a future role hierarchy,
  the file to change is `artefacts/M2-S04/groups/Support_Tier_2.group-meta.xml`, not this step's
  sharing rule.
- **Grounded in:** `artefacts/M2-S05/deploy-order.md` § "Decisions worth reading before deploy",
  item 6; `decisions.md` D-M2S04-01.
- **Evidence:** `artefacts/M2-S04/groups/Support_Tier_2.group-meta.xml`;
  `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml`.

## D-M2S05-05 — The manual-sharing exception layer has no standing use, and no reviewer is named

- **Date:** 2026-09-12
- **Step:** `M2-S05` (`access`)
- **Agent:** `metadata-builder`
- **Kind:** design trade-off — an omission recorded rather than an absence left to be noticed
- **What was recorded:** `case-visibility-model.md`'s Sharing Grants table carries "Manual sharing —
  Exception layer only; no standing use, and no reviewer named yet" and its Risk Checks section
  states the same fact as "Repeated manual sharing pattern ruled out — there is no existing
  manual-share practice to replace; this is a greenfield intake build." No clarification names who
  reviews a manual share if one is ever created, and no cadence is stated.
- **Alternative rejected:** naming a reviewer role (e.g. "Security architect") without a clarification
  behind it. Rejected because it would be an invented owner for a layer this build does not use —
  the same discipline `agents/build-doc-keeper/AGENT.md` applies to `source_req_id`: a row invented
  for an unstated answer makes the record fiction.
- **What remains open:** if manual sharing is ever used on this object, a reviewer and cadence need
  naming before the first manual share is created, not after.
- **Grounded in:** `artefacts/M2-S05/case-visibility-model.md` § "Sharing Grants", § "Risk Checks".
- **Evidence:** `artefacts/M2-S05/case-visibility-model.md`.

---

# Open items for the planner — raised by the M2-S05 documentation run

Same standing as every section above: plan-file text and plan-file declarations, and
`standards/build-orchestration.md` § 2 gives `build_plan.py` sole authority over them. None blocks
the step — `M2-S05` passed every executable test it declares.

## O-M2S05-01 — Billing's access to its own cases and Tier 1's exclusion from Billing cases are served by two different mechanisms across two different steps, and nothing reconciles them

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, cross-reading
  `artefacts/M2-S04/queues/Billing.queue-meta.xml`, `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml`
  and `artefacts/M2-S05/case-visibility-model.md` against `requirement.md` L8 and L19
- Billing reaches its own cases as **queue owner** (`M2-S04`'s `Billing` queue, once `M3-S04`'s
  assignment rules transfer ownership). Tier 1's exclusion from Billing cases rests on the **absence**
  of a sharing rule naming `Billing_Team` or the Billing record type (`M2-S05`, this step,
  `decisions.md` D-M2S05-01). Both are individually correct and grounded, but no single artefact or
  decision in `plan.json` states that the two are meant to compose into the requirement's whole
  Billing-visibility answer — a reviewer reading only `M2-S05` would not learn that Billing's own
  access comes from a different step entirely.
- **Consequence if left unreconciled:** a future change to `M2-S04`'s queue (e.g. a second Billing
  queue, or removing queue-based ownership in favour of direct assignment) could silently break
  Billing's access to its own cases without touching anything `M2-S05` owns, and nothing in the build
  would flag the connection.
- **Remedy at v6, or before the M2 gate:** a plan-level note (or a decision entry cross-referencing
  both steps) stating explicitly that Billing visibility = queue ownership (`M2-S04`) + no competing
  restriction (`M2-S05`'s deliberate absence), so the two steps' artefacts are read together rather
  than independently at the gate.
- **Evidence:** `artefacts/M2-S04/queues/Billing.queue-meta.xml`;
  `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml`; `requirement.md` L8, L19.

## O-M2S05-02 — Correction of record: `M1-S01`'s `CWB-SHARE-001` and `REQ-010` both state the build-scope `check_sharing_model.py` assertion "has not run"; it ran in this pass and passed

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from this run's own
  `check_sharing_model.py --manifest-dir artefacts` result
- `workbook/04-sharing-settings.md` `CWB-SHARE-001`'s notes cell and `traceability.md` `REQ-010`'s
  `test_result` cell both state, verbatim, that "the machine assertion that the OWD is not looser
  than the sharing rule's grant is `M2-S05`'s build-scoped `check_sharing_model.py` test, which needs
  both files and has not run." This run's own `M2-S05-T1` execution of that exact command
  (`check_sharing_model.py --manifest-dir artefacts`) exited 0 with 1 object OWD resolved and 0
  findings — the assertion has now run, and it passed.
- **What this does NOT do:** rewrite `CWB-SHARE-001` or `REQ-010`. Both belong to `M1-S01`, and
  `agents/build-doc-keeper/AGENT.md` Step 8 restricts a per-step run to its own step's rows —
  `M2-S05`'s doc-keeper pass touches only `M2-S05`'s rows and this decisions-log append. Correcting
  the two stale sentences is `M1-S01`'s doc-keeper's edit to make, on a future re-render or rebuild
  of that step, not this run's.
- **Remedy:** the next time `M1-S01` is touched (a rebuild, or a v6 planning pass), update
  `CWB-SHARE-001`'s notes and `REQ-010`'s `test_result` to state that the build-scope check has run
  and passed, citing this entry and `M2-S05`'s own `REQ-029` row as the evidence.
- **Evidence:** `tests/M2-S05/results.json`; `envelopes/M2-S05/2026-09-12T01-41-33Z.md`;
  `workbook/04-sharing-settings.md` `CWB-SHARE-001`; `traceability.md` `REQ-010`.

---

## D-M3S01-01 — DX file suffix and directory for `ValidationRule` carried forward as UNVERIFIED, not resolved by this step

- **Date:** 2026-09-12
- **Step:** `M3-S01` (`validation`)
- **Agent:** `metadata-builder`; recorded here by `build-doc-keeper`
- **Kind:** design trade-off — an inherited library gap, named rather than silently relied on
- **What was recorded:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded" item 1
  carries forward `skills/admin/validation-rules/references/metadata-examples.md`'s own marker:
  "UNVERIFIED (2026-09-04): the Metadata API Developer Guide documents only the metadata-format
  `.object` layout; the string `validationRule-meta` does not appear anywhere in it." The
  **element names and semantics** (`fullName`, `active`, `description`, `errorConditionFormula`,
  `errorDisplayField`, `errorMessage`) are confirmed by the guide's field table and are identical
  in both metadata shapes.
- **Why this build proceeds anyway:** `plan.json` declares the DX path for this build, so the
  file layout is the plan's choice, not a fact this step had to establish. Both artefact files
  parsed (`xml`, exit 0) and the declared checker read them without error.
- **What remains open:** the DX suffix itself is still not confirmed against the Metadata API
  Developer Guide. Skill-gap signal per `standards/build-orchestration.md` § 8, same skill and
  same marker `decisions.md` has carried since before this build reached M3.
- **Grounded in:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded", item 1;
  `skills/admin/validation-rules/references/metadata-examples.md`.
- **Evidence:** `tests/M3-S01/xml_result.json` (3/3 parsed).

## D-M3S01-02 — `Object.RuleName` manifest member form: UNVERIFIED in the skill, corroborated by this build's own manifest checker and one prior org validation, neither of which is `ValidationRule`-specific evidence

- **Date:** 2026-09-12
- **Step:** `M3-S01` (`validation`)
- **Agent:** `metadata-builder`; recorded here by `build-doc-keeper`
- **Kind:** design trade-off — an ungrounded manifest form, corroborated by analogy rather than
  by a `ValidationRule` deploy
- **What was recorded:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded" item 2:
  the cited skill's own reference marks the `Object.RuleName` form UNVERIFIED for `ValidationRule`
  — the guide shows the pattern for `CustomField`/`ListView` sub-components of `CustomObject` and
  no `ValidationRule` manifest sample. `Case.Priority_Required_On_Agent_Save` follows the
  documented sub-component pattern by analogy.
- **What corroborates it, and what it does not prove:** `M1-S01`'s manifest already uses the same
  form for `RecordType` and `CustomField` members and validated against an org
  (`reports/MOCK-DEPLOY-M2.md` run 2, 30 components, 0 errors) — evidence for the pattern in
  general, not for `ValidationRule` specifically. This build's own `manifest` acceptance test
  passed on both files, which confirms internal two-way consistency, not that the platform
  accepts this exact member type/name pairing.
- **Alternative rejected:** none attempted — no second manifest form was trialled for this build.
- **What remains open:** the same skill-gap `admin/validation-rules` has carried since M3-S01 was
  built; only an actual `ValidationRule` deploy (a future `mock_deploy.py` run against M3) closes
  it, the way Run 3 closed the analogous `RecordTypeId` question for `admin/sharing-and-visibility`
  in `decisions.md` **D-M2S05-03**.
- **Grounded in:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded", item 2;
  `reports/MOCK-DEPLOY-M2.md` run 2.
- **Evidence:** `artefacts/M3-S01/package.xml`; `tests/M3-S01/summary.md` § "Manifest derivation".

## D-M3S01-03 — No documented cap on `ValidationRule.description`; both descriptions held under 200 characters as a cross-type precaution, not a documented limit

- **Date:** 2026-09-12
- **Step:** `M3-S01` (`validation`)
- **Agent:** `metadata-builder`; recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a precaution inferred from a different metadata type's org
  rejection, named as such rather than presented as a `ValidationRule` rule
- **What was recorded:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded" item 3: the
  skill's element table gives `errorMessage` an explicit 255-character ceiling and says only
  "free text" for `description`. Both rule descriptions are 188 and 185 characters
  (`envelopes/M3-S01/2026-09-12T03-19-00Z.md` § "The two rules"), held under 200 as a precaution
  inferred from `reports/MOCK-DEPLOY-M2.md` finding **F-15**, where `PermissionSet.description`
  and `Profile.description` failed an org validate over 255.
- **Alternative rejected:** writing longer, more narrative descriptions with no length discipline.
  Rejected because F-15 already showed this org enforces a description cap on at least two other
  metadata types, and there is no cost to staying well under it here.
- **What remains open:** this is a cross-type inference, not a documented `ValidationRule` limit —
  the same caveat `decisions.md` D-M2S05-02/03 apply to other inferred-from-elsewhere facts in
  this build. Skill-gap signal per § 8 for `admin/validation-rules`'s own element inventory.
- **Grounded in:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded", item 3;
  `reports/MOCK-DEPLOY-M2.md` finding F-15.
- **Evidence:** `artefacts/M3-S01/objects/Case/validationRules/*.validationRule-meta.xml`
  (`<description>` elements).

## D-M3S01-04 — Whether an out-of-set `Origin` value can reach the field at all is undocumented; the enumerated clause is written anyway, on the safe (redundant, not permissive) side

- **Date:** 2026-09-12
- **Step:** `M3-S01` (`validation`)
- **Agent:** `metadata-builder`; recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a formula clause that may be redundant, kept rather than dropped,
  with the reasoning named
- **What was recorded:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded" item 4:
  the blank half of `Origin_Must_Be_Known` is plainly grounded; whether a value **outside**
  `CaseOrigin`'s three active values can reach `Origin` at all — through the API, or as a
  retained inactive standard value — is documented in neither cited skill. The three values
  tested are read off `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml`,
  so the clause is correct about what is allowed; it may be redundant if the platform already
  rejects everything else.
- **Alternative rejected:** dropping the `NOT(OR(ISPICKVAL(...)))` half and testing only for
  blank. Rejected because redundant is the safe direction here, and the shape is the documented
  one for a picklist inequality (`skills/admin/validation-rules/references/llm-anti-patterns.md`
  Anti-Pattern 6).
- **What remains open:** same skill-gap as D-M3S01-01/02, recorded once more against a different
  fact — whether the platform enforces `CaseOrigin` membership independent of this rule.
- **Grounded in:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded", item 4;
  `artefacts/M1-S01/standardValueSets/CaseOrigin.standardValueSet-meta.xml`.
- **Evidence:** `artefacts/M3-S01/objects/Case/validationRules/Origin_Must_Be_Known.validationRule-meta.xml`.

## D-M3S01-05 — A12 (Q55 deferred): whether these rules are invariants depends on an assumed sole post-save writer that does not exist yet

- **Date:** 2026-09-12
- **Step:** `M3-S01` (`validation`)
- **Agent:** `metadata-builder`; recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a platform-behaviour risk recorded rather than silently carried
- **What was recorded:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded" item 5: both
  rules are correct at the moment of save; what is unproven is that they are *unbypassable* after
  save. Custom validation rules are not re-run after a workflow field update re-saves a record
  (`skills/admin/validation-rules/references/gotchas.md`). `M4-S03`'s before-save stamping flow
  (`decisions.md` D1) is assumed to be the sole writer of `Priority`/`Origin` after creation, and
  `M4-S03` is not yet built, so the assumption cannot be confirmed from this build's own artefacts.
- **Alternative rejected:** none — resolving this requires `M4-S03` to exist and be read, which is
  outside this step's `depends_on`.
- **What remains open:** the same item `tests/M3-S01/results.json`'s tester envelope names under
  "Ambiguous": M4-S03 is the step to re-check this assumption against once it lands.
- **Grounded in:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded", item 5;
  `plan.json` `assumptions[A12]`; `decisions.md` D1.
- **Evidence:** `plan.json` `steps[M3-S01].inputs.assumptions` (`A11`, `A12`, `A13`).

## D-M3S01-06 — The step's declared checker test description overclaims: `check_validation_rules.py` verifies neither field-token resolution nor `errorDisplayField` resolution

- **Date:** 2026-09-12
- **Step:** `M3-S01` (`validation`)
- **Agent:** `metadata-builder`, named in its own envelope's Concerning observation;
  independently re-confirmed by `step-tester` from the checker's source; recorded here by
  `build-doc-keeper`
- **Kind:** design trade-off — a gap between what a declared acceptance test's `description`
  claims and what its command actually asserts, named rather than left for a reader to discover
  by reading the checker source themselves
- **What was recorded:** `plan.json` `steps[M3-S01].acceptance_tests[0].description` states the
  checker verifies "every field token in every formula resolves" and "an `errorDisplayField` that
  resolves." `skills/admin/validation-rules/scripts/check_validation_rules.py` does neither — it
  has no field inventory and no describe/cross-check logic anywhere in the script; it inspects
  only formula and message text. `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded"
  item 6 names this first; `envelopes/M3-S01/2026-09-12T03-28-00Z.md` (step-tester) independently
  confirms it by reading the checker source end to end, arriving at the same conclusion from a
  different direction.
- **What is NOT missing:** the fields do resolve. `Priority` and `Origin` are real fields on
  `Case` (standard fields, present since `M1-S01`), and `$Permission.Bypass_Case_Intake_Validation`
  resolves to the real Custom Permission built in `M2-S01` — both checked by hand against
  `M1-S01`, `M1-S02` and `M2-S01`'s artefacts while this step was built and again while it was
  documented. What is missing is that the exit code does not carry that confirmation: a rename
  or a typo in either field name would still exit 0.
- **Alternative rejected:** amending the step's `acceptance_tests[0].description` to state
  accurately what the checker checks. Not applied in this pass — amending a step's declared
  `acceptance_tests[]` is `build_plan.py amend-step`'s job, scoped to a `pending`/`blocked` step,
  and `M3-S01` is `tested` (moving to `documented` in this pass), so the amendment window for this
  step has closed per `standards/build-orchestration.md` § 2.
- **What remains open:** two things, kept distinct — (1) the plan's own test description is wrong
  and should be corrected at the next re-plan (**O-M3S01-01** below); (2)
  `check_validation_rules.py` genuinely has no field-inventory logic, which is a real capability
  gap in the checker itself, not only a wording problem in this plan — skill-gap signal per
  `standards/build-orchestration.md` § 8 for `admin/validation-rules` (**O-M3S01-02** below).
- **Grounded in:** `artefacts/M3-S01/deploy-order.md` § "Marked as ungrounded", item 6;
  `envelopes/M3-S01/2026-09-12T03-19-00Z.md` § "Concerning"; `envelopes/M3-S01/2026-09-12T03-28-00Z.md`
  § "Concerning".
- **Evidence:** `skills/admin/validation-rules/scripts/check_validation_rules.py` (read end to
  end by both the builder and the tester); `tests/M3-S01/checker_stdout.txt` (0 findings, which
  is what a rename would also have produced).

---

# Open items for the planner — raised by the M3-S01 documentation run

Same standing as every section above: plan-file text and plan-file declarations, and
`standards/build-orchestration.md` § 2 gives `build_plan.py` sole authority over them. None
blocks the step — `M3-S01` passed every executable test it declares.

## O-M3S01-01 — Correct `steps[M3-S01].acceptance_tests[0].description`: the checker does not verify field-token or `errorDisplayField` resolution

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `decisions.md` **D-M3S01-06**
- The description's claim ("verifies... every field token in every formula resolves" and "an
  `errorDisplayField` that resolves") does not describe `check_validation_rules.py`'s actual
  behaviour. Left uncorrected, a future reader of `PLAN.md` will believe the green exit code
  proves something it does not.
- **Remedy:** at the next re-plan (v6+), rewrite the description to state what the checker
  actually checks — formula and message text, the compound-field ban, the blank-guard REVIEW
  rule under `--strict`, duplicate `fullName`, `RecordType.Name` usage, and the 255-character
  message cap — and note separately that field/permission resolution was confirmed by hand
  against `M1-S01`/`M1-S02`/`M2-S01`.
- **Evidence:** `plan.json` `steps[M3-S01].acceptance_tests[0].description`;
  `skills/admin/validation-rules/scripts/check_validation_rules.py`.

## O-M3S01-02 — Skill-depth signal: `admin/validation-rules`' checker has no field-reference resolution logic

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `decisions.md` **D-M3S01-06**
- Distinct from O-M3S01-01: even a corrected test description would still leave a real gap —
  `check_validation_rules.py` cannot catch a validation rule that references a field that does
  not exist, or a `$Permission` name that is misspelled, because it never inspects anything but
  the two files it is pointed at. Every build that reaches a `validation` step re-derives this
  confirmation by hand, which is exactly the kind of repeated, uninstrumented check
  `docs/reports/skill-depth.md` exists to surface.
- **Remedy:** record `admin/validation-rules` as a candidate for the next depth pass — a
  field-inventory cross-check (reading the object's `CustomField`/standard-field set from the
  same `--manifest-dir` tree, the way `check_permission_set_architecture.py` already cross-checks
  a permission set's grants against object metadata) would close this gap for every future build
  through this layer, not only this one.
- **Evidence:** `skills/admin/validation-rules/scripts/check_validation_rules.py` (no field
  inventory); `docs/reports/skill-depth.md` (the scoreboard this candidate belongs on).

## O-M3S01-03 — Correction of record, in the other direction: `REQ-015`'s "has not run" note on the consumer cross-reference is now partly stale, but not fully closed

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, cross-reading `traceability.md`
  `REQ-015` against `envelopes/M3-S01/2026-09-12T03-19-00Z.md`'s own checker table
- `traceability.md` `REQ-015` (`M2-S01`, `CustomPermission:Bypass_Case_Intake_Validation`) states
  the consumer cross-reference "is M3's milestone test, which runs the same checker at
  `--manifest-dir artefacts --strict` once `M3-S01` writes `Priority_Required_On_Agent_Save` and
  `Origin_Must_Be_Known`." `M3-S01` has now written both. `metadata-builder`'s own build-run
  envelope for this step independently ran `check_custom_permissions.py --manifest-dir artefacts`
  (build scope) as a self-check, not as a declared acceptance test, and got 0 errors, 0 warnings,
  "2 consumers, granted by `Case_Intake_Integration`" — the shape the consumer cross-reference is
  supposed to show.
- **What this does NOT prove:** that self-check was not run by `--strict`'s own declared form
  the way M3-S01's *own* checker command was, and it was never recorded in
  `tests/M3-S01/results.json` or as a milestone-level acceptance test — it is diagnostic evidence
  the builder happened to capture, not the formal cross-step test `standards/build-orchestration.md`
  § 5's Checker scope table describes. That formal test is `milestone-verifier`'s to run once M3
  reaches its gate.
- **What this does NOT do:** rewrite `REQ-015`'s row. It belongs to `M2-S01`, and
  `agents/build-doc-keeper/AGENT.md` Step 8 restricts a per-step run to its own step's rows.
- **Remedy:** when `M2-S01` is next touched, or when `milestone-verifier` runs M3's own
  cross-step test, update `REQ-015`'s `test_result` to record that the consumer count is
  non-zero, citing this entry and the checker table in
  `envelopes/M3-S01/2026-09-12T03-19-00Z.md`.
- **Evidence:** `traceability.md` `REQ-015`; `envelopes/M3-S01/2026-09-12T03-19-00Z.md` §
  "Checker results".

## O-M3S01-04 — Correction of record: `REQ-014`'s note that "no `ValidationRule` metadata exists anywhere under `artefacts/` yet" no longer holds; A13's premise is now checkable for both new rules

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, cross-reading `traceability.md`
  `REQ-014` (`M1-S02`) against `artefacts/M3-S01/`'s two new `ValidationRule` files
- `traceability.md` `REQ-014` states: "no `ValidationRule` metadata exists anywhere under
  `artefacts/` yet — `M3-S01` is `pending` — so there is no `errorDisplayField` to resolve and
  nothing to check against." `M3-S01` now carries exactly two: `Priority_Required_On_Agent_Save`
  (`errorDisplayField` `Priority`) and `Origin_Must_Be_Known` (`errorDisplayField` `Origin`).
  Both fields are `layoutItems` on **both** Case layouts (`artefacts/M1-S02/layouts/*.layout-meta.xml`,
  confirmed again by this run — see `artefacts/M3-S01/validation-bypass-note.md` § "Open items
  this note does not close", A13/Q57), so **assumption A13's premise now holds for both rules
  concretely**, not only in principle. `Severity__c`'s Billing-layout gap that `REQ-014`'s own row
  warns about does not apply here, because neither new rule attaches its error to `Severity__c`.
- **What this does NOT do:** rewrite `REQ-014`'s row, or resolve Q57 (still deferred) or close
  A13 (still `risk: medium` — layout **visibility** per profile remains unreadable from the
  artefacts, per `artefacts/M3-S01/validation-bypass-note.md` § "Open items this note does not
  close", A13/Q57's own final sentence). `REQ-014` belongs to `M1-S02`, and
  `agents/build-doc-keeper/AGENT.md` Step 8 restricts this run to `M3-S01`'s own rows.
- **Remedy:** when `M1-S02` is next touched (a rebuild, or `M1`'s next re-verification), update
  `REQ-014`'s note to record that `M3-S01` has landed and that both its `errorDisplayField`
  values resolve to fields present on both layouts, citing this entry and
  `artefacts/M3-S01/validation-bypass-note.md`.
- **Evidence:** `traceability.md` `REQ-014`; `artefacts/M3-S01/objects/Case/validationRules/*.validationRule-meta.xml`
  (`errorDisplayField` elements); `artefacts/M1-S02/layouts/*.layout-meta.xml`;
  `artefacts/M3-S01/validation-bypass-note.md`.

## D-M3S02-01 — No documented cap on `EmailTemplate`/`EmailFolder.description`; both descriptions held under 200 characters as a cross-type precaution, not a documented limit

- **Date:** 2026-09-12
- **Step:** `M3-S02` (`ui`)
- **Agent:** `metadata-builder`; recorded here by `build-doc-keeper`
- **Kind:** design trade-off — an inherited, cross-type precaution, named rather than silently
  relied on
- **What was recorded:** `artefacts/M3-S02/deploy-order.md` § "Elements and constraints this step
  could NOT ground", item 1: neither cited skill (`admin/email-templates-and-alerts`,
  `admin/email-deliverability-strategy`) states any `description` limit for `EmailTemplate` or
  `EmailFolder`. The 255-character ceiling this step keeps under is carried from this build's own
  mock-deploy finding **F-15** — a different metadata type (`admin` access metadata) — not from a
  cited reference.
- **Why this build proceeds anyway:** nothing here is close to the ceiling either way: the two
  `description` values are 163 and 182 characters, both well under it and under the 200-character
  headroom line F-15 established for this build. The precaution costs nothing to keep.
- **What remains open:** whether `EmailTemplate`/`EmailFolder` actually enforces a `description`
  cap, and at what length, is unconfirmed. Skill-gap signal per `standards/build-orchestration.md`
  § 8 — the same shape `decisions.md` **D-M3S01-03** already records for `ValidationRule`.
- **Grounded in:** `artefacts/M3-S02/deploy-order.md` § "Elements and constraints this step could
  NOT ground", item 1; the M1 mock-deploy finding F-15.
- **Evidence:** `artefacts/M3-S02/email/case_intake/Case_Acknowledgement.email-meta.xml`
  `<description>` (163 chars); `Case_Escalated_To_Tier2.email-meta.xml` `<description>` (182
  chars).

## D-M3S02-02 — Intra-request deploy order (`EmailFolder` before `EmailTemplate`) is an inference, not a quoted rule

- **Date:** 2026-09-12
- **Step:** `M3-S02` (`ui`)
- **Agent:** `metadata-builder`; recorded here by `build-doc-keeper`
- **Kind:** design trade-off — an inferred sequence, corroborated by the cited reference's own
  manifest form rather than by a stated ordering rule
- **What was recorded:** `artefacts/M3-S02/deploy-order.md` § "Elements and constraints this step
  could NOT ground", item 2: neither cited skill states intra-request ordering for `EmailFolder`
  versus `EmailTemplate` on the additive path. What `references/gotchas.md` states explicitly is
  the *deletion* order ("the folder goes last"), and `deploy-order.md`'s additive order (folder,
  then either template) is that same dependency read in reverse.
- **Why this build proceeds anyway:** all three components ship in **one** deploy request — the
  same form the cited reference's own worked `package.xml` uses (`metadata-and-sender-identity.md:83`–`:97`)
  — so no two-deployment split, and no ordering guarantee between components in the same request,
  is actually load-bearing here. The inferred order is recorded as the safe sequence to fall back
  to if the single request is ever split, not as a platform rule this build depends on today.
- **Alternative rejected:** none attempted — no second manifest split was trialled for this build.
- **What remains open:** the same skill-gap `admin/email-templates-and-alerts` carries for
  additive intra-request ordering; only an actual deploy (a future `mock_deploy.py` run against
  M3) would settle it, and nothing in this build's single-request path needs it settled.
- **Grounded in:** `artefacts/M3-S02/deploy-order.md` § "Elements and constraints this step could
  NOT ground", item 2; `skills/admin/email-templates-and-alerts/references/gotchas.md` (deletion
  order); `references/metadata-and-sender-identity.md` (worked manifest).
- **Evidence:** `artefacts/M3-S02/package.xml` (single `<types>` block per metadata type, one
  manifest, one request).

## D-M3S02-03 — No `WorkflowAlert` and no parallel Flow email alert built alongside either template, per Q63's one-event-one-email discipline

- **Date:** 2026-09-12
- **Step:** `M3-S02` (`ui`)
- **Agent:** `metadata-builder`; recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a deliberate omission, grounded in an answered clarification rather
  than a gap
- **What was recorded:** `artefacts/M3-S02/deploy-order.md` § "Elements and constraints this step
  could NOT ground", item 3: this step's `outputs[]` declares no `WorkflowAlert` and no
  `workflows/Case.workflow-meta.xml`. Q63's answer — "one acknowledgement per case creation:
  auto-response only, with no parallel Flow email alert on the same event" — is what rules a
  second, parallel send out, for both the customer acknowledgement (`REQ-032`) and the Tier 2
  handover notice (`REQ-033`).
- **Why this is listed under "could not ground" even though it is grounded:** `references/gotchas.md`
  documents `WorkflowAlert` at length, including that `senderAddress` is legal only with
  `senderType` `OrgWideEmailAddress` — precisely the element type that would have carried a sender
  for these templates had one been built. `deploy-order.md` records this as the pointer for a
  future step that does need a `WorkflowAlert`, not as an unresolved question for this one.
- **Alternatives rejected:** a `WorkflowAlert` mirroring the auto-response send; a `WorkflowAlert`
  mirroring the escalation handover.
- **Consequences:** the only sender element either template will ever have is downstream —
  `M3-S04`'s `AutoResponseRules` entry for the acknowledgement — because this step and its
  deliberately-omitted `WorkflowAlert` both carry none.
- **Grounded in:** `artefacts/M3-S02/deploy-order.md` § "Elements and constraints this step could
  NOT ground", item 3; clarification-answer Q63; `skills/admin/email-templates-and-alerts/references/gotchas.md`
  (`WorkflowAlert` / `senderAddress` / `senderType`).
- **Evidence:** `plan.json` `steps[M3-S02].outputs[]` (no `workflows/` path anywhere in it).

## D-M3S02-04 — M3 gate decision, not to be pre-empted by `M3-S04`: whether `support@acme.example` is itself the Email-to-Case routing address

- **Date:** 2026-09-12
- **Step:** `M3-S02` (`ui`)
- **Agent:** `metadata-builder`; recorded here by `build-doc-keeper`, at the request of the
  builder's own envelope (`envelopes/M3-S02/2026-09-12T03-30-00Z.json` `followups[1]`) and the
  tester's (`envelopes/M3-S02/2026-09-12T03-40-00Z.json` `followups[0]`)
- **Kind:** design trade-off, held open as a milestone-gate decision — the plan carries two
  contradictory readings of one fact, and neither cited skill lets this build pick a side from
  the artefacts alone
- **What was recorded:** `plan.json` clarification **Q22**'s answer states: "yes, from
  `support@acme.example`, for both channels, including the case number... per the answer key:
  support@ (a live routing address) itself sends the acknowledgement." `answers-key.md`'s
  "Acknowledgement" row states the customer acknowledgement is sent "from `support@acme.example`
  (**an org-wide email address, never the Email-to-Case routing address itself**)." These two
  sources describe `support@acme.example` in mutually exclusive terms — one names it a live
  routing address that itself sends the acknowledgement, the other insists it is never the
  routing address.
- **Why this bites, grounded in two skills independently:** `skills/admin/email-templates-and-alerts/references/metadata-and-sender-identity.md`
  § "Org-wide email address (the sender)" — "The auto-response `senderEmail` must match this
  address exactly and must **not** be the Email-to-Case routing address, or the acknowledgement
  re-enters Email-to-Case and loops." `skills/admin/email-to-case-configuration/references/gotchas.md`
  Gotcha 3, "Auto-Response Email Loops When From Address Matches Routing Address" — the mechanism
  is exactly this shape: an auto-response `senderEmail` copied from the routing address, plus a
  mailbox forwarding rule (which `answers-key.md`'s own "Mailbox ownership" row confirms IT holds
  for `support@`/`billing@`), produces an unbounded case-creation loop. Both prohibitions bite
  under Q22's reading and neither bites under the answer key's reading, and this build's own
  `admin/email-to-case-configuration` reference treats the customer-facing address as literally
  the routing address's `<emailAddress>` value — the answer key's "never the routing address
  itself" reading has no citation in either cited skill.
- **Why this step does not resolve it:** `EmailTemplate` carries no sender element at all (the
  element set in `metadata-and-sender-identity.md` — `available`, `description`, `encodingKey`,
  `name`, `style`, `subject`, `type`, `uiType` — has no From address), so no artefact this step
  produces sets, or could set, `senderEmail`. The element that actually decides the question is
  `M3-S04`'s `AutoResponseRules` `ruleEntry.senderEmail`.
- **Decision — recorded as an M3 milestone-gate decision, explicitly not to be pre-empted by `M3-S04`:**
  this build recommends the non-routing reading in practice — i.e., that `M3-S04` set
  `senderEmail` to a **verified org-wide address that is not itself an Email-to-Case routing
  address** (a dedicated address, or a second org-wide address restricted to sending only), which
  is the reading both cited skills' prohibitions are written to protect, and is also Q22's own
  `proposed_default` before the answer key superseded it. `M3-S04` must **not** independently
  decide this by simply copying `support@acme.example` into `senderEmail` because the answer
  key's row appears to bless it — that would resolve the divergence by picking the reading with no
  skill citation, silently, inside a build step, rather than at the human gate this decision names.
  If a human at the M3 gate instead affirms Q22's reading (support@ itself sends it, loop risk
  accepted and covered by the Q68 sandbox loop test), that is a valid outcome too — but it must be
  an explicit gate decision, not `M3-S04`'s default.
- **Alternatives rejected:** silently following the answer key (would contradict Q22, the more
  recently answered and more specific clarification); silently following Q22 (would contradict
  the answer key without surfacing the conflict); inventing a third reading not stated by either
  source.
- **Consequences:** `M3-S04` cannot be documented as "resolving" this question by exit code alone
  — its own declared checkers have no sender-identity assertion (`sender-identity-note.md` § 2)
  — and the milestone verifier must treat this decision as outstanding until the M3 gate records
  an explicit choice.
- **Grounded in:** `plan.json` clarification Q22; `answers-key.md` "Acknowledgement" row;
  `skills/admin/email-templates-and-alerts/references/metadata-and-sender-identity.md`;
  `skills/admin/email-to-case-configuration/references/gotchas.md` Gotcha 3;
  `artefacts/M3-S02/sender-identity-note.md` §§ 1–2.
- **Evidence:** `envelopes/M3-S02/2026-09-12T03-30-00Z.json` `extensions.ambiguities_recorded[0]`;
  `tests/M3-S02/summary.md` "Process notes worth a human's attention"; `tests/M3-S02/results.json`
  `skipped_manual[0]` (B06).

## O-M3S02-01 — Q22 vs `answers-key.md`: a clarification-record defect for the planner, not merely an ambiguity this step carries

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `decisions.md` **D-M3S02-04**
- The contradiction `D-M3S02-04` records is not only a decision this build must make at the M3
  gate — it is evidence that the clarification-answering process itself produced two disagreeing
  records for the same question. `Q22`'s answer was written to say the answer key's own position,
  and instead states the opposite of the row in `answers-key.md` it claims to follow ("Per the
  answer key: yes, from support@acme.example... support@ (a live routing address) itself sends
  the acknowledgement" — but the answer key's own row says the reverse). One of the two records is
  simply wrong about what the other one says.
- **Remedy:** at the next clarification-gate pass, reconcile `plan.json` `clarifications[Q22].answer`
  against `answers-key.md`'s "Acknowledgement" row directly, side by side, and correct whichever
  one misquotes the other — not by picking a winner on technical grounds (that is `D-M3S02-04`'s
  job), but by fixing the record so a future reader is not told "per the answer key" about a
  position the answer key does not hold.
- **Evidence:** `plan.json` `clarifications` (Q22); `answers-key.md` "Acknowledgement" row.

## O-M3S02-02 — The deliverability checker's exit 0 on this step asserts nothing: three declared-file WARNs, not a posture proof

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `tests/M3-S02/checker2_stdout.txt`
- `check_email_deliverability_strategy.py --manifest-dir artefacts/M3-S02` exits 0 with three
  WARNs: no `EmailAdministrationSettings`/`EmailAuthorizationSettings` file, no deliverability
  policy JSON, no DKIM key inventory JSON. This step declares none of those three files, so the
  checker's own documented behaviour on absence (WARN, never fail) means this exit code carries no
  assertion about the org's deliverability posture — it only confirms the three files are, as
  expected, not present. A reader who sees "checker: pass" without reading the WARNs would believe
  more was proven than was.
- **Remedy:** either add a dedicated deliverability step to a future milestone plan that owns
  `settings/EmailAdministration.settings-meta.xml`, a deliverability policy JSON and a DKIM key
  inventory JSON — closing the three open `admin/email-deliverability-strategy` Questions-to-Ask
  rows `sender-identity-note.md` § 4 names (DKIM rotation, SMTP relay and bounce management, DNS
  ownership and lead time) — or explicitly accept the gap at the M3/M5 gate as out of scope for
  this phase.
- **Evidence:** `tests/M3-S02/checker2_stdout.txt`; `tests/M3-S02/summary.md` § "checker 2";
  `artefacts/M3-S02/sender-identity-note.md` § 4.

## O-M3S02-03 — Correction of record: `deploy-order.md` is undeclared in `outputs[]` on both `M3-S02` and `M3-S01`; `amend-step` cannot fix either now that both are documented

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, cross-reading `plan.json`
  `steps[M3-S02].outputs[]` and `steps[M3-S01].outputs[]` against
  `workbook/99-other-configuration.md` `CWB-OTHER-018`
- `plan.json` `steps[M3-S02].outputs[]` lists seven paths and does not include
  `artefacts/M3-S02/deploy-order.md` — confirmed directly in the metadata-builder's own envelope
  (`envelopes/M3-S02/2026-09-12T03-30-00Z.json` `extensions.undeclared_artefacts[0]`), which
  states the file "is written on every run per `agents/build-doc-keeper/AGENT.md` Step 5 rule 2
  but is not in this step's `outputs[]`." Re-reading `steps[M3-S01].outputs[]` while writing this
  entry shows the identical gap there: four paths declared, none of them `deploy-order.md`. That
  is a direct contradiction of `workbook/99-other-configuration.md` `CWB-OTHER-018`'s notes cell,
  which states `M3-S01`'s `deploy-order.md` is "declared in `outputs[]`, present, non-empty" —
  it is present and non-empty, but it is not declared.
- **Why this is left standing rather than fixed in either row:** `agents/build-doc-keeper/AGENT.md`
  Step 8 restricts a per-step documentation run to its own step's rows; `CWB-OTHER-018` belongs to
  `M3-S01` and is not this run's row to rewrite, and `M3-S02`'s own `CWB-OTHER-020` records the
  gap as it actually stands rather than repeating the same claim.
- **Why `amend-step` cannot simply close this:** `scripts/build_plan.py amend-step` amends a step
  that has not yet produced the artefact it is amending outputs for; both `M3-S01` and `M3-S02` are
  already `documented` (this run sets `M3-S02`'s status), with real deploy-order files on disk
  that predate any `outputs[]` entry for them. Amending `outputs[]` now would not change what was
  actually declared at build time, and `check-outputs` for both steps already reads as `ok` from
  the file's presence alone regardless of declaration — so an after-the-fact `outputs[]` edit
  would silently rewrite history rather than correct it. The five prior instances of this same
  undeclared-`deploy-order.md` pattern (`M1-S01`, `M1-S02`, `M2-S02`, and now `M3-S01`/`M3-S02`)
  are open items for the same reason: `decisions.md` O-M1S02-02, O-M2S02-01.
- **Remedy:** for the planner, the durable fix is a template-level one — add `deploy-order.md` to
  the default `outputs[]` list every `metadata-builder`-owned step's scaffold carries, so future
  steps don't reproduce this gap, rather than retrofitting `outputs[]` on documented steps.
- **Evidence:** `plan.json` `steps[M3-S02].outputs[]`; `plan.json` `steps[M3-S01].outputs[]`;
  `envelopes/M3-S02/2026-09-12T03-30-00Z.json` `extensions.undeclared_artefacts[0]`;
  `workbook/99-other-configuration.md` `CWB-OTHER-018`, `CWB-OTHER-020`.

## O-M3S02-04 — Correction of record, forward-looking: two consumer skills' worked examples hand `M3-S04` and `M4-S04` a stale `unfiled$public/` template prefix; and `REQ-033`'s handover notice is not `Q88`'s queue-level notification

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from
  `artefacts/M3-S02/deploy-order.md` § "The stale folder prefix both consumer skills will hand
  you", flagged for the written record by both the builder's and the tester's envelopes
- `skills/admin/escalation-rules/references/metadata-examples.md:95` writes
  `<assignedToTemplate>unfiled$public/Case_Escalated_To_Tier2</assignedToTemplate>`, and
  `skills/admin/assignment-rules/references/metadata-examples.md:148`/`:159` write
  `<template>unfiled$public/Case_Web_Acknowledgement</template>` — the same developer names this
  build's templates carry (except `Case_Acknowledgement`, not `Case_Web_Acknowledgement` — one
  template for both channels, per Q28/Q60, not the examples' channel-split pair), filed under a
  different folder (`unfiled$public` versus this build's `case_intake`). Copying either worked
  example verbatim into `M3-S04` or `M4-S04` produces a template reference that resolves to
  nothing in this build's org, and per `escalation-rules:153` the deploy then fails on the
  reference, not on the rule.
- **What `M3-S04`/`M4-S04` must write instead:** `case_intake/Case_Acknowledgement` (`M3-S04`'s
  `<template>`) and `case_intake/Case_Escalated_To_Tier2` (`M4-S04`'s `<assignedToTemplate>`) —
  the `case_intake/` prefix, never `unfiled$public/`.
- **Second, distinct correction bundled here rather than as a separate entry:** `Q88`'s answer
  ("Tier 1 uses Omni-Channel push, so no queue email; Billing wants the queue address emailed";
  Tier 2 defaulted to a shared mailbox) is a **queue-level** notification control, set on the
  `Group.email`/`doesSendEmailToMembers` elements `M2-S04` built for each queue. `REQ-033`'s
  `Case_Escalated_To_Tier2` template is a **case-level** notice the escalation action fires on
  reassignment — a different mechanism serving a related but distinct need (a queue email is one
  message per record landing in the queue by any path; the escalation handover is one message per
  case specifically reassigned by the SLA breach). Nothing in this build wires them together, and
  nothing should: `M4-S04` should not treat `Q88`'s Tier 2 default as already covering the
  handover notice, or vice versa.
- **Remedy:** when `M3-S04` and `M4-S04` are built, their own deploy-order notes should cite this
  entry and `artefacts/M3-S02/deploy-order.md` directly rather than copying either cited skill's
  worked example's folder prefix by hand.
- **Evidence:** `artefacts/M3-S02/deploy-order.md` § "The stale folder prefix both consumer skills
  will hand you"; `skills/admin/escalation-rules/references/metadata-examples.md:95`;
  `skills/admin/assignment-rules/references/metadata-examples.md:148,159`; `answers-key.md` "Queue
  notifications" row; `plan.json` clarification Q88.

## O-M3S02-05 — Skill-depth signal: `check_rtm.py`'s component-key deriver does not know `EmailFolder`-qualified `EmailTemplate` naming, and reports two false orphans

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the build-scope `check_rtm.py`
  run in `traceability.md` § "Linter result — after M3-S02"
- `check_rtm.py`'s file-to-component deriver (`SUFFIX_TYPE`) keys any `.email` file as
  `EmailTemplate:<file stem>`, with no equivalent of `OBJECT_CHILD_DIR`'s folding logic for a
  folder-nested component. So it derives `EmailTemplate:Case_Acknowledgement` and
  `EmailTemplate:Case_Escalated_To_Tier2` from the two `.email` files under
  `artefacts/M3-S02/email/case_intake/`, while the correct, deployable member names — the ones
  `package.xml` and `traceability.md` `REQ-032`/`REQ-033` both correctly use — are folder-qualified:
  `EmailTemplate:case_intake/Case_Acknowledgement` and `EmailTemplate:case_intake/Case_Escalated_To_Tier2`.
  The two forms don't string-match, so the checker's orphan report lists both as uncovered even
  though both are named by a row.
- **Why the row was not renamed to quiet it:** renaming the traceability row to the checker's
  bare-stem key would make the row assert a manifest member name that does not exist in
  `package.xml` — a wrong row purely to satisfy a linter is a worse outcome than a WARN the reader
  can see is a false positive once explained, which this entry now does.
- **Remedy:** record `admin/requirements-traceability-matrix`'s `check_rtm.py` as a candidate for
  the next depth pass — a folder-qualification rule for `EmailFolder`-nested `EmailTemplate`
  files, mirroring `OBJECT_CHILD_DIR`'s existing fold for `CustomObject` children, would close
  this gap for every future build reaching an email-template step, not only this one.
- **Evidence:** `skills/admin/requirements-traceability-matrix/scripts/check_rtm.py`
  (`SUFFIX_TYPE`, `OBJECT_CHILD_DIR`); `traceability.md` § "Linter result — after M3-S02";
  `artefacts/M3-S02/package.xml`.

## D-M3S03-01 — F-25: `systemUserEmail` is an attribution field, not a sender; `D-M3S02-04` stays open

- **Date:** 2026-09-12 · **Step:** `M3-S03` (`routing`) · **Agent:** `metadata-builder` (rebuild run
  `2026-09-12T04-39-20Z`); recorded here by `build-doc-keeper`
- **Kind:** deviation — the rebuilt artefact adds an element the as-built run's `inputs{}` never
  asked for, in response to an org finding rather than a clarification answer
- **What was recorded:** the operator's validate-only run against the org (`sf project deploy
  start --dry-run`, `checkOnly: true`, alias `sfskills-dev`; `reports/MOCK-DEPLOY-M3.md` Run 3)
  refused the as-built `settings/Case.settings-meta.xml` — `CaseSettings Case: Enter the system
  user's email address` — because `useSystemUserAsDefaultCaseUser` `true` has no `systemUserEmail`.
  Neither cited skill names the element at all (`envelopes/M3-S03/2026-09-12T04-39-20Z.json`: zero
  grep hits across `admin/email-to-case-configuration` and `admin/case-management-setup`). The
  rebuild adds `<systemUserEmail>support-noreply@acme.example</systemUserEmail>` immediately after
  `<useSystemUserAsDefaultCaseUser>` and changes nothing else on that element pair.
- **Why this needed a decision, not just a fix:** `support-noreply@acme.example` is a new address
  this build invents, and this step already carries an open M3-gate decision about a different
  address — `D-M3S02-04`, whether `support@acme.example` itself is the acknowledgement's sender.
  Picking a careless value for `systemUserEmail` (for example, `support@acme.example` itself) would
  read, to a later reviewer, as though this step had quietly resolved that question.
- **Decision:** the value is deliberately **neither** `support@acme.example` **nor**
  `billing@acme.example` — it names a mailbox this build does not otherwise use. api_meta L111871
  scopes `systemUserEmail` to "the email address used when the default case user is the system
  user," an ownership/attribution field on Case History, not a From address on outbound mail;
  `EmailToCaseRoutingAddress` still carries no sender element at all, so nothing this step writes
  can set `senderEmail`. `D-M3S02-04` therefore stays open, exactly as it was before this rebuild —
  this entry does not settle it and is not to be read as doing so.
- **Alternatives rejected:** reusing `support@acme.example` (would look like a silent answer to
  `D-M3S02-04`); leaving `useSystemUserAsDefaultCaseUser` `true` with `systemUserEmail` unset (the
  org refuses the deploy); switching to `useSystemUserAsDefaultCaseUser` `false` with a
  `defaultCaseUser` username (rejected — this build creates no `User` metadata, so a username would
  resolve by name against nobody).
- **Consequences:** `support-noreply@acme.example` is **unprovisioned** by this build — a real
  deploy must confirm the mailbox exists or replace the value first.
- **Grounded in:** api_meta L111871 ("Specifies the email address used when the default case user
  is the system user"); `reports/MOCK-DEPLOY-M3.md` Run 3.
- **Evidence:** `envelopes/M3-S03/2026-09-12T04-39-20Z.json` § decision record;
  `artefacts/M3-S03/settings/Case.settings-meta.xml`; `artefacts/M3-S03/deploy-order.md` §§ 0,
  "F-25 does not pre-empt the acknowledgement-sender decision (D-M3S02-04)".

## D-M3S03-02 — M3 gate decision, not to be pre-empted by `M4-S03`: F-27 forces `casePriority` on both routing addresses, killing that step's null-guard on the email channel

- **Date:** 2026-09-12 · **Step:** `M3-S03` (`routing`) · **Agent:** `metadata-builder` (rebuild run
  `2026-09-12T04-39-20Z`); recorded here by `build-doc-keeper`
- **Kind:** design trade-off, held open as a milestone-gate decision — the as-built design and the
  org's own validation requirement point in opposite directions, and no cited skill lets this build
  pick a side from the artefacts alone
- **What was recorded:** the as-built file left `casePriority` unset on both routing addresses on
  purpose, so that `M4-S03`'s before-save Flow — specified to stamp `Case.Priority` "guarded so it
  writes only into a null value" — would still fire for email-originated cases. The operator's probe
  (`reports/MOCK-DEPLOY-M3.md` Run 4, probe d) returned `EmailToCaseRoutingAddress[support@acme.example]:
  Missing casePriority`; probe e proved the file only validates with a value present. The rebuild
  sets `<casePriority>Medium</casePriority>` on both addresses — the value the skill's own worked
  example carries (`skills/admin/email-to-case-configuration/references/metadata-examples.md` lines
  50, 59), not an answered clarification.
- **Why this bites, and who it bites:** `M4-S03`'s null guard can now never fire for an
  email-originated Case — `Priority` arrives already `Medium`. `WebToCaseSettings` has no priority
  element at all (three children only, api_meta L112128 ff.), so the guard still fires for web
  cases. The two intake channels now diverge in how `Priority` is derived, and `M4-S03`'s own
  `plan.json` wording (`Case_BeforeSave_StampEntitlementAndCalendar`) does not yet say so.
- **Decision — recorded as an M3 milestone-gate decision, explicitly not to be pre-empted by
  `M4-S03`:** three options are named for the gate, and none is chosen here: (1) accept `Medium` as
  the email channel's intake priority and update the requirement record accordingly; (2) have
  `M4-S03`'s flow derive `Priority` from `Severity__c` / `Support_Tier__c` and unconditionally
  **overwrite** rather than null-guard for email-originated cases — the recommended reading of Q16,
  "priority must be set from what the form or email tells us"; (3) some other resolution outside
  this build's current scope. `M4-S03` must not silently pick option 2 merely because it is the
  build's own working assumption — that would resolve a milestone-gate decision inside an unrelated
  step's build run, the same failure mode `D-M3S02-04` already guards against for the sender
  question.
- **Already partly actioned, not fully:** the dry-run operator (Fable) has already written this
  consequence into `M4-S03`'s own `notes` via `amend-step --prose-only`
  (`plan.json` `steps[M4-S03].amendments[0]`, `2026-09-12T04:50:22Z`: "M3-S03 now sets casePriority
  on both Email-to-Case routing addresses, so this flow's null-guarded Priority stamp is dead for
  email cases; builder must derive/overwrite or record acceptance of Medium"). So `M4-S03`'s builder
  will not discover this cold — but the **choice** among the three options above is still open at
  the M3 gate, and the amendment does not make it.
- **Alternatives rejected:** leaving `M4-S03`'s plan wording as if the guard still fires for every
  channel (already partly corrected by the amendment above, but the underlying choice remains
  unmade); having this step silently omit `casePriority` again (the org refuses the deploy).
- **Consequences:** the milestone verifier must treat this as an outstanding M3-gate item, the same
  way it already must for `D-M3S02-04`.
- **Grounded in:** `reports/MOCK-DEPLOY-M3.md` Run 4 (probes d, e); api_meta L112039 ("Specifies
  the default case priority for cases created through this routing address" — no Required marker);
  `skills/admin/email-to-case-configuration/references/metadata-examples.md` lines 50, 59.
- **Evidence:** `envelopes/M3-S03/2026-09-12T04-39-20Z.json` § decision record;
  `artefacts/M3-S03/deploy-order.md` § "F-27's consequence for M4-S03 — read this before building
  the before-save flow"; `plan.json` `steps[M4-S03].amendments[0]`, `steps[M4-S03].inputs.note`.

## O-M3S03-01 — Skill-depth and planner signal: F-26's API ≥ 64.0 floor now leaves this build's `package.xml` files at two different versions, with no plan-level field recording either

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `artefacts/M3-S03/deploy-order.md`
  § 0 and `reports/MOCK-DEPLOY-M3.md` Run 4
- `newEntityRecordType` is rejected at API 62.0 and 63.0 (`Property 'newEntityRecordType' not valid
  in version 63.0`) and accepted from 64.0, and only in its object-qualified form (`Case.Support`,
  never the bare `Support`) — proven live, UNVERIFIED in `admin/case-management-setup` gotcha 9,
  which instructs writing the element but names neither fact. `M3-S03`'s `package.xml` now reads
  `67.0` (the org's own version, and the version `M4`'s Apex steps already target), while
  `artefacts/M1-S01/package.xml` and every `M2-*` manifest still read `62.0` — this build's original
  floor (`reports/MOCK-DEPLOY-M1.md` finding F-06).
- **Why this is a backlog item, not a defect in this step:** `scripts/mock_deploy.py` computes the
  deployed API version as the **highest** across whichever steps are selected in one request (its
  own fix, landed alongside this rebuild), so a mixed-version build still validates correctly end to
  end — Run 5 proved 0 errors deploying `M1 + M2 + M3-S01..S03` together at `67.0`. But `plan.json`
  carries no single field recording "this build's API version" or a floor any step's `package.xml`
  is checked against, so a step can drift upward (as this one just did) with nothing to notice if a
  later step drifted back down, and a real deploy pipeline that pins a version per package rather
  than computing a request-wide maximum would fail exactly the way `mock_deploy.py` did before its
  own fix.
- **Remedy:** record as a `build-planner` v6 backlog item — a plan-level `api_version` (or a
  documented floor every `metadata-builder` step's `package.xml` is generated against), rather than
  each step defaulting independently. Until then, a human deploying this build for real should pass
  an explicit `--api-version` (or rely on `mock_deploy.py`'s computed maximum) instead of trusting
  any single step's `package.xml` as the build's version.
- **Evidence:** `artefacts/M3-S03/package.xml` (`67.0`); `artefacts/M1-S01/package.xml`,
  `artefacts/M2-S01/package.xml` et al. (`62.0`); `reports/MOCK-DEPLOY-M3.md` Run 4 (probes a–e) and
  Run 5; `envelopes/M3-S03/2026-09-12T04-39-20Z.json`.

## O-M3S03-02 — Correction of record: `steps[M3-S03].acceptance_tests[3]`'s manual-test wording contradicts itself, and the artefact is right where the sentence is wrong

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the tester's envelope
  (`envelopes/M3-S03/2026-09-12T04-53-23Z.md` § 7, "Ambiguous") and
  `plan.json` `steps[M3-S03].acceptance_tests[3].description`
- The manual test's own text reads, in part: "...the `webToCase` block carries exactly its three
  documented children — `enableWebToCase` true and a `caseOrigin` that is a live CaseOrigin value
  from M1-S01, with `defaultResponseTemplate` deliberately unset..." — it asserts "exactly its
  three documented children" and then names the deliberate omission of the third in the same
  breath, which cannot both be true. The artefact itself is unambiguous and matches the step's
  stated design: `webToCase` carries exactly **two** children (`enableWebToCase`, `caseOrigin`);
  `defaultResponseTemplate` is not written, for the reason the same sentence gives (scoped to
  Self-Service portal responses, not the customer acknowledgement, which is `M3-S04`'s element).
- **Why not corrected here:** `build-doc-keeper` does not hand-edit `acceptance_tests[].description`
  — that is `amend-step --prose-only`'s job (`standards/build-orchestration.md` § 2), and this agent
  touches `plan.json` only through the single Step 9 status transition. The tester's own boundary is
  the same: it "never ticks a manual test" and records the wording verbatim for the human at the
  gate rather than resolving it.
- **Remedy:** `amend-step --prose-only` should replace "carries exactly its three documented
  children" with "carries two of its three documented children," the same class of fix `O-M2S04-01`
  already recorded for a stale WARN count in a different step's test description. The step is
  `tested`, not `running`, so `--prose-only` may run on it without reopening the `step:M3-S03` gate
  (it has none) or requiring a rejected `step:<id>` gate first.
- **Evidence:** `plan.json` `steps[M3-S03].acceptance_tests[3].description`;
  `envelopes/M3-S03/2026-09-12T04-53-23Z.md` § 7; `artefacts/M3-S03/settings/Case.settings-meta.xml`
  (`webToCase` block, two children); `tests/M3-S03/results.json` `skipped_manual[0]`.

## D-M3S04-01 — Operator's pre-gate resolution of `D-M3S02-04` for this step only: `senderEmail` = `replyToEmail` = `support-noreply@acme.example`

- **Date:** 2026-09-12 · **Step:** `M3-S04` (`routing`) · **Agent:** dry-run operator (Fable),
  `plan.json` `steps[M3-S04].amendments[0]` (`2026-09-12T05:12:42Z`); binding input read by
  `metadata-builder` (run `2026-09-12T05-20-02Z`); recorded here by `build-doc-keeper`
- **Kind:** design trade-off, entered as an operator amendment to the step's `notes` ahead of the
  M3 gate — not a clarification answer and not this step's to invent on its own
- **What was recorded:** `autoResponseRules/Case.autoResponseRules-meta.xml` → `ruleEntry`
  `senderEmail` and `replyToEmail` both read `support-noreply@acme.example` — a verified org-wide
  address that is **not** an Email-to-Case routing address. `support@acme.example` and
  `billing@acme.example` are this org's two routing addresses (`artefacts/M3-S03/settings/Case.settings-meta.xml`
  `emailToCase/routingAddresses/emailAddress`) and neither appears in either element. The value
  also matches `M3-S03`'s `systemUserEmail` (`D-M3S03-01`), so the build now names one
  unprovisioned no-reply mailbox rather than two.
- **This is explicitly a pre-gate resolution, not a closure of `D-M3S02-04`.** That entry holds
  open whether `support@acme.example` itself should be the acknowledgement's sender (Q22's
  reading, loop risk accepted under Q68's sandbox test) or a non-routing address (the reading this
  amendment takes). The M3 gate may still affirm Q22's reading; if it does, only this element
  changes — nothing else in this step depends on the answer (`deploy-order.md` § 0).
- **Alternative rejected:** letting `metadata-builder` pick a sender value on its own judgment at
  build time. Rejected because the choice between two prohibited addresses and a third,
  unprovisioned one is exactly the M3-gate decision `D-M3S02-04` already reserves for a human — an
  operator amendment to the step's binding `notes` is the mechanism `standards/build-orchestration.md`
  provides for resolving it early without editing the gate record itself.
- **Grounded in:** `skills/admin/assignment-rules/references/gotchas.md` #6 ("Auto-Response
  `senderEmail` Equal to the Email-to-Case Routing Address Creates a Mail Loop");
  `skills/admin/email-to-case-configuration/references/gotchas.md` #3 (same prohibition, second
  source); Q22's original `proposed_default`; `D-M3S03-01` (the matching `systemUserEmail` value).
- **Consequence a human must accept with this value:** `support-noreply@acme.example` is
  unprovisioned by this build (see `D-M3S04-03`, F-28).
- **Evidence:** `plan.json` `steps[M3-S04].notes`, `steps[M3-S04].amendments[0]`;
  `artefacts/M3-S04/deploy-order.md` § 0; `artefacts/M3-S04/autoResponseRules/Case.autoResponseRules-meta.xml`.

## D-M3S04-02 — The Account-support-tier criterion is deliberately NOT written; title/manual-test mismatch escalated to the M3 gate

- **Date:** 2026-09-12 · **Step:** `M3-S04` (`routing`) · **Agent:** `metadata-builder` (run
  `2026-09-12T05-20-02Z`); confirmed by `step-tester` (run `2026-09-12T05-27-04Z`)
- **Kind:** design trade-off — an omission recorded rather than a guessed value shape, carrying an
  unresolved title/test mismatch forward to the gate
- **What was recorded:** `plan.json` `steps[M3-S04].title` and the first manual acceptance test
  (`W02`) both say the rule routes on `Case.Origin` **and** the Account support tier. The built
  `assignmentRules/Case.assignmentRules-meta.xml` routes on **`Case.Origin` only** — no
  `criteriaItems` anywhere names `Account.Support_Tier__c` or any related-object field.
- **Alternative rejected — writing a rule entry keyed on the support tier — for two independent
  reasons, either sufficient on its own:**
  1. **No target.** Q25 names `Account.Support_Tier__c` as a field *available* at save; no
     clarification answer, no line of `requirement.md`, and no `answers-key.md` row says which
     queue a `Premier` case should go to instead of the Origin-derived one. The requirement gives
     Premier a faster **SLA** (4 business hours, `M4-S02`), not a different owner.
  2. **No grounded notation.** No file under `skills/` documents a `criteriaItems/field` on a
     *related* object inside a Case assignment rule. Every documented value is base-object
     (`Case.Origin`, `Case.Priority`, `Lead.Country`); `Account.Customer_Tier__c` appears only in
     `admin/outbound-message-setup`, on an **Account** workflow rule, which grounds nothing
     cross-object. Writing `Account.Support_Tier__c` or `Case.Account.Support_Tier__c` would be the
     same class of guessed value *shape* that produced **F-26** in this build (`Support` where the
     org required `Case.Support`) and cost a rebuild.
- **Decision required at the M3 gate — a human's, not this agent's:** either (a) an answer names
  the tier→queue mapping for `Premier` and a live org confirms the cross-object `criteriaItems`
  notation, and the step is rebuilt; or (b) the step's title and `W02` are corrected to
  Origin-only, matching what was actually built and what a customer-tier SLA (not routing) already
  requires.
- **Consequence for this run:** `W02` is deferred at the M3 gate as **not tickable as written**
  against the artefact as built (`tests/M3-S04/summary.md` § "Ambiguity recorded verbatim") — this
  is a plan/artefact mismatch, not a test failure, and no artefact was changed to force a tick.
- **Grounded in:** `artefacts/M3-S04/deploy-order.md` § 6 row 1; `requirement.md` (Premier SLA,
  not a Premier queue); `envelopes/M3-S04/2026-09-12T05-20-02Z.json` § 5.
- **Evidence:** `envelopes/M3-S04/2026-09-12T05-20-02Z.md` § 5; `envelopes/M3-S04/2026-09-12T05-27-04Z.md`
  § 2; `tests/M3-S04/summary.md`.

## D-M3S04-03 — F-28: the `support-noreply@acme.example` OrgWideEmailAddress is a G3 deploy prerequisite, not a metadata defect

- **Date:** 2026-09-12 · **Step:** `M3-S04` (`routing`) · **Agent:** mock-deploy operator, run 6;
  recorded here by `build-doc-keeper`
- **Kind:** design trade-off, held open as a milestone-gate (G3) prerequisite — the org's own
  validation requirement cannot be satisfied by any metadata this build's scope can produce
- **What was recorded:** `reports/MOCK-DEPLOY-M3.md` Run 6 (`M1-S01`..`M3-S04`, API 67.0) —
  `AutoResponseRule Case.Case_Acknowledgement: support-noreply@acme.example is an invalid From
  email address.` `sfskills-dev` carries no `OrgWideEmailAddress` record at all
  (`SELECT Address FROM OrgWideEmailAddress` → 0 rows), and there is no metadata type for one —
  `admin/email-templates-and-alerts` § "Org-wide email address (the sender)" already documents it
  as Setup-only and requiring verification. The assignment rule (`Case_Intake_Routing`) validated
  cleanly in the same run; only the auto-response rule's sender fails.
- **Why this is not a rebuild:** the value is the one the operator decided ahead of the M3 gate
  (`D-M3S04-01`), and this step's own `deploy-order.md` § 2 row 6 already named the address as
  "provisioned by nobody" before the mock deploy confirmed it live. No metadata this build can emit
  substitutes for a verified org-wide address — it is Setup, not deployable source.
- **Decision:** recorded as a **G3 prerequisite**, not an artefact defect: (1) a human provisions
  and verifies `support-noreply@acme.example` as an `OrgWideEmailAddress` in the target org before
  this component deploys; (2) the M3 milestone report lists the address as a G3 prerequisite; (3)
  no rebuild of this step. Until the address exists, M3 mock-deploy validation runs without
  `M3-S04`'s auto-response rule — the assignment rule alone validates.
- **Skill-gap signal:** `admin/assignment-rules` should gain a gotcha and an advisory checker line
  that `senderEmail` / `replyToEmail` are deploy-time prerequisites, not merely send-time ones —
  provision and verify the address before deploying the rule, or the deploy fails.
- **Grounded in:** `reports/MOCK-DEPLOY-M3.md` Run 6; `skills/admin/email-templates-and-alerts`
  § "Org-wide email address (the sender)"; `artefacts/M3-S04/deploy-order.md` § 2 row 6.
- **Evidence:** `reports/MOCK-DEPLOY-M3.md` Run 6 (finding F-28); `artefacts/M3-S04/autoResponseRules/Case.autoResponseRules-meta.xml`.

## D-M3S04-04 — `replyToEmail` mirrors `senderEmail`; the acknowledgement's replies do not thread onto the case

- **Date:** 2026-09-12 · **Step:** `M3-S04` (`routing`) · **Agent:** `metadata-builder` (run
  `2026-09-12T05-20-02Z`); recorded here by `build-doc-keeper`
- **Kind:** design trade-off, recorded as a consequence rather than resolved — a side effect of
  `D-M3S04-01`'s value, following the cited skill's own worked example
- **What was recorded:** `autoResponseRules/Case.autoResponseRules-meta.xml` sets `replyToEmail`
  to the same value as `senderEmail`, `support-noreply@acme.example`, per
  `skills/admin/assignment-rules/references/metadata-examples.md` § "Case auto-response rule".
- **Consequence:** a customer who hits *Reply* on the acknowledgement writes to a mailbox that
  does not feed Email-to-Case, and that reply does **not** thread onto the case — unlike a
  customer replying to the *original* Email-to-Case thread (thread token in subject and body,
  `M3-S03`), which is unaffected.
- **Alternative not chosen here:** setting `replyToEmail` to `support@acme.example` so replies
  thread onto the case. Not written, because that is the routing address `D-M3S04-01`'s value was
  chosen specifically to avoid naming in this element (the mail-loop prohibition, `D-M3S04-01`'s
  own grounding) — routing the acknowledgement's replies back into the case is exactly the
  trade-off `D-M3S02-04` holds open, not something this element can resolve unilaterally.
- **Status:** carried forward as an open question under the same gate item as `D-M3S02-04` — if
  the M3 gate affirms Q22's reading (`support@` itself sends), this element changes along with
  `senderEmail`.
- **Grounded in:** `skills/admin/assignment-rules/references/metadata-examples.md` § "Case
  auto-response rule"; `D-M3S02-04`; `D-M3S04-01`.
- **Evidence:** `artefacts/M3-S04/autoResponseRules/Case.autoResponseRules-meta.xml`;
  `envelopes/M3-S04/2026-09-12T05-20-02Z.md` § 9 ("Ambiguous"); `envelopes/M3-S04/2026-09-12T05-27-04Z.md`.

## O-M3S04-01 — Q24's "defaulted on" checkbox still carries no metadata after three steps; the routing consequence is now concrete

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the `M3-S04` builder and runner
  envelopes
- Q24's answer requires the "Assign using active assignment rule" checkbox **defaulted on** for
  the Case layouts, because ~20 cases a day are logged by hand. `D-M1S02-03` already recorded that
  `M1-S02`'s layouts carry `<showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>`
  and nothing that pre-checks it, because no element in the cited skill's inventory does so at
  skill v1.2.0. `M3-S04`'s builder and runner both raise the same gap again, now with the routing
  mechanism actually built: `owner-writer-map.md` § 5 states plainly that without the default, "~20
  cases a day are owned by their creator and get no acknowledgement" — the assignment rule and the
  auto-response rule both fire only when the checkbox is ticked, so the consequence is no longer
  hypothetical once this step exists.
- **Why this is filed again rather than left as `D-M1S02-03` alone:** that entry recorded the gap
  at the layout step, before any downstream step depended on the checkbox actually being ticked.
  `M3-S04` is the step whose behavior the missing default silently degrades, and it is a Setup-level
  layout property no step's `outputs[]` can add — `agents/metadata-builder` cannot write it here
  any more than `M1-S02` could.
- **Remedy, unchanged from `D-M1S02-03`:** accept the narrowing at the gate (each hand-logged case
  is ticked by the agent), or route the remaining half to a recorded Setup step. Deepen
  `skills/admin/record-types-and-page-layouts` if a `Layout` element that defaults the checkbox on
  turns out to exist in the Metadata API guide — not established by this build.
- **Evidence:** `decisions.md` **D-M1S02-03**; `artefacts/M3-S04/owner-writer-map.md` § 5;
  `envelopes/M3-S04/2026-09-12T05-20-02Z.md` § 9 ("Concerning"); `envelopes/M3-S04/2026-09-12T05-22-40Z.md`.

## O-M3S04-02 — The Billing queue's notification address is a live routing address; the risk named at `M2-S04` is now live rather than latent

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the `M3-S04` builder envelope
- `decisions.md` **D-M2S04-04** already named the risk: `Queue:Billing`'s `<email>` is
  `billing@acme.example`, the same address `M3-S03` configured as an Email-to-Case intake address —
  a queue-assignment notification and a fresh inbound case can chain through the same mailbox. At
  `M2-S04` time, nothing yet sent a notification through that address; `M3-S03`'s Email-to-Case
  routing and `M3-S04`'s assignment rule (which assigns to `Billing` on `Case.Origin` =
  `Email-Billing`) are both now built, so the mailbox is live on both ends of the risk.
- **What has NOT been built, stated rather than implied:** no assignment-notification `<template>`
  was written on the `Billing` entry in `assignmentRules/Case.assignmentRules-meta.xml` — Q88
  accepted the queue's `<email>` deliberately, but no answer in this build asks for a queue-level
  assignment notification, and none is on file. The risk is therefore latent again in this build's
  actual artefacts, not realized — recorded because the *next* person who adds one will not
  otherwise know the mailbox is shared with live inbound mail.
- **Remedy:** carry `D-M2S04-04` forward at the M3 gate alongside `D-M3S04-01`/`-03`/`-04`; before
  any future step adds an assignment-notification template to the `Billing` entry, confirm it does
  not post into `billing@acme.example` itself.
- **Evidence:** `decisions.md` **D-M2S04-04**; `artefacts/M3-S04/deploy-order.md` § 6 row 2;
  `envelopes/M3-S04/2026-09-12T05-20-02Z.md` § 9 ("Concerning").

## O-M3S04-03 — Skill-depth signal: `check_rtm.py` derives two component keys per rule file, and one traceability row can only satisfy one of them

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the RTM checker run over
  `traceability.md` after this step's two rows were added
- **What was recorded:** `check_rtm.py --manifest-dir artefacts` reports **2 orphans** —
  `AssignmentRule:Case.Case_Intake_Routing` (evidenced by
  `assignmentRules/Case.assignmentRules-meta.xml`) and
  `AutoResponseRule:Case.Case_Acknowledgement` (evidenced by
  `autoResponseRules/Case.autoResponseRules-meta.xml`) — exit 0, 0 errors, 0 coverage gaps, 37
  rows, 1 warning (this orphan WARN).
- **Why, read from the script:** for any type in its `RULE_CONTAINERS` map (`AssignmentRules`,
  `AutoResponseRules`, `EscalationRules`), `build_manifest_index()` registers **two** keys per
  file: the container-level member the manifest actually declares (`AssignmentRules:Case`,
  evidenced by `package.xml`, the plural form every other row in this build's convention uses for
  a deployable member) and, separately, a singular per-rule key derived by reading each
  `<ruleEntry>`'s parent `fullName` **inside** the file (`AssignmentRule:Case.Case_Intake_Routing`,
  evidenced by that file itself). `REQ-036`/`REQ-037` name the container form — matching
  `package.xml`, `workbook/06-automation.md` `CWB-AUT-010`/`-011`, and every other row in this
  build, which names the deployable member rather than a sub-component. `resolve_artefact()`
  marks a key "referenced" only when a row's artefact string matches it exactly or shares its
  exact evidencing path; the container key's path is `package.xml`, the rule key's path is the
  rule file itself, so naming one never satisfies the other.
- **Alternative rejected:** renaming `REQ-036`/`REQ-037`'s `artefact` cell to the singular
  per-rule form to quiet the checker. Rejected for the same reason `decisions.md` **O-M3S02-05**
  already gives for a different key-derivation mismatch on this build: it would make the row name
  a component nobody deploys (`AssignmentRule:Case.Case_Intake_Routing` is not what `package.xml`
  declares) purely to satisfy a linter, which is a worse outcome than a WARN a reader can see is a
  false positive once explained.
- **Also rejected:** adding two more rows (one per rule file) solely to name the singular form.
  Rejected because it would mint traceability rows with no requirement behind them, the same
  anti-pattern `agents/build-doc-keeper/AGENT.md`'s Output Contract and Step 7 guard against — a
  row exists to join a requirement to a delivery, not to pre-empt a specific checker's dual-key
  quirk.
- **Remedy:** record `admin/requirements-traceability-matrix`'s `check_rtm.py` as a further
  skill-depth candidate — `RULE_CONTAINERS`' per-rule key derivation should be additive evidence
  toward the *same* orphan check as its container key (matching by name suffix regardless of
  evidencing path, the way `resolve_artefact()`'s own "same name, different type spelling"
  fallback already does for a *row's* lookup), not a second, independently-orphanable component.
  This is the second such gap `O-M3S02-05` and this entry both name in the same script.
- **Evidence:** `skills/admin/requirements-traceability-matrix/scripts/check_rtm.py`
  (`RULE_CONTAINERS`, `build_manifest_index()`, `resolve_artefact()`); `traceability.md` §
  "Linter result — after M3-S04"; `artefacts/M3-S04/package.xml`.

## D-M4S01-01 — Checker-policy block on `Severity 1 24x7` closed at the skill, not the artefact: the flywheel record

- **Date:** 2026-09-12 · **Step:** `M4-S01` (`sla`) · **Agent:** `metadata-builder` (blocked run
  `2026-09-12T06-31-35Z`; closed at re-run `2026-09-12T06-52-00Z`); recorded here by
  `build-doc-keeper`
- **Kind:** skill gap — the gap the runner recorded verbatim when it set the step `blocked`
- **What was recorded:** the step's own declared checker, `check_business_hours_and_holidays.py`,
  rejected the file `steps[M4-S01].inputs.calendars` required: `ISSUE: … calendar 'Severity 1
  24x7': every day is 00:00:00.000Z to 00:00:00.000Z — this is the shipped 24/7 shape; SLA clocks on
  this calendar never pause.` That shape was, at the time, the only always-open form
  `admin/business-hours-and-holidays` documented, and `requirement.md` L18 ("Severity 1 outages are
  24/7 and never pause") is what asked for exactly that shape. `agents/build-step-runner` set the
  step `blocked` with reason `checker-policy` rather than force a repair, because the two repairs
  that would have passed the gate were each worse than the block: deleting the calendar contradicts
  the step's own `inputs{}`, and trimming it to Mon–Fri passes every automated check while closing a
  never-pausing calendar at weekends — verified on scratch copies outside the build directory, never
  applied to the artefact.
- **The gap was closed at the skill, not the artefact.** Commit `5b206697a` (`admin/business-hours-and-holidays`
  v1.0.1) scoped the shipped-24/7-shape rule to the org default (`<default>true</default>`) or a
  calendar literally named `Default`, downgrading the same shape on any other, deliberately named
  always-open calendar to an INFO line that never affects the exit code, and added this exact
  `Severity 1 24x7` calendar to `references/examples.md` Example 1 as a documented worked example.
  The re-run executed the declared command verbatim from the build directory against the
  byte-identical file and observed `EXIT=0` with one INFO line. No repair pass was spent; the file
  that was rejected is the file that now passes.
- **Alternative rejected:** repairing the artefact instead of the rule (see the two rejected repairs
  above), and leaving the block standing pending a human amendment to the plan (dropping the third
  calendar). Both were live options named in the blocked run's own envelope; the skill fix pre-empted
  the need to choose between them.
- **Grounded in:** `envelopes/M4-S01/2026-09-12T06-31-35Z.md` §§ 1, 5 (the block, the two rejected
  repairs); `envelopes/M4-S01/2026-09-12T06-52-00Z.md` §§ 1, 5 (the closure, the verbatim re-run);
  `skills/admin/business-hours-and-holidays` v1.0.1 `references/examples.md` Example 1;
  `artefacts/M4-S01/deploy-order.md` § 0.
- **Evidence:** `plan.json` `steps[M4-S01].runs[1]` (blocked, `checker-policy`), `runs[3]` (built);
  `tests/M4-S01/checker-business-hours-and-holidays.stdout.txt` (`INFO: … EXIT=0`).

## D-M4S01-02 — The 14-holiday seed is a placeholder, not Acme's list; Q90 named a role and a cadence, not a person — both carried to the M4 gate

- **Date:** 2026-09-12 · **Step:** `M4-S01` (`sla`) · **Agent:** `metadata-builder` (run
  `2026-09-12T06:31:35Z`, unchanged by the re-run); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — an ambiguity recorded rather than filled, the same shape as
  `decisions.md` D-M1S01-02
- **What was recorded:** no clarification anywhere in this build supplies Acme's actual holiday
  dates — Q39 established only that each region observes its own set, and `answers-key.md` has no
  row naming them. `holiday-maintenance-runbook.md` § 3 carries 14 entries (6 on `US Support`, 9 on
  `EMEA Support`, computed for the 12 months from 2026-09-12) as a seed so the calendars pause on
  *something* and the shape is reviewable, every weekday computed rather than recalled, marked
  UNCONFIRMED. Separately, Q90 answered *who is accountable* (Service Operations) and *how often*
  (one deploy per year, each Q4) but not *which named individual* — the runbook's own owner row is
  left explicitly OPEN.
- **Alternative rejected:** inventing a plausible individual name to fill Q90's owner cell, or
  omitting the holiday entries entirely pending Acme's confirmed list. Both rejected for the same
  reason `agents/metadata-builder/AGENT.md` gives against inventing an unconfirmed value: a named
  individual with no source would look confirmed while being fabricated, and a calendar with zero
  holidays would silently assert Acme observes none, which no source states either.
- **Grounded in:** `plan.json` clarifications `Q39` (answered, calendar list only), `Q90` (answered,
  role + cadence only); `requirement.md` L16 ("Clocks pause on weekends and regional holidays");
  `artefacts/M4-S01/holiday-maintenance-runbook.md` §§ 1, 3.
- **Remedy, both halves carried to the M4 gate:** (1) the Service Operations owner names the
  accountable individual before this file is deployed to production; (2) the same owner replaces
  the seeded 14-entry table with Acme's actual holiday list per region before deploy — the runbook's
  yearly procedure (§ 4) is what that owner then repeats every Q4.
- **Evidence:** `artefacts/M4-S01/holiday-maintenance-runbook.md` § 1 (owner row, "OPEN"), § 3 (the
  seed table and its UNCONFIRMED framing); `envelopes/M4-S01/2026-09-12T06-31-35Z.md` § 4 ("Which
  holidays does each region observe? — no source anywhere").

## O-M4S01-01 — `Severity 1 24x7` is presently unconsumed: a metadata placeholder for a Severity 1 entitlement process that has not been built

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the rebuilt-run envelope and
  `deploy-order.md` § 0
- **What was recorded:** the checker's INFO line on the always-open calendar asks the author to
  "confirm it is not attached to entitlements that expect business-hour pauses." `deploy-order.md`
  § 0 answers it by checking every step that could read the calendar by name: `M4-S02`'s two
  entitlement processes are both business-time promises (Premier 240 minutes, Standard 1 business
  day); `M4-S03`'s before-save Flow stamps `Case.BusinessHoursId` from `Account.Region__c`, which
  yields only `EMEA Support` or `US Support`; `M4-S04`'s Severity 1 escalation entry uses
  `businessHoursSource = None`, which reads no calendar at all. No holiday in this file is attached
  to it, deliberately. So `Severity 1 24x7` is built and correct, but nothing in this build's
  current scope names it.
- **Why this is worth a gate line rather than a defect:** the calendar is the metadata expression of
  the 24/7 promise `M4-S04` already carries operationally through `businessHoursSource = None`. It
  earns its place the moment a Severity 1 **entitlement process** exists, because a milestone
  entitlement has no `None` source and must read a process calendar
  (`skills/admin/business-hours-and-holidays/references/gotchas.md` #5). Anyone adding such a
  process in a later phase should point it at this calendar; anyone adding a business-hours-based
  process must not.
- **Remedy:** carry this line to the M4 gate alongside D-M4S01-01/-02; no action needed unless or
  until a Severity 1 entitlement process is scoped.
- **Evidence:** `artefacts/M4-S01/deploy-order.md` § 0 (the consumer table); `plan.json`
  `steps[M4-S02].inputs`, `steps[M4-S03].inputs`, `steps[M4-S04].inputs.note`.

## O-M4S01-02 — UNVERIFIED: whether a midnight-to-midnight start/end pair on every day means "open all day" rather than "closed" cannot be settled from documents alone

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `deploy-order.md` § 4
- **What was recorded:** `Severity 1 24x7` writes `00:00:00.000Z`–`00:00:00.000Z` on all seven days.
  Three sources now stand behind that shape — `references/gotchas.md` #1 (the shipped 24/7
  `Default` calendar stores every day the same way and states the pair "means open the whole day");
  `references/examples.md` Example 1, which since commit `5b206697a` carries this exact calendar as
  a documented worked example; and the Metadata API Developer Guide (`api_meta`
  L111304–111306), which documents `00:00:00.000Z` on the `*EndTime` fields as **"midnight"** — the
  value's meaning, not the pair's. `references/gotchas.md` #6 is unchanged and still marks the pair
  UNVERIFIED: from the documented shape alone, "open 24 hours" and "closed" are indistinguishable,
  and the skill's own prescribed resolution is not a document but an org — set one day closed and
  one day 24-hour in Setup, retrieve, and compare.
- **Why it stays open:** this build is `design-only` and has no org connection, so the prescribed
  clock test cannot be run here. The worked-example addition in `5b206697a` narrowed the *positional*
  question (where `saturday*`/`sunday*` sit in the element sequence) but settled neither this pair's
  semantics nor whether the Metadata API enforces a different child-element order than the sample
  shows.
- **Remedy:** before trusting `Severity 1 24x7` in any org, run the clock test
  `holiday-maintenance-runbook.md` § 5 describes, against a sandbox, ahead of any production deploy;
  this is a pre-deploy gate item, not a rebuild of this step's artefact.
- **Evidence:** `artefacts/M4-S01/deploy-order.md` § 4 ("UNVERIFIED — the midnight pair");
  `skills/admin/business-hours-and-holidays/references/gotchas.md` #1, #6;
  `artefacts/M4-S01/holiday-maintenance-runbook.md` § 5.

## O-M4S01-03 — Skill-depth signal: `check_rtm.py` derives a per-calendar key inside `Settings:BusinessHours`, and the container-level row cannot also satisfy it

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the RTM checker run over
  `traceability.md` after this step's two rows were added
- **What was recorded:** `check_rtm.py --manifest-dir artefacts` reports **3 orphans** —
  `BusinessHoursEntry:US Support`, `BusinessHoursEntry:EMEA Support` and `BusinessHoursEntry:Severity
  1 24x7`, all evidenced by `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml` — exit 0, 0
  errors, 0 coverage gaps, 39 rows, 1 warning (this orphan WARN). The pre-existing two `M1-S01`
  `BusinessProcess` file-stem orphans (`decisions.md` D-M1S01-03) are unaffected and still counted
  separately in earlier linter runs' history; this run's 3 are new, all from `M4-S01`.
- **Why, read from the script:** `SETTINGS_ENTRIES` maps the `businesshours` settings stem to
  `("BusinessHoursEntry", "businessHours", "name")`. For any `Settings` component whose stem matches,
  `index_manifest()` registers the container-level member `package.xml` actually declares
  (`Settings:BusinessHours`, evidenced by `package.xml` — the form `REQ-038` and
  `workbook/06-automation.md` `CWB-AUT-013` both name, matching every other Settings row in this
  build) **and, separately**, one `BusinessHoursEntry:<name>` key per `<businessHours>` block read
  **inside** the file, exactly the same shape `RULE_CONTAINERS` already uses for
  `AssignmentRules`/`AutoResponseRules` (`decisions.md` **O-M3S04-03**) and structurally identical to
  the `EmailTemplate` folder-qualification mismatch (`decisions.md` **O-M3S02-05**) before it. The
  script's own comment names the intent — "Index the entries so a row can name one" — but
  `resolve_artefact()` still matches a row's `artefact` cell against these keys by exact string, so
  naming the deployable container (`Settings:BusinessHours`, what actually appears in `package.xml`
  and what every reader of this build's other Settings rows expects) can never also satisfy three
  independently-orphanable per-entry keys.
- **Alternative rejected:** renaming `REQ-038`'s `artefact` cell to one calendar's singular form
  (e.g. `BusinessHoursEntry:US Support`) to quiet two-thirds of the warning while still missing the
  third, or minting three additional rows purely to name each calendar. Both rejected for the same
  reason `O-M3S02-05` and `O-M3S04-03` already give: renaming the cell would make the row describe a
  component nobody deploys as such (the Metadata API deploys `Settings:BusinessHours`, not three
  separate members), and minting rows with no requirement behind them is the anti-pattern
  `agents/build-doc-keeper/AGENT.md`'s Output Contract guards against — a traceability row exists to
  join a requirement to a delivery, not to pre-empt a specific checker's per-entry key derivation.
- **Remedy:** record `admin/requirements-traceability-matrix`'s `check_rtm.py` `SETTINGS_ENTRIES`
  deriver as a third instance of the same skill-depth gap `O-M3S02-05` and `O-M3S04-03` name: a
  derived sub-key should be additive evidence toward the *same* orphan check as its container key
  (matching by container membership, not treated as a second, independently-orphanable component).
  All three instances now point at one fix in one place (`resolve_artefact()`'s key-matching logic),
  not three separate patches.
- **Evidence:** `skills/admin/requirements-traceability-matrix/scripts/check_rtm.py`
  (`SETTINGS_ENTRIES`, `index_manifest()`, `resolve_artefact()`); `traceability.md` §
  "Linter result — after M4-S01"; `artefacts/M4-S01/package.xml`;
  `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml`.

## D-M4S02-01 — Checker-policy block on the First Response milestones' missing `<timeTriggers>`/`<successActions>` closed at the skill, not the artefact: the flywheel record

- **Date:** 2026-09-12 · **Step:** `M4-S02` (`sla`) · **Agent:** `metadata-builder` (blocked run
  `2026-09-12T07-20-25Z`; closed at re-run `2026-09-12T07-45-00Z`); recorded here by
  `build-doc-keeper`
- **Kind:** skill gap — the gap the runner recorded verbatim when it set the step `blocked`
- **What was recorded:** the step's own declared checker, `check_entitlements_and_milestones.py
  --manifest-dir artefacts --strict`, rejected both entitlement processes: `WARN W4 … Milestone
  '… / First Response' has neither <timeTriggers> nor <successActions>. It counts down and
  nothing observable happens at any point.` — `0 error(s), 2 warning(s), 0 info note(s)`,
  `--strict: failing on 2 warning(s)`, `EXIT=1`. Clearing W4 as it then read required a
  `WorkflowAlert` or `WorkflowFieldUpdate` referenced from `<timeTriggers>`, and two facts made
  that unsatisfiable from this step's own inputs: no step anywhere in `plan.json` builds a
  `Workflow` file, and no clarification (the full Q38–Q53, Q90–Q92 group was read) names a
  milestone notification's recipient, offset, sender or template — only `M4-S04`'s escalation
  rule has an answered notify question (Q45), and it is a different component. `agents/build-step-
  runner` set the step `blocked` with reason `ambiguity` rather than force a repair, because the
  two repairs that would have passed the gate were each worse than the block: repair A named a
  `WorkflowAlert` (`First_Response_Warning`) that exists in no step and no clarification, which
  `metadata-examples.md` § 3 says fails the whole deploy rather than just the milestone; repair B
  used an action-less `<timeTriggers>` shape the skill documented nowhere. Both were verified on
  scratch copies outside the build directory — same checker exit (`0/0/2 info`, EXIT=0) for both,
  proving the checker cannot distinguish an invented-but-dangling action from no action at all —
  and neither was applied to the artefact.
- **The gap was closed at the skill, not the artefact.** Commit `a18f9164d`
  (`admin/entitlements-and-milestones` v1.1.2) moves the "neither `<timeTriggers>` nor
  `<successActions>`" finding from WARN to INFO, grounded in api_meta.txt:59162–59169 listing both
  elements with no "Required." qualifier (unlike `apiVersion` at api_meta.txt:5481) — making an
  action-less milestone a documented-legal shape, "intended when completion is driven by a
  trigger/flow and no notification is wanted." The same commit splits the stale-`timeLength` case
  that previously shared the W4 code into its own code **W7**, still a strict-promoted WARN, so no
  real check was weakened. The re-run executed the declared command verbatim from the build
  directory against the byte-identical file (SHA-256 confirmed) and observed `EXIT=0` with
  `0 error(s), 0 warning(s), 2 info note(s)`. No repair pass was spent; the file that was rejected
  is the file that now passes.
- **Alternative rejected:** repairing the artefact instead of the rule (the two rejected repairs
  above), amending the acceptance test to drop `--strict` (would have lost the W3 calendar
  cross-reference assertion), and scoping a new `Workflow:Case` step (a re-plan needing new
  clarifications and Case fields no step in this build owns). All three were live options named in
  the blocked run's own envelope; the skill fix pre-empted the need to choose between them.
- **Grounded in:** `envelopes/M4-S02/2026-09-12T07-20-25Z.md` §§ 1, 5 (the block, the two rejected
  repairs); `envelopes/M4-S02/2026-09-12T07-45-00Z.md` §§ 1, 5, 7 (the closure, the verbatim
  re-run, resolved-since list); `skills/admin/entitlements-and-milestones` v1.1.2
  `scripts/check_entitlements_and_milestones.py` (W4 now INFO, W7 split out);
  `artefacts/M4-S02/deploy-order.md` § 0.
- **Evidence:** `plan.json` `steps[M4-S02].runs[1]` (blocked run, result text verbatim), `runs[3]`
  (built run, result text verbatim); `tests/M4-S02/checker_stdout.txt` (`0 error(s), 0 warning(s),
  2 info note(s)`, `EXIT=0`); `tests/M4-S02/checker_exit.txt`.

## D-M4S02-02 — Standard's `minutesToComplete` 720 is a DERIVED placeholder, not an answered value — carried to the M4 gate like the holiday seed

- **Date:** 2026-09-12 · **Step:** `M4-S02` (`sla`) · **Agent:** `metadata-builder` (run
  `2026-09-12T07-20-25Z`, unchanged by the re-run); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a computed value shown rather than asserted, the same shape as
  `decisions.md` D-M4S01-02
- **What was recorded:** Premier's target is not in question — Q38 answers "a first response
  within 4 business hours" and `4 × 60 = 240` is exact. Standard's is: Q38 answers "standard
  accounts within 1 business day," and nothing anywhere in this build converts a business *day*
  into minutes — `minutesToComplete` is a mandatory int (checker rule E1) so the file cannot be
  written without choosing a number. The chain that produced `720`: Q51 makes the Case's calendar
  the SLA authority, so the process calendar is the Case default calendar; Q40/`answers-key.md`
  name that calendar `US Support`; `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml`
  gives `US Support` as 08:00–20:00 Monday–Friday, 12 open hours = 720 business minutes per day.
  Two other readings were considered and rejected as equally defensible and equally unsourced: a
  conventional 8-hour day (`480`, which would also collide numerically with `M4-S04`'s 8-business-
  hour escalation threshold) and "by the end of the next business day" (not expressible — the
  milestone model carries only an integer minute target, no calendar-date element).
- **Alternative rejected:** `480` (a conventional working day) and a next-business-day promise
  (not expressible in the metadata model). Both rejected in `artefacts/M4-S02/deploy-order.md` § 3
  for the reasons above; neither is grounded in any clarification, requirement line, or answered
  assumption in this build.
- **Grounded in:** `plan.json` clarifications `Q38` (answered, "1 business day," no minute
  conversion), `Q51` (answered, Case's calendar is the SLA authority), `Q40`/`answers-key.md`
  (US Support is the default calendar); `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml`
  (`US Support` 08:00–20:00 Mon–Fri); `artefacts/M4-S02/deploy-order.md` § 3.
- **Remedy:** carried to the M4 gate — the Process Owner confirms what "1 business day" means
  contractually (720, 480, or a next-business-day promise needing a different design) before this
  file is deployed to production. The edit is one integer in one file.
- **Evidence:** `artefacts/M4-S02/entitlementProcesses/First_Response_Standard.entitlementProcess-meta.xml`
  (`<minutesToComplete>720</minutesToComplete>`); `artefacts/M4-S02/deploy-order.md` § 3 (the full
  derivation chain and the two rejected readings).

## O-M4S02-01 — `settings/Entitlement.settings-meta.xml` (`enableEntitlements`) is owned by no step in this plan — every file this step writes is inert without it

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `deploy-order.md` § 5 and the
  step's own `outputs[]`
- **What was recorded:** `enableEntitlements` is the org-level master switch for Entitlement
  Management (`metadata-examples.md` § 5) — without it, both `EntitlementProcess` files and the
  `MilestoneType` this step deploys are inert metadata that never fires. `steps[M4-S02].outputs[]`
  does not declare `settings/Entitlement.settings-meta.xml`, and a search of every step's
  `outputs[]` in `plan.json` finds no other step that declares it either. `enableMilestoneStopped
  Time` (`gotchas.md` #10 — turn on *before* go-live, not after the first dispute) lives in the
  same unowned file.
- **Why this is worth a gate line rather than a defect:** no clarification in this build asks
  whether Entitlement Management itself needs enabling as a distinct deployable — Q38–Q53 all
  presume the feature is available and go straight to configuring processes and milestones on top
  of it. Nothing in this step's own scope could have written the setting without inventing an
  `outputs[]` path the plan does not declare.
- **Remedy:** carry this line to the M4 gate alongside `D-M4S02-01`/`-02` — either a plan amendment
  adds `settings/Entitlement.settings-meta.xml` to some M4 step's declared outputs, or the gate
  records enabling it as a manual Setup prerequisite before any of this milestone's metadata is
  deployed.
- **Evidence:** `artefacts/M4-S02/deploy-order.md` § 5 ("What this step does NOT write, and who
  does"); `plan.json` `steps[].outputs[]` (searched, no match for `Entitlement.settings-meta.xml`).

## O-M4S02-02 — Q51 half-honoured: an EMEA case's first-response milestone counts on US hours while its escalation timer counts on EMEA hours

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `deploy-order.md` § 4.4 and the
  builder's own envelope
- **What was recorded:** Q51's answer is "the Case's calendar is the authority for the first-
  response SLA; set the process and milestone calendars to match it explicitly rather than relying
  on a default." This step honours the "explicitly, not by default" half — both processes and both
  milestone overrides name `<businessHours>US Support</businessHours>` outright — but cannot honour
  the "match the Case's calendar" half: an `EntitlementProcess` takes exactly one calendar name and
  has no `businessHoursSource` element (that element belongs to escalation rules, `gotchas.md` #3),
  while `M4-S03`'s before-save Flow stamps `Case.BusinessHoursId` to `EMEA Support` or `US Support`
  from `Account.Region__c` per case. `US Support` was written because it is the org default
  (`<default>true</default>`) and the documented fallback for unknown accounts (Q40).
  `business-hours-and-holidays` `gotchas.md` #5 names this exact divergence as the failure it
  exists to prevent: "a Case with a regional calendar can escalate on the regional clock while its
  first-response milestone counts on the process calendar."
- **The consequence, stated for the gate:** an EMEA-region case's first-response milestone counts
  down on **US Support** hours (08:00–20:00 New York) while its *escalation* timer
  (`businessHoursSource = Case`, Q43) counts on **EMEA Support** hours (08:00–18:00 London). The
  two SLA clocks on one case pause on different holidays and can disagree about how much time has
  elapsed.
- **Remedy, none of it this step's to choose:** (a) accept the divergence and record it at the
  gate; (b) split each tier into a US and an EMEA process — four processes, contradicting
  assumption A27's fixed count of two, a re-plan; or (c) re-point `M4-S04`'s Tier 2 entry to
  `businessHoursSource = Static` on `US Support` so both clocks agree — contradicting Q43's
  answered `businessHoursSource = Case`. Not resolvable inside this step or this documentation
  pass.
- **Evidence:** `artefacts/M4-S02/deploy-order.md` § 4.4; `skills/admin/business-hours-and-
  holidays/references/gotchas.md` #5; `plan.json` clarifications `Q51`, `Q40`, `Q43`; `plan.json`
  `assumptions[A27]`.

## D-M4S04-01 — F-36: `notifyToTemplate is required` closed at the skill, not the artefact: the second flywheel record in M4

- **Date:** 2026-09-12 · **Step:** `M4-S04` (`sla`) · **Agent:** `metadata-builder` (first build
  `2026-09-12T07-22-10Z`; org-rejected by `reports/MOCK-DEPLOY-M4.md` run 1; rebuilt at
  `2026-09-12T07-58-40Z`); recorded here by `build-doc-keeper`
- **Kind:** skill gap — the same flywheel shape `decisions.md` **D-M4S01-01** already names as the
  first instance in this milestone: an org rejection the library could not have caught, closed by
  amending the skill rather than by a one-off artefact patch
- **What was recorded:** the first build set `<notifyCaseOwner>true</notifyCaseOwner>` on both
  escalation actions with no `<notifyToTemplate>` — every worked example in
  `admin/escalation-rules` at v1.1.1 did the same, and the Metadata API guide's `EscalationAction`
  table marks `notifyToTemplate` a plain `string` with no Required marker and no stated dependency
  on `notifyCaseOwner`. `reports/MOCK-DEPLOY-M4.md` run 1 (`checkOnly`, `sfskills-dev`, API 67.0)
  rejected the byte-identical file: `EscalationRules Case: notifyToTemplate is required`. The
  operator reset the step `tested → failed → pending` and re-claimed it `running`.
- **The gap was closed at the skill, not the artefact.** Commit `9ae71856d`
  (`admin/escalation-rules` v1.1.2) adds rule **E10** (ERROR: `notifyCaseOwner` true or a populated
  `notifyTo` with no `notifyToTemplate`), rule **I4** (INFO: a template reference that is not
  folder-qualified), `references/gotchas.md` **#13** carrying the org's exact error text, and
  `llm-anti-patterns.md` **Anti-Pattern 6**. Re-running the declared checker against the
  byte-identical first-build file after the skill update produced two `ERROR E10` lines — the
  rule now bites on the file that had passed an hour earlier. The rebuild added one
  `<notifyToTemplate>case_intake/Case_Escalated_To_Tier2</notifyToTemplate>` to each of the two
  `escalationAction` blocks and changed nothing else — same rule, same two entries and order, same
  criteria, clocks and 480-minute threshold, same `assignedTo`/`assignedToType`/`assignedToTemplate`,
  still `<active>false</active>`, `package.xml` untouched. The checker then exited 0 (`W1` + two
  `I3`, no `I4` — both references are folder-qualified).
- **What this is not:** the first build was not careless. The constraint was only discoverable
  against a live org, exactly as `D-M4S01-01`'s checker-policy gap was — "the builder should have
  known" is the wrong lesson for either. It is now in the skill, so the next build that sets
  `notifyCaseOwner` gets the check for free, and a future deploy fails at the checker rather than
  at the org.
- **Alternative rejected:** none — there was no artefact-level alternative once the org's rule was
  known; the single grounded fix is to name the template the constraint requires, and the template
  itself was resolved from the plan's upstream outputs rather than invented (see `D-M4S04-04` for
  which template and why one, not two).
- **Grounded in:** `reports/MOCK-DEPLOY-M4.md` run 1; `envelopes/M4-S04/2026-09-12T07-58-40Z.md`
  §§ 1, 4 (the before/after checker output); `admin/escalation-rules` v1.1.2
  `references/metadata-examples.md` § "Verification: E10 catches the missing `notifyToTemplate`
  before the deploy does"; `artefacts/M4-S04/deploy-order.md` § 0.
- **Evidence:** `plan.json` `steps[M4-S04].runs[3]` (mock-deploy failure, F-36); `runs[5]`
  (rebuilt); `tests/M4-S04/checker_stdout.txt` (post-rebuild `EXIT=0`).

## O-M4S04-01 — R2 confirmed real, closing `O-M3S04-02`'s open check: `notifyCaseOwner` on a Billing-owned case posts into a live Email-to-Case intake address — M4 gate item, three remedies

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from the `M4-S04` builder envelope
  (both builds) and `artefacts/M4-S04/escalation-activation-runbook.md` § 4 R2
- **What was recorded:** `decisions.md` **O-M3S04-02** asked the next step that adds a
  notification to the `Billing` entry to confirm it does not post into `billing@acme.example`
  itself before doing so. `M4-S04` is that step: `notifyCaseOwner` is `true` on both entries
  (Q45), the case owner at escalation time is whichever queue `M3-S04`'s assignment rule placed
  the case in, and the `Billing` queue's `<email>` is `billing@acme.example`
  (`artefacts/M2-S04/queues/Billing.queue-meta.xml`) — the same address `M3-S03` configured as a
  live Email-to-Case routing address. **The answer is that the exposure is real:** an escalation
  notification to that address becomes a new case, which itself escalates 480 minutes later and
  notifies it again. The F-36 rebuild (`D-M4S04-01`) makes this concrete rather than theoretical —
  before `notifyToTemplate` was added, `notifyCaseOwner` could not actually send mail at all; after
  it, the mail R2 describes actually sends.
- **Because the rule ships `<active>false</active>`, nothing loops on deploy.** This is an
  **activation** prerequisite, not a deployment defect — recorded as an M4 **gate** item, not a
  blocker to `documented`.
- **Three remedies, none of which this step (or this documentation pass) may choose** — each needs
  an answer this build does not hold:

  | Option | What it needs |
  |---|---|
  | a. Exclude Billing-owned cases from escalation (a third entry, or a criterion on entry 2) | An answer saying finance cases do **not** escalate to Tier 2 Engineering — `requirement.md` L16 says "anything untouched", unqualified, so narrowing it is not this agent's to invent, the same restraint `D-M3S04-02` exercised |
  | b. Drop `notifyCaseOwner` and rely on `assignedToTemplate` alone | Accepting that the notify half of Q45 may reach nobody, given the `assignedToTemplate` recipient is itself unverified (`deploy-order.md` § 3 U3) |
  | c. Give the `Billing` queue a notification address that is not an intake address | A Finance mailbox nobody has named — `D-M2S04-02` already refused to invent the equivalent address for Tier 2 |
- **Alternative rejected:** choosing one of the three remedies unilaterally in this documentation
  pass. Rejected because a traceability/decisions record exists to state what was found and built,
  not to pre-empt a process-owner call none of the seven answered clarifications on this step
  makes.
- **Grounded in:** `decisions.md` **D-M2S04-04** (the risk first named, latent), **O-M3S04-02**
  (the open check this entry closes); `artefacts/M4-S04/escalation-activation-runbook.md` § 4 R2;
  `artefacts/M4-S04/deploy-order.md` § 5.
- **Evidence:** `artefacts/M2-S04/queues/Billing.queue-meta.xml` (`<email>`);
  `artefacts/M3-S03/settings/Case.settings-meta.xml` line 32 (the same address as a routing
  address); `envelopes/M4-S04/2026-09-12T07-22-10Z.md` § 9 ("Concerning", R2, high).

## D-M4S04-02 — Both entries carry `minutesToEscalation` 480; Severity 1's threshold is a composed reading of `requirement.md`, not an answered value

- **Date:** 2026-09-12 · **Step:** `M4-S04` (`sla`) · **Agent:** `metadata-builder` (run
  `2026-09-12T07-22-10Z`, unchanged by the F-36 rebuild); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a value composed from the weakest of four Step 4 sources
  (`requirement.md` itself) rather than read off an answered clarification, the same shape
  `decisions.md` **D-M4S01-02**'s holiday seed already carries for this milestone
- **What was recorded:** Q46 binds one number, 480 minutes, and its own acceptance test asserts it
  for the Tier 2 entry only. `requirement.md` L16 states one threshold ("anything untouched for 8
  business hours escalates to Tier 2") and L18 says only that Severity 1 outages "are 24/7 and
  never pause" — it does not give Severity 1 a *faster* threshold, and no clarification asks for
  one. Writing a shorter Severity 1 value would have been an invented SLA; entry 1 therefore
  carries the same 480 as entry 2, and the difference between the two entries is the clock
  (`businessHoursSource None` vs `Case`), not the number.
- **Alternative rejected:** inventing a shorter Severity 1 threshold (e.g. treating a 24/7
  severity as implying a faster SLA) on the reasoning that a Severity 1 outage "should" escalate
  sooner. Rejected because no source — not `requirement.md`, not any answered clarification —
  states a Severity 1-specific number, and a builder-composed number would read as a customer
  commitment nobody made.
- **Grounded in:** `requirement.md` L16, L18; `plan.json` clarifications `Q46` (answered, 480
  minutes, Tier 2 entry only), `Q43` (answered, the per-entry calendar split); `envelopes/M4-
  S04/2026-09-12T07-22-10Z.md` § 4 ("On the Severity 1 480").
- **Remedy:** if Acme intends Severity 1 to escalate sooner than 8 business-hour-equivalent
  minutes, that is an answer this build does not hold and a one-line change to entry 1's
  `minutesToEscalation` — carried to the M4 gate rather than guessed here.
- **Evidence:** `artefacts/M4-S04/escalationRules/Case.escalationRules-meta.xml` (both entries'
  `<minutesToEscalation>480</minutesToEscalation>`); `artefacts/M4-S04/deploy-order.md` § 4 item 1.

## D-M4S04-03 — Q42's `CaseCreation` clock start is narrower than `requirement.md`'s word "untouched"

- **Date:** 2026-09-12 · **Step:** `M4-S04` (`sla`) · **Agent:** `metadata-builder` (run
  `2026-09-12T07-22-10Z`, unchanged by the F-36 rebuild); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — an answered clarification whose effect diverges from the
  requirement's own wording, named explicitly rather than left for a reader to notice
- **What was recorded:** `escalationStartTime` is `CaseCreation` and `disableEscalationWhenModified`
  is `false` on both entries (Q42). `requirement.md` L16 reads "anything **untouched** for 8
  business hours escalates to Tier 2" — as built, a case an agent is actively working still
  escalates 480 minutes after **creation**, because the clock measures from creation and no edit
  stops it. That is narrower than "untouched": a literal reading of the word would restart or
  suppress the clock on activity, which is exactly the `CaseLastModified` / `disableEscalationWhen
  Modified` alternative Q42's own answer declines.
- **Why the narrower reading was chosen, not a default:** Q42's answer states the reason directly —
  "because the requirement measures from creation, not from last touch" — and
  `references/gotchas.md` #6 gives the operational reason the alternative is worse here: with
  `CaseLastModified`, any automation write pushes the threshold out, and in an org with chatty
  automation (this build has at least the assignment rule and, once built, `M4-S03`'s flow) a case
  can escalate never. `gotchas.md` #7 is the third lever
  (`disableEscalationWhenModified` `true`, "any touch ends escalation"), also declined for the
  same reason. All three are explicit choices per Q42's answer, not a default.
- **Alternative rejected:** `escalationStartTime = CaseLastModified`, and
  `disableEscalationWhenModified = true`. Both rejected per Q42's own stated reasoning above.
- **Grounded in:** `requirement.md` L16; `plan.json` clarification `Q42` (answered); `skills/
  admin/escalation-rules/references/gotchas.md` #6, #7.
- **Remedy:** none required to deploy — this is the one place the built behaviour and the
  requirement's literal wording diverge, worth re-reading at the M4 gate rather than discovering
  in UAT, not a defect to fix.
- **Evidence:** `artefacts/M4-S04/escalationRules/Case.escalationRules-meta.xml` (both entries'
  `<escalationStartTime>CaseCreation</escalationStartTime>`,
  `<disableEscalationWhenModified>false</disableEscalationWhenModified>`); `artefacts/M4-
  S04/deploy-order.md` § 4 item 3.

## D-M4S04-04 — U6: one escalation template serves both `notifyToTemplate` and `assignedToTemplate`, where the cited skill's example uses two

- **Date:** 2026-09-12 · **Step:** `M4-S04` (`sla`) · **Agent:** `metadata-builder` (introduced at
  the F-36 rebuild, run `2026-09-12T07-58-40Z`); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a build-scope limitation (one template exists, not two) accepted
  rather than worked around by inventing a component
- **What was recorded:** the two elements address **different recipients** —
  `assignedToTemplate` is the template for the email sent to the new owner (the
  `Tier_2_Engineering` queue), and `notifyToTemplate` (added by the F-36 rebuild, `D-M4S04-01`) is
  the template for the notification to the outgoing case owner `notifyCaseOwner` selects. The
  cited skill's own worked example uses two distinct templates for exactly this reason. This build
  holds **one** escalation template: `M3-S02` is titled "Classic acknowledgement and escalation
  email templates" and its `outputs[]` declares exactly two templates in total —
  `case_intake/Case_Acknowledgement` (customer-facing) and `case_intake/Case_Escalated_To_Tier2`
  (the one escalation template). No clarification and no line of `requirement.md` asks for a
  second, owner-warning template. So both elements name
  `case_intake/Case_Escalated_To_Tier2` — the outgoing owner and the incoming Tier 2 queue receive
  the same body, whose subject reads correctly in both directions but is one template doing two
  jobs.
- **Alternative rejected:** inventing a second template name (e.g.
  `case_intake/Case_Escalation_Warning`). Rejected on two independent grounds, either sufficient:
  it is a component no step in this build produces, so the deploy would fail on the reference
  rather than on the rule; and naming a template nobody wrote is the same class of invention
  `decisions.md` **D-M2S04-02** already refused for the Tier 2 mailbox address.
- **Grounded in:** `skills/admin/escalation-rules` worked example (two templates,
  `unfiled$public/Sev1_Handover` / `unfiled$public/Sev1_Escalation_Warning`); `plan.json`
  `steps[M3-S02].outputs[]` (exactly two templates, total); `artefacts/M4-S04/deploy-order.md`
  § 3 U6.
- **Remedy:** carried to the M4 gate, not fixed here — if Acme wants a distinct "your case was
  escalated away from you" notice, that is a new `EmailTemplate` on a `ui` step and a one-line
  change to this rule's `notifyToTemplate`.
- **Evidence:** `artefacts/M4-S04/escalationRules/Case.escalationRules-meta.xml` (both actions'
  `<assignedToTemplate>` and `<notifyToTemplate>`, identical values);
  `artefacts/M4-S04/escalation-activation-runbook.md` § "R6".

## D-M4S05-01 — F-37: `TestDataFactory` unresolved in a real org, closed by shipping the template as a declared output — the third flywheel-adjacent record in this build, and the one no skill fix could close

- **Date:** 2026-09-12 · **Step:** `M4-S05` (`automation`) · **Agent:** `apex-builder` (first build
  `2026-09-12T08-12-19Z`; rejected by the operator's dry-run validation `2026-09-12T08:27:29Z`;
  rebuilt `2026-09-12T08-32-00Z`); recorded here by `build-doc-keeper`
- **Kind:** deviation — the rebuild added two declared outputs
  (`classes/TestDataFactory.cls`, `classes/TestDataFactory.cls-meta.xml`) that the step's original
  `outputs[]` never named, per `amend-step`'s own recorded reason (`plan.json`
  `steps[M4-S05].amendments[0]`)
- **What was recorded:** `CaseMilestoneServiceTest` calls `TestDataFactory.createAccounts(...)`
  and `TestDataFactory.createCases(...)`, which the step's `templates[]` and
  `skills/apex/entitlement-apex-hooks/references/code-examples.md` both cite by repo-relative
  path. `templates/README.md` is explicit that a template under `templates/` is a canonical
  building block **copied into the consuming project**, not a deploy-time reference an org can
  resolve — and no step in this plan shipped the class. The first build's four declared acceptance
  tests (checker, `xml`, `manifest`, manual) and `check-outputs` all passed anyway, because none of
  them resolves a symbol across files: `check_entitlement_apex_hooks.py` reads one tree for
  `CaseMilestone` mistakes and has no cross-class symbol resolution, `check-outputs` confirms
  declared paths rather than references, and there is no offline Apex compiler in the `sf` CLI
  (`agents/_shared/AGENT_CONTRACT.md` Gate C row 3). It took `reports/MOCK-DEPLOY-M4.md` run 2 — a
  real `sf project deploy start --dry-run` against `sfskills-dev` — to reject `ApexClass
  CaseMilestoneServiceTest` five times with `Variable does not exist: TestDataFactory`.
- **The gap is a library gap, and no artefact-level repair alone closes it.** The operator reset
  the step `tested → failed → pending`, amended `outputs[]` to add the factory class and its meta
  XML, and re-claimed it. The rebuild shipped `classes/TestDataFactory.cls` as a **byte-identical**
  copy of `templates/apex/tests/TestDataFactory.cls` (`diff` empty) — the template itself was not
  edited, and no method was added, because the test's two calls already match signatures the
  template already defines. `reports/MOCK-DEPLOY-M4.md` F-37 names the durable remedy, carried to
  planner v6: `apex/entitlement-apex-hooks` and the `apex-builder` playbook should state that a
  test referencing a template class ships that class in the same step (or an earlier step the plan
  owns), and a build with more than one Apex step should route this through a shared "Apex
  foundations" step rather than repeat the same fix per step (see **D-M4S05-05** below).
- **Alternative rejected:** writing a step-local test-data helper instead of shipping the
  canonical `TestDataFactory` template. Rejected because `AGENT_RULES.md`'s template-reuse rule
  and `agents/_shared/AGENT_CONTRACT.md` rule 2 both forbid re-inventing a canonical idiom inline
  once a template exists for it — a parallel implementation would have been a second class doing
  the same job as the one already in `templates/apex/tests/`, not a fix to the citation problem.
- **Grounded in:** `reports/MOCK-DEPLOY-M4.md` run 2 (F-37, the rejection) and run 3 (closure
  confirmed — all four Apex classes and the trigger compiled); `envelopes/M4-S05/2026-09-12T08-32-00Z.md`
  §§ 1, 5 (findings `AB-M4S05-05`, `AB-M4S05-06`); `artefacts/M4-S05/deploy-order.md` § 0;
  `templates/README.md` (template-vs-deploy-reference distinction).
- **Evidence:** `plan.json` `steps[M4-S05].amendments[0]` (who, when, why, prior `outputs[]`
  value); `steps[M4-S05].runs[]` (the mock-deploy failure entry and the rebuilt-run entry);
  `tests/M4-S05/results.json` (checker now scans 4 Apex files, `0 ERROR, 0 WARN`, versus 3 on the
  superseded pre-rebuild run).

## D-M4S05-02 — The completion signal is a proxy ("leaves Status `New`"), and Q50's recorded answer named a different one — held open as an M4 gate decision

- **Date:** 2026-09-12 · **Step:** `M4-S05` (`automation`) · **Agent:** `apex-builder` (run
  `2026-09-12T08-12-19Z`, unchanged by the F-37 rebuild); recorded here by `build-doc-keeper`
- **Kind:** design trade-off, held open as a milestone-gate decision — the same shape
  `decisions.md` **D-M3S02-04**, **D-M3S03-02** and **D-M3S04-03** already carry for this build:
  the artefact takes a defensible reading and the gate is where the alternative reading gets its
  say
- **What was recorded:** `D10` settled the completion **mechanism** — an after-update Apex trigger
  on `Case` stamping `CaseMilestone.CompletionDate` — but no clarification settles the completion
  **event**, the Case change that means "the agent has responded." `Q50`'s recorded answer names
  *"satisfiable completion criteria on the first outbound `EmailMessage`, or a Flow that stamps
  `CompletionDate`"* — the first outbound email is the signal that answer has in mind. No
  clarification in the `Q38`–`Q53` SLA group names a `Case` field change as the signal instead.
  What this step implemented is narrower and Case-only: the milestone completes the moment a Case
  **leaves `Status = New`** — the transition `skills/apex/entitlement-apex-hooks/references/examples.md`
  Example 1 documents, and the one transition both of this build's business processes share
  (`New → Escalated → Closed` on `Support_Process`; `New → Closed` on `Billing_Process`,
  `artefacts/M1-S01/objects/Case/businessProcesses/`).
- **Why a proxy, not the requirement.** A case can leave `New` without a customer-facing reply (an
  agent triaging and escalating it untouched), and an agent can reply without leaving `New`. The
  literal signal Q50 names — the first outbound `EmailMessage` — is a **different artefact**: an
  after-insert trigger on `EmailMessage` filtered to `Incoming = false`, which this step's
  `outputs[]` does not declare and this step did not write. The rule is held in one named,
  `@TestVisible` constant (`OPENING_STATUS`) specifically so that changing the signal later is a
  one-line edit, not a rewrite.
- **Alternative rejected:** planning the `EmailMessage`-triggered artefact as part of this step.
  Rejected because it is a distinct component this step's declared `outputs[]` does not name — per
  `standards/build-orchestration.md` § 4 borrowed-agent condition 2, an agent declares only the
  outputs its contract and the step's own `outputs[]` name — and because choosing between the two
  readings is a business-process call this documentation pass has no answered clarification to
  resolve, the same restraint `decisions.md` **D-M3S04-02** exercised for a criterion `M3-S04`
  chose not to invent.
- **Grounded in:** `envelopes/M4-S05/2026-09-12T08-12-19Z.md` finding `AB-M4S05-01`;
  `artefacts/M4-S05/deploy-order.md` § 3; `plan.json` `clarifications[Q50, Q16]`, `decisions[D10]`;
  `artefacts/M1-S01/objects/Case/businessProcesses/`.
- **Evidence:** `artefacts/M4-S05/classes/CaseMilestoneService.cls` (the `OPENING_STATUS`
  `@TestVisible` constant and the query filtering on it); `artefacts/M4-S05/deploy-order.md` § 3
  (the not-implemented `COMPLETING_STATUSES` set and why).

## D-M4S05-03 — The two-file trigger shape (trigger calling the service directly) ships with no recursion guard or `TriggerControl` kill switch, because no step in this build deploys the base classes a handler needs

- **Date:** 2026-09-12 · **Step:** `M4-S05` (`automation`) · **Agent:** `apex-builder` (run
  `2026-09-12T08-12-19Z`, unchanged by the F-37 rebuild); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a build-scope limitation accepted rather than worked around, the
  same shape `decisions.md` **D-M4S04-04** already carries for a template gap
- **What was recorded:** `skills/apex/entitlement-apex-hooks/references/code-examples.md` and
  `skills/apex/apex-design-patterns` both ship a **four-file** bundle — service, trigger, test, and
  `CaseMilestoneTriggerHandler.cls`, a subclass of `templates/apex/TriggerHandler.cls`. This step
  wrote the **two-file** shape instead — the trigger calls the service directly — which is the
  shape `skills/apex/entitlement-apex-hooks/references/examples.md` Example 1 documents. Two facts
  settled it: `plan.json` `steps[M4-S05].outputs[]` declares three components and a handler is not
  one of them, and a search of `plan.json` for `TriggerControl`, `ApplicationLogger` and
  `Trigger_Setting__mdt` returns **zero** occurrences in any step's `outputs[]` — `TriggerHandler`
  appears exactly once, in this step's own `templates[]`, which is an instruction to *read* the
  file, not to deploy it. A handler extending `TriggerHandler` would not compile in the org this
  build produces.
- **What the two-file shape costs, named rather than left implicit:** no recursion guard, no depth
  counter, no `skipOnce()`, and no `TriggerControl` kill switch to disable the trigger from Setup
  without a deploy. What is **not** missing is the idempotency guard that matters in this specific
  domain — `CompletionDate = NULL` in the query means a second pass finds nothing to stamp, and the
  test method `skipsAMilestoneThatIsAlreadyCompleted` asserts it — which is arguably the stronger
  of the two protections for a trigger that only ever runs once per Case's lifetime.
- **Alternative rejected:** writing the handler shape without shipping `TriggerControl` and
  `Trigger_Setting__mdt`. Rejected because it would not compile in this build's org — declaring an
  output the plan does not carry the dependencies for is not a remedy, per
  `standards/build-orchestration.md` § 4 borrowed-agent condition 2.
- **Grounded in:** `envelopes/M4-S05/2026-09-12T08-12-19Z.md` finding `AB-M4S05-02`;
  `artefacts/M4-S05/deploy-order.md` § 2; `skills/apex/entitlement-apex-hooks/references/examples.md`
  Example 1; `skills/apex/apex-design-patterns`.
- **Evidence:** `plan.json` `steps[M4-S05].outputs[]` (three components, no handler); the
  builder's own plan-wide search recorded in `deploy-order.md` § 2
  (`TriggerControl=0, ApplicationLogger=0, Trigger_Setting__mdt=0, TriggerHandler=1`, the one
  occurrence being this step's `templates[]` citation).
- **Remedy, if the build wants the handler shape:** a plan amendment adding
  `classes/CaseMilestoneTriggerHandler.cls` (+ meta) to this step's `outputs[]` and the three
  template components to some step's outputs, then a rebuild — carried to the M4 gate as an open
  item, not fixed here.

## D-M4S05-04 — `CaseMilestoneServiceTest` is forced to `@IsTest(SeeAllData=true)` because `SlaProcess` and `CaseMilestone` carry no `create()` call; an active `SlaProcess` with a `First Response` milestone is now a deploy/gate prerequisite

- **Date:** 2026-09-12 · **Step:** `M4-S05` (`automation`) · **Agent:** `apex-builder` (run
  `2026-09-12T08-12-19Z`, unchanged by the F-37 rebuild); recorded here by `build-doc-keeper`
- **Kind:** design trade-off, held open as a milestone-gate prerequisite — the same shape
  `decisions.md` **D-M3S04-03** already carries for `support-noreply@acme.example`: a platform
  constraint the builder did not choose and cannot repair from the artefact side
- **What was recorded:** two objects in the chain this test needs cannot be created in Apex —
  `SlaProcess` and `CaseMilestone` — while `MilestoneType` and `Entitlement` can. The test can build
  the `Entitlement` and the `MilestoneType`, but not the `SlaProcess` that joins them and not the
  `CaseMilestone` rows that are the thing under test; both must come from the org. That forces
  `@IsTest(SeeAllData=true)` on the whole class and rules out combining it with
  `@IsTest(IsParallel=true)` — the two annotations cannot coexist. `requireActiveProcess()` asserts
  on the org state directly, with a message naming what is missing, rather than returning early,
  so a skipped assertion here is not mistaken for a passing one.
- **What the target org must satisfy before this test proves anything, named as gate/deploy
  prerequisites rather than left implicit:** (1) an **active** `SlaProcess` exists; (2) that
  process includes a milestone whose `MilestoneType.Name` is exactly `First Response` — a Setup
  rename returns zero rows, which the automation treats as silence, not an exception; (3)
  `Status = 'Closed'` is reachable for the running user's default Case record type; (4) every Case
  the test builds carries `Origin = 'Web'` and `Priority = 'Medium'`, because `TestDataFactory`'s
  own defaults (`Origin = 'Email'`, no `Priority`) are rejected by `M3-S01`'s two active validation
  rules (`Origin_Must_Be_Known`, `Priority_Required_On_Agent_Save`) — supplied through the
  factory's own `overrides` map in `CaseMilestoneServiceTest.caseOverrides(Id)`, not by editing the
  factory's shared defaults (see **D-M4S05-05**'s reasoning for why the factory itself was left
  untouched).
- **Alternative rejected:** none — this is a documented platform constraint (the Apex Testing
  Guide lists `SlaProcess` and `CaseMilestone` among objects a test cannot `insert`), not a design
  choice the builder made. The one thing that was a choice — passing `Origin`/`Priority` overrides
  through the test rather than changing `TestDataFactory`'s shared defaults — is the right side of
  the line: the factory's defaults are shared across every future consumer, and this build's
  validation rules are not.
- **Grounded in:** `artefacts/M4-S05/deploy-order.md` § 4 (the prerequisite table and the four
  proof methods); `skills/apex/entitlement-apex-hooks` (the `SeeAllData` constraint as documented);
  `templates/apex/tests/TestDataFactory.cls:57-70` (the `overrides` map).
- **Evidence:** `artefacts/M4-S05/classes/CaseMilestoneServiceTest.cls`
  (`@IsTest(SeeAllData=true)`, `requireActiveProcess()`, `caseOverrides(Id)`);
  `artefacts/M3-S01/objects/Case/validationRules/` (the two rules the overrides satisfy).

## D-M4S05-05 — `TestDataFactory` ships as a step-local copy of a shared template; a second Apex step declaring the same output would deploy the same class twice under one `package.xml` member, not merge with it

- **Date:** 2026-09-12 · **Step:** `M4-S05` (`automation`) · **Agent:** `apex-builder` (rebuild run
  `2026-09-12T08-32-00Z`); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a build-scope limitation accepted because it costs nothing today,
  the same shape `decisions.md` **D-M4S04-04** already carries for a single shared template
  serving two recipients
- **What was recorded:** `classes/TestDataFactory.cls` is now a **step-local** copy of
  `templates/apex/tests/TestDataFactory.cls` (byte-identical, per **D-M4S05-01**). `M4-S05` is the
  only Apex step in this plan, so nothing duplicates today. But a second Apex step whose plan
  declared the same output path would deploy the **same class twice under one `package.xml`
  member** — a deploy conflict, not a merge — because `package.xml` names a member once and two
  steps writing the identical file to the identical path is not a case the manifest aggregation
  (`M5-S05`) can reconcile by itself. The same collision would apply to
  `TriggerHandler`/`TriggerControl`/`ApplicationLogger` if the handler shape named in **D-M4S05-03**
  is ever adopted by a later step.
- **Alternative rejected:** none chosen now — there is nothing to choose between while this is the
  only Apex step. The remedy `reports/MOCK-DEPLOY-M4.md` F-37 and this step's own `apex-builder`
  envelope both name for the future is a **planner v6** backlog item: a shared "Apex foundations"
  step whose `outputs[]` carry `TestDataFactory` (and the trigger-framework classes, if adopted),
  with every Apex step `depends_on` it rather than shipping its own copy.
- **Grounded in:** `envelopes/M4-S05/2026-09-12T08-32-00Z.md` finding `AB-M4S05-07`;
  `artefacts/M4-S05/deploy-order.md` § 0, § 6; `reports/MOCK-DEPLOY-M4.md` F-37's remedy line.
- **Evidence:** the builder's plan-wide search recorded in `deploy-order.md` § 0 ("one step of type
  automation owned by `apex-builder`" — confirming no second Apex step exists yet to collide with);
  `plan.json` `steps[M4-S05].outputs[]` (now 8 paths, including the factory class and its meta).

## D-M4S03-01 — F-38: a Create-triggered `FlowTest` takes `InputTriggeringRecordInitial` only, settled over two org round-trips — the fourth flywheel-adjacent record in this build, and the first the skill fix has not yet closed

- **Date:** 2026-09-12 · **Step:** `M4-S03` (`automation`) · **Agent:** `metadata-builder` (first
  build `2026-09-12T08-11-40Z`; rejected by `reports/MOCK-DEPLOY-M4.md` run 2; rebuilt
  `2026-09-12T08-30-00Z`; rejected again by run 3, the mirror error; corrected build
  `2026-09-12T08-40-00Z`); recorded here by `build-doc-keeper`
- **Kind:** skill gap — the same flywheel shape `decisions.md` **D-M4S01-01** and **D-M4S04-01**
  already name in this milestone, and the one `D-M4S05-01` calls "flywheel-adjacent" because no
  skill file closes it: an org-only constraint no checker in the library could have caught, closed
  here at the artefact rather than at the skill, **and the skill fix is still pending** — unlike
  its three predecessors, this entry cannot cite a commit that closes the gap.
- **What was recorded:** the rule the org's two rejections settle is
  `recordTriggerType Create` → `InputTriggeringRecordInitial` **only**; `Update`/`CreateAndUpdate`
  → **both** `Initial` and `Updated`. The first build's `FlowTest` carried `Updated` only and was
  rejected — *"missing a parameter of type InputTriggeringRecordInitial"*. The first rebuild added
  `Initial` **alongside** `Updated` and was rejected again, with the mirror error — *"contains the
  incompatible parameter value `$Record` of type InputTriggeringRecordUpdated. Remove the parameter
  or change the record trigger type."* Only the second rebuild, which removed `Updated` and left
  `Initial` alone, validated. The first rejection is what makes this the first two-round case:
  *"missing `Initial`"* is satisfied by both the two-parameter shape and the correct one-parameter
  shape, so one org round-trip could not distinguish them.
- **Why the guide pointed the wrong way:** `api_meta.txt` L74351–74365 supplies both parameters and
  L74326–74327 enumerates both types with no trigger-type scoping — neither fact is wrong, but the
  sample flow is **update-triggered**, and the only worked `FlowTest` in
  `flow/record-triggered-flow-patterns/references/metadata-examples.md` § 4
  (`Opportunity_AfterSave_ClosedWon`) is explicitly a **transition** test: *"The two `$Record`
  parameters below are what makes this a transition test."* This step inherited that shape for a
  create-triggered flow, where there is no transition to express.
- **The gap is NOT closed at the skill.** `flow/record-triggered-flow-patterns` is being corrected
  in parallel with a Create-triggered `FlowTest` example and a checker rule for the
  `Create → Initial only` direction, but **no skill file was edited by any of these three runs** —
  the artefact was corrected twice against the org directly. The five other artefacts in this step
  (flow, `Flow.settings`, `package.xml`, `flow-governance-policy.yaml`,
  `no-account-fallback-note.md`) are byte-identical across all three builds (SHA-256 confirmed at
  each run); only the `FlowTest` and `deploy-order.md` changed.
- **Alternative rejected:** none chosen — both wrong shapes (two-parameter, then correct-looking
  one-parameter-plus-Updated) were tried in turn and each was org-rejected; the settled rule came
  from the org's two error messages, not from a design choice between named options.
- **What is still open, and carried forward rather than closed here:** the converse half of the
  rule — that `CreateAndUpdate` requires **both** parameters — is inferred from the guide's sample
  and run 3's error text, not observed; no flow in this build is `CreateAndUpdate`. What a
  create-context `Initial` payload means to the engine is also unproven beyond "the record as
  submitted." Both are named `deploy-order.md` § 0 UNVERIFIED items, and the durable remedy —
  adding a Create-triggered `FlowTest` worked example and a `Create → Initial only` checker rule to
  `flow/record-triggered-flow-patterns` — is the § 8 deepen-a-skill signal this entry opens rather
  than closes.
- **Grounded in:** `artefacts/M4-S03/deploy-order.md` § 0; `reports/MOCK-DEPLOY-M4.md` runs 2 and
  3; `api_meta.txt` L74305–74306, L74326–74327, L74351–74365;
  `flow/record-triggered-flow-patterns/references/metadata-examples.md` § 4.
- **Evidence:** `plan.json` `steps[M4-S03].runs[]` (the three `metadata-builder` builds, the two
  `mock-deploy` rejections, the three `step-tester` re-runs); `tests/M4-S03/summary.md` (post-
  correction re-run, `passed: true`).

## D-M4S03-02 — Priority mechanism: G3 (`milestone:M3`) decision (2) supersedes assumption A2's null guard for `Priority`, on the two email origins only

- **Date:** 2026-09-12 · **Step:** `M4-S03` (`automation`) · **Agent:** `metadata-builder` (run
  `2026-09-12T08-11-40Z`, unchanged across the F-38 rebuilds); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — this step implementing an option the gate already chose, not a
  choice made here
- **What was recorded:** the step's `notes` (amendment `2026-09-12T04:50:22Z`, F-27) put two
  options to the builder — derive `Priority` and **overwrite** the Email-to-Case intake default, or
  **accept** `Medium` for email cases — and asked it to say which in `deploy-order.md`. That choice
  was not this step's to make: the `milestone:M3` human gate (**G3**), approved
  `2026-09-12T06:24:17Z`, records it as gate decision (2), confirming `decisions.md`
  **D-M3S03-02** on option 2 — *"M4-S03 derives Priority from Severity__c/Support_Tier__c and
  OVERWRITES the routing-address default for Email-* origins."* This step implements the approved
  option and adds nothing to it. Implemented as one condition set on `Decision_Derive_Priority`:
  `$Record.Origin EqualTo Email-Support` OR `$Record.Origin EqualTo Email-Billing` OR
  `$Record.Priority IsNull`, so the flow may write `Priority` on the two email origins (overwriting
  `M3-S03`'s routing-address `Medium`) or wherever it arrives null.
- **Where assumption A2's null guard still holds, and where it is superseded.** `inputs.note` says
  the flow *"writes only when the field is null and never overwrites an agent's value"*
  (assumption **A2**, from deferred **Q14**). That rule is **unchanged** for `EntitlementId` and
  `BusinessHoursId` — both keep an explicit `IsNull` guard — and for `Priority` on every origin
  other than the two email ones, including `Web` and a manually created Case: a Case matching none
  of the three conditions keeps whatever `Priority` a human typed (`Priority_Entered_By_A_Human_Is_
  Kept`). It is superseded **only** for `Priority` on `Email-Support` and `Email-Billing`, where the
  flow overwrites the routing address's `Medium` per G3 decision (2).
- **Alternative rejected:** none newly rejected by this step — the three-way choice was raised and
  closed at the G3 gate, not here.
- **Grounded in:** `decisions.md` **D-M3S03-02**; `plan.json` `human_gates` `milestone:M3` decision
  (2); `plan.json` `steps[M4-S03].notes` / `amendments[0]` (F-27); `artefacts/M4-S03/deploy-order.md`
  § 0b.
- **Evidence:** `artefacts/M4-S03/flows/Case_BeforeSave_StampEntitlementAndCalendar.flow-meta.xml`
  (`Decision_Derive_Priority`'s three conditions); `artefacts/M4-S03/deploy-order.md` § 0b's
  condition table.

## D-M4S03-03 — The Priority VALUE mapping (Severity 1 → High, Premier → High, else Medium) is derived, not answered — carried to the M4 gate like the holiday seed and the 720-minute placeholder

- **Date:** 2026-09-12 · **Step:** `M4-S03` (`automation`) · **Agent:** `metadata-builder` (run
  `2026-09-12T08-11-40Z`, unchanged across the F-38 rebuilds); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a computed value shown rather than asserted, the same shape as
  `decisions.md` **D-M4S02-02** and **D-M4S01-02**
- **What was recorded:** G3 decision (2) (`D-M4S03-02` above) chose the *mechanism* — derive and
  sometimes overwrite `Priority` — but no answered clarification anywhere in this build states
  which `CasePriority` value a Severity 1, a Premier or a Standard case should end up with;
  `M3-S03`'s own `web-to-case-form-contract.md` § 7 already recorded the same gap from the other
  side. The mapping written into the flow: `Severity__c = Severity 1` → `High`, grounded in
  `requirement.md` L18 ("Severity 1 outages are 24/7 and never pause") — the only unconditional
  urgency statement in the requirement, and `Severity__c` has exactly one value on file.
  `Support_Tier__c = Premier` → `High`, grounded in Q38 (Premier's 4-business-hour promise against
  Standard's 1-business-day) and the fact that G3 decision (2) names `Support_Tier__c` as a
  derivation input, so a rule that never reads it would not implement the approved option — this is
  the weakest row: nothing says a Premier case is *urgent*, only that it is contractually faster.
  Everything else writable → `Medium`, matching `M3-S03`'s own F-27 intake default. `High`/`Medium`
  themselves are copied from `skills/admin/case-management-setup/references/metadata-examples.md`
  § 1 (`CasePriority`, `Medium` carrying `<default>true</default>`); **no `CasePriority` value set
  exists anywhere under `artefacts/`**, so no checker in this build can assert `High` is a value the
  target org actually carries.
- **Alternative rejected:** *severity-only* (`Severity 1` → `High`, everything else `Medium`,
  leaving `Support_Tier__c` unread) — rejected because G3 decision (2) names `Support_Tier__c` as a
  derivation input. *Tier-only* (`Premier` → `High`, `Standard` → `Medium`, ignoring severity) —
  rejected because `requirement.md` L18 is the stronger of the two statements and a Severity 1 case
  on a Standard account would otherwise land `Medium`.
- **Grounded in:** `requirement.md` L18; `plan.json` clarification `Q38` (answered); `plan.json`
  `human_gates` `milestone:M3` decision (2); `skills/admin/case-management-setup/references/
  metadata-examples.md` § 1; `artefacts/M4-S03/deploy-order.md` § 1.
- **Remedy:** carried to the M4 gate — the Process Owner confirms the three rows above before this
  file is deployed to production. The edit is two `<stringValue>` elements in one file, the same
  shape as `D-M4S02-02`'s `720`.
- **Evidence:** `artefacts/M4-S03/flows/Case_BeforeSave_StampEntitlementAndCalendar.flow-meta.xml`
  (`Decision_Derive_Priority`'s outcomes); `artefacts/M4-S03/deploy-order.md` § 1's mapping table.

## D-M4S03-04 — `<apiVersion>67.0</apiVersion>`, matching the cited template and the build-wide floor, not the cited skill's own 66.0 worked examples

- **Date:** 2026-09-12 · **Step:** `M4-S03` (`automation`) · **Agent:** `metadata-builder` (run
  `2026-09-12T08-11-40Z`, unchanged across the F-38 rebuilds); recorded here by `build-doc-keeper`
- **Kind:** design trade-off (minor) — matching an already-settled build-wide floor rather than a
  skill's older worked examples
- **What was recorded:** the flow carries `<apiVersion>67.0</apiVersion>`, matching
  `package.xml`'s `<version>67.0</version>` and this step's own cited template,
  `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`, which itself carries `67.0`.
  `flow/record-triggered-flow-patterns/references/metadata-examples.md` writes `66.0` in all three
  of its worked flows. The difference is recorded rather than hidden, and it changes nothing here:
  the flow-governance policy floor is `min_api_version: 59`, and every element this flow uses has a
  version floor far below both 66.0 and 67.0 — `RecordBeforeSave` 48.0, `triggerOrder` 54.0,
  `FlowTest` 55.0, `<testType>WithAssertion</testType>` 66.0.
- **Alternative rejected:** matching the cited skill's `66.0` worked examples instead. Rejected
  because the build's API version was already settled at 67.0 at the G3 gate (`decisions.md`
  **O-M3S03-01**, finding **F-31**, gate decision (6)), and the template this step is grounded in
  already carries 67.0 — following the skill's older examples over the template and the build-wide
  floor would have introduced a third `package.xml` version into a build that already carries the
  cost of two (`O-M3S03-01`).
- **Grounded in:** `artefacts/M4-S03/deploy-order.md` § 3; `decisions.md` **O-M3S03-01**;
  `plan.json` `human_gates` `milestone:M3` decision (6);
  `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`.
- **Evidence:** `artefacts/M4-S03/flows/Case_BeforeSave_StampEntitlementAndCalendar.flow-meta.xml`
  (`<apiVersion>67.0</apiVersion>`); `artefacts/M4-S03/package.xml` (`<version>67.0</version>`).

## O-M4S03-01 — Neither cited skill documents a before-save fault-path shape; the flow's four `faultConnector`s route to the next Decision instead, and `check_flow_element_naming_conventions.py` reports it as four advisory `W-FAULT-TARGET` warnings

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `deploy-order.md` § 5 U2 and
  `tests/M4-S03/summary.md`
- **What was recorded:** `flow/flow-element-naming-conventions` Pattern 5 wants every fault routed
  to `LogFault_<Parent>`, and `templates/flow/FaultPath_Template.md` defines that target as one
  that logs *"via an `Application_Log__c` record"* — summarised by
  `flow/record-triggered-flow-patterns/references/metadata-examples.md` as *"capture
  `{!$Flow.FaultMessage}`, write one `Application_Log__c` row."* A `RecordBeforeSave` flow may
  contain **no** `recordCreates` element at all (`check_record_triggered_flow_patterns.py` rule 2),
  so that fault target structurally cannot exist here. The flow's four `faultConnector`s instead
  route to the next `Decision`, so the interview continues on the documented no-match fallback
  rather than stopping silently — which is what rule 4 exists to prevent —
  and `check_flow_element_naming_conventions.py` reports four `W-FAULT-TARGET` warnings for it,
  advisory only, exit 0 with no `--strict` declared.
- **Why this is worth a gate line rather than a defect:** neither cited skill documents what a
  before-save fault path should look like when the standard `LogFault_<Parent>` target is
  structurally unavailable. The flow implements the only fault behaviour a before-save context
  permits; the gap is in the library, not in this artefact.
- **Remedy:** carried to the M4 gate; the durable fix is a documented before-save fault-path
  pattern added to `flow/flow-element-naming-conventions` and/or
  `flow/record-triggered-flow-patterns` — the § 8 deepen-a-skill signal.
- **Grounded in:** `artefacts/M4-S03/deploy-order.md` § 5 U2; `templates/flow/FaultPath_Template.md`;
  `flow/record-triggered-flow-patterns/references/metadata-examples.md` L20–21;
  `check_record_triggered_flow_patterns.py` rule 2 (no `recordCreates` in a `RecordBeforeSave`
  flow); `check_flow_element_naming_conventions.py` rule 4 (`W-FAULT-TARGET`).
- **Evidence:** `tests/M4-S03/summary.md` (`check_flow_element_naming_conventions.py` — "4
  W-FAULT-TARGET warnings"); `tests/M4-S03/check_flow_element_naming_conventions.stdout`.

## O-M4S03-02 — `Settings:Flow`'s `enableFlowDeployAsActiveEnabled true` means a production deploy of this step runs Apex tests, and this build's only Apex (`M4-S05`) landed after this step was first built

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `artefacts/M4-S03/deploy-order.md`
  § 4
- **What was recorded:** `settings/Flow.settings-meta.xml` sets one field,
  `enableFlowDeployAsActiveEnabled`, because it defaults to `false` and an `<status>Active</status>`
  flow would otherwise land `Draft`. `flow/flow-governance/references/metadata-examples.md` § 1
  quotes the guide directly: *"deploying an active process or flow in a production org causes your
  Apex tests to run. If Apex tests don't launch your org's required percentage of active processes
  and autolaunched flows, the deployment is rolled back"* (`api_meta.txt` L116877). This build's
  only Apex is `M4-S05`'s trigger/service/test bundle. A production deploy of this step at
  `<status>Active</status>` can therefore be rolled back for a reason that has nothing to do with
  this flow, if the required launch percentage is not met. The sandbox path is unaffected — the
  same field defaults `true` in non-production orgs. Separately **UNVERIFIED**: whether a
  `FlowSettings` file carrying one element leaves the org's other twelve values untouched or resets
  them is not stated in either cited skill; `api_meta.txt` L116824–116826 says only that there is
  one settings file per settings component.
- **Why this is worth a gate line rather than a defect:** the risk is a sequencing one, not an
  artefact defect — `M4-S05` (the build's only Apex) is now `documented`, but no plan-level
  sequencing states that this step's production-active deploy must be timed against it, and the
  partial-settings-deploy behaviour is unconfirmed either way.
- **Remedy:** confirm the partial-settings-deploy question against a sandbox retrieve before
  deploying to production; sequence this step's production deploy alongside or after `M4-S05`'s so
  the org's required active-automation launch percentage is met.
- **Grounded in:** `artefacts/M4-S03/deploy-order.md` § 4; `flow/flow-governance/references/
  metadata-examples.md` §§ 1, 8 row 2; `api_meta.txt` L116824–116826, L116877.
- **Evidence:** `artefacts/M4-S03/settings/Flow.settings-meta.xml`
  (`enableFlowDeployAsActiveEnabled` `true`).

## D-M5S01-01 — F-49/F-50: the report's `<description>` length cap and the worked example's `reportType`/grouping values, closed in the artefact by two org round-trips; the skill fix stays pending — the fifth flywheel-adjacent record in this build, and the first left open at the skill

- **Date:** 2026-09-12 · **Step:** `M5-S01` (`ui`) · **Agent:** `metadata-builder` (rebuild run
  `2026-09-12T10-08-00Z`, following `build-step-runner`'s F-49/F-50 finding on run
  `2026-09-12T09-46-00Z`); recorded here by `build-doc-keeper`
- **Kind:** skill gap — the gap the owning agent recorded on the rebuild's own envelope, not yet
  acted on at the skill
- **What was recorded:** `reports/MOCK-DEPLOY-M5.md` run 1 rejected the `09-34-00Z` build's report
  file on one field: `Value too long for field: Description maximum length is:255` (**F-49**) — the
  build had put its UNVERIFIED note inside `<description>`, which is capped at 255 characters and
  which `skills/admin/reports-and-dashboards` documents no length rule for (the library's DESC rule
  family covers `PermissionSet` / `Profile` / `CustomPermission` / `CustomObject`; `Report` is
  absent from it). With the description shortened, the operator's scratch-copy probes (never
  applied to the artefact until proven) then rejected the skill's own worked-example values for
  `<reportType>` (`Cases` → `invalid report type`) and the owner grouping column (`USERS.NAME` →
  `Grouping: Invalid value specified`), and surfaced a structural rule neither cited skill states:
  a field cannot be both a `<columns>` entry and a `groupingsDown` field (`PRIORITY`, rejected as
  both) (**F-50**). All three facts trace to one worked example in
  `skills/admin/reports-and-dashboards/references/metadata-examples.md` — one deepening closes all
  three, not three separate ones.
- **Closed in the artefact, not yet at the skill.** The rebuild (`2026-09-12T10-08-00Z`) applied
  the org's own answers — `<description>` cut to 219 characters, `<reportType>CaseList</reportType>`,
  grouping `OWNER`, `PRIORITY` moved out of `<columns>` and kept as the second grouping — and
  `reports/MOCK-DEPLOY-M5.md` run 2 validated the file with only F-28 (the unrelated, already-known
  org prerequisite) remaining. Unlike `D-M4S01-01` and `D-M4S04-01`, the skill itself has **not**
  been patched in this build: `skills/admin/reports-and-dashboards` still carries the wrong
  `reportType`/grouping values in its worked example and still has no `Report` description-length
  rule, so the next build to use this skill hits the same two org round-trips this one did.
- **Alternative rejected:** leaving the file at its rejected values and treating F-49/F-50 as
  pending-only, with no rebuild — rejected because a report the org refuses to deploy is not a
  "built" artefact regardless of what the declared checkers say (see **O-M5S01-01** below).
  Waiting for the skill fix before rebuilding was also rejected: the two facts were already proven
  live by the org's own probes, and holding a known-good file back for a skill edit this agent
  cannot make would cost the milestone for no reason.
- **Grounded in:** `reports/MOCK-DEPLOY-M5.md` runs 1–2; `envelopes/M5-S01/2026-09-12T10-08-00Z.md`
  §§ 1–3; `envelopes/M5-S01/2026-09-12T09-46-00Z.md` § 5 (F-49); `artefacts/M5-S01/deploy-order.md`
  § 0.
- **Evidence:** `artefacts/M5-S01/reports/Support_Operations/Escalated_Open_Cases.report-meta.xml`
  (`<description>` 219 chars, `<reportType>CaseList</reportType>`, `OWNER` grouping);
  `skills/admin/reports-and-dashboards/references/metadata-examples.md` § 2 (unchanged, still
  `Cases`/`USERS.NAME`).

## D-M5S01-02 — F-51: the `Case.IsEscalated` report column code is unresolvable by probing; the Escalated criterion stays out of the file and becomes an M5 gate item and a post-deploy runbook step, not a rebuild

- **Date:** 2026-09-12 · **Step:** `M5-S01` (`ui`) · **Agent:** `metadata-builder` (probed at
  rebuild run `2026-09-12T10-08-00Z`); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — an unresolvable gap recorded rather than guessed, carried to the
  gate as a runbook step
- **What was recorded:** `artefacts/M4-S04/escalation-monitoring-note.md` § 2 specifies the
  report's filter as `Escalated = True` **AND** `Closed = False` **AND**
  `Date/Time Opened = LAST 30 DAYS`. Report column codes are report-type specific and are not
  derivable from field API names (`reports-and-dashboards/SKILL.md` workflow step 3: "Retrieve
  before you write … cannot be derived from field API names"). Five candidate codes were probed
  against the org on the scratch copy — `ESCALATED`, `IS_ESCALATED`, `CASES.ESCALATED`,
  `ISESCALATED`, `CASE_ESCALATED` — and all five were rejected with
  `filters-criteriaItems-column: Invalid value specified`. No file in
  `skills/admin/reports-and-dashboards` carries a code for `Case.IsEscalated`, and inventing a
  sixth is refused under `agents/metadata-builder/AGENT.md` Step 5 rule 1. As shipped, the report
  returns open Cases from the last 30 days, not escalated open Cases — it over-reports, and the gap
  is stated in the file's own 219-character `<description>`, in an XML comment above the filter,
  and in `deploy-order.md` §§ 0 and 2 U1, so a reader in Setup sees it too.
- **Alternative rejected:** substituting `Status = Escalated` for the missing checkbox criterion —
  rejected because the Case status ladder's `Escalated` value and the `IsEscalated` checkbox the
  escalation engine sets are different things, and `M4-S04`'s note is explicit that `IsEscalated`
  is the signal being monitored. Blocking the step until the code is found was also rejected: this
  design-only build has no org to retrieve an existing report from, so no amount of additional
  probing inside this build closes the gap, and holding the milestone for it converts an honestly
  unresolvable item into an artificial delay.
- **Remedy (M5 gate + post-deploy runbook):** deploy the report as written, then either (1) add the
  filter `Escalated equals True` in the report builder and re-export via
  `sf project retrieve start --metadata "Report:Support_Operations/Escalated_Open_Cases"`,
  committing the retrieved file so source and org stop disagreeing and the harvested code enters
  the repo; or (2) retrieve any existing saved Case report from the target org, read the Escalated
  column code off it, add it as a third `<criteriaItems>` block and change
  `<booleanFilter>1 AND 2</booleanFilter>` to `1 AND 2 AND 3`. **Owner:** the role Q91 names — "the
  Tier 2 lead" — not a named person (`workbook/02-page-layouts-and-lightning-pages.md`
  `CWB-LAYOUT-011` records the same gap against the workbook row).
- **Grounded in:** `artefacts/M4-S04/escalation-monitoring-note.md` § 2;
  `artefacts/M5-S01/deploy-order.md` § 2 U1; `reports/MOCK-DEPLOY-M5.md` (probe table);
  `agents/metadata-builder/AGENT.md` Step 5 rule 1; `plan.json` clarification `Q91`.
- **Evidence:** `artefacts/M5-S01/reports/Support_Operations/Escalated_Open_Cases.report-meta.xml`
  (`<description>`, the XML comment above `<filters>`); `envelopes/M5-S01/2026-09-12T10-08-00Z.md`
  §§ 2, 5.

## D-M5S01-03 — A Tier 1 General queue list view is built even though Q31 answers that Tier 1's work is pushed, not pulled — an interim surface under assumption A7 while `M3-S05` stays blocked, not a reversal of D4

- **Date:** 2026-09-12 · **Step:** `M5-S01` (`ui`) · **Agent:** `metadata-builder` (run
  `2026-09-12T09-34-00Z`, unchanged by the F-49/F-50 rebuild); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — an assumption-driven interim surface, recorded against the decision
  it appears to contradict
- **What was recorded:** `Q31`'s answer is explicit — "Tier 1 should get work pushed to them when
  they are available (Omni-Channel push); Billing and Tier 2 pick from a list" — and `D4`
  (`plan.json` `decisions[]`) resolves the mechanism: Tier 1 gets queue-based Omni-Channel push,
  Tier 2 and Billing pull from queue list views. `M3-S05`, the step that would configure that push,
  is blocked on `Q32`–`Q35` (objects pushed and capacity release, capacity model and weight, routing
  model and tie-breaker, push timeout — none defaulted by any cited skill), so no push routing
  ships this phase. `M5-S01` builds `Tier_1_General_Queue.listView-meta.xml` anyway, under
  assumption `A7`, as Tier 1's interim working surface: without it, Tier 1 has no way to see its
  own queue's cases at all until `M3-S05` unblocks.
- **Alternative rejected:** omitting the Tier 1 view and leaving Tier 1 with no working surface
  until `M3-S05` ships — rejected because a support team with no way to see its own queue is a
  worse gap than a pull view that is provisionally the wrong shape. Building the Tier 1 view as the
  intended long-term mechanism, rather than an explicit interim one, was also rejected: it would
  misrepresent `D4`'s own resolution and give a future reader no signal to retire or repurpose the
  view once Omni-Channel ships.
- **Remedy:** carried to the M5 gate. When `Q32`–`Q35` are answered and `M3-S05` ships, a human
  decides deliberately whether this view stays as a supervisor/overflow surface or is retired — it
  is not automatically obsolete, but it is no longer the intended Tier 1 workflow once push routing
  exists.
- **Grounded in:** `plan.json` clarification `Q31` (answered); `plan.json` `decisions[D4]`;
  `artefacts/M5-S01/deploy-order.md` § 5 decision 1; `steps[M5-S01].inputs.assumptions` (`A7`).
- **Evidence:** `artefacts/M5-S01/objects/Case/listViews/Tier_1_General_Queue.listView-meta.xml`;
  `plan.json` `steps[M3-S05].status` = `blocked`.

## O-M5S01-01 — Skill-depth signal: both declared checkers score the org-rejected report and the fixed report identically, so this step's automated gates carried no signal on the fields F-49/F-50 actually changed

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `tests/M5-S01/summary.md` and
  both `metadata-builder` envelopes
- **What was recorded:** `check_list_views_and_compact_layouts.py` (build scope, `No issues
  found.`) and `check_report_inventory.py` (step scope, score 100 / 0 findings) returned the
  identical verdict on the pre-rebuild report that `reports/MOCK-DEPLOY-M5.md` run 1 rejected —
  a `>255`-character `<description>`, an invalid `<reportType>`, an invalid grouping — and on the
  rebuilt report that fixed all three. Neither checker asserts anything about a `Report`'s
  `<description>` length, `<reportType>` value, or the columns/`groupingsDown` exclusivity the org
  enforces; both cover only structural well-formedness, the checkers' own narrower assertions
  (list-view filter/column shape, the compact-layout cross-reference, report-file presence in an
  inventoried folder), and the always-on `xml`/`manifest` checks. The org, not this test harness,
  caught F-49 and F-50 the first time, and would be what catches an equivalent regression the next
  time.
- **Why this is worth a gate line rather than a defect:** this is not a bug in either checker —
  neither one claims to validate report-body semantics the Metadata API itself enforces only at
  deploy time — but it means this step reached `tested` twice (once before the rebuild, once after)
  with identical automated signal both times, and a reviewer reading only the checker output would
  see no difference between the rejected file and the fixed one.
- **Remedy:** carried to the M5 gate, and filed as a skill-depth signal for
  `admin/reports-and-dashboards`: a description-length rule (mirroring the existing DESC rule
  family on `PermissionSet`/`Profile`/`CustomPermission`/`CustomObject`) and a
  `reportType`/grouping-token sanity check would close the gap the org currently closes alone.
  `standards/build-orchestration.md` § 8's deepen-a-skill signal applies here even though the step
  was never `blocked` — the gap surfaced through a mock-deploy rejection, not a checker-policy
  block.
- **Grounded in:** `tests/M5-S01/test2_report_inventory.txt`;
  `envelopes/M5-S01/2026-09-12T10-15-00Z.md` § 4; `envelopes/M5-S01/2026-09-12T10-08-00Z.md` § 4
  (checker results table).
- **Evidence:** identical checker output recorded in both the `09-34-00Z` and `10-08-00Z`
  `metadata-builder` envelopes' § 4 tables (`check_report_inventory.py` — score 100, 0 findings,
  both runs).

## O-M5S01-02 — F-B downgraded: the declared folder filename `Support_Operations-meta.xml` validated against the org at deploy time; what remains is a checker-recognition gap, not a deploy defect

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from
  `artefacts/M5-S01/deploy-order.md` § 3 and `reports/MOCK-DEPLOY-M5.md` run 1
- **What was recorded:** `check_report_inventory.py` recognises a report/dashboard folder only by
  the suffixes `.reportFolder-meta.xml` / `.dashboardFolder-meta.xml` (`FOLDER_SUFFIXES`). The step
  declares the folder at `reports/Support_Operations-meta.xml`, which that check does not scan —
  measured from the build directory, the declared filename scans 1 file with 0 findings while a
  scratchpad copy renamed to the `.reportFolder-meta.xml` form scans 2, both exiting 0 — so
  `acceptance_tests[1]`'s folder-sharing assertion (`accessType`/`folderShares`/not-a-personal-
  folder) never executes at the declared filename, and the W09 empty-directory guard does not catch
  it either, because the report file alone keeps `scanned` above zero. `reports/MOCK-DEPLOY-M5.md`
  run 1 then validated `ReportFolder Support_Operations` against the org at exactly this declared
  filename, alongside all three list views — so the artefact is deployable and correct; only the
  checker's own recognition list is narrower than what the Metadata API accepts.
- **Why this is worth a gate line rather than a defect:** the earlier reading (this step's own
  first envelope, `envelopes/M5-S01/2026-09-12T09-34-00Z.md` § 3) treated the mismatch as a
  possible deploy problem. The org's own validation settles that it is not — this entry corrects
  the record rather than leaving the earlier, more alarming reading standing.
- **Remedy:** two options, neither urgent now that the deploy question is answered. (1) Deepen
  `admin/reports-and-dashboards` so `check_report_inventory.py` recognises the bare
  `<Folder>-meta.xml` form the org accepts, alongside the suffixed forms it already knows — the
  better fix, since it keeps the plan's declared path and closes the gap for every future build.
  (2) Or the M5 gate accepts the folder's `accessType Shared` + one `folderShares` entry on a human
  read of the file rather than on a checker result, and says so in the gate notes, since no
  automated evidence for it exists today.
- **Grounded in:** `artefacts/M5-S01/deploy-order.md` § 3; `reports/MOCK-DEPLOY-M5.md` run 1;
  `envelopes/M5-S01/2026-09-12T10-08-00Z.md` § 1 (run 1 also validated the folder at its declared
  filename).
- **Evidence:** `check_report_inventory.py --manifest-dir artefacts/M5-S01` —
  `Scanned 1 report/dashboard file(s); 0 finding(s)`, exit 0; the same command against a
  `.reportFolder-meta.xml`-renamed scratch copy — `Scanned 2`, exit 0; `reports/MOCK-DEPLOY-M5.md`
  run 1 (folder validated at declared filename).

## O-M5S03-01 — No writer owns the `REQ-` sequence for this build; `story-drafter` minted `REQ-052`-`REQ-058` continuing from `REQ-051`, and `build-doc-keeper` adopts them unchanged rather than re-minting

- **Date:** 2026-09-12 · **Step:** `M5-S03` (`docs`) · **Agent:** `story-drafter` (envelope
  `2026-09-12T10-25-00Z`); recorded here by `build-doc-keeper`
- **Kind:** ambiguity recorded as a contract gap — a requirement-id ownership question with no
  designated owner, carried forward rather than silently resolved either way
- **What was recorded:** `story-backlog.md`'s own internal Requirements Traceability Matrix mints
  seven new ids, `REQ-052`–`REQ-058`, for the testing-and-environment requirements the Q77–Q97
  clarification group contributes, continuing from `REQ-051` — the highest id already in
  `traceability.md` at the time `story-drafter` ran. Nothing in `agents/build-planner/AGENT.md`,
  `agents/story-drafter/AGENT.md` or `agents/build-doc-keeper/AGENT.md` assigns ownership of the
  `REQ-` sequence to one agent; both `story-drafter` (when a step needs a requirement id no earlier
  step minted) and `build-doc-keeper` (at every step's own documentation pass) are capable of
  minting the next id, and neither AGENT.md tells the other it has already done so. `story-drafter`
  flagged the resulting risk itself, as an `ambiguous` process observation
  (`envelopes/M5-S03/2026-09-12T10-25-00Z.json` → `process_observations[9]`): "if
  `build-doc-keeper` mints its own ids at `M5-S04` from the same clarification group the two spaces
  will collide, because no writer owns the `REQ-` sequence for this build." This run confirms the
  fear did not materialize this time — `REQ-051` was and remains the highest id `traceability.md`
  carried before this step, so `REQ-052`–`REQ-058` collide with nothing — but the absence of an
  owner is a standing contract gap, not something this one non-collision closes.
- **Alternative rejected:** re-minting `REQ-052`–`REQ-058` under a fresh `build-doc-keeper`-owned
  sequence (e.g. restarting from `REQ-052` under a different prefix, or renumbering) — rejected
  because the ids do not collide, `story-backlog.md`'s own RTM, its `rtm_req_ids` per story and its
  `dependencies[]` cells all already cite `REQ-052`–`REQ-058` by these exact numbers, and
  renumbering here would make that document disagree with `traceability.md` for no benefit; `REQ-`
  ids are immutable and never reused once minted (`skills/admin/requirements-traceability-matrix`
  § ID Conventions), so a working, non-colliding id space is exactly the case that convention exists
  to protect. Leaving the gap unrecorded and simply adopting the ids silently was also rejected —
  that would make the next collision (should one occur at a future build's `M5-S04`-equivalent step)
  look like a fresh discovery rather than a known, named risk.
- **Remedy:** carried to `planner v6` as a contract item — the planner should either designate one
  agent as the sole minter of `REQ-` ids (most naturally `build-doc-keeper`, since it is the agent
  that already owns `traceability.md`) or add an explicit handoff field a borrowed roster agent like
  `story-drafter` checks before minting, the same shape `plan.json`'s per-milestone gate notes
  already use for other cross-step contract gaps (e.g. `enableEntitlements` owned by no step,
  `O-M4S02-01`). Until then, any step that mints a `REQ-` id must read `traceability.md`'s current
  highest id first, exactly as `story-drafter` did here, and this file is where the resulting
  non-collision (or a future collision) gets recorded.
- **Grounded in:** `agents/story-drafter/AGENT.md` (no `REQ-`-sequence ownership clause);
  `agents/build-doc-keeper/AGENT.md` Step 7 (this agent's own minting authority is likewise
  undocumented as exclusive); `skills/admin/requirements-traceability-matrix` § ID Conventions
  (immutability, never reused).
- **Evidence:** `envelopes/M5-S03/2026-09-12T10-25-00Z.json` → `process_observations[9]`,
  `extensions.req_ids_minted`; `traceability.md` `REQ-052`–`REQ-058` (adopted unchanged, no
  collision with `REQ-051` or earlier); `artefacts/M5-S03/story-backlog.md` § Requirements
  Traceability Matrix.

## O-M5S03-02 — `M5-S03` declares no `deploy-order.md`: `story-drafter`'s Output Contract names no such file, and § 4 condition 2 forbids declaring an output the owning agent does not produce

- **Date:** 2026-09-12 · **Step:** `M5-S03` (`docs`) · **Agent:** `build-step-runner` (envelope
  `2026-09-12T10-32-00Z`, `dimensions_skipped[1]`); recorded here by `build-doc-keeper`
- **Kind:** design trade-off — a contract rule applied correctly, recorded so the resulting
  asymmetry with every other `metadata-builder` step in this build reads as a rule followed, not a
  gap missed
- **What was recorded:** every `metadata-builder` step in this build writes an
  `artefacts/<step>/deploy-order.md`, whether or not that file is declared in the step's
  `outputs[]` (the undeclared-artefact pattern `decisions.md` **O-M3S02-03** tracks separately).
  `M5-S03` writes none, and this is not an instance of that same pattern: `story-drafter` is a
  Tier-2 roster agent borrowed for this step, and `standards/build-orchestration.md` § 4
  "Borrowing a roster agent from outside Tier 4" condition 2 is explicit — "declare only outputs the
  agent's Output Contract names… a path in `outputs[]` with no counterpart there is an artefact
  nobody writes." `agents/story-drafter/AGENT.md`'s Output Contract names one markdown document
  (the story backlog itself) and nothing else; it has no notion of a per-step deploy order, because
  a story backlog is not deployable metadata with an internal deploy sequence. `M5-S03`'s
  `outputs[]` therefore names exactly one path, and `check-outputs` confirms exactly that one path,
  with nothing missing.
- **Alternative rejected:** declaring `artefacts/M5-S03/deploy-order.md` in `outputs[]` anyway, for
  consistency with every metadata-producing step — rejected because `story-drafter` would then never
  write it (its contract has no step for a deploy-order file), `check-outputs` would report it
  `missing` on every run, and the step could never reach `built`. Asking `story-drafter` to invent a
  deploy-order note outside its Output Contract was also rejected, per § 4 condition 2's own
  wording and per `agents/_shared/AGENT_CONTRACT.md` rule 1 (skill-first, never freestyle a format a
  cited skill does not define).
- **Remedy:** none needed — this is the contract working as specified, not a gap to close. If a
  future build wants a deploy-order-equivalent note for a story backlog (e.g. "which milestone's
  UAT session should run these stories first"), that belongs in `story-backlog.md`'s own body or in
  a new field on `story-drafter`'s Output Contract, decided by a human, not manufactured here to
  match an unrelated step type's shape.
- **Grounded in:** `standards/build-orchestration.md` § 4 "Borrowing a roster agent from outside
  Tier 4," condition 2; `agents/story-drafter/AGENT.md` Output Contract (one markdown document,
  no deploy-order file).
- **Evidence:** `plan.json` `steps[M5-S03].outputs` = `["artefacts/M5-S03/story-backlog.md"]`;
  `envelopes/M5-S03/2026-09-12T10-32-00Z.json` → `dimensions_skipped[1]`
  (`dimension: "deploy-order-note"`, `state: "not-run"`).

## O-M5S03-03 — Skill-depth signal: `check_invest.py`'s 250-word body heuristic cannot distinguish an oversized story from a story correctly carrying a G4-mandated handoff note, so all 10 WARNs on this backlog are the same false signal

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `tests/M5-S03/summary.md` and
  `step-tester`'s envelope
- **Kind:** skill gap — a checker limitation surfaced by real output, not a step ever marked
  `blocked`; recorded under the same `standards/build-orchestration.md` § 8 deepen-a-skill signal
  `decisions.md` **O-M5S01-01** already establishes for a checker that scores two materially
  different artefacts identically
- **What was recorded:** `check_invest.py --manifest-dir artefacts/M5-S03` exits 0 with
  `11/11 stories passed (0 ERROR, 10 WARN)`. All 10 WARNs are the same 250-word story-body rule, and
  the three heaviest overflows (`US-CASE-007` at 193 handoff words, `US-CASE-009` at 169,
  `US-CASE-004` at 155) are exactly the three stories carrying the F-40 regional-calendar note, the
  completion-proxy note and the Q24 training note the M4 gate required be written down
  (`story-backlog.md` § Process Observations, "What was concerning"). Measured per story, the
  As-a/I-want/So-that stem plus every acceptance criterion alone runs 143–235 words on all eleven
  stories — under the 250 threshold in every case. The checker counts everything between one story
  heading and the next as body, so `Complexity` / `Fit tier` / `Recommended agents` /
  `Recommended skills` / `Dependencies` / `Notes` are all counted alongside the stem and criteria,
  with no way to separate "this story is too long" from "this story correctly carries a required
  handoff note." Trimming the notes to clear the heuristic would delete the content the M4 gate
  asked for; the notes stand, and the checker's own WARN passes at exit 0 because it does not run
  under `--strict`.
- **Why this is worth a gate line rather than a defect:** identical to `O-M5S01-01`'s framing — this
  is not a bug in the checker (it does not claim to distinguish stem-length from handoff-note
  length), but a reviewer reading only `check_invest.py`'s WARN count would see "10 warnings" and
  not know that every one of them is the same false signal repeating, nor that three specific WARNs
  are the price of carrying forward exactly the notes the M4 gate mandated.
- **Remedy:** carried to the M5 gate, and filed as a skill-depth signal for
  `admin/user-story-writing-for-salesforce`: either a `--max-words` flag scoped to the stem plus
  acceptance criteria only (excluding the handoff fields), or a documented convention that
  gate-mandated notes live in a separate "Handoff" block the word count does not scan. Either fix
  is a future skill-fix session's job, not this run's — this run records the gap where the checker
  output actually surfaced it, per `standards/build-orchestration.md` § 8.
- **Grounded in:** `tests/M5-S03/check_invest.stdout.txt`; `story-backlog.md` § Process
  Observations, "What was concerning," bullet 4; `standards/build-orchestration.md` § 8
  (deepen-a-skill signal).
- **Evidence:** `tests/M5-S03/results.json` → `detail.checker.stdout_summary`
  ("11/11 stories passed (0 ERROR, 10 WARN)"); `envelopes/M5-S03/2026-09-12T10-39-56Z.json` →
  `process_observations[2]` (category `concerning`, domain `checker-signal-quality`).

## D-M5S03-04 — Three skill-path citations in the drafted backlog did not resolve on disk; `story-drafter` corrected all three before finalising the document rather than shipping a dangling citation

- **Date:** 2026-09-12 · **Step:** `M5-S03` (`docs`) · **Agent:** `story-drafter` (envelope
  `2026-09-12T10-25-00Z.md` § 10 Citations)
- **Kind:** deviation — a self-caught correction to the document's own content before handoff, not
  a change to what the step's `inputs{}` asked for
- **What was recorded:** while compiling the Citations section, `story-drafter` checked every
  `skills/…` path named anywhere in the drafted backlog against the skill registry on disk. Three
  did not resolve: `admin/web-to-case-and-email-to-case`, `admin/queue-design` and
  `apex/trigger-handler-pattern` — plausible-sounding names that do not exist as skill packages in
  this repo. Before the document was finalised, all three were corrected to the skills that do
  exist and cover the same ground: `admin/case-management-setup`, `admin/queues-and-public-groups`
  and `apex/case-trigger-patterns` respectively. The corrected names are what appear in the
  finished `story-backlog.md`'s `Recommended skills` cells (`US-CASE-003`'s
  `admin/case-management-setup`; `US-CASE-006`/`US-CASE-010`'s `admin/queues-and-public-groups`;
  `US-CASE-009`'s `apex/case-trigger-patterns`) and in its Citations table.
- **Alternative rejected:** shipping the three uncorrected names and flagging them as a gap for a
  human to fix later — rejected because the correct skills were identifiable by name-similarity
  search against the registry in the same pass, so leaving a known-wrong citation in a document a
  human or another agent will read as ground truth would have been worse than the ten extra seconds
  the correction cost. Silently correcting them with no record at all was also rejected: a citation
  correction is exactly the kind of self-check `agents/_shared/AGENT_CONTRACT.md` rule 1
  ("skill-first, never freestyle") and the anti-pattern list ("citing skills to clear the orphan
  gate") exist to make visible, not to hide once it has already happened correctly.
- **Remedy:** none needed on this document — the correction already landed before this step
  reached `tested`. Filed here as a process note: an agent drafting from clarification text alone
  (no org, no prior skill-search step in its own Plan) is exactly the condition under which a
  plausible-but-nonexistent skill path is most likely to be typed from memory, and this is evidence
  the self-check step in `story-drafter`'s own Plan catches it before it reaches a document another
  agent will cite as fact.
- **Grounded in:** `agents/_shared/AGENT_CONTRACT.md` rule 1 (skill-first, never freestyle) and
  the Anti-patterns list ("citing skills to clear the orphan gate" — the adjacent failure mode this
  correction avoided by fixing rather than padding).
- **Evidence:** `envelopes/M5-S03/2026-09-12T10-25-00Z.md` § 10 ("Every `skills/…` path named
  anywhere in the backlog was checked to resolve on disk; three that did not… were corrected…
  before the document was finalised."); `artefacts/M5-S03/story-backlog.md` `Recommended skills`
  cells on `US-CASE-003`, `US-CASE-006`, `US-CASE-009`, `US-CASE-010`, and § Citations.

## O-M5S03-05 — The email intake channel is split into two stories, not one, because Billing gets its own named tester (Q77) and a story cannot carry two `As a` clauses

- **Date:** 2026-09-12 · **Step:** `M5-S03` (`docs`) · **Agent:** `story-drafter` (envelope
  `2026-09-12T10-25-00Z.json` → `process_observations[11]`); recorded here by `build-doc-keeper`
- **Kind:** design trade-off (backlog-shape) — an INVEST split decision that appears to read
  against a literal count in the step's own manual acceptance test, recorded so a reviewer checks
  the split deliberately rather than assuming it is a miscount
- **What was recorded:** the M5 milestone's manual acceptance test
  (`plan.json` `steps[M5-S03].acceptance_tests[1]`) reads "each of the three intake channels — email,
  web and manual UI — has its own story." `story-backlog.md` ships four stories across those three
  channels: `US-CASE-001` (email, support@, Tier 1 tester), `US-CASE-002` (email, billing@, Billing
  tester), `US-CASE-003` (web) and `US-CASE-004` (manual UI). The email channel is split by data
  variation rather than given one story, because Q77's answer gives Billing its own named tester
  (distinct from Tier 1's), and `admin/user-story-writing-for-salesforce` gotcha 3 (persona drift)
  is explicit that a single story cannot carry two `As a` clauses without losing INVEST's
  Independent and Testable properties — a story written "as a Tier 1 agent or a Billing specialist"
  is two stories wearing one story_id. `check_invest.py` does not check channel count at all, so
  this split was never at risk of failing the checker; it is a reading of the manual test's intent,
  not its literal wording, and `story-drafter` flagged the reading as `ambiguous` rather than
  asserting it as obviously correct (`story-backlog.md` § Process Observations, "What was
  ambiguous," bullet 3).
- **Alternative rejected:** forcing one story for the whole email channel with two persona
  bullets or a parametrised "As a Tier 1 agent or Billing specialist" stem — rejected as the exact
  persona-drift shape gotcha 3 warns against, and as something that would have made the acceptance
  criteria unreadable (which queue, which tester, for which of the two `As a` halves does each
  criterion apply). Renaming `US-CASE-002` as a sub-bullet of `US-CASE-001` rather than a full
  story was also rejected: it carries its own MoSCoW priority, its own dependencies (`REQ-024`, the
  Billing queue mailbox prerequisite P2) and its own tester, all of which a sub-bullet cannot hold
  without duplicating the parent story's structure anyway.
- **Remedy:** carried to the M5 gate as a named reading to confirm, not a defect to fix. If the
  gate reads "three channels, three stories" literally and rejects the four-story shape, the fix is
  to merge `US-CASE-001`/`US-CASE-002` back into one story and accept the persona-drift cost the
  gotcha warns against, which this decision recommends against unless the gate says otherwise.
- **Grounded in:** `plan.json` `steps[M5-S03].acceptance_tests[1].description`; `plan.json`
  clarification `Q77` (Billing's own named tester); `skills/admin/user-story-writing-for-salesforce`
  `references/gotchas.md` gotcha 3 (persona drift).
- **Evidence:** `artefacts/M5-S03/story-backlog.md` `US-CASE-001`, `US-CASE-002` (notes: "split from
  `US-CASE-001` by data variation because the persona differs"); `envelopes/M5-S03/2026-09-12T10-25-00Z.json`
  → `process_observations[11]` (category `ambiguous`, domain `backlog-shape`).

## D-M5S04-01 — The compile's own diligence run surfaced 30 uncited Section 6 rows, one parser-breaking regex cell and 18 UAT/AC negative-coverage gaps; a repair pass closed all but 8 citations, the 8 closed separately at the skill

- **Date:** 2026-09-12 · **Step:** `M5-S04` (`docs`, compile run) · **Agent:** `build-doc-keeper`
  (compile envelope `2026-09-12T11-15-00Z.json`; repair-pass envelope `2026-09-12T11-40-00Z.json`),
  invoked inline both times by `build-step-runner` (envelopes `2026-09-12T11-25-00Z.json` and
  `2026-09-12T11-45-00Z.json`)
- **Kind:** deviation — the coordinator's explicit instruction to run all four declared
  acceptance-test checkers as diligence at compile time (beyond this agent's own Step 10 job, which
  is collation only) surfaced genuine, pre-existing gaps spanning four earlier milestones' own
  documentation runs, which were then repaired at the source rather than left standing or papered
  over in the compiled document alone
- **What was recorded:** the first compile run (`2026-09-12T11-15-00Z`) ran `check_workbook.py`,
  `check_rtm.py`, `check_uat_case.py` and `check_ac_format.py` verbatim against the freshly
  compiled documents. `check_rtm.py` exited 0. The other three did not: `check_workbook.py` found
  30 of 30 Section 6 rows missing a `standards/decision-trees/automation-selection.md` citation — a
  gap in four earlier steps' own documentation runs (`M2-S04`/`M3-S03`/`M3-S04`/`M4-S01`/`M4-S02`/
  `M4-S04`/`M4-S03`), never introduced by this compile run's own writing — plus a fourth,
  previously-unnamed instance of the un-escaped-pipe parser collision on `CWB-AUT-029`'s
  naming-pattern regex (the same defect `workbook/99-other-configuration.md` already documents for
  `CWB-OTHER-001`–`003`); `check_uat_case.py` found 6 `req_id` groups (`REQ-013`, `REQ-025`,
  `REQ-038`, `REQ-040`, `REQ-043`, `REQ-053`) with exactly one manual test and no negative case;
  `check_ac_format.py` found 12 rule-type-requirement negative-coverage gaps and 2 `then` clauses
  naming an implementation mechanism instead of an observable outcome. The repair pass
  (`2026-09-12T11-40-00Z`, after the operator reset the step `built → failed → pending → running`
  naming these three checkers explicitly) fixed at the source rather than the compiled artefact:
  appended a decision-tree citation — quoting the tree's actual branch text — to 22 of the 30
  Section 6 rows in `workbook/06-automation.md`, each traced to a real, already-recorded
  `plan.json` `decisions[]` entry (D1, D3, D6, D7, D10); rewrote `CWB-AUT-029`'s `target_value` to
  describe its regex in prose rather than embed a literal pipe (the real regex is untouched in its
  actual home, `artefacts/M4-S03/flow-governance-policy.yaml`); added 6 derived negative UAT cases
  and 12 derived negative AC records, each carrying a `derived_from` citation to a real
  story-backlog criterion or workbook row; and rephrased the 2 mechanism-naming `then` clauses to
  name the observable outcome. `check_uat_case.py` and `check_ac_format.py` exited 0 after the
  repair; `check_workbook.py` still exited 1 on the remaining 8 rows (`M2-S04`'s three Queue and
  three Group rows; `M4-S01`'s `BusinessHours` settings row and holiday-maintenance-runbook row)
  because no `automation-selection.md` decision exists anywhere in the plan for either step, and
  Queue/Group/BusinessHours creation is not itself a leaf of that tree — closed instead at the
  skill, not the artefact (see **D-M5S04-02**).
- **Alternative rejected:** leaving the 30 missing citations and the regex-parser collision
  unrepaired and reporting them only in Process Observations — rejected by the coordinator's
  explicit direction to fix at the source; inventing a decision-tree citation for the 8 remaining
  Queue/Group/BusinessHours rows to force `check_workbook.py` to exit 0 at the compile — rejected
  because `standards/build-orchestration.md` Step 10's "nothing new is decided here" boundary
  forbids a compile run from resolving a routed choice it has no source for, the same reasoning
  `agents/build-doc-keeper/AGENT.md` gives for not compiling from the metadata artefacts directly.
- **Remedy:** the 8 remaining `check_workbook.py` findings were closed by amending the checker
  itself — see **D-M5S04-02**. `step-tester`'s formal run (`envelopes/M5-S04/2026-09-12T11-52-23Z.json`)
  confirms all four declared checkers exit 0 after that fix, with no further artefact change.
- **Grounded in:** `standards/build-orchestration.md` § 10 "nothing new is decided here"; `plan.json`
  `decisions[]` D1/D3/D6/D7/D10.
- **Evidence:** `envelopes/M5-S04/2026-09-12T11-15-00Z.json` → `process_observations[1..3]`;
  `envelopes/M5-S04/2026-09-12T11-25-00Z.json` → `extensions.declared_acceptance_checks`;
  `envelopes/M5-S04/2026-09-12T11-40-00Z.json` → `summary`, `process_observations`;
  `envelopes/M5-S04/2026-09-12T11-45-00Z.json` → `extensions.declared_acceptance_checks`,
  `extensions.unresolved_findings`; `workbook/06-automation.md` rows `CWB-AUT-001`–`006`,
  `CWB-AUT-013`/`014`, `CWB-AUT-029`.

## D-M5S04-02 — `check_workbook.py`'s blanket Section 6 decision-tree-citation rule closed at the skill, not the artefact, once the residual 8-row gap showed the rule was over-broad — the flywheel record

- **Date:** 2026-09-12 · **Step:** `M5-S04` · **Checker:**
  `skills/admin/configuration-workbook-authoring/scripts/check_workbook.py`, commit `65ec5b82f` ·
  **Recorded by:** `build-doc-keeper`, from `step-tester`'s envelope
- **Kind:** skill gap — the same flywheel shape **D-M4S01-01** names as the first instance in this
  build: an over-broad checker rule closed by amending the skill, not by inventing an
  artefact-level fix
- **What was recorded:** after the repair pass in **D-M5S04-01**, `check_workbook.py` still exited
  1 on 8 Section 6 rows (`M2-S04`'s three Queue and three Group rows; `M4-S01`'s `BusinessHours`
  settings row and holiday-maintenance-runbook row) for lacking an `automation-selection.md`
  citation. Both `build-doc-keeper` (`envelopes/M5-S04/2026-09-12T11-40-00Z.json`) and
  `build-step-runner` (`envelopes/M5-S04/2026-09-12T11-45-00Z.json`) independently confirmed no
  decision anywhere in `plan.json`'s `decisions[]`, `PLAN.md`'s rendered decision table, or
  `decisions.md` names an automation-engine branch for either step, and that Queue/Group/
  BusinessHours creation is not itself a leaf of that tree — the checker's rule assumed every
  Section 6 row represents a routed automation-engine choice, which is false for configuration
  artefacts filed there only because `agents/build-doc-keeper/AGENT.md` Step 4 routes
  `routing`/`sla`-type steps' non-choice artefacts to that section too. `step-tester`'s formal run
  (`envelopes/M5-S04/2026-09-12T11-52-23Z.json` → `process_observations[0]`) confirms the checker
  itself was fixed at commit `65ec5b82f`: the 8 rows now read as INFO ("no automation choice to
  cite — artefact is configuration, not an automation-engine pick",
  `references/gotchas.md` Gotcha 12) rather than ERROR, and `check_workbook.py` exits 0 on the
  byte-identical rows with no artefact edit between the two runs.
- **Alternative rejected:** inventing a decision-tree citation for the 8 rows to force the pre-fix
  checker to exit 0 — rejected in **D-M5S04-01** on the same "nothing new is decided here" grounds;
  backfilling an `automation-selection.md`-shaped decision retroactively into `plan.json` for
  `M2-S04`/`M4-S01` — rejected because neither step's own build run made an automation-engine
  choice, so inventing one would misrepresent the build's own history to satisfy a linter.
- **Remedy:** none needed on the artefact — the gap closed at the skill. A future Section 6 row
  that genuinely is a routed automation-engine choice still must carry the citation; Gotcha 12 in
  the skill's `references/gotchas.md` now names the Queue/Group/BusinessHours exception explicitly
  so the distinction is documented rather than re-discovered on the next build.
- **Grounded in:** the flywheel pattern **D-M4S01-01** establishes (skill gap closed at the skill,
  not the artefact); `skills/admin/configuration-workbook-authoring/references/gotchas.md`
  Gotcha 12.
- **Evidence:** `envelopes/M5-S04/2026-09-12T11-45-00Z.json` → `extensions.unresolved_findings`;
  `envelopes/M5-S04/2026-09-12T11-52-23Z.json` → `process_observations[0]` (category `healthy`,
  domain `checker-quality`); `tests/M5-S04/check_workbook.out`.

## O-M5S04-03 — REQ-055–REQ-058's `Draft`-row coverage-gap WARNs read "waived by decision NONE": no `D<n>` names the waiver because `Draft` status is itself `check_rtm.py`'s waiver condition, not a citation — carried to the M5 gate, not fabricated

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `step-tester`'s envelope and
  `check_rtm.py`'s own output
- **Kind:** observation — a checker message read literally could look like an unfinished waiver;
  the build's own `traceability.md` already explains the mechanism, so this entry names it in
  `decisions.md` rather than leaving it to be rediscovered at the gate
- **What was recorded:** `step-tester`'s formal run (`envelopes/M5-S04/2026-09-12T11-52-23Z.json`
  → `process_observations[2]`) flags that `check_rtm.py` prints 4 coverage-gap WARNs — `REQ-055`,
  `REQ-056`, `REQ-057`, `REQ-058`, each "waived by decision NONE" — and that "a human should
  confirm ... is the intended state before the milestone gate rather than an unfinished waiver."
  Re-running the same command from the build root
  (`python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file
  traceability.md --manifest-dir artefacts --repo-root <repo root>`) reproduces the identical 4
  WARNs and `0 orphan(s), 0 error(s)`. No `D<n>` decision anywhere in `decisions.md` or `plan.json`'s
  `decisions[]` waives these four rows by id — but `traceability.md`'s own coverage narrative (§
  "Coverage gaps (new at this step)", written by `M5-S03`'s own documentation run) already states
  the mechanism: `check_rtm.py`'s waiver rule reads a row's `Draft` **status** as the waiver
  condition for missing test coverage, not a cited decision id, and all four rows are `Draft`
  because `REQ-055` is an environment precondition raised outside any plan step, `REQ-056`/
  `REQ-057` are UAT-programme controls carried in the story backlog's shared Background rather than
  as their own story (`decisions.md` **O-M5S03-01**), and `REQ-058` names a sandbox owner/approver
  that cannot exist while `M5-S02` stays `blocked`. "Decision NONE" is the checker naming the true
  state accurately, not a gap in citation.
- **Remedy:** none needed in the artefacts — the four rows are correctly `Draft` and correctly
  uncited. Carried to the M5 gate as an explicit item, not silently accepted: a human should
  confirm before sign-off that (a) `REQ-055` is raised as a deploy prerequisite (P6) rather than
  lost, (b) `REQ-056`/`REQ-057` are read at each UAT session from the shared Background rather than
  forgotten for having no story, and (c) `REQ-058` remains blocked on `M5-S02`, not silently
  dropped — the same three items `story-backlog.md`'s own Process Observations already name,
  restated here because a gate reviewer reads `decisions.md` and `traceability.md`, not necessarily
  the backlog.
- **Grounded in:** `skills/admin/requirements-traceability-matrix` — the `Draft`-status waiver rule
  `check_rtm.py` implements; `decisions.md` **O-M5S03-01**.
- **Evidence:** `envelopes/M5-S04/2026-09-12T11-52-23Z.json` → `process_observations[2]`;
  `tests/M5-S04/check_rtm.out` (4 WARN lines, "waived by decision NONE"); `traceability.md` §
  "Coverage gaps (new at this step)" and the `REQ-055`–`REQ-058` rows.

## O-M5S04-04 — 111 `check_ac_format.py` WARNs on the compiled acceptance-criteria document, almost all naming a "Build/milestone-gate reviewer" persona with no permission construct, are accepted as expected for build-process meta-criteria rather than a genuine gap

- **Date:** 2026-09-12 · **Recorded by:** `build-doc-keeper`, from `step-tester`'s envelope
- **Kind:** observation — a checker-signal-quality note, the same shape **O-M5S03-03** already
  records for `check_invest.py`'s body-length heuristic: a WARN that fires correctly on the letter
  of the rule while missing that the criterion it is checking was never meant to satisfy that
  rule's premise
- **What was recorded:** `step-tester`'s formal run (`envelopes/M5-S04/2026-09-12T11-52-23Z.json`
  → `process_observations[3]`; `tests/M5-S04/check_ac_format.out`) reports
  `check_ac_format.py --file artefacts/M5-S04/acceptance-criteria.md` exits 0 with 111 WARNs, 0
  errors. Gotcha 5's rule fires whenever a criterion's `persona` field "names a job title but no
  permission construct" — a Profile, Permission Set or PSG — because an end-user acceptance
  criterion whose persona has no named access grant is usually unverifiable. The large majority of
  the 111 name a `Build/milestone-gate reviewer (M#-S##)` persona: these are the 39 build-wide
  manual-test records `acceptance-criteria.md`'s own preamble names as compiled "so `ac_id`
  references have something to resolve against" (Step 10's cross-check requirement) — criteria that
  audit the build's own artefacts (a file exists, a checker exits 0, a decision was recorded)
  rather than what a Salesforce end user can do in the org. A reviewer persona correctly has no
  Profile or PSG, because the criterion is not about Salesforce access at all.
- **Alternative rejected:** inventing a Profile/PSG for the "Build/milestone-gate reviewer" persona
  to clear the WARN — rejected as fabrication with no source, the same reasoning
  **D-M5S04-01**/**D-M5S04-02** give for not inventing a decision-tree citation; suppressing or
  filtering the 111 WARNs before returning the checker's own output — rejected because
  `agents/build-doc-keeper/AGENT.md` names verbatim checker output as the record, and a filtered
  result would hide the one-in-111 case that might genuinely be a missed end-user criterion.
- **Remedy:** none needed on the 39 build-process records — accepted as correctly WARN-level, not
  ERROR-level, exactly as the checker classifies them. Carried to the M5 gate as `step-tester`
  itself frames it: "worth a human's confirmation that none of the 111 hide a genuine end-user
  criterion that still needs a named profile or PSG" — a spot-check item, not a blocking gap,
  because `check_ac_format.py` exits 0 and no ERROR-level finding stands against this document.
- **Grounded in:** `skills/admin/acceptance-criteria-given-when-then/references/gotchas.md`
  gotcha 5 (persona-without-permission-construct); `decisions.md` **O-M5S03-03** (the adjacent
  checker-signal-quality shape).
- **Evidence:** `envelopes/M5-S04/2026-09-12T11-52-23Z.json` → `process_observations[3]`;
  `tests/M5-S04/check_ac_format.out` ("111 warning(s)"; sample lines `AC-040.90`, `AC-043.90`
  naming the reviewer persona).

## D-M5S04-05 — The Assumptions Register renders all 28 `plan.json` assumptions, not only the 25 deferred at G1, with `owner` disclosed as a compile-time join rather than a native field — closes F-54

- **Date:** 2026-09-12 · **Step:** `M5-S04` (`docs`, compile run) · **Agent:** `build-doc-keeper`
  (re-compile envelope `2026-09-12T13-15-00Z.json`), invoked by `build-step-runner` after the
  operator moved the step `documented → running` for this re-run (`re_run_of`: `reports/
  MILESTONE-M5-REPORT.md` § 8, findings F-52/53/54/56/57)
- **Kind:** design trade-off
- **What was recorded:** `reports/MILESTONE-M5-REPORT.md` § 8 F-54 (HIGH) found the compiled
  `configuration-workbook.md` carried no assumptions section at all, so `M5-S04`'s own manual test
  [4] ("all 25 [deferred clarifications] appear as named rows with an owner ... compiled from
  `assumptions[].steps[]`") was not tickable — 16 of 28 assumptions appeared in none of the five
  compiled documents, and 0 of 28 carried an `owner` field natively in `plan.json`. This re-compile
  adds a new **Assumptions Register** section rendering all 28 rows of `plan.json`'s
  `assumptions[]` (not filtered to the 25 deferred at G1 — F-54 names the missing 16 as
  disproportionately `M5-S02`'s/`M5-S03`'s/`M5-S04`'s own still-open assumptions, A15–A23 among
  them, exactly the set a phase-2 owner most needs handed to them), each naming the steps it
  constrains (`assumptions[].steps[]`) verbatim, and an owner column populated by a compile-time
  join: `assumptions[].because` points at a clarification id, and that clarification's own
  `owner_role`/`owner_hint` field supplies the value shown. The join is disclosed in the register's
  own preamble as a compile-time convenience, not a `plan.json`-native `owner` field — the
  finding's root cause (0 of 28 assumptions carry one) is unchanged by this row; only how it
  surfaces changes.
- **Alternative rejected:** rendering only the 25 deferred-at-G1 assumptions, matching the manual
  test's literal count — rejected because narrowing to 25 would repeat exactly the omission F-54
  names; inventing a native `owner` field on `plan.json`'s `assumptions[]` to answer the test's
  "with an owner" clause literally — rejected because `agents/build-doc-keeper/AGENT.md`'s compile
  run invents no row that is not already in a source file, and `plan.json` is the source of record
  for this build, not this agent's to amend.
- **Remedy:** none needed on the artefact beyond the new section. Carried to the M5 gate as a named
  reading, not a settled tick: `step-tester`'s manual-test note (`tests/M5-S04/summary.md`) already
  flags that a human must confirm 28-not-25 and a joined-not-native owner still satisfy the test's
  literal wording. A planner v6 item stands — `assumptions[]` needs a native `owner` field, per
  F-54's own recommendation.
- **Grounded in:** `reports/MILESTONE-M5-REPORT.md` § 8 F-54; `skills/admin/
  configuration-workbook-authoring` (row/section schema the register follows); `plan.json`
  `assumptions[]`/`clarifications[]`.
- **Evidence:** `envelopes/M5-S04/2026-09-12T13-15-00Z.json` → `summary`,
  `compiled_documents[0]`, `process_observations[0]`; `artefacts/M5-S04/configuration-workbook.md`
  § Assumptions Register; `tests/M5-S04/summary.md` (manual test 1 note).

## D-M5S04-06 — Two blocked-step UAT cases kept, not deleted, and marked `phase: 2` / `blocked_on: <step>` instead — structurally closes F-53

- **Date:** 2026-09-12 · **Step:** `M5-S04` · **Agent:** `build-doc-keeper`
  (`envelopes/M5-S04/2026-09-12T13-15-00Z.json`)
- **Kind:** deviation — `M5-S04`'s manual test [5] literally asserts the UAT pack "carries no case
  that depends on" `M3-S05` or `M5-S02`, and the pack in fact carries two cases (`TC-M3-S05-2`,
  `TC-M5-S02-2`) whose `evidence.of` paths (`artefacts/M3-S05/`, `artefacts/M5-S02/`) do not exist
  because both steps are `blocked`
- **What was recorded:** `reports/MILESTONE-M5-REPORT.md` § 8 F-53 (MEDIUM) recommends reading the
  test as "carries no case that can be mistaken for runnable" rather than literally, and names the
  fix as a structural marker rather than deletion, because both cases are exactly what should run
  once their steps unblock. This re-compile adds `phase: 2` and `blocked_on: <step>` keys to both
  cases in `uat-test-cases.yaml`, distinguishing them from the 43 runnable cases without removing
  them or their `pass_fail: "Not Run"` state. `check_uat_case.py`'s record shape
  (`skills/admin/uat-test-case-design`) tolerates the added keys without a schema change; the case
  count (45) is unchanged.
- **Alternative rejected:** deleting the two cases to satisfy the test's literal wording —
  rejected per the finding's own recommendation ("Do not delete the two cases: when the steps
  unblock, these are exactly the cases that should run"); leaving the cases unmarked and relying on
  prose alone (each already carries "Given this step is unblocked in a later phase" as its first
  step) — rejected because F-53 itself names the gap as the absence of a structural marker, not the
  absence of prose.
- **Remedy:** none needed beyond the two added keys. Carried to the M5 gate as a human judgment
  call, not decided here: `step-tester`'s own ambiguous observation
  (`envelopes/M5-S04/2026-09-12T16-06-03Z.json`) flags that whether a `phase`/`blocked_on` marker
  satisfies the test's literal "carries no case that depends on" wording is for a human to tick,
  not this agent to assert.
- **Grounded in:** `reports/MILESTONE-M5-REPORT.md` § 8 F-53; `skills/admin/uat-test-case-design`
  (case record shape); `skills/admin/uat-and-acceptance-criteria` (recording a blocked-step manual
  test as evidence rather than deleting it).
- **Evidence:** `envelopes/M5-S04/2026-09-12T13-15-00Z.json` → `summary` point (3),
  `compiled_documents[3]`; `artefacts/M5-S04/uat-test-cases.yaml` `TC-M3-S05-2`, `TC-M5-S02-2`;
  `tests/M5-S04/summary.md` (manual test 2 note).

## D-M5S04-07 — A ten-member traceability addendum added inside the compiled copy only; the canonical fix (real rows in the build's own `traceability.md`) is named and deferred, not made here — partially closes F-52

- **Date:** 2026-09-12 · **Step:** `M5-S04` · **Agent:** `build-doc-keeper`
  (`envelopes/M5-S04/2026-09-12T13-15-00Z.json`)
- **Kind:** design trade-off
- **What was recorded:** `reports/MILESTONE-M5-REPORT.md` § 8 F-52 (MEDIUM) found 10 of 56
  `M5-S05` manifest members reach no row in `traceability.md` — not even inside an
  `artefact_paths` cell — because `check_rtm.py`'s orphan rule runs step → row only, never
  member → row. This re-compile adds a new addendum section to the compiled
  `artefacts/M5-S04/traceability.md` cross-referencing all 10 members (3 `ApexClass`, 3 `Group`,
  3 `PermissionSetGroup`, 1 `Report` folder) against the `req_id` each already implies via an
  existing row's `artefact_paths` cell (`REQ-018`/`019`/`020`/`022`/`023`/`024`/`044`, plus
  `REQ-032` by analogy for the bare `Report:Support_Operations` folder member — flagged
  ambiguous, not asserted, per this envelope's own `process_observations[2]`). The Matrix table
  itself — copied verbatim from the build's root `traceability.md`, per `CWB-OTHER-038`'s own
  documented promise — is untouched.
- **Alternative rejected:** writing the ten implied rows directly into the build's own
  `traceability.md` at this compile run — rejected because `agents/build-doc-keeper/AGENT.md`'s
  compile run reads `workbook/*.md` and `traceability.md` as sources, not targets, on a compile
  run, and the canonical fix belongs to the four owning steps' own per-step documentation passes
  (`M2-S01`/`M2-S02`/`M2-S04`/`M4-S05`), which alone can touch `traceability.md`'s real rows under
  Step 7 — a compile run adding rows there would blur which run wrote what; silently absorbing the
  ten members into the existing coverage line without naming them — rejected because a gap named is
  worth more at the gate than a coverage count that quietly changed meaning.
- **Remedy:** none on the artefact beyond the addendum. Follow-up named to `build-doc-keeper`'s own
  next per-step touches on the four owning steps (not scheduled by this plan — see this run's own
  `followups[]`); F-52's second half (deepening `skills/admin/requirements-traceability-matrix` so
  `check_rtm.py` gains a manifest-member coverage direction) is a skill-authoring item, not an
  artefact fix.
- **Grounded in:** `reports/MILESTONE-M5-REPORT.md` § 8 F-52; `skills/admin/
  requirements-traceability-matrix` (pipe-delimited multi-value convention; the addendum's framing
  against the verbatim Matrix).
- **Evidence:** `envelopes/M5-S04/2026-09-12T13-15-00Z.json` → `summary` point (5),
  `compiled_documents[1]`, `process_observations[2]` (ambiguous, the analogized tenth member);
  `artefacts/M5-S04/traceability.md` § addendum; `artefacts/M5-S05/package.xml`.

## D-M5S04-08 — `M5-S05` § 5.2's six-item numbering adopted as canonical over the story backlog's independent P-labels, with P6 added as a seventh item and the Entitlement-record prerequisite (F-41) now in the compiled workbook — partially closes F-56

- **Date:** 2026-09-12 · **Step:** `M5-S04` · **Agent:** `build-doc-keeper`
  (`envelopes/M5-S04/2026-09-12T13-15-00Z.json`)
- **Kind:** design trade-off
- **What was recorded:** `reports/MILESTONE-M5-REPORT.md` § 8 F-56 (MEDIUM) found two
  independently numbered prerequisite lists (`M5-S05` § 5.2's six items vs. the story backlog's
  P1–P6) that do not cross-reference each other and do not hold the same items, and that the F-41
  Entitlement-per-Account prerequisite appeared in neither the compiled workbook nor the story
  backlog. This re-compile follows the finding's own recommendation: adds a reconciled seven-item
  org-prerequisites table to `deploy-order.md` adopting `M5-S05` § 5.2's numbering as canonical (it
  is the document a release owner deploys from), cross-referencing the backlog's P-labels against
  it, and adding the sandbox-deliverability prerequisite (backlog P6, absent from § 5.2) as item 7;
  and adds `CWB-DATA-001` to the compiled workbook's Section 10, naming the
  Entitlement-record-per-Account prerequisite for the first time in any compiled document.
- **Alternative rejected:** renumbering `story-backlog.md`'s own P-labels to match, and adding the
  F-41 dependency to `US-CASE-007`'s Dependencies — both are the finding's own recommended remedy,
  and both are rejected for this run specifically because they require a write to
  `artefacts/M5-S03/story-backlog.md`, outside a compile run's Scope Guardrails (writes permitted
  only under `artefacts/M5-S04/`); adopting the backlog's P-numbering as canonical instead of
  § 5.2's — rejected because § 5.2 is the document the finding itself names as the one a release
  owner actually deploys from.
- **Remedy:** none on the artefact beyond the two additions above. `story-backlog.md`'s P-label
  renumbering and its `US-CASE-007` dependency addition are named as an explicit follow-up to
  `story-drafter` (this run's own `followups[]`), not silently left for a future reader to notice
  missing.
- **Grounded in:** `reports/MILESTONE-M5-REPORT.md` § 8 F-56; `skills/admin/
  configuration-workbook-authoring` (Section 10 row schema); `artefacts/M5-S05/deploy-order.md`
  § 5.2; `artefacts/M5-S03/story-backlog.md` (P-labels, read only).
- **Evidence:** `envelopes/M5-S04/2026-09-12T13-15-00Z.json` → `summary` point (4),
  `compiled_documents[0]`, `compiled_documents[2]`, `followups[0]`;
  `artefacts/M5-S04/configuration-workbook.md` § Section 10 `CWB-DATA-001`;
  `artefacts/M5-S04/deploy-order.md` § org-prerequisites addendum.

## D-M5S05-01 — F-43 closed: the Apex now travels in a manifest; flywheel record for the manifest-step tester carve-out the playbook does not yet name

- **Date:** 2026-09-12 · **Step:** `M5-S05` (`docs`) · **Agent:** `metadata-builder` (build run
  `2026-09-12T12-16-22Z`); tested by `step-tester` (`2026-09-12T12-28-47Z`); recorded here by
  `build-doc-keeper`
- **Kind:** two-part — (a) a finding closure, the same shape **D-M4S05-01**/**D-M5S01-01** give a
  flywheel record; (b) a playbook gap, the flywheel's shape applied to an agent's own `AGENT.md`
  rather than to a skill
- **What was recorded (a):** **F-43**, raised at the M4 gate (`envelopes/M4/2026-09-12T09-08-11Z.json`
  → finding `F-43`; `reports/MILESTONE-M4-REPORT.md` § F-43): *"no manifest in the build carries the
  Apex until M5-S05 is built — manifest-mode validation of M4 must wait for M5-S05; source-mode run 4
  is the evidence today."* `M5-S05`'s own envelope names the same gap explicitly before closing it
  (`envelopes/M5-S05/2026-09-12T12-16-22Z.json` → `process_observations`: *"This manifest is the
  first in the build to carry the Apex, so nothing has ever validated the Apex members through a
  merged manifest."*). `reports/MOCK-DEPLOY-M5.md` Run 3 — manifest mode, every built step through
  `M5-S05`, the merged `package.xml` including the four `ApexClass`/`ApexTrigger` members — ran next
  and recorded *"This is the first validation in the build that reads a manifest carrying the Apex
  (M4-S05's trigger and classes) — F-43 closed"*: 60 components, 60 ok, 1 error (`F-28`, the
  unprovisioned `OrgWideEmailAddress`, unchanged and expected). **F-43 is CLOSED.**
- **What was recorded (b):** `step-tester`'s formal run on this same step
  (`envelopes/M5-S05/2026-09-12T12-28-47Z.json` → `process_observations`, category `ambiguous`,
  domain `playbook-gap`) flags that `agents/step-tester/AGENT.md` Step 3's file↔manifest rules are
  written as *"for every artefact file [under the step's artefact directory]"*, with no explicit
  carve-out for a build-level manifest step whose own artefact directory holds no component files at
  all (`M5-S05`'s directory holds only `package.xml` and `deploy-order.md`). The tester widened the
  check to the whole `artefacts/` tree by inference from the step's own `acceptance_tests[2]` wording
  and from `deploy-order.md` § 5.1's self-described method, not from a branch the playbook names —
  and said so rather than silently picking a reading.
- **The gap is NOT yet closed at the source, unlike D-M4S01-01/D-M5S04-02.** This build has exactly
  one build-level manifest step, so there is no second run to prove a fix against; the entry is
  recorded now as the signal for the next build's `agents/step-tester/AGENT.md` revision to add the
  carve-out explicitly, the same flywheel discipline `standards/build-orchestration.md` § 8 applies
  to a skill gap.
- **Alternative rejected:** leaving F-43 open pending a human's own manifest-mode run — rejected
  because `reports/MOCK-DEPLOY-M5.md` Run 3 is that run, already executed and already dry-run-only
  (`checkOnly: true`, nothing deployed); re-deriving the tester's whole-tree reading from scratch on
  a future build rather than naming the playbook gap now — rejected because a future step-tester run
  would face the identical ambiguity with no record of how this one resolved it.
- **Grounded in:** `standards/build-orchestration.md` § 5 "The Apex exception"; § 8 (a skill/playbook
  gap is the signal to deepen the source, never to freestyle around it).
- **Evidence:** `reports/MILESTONE-M4-REPORT.md` § F-43; `envelopes/M5-S05/2026-09-12T12-16-22Z.json`
  → `process_observations`; `reports/MOCK-DEPLOY-M5.md` Run 3; `tests/M5-S05/summary.md` §
  "ambiguous, medium, playbook-gap"; `envelopes/M5-S05/2026-09-12T12-28-47Z.json` →
  `process_observations` (category `ambiguous`, domain `playbook-gap`).

## D-M5S05-02 — This manifest follows `M3-S03`'s safe sequence (rules before `Settings:Case`), diverging from `M5-S04`'s compiled ten-slot order by one position — named, not silently re-ordered

- **Date:** 2026-09-12 · **Step:** `M5-S05` (`docs`) · **Agent:** `metadata-builder`; recorded here
  by `build-doc-keeper`
- **Kind:** design trade-off — a plan-level ordering conflict named rather than silently absorbed,
  the same shape **D-M2S04-05** gives an earlier cross-step ordering question
- **What was recorded:** `artefacts/M5-S05/deploy-order.md` § 3.3 states that its own § 3.1 table
  places `AssignmentRules:Case`/`AutoResponseRules:Case` (slot 10) **before** `Settings:Case`
  (slot 11), while `artefacts/M5-S04/deploy-order.md`'s compiled ten-slot table lists
  `Settings:Case` (`CWB-AUT-007`) ahead of the two rule rows (`CWB-AUT-010`/`CWB-AUT-011`),
  following plan step order (`M3-S03` before `M3-S04`). `artefacts/M3-S03/deploy-order.md` § 3
  itself states the opposite is required for any org that will receive real mail: assignment and
  auto-response rules must be active **before** `Settings:Case` turns the channel on, or live
  traffic lands unrouted at `defaultCaseOwner` with no acknowledgement sent. `M5-S05` follows
  `M3-S03`'s safe sequence rather than `M5-S04`'s compiled one. The failure mode this avoids is not
  a deploy error — both orders deploy cleanly, because Metadata API resolves component dependencies
  within one request regardless of `<types>` block order (§ 3.2) — it is a live-traffic gap between
  activation and the human step (mail-server forwarding, form publication) that actually turns the
  channel on.
- **Alternative rejected:** silently adopting `M5-S04`'s order to make the two files agree —
  rejected because it would ship the less safe sequence with no record that a safer one was known;
  editing `M5-S04`'s already-`documented` compiled table to match — rejected for the same reason
  `agents/build-doc-keeper/AGENT.md` Step 8 leaves another step's rows byte-identical, and because
  `M5-S04`'s table is itself a correct compilation of plan step order, not an error in transcription.
- **Remedy:** none needed in either artefact — both orders are internally consistent and both are
  named. Carried to the M5 gate as an explicit item: a release owner sequencing the actual deploy
  should follow `M5-S05`'s order (slot 10 before slot 11), and the real safety margin is the human
  step after slot 11 (§ 3.3), not the manifest's own `<types>` order.
- **Grounded in:** `artefacts/M3-S03/deploy-order.md` § 3; `artefacts/M5-S04/deploy-order.md`
  (ten-slot table); `admin/case-management-setup/references/metadata-examples.md` § 5.
- **Evidence:** `artefacts/M5-S05/deploy-order.md` §§ 3.1, 3.2, 3.3; `artefacts/M5-S04/deploy-order.md`
  hazard list (M3-S03/M3-S04 entry); `envelopes/M5-S05/2026-09-12T12-16-22Z.json` →
  `extensions.decision_record`.

## D-M5S05-03 — Six org prerequisites carried forward from four milestone gates are compiled into one release checklist; none is expressible as a manifest member or a molecular test

- **Date:** 2026-09-12 · **Step:** `M5-S05` (`docs`) · **Agent:** `metadata-builder`; recorded here
  by `build-doc-keeper`
- **Kind:** design trade-off, held open as a release checklist — the same shape **D-M3S04-03**/
  **D-M3S04-04** hold F-28 open as a milestone-gate prerequisite, extended here to all six
- **What was recorded:** `artefacts/M5-S05/deploy-order.md` § 5.2 compiles six org prerequisites,
  each already raised at an earlier milestone gate and none closable by metadata in this build:
  (1) **F-28** — `support-noreply@acme.example` provisioned and verified as an `OrgWideEmailAddress`
  before `AutoResponseRules:Case` deploys (G3 decision 4); (2) **F-39** — Entitlement Management
  (`enableEntitlements`) plus `enableMilestoneStoppedTime` (G4 decision 2); (3) **F-44** —
  non-routing mailboxes on the `Billing` and `Tier_2_Engineering` queues before the escalation rule
  is activated (G4 decision 1); (4) **F-41** — an `Entitlement` record per Account pointing at the
  right process; (5) **F-51** — the report's "Escalated = True" criterion, added in the report
  builder after deploy, because no column code could be probed; (6) **G4 decision 9** — an active
  `SlaProcess` carrying a First Response milestone, for `M4-S05`'s `SeeAllData=true` test. `M5-S05`'s
  own envelope (`extensions.org_prerequisites`) lists the same six verbatim. `step-tester`'s formal
  run (`process_observations`, category `concerning`, domain `release-readiness`) confirms none of
  the six is expressible as a manifest member, a declared checker, or a molecular test — *"a tested
  build-level manifest carries no signal on any of them."*
- **Alternative rejected:** inventing a manifest member or a checker assertion for one of the six to
  make the step's test suite "cover" them — rejected as fabrication with no metadata type to carry
  it (an org-wide email address, a feature-settings switch already on in the dev org, a data record,
  a report-builder criterion and a test-fixture record are none of them retrievable/deployable
  components); silently omitting the compiled list because no test can assert it — rejected because
  an omitted prerequisite is a prerequisite nobody is warned about.
- **Remedy:** none needed in the artefact. Carried to the M5 gate as the release checklist verbatim
  — six items, none defaulted, none silently dropped.
- **Grounded in:** `admin/change-management-and-deployment` (Questions-to-Ask, § 6); G3 decision 4;
  G4 decisions 1, 2, 9; `reports/MOCK-DEPLOY-M3.md` run 6 (F-28); `reports/MILESTONE-M4-REPORT.md`
  (F-39, F-41, F-44).
- **Evidence:** `artefacts/M5-S05/deploy-order.md` § 5.2; `envelopes/M5-S05/2026-09-12T12-16-22Z.json`
  → `extensions.org_prerequisites`; `tests/M5-S05/summary.md` § "concerning, medium,
  release-readiness".

## D-M5S05-04 — Four release-owner decisions (`rollbackOnError`, `testLevel`, validation timing, the backout plan) are left open by design; this build defaults none of them

- **Date:** 2026-09-12 · **Step:** `M5-S05` (`docs`) · **Agent:** `metadata-builder`; recorded here
  by `build-doc-keeper`
- **Kind:** design trade-off, held open as release-owner decisions — the skill's own Questions-to-Ask
  table, reproduced rather than answered
- **What was recorded:** `artefacts/M5-S05/deploy-order.md` § 6 and the owning agent's own
  `extensions.decision_record` (`envelopes/M5-S05/2026-09-12T12-16-22Z.json`) both record four of
  the skill's release-options questions as **"Not bound by the plan"** rather than defaulted: (1)
  whether `rollbackOnError` is set explicitly — the skill documents production *must* set it `true`
  and that the guide's own `DeployOptions`/`DeployResult` pages disagree on the default, so an
  unstated value is a real ambiguity, not a formality; (2) which `testLevel` applies — recorded that
  this manifest's one trigger and three classes mean a production deploy defaults to
  `RunLocalTests`, but the release owner still chooses the window that absorbs a full local-test
  run; (3) validation timing relative to the deploy window — the ten-day quick-deploy clock is
  named, the actual date is not; (4) the backout plan if the release "behaves badly at 09:00" — the
  skill's deactivate-don't-delete answer is recorded (the two validation rules, the assignment rule,
  the flow's active version; the escalation rule already ships inactive) but nobody has agreed to
  execute it. The fifth and sixth questions in the same table **are** answered by this build's own
  artefacts, not left open: nothing is deleted (§ 2.3), and components arriving needing a switch
  flipped are named in full (§ 4).
- **Alternative rejected:** defaulting `rollbackOnError: true` and `RunLocalTests` into the manifest
  or the deploy-order note as though decided — rejected because neither is a manifest element
  Metadata API deploy options carry in `package.xml` itself, and stating a default as though chosen
  would misrepresent an unmade decision as a made one; silently omitting the four from the compiled
  note because this agent cannot decide them — rejected because an admin running the validate-only
  command in § 7 needs to know these are still open before choosing `--test-level` on the command
  line.
- **Remedy:** none needed in the artefact. Carried to the M5 gate as four named release-owner
  decisions, each with the skill's own default/contradiction stated so the human is not deciding
  from a blank page.
- **Grounded in:** `admin/change-management-and-deployment` (Questions-to-Ask, § 6, `rollbackOnError`
  api_meta L4256–L4260, the ten-day quick-deploy clock, the deactivate-don't-delete guidance).
- **Evidence:** `artefacts/M5-S05/deploy-order.md` § 6; `envelopes/M5-S05/2026-09-12T12-16-22Z.json`
  → `extensions.decision_record` (six question/answer pairs, four marked "Not bound by the plan").

## D-M5S05-05 — The `<version>` split is recorded, not reconciled: nine step manifests stay at `62.0`, the build manifest ships at `67.0` per G3 decision 6; a plan-level `api_version` remains a planner v6 item

- **Date:** 2026-09-12 · **Step:** `M5-S05` (`docs`) · **Agent:** `metadata-builder`; recorded here
  by `build-doc-keeper`
- **Kind:** design trade-off, version-gated — the same shape **D-M2S02-04**/**D-M4S03-04** give an
  earlier API-version choice, here applied to the build-wide aggregate rather than one step
- **What was recorded:** `artefacts/M5-S05/deploy-order.md` § 1.2 and `envelopes/M5-S05/2026-09-12T12-16-22Z.json`
  → `extensions.version_split` both record the same split: nine step manifests —
  `M1-S01`, `M1-S02`, `M2-S01`, `M2-S02`, `M2-S03`, `M2-S04`, `M2-S05`, `M3-S01`, `M3-S02` — still
  declare `<version>62.0</version>`; seven — `M3-S03`, `M3-S04`, `M4-S01`, `M4-S02`, `M4-S03`,
  `M4-S04`, `M5-S01` — declare `67.0`. The build-level `package.xml` this step wrote is stamped
  `67.0` on two independent grounds: (1) **G3 decision 6** (`plan.json.human_gates`,
  `milestone:M3`) — *"build API version = 67.0 accepted; accepted M1/M2 manifests are not
  rewritten; `scripts/mock_deploy.py` deploys at the highest step version; planner v6 adds a
  plan-level `api_version`"* — carried forward unchanged by the `milestone:M4` gate note; (2) **the
  org proved the floor**: `MOCK-DEPLOY-M3.md` run 4 probes a–c show `newEntityRecordType` on the
  Email-to-Case routing addresses is *"not valid in version 62.0"* and *"not valid in version
  63.0,"* resolving only from `64.0`, so `M3-S03`'s `Settings:Case` cannot deploy at all below that
  floor. The nine `62.0` step manifests are **left as they are**, per the same gate decision — a
  merged manifest at `67.0` and a step manifest at `62.0` record two different facts (what the step
  was built and accepted at, versus what the build deploys at) and are not in conflict with each
  other.
- **Alternative rejected:** rewriting the nine `62.0` step manifests to `67.0` to make every file in
  the build agree — rejected explicitly by G3 decision 6 ("accepted M1/M2 manifests are not
  rewritten"), because each step's own manifest is a record of what was built and accepted at the
  time, and rewriting it after the fact would misstate that history; leaving the build-level
  manifest at a mixed or unstated version — not possible, because `package.xml` carries exactly one
  `<version>` element for the whole file.
- **Remedy:** none needed in this build's artefacts. The still-open planner item is a `plan.json`-level
  `api_version` field (`build-planner` v6), so a future build does not have to reconstruct this split
  from nine individual step manifests and a human gate note the way this step did.
- **Grounded in:** `plan.json.human_gates` (`milestone:M3` decision 6, `milestone:M4` note);
  `reports/MOCK-DEPLOY-M3.md` run 4, probes a–c; the build-wide API-version drift `decisions.md`
  **O-M3S03-01** first named as a `build-planner` v6 backlog item.
- **Evidence:** `artefacts/M5-S05/deploy-order.md` § 1.2; `envelopes/M5-S05/2026-09-12T12-16-22Z.json`
  → `extensions.version_split`; `plan.json.human_gates[milestone:M3].notes` (decision 6).
