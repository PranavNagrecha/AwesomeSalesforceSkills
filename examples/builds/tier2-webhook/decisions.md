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
