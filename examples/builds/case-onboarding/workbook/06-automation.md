# Configuration Workbook — Section 6

Per-step slice, written by the build doc keeper after `M2-S04` was tested. The compiled
ten-section workbook is `M5-S04`'s output; this file is one of its sources and is not the
finished document. This is the first Section 6 file in the build.

Row schema and section list: `skills/admin/configuration-workbook-authoring` SKILL.md
Concepts 1–3.

**Why a `Queue` / `Group` step whose declared `type` is `access` lands here, in Section 6, and
not in Section 3 or 4.** `agents/build-doc-keeper/AGENT.md` Step 4 maps step type `access` to
"3 — Profiles + Permission Sets + PSGs, and 4 — Sharing Settings for sharing artefacts" — neither of
which is a `Queue` or a `Group`. Three sources agree the content belongs here instead:

1. `standards/build-orchestration.md` § 4's own step-type table files `Queue` metadata under
   **`routing`**, and Step 4's own mapping sends `routing` artefacts to "6 — Automation, with queue,
   routing and Email-to-Case / Web-to-Case artefacts named in `target_value`" — naming queues
   explicitly.
2. `skills/admin/configuration-workbook-authoring/references/worked-examples.md` row `CWB-AUT-102`
   already files a queue-routing target under the `CWB-AUT-` (Automation) row prefix in its own
   canonical worked example.
3. `metadata-builder`'s own envelope for this step names the same disagreement, unresolved
   (`process_observations`, ambiguous, low): "the step's type is `access` while
   `standards/build-orchestration.md` section 4 files Queue metadata under routing … the type and
   the artefact column disagree."

`plan.json` `steps[M2-S04].type` is unchanged at `access` — this is a workbook-section placement
only, not a plan edit, and it is not this agent's to make unilaterally in the sense of a metadata
decision; it is recorded and flagged for a human at the M2 gate. Full record: `decisions.md`
**D-M2S04-06**; planner pointer **O-M2S04-03**.

**Deploy-position sequence is tracked separately from the section.** These rows carry `routing`'s
position in the ten-slot deployment sequence (objects → fields → picklists → record types → layouts
→ permission sets → sharing → automation → **routing** → SLA) — position **9 of 10** — even though
the *document section* they are filed under is "Automation" (Section 6). The two are not the same
axis: Step 4 decides where an artefact is *documented*; Step 5 decides where it *deploys*.

**Why these cells use `;` and not `|` for multi-value.** Same reason as every other file in this
workbook since `M1-S02`: `check_workbook.py` splits a table row on every bare `|` with no escape
handling (L330).

## Section 6 — Automation

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-AUT-001 | `Group:Support_Tier_1` — `<description>` names the membership source for the Tier 1 General case queue and states that membership changes monthly and is maintained as `GroupMember` data, never as named users in the queue file; `<doesIncludeBosses>true</doesIncludeBosses>` (skill default — no clarification answers the manager-visibility question); Owner: CRM admin lead. No members in this deploy — `GroupMember` is record data. | CRM admin lead (role; the plan names no person — Q29) | REQ-022 | pending:M5-S03 | metadata-builder | admin/queues-and-public-groups; admin/permission-set-architecture; admin/data-skew-and-sharing-performance | executed | Deploy position **9 of 10 (routing)** in the M2 sequence, position 1 inside the step — `deploy-order.md`'s own order table: "Deploy the group before any queue or sharing rule that names it." Verified by: `check_queues.py --manifest-dir artefacts/M2-S04` exit 0 (lists the three public groups); `check_data_skew_and_sharing_performance.py --manifest-dir artefacts/M2-S04` exit 0 as of the 2026-09-11 fix (`decisions.md` O-M2S04-04) — WARN "referenced by 1 reference(s) (queue Tier_1_General (queueMembers/publicGroups)) but Group metadata never carries members"; `manifest` two-way; `xml` parse. Manual test W02(2/3) confirmed no `<users>` element on this file (`tests/M2-S04/results.json` skipped_manual[2]) — the roster-confirmation half is outstanding at the M2 gate. **Gap named:** this file deploys with zero members; the 12-agent load is post-deploy data (`queue-retirement-runbook.md` § 6). |
| CWB-AUT-002 | `Group:Support_Tier_2` — same shape as `CWB-AUT-001`: membership source for the Tier 2 Engineering queue (4 engineers, Q8), `<doesIncludeBosses>true</doesIncludeBosses>` (same default), Owner: CRM admin lead. No members in this deploy. | CRM admin lead (role; the plan names no person — Q29) | REQ-023 | pending:M5-S03 | metadata-builder | admin/queues-and-public-groups; admin/permission-set-architecture; admin/data-skew-and-sharing-performance | executed | Deploy position **9 of 10**, position 2 inside the step. Verified by: same three checks as `CWB-AUT-001` (`check_queues.py` exit 0; `check_data_skew_and_sharing_performance.py` exit 0, WARN "referenced by 1 reference(s) (queue Tier_2_Engineering …)"; `manifest` two-way; `xml` parse); W02(2/3) no-`<users>` confirmation. **Gap named:** zero members in this deploy, same as `CWB-AUT-001`. |
| CWB-AUT-003 | `Group:Billing_Team` — membership source for the Billing case queue (2 finance staff, Q8), `<doesIncludeBosses>true</doesIncludeBosses>` (same default), Owner: CRM admin lead. No members in this deploy. | CRM admin lead (role; the plan names no person — Q29) | REQ-024 | pending:M5-S03 | metadata-builder | admin/queues-and-public-groups; admin/permission-set-architecture; admin/data-skew-and-sharing-performance | executed | Deploy position **9 of 10**, position 3 inside the step. Verified by: same three checks (`check_queues.py` exit 0; `check_data_skew_and_sharing_performance.py` exit 0, WARN "referenced by 1 reference(s) (queue Billing …)"; `manifest` two-way; `xml` parse); W02(2/3) no-`<users>` confirmation. **Gap named:** zero members in this deploy, same as the two rows above. |
| CWB-AUT-004 | `Queue:Tier_1_General` — `doesSendEmailToMembers=false`, no `<email>` (Q88: Omni-Channel push, not email), `queueMembers/publicGroups/publicGroup = Support_Tier_1` (no `<users>`, no `<roles>` — the role half of Q29 is ungrounded, `decisions.md` D-M2S04-03), `queueSobject/sobjectType = Case` (Q30). No `<queueRoutingConfig>` — `Tier_1_Push` is `M3-S05`'s not-yet-built output; deliberately omitted rather than dangling (`decisions.md` D-M2S04-05). No `<doesIncludeBosses>` — dated API 67.0+ on `Queue`, manifest is 62.0 (`decisions.md` D-M2S04-01). | CRM admin lead (role; the plan names no person) | REQ-021; REQ-022 | pending:M5-S03 | metadata-builder | admin/queues-and-public-groups; admin/permission-set-architecture; admin/data-skew-and-sharing-performance | executed | Deploy position **9 of 10**, position 4 inside the step (after all three groups). Verified by: `check_queues.py --manifest-dir artefacts/M2-S04` exit 0, `Objects : Case`, one of the two documented WARNs ("No `<email>` configured"); `manifest` two-way; `xml` parse. Manual test (six-component presence + `sobjectType=Case`) PASS (`tests/M2-S04/results.json` skipped_manual[0]). **This is the M3-S04 catch-all target (Q26) and the M3-S05 Omni-Channel push source** — a step serving each requirement remains, so `traceability.md` carries this row's requirements as `In Build`, not `In UAT`. |
| CWB-AUT-005 | `Queue:Tier_2_Engineering` — `doesSendEmailToMembers=false`, **no `<email>` element at all** (Q88 names only a posture — "a shared mailbox" — with no address anywhere on file; `decisions.md` D-M2S04-02), `queueMembers/publicGroups/publicGroup = Support_Tier_2`, `queueSobject/sobjectType = Case`. No `<doesIncludeBosses>` (same API-version reason as `CWB-AUT-004`). | CRM admin lead (role; the plan names no person) | REQ-023 | pending:M5-S03 | metadata-builder | admin/queues-and-public-groups; admin/permission-set-architecture; admin/data-skew-and-sharing-performance | executed | Deploy position **9 of 10**, position 5 inside the step. Verified by: `check_queues.py` exit 0, `Objects : Case`, the *second* of the two documented WARNs ("No `<email>` configured"). **Gap flagged for the gate, not silently ticked:** manual test W02(1/3) asserts this file "carries the Tier 2 shared mailbox" and it does not — `decisions.md` O-M2S04-02, `tests/M2-S04/results.json` skipped_manual[1] records the mismatch as evidence rather than a tick. `manifest` two-way; `xml` parse. |
| CWB-AUT-006 | `Queue:Billing` — `doesSendEmailToMembers=false`, `<email>billing@acme.example</email>` (Q88 + `requirement.md` L8), `queueMembers/publicGroups/publicGroup = Billing_Team`, `queueSobject/sobjectType = Case`. No `<doesIncludeBosses>` (same API-version reason as the other two queues). | CRM admin lead (role; the plan names no person) | REQ-024 | pending:M5-S03 | metadata-builder | admin/queues-and-public-groups; admin/permission-set-architecture; admin/data-skew-and-sharing-performance | executed | Deploy position **9 of 10**, position 6 inside the step. Verified by: `check_queues.py` exit 0, `Objects : Case`, no WARN on this file (the only queue with an `<email>`); `manifest` two-way; `xml` parse. **Risk named, not a defect:** `billing@acme.example` is also the address `M3-S03` (pending) configures as the Email-to-Case intake address — a queue-assignment notification and a fresh inbound case can chain through the same mailbox. `decisions.md` D-M2S04-04; must be exercised by Q68's sandbox loop test before go-live. |
