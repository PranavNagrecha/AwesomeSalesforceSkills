# Milestone M1 — acceptance report

Build `tier2-webhook` · `scale: feature` · `build_mode: design-only` · plan v2, status `approved`
Written by `milestone-verifier` (`agents/milestone-verifier/AGENT.md`), run `2026-09-12T12-47-33Z`.
**Nothing was deployed. No `sf` command and no `mock_deploy.py` was run by this agent. No gate was approved.**

> **Verdict: `ready-with-findings`.** Every cross-step reference resolves, the merged manifest is
> byte-equivalent to the build-level one, all three declared checker acceptance tests exit 0, and no
> step is blocked. Eight decisions are put to the human below, plus five findings this run raised.
> Recording the verdict as `verified` is a statement about what the checks found — the `milestone:M1`
> gate stays `pending` until a human writes it.

---

## 1. Summary

| | |
|---|---|
| Milestone | `M1` — Tier 2 escalation notification, event and failure record, deploy-ready |
| Steps | 5, **all `documented`**; none `blocked`; predecessor gate — none (M1 is the first milestone), `plan` gate `approved` |
| Cross-step references resolved | **46 of 46** in-scope (12 PS field grants + 1 PS object grant + 1 principal grant + 18 Apex custom symbols + 5 event payload fields + 7 restricted picklist literals + 1 `callout:` name + 1 NC→EC link); **0 unresolved**; 4 external prerequisites unresolvable by design (§ 3.2) |
| Deployment order | consistent in the artefacts; **1 contradiction in the plan's own step input** (§ 4) |
| Merged manifest | 7 types / **33 members** / `<version>67.0</version>` — **no drift** vs `artefacts/M1-S05/package.xml` (§ 5) |
| Acceptance tests | 3 declared `checker` tests ran, **3 exit 0**; 1 `manual` collected to § 7 |
| Confidence | **MEDIUM** (§ 9) |

**Findings by severity:** P1 × 1 · P2 × 2 · INFO × 2 (this run) — plus 8 previously-recorded items
carried to the gate as decisions (§ 8).

---

## 2. Steps and artefacts

| Step | Type | Agent | Status | Artefacts | Builds |
|---|---|---|---|---|---|
| `M1-S01` | `object-model` | `metadata-builder` | documented | `Integration_Failure__c` + 12 fields, `Case.Tier2_Notified_At__c`, `Tier2_Escalation__e` + 5 inline payload fields, `package.xml`, `deploy-order.md` | 1 |
| `M1-S02` | `access` | `metadata-builder` | documented (`step:M1-S02` gate **approved**, re-signed after the S2-F-02 amendment) | `OnCall_Tool_EC`, `OnCall_Tool`, `Tier2_Webhook_Admin`, `package.xml`, `deploy-order.md` | 2 |
| `M1-S03` | `automation` | `apex-builder` | documented | 2 triggers + meta, 10 classes + meta (incl. verbatim `TestDataFactory` and `MockHttpResponseGenerator`), `deploy-order.md` | 3 |
| `M1-S04` | `automation` | `apex-builder` | documented | 3 classes + meta + verbatim `TestDataFactory`, `deploy-order.md` | 2 |
| `M1-S05` | `docs` | `metadata-builder` | documented | build-level `package.xml` (33 members), `deploy-order.md` | 1 |

**No blocked steps.** 50 component files under `artefacts/`; 8 non-component files (5 `deploy-order.md`,
3 per-step `package.xml`), correctly outside every `<types>` block.

---

## 3. Reference resolution

Grep-and-parse resolution over the milestone's artefacts. Reference classes in
`agents/milestone-verifier/AGENT.md` Step 3 that this milestone contains no instance of are marked
n/a so the boundary of the check is visible rather than inferred from silence.

| Reference class | Instances | Resolved in M1 | Unresolved | Notes |
|---|---|---|---|---|
| Permission-set field grants (`<fieldPermissions><field>`) | 12 | 12 | 0 | 11 `Integration_Failure__c` fields + `Case.Tier2_Notified_At__c`; **`Status__c` correctly excluded** — it is `<required>true</required>` and the platform refuses FLS on a required field (D-M1S01-02) |
| Permission-set object grants (`<objectPermissions><object>`) | 1 | 1 | 0 | `Integration_Failure__c`. **No `Case` row** — assumption A14, deliberate (§ 8 item 3) |
| External-credential principal grant | 1 | 1 | 0 | `OnCall_Tool_EC-OnCallToolNamedPrincipal` = EC file stem + `-` + `NamedPrincipal` `parameterName`. Dash-joined, matches both halves |
| Apex → custom object / field symbols | 18 distinct | 18 | 0 | Every `*__c` / `*__e` token in all 15 Apex files, tests included, resolves to an `M1-S01` artefact |
| Platform-event payload fields written by Apex | 5 | 5 | 0 | `Case_Number__c`, `Subject__c`, `Severity__c`, `Case_Link__c`, `Escalated_At__c` — **⊆ the 5 fields the event defines**; no field written that the event lacks, none defined that Apex never writes |
| Restricted picklist literals written by Apex | 7 | 7 | 0 | `Status__c` ← {New, Retrying, Resent, Resolved, Abandoned}; `Severity__c` ← {Error, Warning}. **Exactly the restricted value sets**, no eighth literal anywhere |
| `callout:` name → Named Credential | 1 | 1 | 0 | `callout:OnCall_Tool` (composed from `NAMED_CREDENTIAL = 'OnCall_Tool'`) ↔ `OnCall_Tool.namedCredential-meta.xml`. No path appended; the credential's `Url` is the full endpoint |
| Named Credential → External Credential | 1 | 1 | 0 | `<externalCredential>OnCall_Tool_EC</externalCredential>` inside the `Authentication` parameter (correct nesting — not a top-level field) |
| Validation-rule field references | 0 | — | — | n/a — this milestone ships no validation rule |
| Assignment-rule criteria | 0 | — | — | n/a — no assignment rule; routing is Apex |
| Flow field references | 0 | — | — | n/a — **no Flow in this milestone.** The automation is Apex, so `skills/devops/flow-deployment-activation-ordering` applies only by analogy — see § 4 |
| Entitlement-process milestones / business hours | 0 | — | — | n/a |
| Layout / path assignments | 0 | — | — | n/a — no `ui` step in M1 |

### 3.1 The `$Credential` formula ↔ External Credential developer name

`{!$Credential.OnCall_Tool_EC.ApiKey}` in `OnCall_Tool_EC.externalCredential-meta.xml`:

- **First segment resolves.** `OnCall_Tool_EC` matches the External Credential's developer name — the
  file stem, which is the `fullName` for a file-based metadata type (the file declares no
  `<fullName>` element, as expected).
- **Second segment resolves to nothing in metadata, and cannot.** `ApiKey` names an authentication
  parameter entered in Setup against the principal after deploy. Nothing in this build, or any
  earlier milestone, defines it. That is by design (no secret in the repo) and the deploy-order note
  makes the name load-bearing: a parameter named anything else leaves the header empty and every
  callout returns 401 (`artefacts/M1-S05/deploy-order.md` § 3 step 2).
- **The grammar itself is still UNVERIFIED.** Mock-deploy run 1 established the element is *required*;
  run 2 and run 5 established the formula *parses on deploy*. Neither establishes that it *resolves
  to a non-empty header at run time* — a formula that parses and resolves to empty deploys perfectly
  and 401s on every callout. See § 8 item 6.

### 3.2 The four references that resolve to nothing — external prerequisites, not defects

Each is out of the manifest on purpose and is named in `artefacts/M1-S05/deploy-order.md` § 2:

| # | Reference | Made by | Predicted failure if absent |
|---|---|---|---|
| 1 | Queue `Tier_2_Engineering`, resolved by `DeveloperName` | `CaseTriggerHandler.queueId()` | No deploy error. `queueId()` returns `null`, the handler logs at `LoggingLevel.ERROR` and returns — **escalation becomes silently impossible** (A8) |
| 2 | Org-wide email address `support-noreply@acme.example` | `Tier2ChannelHealthQueueable.sendAlert()` | No deploy error. The query returns empty, the job logs and sends nothing; it never falls back to the running user (A4) |
| 3 | Read access on `PermissionSetAssignment` for the scheduling user | `Tier2ChannelHealthQueueable.resolveRecipients()` | No deploy error. Returns empty → every run takes the gap path (§ 8 item 3) |
| 4 | No pre-existing `after update` trigger named `CaseTrigger` on `Case` | the deploy itself | **Deploy error.** A second trigger of the same name cannot be created. Unasked in all 45 clarifications |

None is an unresolved reference in the § 3 sense — they resolve against the target org, not against
this build — but all four are why confidence is MEDIUM rather than HIGH (§ 9).

---

## 4. Deployment order

Canonical sequence from `agents/milestone-verifier/AGENT.md` Step 4: objects → fields → picklists →
record types → layouts → permission sets → sharing → automation → routing → SLA.

At `scale: feature` the workbook is optional and this build skipped it, so there is no workbook row
carrying a recorded position. The position of record is each step's `deploy-order.md`, compiled in
`artefacts/M1-S05/deploy-order.md` § 2. (That substitution is a § 3.1 support gap — § 11.)

| Group | Components | Step | Agrees with the sequence? |
|---|---|---|---|
| 1 | `CustomObject` ×2, `CustomField` ×13 | M1-S01 | ✅ objects then fields, first |
| 2 | `ExternalCredential` → `NamedCredential` | M1-S02 | ✅ EC before NC (the NC's `Authentication` parameter names the EC). No canonical slot for credentials; independent of group 1 |
| 3 | `ApexClass` ×13, `ApexTrigger` ×2 | M1-S03, M1-S04 | ⚠️ **automation before permission sets**, where the canonical list puts permission sets first |
| 4 | `PermissionSet` `Tier2_Webhook_Admin` | M1-S02 | ⚠️ last |

**Groups 3/4 invert the canonical order and it is safe here — stated rather than assumed.**
`Tier2_Webhook_Admin` carries **no `classAccesses` element**, so it references no Apex. Its only
forward references are the 12 fields and 1 object of group 1 and the principal of group 2, both of
which precede it. There is no dependency running backwards through the artefacts' order.

**One backwards dependency exists, and it is in `plan.json`, not in the artefacts.**
`steps[M1-S05].inputs.deploy_order` reads *"ExternalCredential, NamedCredential, PermissionSet, then
the object and field metadata, then the Apex"* — placing the permission set **before the twelve
fields it grants**. Deployed in that order as separate requests it is exactly the case
`skills/devops/permission-set-deployment-ordering` exists to catch, and the deploy-time error per
`skills/devops/deployment-error-diagnosis` is *"Field-level security cannot be set on a non-existent
field"* / `INVALID_CROSS_REFERENCE_KEY`. The compiled note corrects it (D-M1S05-02) and the single
combined request the merged manifest deploys makes the difference invisible — the Metadata API
processes objects before permission sets inside one request. **Not silently corrected:** `amend-step`
is refused once a step has left `pending`, so this is a human's to amend or to accept as superseded.

**The Flow-ordering check is n/a, and its Apex analogue is not.** No Flow is in this milestone. The
equivalent arrival-state question is what `<status>` the two triggers carry — and both
`CaseTrigger.trigger-meta.xml` and `IntegrationFailureTrigger.trigger-meta.xml` declare
`<status>Active</status>`. **The feature goes live the moment the deploy lands**; there is no
deploy-dark step, and with no kill switch (§ 8 item 1) no way to turn it off afterwards short of a
second deploy. See finding **S2-F-08**.

**Superseded per-step guidance, deliberately.** M1-S01 § 3 and M1-S02 § 3 both say "do not deploy
this step in the same request as the other"; the merged manifest does. `artefacts/M1-S05/deploy-order.md`
§ 2 item 2 carries the reasoning — Gotcha 10's hazard is a *retrieve* rewriting permission-set files,
nothing here was retrieved, the permission set is hand-authored and new, and the access change is the
point of this deployment, which is Gotcha 10's own carve-out. Accepted as reasoned, not flagged.

---

## 5. Merged manifest

**`reports/MILESTONE-M1-package.xml`** — union of the three step-level manifests (`M1-S01`, `M1-S02`,
`M1-S05`), members sorted within each `<types>` block.

| Type | Members |
|---|---|
| `CustomObject` | 2 |
| `CustomField` | 13 |
| `ExternalCredential` | 1 |
| `NamedCredential` | 1 |
| `PermissionSet` | 1 |
| `ApexClass` | 13 |
| `ApexTrigger` | 2 |
| **Total** | **33** |

- **Version: no conflict.** All three step manifests declare `67.0`; one `<version>67.0</version>` in
  the merged file. (`REFUSAL_NEEDS_HUMAN_REVIEW` was not triggered.)
- **Drift vs `artefacts/M1-S05/package.xml`: none.** Type-for-type and member-for-member identical,
  including the version. The two files differ only in `<types>` block order, which carries no
  documented deployment semantics (M1-S05 note § 5 item 1).
- **Member collisions: 18, all resolved, none a defect.** Every `M1-S01` member (15) and every
  `M1-S02` member (3) also appears in `M1-S05`'s manifest — that is what a build-level aggregating
  step *is*. Each collision is the same member name backed by the same single file, so the union is
  unambiguous.
- **`TestDataFactory` appears once.** M1-S03 and M1-S04 each ship a copy; both are byte-identical to
  each other and to `templates/apex/tests/TestDataFactory.cls` (sha256 `2f87c8c3…`, meta XML
  `a242f6e2…`) — re-hashed by this run, not taken from the note. One `ApexClass` member is correct.
- **Two-way consistency: clean.** All 50 component files reach a `<types>` block; all 33 members have
  a backing file. The 8 files reaching none are the 5 `deploy-order.md` notes and the 3 per-step
  `package.xml` fragments — notes and fragments, not components.
- **Manifest grammar** per `skills/devops/metadata-api-retrieve-deploy`: explicit members only (no
  wildcards), `CustomField` object-qualified, `<version>` present, no `destructiveChanges*.xml`
  (this build only adds). `Tier2_Escalation__e`'s 5 payload fields are declared inline in the object
  file and are correctly **not** separate `CustomField` members — hence 13, not 18.

---

## 6. Acceptance-test results

Run verbatim from the build directory (`skills` symlink present), deny-list cleared, nothing rewritten.

| # | Type | Command | Exit | Verdict |
|---|---|---|---|---|
| 1 | `checker` | `python3 skills/admin/permission-set-architecture/scripts/check_permission_set_architecture.py --manifest-dir artefacts` | **0** | **pass** — 1 WARN: `modifyAllRecords=true` on `Integration_Failure__c`, the sharing bypass decision D12 makes deliberate. WARN does not affect the exit code |
| 2 | `checker` | `python3 skills/apex/apex-named-credentials-patterns/scripts/check_apex_named_credentials_patterns.py --manifest-dir artefacts` | **0** | **pass** — `OK: no Named Credential findings.` Every `callout:` in M1-S03's Apex resolved against M1-S02's credential |
| 3 | `checker` | `python3 skills/admin/change-management-and-deployment/scripts/check_deployment_manifest.py --manifest-dir artefacts` | **0** | **pass** — score 80, 4 WARN, **0 blocking**. 58 manifest/metadata files scanned |
| 4 | `manual` | — | — | **collected to § 7**, not ticked by this agent |

All three declared checkers exist on disk and ran; none was skipped, none blocked.
**Test 3's declared description says "exactly those two WARN findings" and the run produced four** —
see finding **S2-F-09**. The exit code is unaffected.

**Not a declared test, run as verification support:**
`python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root <repo>`
→ `16 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 0 warning(s)` (exit 0).
Read-only; run to state § 10 from evidence rather than from the file's own prose.

---

## 7. Manual checklist for the human at the G3 gate

Six lines. Each is tickable from the artefacts alone — no org needed for 1–5; line 6 is the
cross-step read. **None was ticked by this agent.** Form checked against
`skills/admin/uat-and-acceptance-criteria` § *Acceptance Criteria Format*: every line names a
precondition, an action and an observable outcome.

| # | From | The human does | Ticks when |
|---|---|---|---|
| 1 | `M1-S01` | Opens `artefacts/M1-S01/objects/Integration_Failure__c/fields/Status__c.field-meta.xml` and `Severity__c.field-meta.xml` | Both value sets are `<restricted>true</restricted>` and hold exactly `New, Retrying, Resent, Resolved, Abandoned` and exactly `Error, Warning` — character for character with the Apex constants |
| 2 | `M1-S02` | Opens the three files under `artefacts/M1-S02/` | (a) `externalCredentialPrincipal` reads exactly `OnCall_Tool_EC-OnCallToolNamedPrincipal`; (b) no credential value appears in any of the three files; (c) `generateAuthorizationHeader` is explicitly `false`; (d) `fieldPermissions` carries `Case.Tier2_Notified_At__c` readable+editable and every `Integration_Failure__c` field bar `Status__c`; (e) **a named person accepts the D14 assignee set** (wider than the three admins Q19 names) or sends D14 back; (f) the `X-API-Key` formula is flagged for confirmation before deploy |
| 3 | `M1-S03` | Opens `Tier2EscalationService.cls` and `Tier2WebhookQueueable.cls` | (a) `EventBus.publish` is in the **service**, in the escalating transaction, its `List<Database.SaveResult>` inspected and a failure writing an `Integration_Failure__c` row — not discarded, not moved into the Queueable; (b) no class sets an `X-API-Key` or `Authorization` header, reads a credential value, or names a literal hostname, and every endpoint is `callout:OnCall_Tool` |
| 4 | `M1-S04` | Opens `Tier2ChannelHealthSchedulable.cls` and `Tier2ChannelHealthQueueable.cls` | (a) the CRON literal is hourly and `execute()` does nothing but enqueue; (b) the two thresholds are Q24's — more than three failures in an hour, or no success in 24 h while escalations exist; (c) the sender is `support-noreply@acme.example` **and a named person confirms that org-wide address is already verified in the target org** |
| 5 | `M1-S05` | Opens `artefacts/M1-S05/deploy-order.md` | § 3 lists the five manual steps no deploy performs, each with an owner and a timing, and § 7's `mock_deploy.py` line is written as text for a human rather than as anything an agent executes |
| 6 | **milestone** | Opens `artefacts/M1-S05/deploy-order.md` alongside all five steps' artefacts | (a) the order runs ExternalCredential → NamedCredential → PermissionSet → object/field metadata → Apex **as the note's § 2 table states it, not as the plan's step input states it** (§ 4); (b) the build-level `package.xml` names every Apex member from M1-S03/M1-S04 and every metadata member from M1-S01/M1-S02, no member without a file and no file without a member; (c) the note states the two steps no deploy performs — a human entering the API key against the `OnCall_Tool_EC` principal, and assigning `Tier2_Webhook_Admin` to the D14 assignee set |

**Every line states an observable outcome.** No line is listed with an undefined tick condition.
**Line 6(a) needs care:** as written in `plan.json` the milestone test asks the reviewer to confirm
the order *the plan's own stale step input contradicts*. Read § 4 of this report first.

---

## 8. The eight decision items — put to the human together

Each already exists in the build's record; none is renumbered here. My recommendation follows each.

| # | Item | Recorded as | Severity | Recommendation |
|---|---|---|---|---|
| 1 | **No trigger kill switch (remedy B).** `TriggerHandler`/`TriggerControl`/`Trigger_Setting__mdt` were dropped because no step could ship the closure. A bulk load reassigning Case ownership escalates **every** affected Case with no bypass; turning the feature off is a deployment, not a checkbox. Both triggers arrive `Active` | `S3-F-01` (P1), `D-M1S03-04`, M1-S03 note § 4 | **P1** | **Accept for this milestone, schedule the Apex-foundations step before go-live.** It is not a milestone defect — it is a re-plan, and the same step that restores the switch also removes the `TestDataFactory` duplication. Until it exists, gate the first deploy on "no bulk Case-owner load is scheduled" and put `CaseTrigger` `<status>Inactive</status>` in the rollback runbook |
| 2 | **`Tier2_Escalation__e.Severity__c ← Case.Priority` is UNVERIFIED.** No clarification maps the event's severity to a Case field; `Priority` is the only severity-shaped field this build has seen. Q11's answer says "a Severity 1 escalation", which is *not* the shape of standard `Case.Priority` (High/Medium/Low) — the org may hold a severity field this build never saw | `S3-F-02` (P2), `D-M1S03-05`, inline `// UNVERIFIED` at the assignment | **P2** | **Ask the dashboard team before UAT, not at the gate.** A wrong value here is silently wrong, not loud — the deploy is clean and the dashboard shows plausible garbage. One question to one team closes it; approving M1 without the answer is fine as long as the question is owned |
| 3 | **The scheduling user's `PermissionSetAssignment` read and Case record visibility.** `resolveRecipients()` queries `PermissionSetAssignment` in user mode; `Tier2_Webhook_Admin` grants nothing on it. Separately, the set deliberately carries **no** `Case` `objectPermissions` row (A14), so `SELECT COUNT() FROM Case WHERE Tier2_Notified_At__c >= …` returns only Cases that user can see | `D-M1S04-03`, M1-S04 note § 4 items 1 and 3; prerequisite 4 in M1-S05 § 2 | **P2** | **Confirm both before the first scheduled run — this is the item most likely to bite quietly.** Missing PSA read → empty roster → every run takes the gap path (item 4). Insufficient Case visibility → `successesLastDay` reads 0 → the job raises a **false** dead-channel alert. Neither produces a deploy error. Name the scheduling user at the gate and check their profile |
| 4 | **The gap-row self-alert loop, and no suppression.** `recordRecipientGap()` writes an `Integration_Failure__c` row of Severity `Warning`; the threshold queries count rows with **no Severity filter**. An org with no active assignee accrues one self-inflicted row per hour, and `channelSilent` (`successesLastDay == 0 && failuresLastDay > 0`) is then satisfied **by the job's own output** — a self-sustaining hourly alert. Separately, while the channel is dark the job emails the roster every hour for up to 24 h with no acknowledgement mechanism | `D-M1S04-04`, M1-S04 note § 4 items 5 and 6 | **P2** | **Accept as documented, and fix the filter in the next milestone.** It cannot alert anyone while it fires (that is the condition), so the blast radius is list-view noise, not a page storm. But the loop is self-feeding and the code comment is right that excluding gap rows is a *threshold change to the plan*, not a code change. Recommend one clarification — "do `Warning` rows count toward the failure thresholds?" — and a `Severity__c != 'Warning'` filter as the expected answer |
| 5 | **Five manual deploy steps + four out-of-manifest prerequisites.** Confirm the AuthHeader formula; enter the API key in Setup; assign `Tier2_Webhook_Admin` to the D14 set; `System.schedule` the hourly job; confirm the org-wide sender. Prerequisites: the `Tier_2_Engineering` queue, the verified sender, no pre-existing `CaseTrigger`, PSA read | `artefacts/M1-S05/deploy-order.md` § 3 and § 2; A4, A8, A13 | **P2** | **Accept — this is the correct shape, and it is unusually complete.** Every step has an owner and a timing; steps 2 and 4 repeat in every org and after every sandbox refresh, which is stated. **One gap worth closing at the gate:** prerequisite 3 (no pre-existing `CaseTrigger` on `Case`) is the only one that produces a hard deploy error and it was never asked in any of the 45 clarifications. Check it before the first deploy; `/consolidate-triggers` is the agent if one exists |
| 6 | **The stale AuthHeader plan prose (PV-007).** `plan.json`'s own text for M1-S05 still frames the AuthHeader question as wholly open. Two of its three parts are closed: the parameter name and formula were supplied by the requester, and the org confirmed the element is required (run 1). What remains is narrower — grammar-parses-on-deploy (settled by run 5) and header-arrives-with-the-key (settled only at UAT) | `D-M1S02-06`, `D-M1S05-04`, M1-S05 note § 3 step 1 and § 6(c) | **P2** | **Accept the note as the carrier; do not block on the prose.** `amend-step` is refused once a step leaves `pending`, so there is no writer for this text today — the correct reading exists in the artefact and the report. Tick manual line 5 against the *narrowed* question. **Flag for the loop, not the human:** a `--prose-only` amendment that could reach a `documented` step's test descriptions would have closed this |
| 7 | **`inputs.recipients` vs `inputs.alert_recipients` disagree.** `amend-step` replaces `inputs` wholesale, so the superseded `recipients` ("the distribution list address is taken from the deploy-order note") survived beside the new `alert_recipients` (active assignees of `Tier2_Webhook_Admin`, queried at run time). The Apex followed `alert_recipients` | `D-M1S04-02`, driver's-log friction 36 | **P2** | **Accept — the built code followed the right key, and confirm that at the gate rather than assuming it.** I verified it directly: `Tier2ChannelHealthQueueable.resolveRecipients()` queries `PermissionSetAssignment`, and no distribution-list address appears anywhere in the class. The residual risk is a future reader trusting the stale key. Recommend a `superseded_by` convention on `inputs{}` keys, or key-level amendment — a library fix, not a build fix |
| 8 | **The `setMock`-ordering library contradiction.** `skills/apex/apex-named-credentials-patterns/references/code-examples.md` § 6 shows `Test.setMock(...)` **before** `Test.startTest()`. `check_callouts_and_http_integrations.py` rule 6 flags exactly that as HIGH, quoting the Apex Developer Guide: *"The Test.startTest statement must appear before the Test.setMock statement"* (L35677–35681) | `D-M1S03-07`, driver's-log friction 40 (**not** `S3-F-07`, which is the LongTextArea SOQL filter) | **P2 (library)** | **No action on this build — it resolved the contradiction correctly, and the library is what needs fixing.** All three M1-S03 test classes put `startTest()` first, matching the guide quote and the checker; the checker exits 0. Per `standards/source-hierarchy.md` Tier 1 wins and the guide is Tier 1, so the skill's example is the defect. **Recommend a skill fix outside this build**; it changes nothing at the gate |

---

## 9. Confidence — **MEDIUM**

Per `agents/milestone-verifier/AGENT.md` Step 10. HIGH requires *no unclassifiable references*, and
this milestone has four (§ 3.2): the queue by `DeveloperName`, the org-wide sender, `PermissionSetAssignment`
read, and the `ApiKey` half of the `$Credential` formula. Each resolves against the target org rather
than against any artefact of this or an earlier milestone, so none is an unresolved reference — and
none can be classified as resolved either. That is the MEDIUM trigger, exactly.

Not LOW: every declared checker exists and ran, no artefact directory is empty, no step is blocked,
and there is no earlier milestone whose inventory could have failed to build.

Sharpening it rather than leaving it a letter: the merged manifest built with no version conflict and
no unresolved collision, and the three checkers passed — but **no Apex has ever been compiled against
a test run** (finding S2-F-06), so the 15 Apex components are structurally verified and behaviourally
unverified. The gate should read "the artefacts hold together", not "the feature works".

---

## 10. Requirements this milestone closes

Per `skills/admin/requirements-traceability-matrix` § *The Build-Layer RTM*, verified by running
`check_rtm.py` rather than read off the file's prose.

- **16 requirements, `REQ-001`–`REQ-016`**, minted at the documentation pass with the settling
  clarification id preserved in `source` (`Q4`–`Q30`). **0 coverage gaps, 0 orphan artefacts, 0 errors.**
- **All 16 are at status `In UAT`. None is `Released`, and none should be** — this is a `design-only`
  build and nothing has deployed. Every `In UAT` row carries a `test_id`, which is the skill's own
  rule 2 for that status.
- **0 requirements remain open.** Every clarification that produced a requirement produced a row, and
  every row has an artefact and a test.
- What `In UAT` does *not* assert, stated plainly: no Apex test has executed and no manual line has
  been ticked (§ 7). The rows record that the artefacts exist and their checkers pass.

---

## 11. Findings raised by this run

Continuing the **`S2-F-xx`** sequence from `S2-F-05`. See § 12 on the numbering.

| id | Severity | Finding |
|---|---|---|
| **S2-F-06** | **P1** | **No Apex test has ever executed; coverage is unmeasured.** Mock-deploy run 5 records `runTestsEnabled: false`, `numberTestsCompleted: 0`, `testLevel: null` (`reports/mock-deploy/2026-09-12T12-21-51Z/result.json`). The milestone ships **13 `ApexClass` + 2 `ApexTrigger`**, and per `skills/devops/pre-deployment-checklist` a production deploy requires `RunLocalTests` with ≥75% org-wide coverage. The five test classes were written and read but never run, so the predicted production failure per `skills/devops/deployment-error-diagnosis` is *"Average test coverage across all Apex Classes is below 75%"* — and a sandbox deploy at `NoTestRun` will pass and tell the human nothing. **Recommend:** before the production deploy, one `sf project deploy validate --test-level RunLocalTests` against production, and capture the coverage number. This is a go/no-go item the checker suite structurally cannot produce |
| **S2-F-07** | **P2** | **`PermissionSet` full-replace was never checked against the target.** From API v40+ a `PermissionSet` deploy **fully replaces** the target record — anything not in the XML is silently removed, with no warning (`skills/devops/permission-set-deployment-ordering` § *Full-Replace Semantics*). `Tier2_Webhook_Admin` is new *in this build*, but no step confirmed the target org holds no set of that name, and `skills/devops/pre-deployment-checklist`'s "pre-release backup retrieved" gate was never run. **Recommend:** one `sf project retrieve start --metadata "PermissionSet:Tier2_Webhook_Admin"` against the target before deploying. Empty result → proceed |
| **S2-F-08** | **P2** | **The feature cannot be deployed dark.** Both trigger meta files declare `<status>Active</status>`, and item 1 above removed the kill switch. Escalation is live at the instant the deploy lands, before the API key is entered (manual step 2) and before `Tier2_Webhook_Admin` is assigned (manual step 3) — so the window between deploy and those two steps produces a 401 and an `Integration_Failure__c` row for **every** Case escalated in it. **Recommend:** either deploy `CaseTrigger` with `<status>Inactive</status>` and activate after manual steps 2–3, or deploy outside business hours and complete both steps immediately |
| **S2-F-09** | INFO | **Milestone test 3's description undercounts its own findings.** It states "exit 0 with exactly those two WARN findings"; the run over `artefacts` produces **four** — `ExternalCredential` and `NamedCredential`, once each for `M1-S02/package.xml` *and* `M1-S05/package.xml`. The fixture it was verified against predated the M1-S05 manifest. Exit code 0 either way; the test passes. Prose only |
| **S2-F-10** | INFO | **Finding-id namespace collision** between the scenario sequence and a step-local one. See § 12 |

---

## 12. Numbering reconciliation

Two `S<n>-F-xx` sequences exist in this build and they are **not** one series:

- **`S2-F-01` … `S2-F-05`** — *scenario*-level. "S2" is scenario 2 (this build) in
  `reports/drivers-log.md`; the ids were minted by the operator's mock-deploy runs
  (`reports/MOCK-DEPLOY-M1.md`). `S2-F-02`/`-03` are run 1's credential failures, `S2-F-04`/`-05`
  run 3's Apex failures.
- **`S3-F-01` … `S3-F-07`** — *step*-local. "S3" is step `M1-S03`, minted by that step's runner in
  `envelopes/M1-S03/*.json`. Read as a scenario prefix it looks like "scenario 3", which does not
  exist in this build.

**This report continues the scenario sequence: `S2-F-06` … `S2-F-10`.** No `S3-F-xx` id is reused or
renumbered, and the eight decision items in § 8 keep the ids they were recorded under. Recorded as a
finding (**S2-F-10**) because the two prefixes are one character apart and mean different things;
the convention worth adopting is a step-scoped form that cannot be misread — `M1-S03-F-01`.

---

## 13. Optional validate-only command — for a human to run, never for an agent

**This agent ran no `sf` command and no `mock_deploy.py`.** The line below is printed for a human.

The build's own dry run, which is the one that reads the merged manifest:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/tier2-webhook/plan.json \
  --org-alias <alias> --milestone M1 --mode manifest
```

Raw equivalent — **sandbox** target (`--dry-run` compiles and validates without saving):

```bash
sf project deploy start --manifest .sfskills/builds/tier2-webhook/reports/MILESTONE-M1-package.xml \
  --dry-run --target-org <alias>
```

**Production** target — a different command, documented by Salesforce as production-only; it requires
Apex tests and returns a job id for a later `sf project deploy quick`:

```bash
sf project deploy validate --manifest .sfskills/builds/tier2-webhook/reports/MILESTONE-M1-package.xml \
  --test-level RunLocalTests --target-org <prod-alias>
```

Per finding **S2-F-06**, the production form with `--test-level RunLocalTests` is the only one of the
three that will tell anyone whether the Apex passes its own tests.

---

## 14. Gate

The verdict and this report's path were recorded with:

```bash
python3 scripts/build_plan.py set-milestone .sfskills/builds/tier2-webhook/plan.json M1 \
  --status verified --report-path reports/MILESTONE-M1-REPORT.md
```

That is bookkeeping, **not** approval. The gate is the human's and this agent does not run it:

```bash
python3 scripts/build_plan.py gate .sfskills/builds/tier2-webhook/plan.json milestone:M1 approve --by "<name>"
```

`standards/build-orchestration.md` § 3 will check, before writing: `plan` approved (✅), the preceding
milestone gate approved (✅ n/a — M1 is first), and every step in M1 `documented` or `blocked` with a
recorded reason (✅ all five `documented`, none blocked). **No blocked step is being accepted.**

---

## 15. Re-verification — 2026-09-15T19-07-06Z

**The `milestone:M1` gate is already `approved`.** It was re-signed (`reject` then `approve`, the
CLI's only re-sign path) on `2026-09-12T18:35:37Z` and the build's own `status` moved to `done` on
that same signing. This section does not touch the gate and is not a precondition for one — it is a
second, independent pass over the evidence the operator's re-sign note cites, run six repair rounds
(`S2-F-11` … `S2-F-16`, plus the `S2-F-06` closure) after § 1–14 above were written. Nothing here
supersedes § 1–14; where this pass reaches a different number it says so and keeps both.

### 15.1 Why re-verify an accepted milestone

The re-sign note (`plan.json` `human_gates[]`, `milestone:M1`) states plainly that
`reports/MILESTONE-M1-package.xml` (33 members, § 5 above) "is stale by two rebuilds and is not
re-verified (budget) — the build manifest M1-S05 is the release artefact." That is an honest
disclosure, not a defect, but it means the artefact this agent is the sole writer of was accepted
into a `done` build without this agent having re-read it. This pass closes that gap.

### 15.2 Merged manifest — regenerated, 35 members, zero drift

`reports/MILESTONE-M1-package.xml` regenerated from the same three step-level fragments as § 5
(`artefacts/M1-S01/package.xml`, `artefacts/M1-S02/package.xml`, `artefacts/M1-S05/package.xml`),
same method: union members per type, sort within each `<types>` block, one `<version>` element.

| Type | Members (§ 5, 2026-09-12) | Members (this pass) |
|---|---|---|
| `CustomObject` | 2 | 2 |
| `CustomField` | 13 | 13 |
| `ExternalCredential` | 1 | 1 |
| `NamedCredential` | 1 | 1 |
| `ApexClass` | 13 | **15** (+`TestUserFactory`, +`Tier2WebhookFinalizerTest`) |
| `ApexTrigger` | 2 | 2 |
| `PermissionSet` | 1 | 1 |
| **Total** | **33** | **35** |

- **Drift vs `artefacts/M1-S05/package.xml`: none.** `diff` against the regenerated file is empty —
  byte-identical, not merely member-for-member equal. This matches the 35-member count `D-M1S05-07`
  and `reports/MOCK-DEPLOY-M1.md` run 13 already recorded; this pass re-derives it from the artefacts
  rather than taking the decision log's word for it.
- **Two-way consistency, re-run over the current tree:** 54 defining files (15 `M1-S01` + 3 `M1-S02` +
  28 `M1-S03` + 8 `M1-S04`, `.cls`/`.trigger` counted once per class alongside their `-meta.xml`) back
  35 members with no member lacking a file, no file lacking a member, no duplicate, no wildcard —
  matching the bidirectional check `D-M1S05-07` recorded, reproduced independently here.
- **Member collisions: 18** (up from the 18 already reported at 33 members — the two new `ApexClass`
  members are new *members*, not new collisions, since neither `TestUserFactory` nor
  `Tier2WebhookFinalizerTest` had a manifest fragment of its own to collide with). Same resolution as
  § 5: every collision is `M1-S05` aggregating a member already declared by `M1-S01` or `M1-S02`.
  `TestDataFactory` still appears once, shipped twice (`M1-S03`, `M1-S04`), both copies re-hashed this
  pass and still identical to each other and to `templates/apex/tests/TestDataFactory.cls`.
- **Version: no conflict.** All three fragments still declare `67.0`.

### 15.3 Reference resolution — re-checked, one new grant, still zero unresolved

The repair wave added exactly one new cross-artefact reference beyond § 3's table: a second
`objectPermissions` row on `Tier2_Webhook_Admin.permissionset-meta.xml`, granting Create/Read on
`Tier2_Escalation__e` (`D-M1S02-07`, closing `S2-F-13`). Re-run against the same resolution method
as § 3:

| Reference class | Instances now | Resolved | Unresolved | Note |
|---|---|---|---|---|
| Permission-set object grants | **2** (was 1) | 2 | 0 | New: `Tier2_Escalation__e`, resolves against the `M1-S01` `CustomObject` inventory. `Integration_Failure__c` grant unchanged |
| Permission-set field grants | 12 (unchanged) | 12 | 0 | Still excludes `Status__c` — still `<required>true</required>` |
| Apex → custom object/field symbols | 18 (unchanged) | 18 | 0 | `TestUserFactory.cls` names no custom object or field (only standard `User`, `Group`, `PermissionSetAssignment`); `Tier2WebhookFinalizerTest.cls` names 14 tokens, all already in the § 3 inventory (`Integration_Failure__c` + its 12 fields via the `Case.Tier2_Notified_At__c` alias, no new symbol) |

Everything else in § 3's table is unaffected by the repair wave (no validation rule, assignment rule,
Flow, entitlement, or layout artefact was touched) and was re-confirmed present and unchanged. **Zero
unresolved references, before or after the repair wave.**

### 15.4 Deployment order — unchanged conclusion

The one item § 4 raised — `steps[M1-S05].inputs.deploy_order` in `plan.json` still sequences
`PermissionSet` before the fields it grants, a static plan-input string untouched by any of the six
repairs — is still present, word for word, and still resolved the same way: safe in the artefacts
because the merged manifest deploys as one request and `Tier2_Webhook_Admin` carries no
`classAccesses` element to create a backwards Apex dependency. The new `Tier2_Escalation__e` grant
does not change this: it is another forward reference into group 1 (§ 4), not a new backwards one.
No group's position in the sequence changed.

### 15.5 Acceptance tests — re-run against the current artefacts tree

The milestone's three declared `checker` tests, run verbatim from the build directory:

| # | Command | Exit | Verdict |
|---|---|---|---|
| 1 | `check_permission_set_architecture.py --manifest-dir artefacts` | **0** | pass — same WARN as § 6 (`modifyAllRecords=true` on `Integration_Failure__c`, D12) plus one new INFO (`PermissionSet description is 224 characters, approaching the 255-character limit` — the S2-F-13 description text pushed it there; not blocking) |
| 2 | `check_apex_named_credentials_patterns.py --manifest-dir artefacts` | **0** | pass — `OK: no Named Credential findings.` |
| 3 | `check_deployment_manifest.py --manifest-dir artefacts` | **0** | pass — score 80, **4 WARN** (`ExternalCredential`/`NamedCredential` named once each in `M1-S02/package.xml` and `M1-S05/package.xml`), 0 blocking, 62 manifest/metadata files scanned (was 58 at 33 members — the two new Apex files plus their `-meta.xml` account for the difference). **S2-F-09 still applies unchanged**: the declared description still says "exactly those two WARN findings" |

`check_rtm.py --file traceability.md --manifest-dir artefacts` (verification support, not a declared
test, same as § 6): **16 rows, 0 coverage gaps, 0 orphans, 0 errors, 0 warnings** — identical to the
original run.

**What changed since § 6 that this pass can now state as evidence rather than repeat from the note:**
`reports/MOCK-DEPLOY-M1.md` run 13 (`2026-09-12T18:21:32Z`) is a `MANIFEST`-mode,
`--test-level RunSpecifiedTests` run against the 35-member manifest: **37 tests run, 37 passed, 0
failed**, aggregate coverage **89.9%**. Re-derived from `reports/mock-deploy/2026-09-12T18-21-32Z/
result.json` rather than taken from the summary line: nine classes carry coverage data, and
**every one individually clears the 75% floor** —
`Tier2ChannelHealthQueueable` 84/100 (84%), `CaseTriggerHandler` 36/43 (83.7%),
`IntegrationFailureTriggerHandler` 39/46 (84.8%), `Tier2WebhookQueueable` 167/183 (91.3%),
`Tier2EscalationService` 40/41 (97.6%), `Tier2WebhookFinalizer` 73/76 (96.1%), `CaseTrigger` 1/1,
`IntegrationFailureTrigger` 1/1, `Tier2ChannelHealthSchedulable` 2/2 — aggregate 443/493 = 89.9%,
matching the run's own summary line. **This closes finding `S2-F-06`** (§ 11: "no Apex test has ever
executed") on evidence this pass re-derived from the raw result, not on the operator's word for it.

### 15.6 Findings — continuing from S2-F-16

`S2-F-11` through `S2-F-16` were minted by the operator's mock-deploy runs 6–11 (`reports/
MOCK-DEPLOY-M1.md`), not by this agent, and are recorded as closed in `decisions.md` (`D-M1S03-09`,
`D-M1S03-12`/`D-M1S04-11`, `D-M1S02-07`, `D-M1S03-14`). This pass re-checked each closure against
the current artefacts directly rather than accepting the decision log's claim:

| id | Closure claimed | Re-checked against | Holds? |
|---|---|---|---|
| `S2-F-11` | Tests now run as a `TestUserFactory`-provisioned, permissioned user | `PERM_SET = 'Tier2_Webhook_Admin'` + `System.runAs` present in all four affected test classes (`Tier2EscalationServiceTest`, `Tier2WebhookQueueableTest`, `IntegrationFailureResendTest`, `Tier2ChannelHealthTest`) | **Yes** |
| `S2-F-12` | `TestDataFactory` sets a lookup only when the caller supplies it | `artefacts/M1-S03/classes/TestDataFactory.cls` lines 37–38, 56–57, 73–74: `if (accountId != null) { …AccountId = accountId; }` in all three record builders | **Yes** |
| `S2-F-13` | `Tier2_Webhook_Admin` grants Create/Read on `Tier2_Escalation__e` | Second `objectPermissions` block present, `allowCreate=true allowRead=true`, § 15.3 | **Yes** |
| `S2-F-14` | `Tier2WebhookFinalizerTest` exercises the finalizer's own branches | File present, shipped as a 15th `ApexClass` member (§ 15.2); its own coverage now 96.1% | **Yes** |
| `S2-F-15` | The re-enqueued job no longer runs to a designed failure inside the test | `Tier2WebhookFinalizerTest.cls` line 236: `Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator().withResponse(200, OK_BODY))` registered ahead of the retry boundary in `transientFailureBelowAttemptCeilingIsRecordedRetryingAndReEnqueuedOnce` | **Yes** |
| `S2-F-16` | `Tier2EscalationService` gains its own branch tests past the per-class 75% floor | `Tier2EscalationServiceTest.cls` carries 9 `@isTest` methods (was fewer pre-repair); per-class coverage 97.6% in run 13 | **Yes** |

**Findings still open, unaffected by the repair wave — carried forward, not renumbered:**

- **`S2-F-07`** (P2) — `PermissionSet` full-replace against the target org was never checked. Nothing
  in `decisions.md` closes it; still applies to the now-35-member manifest identically.
- **`S2-F-08`** (P2) — the feature cannot be deployed dark; both triggers still declare
  `<status>Active</status>`, and no kill switch was added by any of the six repairs.
- **`S2-F-09`** (INFO) — still 4 WARN against a description that says 2 (§ 15.5).
- **`S2-F-10`** (INFO) — the `S2-F-xx` / `S3-F-xx` numbering-namespace note (§ 12) is unaffected.

**No new finding from this pass.** The one candidate considered and rejected: `check_deployment_manifest.py`
scanned 62 files this run against 58 at 33 members — a pure consequence of two new Apex files (`.cls`
+ `.cls-meta.xml`) entering the tree, not a new condition. `mock_deploy.py`'s own "N total, N+1 ok"
component-count convention (package.xml counted in "ok" but not "total") is unchanged across every
run in `reports/mock-deploy/*/summary.md` from run 1 onward, including run 13 — a display convention,
not a defect surfaced by this pass.

### 15.7 Manual checklist — one line's tick condition widened

§ 7 line 2 (`M1-S02`) is still correct as far as it goes, but `tests/M1-S02/results.json`'s own
`skipped_manual[]` entry now carries a **RE-TEST NOTE** this report's § 7 table predates: item (d)'s
tick condition must also cover the new `Tier2_Escalation__e` `objectPermissions` row
(`allowCreate`/`allowRead` true), per `artefacts/M1-S02/deploy-order.md` § 0b and the permission
set's own updated `<description>`. Restated here rather than rewriting § 7, which is this agent's own
prior output and stays as written:

> **§ 7 line 2, superseding tick condition for (d):** `fieldPermissions` carries
> `Case.Tier2_Notified_At__c` readable+editable and every `Integration_Failure__c` field bar
> `Status__c`, **and** `objectPermissions` carries `Tier2_Escalation__e` with `allowCreate` and
> `allowRead` both `true` and `allowEdit`/`allowDelete`/`modifyAllRecords`/`viewAllRecords` all
> `false`.

The other five checklist lines are unaffected by the repair wave and are re-confirmed tickable as
written.

### 15.8 Confidence — MEDIUM, unchanged, on a narrower rationale

Per `agents/milestone-verifier/AGENT.md` Step 10, same letter as § 9 but for a different reason now.
§ 9's MEDIUM rested partly on `S2-F-06` (no Apex test had ever executed) sharpening the letter
downward; that finding is closed (§ 15.5). What still holds MEDIUM below HIGH is unchanged from § 9
and untouched by the repair wave: **four references remain unclassifiable** — the `Tier_2_Engineering`
queue by `DeveloperName`, the org-wide sender, the scheduling user's `PermissionSetAssignment` read,
and the `ApiKey` half of the `$Credential` formula — each resolving only against the target org.
Not LOW: every declared checker exists and ran, no artefact directory is empty, no step is blocked.
Read together with § 9: the repair wave moved this milestone's confidence gap from "behaviourally
unverified" to "verified in a sandbox, unverified against the four org-only externals" — a real
improvement that does not cross the HIGH threshold, because the threshold is about reference
classification, not about how much testing happened.

### 15.9 `set-milestone` on a `done` build, and what the tool does that this AGENT.md does not describe

`agents/milestone-verifier/AGENT.md` Step 9 gives one `set-milestone` invocation shape
(`--status verified|rejected`) and describes it as recording "a statement about what the checks
found." It does not describe what happens when the milestone it names is already `accepted` — which
is exactly this case, and is not this agent's invention to handle silently. Reading
`scripts/build_plan.py::cmd_set_milestone` before invoking it (required, since the AGENT.md is silent
here): when `milestone.status == "accepted"` and `--status` is anything else, the command does **not**
move the milestone away from `accepted` — only a human's `gate … reject` can do that. Instead it
appends one entry to a `milestones[].reverifications[]` array (`{at, verdict, report_path}`) and
updates `report_path`, leaving `status: "accepted"` untouched. This is a real, tested code path (its
inline comment cites `F-12`, "an `accepted` milestone is the human's G3 record"), not a guess this
report is making about what "if refused" should mean — the command does not refuse, it degrades to a
recorded re-verification. Invoked below with `--status verified`, matching this pass's verdict
(§ 15.11).

**What the playbook does not support, stated plainly, per this run's brief:**

- **AGENT.md Step 9 has no branch for a milestone already `accepted`.** It assumes the run it
  describes is the one that produces the first verdict feeding a still-`pending` gate. The CLI has
  evidently been extended (`F-12`) to carry a second, later use — recording a re-verification against
  a decision already on record — but the AGENT.md's prose was not updated alongside it. This report
  had to read the script source to know what would happen; a caller who only reads AGENT.md would not
  know `reverifications[]` exists.
- **`standards/build-orchestration.md` names no re-verification concept at all** — grepped for
  "reverif" and "already approved" across the whole file, zero hits. § 3's gate table describes one
  pass from `pending` to `approved`/`rejected` and is silent on a later pass over the same,
  already-decided milestone.
- **The Wave 10 generic persistence pair (`docs/reports/milestone-verifier/<run_id>.{md,json}`,
  `DELIVERABLE_CONTRACT.md`) was not written by this pass**, per this run's explicit instruction to
  write only inside the build directory. The original 2026-09-12 run did not write it either, so this
  is a standing gap between the generic contract and this agent's actual practice, not a new
  deviation introduced here — worth a line rather than a silent repeat.
- **Step 1's precondition table has no row for "milestone already `accepted`."** It lists the
  in-progress statuses that block a run and the `blocked`-with-reason exception; an already-`accepted`
  milestone is neither, and this report proceeded on the reading that verifying an accepted milestone
  is in scope (the user's explicit ask, and the CLI's own `reverifications[]` support agree) rather
  than a `REFUSAL_OUT_OF_SCOPE` condition Step 1 lists.

### 15.10 Verdict — this pass

**`ready-with-findings`, unchanged from § 1.** No unresolved reference (§ 15.3), the merged manifest
rebuilds with zero drift (§ 15.2), all three declared checkers still exit 0 (§ 15.5), and no step is
blocked — but the one deployment-order contradiction in `plan.json`'s own stale step input (§ 15.4,
carried from § 4) is still present, which is what keeps this below `ready-for-gate` under Step 9's
rubric even though every acceptance test now has run-time evidence behind it.

**On the already-approved gate:** the evidence the 2026-09-12T18:35:37Z re-sign note cites —
run 13's 35-member manifest, `RunSpecifiedTests` success, 37/37 tests, 89.9% coverage, no coverage
warnings — is independently confirmed by this pass, re-derived from the raw artefacts and the raw
mock-deploy result rather than taken from the note's prose. The findings the repair wave did not
touch (`S2-F-07`, `S2-F-08`, the § 4/§ 15.4 ordering item) were already on record and already
weighed by the human before the re-sign; this pass adds no new item to that weighing. **This pass's
conclusion is that the currently-approved gate is supported by the evidence its own re-sign note
cites** — a finding *about* the approval, not a re-opening of it.

```bash
python3 scripts/build_plan.py set-milestone .sfskills/builds/tier2-webhook/plan.json M1 \
  --status verified --report-path reports/MILESTONE-M1-REPORT.md
```

Per § 15.9 this **does not** move `milestones[].status` off `accepted` — it records a
`reverifications[]` entry and updates `report_path`. **No gate command is printed in this section**:
`milestone:M1` is already `approved`, re-running the approve line would be meaningless, and nothing
in this pass gives a human cause to run `gate milestone:M1 reject`. Nothing was deployed and no `sf`
command or `mock_deploy.py` run was executed by this agent in this pass.
