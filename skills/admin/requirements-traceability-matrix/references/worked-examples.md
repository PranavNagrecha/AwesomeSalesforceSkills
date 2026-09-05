# Worked Example — The Traceability Matrix for the Acme Case-Intake Build

One build, traced end to end. The build is the case-intake solution in
`skills/admin/case-management-setup/references/worked-example-case-intake.md`: Acme Software moving
B2B support off a shared mailbox onto Service Cloud. That file produced the configuration workbook
and the deployable metadata; `skills/admin/uat-and-acceptance-criteria/references/worked-examples.md`
produced the UAT programme that tested it. **This file produces the matrix that ties the two
together** — and it is deliberately the format
`standards/build-orchestration.md` § 2 names for `.sfskills/builds/<build-id>/traceability.md`
("REQ → step → artefact → test"), written by `agents/build-doc-keeper/AGENT.md` after every tested
step. There is no second format.

Boundaries, so nothing here is written twice:

| Concern | Owned by |
|---|---|
| The build's requirements, decisions and metadata | `admin/case-management-setup` → `references/worked-example-case-intake.md` |
| The workbook rows (`CWB-*`) and their `source_req_id` rule | `admin/configuration-workbook-authoring` |
| The UAT cases (`UAT-CI-*`), personas, sandbox and sign-off | `admin/uat-and-acceptance-criteria` |
| The Given/When/Then form behind each `UAT-CI-*` | `admin/acceptance-criteria-given-when-then` |
| The step / gate / test-type contract | `standards/build-orchestration.md` |
| **The matrix, its key, its two derived views, and the linter** | **this skill** |

---

## 1. The build's shape, in one table

| Milestone | Steps | What it delivers |
|---|---|---|
| `M1` — foundations | `M1-S01` object model, `M1-S02` queues and groups, `M1-S03` access | Region and severity fields, three queues, the support PSG |
| `M2` — intake and routing | `M2-S01` assignment, `M2-S02` auto-response, `M2-S03` validation | Case routed and acknowledged on arrival |
| `M3` — clock and push | `M3-S01` calendars, `M3-S02` escalation, `M3-S03` entitlements, `M3-S04` Omni | The SLA promise and how work reaches an agent |
| `M4` — data and handover | `M4-S01` backlog load, `M4-S02` manifest, `M4-S03` reporting | The load plan, the deploy order, the support dashboard |

Step ids follow `agents/_shared/schemas/build-plan.schema.json` (`^M[0-9]+-S[0-9]{2,}$`), and each
step's `agent` is a roster id that resolves to `agents/<id>/AGENT.md` with `class: runtime`.

## 2. The key: why these rows carry both `REQ-` and `FG-` ids

Acme ran discovery first, so elicitation minted `REQ-001…REQ-017` and the fit-gap pass against the
existing org produced `FG-021` for the one thing the org already did and the project chose not to
touch. Per SKILL.md § REQ-XXX ⇄ FG-XXX, the elicited prefix is the key and the fit-gap id keeps its
own prefix on the row it owns — one row per need, never two. `scripts/check_rtm.py` accepts both.

## 3. The matrix as CSV

This is the authoritative form. `traceability.md` (section 4) is generated from it.

```csv
req_id,source,requirement,step_id,artefact,agent,decision_ref,test_id,test_type,status
REQ-001,Q3,Every case knows its account's region so the SLA clock uses the right calendar,M1-S01,CustomField:Account.Region__c,object-designer,D1,M1-S01-T1,checker,Released
REQ-002,Q1,Cases carry a severity 1-4 that routing and the SLA both read,M1-S01,CustomField:Case.Severity__c,object-designer,D1,M1-S01-T2,checker,Released
REQ-003,Q4,Tier 1 Tier 2 and Billing work from queues whose membership survives monthly churn,M1-S02,Queue:Tier_1_General,permission-set-architect,D2,M1-S02-T1,xml,Released
REQ-004,Q4,Support managers see queue-owned cases without owning them,M1-S02,Queue:Billing_Queue,permission-set-architect,D2,UAT-CI-006,manual,Released
REQ-005,Q9,Tier 1 agents can reply to case email and accept Omni-Channel pushes,M1-S03,PermissionSet:Feat_CaseEmailReply,permission-set-architect,D3,M1-S03-T1,checker,In UAT
REQ-006,Q2,Mail to billing@ creates a case owned by the Billing queue,M2-S01,AssignmentRules:Case,assignment-and-auto-response-rules-designer,D4,UAT-CI-002,manual,Released
REQ-007,Q8,Every new case gets exactly one acknowledgement from support@ and never from a routing address,M2-S02,AutoResponseRules:Case,assignment-and-auto-response-rules-designer,D5,UAT-CI-002,manual,Released
REQ-008,Q6,Severity 1 cannot be saved without a description and an account,M2-S03,ValidationRule:Case.Severity1_Requires_Detail,audit-router,D6,UAT-CI-003,manual,Released
REQ-009,Q11,EMEA and US cases run on their own working calendars,M3-S01,BusinessHoursEntry:EMEA_Support_Hours,business-hours-and-holidays-configurator,D7,M3-S01-T1,checker,Released
REQ-010,Q10,A case gets its regional calendar before save not after,M3-S01,Flow:Case_Set_Calendar,flow-builder,D8,UAT-CI-004,manual,Released
REQ-011,Q9,Untouched cases escalate to Tier 2 after 8 business hours,M3-S02,EscalationRules:Case,audit-router,D9,M3-S02-T1,checker,Released
REQ-012,Q12,Severity 1 escalates on a 24/7 clock with no pause,M3-S02,EscalationRules:Case,audit-router,D10,M3-S02-T2,manual,Released
REQ-013,Q9,Premier accounts get a 4 business-hour first response tracked as a milestone,M3-S03,EntitlementProcess:premier_support_v1,entitlement-and-milestone-designer,D11,M3-S03-T1,xml,In UAT
REQ-014,Q5,Tier 1 is pushed work by availability instead of pulling from a list view,M3-S04,QueueRoutingConfig:Case_Routing_Least_Active,omni-channel-routing-designer,D12,M3-S04-T1,checker,In UAT
REQ-015,Q13,A 200-row backlog load routes by the same rules as UI-created cases,M4-S01,File:artefacts/M4-S01/cases_backlog_mapping.csv,csv-to-object-mapper,D13,UAT-CI-005,manual,In UAT
REQ-016,Q14,The release can be rebuilt from a recorded deploy order,M4-S02,File:artefacts/M4-S02/package.xml,changeset-builder,D14,M4-S02-T1,manifest,Released
REQ-017,Q15,Support leadership sees queue age milestone violations and escalations by entry,M4-S03,,audit-router,D15,,,In Build
FG-021,Q7,Historic mailbox cases stay in the mailbox and are not migrated this release,,,,D16,,,Dropped
```

Reading rules, so a row is unambiguous:

- **`source`** is the clarification id from `plan.json.clarifications[]` (`^Q[0-9]+$`), not free text.
  A requirement whose source is a person rather than a clarification carries the name instead —
  either way the cell answers "who has to be asked again when this changes".
- **`artefact`** is `<MetadataType>:<ApiName>` and the API name is the Metadata API `fullName`, not
  the Setup label. For a `CustomField` the guide fixes the shape as `Object.Field__c`
  (`api_meta.txt` L43221–43226: "Specify the full name whenever you create or update a field. For
  example, a custom field on a custom object: `MyCustomObject__c.MyCustomField__c`" and "a custom
  field on a standard object: `Account.MyAcctCustomField__c`").
- **`File:<path>`** is the form for an artefact that is a project file rather than a metadata
  component — a field mapping, the manifest itself. The path is relative to the build directory.
  **`setup-only:<component>`** is the form for a component the Metadata API cannot carry (gotcha 14).
- **`agent`** is one roster id. Two agents on a row means two steps.
- **`decision_ref`** is `D<n>` from `plan.json.decisions[]` — section 5 lists them.
- **`test_type`** is one of the five runners in `standards/build-orchestration.md` § 5:
  `checker`, `xml`, `manifest`, `command`, `manual`.
- **Empty cells are data**, not omissions: `REQ-017` has no artefact and no test because the design
  does not exist yet, and `FG-021` has none because nothing will ever be built. The first is a
  blocker, the second is a waiver. The derived views are what tell them apart.

## 4. The same matrix as `traceability.md`

Generated from the CSV, never hand-maintained. This is the file that lands at
`.sfskills/builds/acme-case-intake/traceability.md`.

| req_id | source | requirement | step_id | artefact | agent | decision_ref | test_id | test_type | status |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | Q3 | Every case knows its account's region so the SLA clock uses the right calendar | M1-S01 | `CustomField:Account.Region__c` | object-designer | D1 | M1-S01-T1 | checker | Released |
| REQ-002 | Q1 | Cases carry a severity 1–4 that routing and the SLA both read | M1-S01 | `CustomField:Case.Severity__c` | object-designer | D1 | M1-S01-T2 | checker | Released |
| REQ-003 | Q4 | Tier 1, Tier 2 and Billing work from queues whose membership survives monthly churn | M1-S02 | `Queue:Tier_1_General` | permission-set-architect | D2 | M1-S02-T1 | xml | Released |
| REQ-004 | Q4 | Support managers see queue-owned cases without owning them | M1-S02 | `Queue:Billing_Queue` | permission-set-architect | D2 | UAT-CI-006 | manual | Released |
| REQ-005 | Q9 | Tier 1 agents can reply to case email and accept Omni-Channel pushes | M1-S03 | `PermissionSet:Feat_CaseEmailReply` | permission-set-architect | D3 | M1-S03-T1 | checker | In UAT |
| REQ-006 | Q2 | Mail to `billing@` creates a case owned by the Billing queue | M2-S01 | `AssignmentRules:Case` | assignment-and-auto-response-rules-designer | D4 | UAT-CI-002 | manual | Released |
| REQ-007 | Q8 | Every new case gets exactly one acknowledgement from `support@`, never from a routing address | M2-S02 | `AutoResponseRules:Case` | assignment-and-auto-response-rules-designer | D5 | UAT-CI-002 | manual | Released |
| REQ-008 | Q6 | Severity 1 cannot be saved without a description and an account | M2-S03 | `ValidationRule:Case.Severity1_Requires_Detail` | audit-router | D6 | UAT-CI-003 | manual | Released |
| REQ-009 | Q11 | EMEA and US cases run on their own working calendars | M3-S01 | `BusinessHoursEntry:EMEA_Support_Hours` | business-hours-and-holidays-configurator | D7 | M3-S01-T1 | checker | Released |
| REQ-010 | Q10 | A case gets its regional calendar before save, not after | M3-S01 | `Flow:Case_Set_Calendar` | flow-builder | D8 | UAT-CI-004 | manual | Released |
| REQ-011 | Q9 | Untouched cases escalate to Tier 2 after 8 business hours | M3-S02 | `EscalationRules:Case` | audit-router | D9 | M3-S02-T1 | checker | Released |
| REQ-012 | Q12 | Severity 1 escalates on a 24/7 clock with no pause | M3-S02 | `EscalationRules:Case` | audit-router | D10 | M3-S02-T2 | manual | Released |
| REQ-013 | Q9 | Premier accounts get a 4 business-hour first response tracked as a milestone | M3-S03 | `EntitlementProcess:premier_support_v1` | entitlement-and-milestone-designer | D11 | M3-S03-T1 | xml | In UAT |
| REQ-014 | Q5 | Tier 1 is pushed work by availability instead of pulling from a list view | M3-S04 | `QueueRoutingConfig:Case_Routing_Least_Active` | omni-channel-routing-designer | D12 | M3-S04-T1 | checker | In UAT |
| REQ-015 | Q13 | A 200-row backlog load routes by the same rules as UI-created cases | M4-S01 | `File:artefacts/M4-S01/cases_backlog_mapping.csv` | csv-to-object-mapper | D13 | UAT-CI-005 | manual | In UAT |
| REQ-016 | Q14 | The release can be rebuilt from a recorded deploy order | M4-S02 | `File:artefacts/M4-S02/package.xml` | changeset-builder | D14 | M4-S02-T1 | manifest | Released |
| REQ-017 | Q15 | Support leadership sees queue age, milestone violations and escalations by entry | M4-S03 | — | audit-router | D15 | — | — | In Build |
| FG-021 | Q7 | Historic mailbox cases stay in the mailbox and are not migrated this release | — | — | — | D16 | — | — | Dropped |

Note `REQ-011` and `REQ-012` sharing `AssignmentRules`-style coarse granularity on
`EscalationRules:Case`. That is not sloppiness: assignment and escalation rules for an object are
stored as **one file per object** — "Assignment rules for an object have the suffix
`.assignmentRules` and are stored in the `assignmentRules` folder. For example, all Case assignment
rules are stored in the `Case.assignmentRules` file" (`api_meta.txt` L23689–23691). The manifest can
name individual rules by switching the type name to the singular `AssignmentRule` with members like
`Case.samplerule` (`api_meta.txt` L23675–23682). So `artefact` is **not** a unique key, and any
tooling that assumes one row per file is wrong — see gotcha 9.

`REQ-009` is the same shape one level worse. Business hours are not a per-calendar file at all:
"Business hours and holidays settings are stored in a single file named `businessHours.settings` in
the `settings` directory. The `.settings` files are different from other named components because
there's only one settings file for each settings component" (`api_meta.txt` L111264–111273). Every
calendar and every holiday in the org shares that file, so the row names the *entry*
(`BusinessHoursEntry:EMEA_Support_Hours`, whose `name` field the guide describes at L111288–111294)
and the linter resolves it by reading the entries out of the one settings file.

## 5. The decisions the `decision_ref` column points at

`plan.json.decisions[]` carries `id`, `decision`, `decision_tree`, `branch`, `rationale`. Rendered:

| id | Decision | Resolved by |
|---|---|---|
| D1 | Region and severity are picklists on the record, not derived at read time | `admin/case-management-setup`; `admin/picklist-and-value-sets` |
| D2 | Queue membership by public group and role, never named users; `doesIncludeBosses` true | `standards/decision-trees/sharing-selection.md` § The 7-step sharing design sequence |
| D3 | Access via a feature permission set inside the `Support_Agent` PSG, not a profile edit | `admin/permission-set-architecture` |
| D4 | Assignment rules set the owner, not a Flow | `admin/assignment-rules` → `references/routing-selector.md`. `automation-selection.md` does not route rule-engine objects — recorded as a tree gap, not a tree branch |
| D5 | Auto-response sends from the org-wide address `support@`, never a routing address | `admin/email-to-case-configuration` gotchas; `admin/email-templates-and-alerts` |
| D6 | Severity-1 completeness enforced by a validation rule, not by the Flow that sets the calendar | `automation-selection.md` Q2 — record-level, sub-10 s, own fields only |
| D7 | Two calendars, one per region, US default | `admin/business-hours-and-holidays` § Questions to Ask |
| D8 | Before-save record-triggered Flow sets `BusinessHoursId` | `standards/decision-trees/automation-selection.md` Q1 → "A record change" → Q2 → "Yes" → before-save record-triggered Flow |
| D9 | Escalation via escalation rules on the `Case` business-hours source | `admin/escalation-rules`; `admin/business-hours-and-holidays` Decision Guidance |
| D10 | Severity-1 entry uses `businessHoursSource` = `None` — a documented 24/7 exception | `admin/business-hours-and-holidays` Decision Guidance |
| D11 | Premier SLA as an entitlement process with a First Response milestone | `admin/entitlements-and-milestones` |
| D12 | Omni-Channel on Tier 1 only; Tier 2 and Billing stay list-view queues | `admin/omni-channel-routing-setup` § Questions to Ask |
| D13 | Backlog loaded through Data Loader with the assignment-rule id set, one SOAP batch | `admin/uat-and-acceptance-criteria` § Why UAT-CI-005 is written the way it is |
| D14 | One manifest in the deploy order fields → groups → queues → templates → hours → routing → rules → Flow → entitlement process | `admin/assignment-rules` → `references/migration-and-sandbox.md` |
| D15 | Support dashboard deferred to design in M4; no skill covers the report set | recorded as `blocked: skill-gap` per `standards/build-orchestration.md` § 8 |
| D16 | Historic mailbox cases not migrated | descope ledger; waiver by Head of Support, 2026-08-20 |

A `decision_ref` that resolves to nothing is worse than an empty cell: it looks like the choice was
deliberate. `check_rtm.py` does not validate `D<n>` against `plan.json` — `scripts/build_plan.py
validate` owns that — but it does require the column to exist.

## 6. Derived view 1 — coverage gaps

**Definition:** every row with an empty `artefact` **or** an empty `test_id`, plus every row whose
`status` claims more than its cells support (`Released` with no `test_id`; `In UAT` with no
`artefact`).

```yaml
report: coverage-gaps
build: acme-case-intake
generated_from: traceability.md
gate: G3-M4
rows:
  - req_id: REQ-017
    missing: [artefact, test_id]
    status: In Build
    why: "Reporting design does not exist. admin/reports-and-dashboards-fundamentals is generic;
          no skill carries a support-operations report set (case-intake worked example, gap 4)."
    disposition: BLOCKER
    owner: ba.lead@acme.example
    due: 2026-09-12
  - req_id: FG-021
    missing: [step_id, artefact, test_id]
    status: Dropped
    why: "Deliberate descope. Decision D16, waived by Head of Support 2026-08-20."
    disposition: WAIVED
    owner: head.of.support@acme.example
    due: null
summary:
  rows_total: 18
  gaps: 2
  blockers: 1
  waived: 1
  gate_verdict: FAIL
```

The verdict is `FAIL` on one row out of eighteen, and that is the point: a matrix that is 94%
covered is not 94% shippable. `REQ-017` reached `In Build` with nothing to test, so the milestone
gate stops and `M4` does not close. The waived row does not count against the verdict *because it
carries a decision id and an owner* — a `Dropped` row with an empty `decision_ref` would be a second
blocker, not a second waiver.

## 7. Derived view 2 — orphans

**Definition:** every metadata component in the build's manifest that no row's `artefact` names.
This is the backward direction, and it is the one teams skip: nothing about building the matrix
forward surfaces it.

```yaml
report: orphans
build: acme-case-intake
manifest: artefacts/M4-S02/package.xml
rows:
  - artefact: "Group:Support_Agents_EMEA"
    produced_by: M1-S02
    why: "Membership vehicle for Tier_1_General. Real, needed, and asked for by no requirement."
    disposition: ADOPT
    action: "Add REQ-018 'queue membership survives agent churn' and point it at this artefact."
  - artefact: "PresenceDeclineReason:Busy"
    produced_by: M3-S04
    why: "Shipped by the Omni-Channel template defaults, never discussed with Acme."
    disposition: ADOPT-OR-REMOVE
    action: "Confirm with the support lead at G3-M3; if unwanted, destructiveChangesPost.xml."
  - artefact: "Queue:Tier_2_Support_Queue"
    produced_by: M1-S02
    why: "REQ-011 and REQ-012 route work INTO this queue, but their artefact is the escalation
          rule, not the queue. Nothing names the queue itself."
    disposition: DOCUMENT-AS-DEPENDENCY
    action: "Note it on REQ-011 as a dependency artefact, or give REQ-003 a second artefact row."
  - artefact: "CustomField:Case.Round_Robin_Counter__c"
    produced_by: null
    why: "Pre-existing in the org from an abandoned round-robin design. Workbook row CWB-OBJ-003
          explicitly says not in scope this release."
    disposition: DESTRUCTIVE-CHANGE-CANDIDATE
    action: "Out of this release. Raise as its own change; do not delete inside a feature deploy."
summary:
  orphans: 4
  gate_verdict: REVIEW
```

Three dispositions, and only three, are legal: **adopt** (write the requirement the artefact
already satisfies), **remove** (a destructive change with its own row), or **document as a
dependency** (the artefact exists only to make another one work). "Leave it" is not one of them —
an unexplained component in the manifest is exactly what a `Dropped` requirement looks like from
the outside. Note that three of these four are perfectly good components; an orphan is a *tracing*
finding, not a quality finding, and treating it as a defect is how teams learn to suppress the view.

The last row is the one to be careful with. Deleting a component that is already live is a
destructive change, and the delete manifest has its own rules: it is named `destructiveChanges.xml`,
**wildcards are not supported in it**, and it needs a companion `package.xml` that lists no
components and carries the API version (`api_meta.txt` L4614–4632). Bundling that delete into the
feature deploy would make the feature's rollback also a restore.

## 8. Running the linter

```bash
# The build directory: finds traceability.md, resolves artefact API names against the
# metadata under artefacts/, resolves agent ids against the repo roster.
python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py \
  --manifest-dir .sfskills/builds/acme-case-intake \
  --repo-root .

# One file, either schema, either format (.csv or .md):
python3 .../scripts/check_rtm.py --file governance/rtm.csv

# Write the two derived views instead of only printing them:
python3 .../scripts/check_rtm.py --manifest-dir .sfskills/builds/acme-case-intake \
  --repo-root . --report-dir reports/

# Prove the rules still fire before trusting a green run:
python3 .../scripts/check_rtm.py --self-check
```

Actual output on the matrix above, against the build directory whose artefacts section 7 lists —
one error, and it is the right one:

```text
WARN: row 14 (REQ-013): artefact 'EntitlementProcess:premier_support_v1' not found under the manifest dir — check the fullName, or mark the row 'setup-only:' if the Metadata API cannot carry it
WARN: row 19: coverage gap: FG-021 has no artefact and no test id (status 'Dropped') — waived by decision D16
WARN: orphan artefacts: 4 component(s) in the manifest are named by no requirement — see the orphan report
ERROR: row 18: coverage gap: REQ-017 has no artefact and no test id while status is 'In Build'
traceability.csv: 18 row(s), build schema, 2 coverage gap(s), 4 orphan(s), 1 error(s), 3 warning(s)
```

Read the three warnings as three different things. `FG-021` is the waiver working: the row is
allowed to be empty *because* it carries `D16`, and dropping `D16` turns that line into an error.
The orphan line is a pointer to the second view, not a verdict. Only the `EntitlementProcess`
line is a defect in the matrix itself.

The `EntitlementProcess` warning is a real trap rather than noise. The entitlement process file is
named for the process **with its version appended when entitlement versioning is on** — the guide's
own example is a process named "gold_support" living in `gold_support_v2.entitlementProcess`, and
that file name corresponds to `slaProcess.NameNorm`, the lowercase form of the UI `name`, which
several versions can share (`api_meta.txt` L59074–59082). A row that says
`EntitlementProcess:Premier_Support` will never resolve. Write the file's name.

## 9. What this file deliberately does not carry

- **The build itself.** Every artefact named here was designed in
  `admin/case-management-setup` → `references/worked-example-case-intake.md`. This file traces them;
  it does not re-derive them.
- **The UAT cases behind `UAT-CI-001…006`.** Their personas, sandbox, data setup and sign-off record
  are in `admin/uat-and-acceptance-criteria` → `references/worked-examples.md`.
- **The audit RTM's `story_ids` / `defect_ids` / `sprint` / `release` columns.** A build has one
  release; those columns belong to the multi-release audit schema in `references/examples.md` and
  `templates/rtm.md`.
- **A second matrix format.** If this file and `standards/build-orchestration.md` § 2 ever disagree,
  the standard wins and this file is regenerated.
