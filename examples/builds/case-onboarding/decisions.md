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
