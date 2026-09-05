# Worked Examples — Requirements Gathering for Salesforce

One scenario, carried end to end: the interview guide, the requirements catalogue, the NFR sheet, the
As-Is / To-Be summary and the handoff map. Copy the shapes; replace the content.

---

## Scenario

**Meridian Supply Co.**, a wholesale plumbing distributor with 6 branches, 140 internal users and
~60 independent distributor partners, runs its returns (RMA) process on a shared spreadsheet on a
network drive. A branch clerk types the customer, the part number and a reason; a supervisor colours
the row green when it is approved; finance keys a credit memo into the ERP by hand. Nobody can say
how many returns are open, and the spreadsheet has a `HOLD?` column whose meaning nobody can explain.

Scope for this discovery: replace the spreadsheet with a Salesforce process, keep the ERP as the
system of record for credit memos, and let distributor partners raise their own returns.

---

## 1. Interview guide with Salesforce-aware probes

Two columns matter: the question you ask the stakeholder, and the follow-up that turns the answer
into a catalogue field. The follow-up is never asked in the stakeholder's language.

| # | Ask the stakeholder | Salesforce-aware probe (asked of the answer, not the person) | Catalogue field it fills |
|---|---|---|---|
| 1 | "Walk me through a return from the phone call to the credit." | Which steps are keying data, which are decisions, which are waiting? Is any step a workaround for a limitation of the spreadsheet? | `statement`, As-Is row, `status: blocked` for anything unexplained |
| 2 | "What do you type into the sheet, and what do you look up somewhere else?" | Each typed column is a field candidate; each looked-up column is either a formula, a related record, or an integration. | `objects`, `fields` |
| 3 | "When you say a supervisor approves it — what stops it moving before then?" | Nothing stops it today, or a person does. Is the control a validation rule, an approval process, or a stage gate? | `automation_candidate`, `decision_tree_step` |
| 4 | "Who can see this sheet?" then "who *should* be able to open a return, and who should be able to see the credit amount on one they can already open?" | Two different mechanisms. The first is record access (seven ordered layers); the second is FLS. Split into two rows. | `sharing_impact`, `sharing_layer` |
| 5 | "How many rows a month? What was the worst month? Has anyone ever pasted in a year of history?" | Steady state sizes the automation; the paste sizes the transaction. Ask for the backfill explicitly — nobody volunteers it. | `data_volume`, NFR sheet |
| 6 | "Where does the credit memo number come from?" | Another system. Direction, latency tolerance, and who owns the record become an integration row. | `licence_implication` (no), integration row + `decision_tree_step` |
| 7 | "Who else raises returns?" | "Our distributors" is a licence answer, not a persona answer. Employee / customer / partner selects the licence before anything is designed. | `licence_implication` |
| 8 | "What report does your GM ask for on Monday?" | Name the base object and everything that must appear on the same row. Check the join chain before promising it. | reporting row, NFR sheet |
| 9 | "What does the `HOLD?` column mean?" | If nobody knows, it is not a requirement yet. It is a `blocked` row with a named owner and a date. | `status`, `source_stakeholder` |

---

## 2. Requirements catalogue

Machine-lintable. Run `python3 scripts/check_requirements_catalogue.py --file requirements-catalogue.yaml`.

```yaml
project: "Meridian Returns — Phase 1"
requirements:
  - id: REQ-001
    statement: "A branch clerk records a return request against the customer account, with the part returned and a reason, in one place that everyone can see."
    type: functional
    source_stakeholder: "Dana Okafor — Branch Operations Lead, Leeds"
    objects: [Account, Return__c]
    fields: [Return__c.Reason__c, Return__c.Part_Number__c, Return__c.Quantity__c]
    priority: Must
    status: confirmed
    downstream:
      story: STORY-001
      fit_gap_row: FG-001
      workbook_section: "2. Objects and Fields"

  - id: REQ-002
    statement: "A new return is owned by the branch that raised it without the clerk choosing an owner."
    type: functional
    source_stakeholder: "Dana Okafor — Branch Operations Lead, Leeds"
    objects: [Return__c]
    fields: [Return__c.OwnerId, Return__c.Branch__c]
    automation_candidate: "Before-save record-triggered Flow setting OwnerId from Branch__c"
    decision_tree_step: "standards/decision-trees/automation-selection.md Q1 (record change) -> Q2 (under ~10s, fields on the record itself)"
    data_volume: "~4,200 returns per month steady state; one-off historical backfill of ~18,000 rows at go-live"
    priority: Must
    status: confirmed
    downstream:
      story: STORY-002
      workbook_section: "6. Automation"

  - id: REQ-003
    statement: "A return worth more than 5,000 GBP cannot be credited until a warehouse manager has agreed to it, and the agreement is on the record."
    type: functional
    source_stakeholder: "Priya Ramesh — Warehouse Manager, Midlands"
    objects: [Return__c]
    fields: [Return__c.Credit_Value__c, Return__c.Approval_Status__c]
    automation_candidate: "Approval Process with a post-approval Flow"
    decision_tree_step: "standards/decision-trees/automation-selection.md Cheat sheet, 'Approval chain' row (Approval Process -> Flow post-approval; never Apex custom approval)"
    sharing_impact: "Approvers lock the record while it is pending; submitters must still see it"
    sharing_layer: "Manual / Apex"
    priority: Must
    status: confirmed
    downstream:
      story: STORY-003
      fit_gap_row: FG-003
      workbook_section: "6. Automation"

  - id: REQ-004
    statement: "When a return is agreed, the credit reaches the ERP without anyone retyping it, and the ERP's credit memo number comes back onto the return."
    type: functional
    source_stakeholder: "Marcus Bell — Financial Controller"
    objects: [Return__c]
    fields: [Return__c.ERP_Credit_Memo__c, Return__c.ERP_Sync_Status__c]
    automation_candidate: "Approval outcome -> Queueable Apex with AllowsCallouts, Named Credential to the ERP"
    decision_tree_step: "standards/decision-trees/integration-pattern-selection.md Direction 1 Q1 ('No, fire-and-forget' -> Queueable with AllowsCallouts) + Q2 (Named Credential auth)"
    data_volume: "~4,200 outbound calls per month; no burst above 60 per hour observed"
    priority: Must
    status: confirmed
    downstream:
      story: STORY-004
      fit_gap_row: FG-004
      workbook_section: "9. Integrations"

  - id: REQ-005
    statement: "Overnight, the ERP tells Salesforce which returned parts were physically received, so branches stop chasing goods that are already back."
    type: functional
    source_stakeholder: "Marcus Bell — Financial Controller"
    objects: [Return__c]
    fields: [Return__c.Goods_Received_Date__c]
    automation_candidate: "Bulk API 2.0 nightly ingest keyed on an External Id"
    decision_tree_step: "standards/decision-trees/integration-pattern-selection.md Direction 2 Q5 (volume) + Q6 (batch/nightly -> Bulk API 2.0); automation-selection.md Q11 (large volume, one-way replication)"
    data_volume: "~900 rows per night; month-end peak observed at ~3,100"
    priority: Should
    status: confirmed
    downstream:
      story: STORY-005
      workbook_section: "9. Integrations"

  - id: REQ-006
    statement: "The credit value is visible to finance and to warehouse managers, but not to branch clerks, on returns they can already open."
    type: functional
    source_stakeholder: "Marcus Bell — Financial Controller"
    objects: [Return__c]
    fields: [Return__c.Credit_Value__c]
    sharing_impact: "Field-level, not record-level: clerks still open the record"
    sharing_layer: "Field-Level Security"
    priority: Must
    status: confirmed
    downstream:
      story: STORY-006
      workbook_section: "4. Profiles and Permission Sets"

  - id: REQ-007
    statement: "A branch sees its own returns; a regional manager sees every branch in their region; nobody sees another region by default."
    type: functional
    source_stakeholder: "Priya Ramesh — Warehouse Manager, Midlands"
    objects: [Return__c]
    sharing_impact: "Record access, designed as a stack rather than a single rule"
    sharing_layer: "Role Hierarchy"
    decision_tree_step: "standards/decision-trees/sharing-selection.md 7-step sequence steps 1-2 (OWD Private, then Role Hierarchy) with Q3 confirming no criteria-based rule is needed"
    priority: Must
    status: confirmed
    downstream:
      story: STORY-007
      fit_gap_row: FG-007
      workbook_section: "5. Sharing and Visibility"

  - id: REQ-008
    statement: "A distributor raises its own return and sees only the returns it raised, without phoning a branch."
    type: functional
    source_stakeholder: "Dana Okafor — Branch Operations Lead, Leeds"
    objects: [Return__c, Account, Contact]
    sharing_impact: "External user access is not the internal model; sharing sets and the site's guest/authenticated split apply"
    sharing_layer: "Sharing Rules"
    decision_tree_step: "standards/decision-trees/sharing-selection.md 'Experience Cloud sharing — a different world'"
    licence_implication: "Partner Community (or Partner Community Login) for ~60 distributors; not an internal Salesforce licence"
    priority: Should
    status: draft
    downstream:
      fit_gap_row: FG-008
      workbook_section: "5. Sharing and Visibility"

  - id: REQ-009
    statement: "The GM wants one weekly view of returns by branch and reason, showing the original order line each return came from, including returns that have no matching order line."
    type: functional
    source_stakeholder: "Alan Whitcombe — General Manager"
    objects: [Return__c, Account, Order, OrderItem]
    priority: Should
    status: blocked
    notes: "Base object Return__c plus three joins reaches the four-object ceiling exactly; the 'including returns with no matching order line' clause forces an outer join, after which no later join may be inner. Prove the chain with admin/report-type-strategy before committing."
    downstream:
      fit_gap_row: FG-009
      workbook_section: "8. Reports and Dashboards"

  - id: REQ-010
    statement: "Returns volume: the process must absorb normal branch activity and a one-off load of historical returns at go-live without failing part-way."
    type: nfr
    source_stakeholder: "Dana Okafor — Branch Operations Lead, Leeds"
    measure: "4,200 records/month steady state; 18,000-row historical load at go-live; largest observed single day 310"
    data_volume: "18,000-row backfill is the sizing case, not the 4,200"
    priority: Must
    status: confirmed
    downstream:
      workbook_section: "10. Data"

  - id: REQ-011
    statement: "Nightly ERP receipt confirmations must be applied before the branches open."
    type: nfr
    source_stakeholder: "Marcus Bell — Financial Controller"
    measure: "~900 rows/night, month-end peak ~3,100; must complete inside a 03:00-06:00 window"
    priority: Should
    status: confirmed
    downstream:
      workbook_section: "9. Integrations"

  - id: REQ-012
    statement: "The solution must be affordable for a partner population that logs in occasionally."
    type: nfr
    source_stakeholder: "Alan Whitcombe — General Manager"
    measure: "140 internal users; ~60 distributor accounts averaging 3 logins/month each"
    licence_implication: "Login-based partner licensing is the cost-shaped option; API allocation per external licence differs sharply from an internal one"
    priority: Should
    status: draft
    downstream:
      fit_gap_row: FG-012

  - id: REQ-013
    statement: "Nobody can explain what the spreadsheet HOLD? column means or who sets it."
    type: functional
    source_stakeholder: "Dana Okafor — Branch Operations Lead, Leeds"
    priority: Could
    status: blocked
    notes: "Do not carry forward as a checkbox. Owner: Dana Okafor, decision needed before sprint 2 planning. If it turns out to mean 'waiting for the customer to send the part back', it is already covered by REQ-005."
    downstream:
      fit_gap_row: FG-013
```

**How to read it**

- `id` is permanent. It is the join key the RTM (`admin/requirements-traceability-matrix`) uses to
  reach story ids, test ids and defect ids. Renumbering breaks traceability retroactively.
- `statement` is the outcome in the stakeholder's words after the Solution-to-Requirement Rewind —
  never "build a trigger", never a field name in a sentence.
- `automation_candidate` is a hypothesis; `decision_tree_step` is the evidence for it. A row with the
  first and not the second is a preference wearing a decision's clothes, and the linter fails it.
- `sharing_impact` describes the ask; `sharing_layer` names which of the seven ordered layers is
  being asked for. REQ-006 and REQ-007 are deliberately separate rows: one is field access, one is
  record access.
- `status: blocked` (REQ-009, REQ-013) is a legitimate finished state for discovery. It carries an
  owner and a decision date. Silently deleting the row is not.
- `type: nfr` rows carry `measure` — a number with a unit. An NFR without a number is an opinion.

---

## 3. NFR sheet

Each row pairs the elicited requirement with the platform fact that bounds it. The fact is written
down so the next person does not have to re-derive it, and so an over-promise is visible on the page.

| NFR class | Requirement (`REQ-`) | Bounding platform fact | Consequence for design |
|---|---|---|---|
| Record volume | REQ-010: 4,200/month steady, 18,000-row go-live backfill | Per-transaction limits are shared by Flow and Apex — 100 SOQL synchronous / 200 asynchronous, 50,000 rows retrieved, 150 DML statements, 10,000 records processed by DML (App Limits, *Per-Transaction Apex Limits*) | The backfill, not the monthly rate, sets the design. Load in batches; do not let the REQ-002 owner-assignment Flow be the thing that discovers this. |
| Data movement | REQ-010: the 18,000-row load | "Any data operation that includes more than 2,000 records is a good candidate for Bulk API 2.0… Jobs with fewer than 2,000 records should involve 'bulkified' synchronous calls in REST (for example, Composite) or SOAP" (App Limits, *Bulk API and Bulk API 2.0 Limits and Allocations*) | 18,000 rows is a Bulk API 2.0 load, not a Data Loader SOAP run. Data Loader's import batch size maxes at 200 for SOAP and 10,000 for Bulk API, and Bulk API 2.0 sets it automatically (Data Loader Guide, *Settings*). |
| Data movement (ceiling) | REQ-011: nightly ingest | 15,000 batches per rolling 24 h, shared between Bulk API and Bulk API 2.0; 150,000,000 records uploaded per 24 h rolling period (App Limits, *Batch Allocations*, *Limits Specific to Ingest Jobs*) | 900–3,100 rows a night is nowhere near the ceiling. Record it anyway: it is the number that makes "can we also sync invoices?" answerable next quarter. |
| Integration | REQ-004 outbound, REQ-005 inbound | Total API calls per 24 h in Enterprise Edition = 100,000 + (number of licences × calls per licence type) + purchased API Call Add-Ons; a Salesforce licence contributes 1,000 per 24 h in EE and 5,000 in Unlimited/Performance (App Limits, *API Request Limits and Allocations*) | 140 internal licences in EE give a large headroom against ~4,200 outbound calls/month. The number to watch is the partner population, below. |
| Sharing / visibility | REQ-006 (field), REQ-007 (record), REQ-008 (external) | The seven ordered layers in `standards/decision-trees/sharing-selection.md`; Experience Cloud is explicitly "a different world" in that tree | Three requirements, three different mechanisms. Writing them as one "only the right people see returns" row is how a project ends up with a sharing rule where it needed FLS. |
| Reporting | REQ-009 | "A maximum of four objects can be joined in a custom report type. When more than two objects are joined, an inner join isn't allowed if there has been an outer join earlier in the join sequence" (Metadata API Developer Guide, `ObjectRelationship`) | `Return__c → Account → Order → OrderItem` is exactly four. The "including returns with no matching order line" clause makes the first join outer, so every later join must be outer too. Prove it in `admin/report-type-strategy` before it is promised to the GM. |
| Licence / persona | REQ-008, REQ-012 | API calls per licence per 24 h: Customer Community 0, Customer Community Login 0, Customer Community Plus 200, Partner Community 200, Partner Community Login 10, Salesforce 1,000 (EE) (App Limits, *API Request Limits and Allocations*) | A partner licence contributes a fraction of an internal one, and the Login variants contribute 10. If the distributor portal is ever expected to drive API traffic, the licence choice is the constraint — decided now, not after the site is built. |
| Storage | not yet an NFR | The Developer Limits quick reference states it does not cover contractual limits | Read data and file storage from the org's own Storage Usage page. Do not quote a storage figure from a limits guide; there isn't one to quote. |
| Mobile / offline | not yet an NFR | UNVERIFIED (2026-09-04): no offline-entry limit or allocation appears in the eight extracted Salesforce guides used to ground this skill | Branch clerks are at a desk; warehouse staff may not be. Confirm the org's mobile configuration before any requirement promises offline entry, and mark the row `blocked` until it is confirmed. |

---

## 4. As-Is / To-Be summary

This is the table, not the diagram. Hand it to `admin/process-flow-as-is-to-be` (or
`agents/process-flow-mapper/AGENT.md`, input `process_narrative_path`) for the swim-lane version with
decision diamonds, sad paths and automation-tier annotations.

| # | Actor | As-Is (today) | Pain point | To-Be (Salesforce) | `REQ-` generated |
|---|---|---|---|---|---|
| 1 | Branch clerk | Types customer, part, reason into a row on the shared sheet | No history, no validation, two clerks overwrite each other | Creates a `Return__c` from the Account | REQ-001 |
| 2 | Branch clerk | Types the branch name into a column | Free text; "Leeds", "LEEDS", "Leeds Br." all exist | `Branch__c` set from the user, owner assigned automatically | REQ-002 |
| 3 | Supervisor | Colours the row green | No record of who approved or when; colour is lost on copy-paste | Approval Process; approver and timestamp on the record | REQ-003 |
| 4 | Finance | Reads the green rows, keys a credit memo into the ERP | Manual rekeying, 2–3 day lag, transcription errors | Approval outcome fires the ERP callout; memo number returns to the record | REQ-004 |
| 5 | Warehouse | Emails the branch when the part physically arrives | Branches chase parts already on the shelf | Nightly ERP ingest stamps `Goods_Received_Date__c` | REQ-005 |
| 6 | Distributor | Phones a branch, who types the row on their behalf | Branch time spent as a data-entry service | Distributor raises the return directly on the partner site | REQ-008, REQ-012 |
| 7 | GM | Asks a clerk to filter the sheet on Monday morning | Numbers differ from week to week depending on who filtered | Report on a purpose-built report type | REQ-009 |
| 8 | Everyone | Sets the `HOLD?` column | Nobody can define it | Not carried forward until defined | REQ-013 |

**Transition state** (the state the methodology requires and packages usually omit): for the first two
weeks after go-live, returns raised before cutover stay in the spreadsheet and are worked there to
completion; only new returns are raised in Salesforce. The `18,000-row` historical load (REQ-010) runs
read-only for reporting, with `Approval_Status__c` pre-set and automation bypassed, so the backfill
does not fire 18,000 approval submissions.

---

## 5. Handoff map

Every row has exactly one primary target. A row with no target is a dropped requirement.

| Target | Reads | Rows | Why this target |
|---|---|---|---|
| `agents/story-drafter/AGENT.md` (`/draft-stories`) | `discovery_artifact_path` = the catalogue, `discovery_artifact_kind: requirements-list` | REQ-001 … REQ-007 | Confirmed functional rows with an object and a persona; the agent needs ≥5 distinct requirements or it stops and asks |
| `agents/fit-gap-analyzer/AGENT.md` (`/run-fit-gap`) | `backlog_path` = the drafted stories, `target_org_alias` required | REQ-003, REQ-004, REQ-008, REQ-009, REQ-012, REQ-013 | Rows whose feasibility depends on the actual org — licences, an ERP boundary, a join chain, and the two `blocked` rows |
| `agents/process-flow-mapper/AGENT.md` (`/map-process-flow`) | `process_narrative_path` = the As-Is/To-Be summary above, `process_kind: as-is-to-be` | all 8 process steps | Owns the swim lanes; this skill only supplies the step table |
| `agents/config-workbook-author/AGENT.md` (`/author-config-workbook`) | confirmed rows grouped by workbook section | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-010, REQ-011 | The 10-section admin handoff; each row already carries its `workbook_section` |
| `admin/report-type-strategy` | REQ-009's base object and join chain | REQ-009 | The four-object ceiling and outer-join ordering must be proved before the report is promised |
| `architect/license-optimization-strategy` | `licence_implication` values | REQ-008, REQ-012 | Partner licence type and count is a costing decision, not a BA decision |
| `admin/requirements-traceability-matrix` | every `id` | all 13 | Forward traceability from `REQ-` to story, test and defect ids |

---

## 6. Lint before handing off

```bash
# lint a single catalogue
python3 skills/admin/requirements-gathering-for-sf/scripts/check_requirements_catalogue.py \
  --file docs/discovery/requirements-catalogue.yaml

# lint every catalogue in a discovery folder (.yaml/.yml, and .md files with a yaml fence)
python3 skills/admin/requirements-gathering-for-sf/scripts/check_requirements_catalogue.py \
  --manifest-dir docs/discovery/

# exit code 0 = no ERRORs (WARNs may still be printed); exit code 1 = at least one ERROR
```

The linter fails the handoff on: a missing required field, a duplicate or malformed `id`, a priority
outside the MoSCoW set, a status outside the allowed set, a row with no `source_stakeholder`, a row
with no `downstream` target, an `automation_candidate` with no `decision_tree_step`, a
`sharing_impact` with no recognised `sharing_layer`, and a `type: nfr` row with no `measure`. It also
checks that any repo path named inside `decision_tree_step` actually resolves.
