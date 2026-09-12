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
