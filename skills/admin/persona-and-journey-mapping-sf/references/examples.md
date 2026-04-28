# Examples — Persona And Journey Mapping (Salesforce-Anchored)

Three worked personas + journeys spanning mobile-heavy, desktop-heavy, and
queue-driven postures.

---

## Example 1: Outside Sales Rep (Mobile-Heavy)

**Context:** Field sales org, 42 reps in territory. Reps log 6–10 customer
visits per day from a phone between meetings, then triage the queue at night
on a laptop.

**Problem (without anchored persona):** prior persona work assumed reps were
"50/50 mobile vs desktop" — actual measurement from EventLogFile UriEvent
showed 70% mobile, 30% desktop. Record page redesign had been built for
desktop-density. Reps were tab-switching mid-visit because Visit Type required
manual entry on mobile.

**Anchored persona:**

```json
{
  "persona_id": "outside_sales_rep",
  "name": "Outside Sales Rep",
  "headcount": 42,
  "psg_assigned": "PSG_Sales_Field",
  "primary_record_types": ["Account.Customer", "Opportunity.Field_Deal", "Visit__c.Standard"],
  "primary_list_views": ["My_Open_Opps_This_Week", "Visits_Due_Today"],
  "dashboards": ["Field_Sales_Daily"],
  "mobile_pct": 70,
  "desktop_pct": 30,
  "automation_touched": [
    "Flow:Visit_After_Save",
    "ValidationRule:Opp.Field_Stage_Required_Fields",
    "AssignmentRule:Lead_Field_Territory"
  ]
}
```

**Journey: log a customer visit (daily, ~8x/day):**

```json
{
  "persona_id": "outside_sales_rep",
  "task": "Log a customer visit between meetings",
  "frequency": "daily",
  "steps": [
    {"step": "Open Salesforce mobile app", "surface": "mobile"},
    {"step": "Tap Visits Due Today list view", "surface": "mobile"},
    {"step": "Open visit record", "surface": "mobile"},
    {"step": "Tap Log Visit Quick Action", "surface": "mobile"},
    {"step": "Enter Visit Type, Notes, Next Step", "surface": "mobile", "friction": "data_input"},
    {"step": "Save", "surface": "mobile"},
    {"step": "Return to list view", "surface": "mobile"}
  ],
  "friction_points": [
    {"step_index": 4, "tag": "data_input", "note": "No default for Visit Type; territory not pre-populated"}
  ],
  "desired_outcome": "Visit logged in <60s without leaving mobile",
  "next_task": "Drive to next account and repeat"
}
```

**Why it works:** the `mobile_pct` is measured (UriEvent), the `friction` tag
is in the fixed enum (`data_input`), the journey ends at the next task (not
"save"), and the friction routes cleanly to record-page-auditor with a
concrete intervention (default Visit Type from territory).

---

## Example 2: Inside Sales SDR (Desktop-Heavy)

**Context:** SDR pod of 18, dialing inbound leads from a queue all day at a
desk. Mobile usage near zero except for after-hours email triage.

**Anchored persona:**

```json
{
  "persona_id": "inside_sdr",
  "name": "Inside Sales SDR",
  "headcount": 18,
  "psg_assigned": "PSG_SDR_Pod",
  "primary_record_types": ["Lead.Inbound_MQL", "Task.Call", "Opportunity.SDR_Created"],
  "primary_list_views": ["My_New_Leads_This_Hour", "My_Open_Tasks_Today"],
  "dashboards": ["SDR_Daily_Pipeline", "SDR_Conversion_Funnel"],
  "mobile_pct": 5,
  "desktop_pct": 95,
  "automation_touched": [
    "AssignmentRule:Lead_Round_Robin",
    "Flow:Lead_Convert_To_Opp",
    "ValidationRule:Lead.Disposition_Required_On_Convert"
  ]
}
```

**Journey: triage one inbound MQL (daily, ~80x/day):**

```json
{
  "persona_id": "inside_sdr",
  "task": "Triage one inbound MQL from queue",
  "frequency": "daily",
  "steps": [
    {"step": "Open My_New_Leads_This_Hour list view", "surface": "desktop"},
    {"step": "Open top lead", "surface": "desktop"},
    {"step": "Scan firmographic and engagement panels", "surface": "desktop", "friction": "cognitive_load"},
    {"step": "Click Log a Call quick action", "surface": "desktop"},
    {"step": "Disposition + outcome", "surface": "desktop"},
    {"step": "Save", "surface": "desktop"},
    {"step": "Return to list view, open next lead", "surface": "desktop"}
  ],
  "friction_points": [
    {"step_index": 2, "tag": "cognitive_load", "note": "Lead page has 11 sections; SDR only needs 3"}
  ],
  "desired_outcome": "Disposition logged in <90s",
  "next_task": "Open next lead from list view"
}
```

**Why it works:** Dynamic Forms with a role-based visibility rule cuts the
SDR-visible page to 3 sections; routes to `lightning-record-page-auditor`.

---

## Example 3: Service Agent (Queue-Driven, Dashboard-Heavy)

**Context:** Tier-1 contact center, 60 agents, omnichannel queue. Heavy
dashboard consumption (queue depth, SLA breach risk).

**Anchored persona:**

```json
{
  "persona_id": "service_agent_t1",
  "name": "Tier-1 Service Agent",
  "headcount": 60,
  "psg_assigned": "PSG_Service_Tier1",
  "primary_record_types": ["Case.Customer_Inquiry", "Case.Complaint"],
  "primary_list_views": ["My_Open_Cases", "Queue_Tier1_Backlog"],
  "dashboards": ["Service_Console_Live", "Tier1_SLA_Heatmap"],
  "mobile_pct": 2,
  "desktop_pct": 98,
  "automation_touched": [
    "Flow:Case_Auto_Categorize",
    "ValidationRule:Case.Reason_Required_On_Close",
    "AssignmentRule:Case_Omnichannel_Routing"
  ]
}
```

**Journey: handle one case from queue (daily, ~50x/day):**

```json
{
  "persona_id": "service_agent_t1",
  "task": "Handle one case routed via Omnichannel",
  "frequency": "daily",
  "steps": [
    {"step": "Accept case from Omnichannel widget", "surface": "desktop"},
    {"step": "Read case description, scan related cases panel", "surface": "desktop"},
    {"step": "Open KB Search side panel", "surface": "desktop", "friction": "search"},
    {"step": "Reply to customer via Email Quick Action", "surface": "desktop"},
    {"step": "Update Case Reason + Status", "surface": "desktop"},
    {"step": "Close case", "surface": "desktop"},
    {"step": "Wait for next Omnichannel route", "surface": "desktop"}
  ],
  "friction_points": [
    {"step_index": 2, "tag": "search", "note": "KB Search returns 60+ results, no filter on Case.Reason"}
  ],
  "desired_outcome": "Case closed inside SLA",
  "next_task": "Accept next case from Omnichannel"
}
```

**Why it works:** `search` friction routes cleanly to
`list-view-and-search-layout-auditor` with a concrete intervention (filter
KB Search results by Case Reason).

---

## Anti-Pattern: Title-Based Persona ("Sales Rep")

**What practitioners do:** write a "Sales Rep" persona with no PSG, no record
types, no dashboard, and a guessed mobile_pct.

**What goes wrong:** outside reps and SDRs collapse into one persona; the
record page redesign optimizes for nobody. Friction backlog has no concrete
routing target. UAT test design has no persona to bind cases to.

**Correct approach:** split into `outside_sales_rep` and `inside_sdr`, each
anchored to its own PSG and measured posture, as shown above.
