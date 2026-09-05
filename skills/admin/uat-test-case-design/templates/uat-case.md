# UAT Test Case Template

Four formats: a YAML record (the shape `scripts/check_uat_case.py` reads natively and the one
`references/worked-examples.md` uses), a markdown skeleton (humans), a JSON envelope
(machines / RTM ingest), and a CSV import schema (bulk authoring in a spreadsheet).

All four encode the same canonical schema. Two fields carry most of the weight and are worth
copying carefully: **every step has its own `expected`**, and every case declares an
`automation_candidate` of `apex`, `flow-test` or `none` with the reason. The checker fails a
step with no expected result and an automation verdict outside that enum.

---

## Format 0 — YAML Record (preferred)

```yaml
project: "<release name>"
sandbox: "<sandbox name>"
test_cases:
  - case_id: TC-XXX-001            # unique; TC- or UAT- prefix, letters/digits/hyphens
    ac_id: AC-001.1                # must resolve to a criterion in the criteria file
    req_id: REQ-001
    story_id: US-XX-01
    programme_case_id: UAT-XX-001  # the RTM's test_id, when the programme minted one
    persona: "<persona id> — <profile> + <grant>"   # never an administrator, never generic
    sandbox: "<sandbox name>"
    negative_path: false           # >= 1 true per requirement
    permission_setup:
      - "Assign <grant>"
      - "PermissionSetGroup <name> Status = Updated before login"
      - "DO NOT assign System Administrator to the tester"
    data_setup:
      - "<record or import to seed, in order>"
    precondition: "<sandbox, build date, form factor, login state>"
    steps:
      - step: "<what the tester does — a Setup destination, a record action, a query>"
        expected: "<what they observe: a field value, a row, a message, a file line>"
      - step: "<...>"
        expected: "<...>"
    evidence:
      - type: screenshot           # screenshot | soql | email-log | loader-csv | history-row
        of: "<what the artefact shows>"
    pass_rule: "<which steps must all hold; name the near-miss that is still a fail>"
    automation_candidate: none     # apex | flow-test | none
    automation_rationale: "<the platform fact behind the verdict>"
    actual_result: ""
    pass_fail: "Not Run"           # Pass | Fail | Blocked | Not Run

  # The skeleton is a PAIR, not a single case: the checker fails a requirement
  # with no negative case, so copy this one too rather than deleting it.
  - case_id: TC-XXX-002
    ac_id: AC-001.3
    req_id: REQ-001
    story_id: US-XX-01
    persona: "<persona id> — <profile> + <grant>"
    sandbox: "<sandbox name>"
    negative_path: true
    permission_setup:
      - "Assign <grant>"
      - "DO NOT assign <the grant being withheld> — the absence is the test condition"
      - "Confirm neither viewAllRecords nor modifyAllRecords is set on the object for that grant"
    data_setup:
      - "<the record the persona must not reach>"
    precondition: "<sandbox, build date, form factor, login state>"
    steps:
      - step: "<attempt the action through the path the persona uses>"
        expected: "<the specific refusal — a message, an empty result, a false flag>"
      - step: "<attempt it through the path that bypasses the list view, e.g. the record id>"
        expected: "<still refused>"
    evidence:
      - type: screenshot
        of: "<the refusal>"
      - type: soql
        of: "<the query that records why it was refused>"
    pass_rule: "<both refusal steps; the list-view step alone is not a deny>"
    automation_candidate: apex
    automation_rationale: "<the platform fact behind the verdict>"
    actual_result: ""
    pass_fail: "Not Run"
run_sheet:
  - run_id: R-001
    case_id: TC-XXX-001
    tester: "<username>"
    executed_on: "<YYYY-MM-DD>"
    result: "Not Run"
    evidence_ref: ""
    defect_id: ""                  # never on a Blocked row
    notes: ""
```

Lint it before anyone runs it:

```bash
python3 scripts/check_uat_case.py --file uat-cases.yaml
python3 scripts/check_uat_case.py --manifest-dir ./uat/           # cross-checks ac_ids and run-sheet rows
python3 scripts/check_uat_case.py --manifest-dir ./uat/ --rtm-gate
```

---

## Format 1 — Markdown Skeleton

Copy this block per case. Fields above the `---` are authored before the run.
Fields below the `---` are filled in at execution time.

```markdown
### Case `<UAT-XXX-NNN>`

- **story_id:** `<STORY-XXX>`
- **ac_id:** `<AC-XXX-N>`
- **persona:** `<Profile name + PSG, e.g. "Sales Rep — Pipeline Edition">`
- **negative_path:** `false`   <!-- set true for at least one case per story -->
- **precondition:** `<Sandbox name, login user, record state — one paragraph>`

**data_setup**
1. `<Record or import to seed before steps>`
2. `<...>`

**permission_setup**
1. `<PSG to assign>`
2. `<DO NOT assign: System Administrator>`

**steps**
1. `<Click-level step 1>`
2. `<Click-level step 2>`
3. `<...>`

**expected_result**

> `<Verbatim from the AC's "then" clause>`

---

**actual_result:** `<filled at run>`
**pass_fail:** `<Pass | Fail | Blocked | Not Run>`
**evidence_url:** `<link to screenshot or recording>`
**tester:** `<username>`
**executed_at:** `<ISO 8601 UTC timestamp>`
```

---

## Format 2 — JSON Envelope

Suitable for ingestion into the RTM tool, the test management platform, or an LLM-driven generator. One object per case; case sets are an array on `cases`.

```json
{
  "schema_version": "1.0",
  "release": "RELEASE-2026.05",
  "sandbox": "UAT-Full",
  "cases": [
    {
      "case_id": "UAT-OPP-001",
      "story_id": "STORY-734",
      "ac_id": "AC-734-1",
      "persona": "Sales Rep — Pipeline Edition",
      "negative_path": false,
      "precondition": "Tester is logged into UAT-Full sandbox as the seeded Sales Rep user with Sales_Pipeline_PSG assigned.",
      "data_setup": [
        "Seed Account 'Acme Co' with Industry = Manufacturing",
        "Seed Opportunity 'Acme Q2 Renewal' on that Account, StageName = 'Negotiation', CloseDate = today + 7"
      ],
      "permission_setup": [
        "Assign Sales_Pipeline_PSG to the tester user",
        "DO NOT assign System Administrator profile"
      ],
      "steps": [
        "Open the Sales app and navigate to the 'Acme Q2 Renewal' Opportunity",
        "Click the Stage path and select 'Closed Won'",
        "Mark Stage as Complete and confirm"
      ],
      "expected_result": "Opportunity StageName = Closed Won, IsWon = true, a Task with subject 'Post-Sale Follow-Up' is auto-created on the parent Account due in 7 days",
      "actual_result": "",
      "pass_fail": "Not Run",
      "evidence_url": "",
      "tester": "",
      "executed_at": ""
    }
  ]
}
```

### Field Contract

| Field | Type | Required at author time | Notes |
|---|---|---|---|
| `case_id` | string | yes | unique within release |
| `story_id` | string | yes | RTM key |
| `ac_id` | string | yes | RTM key (story_id + ac_id closes a row) |
| `persona` | string | yes | named profile + PSG; never "System Administrator" |
| `negative_path` | boolean | yes | ≥1 per story must be `true` |
| `precondition` | string | yes | non-empty |
| `data_setup` | array of strings | yes | non-empty |
| `permission_setup` | array of strings | yes | non-empty |
| `steps` | array | yes | each entry `{step, expected}`; every step needs its own expected result |
| `evidence` | array | yes | what closes the case: screenshot / soql / email-log / loader-csv / history-row |
| `pass_rule` | string | yes | which steps must all hold; no "looks correct" |
| `automation_candidate` | enum | yes | `apex`, `flow-test` or `none` |
| `automation_rationale` | string | when not `none` | the platform fact behind the verdict |
| `expected_result` | string | optional | case-level summary; the per-step `expected` values are the contract |
| `actual_result` | string | filled at run | |
| `pass_fail` | enum | filled at run | one of `Pass`, `Fail`, `Blocked`, `Not Run` |
| `evidence_url` | string | required at run if pass_fail in {Pass, Fail} | |
| `tester` | string | filled at run | |
| `executed_at` | string (ISO 8601) | filled at run | UTC |

---

## Format 3 — CSV Import Schema

For authors who prefer Google Sheets / Excel for bulk authoring. One case per row.
Multi-value fields are pipe-delimited (`|`) within a single cell.

```csv
case_id,story_id,ac_id,persona,negative_path,precondition,data_setup,permission_setup,steps,expected_result,actual_result,pass_fail,evidence_url,tester,executed_at
UAT-OPP-001,STORY-734,AC-734-1,Sales Rep — Pipeline Edition,false,"Tester is logged into UAT-Full sandbox as the seeded Sales Rep user with Sales_Pipeline_PSG assigned.","Seed Account 'Acme Co' with Industry = Manufacturing|Seed Opportunity 'Acme Q2 Renewal' on that Account, StageName = 'Negotiation', CloseDate = today + 7","Assign Sales_Pipeline_PSG to the tester user|DO NOT assign System Administrator profile","Open the Sales app and navigate to the 'Acme Q2 Renewal' Opportunity|Click the Stage path and select 'Closed Won'|Mark Stage as Complete and confirm","Opportunity StageName = Closed Won, IsWon = true, a Task with subject 'Post-Sale Follow-Up' is auto-created on the parent Account due in 7 days",,Not Run,,,
UAT-OPP-002,STORY-734,AC-734-2,Sales Rep — Read Only,true,"Tester is logged in to UAT-Full sandbox as the Read Only user with NO Sales_Pipeline_PSG.","Reuse the 'Acme Q2 Renewal' Opportunity from UAT-OPP-001","Confirm Sales_Pipeline_PSG is NOT assigned to the tester user|DO NOT assign System Administrator profile","Open the Sales app and navigate to the 'Acme Q2 Renewal' Opportunity|Attempt to click the Stage path and select 'Closed Won'","The Stage path is read-only or the save fails with the validation error 'Only Pipeline-Edition reps can advance the stage'",,Not Run,,,
```

### CSV Authoring Rules

- Pipe (`|`) separates list entries within `data_setup`, `permission_setup`, and `steps`. The check script splits on `|` when ingesting.
- Quotes around any cell that contains a comma, pipe, or newline.
- `negative_path` is the literal string `true` or `false` (lowercase).
- `pass_fail` defaults to `Not Run` at authoring time.
- Empty trailing fields (`actual_result` through `executed_at`) are intentional — they fill at run time.

---

## Handoff to RTM

Once `pass_fail` is set to `Pass` and `evidence_url` is non-empty, the case is
RTM-ready. Push the row keyed by `(story_id, ac_id, case_id)` into the RTM cell.
A cell is closed when:

1. ≥1 case for the AC has `pass_fail: Pass`, AND
2. ≥1 case for the parent story has `pass_fail: Pass` AND `negative_path: true`.

Both conditions are enforced by `scripts/check_uat_case.py` when run in
`--rtm-gate` mode, which reads the **latest** run-sheet row per case — so a re-run
after a fix is a new row and the failing row stays as the evidence the defect was
raised against.
