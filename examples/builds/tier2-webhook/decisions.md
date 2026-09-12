# Decisions log

Append-only. Written by the build doc keeper.

Entry shape follows `skills/devops/development-documentation-standards` § "Org-level design
standards" — one central location, and an entry that records the date, the step, the agent that
made the call, **the alternative it rejected** and **the source it was grounded in**, rather than a
sentence asserting the outcome. Append-only: an earlier entry is never rewritten, and a reversal is
a new entry naming the one it supersedes.

---

## D-M1S01-01 — Planner reading-list gap: `admin/custom-field-creation` cited by no writer step

- **Date:** 2026-09-12
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-12T09-34-25Z`), surfaced again by `build-step-runner`
  (run `2026-09-12T09-36-29Z`)
- **Kind:** skill gap, per `agents/build-doc-keeper/AGENT.md` Step 3 table — "the gap the runner
  recorded when it set a step `blocked`" generalised here to a gap the owning agent recorded without
  blocking, because the artefact still built correctly against a real, uncited skill.
- **What was recorded:** the step's `skills[]` names four skills (`admin/object-creation-and-design`,
  `admin/picklist-and-value-sets`, `apex/platform-events-apex`, `flow/flow-error-monitoring`). None of
  the four, nor any of `metadata-builder`'s eight floor skills, carries a fenced example for
  `<type>DateTime</type>` (three fields: `Last_Attempted_At__c`, `Case.Tier2_Notified_At__c`, plus the
  event's `Escalated_At__c`) or `<type>Checkbox</type>`/`<defaultValue>` (`Resend__c`). The builder
  grounded both in `skills/admin/custom-field-creation/references/metadata-examples.md` (the FieldType
  enum list and the Checkbox worked example in § 4) — a real library skill that owns exactly this
  surface, but that the step's `skills[]` does not cite. `admin/object-creation-and-design`'s own
  frontmatter description says "NOT for designing the fields on the object - use
  admin/custom-field-creation", which the plan did not act on for this step.
- **Alternative rejected:** refusing to build the two field types until the step was amended to add
  the citation. Rejected by the owning agent because `amend-step` requires the build status to be
  `building` or `approved` and the step's own status `pending`/`blocked` — both held at the time — so
  amendment *was* legally available, but the builder judged a correctly-grounded field (just grounded
  in an uncited-but-real skill) a lower-risk path than stalling the step, and filed the gap instead of
  silently absorbing it.
- **Grounded in:** `skills/admin/custom-field-creation/references/metadata-examples.md` (FieldType
  enum, § 4 Checkbox example); `skills/admin/object-creation-and-design/SKILL.md` frontmatter
  description line 3; `reports/drivers-log.md` "Build M1-S01" entry, friction (20).
- **Why this agent cannot fix it:** per `agents/build-doc-keeper/AGENT.md` "This Agent Does NOT Do" —
  it does not touch `plan.json` beyond the single status transition it owns, and adding a skill
  citation to another agent's claimed step is `build-planner`'s or a human's call via `amend-step`,
  not a doc-keeper edit. Recorded here as the signal `standards/build-orchestration.md` § 8 names — a
  documented gap is how a skill gets deepened or a step's reading list gets corrected — not fixed by
  this run.
- **Open item:** either `amend-step M1-S01` to add `admin/custom-field-creation` to `skills[]` (legal
  now only if the step is reset `documented` → `running`, since it has already passed `built`), or fix
  the planner's Step-2 grep so an `object-model` step with `CustomField` outputs always pulls in the
  field-creation skill.
- **Evidence:** `envelopes/M1-S01/2026-09-12T09-34-25Z.json` → `dimensions_skipped[0]` and
  `process_observations[0..1]`; `envelopes/M1-S01/2026-09-12T09-36-29Z.json` →
  `dimensions_skipped[0]`; `reports/drivers-log.md` "Build M1-S01 (13:55–14:40)" friction (20).

## D-M1S01-02 — `Status__c` is a required field; its permissions can't be retrieved or deployed, and M1-S02 has to absorb that

- **Date:** 2026-09-12
- **Step:** `M1-S01` (`object-model`), constraint binding on `M1-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T09-34-25Z`); the exclusion itself was applied by the
  dry-run operator's amendment to `M1-S02.inputs` at `2026-09-12T09:41:08Z`, recorded in
  `plan.json` → `steps[M1-S02].amendments[0]`
- **Kind:** design trade-off surfaced as a cross-step constraint, per `agents/build-doc-keeper/AGENT.md`
  Step 3 ("Deviation" — M1-S02 built differently from what its original `inputs{}` asked for, with a
  stated reason).
- **What was recorded:** `Integration_Failure__c.Status__c` is written `required true` (Q17). The
  Metadata API Developer Guide states, of `PermissionSet`/`Profile` field permissions: "In API version
  30.0 and later, permissions for required fields can't be retrieved or deployed" — cited in this
  step's own `deploy-order.md` § 6 as `api_meta.txt:95020–95021`, and independently quoted (same line
  numbers) in `skills/admin/custom-field-creation/references/metadata-examples.md` line 99–101, § 9
  ("Do not write a `fieldPermissions` entry for it — see §9"). M1-S02's original
  `inputs.permission_set.fieldPermissions` read "Every custom field on `Integration_Failure__c` from
  M1-S01 readable and editable" — twelve fields, including `Status__c`. Taken literally that is a
  `fieldPermissions` entry the platform refuses to deploy. The operator's amendment narrows the grant
  to the eleven non-required fields, citing `api_meta L95020–95021` directly in the amendment's
  `reason` field.
- **Alternative rejected:** leaving `Status__c` `required false` so its field permission could be
  granted explicitly. Rejected because `required true` is Q17's own answer and a database constraint
  every DML path pays (Data Loader, Bulk API, Flow, Apex) — softening it to work around a permission-set
  mechanic would be optimizing the object for the wrong thing.
- **Grounded in:** Metadata API Developer Guide (id `api_meta` per `knowledge/sources.yaml`, url
  `https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm`), the
  passage quoted at `api_meta.txt:95020–95021` in
  `skills/admin/custom-field-creation/references/metadata-examples.md` line 99–101; the same citation
  appears in this step's `artefacts/M1-S01/deploy-order.md` § 6 and in this build's
  `envelopes/M1-S01/2026-09-12T09-34-25Z.json` `process_observations[2]` (severity `high`).
  **On the `api_meta L95020` citation itself:** I could not independently verify the exact quoted
  sentence against a local full copy of the Metadata API Developer Guide — the only local import
  (`knowledge/imports/salesforce-metadata-api-guide.md`) is a 6,507-line excerpt, far short of line
  95020, so the citation resolves to the *online* guide, which this run did not fetch. What I did
  verify locally: the sentence is quoted character-for-character in
  `skills/admin/custom-field-creation/references/metadata-examples.md` (line 101, dated skill content,
  not this run's invention), the same line-number citation (`L95020–95021`) is used nowhere else in
  the repo for a different claim (checked: `grep -rn "L95020"` returns only this skill file and this
  build's own plan/envelope/deploy-order files, all pointing at the same sentence), and the
  neighbouring citations from the same skill file and the same permission-set family of skills land in
  the immediately adjacent range (`api_meta L95069`–`L95397`, the `PermissionSet`/`PermissionSetGroup`
  field documentation per `skills/admin/permission-set-group-composition/references/metadata-examples.md`),
  which is consistent with `L95020` sitting in the same document region (the `fieldPermissions`
  element's own description, just before `objectPermissions` at `L95069`). That consistency is
  circumstantial corroboration, not verification of the exact wording — recorded honestly rather than
  asserted as confirmed.
- **Consequences:** M1-S02's permission set covers eleven `Integration_Failure__c` fields, not twelve;
  a human reviewer at the M1-S02 gate should confirm the amendment landed in the step's actual
  `inputs.permission_set.fieldPermissions` before that step is built.
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 6; `plan.json` →
  `steps[M1-S02].amendments[0].reason`; `tests/M1-S01/summary.md` "Process notes"; `reports/drivers-log.md`
  "Build M1-S01" entry ("Cross-step finding … api_meta L95020").

## D-M1S01-03 — Unbound: the `enableBulkApi`/`enableSharing`/`enableStreamingApi` trio is written `true`, but only the all-or-none rule is confirmed

- **Date:** 2026-09-12
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-12T09-34-25Z`)
- **Kind:** design trade-off — an ambiguity recorded rather than filled.
- **What was recorded:** `Integration_Failure__c` ships with `enableBulkApi`, `enableSharing` and
  `enableStreamingApi` all `true`.
- **Alternative rejected:** leaving all three elements absent. Both shapes clear every declared
  checker (the checker enforces only that the trio is all-or-none, per the step's own
  `inputs.custom_object.optional_feature_trio`), so absence was a live, equally-legal alternative.
- **Grounded in:** the only fenced worked example the step's cited skills carry
  (`admin/object-creation-and-design/references/metadata-examples.md`, the parent-object example),
  which writes the trio `true`. No clarification or decision names the value itself, only the
  all-or-none constraint.
- **Open item:** exact language from `artefacts/M1-S01/deploy-order.md` § 5 item 1 — "If the org does
  not want `Integration_Failure__c` classified as an Enterprise Application object, remove all three
  elements — not one of them."
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 5 item 1; `envelopes/M1-S01/2026-09-12T09-34-25Z.json`
  → `extensions.unbound_elements_flagged[0]`.

## D-M1S01-04 — Unbound: `externalSharingModel` omitted

- **Date:** 2026-09-12
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-12T09-34-25Z`)
- **Kind:** design trade-off — an ambiguity recorded rather than filled.
- **What was recorded:** no `<externalSharingModel>` element is written on `Integration_Failure__c`.
- **Alternative rejected:** guessing a value (`Private`, to match the internal `sharingModel`).
  Rejected because no clarification, decision or step input names it, and decision D12 reasons only
  about internal access.
- **Grounded in:** the Metadata API Developer Guide describes `externalSharingModel` as a second,
  separate OWD governing external users (`api_meta.txt:42132–42134`, per this step's own
  `deploy-order.md` § 4/§5), which defaults on in an org with Salesforce Experiences enabled.
- **Open item:** exact language from `artefacts/M1-S01/deploy-order.md` § 5 item 2 — "**If the target
  org is an Experience Cloud org, decide this before deploy** — an omitted element leaves external
  access at whatever the org already had." `requirement.md`'s Q44 states the audience is "internal
  employees only, with no Experience Cloud or partner licence implication" (per `plan.json` `scope.out`),
  which weighs against this ever mattering for this build but does not remove the open item from the
  artefact itself.
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 5 item 2; `envelopes/M1-S01/2026-09-12T09-34-25Z.json`
  → `process_observations[3]`, `extensions.unbound_elements_flagged[1]`.

## D-M1S01-05 — Unbound: `startingNumber` omitted on the `AutoNumber` name field

- **Date:** 2026-09-12
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-12T09-34-25Z`)
- **Kind:** design trade-off — an ambiguity recorded rather than filled.
- **What was recorded:** `Integration_Failure__c`'s `nameField` carries `type AutoNumber` and
  `displayFormat IF-{00000000}` but no `startingNumber` element.
- **Alternative rejected:** writing `startingNumber` `1` explicitly. Rejected as redundant noise: the
  platform default for a custom Auto Number field is already 1, and the step input names no other
  value.
- **Grounded in:** exact language from `artefacts/M1-S01/deploy-order.md` § 5 item 3 — "The platform
  default for a custom Auto Number field is 1. It 'can't be retrieved… through Metadata API' (Gotcha 6,
  api_meta.txt L43623–43635), so a later retrieve/redeploy round trip will not carry it either."
- **Open item:** "If this build ever seeds historical rows that must continue an external sequence, add
  the element deliberately at that deploy" (`deploy-order.md` § 5 item 3, verbatim).
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 5 item 3; `envelopes/M1-S01/2026-09-12T09-34-25Z.json`
  → `extensions.unbound_elements_flagged[2]`.

## D-M1S01-06 — Unbound: derived, cosmetic labels written without a source answer

- **Date:** 2026-09-12
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-12T09-34-25Z`)
- **Kind:** design trade-off — an ambiguity recorded rather than filled.
- **What was recorded:** `nameField/label` = "Integration Failure Number"; `Tier2_Escalation__e/pluralLabel`
  = "Tier 2 Escalations"; `Case__c`'s `relationshipName` (`Integration_Failures`) and
  `relationshipLabel` ("Integration Failures") were all derived by the builder, not supplied by any
  clarification or decision.
- **Alternative rejected:** blocking the step until a human named every label. Rejected because all
  four appear in the shape of every cited fenced example, are user-facing text only (three of the
  four), and the plan carries no answer that would be contradicted by a reasonable derivation.
- **Grounded in:** exact language from `artefacts/M1-S01/deploy-order.md` § 5 item 4 — "Both elements
  appear in every cited fenced example, both are user-facing text only, and neither is bound by the
  plan. Rename freely." The same item flags that `relationshipName` is **not** cosmetic like the other
  three: "it is the subquery name (`SELECT Id, (SELECT Id FROM Integration_Failures__r) FROM Case`), so
  changing it after M1-S03 is written is a code change too."
- **Open item:** `relationshipName` (`Integration_Failures`) is now load-bearing for M1-S03's Apex —
  renaming it after that step is written requires an Apex change, not just a metadata rename.
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 5 item 4; `envelopes/M1-S01/2026-09-12T09-34-25Z.json`
  → `extensions.unbound_elements_flagged[3]`.

## D-M1S01-07 — Unbound: `Severity__c` ships with no default value; both restricted values written `false`

- **Date:** 2026-09-12
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-12T09-34-25Z`)
- **Kind:** design trade-off — an ambiguity recorded rather than filled.
- **What was recorded:** `Integration_Failure__c.Severity__c`'s restricted picklist carries `Error` and
  `Warning`, **neither** marked `<default>true</default>`.
- **Alternative rejected:** defaulting one value (e.g. `Error`, the more severe of the two) so the
  field is never blank on a hand-created test record. Rejected because no answer names a default, and
  the Metadata API's own rule cuts the other way.
- **Grounded in:** exact language from `artefacts/M1-S01/deploy-order.md` § 4 (the "Decisions recorded
  while writing these files" table, `Severity__c` row) — "Step input fixes the value list only; no
  answer names a default. `default` is required on every `CustomValue` and defaults to `true` when
  omitted (api_meta.txt:47513–47516), so both are written `false` rather than letting the platform
  pick." Contrast with `Status__c`, whose default (`New`) **is** named in Q17's answer.
- **Open item:** none named by the step itself; flagged here because a human reading this row should
  not assume the absence of a default is an oversight — it is the documented, narrower alternative to
  the platform silently picking one when `default` is omitted.
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 4, `Severity__c` row.

## D-M1S01-08 — Unbound: `visibleLines` on the three `LongTextArea` fields is a display choice, not a requirement

- **Date:** 2026-09-12
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-12T09-34-25Z`)
- **Kind:** design trade-off — an ambiguity recorded rather than filled.
- **What was recorded:** `Response_Body__c` and `Request_Payload__c` carry `visibleLines 10`;
  `Error_Message__c` carries `visibleLines 5`.
- **Alternative rejected:** picking different line counts, or omitting a rationale for the ones chosen.
  Rejected because `visibleLines` is a required element on the type regardless of the number chosen, so
  *some* value had to be written either way, and copying a template's numbers is more defensible than a
  fresh guess.
- **Grounded in:** exact language from `artefacts/M1-S01/deploy-order.md` § 5 item 5 — "a display
  choice copied from `templates/apex/custom_objects/fields/Message__c.field-meta.xml` and
  `Stack_Trace__c`. The element is required on the type; the numbers carry no requirement behind them."
- **Open item:** none — flagged so a reviewer does not read the specific numbers (10/5/10) as
  requirement-driven.
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 5 item 5;
  `envelopes/M1-S01/2026-09-12T09-34-25Z.json` → `extensions.unbound_elements_flagged[4]`.

## D-M1S02-01 — Skill gap: neither declared checker asserts an `AuthHeader` parameter carries `parameterValue`; run 1 shipped a credential both checkers passed and the org rejected

- **Date:** 2026-09-12
- **Step:** `M1-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-12T10-08-07Z`, `run 1`); the gap was caught by `mock-deploy`
  (run `2026-09-12T10:22:48Z`) and reconfirmed by `step-tester` against the rebuilt artefacts (run
  `2026-09-12T10-32-00Z`)
- **Kind:** skill gap, per `agents/build-doc-keeper/AGENT.md` Step 3 table, generalised the same way
  `D-M1S01-01` generalised it — a gap the owning agent's tooling did not catch, surfaced without the
  step ever being set `blocked`.
- **What was recorded:** run 1 shipped `ExternalCredential OnCall_Tool_EC`'s `X-API-Key` `AuthHeader`
  parameter with no `parameterValue`, because two unknowns sat on top of each other: the formula
  grammar was UNVERIFIED in `skills/apex/apex-named-credentials-patterns`, and no clarification named
  the Setup parameter the API key would be stored under. Both declared checkers —
  `check_apex_named_credentials_patterns.py` (step scope) and `check_permission_set_architecture.py`
  (build scope) — exited 0 on that credential (`envelopes/M1-S02/2026-09-12T10-19-53Z.json`). The
  org did not: `sf project deploy start --dry-run` returned `The parameter type "AuthHeader" requires
  these fields: ParameterValue.` (finding S2-F-02, `reports/MOCK-DEPLOY-M1.md` run 1), and a cascade
  failure on the permission set's principal grant (S2-F-03). After the rebuild added
  `parameterValue` (§ below), **both checkers still exited 0 on the corrected credential** — proving
  the gap is a genuine blind spot in the checkers' rule set, not a fluke of run 1's specific value:
  `envelopes/M1-S02/2026-09-12T10-32-00Z.json` → `process_observations`, category `concerning`,
  severity `high`, domain `checker-coverage-gap`: "a green run from this agent is not evidence the
  org would accept the credential."
- **The flywheel this closes and the one it opens:** the *value* is closed — the requester supplied
  the endpoint URL and the Setup parameter name (`amendments[1]`, `2026-09-12T10:23:06Z`) that the
  clarifier's own question set never asked for (`driver's log 26`, quoted verbatim in
  `artefacts/M1-S02/deploy-order.md` § 0: "The clarifier never asked either fact"). The *skill/checker*
  gap is not closed by this run: `reports/MOCK-DEPLOY-M1.md`'s own remedy line says "the skill gains
  two Questions-to-Ask rows, a corrected example and a checker rule (AuthHeader without
  `parameterValue` → ERROR with the org's text)" — none of that is this agent's to write.
- **Alternative rejected:** guessing a plausible `parameterValue` formula and a plausible endpoint URL
  at build time, so the credential would deploy clean on the first attempt. Rejected by the original
  builder, and endorsed here in hindsight by `tests/M1-S02/results.json` → `healthy` observation
  ("Run 1's decision to omit the AuthHeader parameterValue rather than guess it produced exactly the
  right failure: a loud deploy-time error naming the missing element, not a credential that deploys
  clean and 401s at run time.") — a wrong guess would have passed every checker and every dry run and
  failed silently in production.
- **Grounded in:** `reports/MOCK-DEPLOY-M1.md` run 1 (org error text, verbatim); `skills/apex/apex-
  named-credentials-patterns/references/code-examples.md` § 1 (UNVERIFIED marker, dated 2026-09-05);
  `artefacts/M1-S02/deploy-order.md` § 0 and § 5 item 1; `envelopes/M1-S02/2026-09-12T10-28-30Z.json`
  → `process_observations` (`concerning`, `skill-quality`: "The cited skill has no Questions-to-Ask
  row for either fact the requester had to supply late … and its own worked example carries the same
  dangling reference that misled run 1").
- **Open item:** `skills/apex/apex-named-credentials-patterns` needs (a) two Questions-to-Ask rows —
  the endpoint URL and the Setup parameter name a stored secret resolves by — (b) its
  `$Credential.Partner_Orders_EC.ApiToken` worked example corrected to declare the parameter it
  references, and (c) `check_apex_named_credentials_patterns.py` needs a rule that ERRORs an
  `AuthHeader` `externalCredentialParameters` entry with an empty or absent `parameterValue`, quoting
  the org's own text. None of this is `build-doc-keeper`'s to fix — recorded here as the signal
  `standards/build-orchestration.md` § 8 names.
- **Evidence:** `reports/MOCK-DEPLOY-M1.md` runs 1–2; `envelopes/M1-S02/2026-09-12T10-08-07Z.json`,
  `.../2026-09-12T10-28-30Z.json`, `.../2026-09-12T10-32-00Z.json`; `tests/M1-S02/results.json`;
  `artefacts/M1-S02/deploy-order.md` §§ 0, 5.

## D-M1S02-02 — Deviation: the `step:M1-S02` human gate was rejected and re-signed mid-build after an operator sequencing error

- **Date:** 2026-09-12
- **Step:** `M1-S02` (`access`)
- **Agent:** `dry-run operator (Fable)`, recorded in `plan.json` → `steps[M1-S02].runs[]`
- **Kind:** deviation — the build did not follow its own single-pass gate-then-build sequence for
  this step, with the reason stated in the run record itself.
- **What was recorded:** `step:M1-S02` was first approved at `2026-09-12T10:01:57Z`, before the
  credential's contents were finalised. Run 1's `mock-deploy` rejection (S2-F-02/S2-F-03) then
  required the requester to supply new facts (`amendments[1]`). The `runs[]` array carries an
  operator's own admission of a sequencing fault: *"operator sequencing error: moved to running
  before the amendment landed; stepping back to pending to reject the step gate, amend, and
  re-sign"* (`2026-09-12T10:23:06Z`). `human_gates` then shows `step:M1-S02` re-approved one second
  later, `2026-09-12T10:23:07Z`, with the note "Re-signed after the S2-F-02 amendment: same
  credential, named credential and permission-set grant as before, now with the real endpoint URL and
  the AuthHeader formula … the key itself is entered in Setup after deploy and never lives in
  metadata."
- **Why this is recorded as a deviation rather than absorbed silently:** a `human_gate: true` step
  exists precisely because its content (a credential and a permission set) needs a human's eyes before
  the step is allowed to run; a gate signed against one version of that content and then built against
  a materially different one — a real endpoint and a real auth formula in place of a
  reserved-documentation placeholder and an absent element — would make the gate's own timestamp
  misleading about what was actually reviewed.
- **Alternative rejected:** treating the amendment as covered by the original `10:01:57Z` approval
  and proceeding straight to rebuild without a second signature. Rejected by the operator itself, per
  the `runs[]` entry above — the step was deliberately stepped back to `pending` to force the
  re-approval rather than let the original gate stand for changed content.
- **Grounded in:** `plan.json` → `steps[M1-S02].runs[]` (the `dry-run-operator` entry,
  `2026-09-12T10:23:06Z`) and `steps[M1-S02].amendments[1]`; `plan.json` → `human_gates[]`, the two
  `step:M1-S02` records at `10:01:57Z` and `10:23:07Z`.
- **Consequences:** the cost of the error is one step re-run cycle (rebuild, re-test) rather than a
  gate silently covering content the human never saw; no artefact was deployed under the stale
  approval, since this build never deploys.
- **Evidence:** `plan.json` → `steps[M1-S02].runs[]`, `steps[M1-S02].amendments[1]`, `human_gates[]`
  (`step:M1-S02`); `artefacts/M1-S02/deploy-order.md` § 0.

## D-M1S02-03 — Design trade-off: `Integration_Failure__c` ships Private OWD with `modifyAllRecords` on `Tier2_Webhook_Admin` rather than a sharing rule (decision D12)

- **Date:** 2026-09-12
- **Step:** `M1-S02` (`access`), decision made at `M1-S01` and realised in this step's permission set
- **Agent:** `metadata-builder`
- **Kind:** design trade-off, with the skill/decision-tree branch it rests on.
- **What was recorded:** `Tier2_Webhook_Admin.permissionset-meta.xml` grants
  `Integration_Failure__c` all six object-permission flags true, including `modifyAllRecords`. Both
  checker runs against this step — run 1 (`envelopes/M1-S02/2026-09-12T10-08-07Z.json`) and the
  rebuild (`.../2026-09-12T10-28-30Z.json` and `.../2026-09-12T10-32-00Z.json`) — return the identical
  non-failing WARN: `"objectPermissions for Integration_Failure__c sets modifyAllRecords=true, which
  bypasses sharing for that object"`. The step's own acceptance-test description names this WARN in
  advance as expected and non-blocking.
- **Alternative rejected:** a criteria-based sharing rule granting the same admins visibility instead
  of the object-scoped bypass. Rejected per decision **D12** (`standards/decision-trees/sharing-
  selection.md`, Q1): "the criterion would be 'every row', which is a whole-object grant wearing a
  rule's clothes" — the tree's own guidance places "can user bypass sharing to do admin things?" on
  View/Modify All at object scope for a narrow admin permission set, which `Tier2_Webhook_Admin` is.
- **Grounded in:** `standards/decision-trees/sharing-selection.md` Q1; `traceability.md`'s `D12` entry
  (source `Q1`); `artefacts/M1-S02/deploy-order.md` § 4, `objectPermissions` row: "The checker's
  sharing-bypass WARN on this row is deliberate per D12."
- **Consequences:** every user assigned `Tier2_Webhook_Admin` — the D14 assignee set, wider than
  Q19's three admins — can read, edit and delete every `Integration_Failure__c` row regardless of
  ownership. This is the documented, intended shape, not an oversight; a human reading the WARN in a
  future checker run should not treat it as a new finding.
- **Evidence:** `envelopes/M1-S02/2026-09-12T10-08-07Z.json`, `.../2026-09-12T10-28-30Z.json`,
  `.../2026-09-12T10-32-00Z.json` → `extensions.checker_results[1]`; `artefacts/M1-S02/permission
  sets/Tier2_Webhook_Admin.permissionset-meta.xml`; `artefacts/M1-S02/deploy-order.md` § 4.

## D-M1S02-04 — Design trade-off: no `Case` `objectPermissions` row is added even though the set grants a `Case` field (assumption A14)

- **Date:** 2026-09-12
- **Step:** `M1-S02` (`access`)
- **Agent:** `metadata-builder`
- **Kind:** design trade-off, verified against the checker's own source logic rather than asserted.
- **What was recorded:** `Tier2_Webhook_Admin` carries a `fieldPermissions` entry for
  `Case.Tier2_Notified_At__c` (`readable`/`editable` true) but no `objectPermissions` row for `Case`
  at all. The step's own input names the reasoning verbatim:
  `objectPermissions_scope_note`: "No objectPermissions row is added for Case. Its users already hold
  Case object access from their profile, a CRUD row here would grant more than any answer asked for,
  and the checker's object-row rule only fires when a set that HAS a row for an object grants a field
  on it without allowRead=true — a fieldPermissions entry with no matching object row is legal and
  narrower. Assumption A14."
- **Alternative rejected:** adding a `Case` `objectPermissions` row with `allowRead=true` to
  "future-proof" the grant or to satisfy an assumed checker expectation. Rejected because it would
  grant more Case access than any clarification asked for — the users this set is assigned to
  (D14's wider list) already hold Case object access through their profile, and a set built for one
  narrow integration purpose should not carry a second, broader access grant nobody requested.
- **Grounded in:** `check_permission_set_architecture.py`'s own object-row rule, verified in both
  directions per the step's acceptance-test description: "the object-row rule is guarded by `if
  has_object_row and owner not in granted_objects`, so a `fieldPermissions` entry for a `Case` field
  with no `Case` object row cannot fire it" — confirmed on this exact artefact (exit 0, no ERROR on
  the missing `Case` row) across all three checker runs this step recorded.
- **Evidence:** `plan.json` → `steps[M1-S02].inputs.permission_set.value.
  objectPermissions_scope_note`; `traceability.md`'s `A14` entry; `artefacts/M1-S02/deploy-order.md`
  § 4, "No `objectPermissions` row for `Case`" row; `tests/M1-S02/results.json` (checker exit 0 on the
  rebuilt file, same shape).

## D-M1S02-05 — Design trade-off: the API key is entered in Setup after deploy, never in metadata — a standing deploy prerequisite owned by Support Engineering

- **Date:** 2026-09-12
- **Step:** `M1-S02` (`access`)
- **Agent:** `metadata-builder`
- **Kind:** design trade-off, directly required by the requirement's own text rather than a builder
  preference.
- **What was recorded:** none of the three files this step ships carries a literal API-key value. The
  `AuthHeader` `parameterValue` is the merge-field formula `{!$Credential.OnCall_Tool_EC.ApiKey}` —
  a reference to where the platform reads the secret at run time, not the secret itself.
  `artefacts/M1-S02/deploy-order.md` § 7 step 1 names the human action this defers to: "Enter the API
  key in Setup, against the `OnCallToolNamedPrincipal` principal on `OnCall_Tool_EC` … a parameter
  **named exactly `ApiKey`** holding the key … never in metadata, never in an export, and does not
  survive a sandbox refresh — so this step repeats in every org." No agent in this build loop performs
  it.
- **Alternative rejected:** any mechanism that would let the key ship with the metadata — a Custom
  Metadata Type protected field, a static resource, or a hardcoded value pending a later masking pass.
  Rejected outright by `requirement.md` L7–8's own words ("The on-call tool's API key must never be
  stored in code or in a custom setting"), and never proposed by any clarification; entering a secret
  against an External Credential principal in Setup is the mechanism the Metadata API itself makes
  available for this, per the cited skill.
- **Owner named:** Support Engineering. Every clarification naming a human owner for this
  integration's operational surface names the same team — Q19 ("the three Support Engineering
  admins"), Q20 ("Support Engineering resends"), Q21 ("Support Engineering lead" sets the SLA) — so
  the post-deploy Setup entry, like the resend and the backlog review, is recorded as Support
  Engineering's prerequisite, not an unowned manual step.
- **Grounded in:** `requirement.md` L7–8; `artefacts/M1-S02/deploy-order.md` §§ 6(b), 7 step 1;
  clarifications Q19–Q21.
- **Evidence:** `artefacts/M1-S02/externalCredentials/OnCall_Tool_EC.externalCredential-meta.xml`
  (the formula, no literal value); `artefacts/M1-S02/deploy-order.md` § 7.

## D-M1S02-06 — Skill gap (plan-hygiene): M1-S05's manual test still names the pre-amendment AuthHeader question as open (candidate PV-007 prose-only amendment)

- **Date:** 2026-09-12
- **Step:** `M1-S02` (`access`); the stale text lives in `M1-S05` (`docs`)
- **Agent:** surfaced by `metadata-builder`'s rebuild run (`2026-09-12T10-28-30Z`)
- **Kind:** skill gap, generalised to a cross-step plan-hygiene gap the same way `D-M1S01-01` and
  `D-M1S02-01` generalise it — a gap recorded without blocking any step.
- **What was recorded:** `M1-S05`'s manual acceptance test still reads "confirm the X-API-Key
  AuthHeader parameterValue formula against Salesforce Help before the External Credential is
  deployed" — the exact framing of an *open* question. The requester's amendment
  (`steps[M1-S02].amendments[1]`) and `mock-deploy` run 1 have partly overtaken that framing: the
  parameter name and the formula are now supplied and closed (assumption A5), and the org has
  confirmed the element is required. What remains open is narrower — the grammar parses on deploy and
  the header's run-time behaviour at UAT (`deploy-order.md` § 5 item 1) — but `M1-S05`'s text does not
  say so. This is the item the plan-approval note at `human_gates[] → name: "plan"` flagged in advance
  as **"PV-007 deploy-order prose lag to be fixed by prose-only amendment once building."**
- **Why this agent does not fix it:** per `agents/build-doc-keeper/AGENT.md` "What This Agent Does NOT
  Do" — it does not touch `plan.json` beyond the single status transition it owns for `M1-S02`, and
  `M1-S05`'s step text is not this step's to amend. `amend-step M1-S05` is legal only while that
  step's status is `pending`/`blocked` (it is currently `pending`, per `plan.json`), so the fix remains
  available to a human or to `M1-S05`'s own owning agent when that step is built.
- **Alternative rejected:** rewriting `M1-S05`'s prose under cover of this M1-S02 documentation pass,
  since the fix is small and the context is fresh. Rejected for the same reason `D-M1S01-01` rejected
  the analogous shortcut: a documentation agent editing another step's declared fields blurs who is
  accountable for that step's content, and `amend-step` exists precisely so the edit is attributable
  and legal-checked.
- **Grounded in:** `plan.json` → `human_gates[] → name: "plan"` notes ("PV-007 deploy-order prose lag
  to be fixed by prose-only amendment once building"); `envelopes/M1-S02/2026-09-12T10-28-30Z.json` →
  `process_observations`, category `ambiguous`, domain `plan-hygiene`; `plan.json` →
  `steps[M1-S05]` manual acceptance test text.
- **Open item:** `amend-step M1-S05` to narrow the manual test's wording to "the grammar parses on
  deploy (mock-deploy run 2) and the header's run-time behaviour is confirmed at UAT" — a prose-only
  change, not a scope change.
- **Evidence:** `plan.json` → `human_gates[]` ("plan" record); `steps[M1-S05]`;
  `envelopes/M1-S02/2026-09-12T10-28-30Z.json` → `process_observations[3]`.

## D-M1S04-01 — Round-1 P0: the planner wired a logger whose skill names two object prerequisites no step of this build ships; closed at the plan level, not the code level

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`)
- **Agent:** `apex-builder` (run `2026-09-12T10-44-00Z`, `run 1`); the resolution was applied by the
  dry-run operator's amendment (`plan.json` → `steps[M1-S04].amendments[0]`, `2026-09-12T10:51:56Z`)
  and rebuilt by `apex-builder` (run `2026-09-12T10-57-00Z`)
- **Kind:** skill gap surfaced as a P0 build finding, per `agents/build-doc-keeper/AGENT.md` Step 3
  table ("Skill gap — the gap the runner recorded when it set a step `blocked`", generalised the same
  way `D-M1S01-01` and `D-M1S02-01` generalise it: this step never reached `blocked` in `plan.json`
  because the amendment landed before a `failed`→`blocked` transition was recorded, but run 1's own
  envelope names the identical shape — a step input asked for a component the owning agent cannot
  ship and no earlier step provisions).
- **What was recorded:** step input `include_logger: true` wires every emitted class through
  `templates/apex/ApplicationLogger.cls` (`agents/apex-builder/AGENT.md` Inputs table). That template
  writes `Application_Log__c` rows and reads `Logger_Setting__mdt.getInstance('Default')`; its owning
  skill's own deploy-order table — `skills/apex/error-handling-framework/references/code-examples.md`
  § 9, rows 1–2 — names both as **compile** prerequisites of shipping `ApplicationLogger`, not merely
  runtime ones. Clarification `Q16` had already answered "We have no existing Apex log object in the
  org," and `M1-S01` (already `documented` at the time) ships neither object. `apex-builder` emits
  `.cls` files only and cannot ship the object model or the CMDT itself, so round 1's package would
  not have compiled in the target org — finding `AB-01`, severity `P0`
  (`envelopes/M1-S04/2026-09-12T10-44-00Z.json` → `findings[0]`).
- **The flywheel this names:** a step's `skills[]`/`templates[]` entry can carry hard deploy
  prerequisites — real object-model components — that the plan never provisioned, and neither
  `apex-builder`'s own checkers nor the step's declared acceptance tests catch it before the P0 fires,
  because none of them reads the cited skill's own deploy-order table. This is the same shape
  `D-M1S01-01` and `D-M1S02-01` name for a different skill and a different gap; recorded here as a
  third instance rather than assumed to be this step's alone.
- **What the requester decided (option (b) of the two `apex-builder` named):** `include_logger:
  false`. No `ApplicationLogger` anywhere in the package; the visible log for this feature **is**
  `Integration_Failure__c` (`Q16`–`Q18`), and every other log call is `System.debug(LoggingLevel.…)`.
  `ApplicationLogger.cls` and its `-meta.xml` were deleted from the step's rebuilt artefacts; the
  amendment removes both from `templates[]`.
- **Alternative rejected:** option (a) — add an `object-model` step owned by `metadata-builder`
  shipping `templates/apex/custom_objects/Application_Log__c` (plus its eight fields) and
  `templates/apex/cmdt/Logger_Setting__mdt` with a `Default` record, which `M1-S03` and `M1-S04` would
  then both depend on. Rejected by the requester in favour of the narrower fix: the feature's own
  design already has a durable sink (`Integration_Failure__c`) for the failure paths that matter, and
  a healthy run needs no durable record at all, so the dependency was removed rather than satisfied.
  Recorded as a live alternative, not a foreclosed one — `envelopes/M1-S04/2026-09-12T10-44-00Z.json`
  → `findings[0].recommendation` states both options without choosing between them; the choice was
  made at the plan, not by either `apex-builder` run.
- **Grounded in:** `skills/apex/error-handling-framework/references/code-examples.md` § 9 (Deploy
  order table, rows 1–2: `Application_Log__c` and `Logger_Setting__mdt`); clarification `Q16`'s answer
  (`requirement.md`-adjacent, `plan.json` → `clarifications[]`); `agents/apex-builder/AGENT.md` Inputs
  table (`include_logger` wiring) and Step 6 (template provenance).
- **Consequences:** round 1's `ApplicationLogger.cls`/`-meta.xml` pair, once shipped as an undeclared
  artefact, is now absent from the package entirely; the class inventory shrank from five to four.
  The tension `D-M1S04-04` below also closed itself as a side effect: `execute()` no longer has a
  logging line competing with decision `D11`'s "does nothing else."
- **Evidence:** `envelopes/M1-S04/2026-09-12T10-44-00Z.json` → `findings[0]`,
  `process_observations[2]` (severity `high`, domain `deploy-order`); `plan.json` →
  `steps[M1-S04].amendments[0]`; `envelopes/M1-S04/2026-09-12T10-57-00Z.json` → `findings[0]` (`AB-R1`,
  `INFO`, "Round-1 P0 closed by the amendment, not by this step"); `artefacts/M1-S04/deploy-order.md`
  § 0.

## D-M1S04-02 — Stale sibling: `inputs.recipients` and `inputs.alert_recipients` now say different things in the amended plan; a prose-only amendment candidate, not resolved by this pass

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`)
- **Agent:** surfaced by `apex-builder`'s rebuild run (`2026-09-12T10-57-00Z`) and reconfirmed by
  `build-step-runner` (`2026-09-12T10-58-44Z`) and `step-tester` (`2026-09-12T11-06-58Z`)
- **Kind:** skill gap (plan-hygiene), generalised the same way `D-M1S02-06` generalises it — a stale
  field left behind by a wholesale `amend-step` replacement, recorded without blocking the step.
- **What was recorded:** `steps[M1-S04].amendments[0]` replaced `inputs` wholesale, but the resulting
  `inputs{}` carries **both** keys: the pre-amendment `recipients` ("Support Engineering (Q24). The
  distribution list address is taken from the deploy-order note rather than hardcoded per
  environment.") and the dated, specific `alert_recipients` ("alert the users who hold an active
  `PermissionSetAssignment` to `Tier2_Webhook_Admin` … If the query returns no one, log to
  `System.debug` and write an `Integration_Failure__c` row of Severity Warning"). The rebuild
  implemented `alert_recipients`; `recipients` was never removed and now reads as a second, disagreeing
  answer to the same question.
- **Alternative rejected:** treating the two keys as reconciled because the newer one is dated and the
  code matches it. Rejected — a later reader of `plan.json` alone, without the rebuild's envelope
  trail, cannot tell which key is authoritative from the file itself, and the plan-approval note at
  `human_gates[] → name: "plan"` already named exactly this class of drift (`PV-007`) as something to
  fix by prose-only amendment once building, not to leave standing.
- **Why this agent does not fix it:** per `agents/build-doc-keeper/AGENT.md` "What This Agent Does NOT
  Do" — it does not touch `plan.json` beyond the single status transition it owns for `M1-S04`, and a
  prose-only amendment to `inputs.recipients` is `build-planner`'s or a human's call via `amend-step`,
  legal now only because the step's status has left `pending` and re-entering it requires the
  `built`/`tested`→`failed`→`pending` recovery path, not a doc-keeper edit.
- **Grounded in:** `plan.json` → `steps[M1-S04].inputs.recipients` vs `.alert_recipients`;
  `envelopes/M1-S04/2026-09-12T10-57-00Z.json` → `findings[6]` (`AB-R7`, `P2`); `artefacts/M1-S04/
  deploy-order.md` § 0 ("One stale sibling in `inputs{}`").
- **Open item:** `amend-step M1-S04` (once legally available again) to drop or rewrite `inputs.
  recipients` so it names `alert_recipients` as the superseding answer, or removes the older key
  outright.
- **Evidence:** `envelopes/M1-S04/2026-09-12T10-57-00Z.json` → `findings[6]`,
  `process_observations` (`ambiguous`, domain `plan-shape`); `envelopes/M1-S04/2026-09-12T10-58-44Z.json`
  → `process_observations` (`concerning`, `medium`, domain `plan-shape`); `envelopes/M1-S04/
  2026-09-12T11-06-58Z.json` → `process_observations` (`ambiguous`, `medium`, domain `orchestration`).

## D-M1S04-03 — Two access gaps confirmed nowhere in the build, deferred to the M1 gate: `PermissionSetAssignment` read for the alert roster, and `Case` visibility for the dead-channel count

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`)
- **Agent:** `apex-builder` (rebuild run `2026-09-12T10-57-00Z`); the `Case` half carries forward
  unchanged from run 1 (`2026-09-12T10-44-00Z`)
- **Kind:** design trade-off recorded as an open access question, per `agents/build-doc-keeper/
  AGENT.md` Step 3 ("Design trade-off — the trade-off the owning agent named, with the skill it cited
  for it").
- **What was recorded, gap 1 (roster resolution):** `resolveRecipients()` queries
  `PermissionSetAssignment` in API 67.0 user mode. `Tier2_Webhook_Admin` (`M1-S02`) grants
  `Integration_Failure__c` object/field permissions and the `Case.Tier2_Notified_At__c` field
  permission; it grants nothing on `PermissionSetAssignment`. No answer, decision or step input names
  that permission for the scheduling user. If the scheduling user cannot read it, every run degrades
  to the recipient-gap path (`D-M1S04-04` below) and alerts nobody.
- **What was recorded, gap 2 (Case visibility):** `Tier2_Webhook_Admin` grants `viewAllRecords` on
  `Integration_Failure__c` (decision `D12`) but carries no `objectPermissions` row for `Case` at all
  (assumption `A14`, decision `D-M1S02-04`). `successesLastDay` therefore returns only Cases the
  scheduling user can see under the org's own Case sharing model; if that user cannot see other
  people's Cases, the query reads 0 and the job raises a false dead-channel alert. No answer names a
  Case OWD.
- **Alternative rejected (both gaps):** guessing a permission grant or a Case OWD to close the gap
  outright. Rejected because no clarification, decision or step input names either value, and
  `D-M1S02-04` already rejected widening `Tier2_Webhook_Admin`'s `Case` access beyond what was asked
  for — inventing it here to make this step self-sufficient would reopen that same rejected trade-off
  from the other direction.
- **Grounded in:** `artefacts/M1-S02/permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml`; decision
  `D12` (`traceability.md`); decision `D-M1S02-04` (assumption `A14`, `Case` scope note);
  `artefacts/M1-S04/deploy-order.md` § 3 rows 3 and 5, § 4 items 1 and 3.
- **Open item:** both are M1-gate confirmation items — the scheduling user's `PermissionSetAssignment`
  read access, and the scheduling user's `Case` visibility under the org's sharing model. Neither is a
  code change; both are org-configuration facts a human must state before the first scheduled run.
- **Evidence:** `envelopes/M1-S04/2026-09-12T10-57-00Z.json` → `findings[1]` (`AB-R2`),
  `findings[4]` (`AB-R5`); `envelopes/M1-S04/2026-09-12T10-44-00Z.json` → `findings[3]` (`AB-04`);
  `tests/M1-S04/results.json` (step-tester `concerning`, `medium`, domain `apex-security`,
  "PermissionSetAssignment read access … is granted by nothing this build ships … Case record
  visibility … depends on an unstated OWD").

## D-M1S04-04 — Accepted: the recipient-gap row counts toward the job's own alert thresholds, and there is no duplicate-alert suppression across up to 24 hourly repeats

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`)
- **Agent:** `apex-builder` (rebuild run `2026-09-12T10-57-00Z` for the gap-row loop, both runs for the
  suppression question)
- **Kind:** design trade-off — two related ambiguities recorded and accepted rather than filled or
  built around.
- **What was recorded, the gap-row loop:** `recordRecipientGap()` writes an `Integration_Failure__c`
  row of Severity `Warning` when the roster resolves empty. The threshold queries count rows with **no
  Severity filter** — the step input defines rule 1 as "`Integration_Failure__c` rows created in the
  last hour exceed three" with no carve-out — so an org with no active `Tier2_Webhook_Admin` assignee
  accumulates one self-inflicted Warning row per hour, and after four hours rule 1 fires on the job's
  own output. It still cannot alert anyone; that is the condition itself.
- **What was recorded, no suppression:** `Q24` asked for the alert and said nothing about repetition,
  and no answer names an acknowledgement or de-duplication mechanism. While the channel stays dark,
  the job emails the roster every hour for up to 24 hours — at most 24 sends × roster size against the
  org's 5,000-external-email/day cap, which counts recipients, not calls.
- **Alternative rejected:** adding a `Severity` filter to the threshold query, or building a
  high-water-mark suppression field, to close either gap unasked. Rejected in both cases for the same
  reason — `Q24` names the thresholds and the recipients and nothing else; a filter or a suppression
  mechanism is a threshold or scope change to the plan, not a code fix available inside this step, and
  a suppression field would need configuration metadata no step of this build ships.
- **Grounded in:** step input `thresholds` (`plan.json` → `steps[M1-S04].inputs.thresholds`, verbatim
  "rows created in the last hour exceed three," no Severity qualifier); clarification `Q24`'s answer
  (repetition and acknowledgement both unaddressed).
- **Consequences:** accepted as designed, at the hourly cadence `D11` already sets. A human reading a
  run of self-inflicted Warning rows in the list view, or four-plus alert emails in a day, should read
  this entry before treating either as a defect.
- **Evidence:** `envelopes/M1-S04/2026-09-12T10-57-00Z.json` → `findings[2]` (`AB-R3`, `P2`);
  `envelopes/M1-S04/2026-09-12T10-44-00Z.json` → `findings[4]` (`AB-05`, `INFO`); `artefacts/M1-S04/
  deploy-order.md` § 4 items 5–6.

## D-M1S04-05 — UNVERIFIED, plan-bound: `WITH USER_MODE` is not written on the three aggregate `COUNT()` queries

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`)
- **Agent:** `apex-builder` (rebuild run `2026-09-12T10-57-00Z`, per requester input
  `aggregate_user_mode_note`)
- **Kind:** skill gap surfaced as a plan-bound UNVERIFIED, per `agents/build-doc-keeper/AGENT.md` Step
  3 ("Skill gap … generalised" the way `D-M1S01-01` generalises it — a real gap in the cited skills'
  coverage, recorded rather than guessed past).
- **What was recorded:** whether the `WITH USER_MODE` clause is legal syntax on an aggregate `COUNT()`
  SOQL query is stated in no skill this step cites, including `skills/apex/soql-security`. Step input
  `aggregate_user_mode_note` (dated 2026-09-12) instructs: omit the clause and rely on API 67.0's
  default user mode instead, and say so in `deploy-order.md`. The three `COUNT()` queries in
  `Tier2ChannelHealthQueueable.evaluate()` therefore carry no `WITH` clause at all; a `// reason:`
  comment in the method names the UNVERIFIED status inline. `WITH SECURITY_ENFORCED` does not compile
  at API 67.0 (`agents/_shared/AGENT_CONTRACT.md` § *Apex security idiom by API version*) and appears
  nowhere in the package.
- **Alternative rejected:** guessing that the clause is legal and writing it anyway, on the theory that
  an illegal clause would simply fail to deploy and surface the answer for free. Rejected because a
  design-only build has no deploy step to surface that failure, so an unverified guess would ship
  silently as fact rather than as a flagged question.
- **Grounded in:** `agents/_shared/AGENT_CONTRACT.md` § *Apex security idiom by API version*, the
  67.0+ row (default user mode, `WITH SECURITY_ENFORCED` removed); `skills/apex/soql-security/
  references/gotchas.md` (no statement either way on `WITH USER_MODE` with an aggregate function);
  step input `aggregate_user_mode_note`.
- **Open item:** confirm against a scratch org or the Apex Reference Guide's SOQL grammar before the
  next release that touches this class; until then the omission is documented as deliberate rather
  than an oversight.
- **Evidence:** `artefacts/M1-S04/classes/Tier2ChannelHealthQueueable.cls` (the `// reason:` comment in
  `evaluate()`); `artefacts/M1-S04/deploy-order.md` § 4 item 2; `envelopes/M1-S04/
  2026-09-12T10-57-00Z.json` → `process_observations` (`ambiguous`, `low`, domain `fls`).

## D-M1S04-06 — Undeclared artefacts persist after the rebuild: `TestDataFactory.cls`/`-meta.xml` and `deploy-order.md` still ship outside `outputs[]`; the structural fix is a plan change this pass cannot make

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`)
- **Agent:** `apex-builder` (both runs); reconfirmed unchanged by `build-step-runner`
  (`2026-09-12T10-58-44Z`)
- **Kind:** skill gap (plan-shape), generalised the same way `D-M1S01-01` generalises it — a gap
  between what a step's `templates[]` requires it to ship and what its `outputs[]` declares, carried
  through the amendment rather than closed by it.
- **What was recorded:** `agents/apex-builder/AGENT.md` Step 6 forces a verbatim copy of every
  `templates/apex/**` class an emitted class or test references into the step's own artefacts, plus
  its `-meta.xml`. `steps[M1-S04].templates[]` still cites `templates/apex/tests/TestDataFactory.cls`;
  `outputs[]` still declares only the six original Schedulable/Queueable/Test paths. The amendment
  (`amendments[0]`, fields `inputs` and `templates`) removed `ApplicationLogger` from `templates[]` but
  left this gap exactly as round 1 reported it — three undeclared artefacts remain
  (`TestDataFactory.cls`, its `-meta.xml`, `deploy-order.md`), down from five. `check-outputs` passes
  regardless, because it only confirms the six declared paths.
- **The wider pattern:** `M1-S03` cites the same template and declares no output for it either, so both
  Apex steps in this plan carry the identical undeclared-copy problem, and the plan has no dedicated
  Apex-foundations step to hold a template dependency two steps share.
  `standards/build-orchestration.md` § 4's Apex row note names the structural remedy directly.
- **Alternative rejected:** having this documentation pass add the missing paths to `outputs[]`
  itself. Rejected — `amend-step` is the only legal writer of `outputs[]`, is refused once a step has
  left `pending` without going through the `failed`→`pending` recovery path, and is not this agent's
  to invoke per its "What This Agent Does NOT Do" (it touches `plan.json` only for the single status
  transition it owns).
- **Grounded in:** `agents/apex-builder/AGENT.md` Step 6 (template provenance);
  `standards/build-orchestration.md` § 4, Apex row note (dedicated Apex-foundations step when more than
  one Apex step shares a template dependency); `plan.json` → `steps[M1-S04].templates[]` vs
  `.outputs[]`, and the identical shape at `steps[M1-S03]`.
- **Open item:** a re-plan adds either a shared Apex-foundations step for `M1-S03`/`M1-S04`, or amends
  both steps' `outputs[]` to declare the copies they already ship.
- **Evidence:** `envelopes/M1-S04/2026-09-12T10-44-00Z.json` → `findings[1]` (`AB-02`, `P1`);
  `envelopes/M1-S04/2026-09-12T10-58-44Z.json` → `process_observations` (`concerning`, `low`, domain
  `plan-shape`); `artefacts/M1-S04/deploy-order.md` §§ 1–2.

## D-M1S04-07 — Skill gap (plan-hygiene): `M1-S05`'s manifest acceptance test still says "the three `ApexClass` members" from this step; four now ship

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`); the stale text lives in `M1-S05` (`docs`)
- **Agent:** surfaced by `step-tester` (`2026-09-12T11-06-58Z`)
- **Kind:** skill gap, generalised the same way `D-M1S02-06` generalises it — a cross-step plan-hygiene
  gap recorded without blocking either step.
- **What was recorded:** `steps[M1-S04].acceptance_tests[type=manifest].description` reads "the three
  `ApexClass` members here are carried by the build-level manifest step M1-S05" — written when the
  step's outputs were the Schedulable, Queueable and Test classes only. The template-provenance rule
  (`D-M1S04-06` above) adds a fourth, `TestDataFactory`, which was already true at round 1 (five
  classes including `ApplicationLogger`) and remains true after the rebuild (four classes). The
  manifest classification itself is unaffected — still `skipped-not-applicable`, still naming `M1-S05`
  — but `M1-S05`'s own test run should expect **four** `ApexClass` members from this step, not three,
  or it will under-count and mis-flag genuine drift as agreement.
- **Why this agent does not fix it:** per `agents/build-doc-keeper/AGENT.md` "What This Agent Does NOT
  Do" — it does not touch `plan.json` beyond the single status transition it owns for `M1-S04`, and
  `M1-S04`'s own acceptance-test text, like `M1-S05`'s, is not this pass's to amend; `amend-step` is
  legal only while the target step's status is `pending`/`blocked` (`M1-S04` is `tested`, `M1-S05` is
  `pending`), so the fix is available to a human or to `M1-S05`'s own owning agent when that step
  builds.
- **Grounded in:** `plan.json` → `steps[M1-S04].acceptance_tests[type=manifest].description` (the
  stale "three" count); `artefacts/M1-S04/deploy-order.md` § 5 ("Members M1-S05 must carry for this
  step, **four** of them").
- **Alternative rejected:** rewriting the description under cover of this documentation pass, since
  the fix is small and the context is fresh. Rejected for the same reason `D-M1S01-01` and
  `D-M1S02-06` reject the analogous shortcut: a documentation agent editing another step's declared
  fields blurs who is accountable for that step's content.
- **Open item:** `amend-step M1-S04` (prose-only, once legally available) to change "three" to "four,"
  or leave the correction to `M1-S05`'s own build pass, which will discover the mismatch directly
  against the artefacts on disk regardless.
- **Evidence:** `tests/M1-S04/results.json` → `skipped_manual` is unaffected, but
  `envelopes/M1-S04/2026-09-12T11-06-58Z.json` → `process_observations` (`ambiguous`, `low`, domain
  `orchestration`, "the description predates the TestDataFactory template-provenance addition");
  `artefacts/M1-S04/deploy-order.md` § 5.

## D-M1S03-01 — Round-1 refusal on template-closure, and remedy B: the flywheel record

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`)
- **Agent:** `apex-builder` (run 1, `2026-09-12T10:57:25Z`, refusal); the remedy was chosen by the
  requester and the dry-run operator (Fable) at `2026-09-12T11:03:46Z`
  (`plan.json` → `steps[M1-S03].amendments[1]`); `apex-builder` rebuilt to it at run 2
  (`2026-09-12T11:23:31Z`)
- **Kind:** skill gap surfaced as a `REFUSAL_INPUT_AMBIGUOUS` before any file was written, per
  `agents/build-doc-keeper/AGENT.md` Step 3 table, generalised the way `D-M1S01-01`/`D-M1S02-01`
  generalise it into a build-wide pattern — this is the third and largest instance of the same shape:
  a step's `templates[]`/`skills[]` entry carries a transitive closure the plan never provisioned.
- **What was recorded:** the step's `templates[]` mandated five canonical templates. Three fail
  `agents/apex-builder/AGENT.md` Step 6's provenance test transitively: `templates/apex/HttpClient.cls`
  (lines 67, 96) and `templates/apex/BaseService.cls` (lines 45, 50) call `ApplicationLogger`, which
  needs `Application_Log__c` + `Logger_Setting__mdt` that no step ships (`Q16`: "We have no existing
  Apex log object in the org"); `templates/apex/TriggerHandler.cls` (line 38) calls
  `TriggerControl.isActive(...)`, a template this step's `templates[]` does not even list, whose
  `getCache()` queries `Trigger_Setting__mdt`, also unshipped. `inputs.callout_endpoint` ("composed
  through `templates/apex/HttpClient.cls`") and `inputs.logging_decision_2026_09_12` ("Do not
  reference `ApplicationLogger`") could not both be satisfied. Zero files were written; `check-outputs`
  reported 20 missing. This is the same closure problem `D-M1S04-01` records for `M1-S04`'s
  `ApplicationLogger` dependency, discovered independently by the other Apex step in this plan and
  before `M1-S04`'s own P0 had been generalised into a documented pattern — `apex-builder`'s own
  refusal message on this step cites the identical two unshipped types (`Application_Log__c`,
  `Logger_Setting__mdt`) plus a third this step alone needs (`Trigger_Setting__mdt`).
- **The flywheel this closes and the one it opens:** the *build* is closed — remedy B let run 2
  through and run 3 fixed the two faults the org then found (`D-M1S03-02`, `D-M1S03-03`). The
  *skill/template* gap is not closed by this run: three canonical templates
  (`TriggerHandler.cls`/`TriggerControl.cls`, `BaseService.cls`, `HttpClient.cls`,
  `ApplicationLogger.cls`) each has a hard object-model/CMDT prerequisite that
  `agents/apex-builder/AGENT.md` Step 6 does not surface until the step is already refused, and
  `standards/build-orchestration.md` § 4's Apex row note — a dedicated Apex-foundations step when more
  than one Apex step shares a template dependency — is the structural fix neither this run nor
  `M1-S04`'s made. `skills/apex/test-class-standards` and `skills/apex/test-data-factory-patterns`
  (`agents/apex-builder/AGENT.md` Mandatory Reads items 34–35) are the two skills that ground why the
  two templates that *did* survive remedy B — `TestDataFactory.cls`, `MockHttpResponseGenerator.cls` —
  are mandated regardless of the closure problem: both skills require the canonical factory and mock
  generator verbatim rather than a freestyled equivalent, and both templates are self-contained (no
  further `templates/apex` reference, no custom object or CMDT), which is the literal reason they were
  the two remedy B did not need to touch.
- **What the requester and operator decided (remedy B, of the two named in the refusal):**
  `templates/apex/TriggerHandler.cls`, `templates/apex/BaseService.cls` and `templates/apex/HttpClient.cls`
  dropped from `templates[]`; build-local equivalents authorised — a plain `after update` trigger
  delegating to a static handler with a per-transaction recursion guard (no `TriggerControl` kill
  switch — see `D-M1S03-04`), an `HttpRequest` built directly against `callout:OnCall_Tool` per
  `apex/callouts-and-http-integrations` (no `HttpClient` wrapper), and logging via
  `Integration_Failure__c` rows plus `System.debug` only. Decision **D4** ("the webhook body is
  JSON... through `templates/apex/HttpClient.cls`", `PLAN.md` line 84) is revisited to that extent —
  `HttpClient.cls` no longer composes the endpoint in this build. `TestDataFactory` and
  `MockHttpResponseGenerator` still ship verbatim with their meta XML.
- **Alternative rejected:** remedy A — a dedicated Apex-foundations `metadata-builder` step shipping
  `Application_Log__c`, `Logger_Setting__mdt` and `Trigger_Setting__mdt` (plus their fields/records),
  with `M1-S03` then `depends_on` it and shipping all five templates as designed. Rejected by the
  requester because it reopens `Q16` (whose answer was about where failures are visible to Support
  Engineering, not about whether a framework log table may exist) and adds a sixth functional step to
  a `feature`-tier plan whose ceiling is five (`standards/build-orchestration.md` § 3.1).
- **Grounded in:** `envelopes/M1-S03/2026-09-12T10-57-25Z.json` → `refusal`, `process_observations[0]`
  (`healthy`, the two surviving templates' self-containment) and `[2]`–`[3]` (`concerning`, the
  closure gap); `plan.json` → `steps[M1-S03].amendments[1]`; `artefacts/M1-S03/deploy-order.md` § 4;
  `agents/apex-builder/AGENT.md` Mandatory Reads items 34–35 and Step 6; `standards/build-orchestration.md`
  § 4 Apex row note.
- **Consequences:** see `D-M1S03-04` for what the `TriggerHandler`/`TriggerControl` drop costs
  specifically; the `BaseService`/`HttpClient` drop cost nothing this feature used (the retry loop
  `HttpClient` would have supplied was already off by design — `retryOnTransient(false)`, since its
  back-off is a busy-wait against Apex CPU time).
- **Evidence:** `envelopes/M1-S03/2026-09-12T10-57-25Z.json` (full refusal); `plan.json` →
  `steps[M1-S03].runs[0..1]`, `.amendments[1]`; `artefacts/M1-S03/deploy-order.md` §§ 2, 4.

## D-M1S03-02 — S2-F-04: `URL.getSalesforceBaseUrl()` removed after v58.0; the attestation-vs-version lesson

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`)
- **Agent:** `apex-builder` (run 2 shipped the fault, `2026-09-12T11:23:31Z`; run 3 fixed it,
  `2026-09-12T11:40:10Z`); the org's own dry-run caught it (`mock-deploy` run
  `2026-09-12T11:37:21Z`, `reports/MOCK-DEPLOY-M1.md` "Run 3")
- **Kind:** skill gap surfaced as a build-time compile failure, per `agents/build-doc-keeper/AGENT.md`
  Step 3 table, generalised the same way `D-M1S01-01` generalises it — a real defect in three cited
  skills' worked examples, recorded rather than silently patched around.
- **What was recorded:** run 2 emitted `URL.getSalesforceBaseUrl().toExternalForm()` in
  `Tier2EscalationService` and `Tier2WebhookQueueable` to build the link back to the Case. The org's
  `sf project deploy start --dry-run` rejected both classes: `Method was removed after version 58.0:
  getSalesforceBaseUrl` (`reports/MOCK-DEPLOY-M1.md` "Run 3", verbatim). These classes are pinned to
  API **67.0**, nine versions past the removal. **The identifier was attested — three skills in this
  repo spell `getSalesforceBaseUrl`, which is exactly why `agents/apex-builder/AGENT.md`'s Gate C
  check 2 (identifier provenance, a corpus grep) returned a hit and let it through — but the *idiom*
  was recalled from memory, and none of the three skills carries the version gate.** A repo grep
  proves a name exists somewhere in the corpus; it does not prove the name is legal at the `apiVersion`
  the step stamps into its own meta XML. Nothing offline caught the difference — not the three
  declared checkers, not the XML parse, not the tester's own brace/paren/bracket/string-balance scan.
  Only the org did.
- **What was fixed:** both call sites now use `URL.getOrgDomainUrl().toExternalForm()`, the form the
  Apex Developer Guide's own examples use at API 67.0 (cited in `artefacts/M1-S03/deploy-order.md` § 0
  as `apexdev` L32630/L37043), supplied by the operator with the failure. Every other file in the
  package is byte-identical to run 2.
- **Alternative rejected:** trusting the corpus-grep attestation as sufficient and shipping the
  identifier unchanged a second time. Rejected — it is exactly what run 2 did and exactly what the
  org rejected; a second unchanged submission would fail identically.
- **Grounded in:** `reports/MOCK-DEPLOY-M1.md` "Run 3" (org error text, verbatim); the Apex Developer
  Guide (`apexdev`, per `knowledge/sources.yaml`) L32630/L37043 for `URL.getOrgDomainUrl()`;
  `artefacts/M1-S03/deploy-order.md` § 0 "Root 1"; `envelopes/M1-S03/2026-09-12T11-40-10Z.json` →
  `findings[0]` (`S3-F-06`, P1, "An attested identifier shipped and did not compile: attestation is
  not a version gate") and `process_observations` (`concerning`, `high`, domain `tooling-gap`: "Every
  offline gate this step has ... passed on a package the org rejected"; `concerning`, `medium`, domain
  `agent-contract`: "The identifier-provenance check ... asks whether the corpus spells a name and
  cannot ask whether the name is legal at the apiVersion").
- **Open item, and it is not this step's to close:** `reports/MOCK-DEPLOY-M1.md` "Run 3" and this
  step's own `deploy-order.md` § 0 both name the fix as a **skill defect**, not a build defect —
  three unnamed skills in this repo still carry `URL.getSalesforceBaseUrl()` as a live example at API
  67.0-and-later without the version gate. `agents/apex-builder/AGENT.md` Gate C's own two-check
  design (symbol grounding, then identifier provenance) needs a third question — *is this identifier
  legal at the emitted `apiVersion`* — that neither check currently asks, and the operator has logged
  it against the corpus rather than patched it here.
- **Evidence:** `reports/MOCK-DEPLOY-M1.md` "Run 3"; `artefacts/M1-S03/deploy-order.md` § 0 "Root 1"
  and § 9 (symbol-grounding note, "one attested name shipped anyway and did not compile");
  `envelopes/M1-S03/2026-09-12T11-40-10Z.json` → `findings[0]`; `tests/M1-S03/results.json` →
  `detail.run3_fix_verification.s2_f04_getSalesforceBaseUrl_removed` (mechanical grep confirming
  `getSalesforceBaseUrl` is absent from every `.cls` file under this step and
  `URL.getOrgDomainUrl().toExternalForm()` is present at `Tier2EscalationService.cls:55` and
  `Tier2WebhookQueueable.cls:212`).

## D-M1S03-03 — S2-F-05: a `LongTextArea` field cannot be filtered in SOQL; the resend test's fixture selection was wrong, not its intent

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`)
- **Agent:** `apex-builder` (run 2 shipped the fault; run 3 fixed it, `2026-09-12T11:40:10Z`); caught
  by the same `mock-deploy` run as `D-M1S03-02`
- **Kind:** skill gap surfaced as a build-time compile failure, generalised the same way
  `D-M1S03-02` generalises it — a platform constraint neither cited skill states, caught only by the
  org.
- **What was recorded:** `IntegrationFailureResendTest` selected its two fixture rows with
  `WHERE Request_Payload__c != NULL` and `WHERE Request_Payload__c = NULL`. `M1-S01` declares
  `Integration_Failure__c.Request_Payload__c` `<type>LongTextArea</type>`, and the org rejected both
  filters: `field 'Request_Payload__c' can not be filtered in a query call`
  (`reports/MOCK-DEPLOY-M1.md` "Run 3", verbatim) — a long or rich text area cannot be filtered,
  grouped or sorted in SOQL, a constraint neither `apex/test-class-standards` nor
  `admin/object-creation-and-design` (the two skills this step and `M1-S01` respectively cite) states
  anywhere in their reference material.
- **What was fixed:** one helper, `rowsWithACase()`, selects every seeded row that has a Case
  (`WHERE Case__c != NULL ORDER BY Attempt_Count__c DESC` — both filterable, both real fields) and
  `rowWithPayload()` / `rowWithoutPayload()` pick in memory on the **selected** value rather than
  filtering on it. The no-payload test now asserts `Request_Payload__c` is null on the row it picked,
  so the test still proves which fixture it got rather than trusting a filter the platform will not
  run.
- **Alternative rejected:** none — this is a hard platform constraint (the field type makes the
  filter illegal, not merely inadvisable), so there is no alternative query shape that keeps the
  filter and also deploys.
- **Grounded in:** `reports/MOCK-DEPLOY-M1.md` "Run 3" (org error text, verbatim);
  `artefacts/M1-S01/objects/Integration_Failure__c/fields/Request_Payload__c.field-meta.xml`
  (`<type>LongTextArea</type>`); `artefacts/M1-S03/deploy-order.md` § 0 "Root 2".
- **Open item, and it is not this step's to close:** `reports/MOCK-DEPLOY-M1.md`'s own remedy line
  says "`apex/test-class-standards` and `admin/object-creation-and-design` gain the rule" — a checker
  rule and a skill gotcha for "no `WHERE`/`ORDER BY`/`GROUP BY` on a `LongTextArea` field," so the
  next test author does not rediscover this at the org a second time.
- **Evidence:** `reports/MOCK-DEPLOY-M1.md` "Run 3"; `artefacts/M1-S03/deploy-order.md` § 0 "Root 2";
  `tests/M1-S03/results.json` → `detail.run3_fix_verification.s2_f05_longtextarea_filter_removed`
  (mechanical grep confirming no `WHERE` clause on `Request_Payload__c` remains in
  `IntegrationFailureResendTest.cls`, and that `rowsWithACase()` / `rowWithPayload()` /
  `rowWithoutPayload()` are present at lines 73, 82 and 92); `envelopes/M1-S03/2026-09-12T11-40-10Z.json`
  → `findings[1]` (`S3-F-07`, P2).

## D-M1S03-04 — Accepted, P1: remedy B leaves the org with no trigger kill switch and no data-load bypass — an M1-gate item

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`)
- **Agent:** `apex-builder` (run 2, `2026-09-12T11:23:31Z`, finding `S3-F-01`, carried unchanged
  through run 3)
- **Kind:** design trade-off, the direct cost of `D-M1S03-01`'s remedy B, recorded as a standing
  operational risk rather than closed.
- **What was recorded:** `templates/apex/TriggerHandler.cls` (→ `TriggerControl` →
  `Trigger_Setting__mdt`) is what lets an admin switch a handler off from Setup, without a deployment,
  and what honours the `TriggerControl_BypassAll` Custom Permission during a data load. Remedy B
  replaced it with a plain `after update` trigger delegating to a static handler entry point, with a
  per-transaction `Set<Id>` recursion guard (`skills/apex/recursive-trigger-prevention/references/examples.md`).
  Neither `TriggerControl` nor `Trigger_Setting__mdt` exists anywhere in this build. Consequences, per
  the step's own `deploy-order.md` § 4: (1) a data load that reassigns Case ownership in bulk into
  `Tier_2_Engineering` will escalate every affected Case — there is no bypass; (2) turning the feature
  off is a deployment (`CaseTrigger.trigger-meta.xml` with `<status>Inactive</status>`), not a Setup
  checkbox; (3) the recursion guard is not a substitute — it stops one handler re-entering itself
  inside one transaction, and does nothing about a bulk load, which is many transactions each doing
  exactly what it was asked to do.
- **Alternative rejected:** the Apex-foundations step (remedy A) that would have shipped
  `Trigger_Setting__mdt` and let `TriggerHandler`/`TriggerControl` be used as intended — see
  `D-M1S03-01`'s "Alternative rejected." Also rejected: silently absorbing the gap by asserting the
  recursion guard is "good enough," which `tests/M1-S03/results.json` itself declines to do
  (`process_observations`, `concerning`, `low`, domain `automation-governance`).
- **Grounded in:** `artefacts/M1-S03/deploy-order.md` § 4 "The missing kill switch — read this before
  go-live"; `envelopes/M1-S03/2026-09-12T11-23-31Z.json` → `findings[0]` (`S3-F-01`, P1);
  `envelopes/M1-S03/2026-09-12T11-40-10Z.json` → `findings[2]` (`S3-F-01`, "still open").
- **Consequences:** a bulk Case-ownership reassignment into `Tier_2_Engineering` — a data load, a
  mass-reassignment tool, or a bulk update — will fire this automation for every record with no way
  to bypass it short of a deployment. This is an **M1-gate confirmation item**: a human should accept
  this risk explicitly, or request the Apex-foundations step, before the milestone is accepted.
- **Evidence:** `envelopes/M1-S03/2026-09-12T11-23-31Z.json` → `findings[0]`;
  `envelopes/M1-S03/2026-09-12T11-40-10Z.json` → `findings[2]`;
  `tests/M1-S03/results.json` → `process_observations` (`concerning`, `low`, `automation-governance`);
  `artefacts/M1-S03/deploy-order.md` § 4.

## D-M1S03-05 — UNVERIFIED, plan-bound: `Tier2_Escalation__e.Severity__c` is mapped from `Case.Priority`, and nothing says it should be

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`)
- **Agent:** `apex-builder` (run 2, `2026-09-12T11:23:31Z`, finding `S3-F-02`, unchanged through run 3)
- **Kind:** skill gap surfaced as a plan-bound UNVERIFIED, generalised the same way `D-M1S04-05`
  generalises it — a real ambiguity in the requirement's own language, recorded rather than guessed
  past.
- **What was recorded:** `Tier2_Escalation__e.Severity__c` is a `Text(40)` field (`M1-S01`). No
  clarification maps it to a Case field. `Case.Priority` (`High` / `Medium` / `Low`) is the only
  severity-shaped field this build has seen on Case, so `Tier2EscalationService` writes it there, with
  an inline `// UNVERIFIED` note at the assignment. `Q11`'s answer talks about "a Severity 1
  escalation" — a shape that does not match standard `Case.Priority` values at all, which raises the
  live possibility that the org has a dedicated severity field this build never saw.
- **Alternative rejected:** guessing a mapping table (e.g. `High` → `Severity 1`) to make the value
  look intentional. Rejected because no answer states the target shape or the mapping rule, and a
  silently-wrong severity on the ops dashboard is worse than a loudly-flagged one — this is exactly
  the class of defect `deploy-order.md` § 5 item 1 calls out as "silently wrong, not loud."
- **Grounded in:** `artefacts/M1-S03/deploy-order.md` § 5 item 1; step input `Q11`'s answer (verbatim
  "a Severity 1 escalation"); `artefacts/M1-S01/objects/Tier2_Escalation__e/fields/Severity__c.field-meta.xml`
  (`Text(40)`, no picklist).
- **Open item:** confirm with the dashboard team, before UAT, whether `Case.Priority` is the field the
  dashboard actually wants, or whether a `Severity 1`-shaped field exists elsewhere in the org that
  this build never probed (`build_mode: design-only` — no org was read to check).
- **Evidence:** `envelopes/M1-S03/2026-09-12T11-23-31Z.json` → `findings[1]` (`S3-F-02`, P2);
  `artefacts/M1-S03/deploy-order.md` § 5 item 1.

## D-M1S03-06 — Accepted: `TestDataFactory` is shipped byte-identical by both `M1-S03` and `M1-S04`; `M1-S05` lists the `ApexClass` member once

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`); the resolution is `M1-S05`'s (`docs`) to apply
- **Agent:** `apex-builder` (both runs; finding `S3-F-04`)
- **Kind:** design trade-off, the same shape `D-M1S04-06` records from the `M1-S04` side of the same
  fact — recorded twice, once per step that produces the duplicate, because each step's own
  `deploy-order.md` is the artefact a reader of that step consults first.
- **What was recorded:** `artefacts/M1-S03/classes/TestDataFactory.cls` and
  `artefacts/M1-S04/classes/TestDataFactory.cls` are both verbatim copies of
  `templates/apex/tests/TestDataFactory.cls` (`diff` empty against the template, verified this run per
  `artefacts/M1-S03/deploy-order.md` § 2). This is not a deploy collision:
  `scripts/mock_deploy.py:copy_artefacts` rebases every file onto
  `<dest>/<path-relative-to-the-step-dir>`, so both land on the same assembled path and the later step
  overwrites the earlier — both are byte-identical to the template, so the assembled tree is correct
  either way. It **is** a manifest hazard: a `package.xml` listing the `ApexClass` member twice is a
  manifest defect.
- **Alternative rejected:** having `M1-S03` or `M1-S04` declare the file as a dependency on the other
  rather than each shipping its own copy. Rejected because neither step `depends_on` the other (they
  are independent per the plan's DAG) and `agents/apex-builder/AGENT.md` Step 6 requires each step to
  ship every template it references, verbatim, regardless of what a sibling step also ships — the
  redundancy is the template-provenance rule working as designed, not a mistake.
- **Grounded in:** `artefacts/M1-S03/deploy-order.md` § 2 "The `TestDataFactory` duplication, and what
  `M1-S05` must do about it" (full member list this step contributes: `CaseTriggerHandler`,
  `IntegrationFailureTriggerHandler`, `Tier2EscalationService`, `Tier2WebhookQueueable`,
  `Tier2WebhookFinalizer`, `Tier2EscalationServiceTest`, `Tier2WebhookQueueableTest`,
  `IntegrationFailureResendTest`, `MockHttpResponseGenerator`, `TestDataFactory` — the last one "also
  contributed by M1-S04"); `envelopes/M1-S03/2026-09-12T11-23-31Z.json` → `findings[3]` (`S3-F-04`,
  INFO); `D-M1S04-06` (the `M1-S04`-side record of the same fact, plus the wider pattern that this
  plan has two Apex steps and no dedicated Apex-foundations step to hold a shared template dependency).
- **Open item:** `M1-S05` (build-level `package.xml`, type `docs`, agent `metadata-builder`,
  `depends_on` both `M1-S03` and `M1-S04`) emits the `ApexClass:TestDataFactory` member exactly once
  when it aggregates. This is `M1-S05`'s job, not a re-plan — recorded here so `M1-S05`'s own build
  pass does not have to rediscover it from the raw file list.
- **Evidence:** `artefacts/M1-S03/deploy-order.md` § 2; `artefacts/M1-S04/deploy-order.md` §§ 1–2;
  `envelopes/M1-S03/2026-09-12T11-23-31Z.json` → `findings[3]`.

## D-M1S03-07 — Skill gap: the library disagrees with itself on `Test.setMock` ordering — `apex-named-credentials-patterns` says before `Test.startTest`, the callouts checker and `test-class-standards` say after

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`)
- **Agent:** `apex-builder` (run 2, `2026-09-12T11:23:31Z`)
- **Kind:** skill gap, generalised the same way `D-M1S02-01` generalises it — a genuine contradiction
  between two cited skills and a checker, surfaced by following the checker (which fails the build)
  rather than the skill (which does not enforce anything).
- **What was recorded:** `skills/apex/apex-named-credentials-patterns/references/code-examples.md`
  § 6 places `Test.setMock(...)` **before** `Test.startTest()`.
  `skills/apex/callouts-and-http-integrations/scripts/check_callouts_and_http_integrations.py`'s rule
  6 flags exactly that ordering as **HIGH** and quotes the guide's own requirement that `startTest`
  precede the first `setMock` — the same ordering `skills/apex/test-class-standards/references/code-examples.md`
  already uses. This step's own acceptance-test description for the callouts checker compounds the
  confusion: it states the checker "fails on 'a test with setMock after startTest,'" which is the
  **opposite** of what the checker code actually does — it fails when no `startTest` precedes the
  first `setMock`. A reader fixing a failure from the plan's prose rather than the checker's own
  output would move the call the wrong way.
- **What was built:** every callout test in this step's three test classes calls `Test.startTest()`
  before `Test.setMock(...)`, following the checker (which fails the build) and
  `test-class-standards` over the named-credentials skill's own worked example. All three declared
  checkers exit 0 on the result.
- **Alternative rejected:** following `apex-named-credentials-patterns`'s worked example instead,
  which would have failed `check_callouts_and_http_integrations.py` rule 6 outright — not a live
  option once the checker is the acceptance test that gates `built`.
- **Grounded in:** `skills/apex/apex-named-credentials-patterns/references/code-examples.md` § 6;
  `skills/apex/callouts-and-http-integrations/scripts/check_callouts_and_http_integrations.py` rule 6;
  `skills/apex/test-class-standards/references/code-examples.md`;
  `envelopes/M1-S03/2026-09-12T11-23-31Z.json` → `process_observations` (`concerning`, `medium`,
  domain `library-consistency`; `concerning`, `low`, domain `plan-integrity`,
  `evidence.path: "plan.json steps[M1-S03].acceptance_tests[1].description"`).
- **Open item:** `skills/apex/apex-named-credentials-patterns` § 6's worked example needs its
  `Test.setMock`/`Test.startTest` order corrected to match the checker and
  `test-class-standards`, and this step's own `acceptance_tests[1].description` needs its
  "setMock after startTest" clause reversed to "setMock with no startTest before it" — neither of
  which is `build-doc-keeper`'s to write (a skill edit and a plan-text amendment, respectively).
- **Evidence:** `envelopes/M1-S03/2026-09-12T11-23-31Z.json` → `process_observations` (both entries
  above, `domain: library-consistency` and `domain: plan-integrity`); `plan.json` →
  `steps[M1-S03].acceptance_tests[1].description`.

## D-M1S03-08 — Skill gap (plan-hygiene): the `prose-only` amendment recorded as fixing the manual test's stale `HttpClient.cls` clause wrote no change at all

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`)
- **Agent:** surfaced by `build-doc-keeper` this pass, cross-checking `plan.json` directly; first
  flagged (without diagnosing the cause) by `step-tester` (`2026-09-12T11-50-18Z`)
- **Kind:** skill gap (plan-hygiene), generalised the same way `D-M1S02-06`/`D-M1S04-02`/`D-M1S04-07`
  generalise it — a stale plan-text defect, except that here the recorded *fix* for a stale defect is
  itself the defect.
- **What was recorded:** `step-tester`'s final run flagged that the step's manual acceptance test's
  clause (b) still names `templates/apex/HttpClient.cls` as the endpoint-composition mechanism, even
  though remedy B (`D-M1S03-01`) dropped that template before run 2 and neither run 2 nor run 3 ships
  it (`tests/M1-S03/results.json` → `detail.manual_classification.stale_reference_flagged`). `plan.json`
  separately records an amendment at `2026-09-12T11:52:45Z`
  (`steps[M1-S03].amendments[2]`, `prose_only: true`) whose stated `reason` is "Manual test clause (b)
  named `templates/apex/HttpClient.cls`, dropped by remedy B; re-worded so the M1 gate reviewer looks
  for the endpoint composition that exists." **Comparing `steps[M1-S03].acceptance_tests` (the current
  field) against `amendments[2].before.acceptance_tests` (what it replaced) byte-for-byte shows the two
  are identical** — the manual test's `expected` text still reads "...through templates/apex/HttpClient.cls"
  in both. The amendment was recorded — a `before` snapshot, a reason, a timestamp, `prose_only: true`
  — but no field actually changed. This is not the same defect `step-tester` flagged (a stale clause);
  it is a defect in the *attempted fix* for that clause, one layer further down, and it means the M1
  gate reviewer will still find `HttpClient.cls` named in the manual test text despite the plan's own
  record claiming otherwise.
- **Why this matters at the M1 gate:** the underlying security property clause (b) tests for — no
  literal hostname, no Apex-set `X-API-Key`/`Authorization` header, the endpoint composed as
  `callout:OnCall_Tool` — is independently true by inspection
  (`tests/M1-S03/results.json` → `detail.manual_classification.clause_a_verified_by_inspection` and
  the surrounding note), so nothing about the *feature* is wrong. What is wrong is that a reviewer
  ticking clause (b) literally against the named `HttpClient.cls` mechanism will find that file absent
  from the artefacts and may read the manual test itself as failing, or as evidence of an
  undocumented deviation, when the actual gap is a plan-text amendment that did not write.
- **Alternative rejected:** treating the amendment's existence (a recorded `before`, a reason, a
  timestamp) as proof the fix landed, and closing the item without checking the current field.
  Rejected — `agents/build-doc-keeper/AGENT.md` Step 7/8's idempotence discipline is exactly "verify
  what is on disk, never narrate," and `step-tester`'s own `suggested_followup`
  (`envelopes/M1-S03/2026-09-12T11-50-18Z.json`) explicitly asked this pass to record the stale clause
  into `decisions.md` — checking whether it had already been fixed, rather than assuming it, is what
  surfaced this.
- **Why this agent does not fix it:** per `agents/build-doc-keeper/AGENT.md` "What This Agent Does NOT
  Do" — it does not touch `plan.json` beyond the single status transition it owns for `M1-S03`, and
  a corrected re-wording of `acceptance_tests[type=manual].expected` is `amend-step --prose-only`'s
  job, legal now only because the step's status has left `pending` via the `built`/`tested`→`failed`→
  `pending` recovery path (the step is currently `tested`, not `pending`/`blocked`), not a doc-keeper
  edit.
- **Grounded in:** `plan.json` → `steps[M1-S03].acceptance_tests` vs `.amendments[2].before.acceptance_tests`
  (verified identical, this pass); `tests/M1-S03/results.json` →
  `detail.manual_classification.stale_reference_flagged`; `envelopes/M1-S03/2026-09-12T11-50-18Z.json`
  → `process_observations` (`concerning`, `medium`, domain `plan-text-drift`) and
  `suggested_followup` (domain `build-orchestration`).
- **Open item:** a second `amend-step M1-S03 --prose-only` that actually writes the reworded clause
  (b) text — e.g. "every endpoint is composed as `callout:OnCall_Tool` with no path appended; no class
  sets a literal hostname or an `Authorization`/`X-API-Key` header" — in place of the current text,
  and a check, after writing it, that the field changed.
- **Evidence:** `plan.json` → `steps[M1-S03].acceptance_tests[type=manual]`,
  `.amendments[2]`; `tests/M1-S03/results.json` → `detail.manual_classification`;
  `envelopes/M1-S03/2026-09-12T11-50-18Z.json` → `process_observations`, `suggested_followup`.

## D-M1S05-01 — Accepted: the manifest-aggregating step follows the artefacts on disk, not the step's own stale `inputs.members`; 13 `ApexClass` members, not the 11 the input names

- **Date:** 2026-09-12
- **Step:** `M1-S05` (`docs`)
- **Agent:** `metadata-builder` (run `2026-09-12T12-16-55Z`)
- **Kind:** design trade-off — which of two disagreeing sources an aggregating step follows when
  they conflict, generalised beyond this one step per `reports/drivers-log.md` friction (43).
- **What was recorded:** `plan.json` → `steps[M1-S05].inputs.members.ApexClass` names 11 classes.
  The artefacts under `artefacts/M1-S03/classes/` and `artefacts/M1-S04/classes/` carry 13 distinct
  `ApexClass` files (`TestDataFactory` and `MockHttpResponseGenerator`, both template-provenance
  copies that reached the build after the input was written and were never folded back into it —
  `D-M1S03-06`/`D-M1S04-06` record the `TestDataFactory` half of this from each producing step's own
  side). The input predates the two Apex rebuilds; the artefacts postdate them. `package.xml` was
  built from the artefacts: 13 `ApexClass` members, `TestDataFactory` counted once by SHA-256
  identity (`artefacts/M1-S05/deploy-order.md` § 1). The step's own always-on `manifest` check
  verifies this directly — 33 manifest members, 33 derived members, consistent in both directions
  (`tests/M1-S05/manifest-check.txt`) — so the choice is not merely asserted, it is the reading the
  step's own acceptance test enforces.
- **Alternative rejected:** manifesting exactly the 11 classes `inputs.members` names and leaving
  `TestDataFactory`/`MockHttpResponseGenerator` unmanifested. Rejected because the always-on
  `manifest` check (`standards/build-orchestration.md` § 5) fails a metadata-type step when an
  artefact file carries no member, so an 11-member manifest would fail this step's own acceptance
  test the moment it ran — the input's count was never a legal reading once the artefacts existed.
- **Grounded in:** `plan.json` → `steps[M1-S05].inputs.members.ApexClass` (11 names);
  `artefacts/M1-S05/package.xml` (13 `ApexClass` members); `artefacts/M1-S05/deploy-order.md` § 1
  ("Member roll-up"); `tests/M1-S05/manifest-check.txt`; `envelopes/M1-S05/2026-09-12T12-16-55Z.json`
  → `process_observations[2]` (`concerning`, `medium`, domain `plan-integrity`);
  `reports/drivers-log.md` "Build M1-S05 + manifest dry run" entry, friction (43).
- **Open item:** `steps[M1-S05].inputs.members.ApexClass` remains 11 in `plan.json` — a plan-text
  correction (`amend-step M1-S05 --prose-only`, still refused now the step has left `pending`) is a
  human's or a future re-plan's, not this pass's; `build-planner`'s own rule for an aggregating step
  should say inputs are a floor, not a ceiling, so a later rebuild of a contributing step cannot
  silently shrink the manifest back to a stale count.
- **Evidence:** `artefacts/M1-S05/package.xml`; `artefacts/M1-S05/deploy-order.md` § 1;
  `tests/M1-S05/manifest-check.txt`; `envelopes/M1-S05/2026-09-12T12-16-55Z.json`;
  `reports/drivers-log.md` friction (43).

## D-M1S05-02 — Skill gap (plan-hygiene): the plan's input deploy order sequences `PermissionSet` ahead of the fields it grants; the compiled order corrects it

- **Date:** 2026-09-12
- **Step:** `M1-S05` (`docs`)
- **Agent:** `metadata-builder` (run `2026-09-12T12-16-55Z`)
- **Kind:** skill gap (plan-hygiene), generalised the same way `D-M1S02-06`/`D-M1S04-02`/`D-M1S04-07`/
  `D-M1S03-08` generalise a plan-text defect, and separately filed as `reports/drivers-log.md`
  friction (44).
- **What was recorded:** `plan.json` → `steps[M1-S05].inputs.deploy_order` reads "ExternalCredential,
  NamedCredential, PermissionSet, then the object and field metadata, then the Apex" — `PermissionSet`
  third, ahead of the `CustomObject`/`CustomField` group its own twelve `fieldPermissions` rows and one
  `objectPermissions` row name. `admin/change-management-and-deployment/references/llm-anti-patterns.md`
  Anti-Pattern 4 states plainly that "permission sets referencing new fields fail if fields are not
  yet in the target," and both `artefacts/M1-S01/deploy-order.md` § 3 and `artefacts/M1-S02/deploy-order.md`
  § 3 already record the same fact from their own side. Deployed as separate staged requests in the
  input's own order, `Tier2_Webhook_Admin` fails on every field permission it grants. The input's own
  sentence frames that ordering as being *for* the staged case ("deploying in stages gives a readable
  failure when a reference is wrong") — which is exactly backwards, since that is the order that does
  not work staged.
- **What was built instead:** `artefacts/M1-S05/deploy-order.md` § 2 states the corrected build-wide
  order — objects and fields (group 1), the credential pair (group 2, independent of group 1), Apex
  (group 3), `PermissionSet` **last** (group 4), because it references all three groups before it.
  A single combined `sf project deploy start` over the merged manifest resolves all four groups in
  one request regardless (`reports/MOCK-DEPLOY-M1.md` run 5, manifest mode, 38/38), so the ordering
  question only bites a staged deploy — which is precisely the case the input's own text claims to be
  optimising for.
- **Alternative rejected:** silently deploying the input's order without comment, on the theory that a
  single combined manifest deploy makes the staged-order question moot. Rejected because the input's
  own text is offered as guidance for exactly the staged case it would break, and a future reader who
  splits this deploy into stages — the input's own suggested path — needs the corrected order named,
  not just the fact that the risk is currently avoided by not staging.
- **Grounded in:** `plan.json` → `steps[M1-S05].inputs.deploy_order`;
  `skills/admin/change-management-and-deployment/references/llm-anti-patterns.md` Anti-Pattern 4;
  `artefacts/M1-S01/deploy-order.md` § 3; `artefacts/M1-S02/deploy-order.md` § 3;
  `artefacts/M1-S05/deploy-order.md` § 2 ("Two ordering facts a reader of the per-step notes will
  otherwise trip on", item 1); `envelopes/M1-S05/2026-09-12T12-16-55Z.json` →
  `process_observations[3]` (`concerning`, `medium`, domain `deploy-order`);
  `reports/drivers-log.md` friction (44).
- **Open item:** a planner rule — field permissions after fields — so a future step's
  `inputs.deploy_order` cannot repeat this ordering, per the drivers-log friction's own proposed fix
  ("planner rule: field permissions after fields").
- **Evidence:** `artefacts/M1-S05/deploy-order.md` § 2; `reports/MOCK-DEPLOY-M1.md` run 5;
  `envelopes/M1-S05/2026-09-12T12-16-55Z.json`; `reports/drivers-log.md` friction (44).

## D-M1S05-03 — Accepted: the build-level manifest deliberately combines `M1-S01` and `M1-S02` in one deploy, against each step's own "don't combine" note, under Gotcha 10's own carve-out

- **Date:** 2026-09-12
- **Step:** `M1-S05` (`docs`)
- **Agent:** `metadata-builder` (run `2026-09-12T12-16-55Z`)
- **Kind:** design trade-off, resolving an apparent contradiction between two upstream steps' own
  deploy-order notes and the shape this aggregating step is required to produce.
- **What was recorded:** `artefacts/M1-S01/deploy-order.md` and `artefacts/M1-S02/deploy-order.md`
  both instruct that the object/field metadata and the permission-set/profile metadata should not
  travel in the same deploy request, citing
  `skills/admin/object-creation-and-design/references/gotchas.md` Gotcha 10. The build-level
  `package.xml` this step writes necessarily puts both in one manifest — that is the step's whole
  job. Gotcha 10's own remedy carries a carve-out: keep the two apart "**unless the access change is
  the point of the deployment**," and the hazard it actually describes is retrieve-side — a
  *retrieve* of one metadata type silently rewriting Profile/PermissionSet files that were retrieved
  in the same package (api_meta L41920–41921), not a deploy of hand-authored files.
- **What was built:** the combined manifest, on the reasoning that every condition of the carve-out
  holds here: `Tier2_Webhook_Admin` is hand-authored (never retrieved), is net-new in this build, is
  the access change this build exists to make, and is reviewed line by line at the M1 gate
  (`artefacts/M1-S02/deploy-order.md` § 6). No `Profile` component is in this manifest at all.
- **Alternative rejected:** splitting the milestone's deploy into two manifests (objects+fields, then
  access) to honour the two upstream notes literally. Rejected because § 5's Apex exception and this
  step's own purpose — one addressable unit for the whole build — require a single manifest, and the
  literal reading of Gotcha 10 the upstream notes state is the general case, not the carve-out case
  this build actually sits in.
- **Grounded in:** `artefacts/M1-S01/deploy-order.md` § 3; `artefacts/M1-S02/deploy-order.md` § 3;
  `skills/admin/object-creation-and-design/references/gotchas.md` Gotcha 10 (remedy and carve-out);
  `artefacts/M1-S05/deploy-order.md` § 2 (item 2, "The per-step notes say ... this manifest
  deliberately does"); `envelopes/M1-S05/2026-09-12T12-16-55Z.json` → `process_observations[4]`
  (`concerning`, `low`, domain `deploy-order`).
- **Open item:** none — the note itself is the safeguard: "if anyone ever retrieves this manifest
  back out of an org, re-read Gotcha 10 before deploying what comes back"
  (`artefacts/M1-S05/deploy-order.md` § 2).
- **Evidence:** `artefacts/M1-S05/deploy-order.md` § 2 item 2; `skills/admin/object-creation-and-design/references/gotchas.md`
  Gotcha 10; `envelopes/M1-S05/2026-09-12T12-16-55Z.json` → `process_observations[4]`.

## D-M1S05-04 — PV-007 closed for the deploy question, still open in the plan's own text: the AuthHeader manual test narrows in `deploy-order.md` § 3 but `plan.json` was not amendable to match

- **Date:** 2026-09-12
- **Step:** `M1-S05` (`docs`); the stale text and the decision that first flagged it (`D-M1S02-06`)
  both live one step earlier
- **Agent:** `metadata-builder` (run `2026-09-12T12-16-55Z`), closing the open item `D-M1S02-06` left
- **Kind:** skill gap (plan-hygiene), the same class `D-M1S02-06` opened and `D-M1S03-08`/`D-M1S04-07`
  generalise — a stale plan-text defect that a prior pass named and this pass narrows without being
  able to write the fix, because `amend-step` is refused once a step has left `pending`.
- **What was recorded:** `D-M1S02-06` named `M1-S05`'s manual acceptance test as still framing the
  `X-API-Key` `AuthHeader` `parameterValue` question in its pre-amendment, fully-open form, and filed
  it as `PV-007` ("deploy-order prose lag to be fixed by prose-only amendment once building"). This
  step's own `inputs.manual_steps_the_deploy_does_not_perform` item 1 — read at this pass — still
  reads unchanged: "Confirm the X-API-Key AuthHeader parameterValue formula against Salesforce Help
  before the External Credential is deployed - assumption A5 records that merge-field grammar as
  UNVERIFIED in the cited skill." Two of the three facts that framing left open are now closed: the
  parameter name and formula are supplied (`steps[M1-S02].amendments[1]`), and the org confirmed the
  element is required (`reports/MOCK-DEPLOY-M1.md` run 1, finding S2-F-02). What remains open is
  narrower than the plan's text still states.
- **What was built:** `artefacts/M1-S05/deploy-order.md` § 3 "Step 1" carries the narrowed reading in
  full — the parameter name/formula and the required-element question are marked **Closed**, and what
  is **still open** is stated as exactly two things: (a) the grammar parses on deploy, settled by
  `reports/MOCK-DEPLOY-M1.md` run 5 (manifest mode, 38/38, this build's own evidence that (a) is now
  also closed); (b) the header carries the key at run time, which only UAT can settle, because a
  formula that parses and resolves empty deploys cleanly and 401s on every callout. `deploy-order.md`
  § 3 Step 1 states this narrowed form and names the still-open amendment as `M1-S05`'s own to make
  once legal.
- **Why this agent does not fix `plan.json`:** per this agent's own "What This Agent Does NOT Do" —
  it touches `plan.json` only through the single status transition it owns for `M1-S05`, and
  `amend-step M1-S05 --prose-only` is refused now that the step is `tested` (past `pending`/`blocked`).
  The corrected wording lives in `deploy-order.md` § 3 as the interim carrier, exactly as `D-M1S02-06`
  anticipated it would have to.
- **Alternative rejected:** treating `D-M1S02-06`'s open item as already resolved because
  `deploy-order.md` now states the narrowed reading. Rejected — the plan's own `inputs` text, which is
  what a reviewer reading `PLAN.md` at the M1 gate sees first, is unchanged, so the staleness
  `D-M1S02-06` named is narrowed in the artefact but not closed in the plan record.
- **Grounded in:** `D-M1S02-06` (full text above); `plan.json` →
  `steps[M1-S05].inputs.manual_steps_the_deploy_does_not_perform` item 1;
  `artefacts/M1-S05/deploy-order.md` § 3 "Step 1 — confirm the AuthHeader formula (read the
  narrowing, not the original question)"; `reports/MOCK-DEPLOY-M1.md` runs 1 and 5;
  `envelopes/M1-S05/2026-09-12T12-16-55Z.json` → `process_observations[5]` (`ambiguous`, `low`,
  domain `plan-hygiene`).
- **Open item:** unchanged from `D-M1S02-06` — `amend-step M1-S05` (or a re-plan) to narrow the plan's
  own manual-test wording to match `deploy-order.md` § 3 Step 1's reading: the grammar parses on
  deploy (now itself closed by run 5) and the header's run-time behaviour is confirmed at UAT.
- **Evidence:** `plan.json` → `steps[M1-S05].inputs.manual_steps_the_deploy_does_not_perform`;
  `artefacts/M1-S05/deploy-order.md` § 3; `reports/MOCK-DEPLOY-M1.md` runs 1 and 5; `D-M1S02-06`.

## D-M1S05-05 — Accepted: manifest-mode dry run (run 5) is the build's own proof that the aggregated `package.xml` deploys as one unit, closing the question run 4's source-mode dry run could not reach

- **Date:** 2026-09-12
- **Step:** `M1-S05` (`docs`)
- **Agent:** `step-tester` (run `2026-09-12T12-25-04Z`), decision recorded by `build-doc-keeper` this
  pass
- **Kind:** design trade-off — which of two dry-run modes counts as evidence for which claim — the
  same shape as `D-M1S03-06`'s discharge, recorded here because it settles what `M1-S05` itself
  contributes rather than what a producing step contributes.
- **What was recorded:** `reports/MOCK-DEPLOY-M1.md` run 4 (source mode, `M1-S01`…`M1-S04`) proved
  every individual class and trigger compiles; it does not exercise the merged `package.xml`, because
  source mode assembles a source tree directly from the selected steps' artefact directories and does
  not read any manifest (`standards/build-orchestration.md` § 5, "Manifest mode is the only check that
  reads the merged package.xml"). Run 4 is therefore evidence for M1-S03/M1-S04's own claims, not for
  this step's.
- **What was built:** run 5, over this step's own `artefacts/M1-S05/package.xml`, in manifest mode —
  the mode that reads the merged manifest and is "the shape a real deployment would use"
  (`reports/MOCK-DEPLOY-M1.md` run 5). 38/38 succeeded, matching run 4's count exactly, which is the
  build's own confirmation that the manifest names neither more nor fewer deployable components than
  the source tree carries. This is the evidence this step's own manual acceptance test and
  `D-M1S05-01`'s manifest-authority claim both rest on, rather than the step's declared checker alone
  (`check_deployment_manifest.py` asserts manifest shape and risky-type presence; it does not deploy
  or compile anything).
- **Alternative rejected:** treating run 4's success as sufficient evidence for this step, on the
  theory that "the same files compiled once, so the manifest naming them must be fine too." Rejected
  because a manifest can misname, omit or duplicate a member while every underlying file still
  compiles in isolation — exactly the class of defect the `TestDataFactory` de-duplication
  (`D-M1S03-06`/`D-M1S04-06`, discharged by `D-M1S05-01` above) shows this build actually had to
  guard against.
- **Grounded in:** `standards/build-orchestration.md` § 5 ("Manifest mode is the only check that reads
  the merged package.xml"); `reports/MOCK-DEPLOY-M1.md` runs 4 and 5; `tests/M1-S05/manifest-check.txt`;
  `envelopes/M1-S05/2026-09-12T12-25-04Z.json` (`step-tester`, confidence HIGH).
- **Open item:** none — this is the milestone's own manifest-mode proof; `milestone-verifier` reads
  it as evidence for the M1 acceptance report rather than re-deriving it.
- **Evidence:** `reports/MOCK-DEPLOY-M1.md` runs 4–5; `tests/M1-S05/manifest-check.txt`;
  `envelopes/M1-S05/2026-09-12T12-25-04Z.json`.

## D-M1S03-09 — Deviation (repair): all three test classes now run their assertions as a permissioned `TestUserFactory` user, closing S2-F-11

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`), run 4 — a § 4 test-only repair (`documented` → `running` → `built`)
- **Agent:** `apex-builder` (run 4, `2026-09-12T16-13-43Z`, finding `S4-F-01`); confirmed by
  `step-tester` (`2026-09-12T16-30-00Z`, `built → tested`)
- **Kind:** Deviation, per `agents/build-doc-keeper/AGENT.md` Step 3 — the tests as originally shipped
  (runs 2–3) ran as the deploying user; the repair changes them to run as a provisioned permissioned
  user, a real change from what was built before, with its reason stated in the finding it closes.
- **What was recorded:** `reports/MOCK-DEPLOY-M1.md` run 6 (`--test-level RunSpecifiedTests`)
  compiled this step's package clean (39/39 `ok`) and then failed all 28 test methods at execution
  (`S2-F-11`): none of `Tier2EscalationServiceTest`, `Tier2WebhookQueueableTest` or
  `IntegrationFailureResendTest` carried a `System.runAs` block for a permissioned user, while
  `Tier2WebhookQueueable` and `CaseTriggerHandler` correctly enforce the running user's FLS with
  `WITH USER_MODE` at API 67.0 — the tests were the first user-mode caller and were written as if the
  running user were omnipotent. The repair adds `classes/TestUserFactory.cls` (+ `-meta.xml`, a
  verbatim copy of `templates/apex/tests/TestUserFactory.cls`, diff empty) and, in each of the three
  test classes, folds `TestUserFactory.createUser('Standard User', new List<String>{
  'Tier2_Webhook_Admin' })` into the existing mixed-DML setup-object fence, then wraps every one of
  the 19 pre-existing `@IsTest` method bodies in `System.runAs(agent())` — same statements, same
  assertions, same messages, nothing added or removed. `check_test_class_standards.py`'s
  `user-mode-test-without-runas` rule now reports 0 findings against `artefacts/M1-S03/classes`, down
  from a finding per test class before this run.
- **Alternative rejected:** relaxing the production classes' `WITH USER_MODE` enforcement so the tests
  would pass without a permissioned running user. Rejected because the org's own diagnosis is explicit
  that the enforcement is correct and the tests were the defect — `Tier2WebhookQueueable` and
  `CaseTriggerHandler` are unchanged by this repair, and the fix is confined to the tests' own running
  user and setup, per the finding's own scoping.
- **Grounded in:** `skills/apex/test-class-standards/references/gotchas.md` Gotcha 13;
  `skills/apex/test-class-standards/references/examples.md` Example 5 (this exact class, worked
  through in full — `Tier2EscalationServiceTest` / `Tier2_Webhook_Admin` / `Tier2_Notified_At__c`);
  `skills/apex/mixed-dml-and-setup-objects` (why the user-provisioning call sits inside the existing
  setup-object `runAs` fence, ahead of any `Case` DML in the same transaction).
- **Evidence:** `envelopes/M1-S03/2026-09-12T16-13-43Z.json` → `findings[0]` (`S4-F-01`, P0);
  `envelopes/M1-S03/2026-09-12T16-30-00Z.json` (step-tester retest, confidence HIGH);
  `reports/MOCK-DEPLOY-M1.md` run 6 (`S2-F-11`); `artefacts/M1-S03/deploy-order.md` § 0b.

## D-M1S03-10 — UNVERIFIED, plan-bound: `PROFILE = 'Standard User'` is the library's own worked-example default, not a value any clarification names (S4-F-03)

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`), run 4 repair
- **Agent:** `apex-builder` (run 4, `2026-09-12T16-13-43Z`, finding `S4-F-03`)
- **Kind:** skill gap surfaced as a plan-bound UNVERIFIED, the same shape `D-M1S03-05` and `D-M1S04-05`
  already record from this build — a real ambiguity the plan's own clarifications never settle,
  written down rather than guessed past.
- **What was recorded:** each of the three repaired test classes now carries `PROFILE = 'Standard
  User'`, passed to `TestUserFactory.createUser(PROFILE, ...)`. No clarification in this build's 45
  names a Profile for the users who can escalate a Case — `Q19` names three admins by role ("Support
  Engineering admins"), not by profile. `'Standard User'` is used because it is a real, standard
  Salesforce profile present in every org and is the exact value
  `skills/apex/test-class-standards/references/examples.md` Example 5 uses for this same class — the
  narrowest legal default rather than a grounded fact.
- **Alternative rejected:** leaving `PROFILE` unset or inventing an org-specific-sounding profile name
  to make the value look grounded. Rejected on `AGENT_CONTRACT.md` rule 12 — a plausible-sounding name
  that is not attested is worse than a real, generic one flagged as a default; `TestUserFactory`
  requires a real profile name to compile against any org, so a default was unavoidable, and the one
  chosen is at least attested against a worked example rather than invented.
- **Grounded in:** `skills/apex/test-class-standards/references/examples.md` Example 5; `plan.json` →
  `clarifications` `Q19` (verbatim: three admin roles, no profile named).
- **Open item:** confirm the actual profile(s) of the users `Tier2_Webhook_Admin` is assigned to
  (`artefacts/M1-S03/deploy-order.md` § 10 item 2) and update `PROFILE` in all three test classes if it
  differs from `'Standard User'`, before UAT. Does not block this repair or the retest: the checker and
  the pattern do not depend on which real profile is named, only that one exists in the target org.
- **Evidence:** `envelopes/M1-S03/2026-09-12T16-13-43Z.json` → `findings[2]` (`S4-F-03`, INFO) and
  `process_observations` (`ambiguous`, `low`, domain `integration-contract`);
  `artefacts/M1-S03/deploy-order.md` § 9.

## D-M1S03-11 — Accepted: `TestUserFactory` is a new `ApexClass` member `M1-S05`'s manifest must add (S4-F-02) — an `M1-S05` obligation, not `M1-S03`'s

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`), run 4 repair; the resolution is `M1-S05`'s (`docs`) to apply
- **Agent:** `apex-builder` (run 4, `2026-09-12T16-13-43Z`, finding `S4-F-02`)
- **Kind:** design trade-off / obligation, the same shape `D-M1S03-06` already records for
  `TestDataFactory` from this same step — a new file this step ships that another step's manifest must
  learn about, recorded on the producing step because that is the artefact a reader of this step
  consults first.
- **What was recorded:** the repair's own task asked for `TestUserFactory` to be added to "the step's
  `package.xml`." This `apex-builder`-owned `automation` step has never declared one of its own —
  `standards/build-orchestration.md` § 5 **The Apex exception** assigns every `ApexClass`/`ApexTrigger`
  member this step produces to the build-level manifest step **M1-S05** (`depends_on` this step)
  instead, and this step's own `manifest` acceptance test already records skipped-not-applicable,
  naming M1-S05. Declaring a local `package.xml` here would contradict that recorded exception and
  § 4 condition 2 (an agent may not declare an output its own Output Contract does not produce —
  `apex-builder`'s names none). `artefacts/M1-S05/package.xml` and `reports/MILESTONE-M1-package.xml`
  still list only the pre-run-4 twelve `ApexClass` members from this step; `TestUserFactory` is a
  thirteenth, not yet in either file.
- **Alternative rejected:** writing a local `package.xml` under `artefacts/M1-S03/` anyway, so the new
  class would have manifest coverage immediately. Rejected because it would contradict this step's own
  recorded Apex exception and duplicate what `M1-S05` exists to aggregate — the fix belongs at M1-S05,
  not as a second, competing manifest.
- **Grounded in:** `standards/build-orchestration.md` § 4 condition 2, § 5 **The Apex exception**;
  `D-M1S03-06` (the same pattern already applied to `TestDataFactory` from this step).
- **Open item:** re-run `M1-S05` (`metadata-builder`) once this step is `documented`, to add the
  `TestUserFactory` `ApexClass` member to the build-level `package.xml` — out of scope for this
  M1-S03-only repair and documentation pass. `milestone:M1` was approved on evidence (dry runs 1–5)
  that predates both `S2-F-06` (tests never executed) and `S2-F-11` (tests failed once they did); a
  fresh `M1-S05` build plus `/verify-milestone` against a dry run that actually executes tests is what
  re-signs the M1 acceptance this repair puts back in question.
- **Evidence:** `envelopes/M1-S03/2026-09-12T16-13-43Z.json` → `findings[1]` (`S4-F-02`, P2) and
  `process_observations` (`suggested_followup`, `medium`, domain `build-loop`,
  `suggested_followup_agent: milestone-verifier`); `artefacts/M1-S03/deploy-order.md` §§ 0b, 2.

## D-M1S04-08 — Deviation: the § 0c test-only repair closes `S2-F-11` for `M1-S04` by running every `Tier2ChannelHealthTest` method as a `TestUserFactory`-provisioned user holding `Tier2_Webhook_Admin`

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`), run 3 — a § 4 test-only repair (`documented` → `running` → `built` → `tested`)
- **Agent:** `apex-builder` (run 3, `2026-09-12T16-30-00Z`, finding `S5-F-01`); confirmed by
  `step-tester` (`2026-09-12T16-45-00Z`, `built → tested`)
- **Kind:** Deviation, per `agents/build-doc-keeper/AGENT.md` Step 3 — the tests as originally shipped
  (runs 1–2) ran as the deploying user; the repair changes them to run as a provisioned permissioned
  user, the same shape M1-S03's own accepted repair (`D-M1S03-09`) applied to its three test classes.
- **What was recorded:** `reports/MOCK-DEPLOY-M1.md` run 6 (`--test-level RunSpecifiedTests`) is the
  finding source for both steps' repairs (`S2-F-11`): `Tier2ChannelHealthQueueable`'s three aggregate
  `COUNT()` queries enforce the running user's FLS with no keyword at all under API 67.0 default user
  mode, and `Tier2ChannelHealthTest` carried no `System.runAs` block for a permissioned user — every
  method ran as the deploying user. The repair adds `PERM_SET`/`PROFILE` constants, a new setup-object
  `System.runAs` fence in `@TestSetup` around `TestUserFactory.createUser('Standard User', new
  List<String>{ 'Tier2_Webhook_Admin' })`, a re-queried `agent()` helper, and wraps all 11
  pre-existing `@IsTest` method bodies in `System.runAs(testUser)` — same statements, same assertions,
  same messages, same order, confirmed by a whitespace-insensitive diff showing only inserted lines.
  `check_test_class_standards.py`'s `user-mode-test-without-runas` rule now reports 0 findings against
  `artefacts/M1-S04/classes` (down from 1, confirmed against the pre-repair file in isolation).
  `Tier2ChannelHealthSchedulable.cls` and `Tier2ChannelHealthQueueable.cls` are untouched.
- **Alternative rejected:** relaxing the Queueable's default-user-mode enforcement so the tests would
  pass under the deploying user. Rejected for the same reason `D-M1S03-09` rejects it: the org's own
  diagnosis is that the enforcement is correct and the test fixture was the defect.
- **Grounded in:** `skills/apex/test-class-standards/references/gotchas.md` Gotcha 13;
  `skills/apex/test-class-standards/references/examples.md` Example 5;
  `skills/apex/mixed-dml-and-setup-objects` (why the user-provisioning call sits in its own new
  `runAs` fence — unlike M1-S03, this class had no pre-existing setup-object fence to fold into);
  `D-M1S03-09` (the identical pattern already accepted for this build's other Apex step).
- **Evidence:** `envelopes/M1-S04/2026-09-12T16-30-00Z.json` → `findings[0]` (`S5-F-01`, P0);
  `envelopes/M1-S04/2026-09-12T16-45-00Z.json` (step-tester retest, confidence HIGH);
  `reports/MOCK-DEPLOY-M1.md` run 6 (`S2-F-11`); `artefacts/M1-S04/deploy-order.md` § 0c.

## D-M1S04-09 — Accepted: `Tier2ChannelHealthTest` now depends on `M1-S03`'s `TestUserFactory` copy, recorded in prose because `amend-step` could not add it to `depends_on`

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`), run 3 repair
- **Agent:** `apex-builder` (run 3, `2026-09-12T16-30-00Z`, finding `S5-F-02`)
- **Kind:** Design trade-off / obligation, the same shape `D-M1S03-11` records for the mirror-image
  gap on `M1-S03`'s side — a new cross-step dependency the plan's machine-readable state cannot yet
  carry, recorded where a reader of this step consults first.
- **What was recorded:** the § 0c repair's `TestUserFactory.createUser(...)` call references a class
  this step does not ship — `templates/apex/tests/TestUserFactory.cls` is already shipped verbatim by
  `M1-S03`'s own `S2-F-11` repair (`artefacts/M1-S03/classes/TestUserFactory.cls` + `-meta.xml`), and
  this step depends on that copy rather than shipping a second one. `plan.json`'s
  `steps[M1-S04].depends_on` is still `["M1-S01"]` only: `amend-step` is refused once a step has left
  `pending` (this step was `running`), the same limitation `M1-S03`'s own repair recorded for its
  `package.xml` request (`D-M1S03-11`). `scripts/mock_deploy.py:copy_artefacts` rebases every step's
  files onto one assembled path, so the single shipped copy is sufficient at deploy time regardless of
  what `depends_on` says — the gap is in the plan's own dependency record, not in what would actually
  be assembled.
- **Alternative rejected:** shipping a second, redundant copy of `TestUserFactory.cls` under
  `artefacts/M1-S04/` so the step's own manifest directory would be self-contained. Rejected because
  it would produce two identical `ApexClass` members for `M1-S05`'s build-level manifest to
  deduplicate — the same problem this build's `TestDataFactory` dependency already causes and already
  has an open recommendation for (`artefacts/M1-S04/deploy-order.md` § 2, Apex-foundations step).
- **Grounded in:** `standards/build-orchestration.md` § 2 (`amend-step` refused once a step leaves
  `pending`), § 4 Apex row note (the Apex-foundations recommendation for a shared
  `templates/apex/**` dependency shared by more than one Apex step); `D-M1S03-11` (the same
  limitation recorded from the producing step's side).
- **Open item:** whoever next re-plans this build should add `M1-S03` to `steps[M1-S04].depends_on`,
  and should consider the Apex-foundations step `standards/build-orchestration.md` § 4 already
  recommends for the shared `TestDataFactory` dependency — `TestUserFactory` is now a second,
  independent reason for it.
- **Evidence:** `envelopes/M1-S04/2026-09-12T16-30-00Z.json` → `findings[1]` (`S5-F-02`, P1) and
  `extensions.not_carried_out[0]`; `artefacts/M1-S04/deploy-order.md` § 0c, § 2.

## D-M1S04-10 — UNVERIFIED, plan-bound: two of the eleven `runAs`-wrapped test methods now depend on the `Standard User` profile's ability to read `PermissionSetAssignment`/`CronTrigger`/`AsyncApexJob`, which `Tier2_Webhook_Admin` does not grant

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`), run 3 repair
- **Agent:** `apex-builder` (run 3, `2026-09-12T16-30-00Z`, finding `S5-F-03`)
- **Kind:** skill gap surfaced as a plan-bound UNVERIFIED, the same shape `D-M1S04-05` (the
  `WITH USER_MODE`-on-aggregate question) and `D-M1S03-10` already record from this build — a real
  ambiguity the plan's own clarifications never settle, written down rather than guessed past.
- **What was recorded:** `Tier2_Webhook_Admin` (confirmed via
  `artefacts/M1-S02/permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml`) grants object/field
  permissions only on `Integration_Failure__c` and `Case.Tier2_Notified_At__c` — nothing on
  `PermissionSetAssignment`, `CronTrigger` or `AsyncApexJob`. Since the § 0c repair,
  `rosterResolutionReturnsTheDistinctActiveAssigneeEmails` (queries `PermissionSetAssignment`
  directly) and `scheduleCreatesAWaitingCronTriggerAndDispatchesTheQueueable` (calls
  `System.schedule` and queries `CronTrigger`/`AsyncApexJob`) both run as the `Standard
  User`-profile permissioned agent under API 67.0's default user mode instead of the deploying user.
  Whether that profile can read those objects or schedule Apex is stated in no cited skill. This
  mirrors the same open question `artefacts/M1-S04/deploy-order.md` § 4 item 1 already raises for the
  production scheduling user — the repair surfaces it in the test fixture too, rather than resolving
  it, because resolving it means changing `Tier2_Webhook_Admin` (`M1-S02`, a different step, out of
  scope for a test-only repair).
- **Alternative rejected:** widening `Tier2_Webhook_Admin`'s grants to cover
  `PermissionSetAssignment`/`CronTrigger`/`AsyncApexJob` as part of this repair. Rejected because that
  permission set belongs to `M1-S02`, which is `documented`; changing it is outside a test-only
  repair's scope and outside this step's own artefacts.
- **Grounded in:** `artefacts/M1-S02/permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml`;
  `artefacts/M1-S04/deploy-order.md` §§ 0c, 4 item 1, 8.
- **Open item:** the org's own answer is pending a dry run that actually executes these two methods
  under the permissioned agent (dry run 7 in the mock-deploy sequence, following run 6's
  `reports/mock-deploy/2026-09-12T13-08-43Z/`); until that result lands and is reconciled into
  `reports/MOCK-DEPLOY-M1.md`, whether the two methods pass, throw, or read empty under a `Standard
  User` profile is not established either way by this pass. Does not block this repair or the retest:
  the checker and the repair pattern do not depend on the answer, only on a permissioned user
  existing.
- **Evidence:** `envelopes/M1-S04/2026-09-12T16-30-00Z.json` → `findings[2]` (`S5-F-03`, P2) and
  `process_observations` (`ambiguous`, `low`, domain `integration-contract`);
  `artefacts/M1-S04/deploy-order.md` §§ 0c, 4, 8.

## D-M1S03-12 — Deviation (repair): `TestDataFactory` refreshed to the corrected template — a lookup is populated only when the caller supplies it — closing S2-F-12 for this step

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`), run 5 — a second, narrower § 4 test-only repair
  (`documented` → `running` → `built` → `tested`), after run 4's `S2-F-11` repair (`D-M1S03-09`)
- **Agent:** `apex-builder` (run 5, `2026-09-12T17-05-00Z`, finding `S5-F-01`); confirmed by
  `step-tester` (`2026-09-12T16-51-00Z`, `built → tested`)
- **Kind:** Deviation, per `agents/build-doc-keeper/AGENT.md` Step 3 — the shared test factory as
  shipped through run 4 assigned a lookup field unconditionally; the repair changes it to assign the
  field only when the caller supplies a non-null Id, a real change from what was built before, with
  its reason stated in the finding it closes.
- **What was recorded:** `reports/MOCK-DEPLOY-M1.md` run 7 — after the § 0b (`S2-F-11`) fix put every
  test method inside `System.runAs(agent)` as the `Tier2_Webhook_Admin`-permissioned user — failed
  all 30 test methods across `M1-S01`…`M1-S04` at the same `@TestSetup` seed insert:
  `System.DmlException: Operation failed due to fields being inaccessible on Sobject Case ...
  fieldNames: AccountId`. `TestDataFactory.createCases(count, accountId, overrides)` assigned
  `AccountId = accountId` directly inside the constructor's field list, so a `null` argument still
  marked the field populated once Apex's default user-mode DML (API 67.0+) checked FLS on every
  populated field at insert, and the `Standard User`-profile agent holds no create access on
  `Case.AccountId` — a field this deployment's permission set was never asked to grant, because no
  test needed it. All three of this step's test classes call the factory as `createCases(<n>, null,
  null)` (`IntegrationFailureResendTest.cls:57`, `Tier2EscalationServiceTest.cls:61`,
  `Tier2WebhookQueueableTest.cls:64`) and none references `Case.AccountId` anywhere — verified by
  grep before and after this run. `classes/TestDataFactory.cls` was replaced with a verbatim copy of
  the corrected `templates/apex/tests/TestDataFactory.cls` (`diff` empty, commit `5edcb3281`):
  `createContacts`, `createOpportunities` and `createCases` now construct the record without the
  lookup field and set it only inside `if (accountId != null) { record.AccountId = accountId; }`.
  No test-class call site needed a change — the corrected factory leaves the field genuinely unset
  for a `null` argument, which is the intent `skills/apex/test-class-standards/references/gotchas.md`
  Gotcha 14 describes, not a regression. The three previously-declared checkers plus the undeclared
  `check_test_class_standards.py --manifest-dir artefacts/M1-S03/classes` were re-run verbatim: 0
  findings across all four; `check-outputs` is `ok` on all 20 declared paths.
- **Alternative rejected:** granting `Tier2_Webhook_Admin` create-FLS on `Case.AccountId` so the
  unconditional assignment would deploy clean instead of correcting the factory. Rejected because no
  call site in this step needs the field and no clarification asks for `AccountId` access on this
  permission set — granting it here would reopen, from the other direction, the same widening
  `D-M1S02-04` already rejected for `Case` access on `Tier2_Webhook_Admin`.
- **Grounded in:** `skills/apex/test-class-standards/references/gotchas.md` Gotcha 14 (names this
  exact org message and this build as its source); `templates/apex/tests/TestDataFactory.cls`
  (commit `5edcb3281`); `reports/MOCK-DEPLOY-M1.md` run 7.
- **Consequences for `M1-S04`:** `M1-S04` ships an independent copy of `TestDataFactory.cls` under
  its own artefacts and carried the identical defect; this run's scope was `M1-S03` alone
  (`envelopes/M1-S03/2026-09-12T17-05-00Z.json` → `findings[1]`, `S5-F-02`, flagged `M1-S04` as
  needing the same repair). **That gap is closed, not open:** `M1-S04` was repaired in parallel by
  its own run 3 — `artefacts/M1-S04/deploy-order.md` § 0d records the identical verbatim-template
  replacement, closing the same `S2-F-12` finding for that step's copy — so a reader of `S5-F-02` or
  of `tests/M1-S03/summary.md`'s "concerning" note about `M1-S04` shipping "a byte-identical
  (pre-fix) copy" should treat that specific observation as superseded by `M1-S04`'s own
  documentation pass, not as a standing gap.
- **Evidence:** `envelopes/M1-S03/2026-09-12T17-05-00Z.json` → `findings[0]` (`S5-F-01`) and
  `findings[1]` (`S5-F-02`); `envelopes/M1-S03/2026-09-12T16-51-00Z.json` (step-tester retest,
  confidence HIGH, `built → tested`); `artefacts/M1-S03/deploy-order.md` § 0c;
  `tests/M1-S03/results.json`; `artefacts/M1-S04/deploy-order.md` § 0d (the parallel repair that
  closes `S5-F-02`).

## D-M1S04-11 — Deviation (repair): `TestDataFactory.cls` replaced with the corrected canonical template, closing `S2-F-12` for `M1-S04`

- **Date:** 2026-09-12
- **Step:** `M1-S04` (`automation`), run 4 repair (§ 0d)
- **Agent:** `apex-builder` (run 4, `2026-09-12T16-45-51Z`, finding `S6-F-01`); confirmed by
  `step-tester` (`2026-09-12T16-49-37Z`, re-test after run 4)
- **Kind:** Deviation, per `agents/build-doc-keeper/AGENT.md` Step 3 — the shared test-data factory
  this step ships (a verbatim `templates/apex/tests/TestDataFactory.cls` copy) is replaced wholesale
  with a newer verbatim copy of the same template, corrected upstream; no production or test class in
  this step's own artefacts changed.
- **What was recorded:** `reports/MOCK-DEPLOY-M1.md` run 7 is the finding source (`S2-F-12`, HIGH,
  library): `TestDataFactory.createCases(count, accountId, overrides)` assigned `AccountId =
  accountId` unconditionally, so `Tier2ChannelHealthTest.seed()`'s call with a null `accountId`
  argument still left the field marked populated on the constructed sObject. Under API 67.0's default
  user mode, the plain `insert` inside `System.runAs(agent)` (the § 0c repair's permissioned test
  user) checked FLS on that populated-but-null field, and the `Standard User`-profile agent this
  build's `Tier2_Webhook_Admin` grants no create access to `Case.AccountId` — confirmed by the
  operator's run-7 probe (`createable=true Subject=true Status=true Origin=true AccountId=false
  Tier2_Notified_At__c=true profile=Standard User psa=1 | fields=AccountId |
  code=CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY`). The same defect failed all 30 test methods across both
  this step and `M1-S03` at the identical `@TestSetup` seed-insert line.
  `skills/apex/test-class-standards/references/gotchas.md` Gotcha 14 names this exact failure mode and
  its two-part fix. `classes/TestDataFactory.cls` is replaced with a verbatim copy of the corrected
  `templates/apex/tests/TestDataFactory.cls` (commit `5edcb3281`) — `diff` against the template is
  empty, confirmed this run. `Tier2ChannelHealthSchedulable.cls`, `Tier2ChannelHealthQueueable.cls`
  and `Tier2ChannelHealthTest.cls` are all unchanged: the existing seed already called
  `createCases(1, null, overrides)` and no test method reads or asserts on `Case.AccountId`, so no
  compensating test edit was needed. All three declared checkers, plus the due-diligence
  `check_test_class_standards.py` run, re-ran at exit 0 (`tests/M1-S04/results.json`, `step-tester`
  run `2026-09-12T16-49-37Z`).
- **Alternative rejected:** patching `Tier2ChannelHealthTest.seed()` to pass a non-null placeholder
  `accountId` instead of fixing the factory. Rejected because the defect is in the shared template,
  not the caller — the same unconditional assignment would still fail the identical `M1-S03` seed call
  and any future caller passing `null`, and the library's own canonical fix (Gotcha 14) is at the
  factory, not at each call site.
- **Grounded in:** `skills/apex/test-class-standards/references/gotchas.md` Gotcha 14;
  `templates/apex/tests/TestDataFactory.cls` (corrected, commit `5edcb3281`);
  `standards/build-orchestration.md` § 4 (`documented → running` test-only repair transition);
  `D-M1S04-08` (the identical repair shape this build already accepted for `S2-F-11`).
- **Evidence:** `envelopes/M1-S04/2026-09-12T16-45-51Z.json` → `findings[0]` (`S6-F-01`, P0);
  `envelopes/M1-S04/2026-09-12T16-49-37Z.json` (step-tester retest, confidence HIGH);
  `reports/MOCK-DEPLOY-M1.md` run 7 (`S2-F-12`); `artefacts/M1-S04/deploy-order.md` § 0d.

## D-M1S05-06 — Accepted: `TestUserFactory` added as a fourteenth `ApexClass` member (33→34), closing `S2-F-11`; the re-run brief's finding-id citation corrected, not propagated

- **Date:** 2026-09-12
- **Step:** `M1-S05` (`docs`), run 2 (`documented` → `running` → `built` → `tested`, a § 4 test-only-
  adjacent rebuild)
- **Agent:** `metadata-builder` (run 2, `2026-09-12T17-03-58Z`); confirmed by `step-tester`
  (`2026-09-12T17-09-17Z`)
- **Kind:** Deviation, paired with a skill gap (plan-hygiene) citation correction — the same
  generalisation `D-M1S02-06` and `D-M1S04-07` apply to a re-run instruction's own wording, recorded
  without blocking the step.
- **What was recorded:** `artefacts/M1-S05/package.xml` (the build-level manifest) was regenerated to
  add `classes/TestUserFactory.cls` as a new `ApexClass` member — 13 → **14** `ApexClass` members, 33
  → **34** total. This closes the obligation `D-M1S03-11` already recorded (that `M1-S05`'s manifest
  must add `TestUserFactory` once `M1-S03` shipped it) and traces to the underlying root cause named in
  finding **S2-F-11** (`reports/MOCK-DEPLOY-M1.md` run 6): the deploying user held no FLS on the
  `M1-S01` fields, so every `M1-S03` test method failed as that user, and `M1-S03`'s repair added
  `TestUserFactory` to provision a permissioned `@TestSetup` user. Verified this run by SHA-256 against
  `templates/apex/tests/TestUserFactory.cls` (verbatim copy) and by a bidirectional 34-member/34-file
  manifest check over the whole `artefacts/M1-S0[1-4]/` tree — no member without a file, no file
  without a member, no duplicate, no wildcard. No other member type changed; `TestDataFactory`'s
  backing bytes changed under the unrelated `S2-F-12` repair, re-verified by SHA-256 as still one
  unambiguous member with no member-count effect.
- **Finding-id correction — recorded, not propagated:** the operator's re-run brief cited "finding
  `S4-F-02`" as the reason to add `TestUserFactory`. `metadata-builder`'s own investigation
  (`artefacts/M1-S05/deploy-order.md` § 0; `envelopes/M1-S05/2026-09-12T17-03-58Z.json` →
  `process_observations`, `concerning`/`medium`) reports finding no id `S4-F-02` in
  `reports/MOCK-DEPLOY-M1.md` or either Apex step's `deploy-order.md`, and names **S2-F-11** as the
  actual grounding finding instead. This entry cites S2-F-11 as the grounding fact, per that
  determination, and does not carry `S4-F-02` forward as if it were the reason `TestUserFactory`
  exists.
  **Caveat this pass adds, from re-reading this file before appending:** `D-M1S03-11` (above, this
  file) is itself titled with a finding literally labelled `S4-F-02` — `apex-builder`'s own run-4
  finding on `M1-S03`, recording the *obligation* that `M1-S05` must add `TestUserFactory` to its
  manifest, which is a different fact from S2-F-11's role as the *root cause* that made
  `TestUserFactory` necessary in the first place. So "no finding of that id exists in this build's
  records," as `metadata-builder`'s envelope puts it, is not quite exact: a differently-scoped
  `S4-F-02` does exist, in this very file. Recorded as a citation-quality observation about the
  re-run brief and about the search that produced `metadata-builder`'s envelope text — not resolved in
  either direction here, and this pass does not amend `metadata-builder`'s envelope or `D-M1S03-11`
  (append-only).
- **Alternative rejected:** silently accepting the brief's `S4-F-02` citation as authoritative, or
  omitting the discrepancy from the record now that the member itself is correctly added. Rejected
  because Step 3 of `agents/build-doc-keeper/AGENT.md` records a citation mismatch rather than adopting
  it as fact, and because omitting the caveat above would have hidden that decisions.md already
  contains a real, if differently-scoped, `S4-F-02` entry — exactly the kind of thing a reader
  reconciling the two would need.
- **Grounded in:** `envelopes/M1-S05/2026-09-12T17-03-58Z.json` (`metadata-builder`, § 0 rebuild
  record and `process_observations`); `artefacts/M1-S05/deploy-order.md` § 0;
  `envelopes/M1-S05/2026-09-12T17-09-17Z.json` (`step-tester`); `tests/M1-S05/results.json`;
  `D-M1S03-11` and `D-M1S05-01` (this file).
- **Why this agent does not resolve the citation question further:** per "What This Agent Does NOT
  Do" — it does not touch `plan.json` beyond the single status transition it owns for `M1-S05`, and it
  does not amend another agent's envelope or an earlier `decisions.md` entry, which is append-only.
  Which finding the operator's brief actually intended is left for a human or `milestone-verifier` to
  adjudicate against `reports/MOCK-DEPLOY-M1.md`.
- **Open item:** none blocking. A human reading this entry should treat **S2-F-11** as the grounding
  fact for why `TestUserFactory` exists, and treat `D-M1S03-11`'s `S4-F-02` label as a separate,
  narrower "obligation recorded" finding — not as evidence that the re-run brief's citation was
  correct.
- **Evidence:** `envelopes/M1-S05/2026-09-12T17-03-58Z.json`; `envelopes/M1-S05/2026-09-12T17-09-17Z.json`;
  `artefacts/M1-S05/deploy-order.md` § 0; `tests/M1-S05/results.json`; `decisions.md` `D-M1S03-11`,
  `D-M1S05-01`.

## D-M1S02-07 — Deviation (repair): `Tier2_Webhook_Admin` gains Create/Read on `Tier2_Escalation__e`, closing S2-F-13 — grounded in D10/D14; the checker-coverage gap the tester named is now a WARN rule in `platform-events-apex`'s checker

- **Date:** 2026-09-12
- **Step:** `M1-S02` (`access`), run 3 — a repair after the whole-build mock deploy surfaced a
  finding no step-scoped or build-scoped checker of this step's own could see (`standards/build-
  orchestration.md` § 4 `documented` → `running` recovery transition, the same shape as `D-M1S02-01`'s
  rebuild and `D-M1S03-12`'s)
- **Agent:** `metadata-builder` (run 3, `2026-09-12T17-20-00Z`); confirmed by `step-tester`
  (`2026-09-12T17-21-00Z`, `built → tested`)
- **Kind:** Deviation (repair) — a real change to the shipped permission set, with the persona
  question it turned on recorded as a design-trade-off choice between two ways to grant it.
- **What was recorded:** `reports/MOCK-DEPLOY-M1.md` run 8 —
  `Tier2EscalationServiceTest.ownerChangeToTier2QueueEscalatesAndStamps` passed its webhook-stamp
  assertion but failed its failure-row assertion ("Expected 0, Actual 2"); the operator's
  scratch-copy probe showed both rows carrying `Severity Error — "Tier2_Escalation__e publish
  rejected: Access to entity 'Tier2_Escalation__e' denied"`. Root cause: `Tier2EscalationService`
  (`M1-S03`, decision **D10** — publish-after-commit from the service layer, before the Queueable
  runs) calls `EventBus.publish` as the same async-context user decision **D14** already reasons
  about for this whole step; at API 67.0, `EventBus.publish` runs in user mode by default and
  requires Create on the event object (`skills/apex/platform-events-apex/references/gotchas.md`,
  "API 67.0 Silently Moves Publishing Into User Mode"). No permission set this build ships granted
  anything on `Tier2_Escalation__e`. **The fix:** one new `objectPermissions` row added to the
  existing `Tier2_Webhook_Admin` set — `allowCreate`/`allowRead` both `true`,
  `allowEdit`/`allowDelete`/`viewAllRecords`/`modifyAllRecords` all `false`. `allowRead` rides
  along only because `check_permission_set_architecture.py`'s dependency-chain rule ERRORs
  `allowCreate` without it, not because a publisher needs to query the event back. **Persona
  reasoning — why the existing set, not a new one:** the population that needs to publish is not a
  new persona; it is exactly decision **D14**'s existing assignee set (every user who can escalate a
  Case to `Tier_2_Engineering`, plus the M1-S04 scheduling user), because the publish call and the
  Named-Credential-authenticated webhook call decision **D10** sequences immediately after it both
  run as the same async-context user in the same escalating transaction — the same user `D14`
  already reasons the Named Credential principal access and the `Integration_Failure__c` CRUD in
  this same set must be assigned to. Both cited checkers exited 0 on the repaired set;
  `check-outputs` returned `ok`; `package.xml` and the External Credential / Named Credential files
  are unchanged, so no new manifest member and no change to `M1-S05`.
- **Checker-coverage gap named by the tester, and its status now:** at the time of this repair,
  neither declared checker (`check_apex_named_credentials_patterns.py`,
  `check_permission_set_architecture.py --manifest-dir artefacts`) asserted that a permission set
  granting `EventBus.publish` access actually names the platform event it publishes — the same
  shape of gap `D-M1S02-01` already recorded for the `AuthHeader` `parameterValue` element:
  `step-tester`'s own retest envelope (`2026-09-12T17-21-00Z`) flagged it "Concerning (medium)":
  "S2-F-13 was found only by mock-deploy exercising the Apex test end to end, after three prior
  tester runs had both checkers green on the pre-repair set. A second Apex publish added later with
  no matching `objectPermissions` row would again pass both checkers silently." **This gap is now
  closed at the skill level, verified by reading the checker's current source rather than assumed:**
  `skills/apex/platform-events-apex/scripts/check_platform_events_apex.py` carries rule **R9** —
  "`EventBus.publish(...)` of a `<Name>__e` with no `*.permissionset-meta.xml` or
  `*.profile-meta.xml` under the scanned tree granting `<allowCreate>true` on that `<Name>__e` via
  `<objectPermissions>`" — deliberately `WARN`, not `ERROR`, because a build may grant the
  permission by other means or bypass deliberately with `EventBus.publishWithAccessLevel` (the
  checker's own docstring, and its `--strict` flag to escalate the WARN to a failing exit). This
  checker is cited in this step's `skills[]` as `apex/platform-events-apex` for a different purpose
  (the gotcha, not the rule); the rule itself was not run against this step's artefacts as an
  acceptance test, because the step's declared `acceptance_tests[]` does not name it — recorded here
  as an observation for `milestone-verifier` or a future plan amendment, not acted on by this agent.
- **Alternative rejected:** a new, narrowly-scoped `Tier2_Escalation_Publisher` permission set
  granting only Create on the event. Not chosen: the population is identical to `Tier2_Webhook_Admin`'s
  existing D14 assignees, the publish and the webhook callout run in the same transaction as the same
  user, and a second set would add an assignment operation with no least-privilege benefit — there is
  no user who should hold one grant without the other. Recorded in `artefacts/M1-S02/deploy-order.md`
  § 0b so a future reviewer sees the option was considered, not missed.
- **Grounded in:** `skills/apex/platform-events-apex/references/gotchas.md` ("API 67.0 Silently
  Moves Publishing Into User Mode"); `skills/apex/platform-events-apex/scripts/check_platform_events_apex.py`
  (rule R9, read this pass to confirm it exists before citing it); `skills/admin/permission-set-
  architecture/scripts/check_permission_set_architecture.py` (dependency-chain rule requiring
  `allowRead` alongside `allowCreate`); decisions **D10** and **D14** (`plan.json` → `decisions[]`);
  `artefacts/M1-S02/deploy-order.md` §§ 0b, 4, 6(g).
- **Open item:** none blocking this step. `milestone-verifier` should confirm whether R9 ought to be
  added to this step's or the M1 milestone's declared `acceptance_tests[]` now that it exists, since
  no acceptance test in this plan currently runs it.
- **Evidence:** `envelopes/M1-S02/2026-09-12T17-20-00Z.json` (`metadata-builder` repair envelope,
  `process_observations` "concerning"/"high"); `envelopes/M1-S02/2026-09-12T17-21-00Z.json`
  (`step-tester` retest, `process_observations` "concerning"/"medium"); `reports/MOCK-DEPLOY-M1.md`
  run 8; `tests/M1-S02/results.json` (`skipped_manual[0]` re-test note); `artefacts/M1-S02/deploy-
  order.md` § 0b.

## D-M1S03-13 — Deviation (repair): `Tier2WebhookFinalizer`'s retry/abandon/update branches now unit-tested via a customer-implemented `FinalizerContext` stub — UNVERIFIED at run 6, confirmed by the org at run 7

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`), runs 6–7 — two consecutive § 4 test-only repairs
  (`documented` → `running` → `built`, twice, then `tested` once at run 8's retest)
- **Agent:** `apex-builder` (run 6, `2026-09-12T17-40-00Z`, findings `S6-F-01`/`S6-F-02`; run 7,
  `2026-09-12T17-50-00Z`, findings `S7-F-01`/`S7-F-02`); confirmed by `step-tester`
  (`2026-09-12T18-08-27Z`, `built → tested`)
- **Kind:** Deviation, per `agents/build-doc-keeper/AGENT.md` Step 3 — `Tier2WebhookFinalizer` had no
  direct unit test before run 6; the repair adds one via a technique (a hand-built class implementing
  `System.FinalizerContext`) not previously used or confirmed anywhere in this repo's corpus, a real
  change from what was built before, with its reason and its later confirmation both stated here.
- **What was recorded:** `reports/MOCK-DEPLOY-M1.md` run 9 (`--test-level RunSpecifiedTests`) found
  `Tier2WebhookFinalizer` under the 75% coverage floor (`S2-F-14`, 63 of 76 lines uncovered) after
  run 5's repair. Run 6 added `artefacts/M1-S03/classes/Tier2WebhookFinalizerTest.cls` (+
  `-meta.xml`), 5 methods calling `Tier2WebhookFinalizer.execute(FinalizerContext)` directly against
  a private inner `StubFinalizerContext` implementing `System.FinalizerContext` — a technique the
  run's own envelope flagged P0/UNVERIFIED (`S6-F-02`) because no skill under `skills/apex/` states
  whether a customer class may implement `System.FinalizerContext`, and
  `skills/apex/apex-transaction-finalizers/references/code-examples.md` solves the identical
  test-design problem with a different technique (a `@TestVisible` seam) that this run could not use
  without editing the shipped class. Run 7's org evidence (`reports/MOCK-DEPLOY-M1.md` run 10)
  settled the question: `Tier2WebhookFinalizerTest.cls` compiled and 33 of 34 methods passed at
  86.8% coverage, confirming `System.FinalizerContext` is customer-implementable at API 67.0 in this
  org (`S7-F-02`). The one failure
  (`transientFailureBelowAttemptCeilingIsRecordedRetryingAndReEnqueuedOnce`) was a separate, unrelated
  defect: the Finalizer's own re-enqueued job ran to completion inside the test method regardless of
  `Test.startTest()`/`Test.stopTest()` wrapping, and with no `HttpCalloutMock` registered anywhere in
  that method its callout threw and was re-thrown. Run 7 fixed it with one line —
  `Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator().withResponse(200, OK_BODY))`
  immediately before the `finalizer.execute(...)` call, plus a new `OK_BODY` constant — no assertion
  changed. `reports/MOCK-DEPLOY-M1.md` run 12 (SOURCE mode, `--test-level RunSpecifiedTests`) later
  confirmed 37/37 tests passing at 89.9% coverage with no coverage warnings.
- **Alternative rejected:** (run 6) driving the Finalizer's branches by letting a real Queueable throw
  inside `Test.stopTest()`, which `artefacts/M1-S03/deploy-order.md` § 5 item 3 already recorded, from
  this same build, fails the test method outright; (run 7) asserting the enqueue without forcing
  execution, an option no longer available once the org's own run 10 result showed the re-enqueued job
  runs to completion regardless of how the call is wrapped.
- **Skill gap:** `skills/apex/apex-transaction-finalizers` does not document that a customer class may
  implement `System.FinalizerContext` directly for isolated Finalizer unit tests, as an alternative to
  the `@TestVisible` seam it currently shows exclusively — now org-confirmed here, per `S7-F-02`'s own
  recommendation to record it there once known.
- **Grounded in:** `skills/apex/apex-transaction-finalizers/references/code-examples.md` (the
  identical test-design problem, solved there by a different, here-unusable technique — the
  direct-implementation technique itself is not documented by any skill, hence the initial UNVERIFIED
  tag); `skills/apex/apex-queueable-patterns/SKILL.md` (`FinalizerContext`'s four documented methods,
  no `getJobId()`); `skills/apex/callouts-and-http-integrations` and `skills/apex/apex-mocking-and-
  stubs` (the `Test.setMock` registration rule behind the run-7 fix);
  `templates/apex/tests/MockHttpResponseGenerator.cls` (`withResponse(200, body)`).
- **Evidence:** `envelopes/M1-S03/2026-09-12T17-40-00Z.json` → `findings[0]` (`S6-F-01`) and
  `findings[1]` (`S6-F-02`); `envelopes/M1-S03/2026-09-12T17-50-00Z.json` → `findings[0]` (`S7-F-01`)
  and `findings[1]` (`S7-F-02`); `envelopes/M1-S03/2026-09-12T18-08-27Z.json` (step-tester retest);
  `reports/MOCK-DEPLOY-M1.md` runs 9, 10 and 12; `artefacts/M1-S03/deploy-order.md` §§ 0d–0e;
  `tests/M1-S03/results.json`.

## D-M1S03-14 — Deviation (repair): two branch tests close `Tier2EscalationService`'s per-class coverage gap the aggregate floor had been masking (`S2-F-16`)

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`), run 8 — a third § 4 test-only repair
  (`documented` → `running` → `built` → `tested`)
- **Agent:** `apex-builder` (run 8, `2026-09-12T18-05-00Z`, finding `S8-F-01`); confirmed by
  `step-tester` (`2026-09-12T18-08-27Z`, `built → tested`) and, at the build level, by
  `reports/MOCK-DEPLOY-M1.md` run 12 (37/37 tests, 89.9% coverage, no coverage warnings)
- **Kind:** Deviation, per `agents/build-doc-keeper/AGENT.md` Step 3 — Apex's `RunSpecifiedTests`
  coverage floor is enforced **per class**, not only in aggregate; the repair adds branch coverage
  the previous two repairs' aggregate-level view could not see was still missing, a real change from
  what was built before, with its reason stated in the finding it closes.
- **What was recorded:** run 11 (`reports/MOCK-DEPLOY-M1.md`) showed 35/35 tests passing at 86.2%
  aggregate coverage yet still `Failed`, on a per-class floor: `Tier2EscalationService` individually
  at 53.659%. The 19 uncovered lines (`reports/mock-deploy/2026-09-12T17-17-07Z/result.json`'s
  `codeCoverage` array, recorded at run 9) resolved to exactly two branches unreachable from the
  trigger-driven path every existing test in `Tier2EscalationServiceTest` used: the empty/null-input
  early return (line 44) and the `EventBus.publish()` rejection path — building an
  `Integration_Failure__c` row, the conditional insert, and the whole `errorText()` helper (lines
  84–96, 106, 119–127). Two methods were added to `Tier2EscalationServiceTest.cls`, both calling
  `Tier2EscalationService.escalate(List<Case>)` directly: `escalateWithNoCasesReturnsImmediately`
  (line 44) and `escalateWithAMissingCaseNumberWritesAPublishFailureRowAndStillEnqueuesTheJob`, which
  forces a deterministic publish rejection via `Tier2_Escalation__e.Case_Number__c`'s `required=true`
  constraint (`M1-S01`) rather than `S2-F-13`'s FLS-based mechanism, which the current, merged
  permission set can no longer reproduce. Both new methods register a 2xx
  `MockHttpResponseGenerator` before calling `escalate()`, applying `D-M1S03-13`'s lesson
  proactively rather than reactively. No shipped class, no other test method and no other file
  changed.
- **Alternative rejected:** reproducing `S2-F-13`'s exact FLS-based rejection mechanism (a user
  lacking `Tier2_Escalation__e` Create while holding `Integration_Failure__c` Create). Rejected
  because `Tier2_Webhook_Admin` now bundles both grants — that asymmetry existed only because the two
  grants were added at different times, and `S2-F-13`'s own fix closed the gap — so only a bespoke,
  test-local `PermissionSet` built via DML could still reproduce it, not attempted here; the
  required-field mechanism is a different and, per the finding, arguably more robust trigger for the
  identical `sr.isSuccess() == false` branch.
- **Grounded in:**
  `artefacts/M1-S01/objects/Tier2_Escalation__e/Tier2_Escalation__e.object-meta.xml`
  (`Case_Number__c` `required=true`);
  `artefacts/M1-S02/permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml` (confirming both
  grants are bundled in one permission set); `templates/apex/tests/MockHttpResponseGenerator.cls`
  (`withResponse(200, body)`).
- **Evidence:** `envelopes/M1-S03/2026-09-12T18-05-00Z.json` → `findings[0]` (`S8-F-01`) and
  `findings[1]` (`S8-F-02`); `envelopes/M1-S03/2026-09-12T18-08-27Z.json` (step-tester retest);
  `reports/MOCK-DEPLOY-M1.md` runs 11–12; `artefacts/M1-S03/deploy-order.md` § 0f;
  `tests/M1-S03/results.json`.

## D-M1S03-15 — Accepted: `Tier2WebhookFinalizerTest` is a new `ApexClass` member `M1-S05`'s manifest must add — handled in a parallel `M1-S05` re-run, not this pass

- **Date:** 2026-09-12
- **Step:** `M1-S03` (`automation`), run 6 repair; the resolution is `M1-S05`'s (`docs`) to apply
- **Agent:** `apex-builder` (run 6, `2026-09-12T17-40-00Z`, finding `S6-F-04`); `step-tester`
  (`2026-09-12T18-08-27Z`) confirms the gap is still open as of the `tested` state this pass documents
- **Kind:** Design trade-off / obligation, the same shape `D-M1S03-11` already records for
  `TestUserFactory` from this same step — a new file this step ships that another step's manifest
  must learn about, recorded on the producing step because that is the artefact a reader of this step
  consults first.
- **What was recorded:** `Tier2WebhookFinalizerTest` is a fourteenth `ApexClass` this build ships
  from `M1-S03` (joining `TestUserFactory`, `D-M1S03-11`, already closed). `artefacts/M1-S05/
  package.xml` does not name it as of the state this pass reads
  (`envelopes/M1-S03/2026-09-12T18-08-27Z.json` → `extensions.unresolved_from_prior_runs`). Per
  `standards/build-orchestration.md` § 5 **The Apex exception**, this step declares no `package.xml`
  of its own — `M1-S05` (`metadata-builder`, `depends_on` this step) carries its
  `ApexClass`/`ApexTrigger` members instead, and this step's own `manifest` acceptance test correctly
  records skipped-not-applicable, naming `M1-S05`.
- **Alternative rejected:** writing a local `package.xml` under `artefacts/M1-S03/` so the new class
  would have manifest coverage immediately. Rejected for the same reason `D-M1S03-11` rejects it — it
  would contradict this step's own recorded Apex exception and duplicate what `M1-S05` exists to
  aggregate.
- **Grounded in:** `standards/build-orchestration.md` § 4 condition 2, § 5 **The Apex exception**;
  `D-M1S03-11` (the identical pattern already applied to `TestUserFactory` from this step).
- **Open item:** a parallel `M1-S05` re-run (`metadata-builder`) is already in progress, outside this
  pass, to add both `TestUserFactory` and `Tier2WebhookFinalizerTest` as `ApexClass` members — out of
  scope for this `M1-S03`-only documentation pass. Per this pass's own instructions, no file under
  `artefacts/M1-S05/` or any of `M1-S05`'s own workbook/traceability rows is touched here; a reader
  should look to `M1-S05`'s own documentation pass for that resolution rather than to this entry.
- **Evidence:** `envelopes/M1-S03/2026-09-12T17-40-00Z.json` → `findings[3]` (`S6-F-04`);
  `envelopes/M1-S03/2026-09-12T18-08-27Z.json` → `process_observations` (`suggested_followup`,
  `metadata-builder`) and `extensions.unresolved_from_prior_runs`; `artefacts/M1-S03/deploy-order.md`
  § 0d; `D-M1S03-11`.

## D-M1S05-07 — Accepted: `Tier2WebhookFinalizerTest` added as a fifteenth `ApexClass` member (34→35), closing `S2-F-14`, discharging `D-M1S03-15`

- **Date:** 2026-09-12
- **Step:** `M1-S05` (`docs`), run 3 (`documented` → `running` → `built` → `tested`, a § 4 test-only-
  adjacent rebuild)
- **Agent:** `metadata-builder` (run 3, `2026-09-12T18-18-48Z`); confirmed by `step-tester`
  (`2026-09-12T18-26-05Z`)
- **Kind:** Deviation, discharging the obligation `D-M1S03-15` already recorded — the same shape
  `D-M1S05-06` applies to `TestUserFactory`'s addition one run earlier.
- **What was recorded:** `artefacts/M1-S05/package.xml` (the build-level manifest) was regenerated to
  add `classes/Tier2WebhookFinalizerTest.cls` as a new `ApexClass` member — 14 → **15** `ApexClass`
  members, 34 → **35** total. This closes the obligation `D-M1S03-15` already recorded (that
  `M1-S05`'s manifest must add `Tier2WebhookFinalizerTest` once `M1-S03`'s run-6 repair shipped it)
  and traces to the underlying root cause named in finding **S2-F-14**
  (`reports/MOCK-DEPLOY-M1.md` run 9): `Tier2WebhookFinalizer` sat under the platform's 75% coverage
  floor (63 of 76 lines uncovered) because the finalizer's own retry/abandon/permanent-failure
  branches were exercised only through the Queueable, never through `execute(FinalizerContext)`
  directly; `M1-S03`'s repair (`artefacts/M1-S03/deploy-order.md` § 0d) added
  `Tier2WebhookFinalizerTest.cls` to close the gap, a test-only addition with no shipped-code change.
  Only the `ApexClass` `<types>` block changed — one `<members>Tier2WebhookFinalizerTest</members>`
  line inserted alphabetically between `Tier2WebhookFinalizer` and `Tier2WebhookQueueable`; no other
  block (`CustomObject`, `CustomField`, `ExternalCredential`, `NamedCredential`, `ApexTrigger`,
  `PermissionSet`) changed. Verified this run by a bidirectional 35-member/54-file manifest check
  over the whole `artefacts/M1-S0[1-4]/` tree — no member without a file, no file without a member,
  no duplicate, no wildcard.
- **Alternative rejected:** waiting for a later, combined manifest re-run to add both
  `Tier2WebhookFinalizerTest` and any further test-repair members in one pass. Rejected because
  `D-M1S03-15` already named this as a standing obligation on `M1-S05` once `M1-S03`'s run-6 repair
  landed, and `standards/build-orchestration.md` § 4's `documented` → `running` recovery transition
  exists precisely so a step is re-run as soon as the obligation it owes is known, rather than batched
  against an unrelated future change.
- **Grounded in:** `envelopes/M1-S05/2026-09-12T18-18-48Z.json` (`metadata-builder`, § 0a rebuild
  record and `process_observations`); `artefacts/M1-S05/deploy-order.md` § 0a;
  `envelopes/M1-S05/2026-09-12T18-26-05Z.json` (`step-tester`); `tests/M1-S05/results.json`;
  `D-M1S03-15` and `D-M1S05-06` (this file); `reports/MOCK-DEPLOY-M1.md` runs 9–10.
- **Open item:** none blocking for this step. `reports/MILESTONE-M1-package.xml` (the verifier's
  merged milestone manifest) still carries 33 members and names neither `TestUserFactory` nor
  `Tier2WebhookFinalizerTest`, so it is now stale against this step's own `artefacts/M1-S05/
  package.xml` (35 members) by two rebuilds of this step (33→34, 34→35) — recorded as a Process
  Observation on this run rather than as a decision, since it is `milestone-verifier`'s file to
  regenerate, not this agent's to edit.
- **Evidence:** `envelopes/M1-S05/2026-09-12T18-18-48Z.json`;
  `envelopes/M1-S05/2026-09-12T18-26-05Z.json`; `artefacts/M1-S05/deploy-order.md` § 0a;
  `tests/M1-S05/results.json`; `reports/MOCK-DEPLOY-M1.md` runs 9, 10, 13; `decisions.md`
  `D-M1S03-15`, `D-M1S05-06`.
