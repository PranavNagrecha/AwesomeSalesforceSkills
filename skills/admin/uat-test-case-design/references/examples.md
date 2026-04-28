# Examples — UAT Test Case Design

These three example case sets illustrate the canonical schema in three flavors:
record-state UI flow, bulk import via Data Loader, and Lightning record page render.
Each set includes a happy-path case and a paired negative-path case so the story is
fully covered.

---

## Example 1: Opportunity Stage Update — Happy Path + Permission Deny

**Context:** Story `STORY-734` requires that a "Sales Rep — Pipeline Edition" persona
can advance an Opportunity from `Negotiation` to `Closed Won`, but a "Sales Rep —
Read Only" persona cannot. AC has two scenarios in Given/When/Then form
(`AC-734-1` happy, `AC-734-2` deny).

**Problem without this skill:** The team writes a single case that runs as System
Administrator, advances the stage, and declares the feature works. The deny path
is never tested. A real Read Only rep can advance the stage in production because
the validation rule was scoped to the wrong custom permission.

**Solution — Case 1 (happy path):**

```yaml
case_id: UAT-OPP-001
story_id: STORY-734
ac_id: AC-734-1
persona: "Sales Rep — Pipeline Edition"
negative_path: false
precondition: "Tester is logged into UAT-Full sandbox as the seeded Sales Rep user. The user has been assigned the Sales_Pipeline_PSG permission set group. An Opportunity in Negotiation stage exists, owned by the tester."
data_setup:
  - "Seed Account 'Acme Co' with Industry = Manufacturing"
  - "Seed Opportunity 'Acme Q2 Renewal' on that Account, StageName = 'Negotiation', CloseDate = today + 7"
permission_setup:
  - "Assign Sales_Pipeline_PSG to the tester user"
  - "DO NOT assign System Administrator profile to the tester"
steps:
  - "Open the Sales app and navigate to the 'Acme Q2 Renewal' Opportunity"
  - "Click the Stage path and select 'Closed Won'"
  - "Mark Stage as Complete and confirm"
expected_result: "Opportunity StageName = Closed Won, IsWon = true, a Task with subject 'Post-Sale Follow-Up' is auto-created on the parent Account due in 7 days"
actual_result: ""
pass_fail: "Not Run"
evidence_url: ""
tester: ""
executed_at: ""
```

**Solution — Case 2 (negative-path companion, deny):**

```yaml
case_id: UAT-OPP-002
story_id: STORY-734
ac_id: AC-734-2
persona: "Sales Rep — Read Only"
negative_path: true
precondition: "Tester is logged into UAT-Full sandbox as the seeded Read Only user. The user has NOT been assigned Sales_Pipeline_PSG."
data_setup:
  - "Reuse the 'Acme Q2 Renewal' Opportunity from UAT-OPP-001"
permission_setup:
  - "Confirm Sales_Pipeline_PSG is NOT assigned to the tester user"
  - "DO NOT assign System Administrator profile to the tester"
steps:
  - "Open the Sales app and navigate to the 'Acme Q2 Renewal' Opportunity"
  - "Attempt to click the Stage path and select 'Closed Won'"
expected_result: "The Stage path is read-only or the save fails with the validation error 'Only Pipeline-Edition reps can advance the stage'"
actual_result: ""
pass_fail: "Not Run"
evidence_url: ""
tester: ""
executed_at: ""
```

**Why it works:** Two personas, two PSG postures, both AC scenarios proven.
The deny case is what catches the FLS or custom-permission misconfiguration that
a Sys-Admin run would silently bypass.

---

## Example 2: Bulk Lead Import via Data Loader + Duplicate Rule

**Context:** Story `STORY-812` introduces a duplicate rule that blocks new Lead
records sharing an email with an existing Lead in the last 90 days. The feature
has to work both via UI and via Data Loader (`AC-812-1` happy bulk insert,
`AC-812-2` dup rule fires on bulk insert).

**Problem without this skill:** The team tests the dup rule by creating one Lead in
the UI and gets a green pass. In production, the marketing team's nightly
Data Loader run silently inserts 4,000 duplicates because the dup rule was set
to "Allow with alert" for API runs.

**Solution — Case 1 (happy bulk insert):**

```yaml
case_id: UAT-LEAD-001
story_id: STORY-812
ac_id: AC-812-1
persona: "Marketing Ops — Loader User"
negative_path: false
precondition: "Tester is logged into UAT-Full sandbox as marketing-ops-loader@uat.org and authenticated to Data Loader. Lead object is empty for tester-owned records."
data_setup:
  - "Source CSV 'leads-clean-50.csv' with 50 unique Lead rows (FirstName, LastName, Email, Company)"
permission_setup:
  - "Assign Marketing_Ops_Loader_PSG which grants API Enabled, Bulk API Hard Delete, and Lead CRUD"
  - "DO NOT assign System Administrator profile to the tester"
steps:
  - "Open Data Loader, choose 'Insert', select Object = Lead"
  - "Select source file leads-clean-50.csv"
  - "Use auto-mapping; verify Email is mapped"
  - "Run the insert with batch size 200"
  - "Open the success and error CSVs Data Loader writes"
expected_result: "50 success rows in success.csv, 0 rows in error.csv, 50 new Lead records visible under tester ownership"
actual_result: ""
pass_fail: "Not Run"
evidence_url: ""
tester: ""
executed_at: ""
```

**Solution — Case 2 (negative bulk insert with duplicates):**

```yaml
case_id: UAT-LEAD-002
story_id: STORY-812
ac_id: AC-812-2
persona: "Marketing Ops — Loader User"
negative_path: true
precondition: "UAT-LEAD-001 has run and the 50 leads from leads-clean-50.csv exist."
data_setup:
  - "Source CSV 'leads-with-3-dups.csv' containing 10 Lead rows where 3 rows share an email with the leads inserted in UAT-LEAD-001"
permission_setup:
  - "Assign Marketing_Ops_Loader_PSG"
  - "Confirm duplicate rule 'Lead_Email_Duplicate_Block' is Active"
steps:
  - "Open Data Loader, choose 'Insert', select Object = Lead"
  - "Select source file leads-with-3-dups.csv"
  - "Run the insert with batch size 200"
  - "Open success.csv and error.csv"
expected_result: "7 rows in success.csv, 3 rows in error.csv each with the message 'DUPLICATES_DETECTED — A duplicate Lead exists with the same email'"
actual_result: ""
pass_fail: "Not Run"
evidence_url: ""
tester: ""
executed_at: ""
```

**Why it works:** The persona is the human running Data Loader, with their loader
PSG. The negative case proves the rule fires under bulk, not just UI.

---

## Example 3: Lightning Record Page for a Custom Object — Render + Edit + Sharing

**Context:** Story `STORY-905` adds a custom object `Service_Visit__c` and assigns
a new Lightning record page to the "Field Tech" persona on record type
`Onsite_Visit`. AC covers render (`AC-905-1`), inline-edit of the Notes field
(`AC-905-2`), and sharing visibility from a peer Field Tech (`AC-905-3`, deny).

**Problem without this skill:** The team tests render only and as System Admin.
The page renders for the Sys Admin profile, but Field Techs see the default
record page because the page assignment was scoped to the wrong record type.

**Solution — Case 1 (render):**

```yaml
case_id: UAT-SV-001
story_id: STORY-905
ac_id: AC-905-1
persona: "Field Tech"
negative_path: false
precondition: "Tester is logged into UAT-Partial sandbox as field-tech-1@uat.org and assigned the Field Tech profile + Field_Service_Tech_PSG."
data_setup:
  - "Seed Service_Visit__c record SV-100 with RecordType = Onsite_Visit, Owner = field-tech-1, Status = Scheduled"
permission_setup:
  - "Field Tech profile (page-layout assignment + record type access)"
  - "Field_Service_Tech_PSG (object CRUD, FLS on Notes__c)"
  - "DO NOT assign System Administrator profile"
steps:
  - "Open the Service app, navigate to Service Visits, open SV-100"
  - "Confirm the page renders with sections: Visit Details, Customer, Notes, Activity"
  - "Confirm the 'Mark Complete' quick action is visible in the highlights bar"
expected_result: "All four sections render, Notes__c field is editable inline, 'Mark Complete' quick action is visible, Activity timeline shows the seeded record creation event"
actual_result: ""
pass_fail: "Not Run"
evidence_url: ""
tester: ""
executed_at: ""
```

**Solution — Case 2 (inline edit, happy):** structurally identical, persona +
PSG identical, steps focus on inline-edit Notes__c, expected_result quotes the
AC's `then` for AC-905-2.

**Solution — Case 3 (peer sharing deny, negative):**

```yaml
case_id: UAT-SV-003
story_id: STORY-905
ac_id: AC-905-3
persona: "Field Tech (peer)"
negative_path: true
precondition: "Tester is logged into UAT-Partial sandbox as field-tech-2@uat.org. SV-100 is owned by field-tech-1, not the tester. Object OWD is Private."
data_setup:
  - "Confirm SV-100 from UAT-SV-001 still exists, Owner = field-tech-1"
permission_setup:
  - "Field Tech profile + Field_Service_Tech_PSG (same posture as UAT-SV-001)"
steps:
  - "Open the Service app, navigate to Service Visits"
  - "Search for SV-100 in the list view"
  - "Attempt to open SV-100 directly via URL"
expected_result: "SV-100 does not appear in the list view; direct URL navigation returns 'Insufficient privileges' error per Private OWD"
actual_result: ""
pass_fail: "Not Run"
evidence_url: ""
tester: ""
executed_at: ""
```

**Why it works:** Two Field Tech users, same PSG, different ownership — proves
the page renders for the right persona AND that sharing isolates peers.

---

## Anti-Pattern: One Case Per Click

**What practitioners do:** Write a separate UAT case for every individual click in
a flow, producing 40 cases for a 6-step wizard.

**What goes wrong:** Cases drift from AC scenarios. Reviewers cannot tell which
case proves which AC. Run cost balloons. Negative-path coverage is buried.

**Correct approach:** One case per AC scenario per persona. A 6-step wizard
that satisfies one AC scenario is one case with 6 steps in the `steps` array,
not 6 cases. Granularity comes from `ac_id`, not click count.

---

## Anti-Pattern: One Case Per Story

**What practitioners do:** Write a single case per user story that walks through
the entire feature in one breath.

**What goes wrong:** When the case fails, the team cannot tell which AC scenario
broke. Negative paths are typically dropped. RTM cells cannot be closed at AC
granularity.

**Correct approach:** Decompose to AC-scenario level. Each scenario = ≥1 case.
The RTM is keyed at `story_id` + `ac_id`, so cases must match.
