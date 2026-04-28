# Persona + Journey — Authoring Skeleton

Use this skeleton when authoring a Salesforce-anchored persona and its
journeys. All placeholder values are wrapped in `<<...>>`. Replace each one,
then run the skill checker.

---

## Persona

```yaml
persona_id: <<short_snake_case_id>>           # e.g. outside_sales_rep
name: <<Display Name>>                         # e.g. Outside Sales Rep
headcount: <<integer>>                         # e.g. 42
psg_assigned: <<PSG_DeveloperName>>            # MUST match a real or planned PSG
primary_record_types:                          # ≥1 entry, each "Object.RecordType"
  - <<Object.RecordType>>
primary_list_views:                            # ≥1 entry, prefer shared list views
  - <<List_View_API_Name>>
dashboards:                                    # ≥1 entry, dashboard developer name
  - <<Dashboard_DeveloperName>>
mobile_pct: <<int 0-100>>                      # measured, not guessed
desktop_pct: <<int 0-100>>                     # mobile_pct + desktop_pct must ≈ 100
posture_source: <<measurement source>>         # e.g. "EventLogFile UriEvent 30d"
automation_touched:                            # Flow/VR/Assignment/Approval that fires for them
  - <<Flow:DeveloperName>>
  - <<ValidationRule:Object.DeveloperName>>
```

## Persona JSON Form

```json
{
  "persona_id": "<<short_snake_case_id>>",
  "name": "<<Display Name>>",
  "headcount": 0,
  "psg_assigned": "<<PSG_DeveloperName>>",
  "primary_record_types": ["<<Object.RecordType>>"],
  "primary_list_views": ["<<List_View_API_Name>>"],
  "dashboards": ["<<Dashboard_DeveloperName>>"],
  "mobile_pct": 0,
  "desktop_pct": 100,
  "posture_source": "<<measurement source>>",
  "automation_touched": ["<<Flow:DeveloperName>>"]
}
```

---

## Journey (one per persona-task pair)

```yaml
persona_id: <<must match a persona above>>
task: <<one task, present tense, no system events>>
frequency: <<daily | weekly | monthly | quarterly>>
steps:                                        # ≥3 entries
  - step: <<what the user does>>
    surface: <<mobile | desktop | console>>
  - step: <<next action>>
    surface: <<mobile | desktop | console>>
    friction: <<one of: cognitive_load | click_count | mode_switch | data_input | search>>
  - step: <<next action>>
    surface: <<mobile | desktop | console>>
friction_points:                              # cross-reference step indices
  - step_index: <<int>>
    tag: <<one of fixed enum>>
    note: <<concrete description>>
desired_outcome: <<what done looks like>>
next_task: <<what the persona does next — required, never blank>>
```

## Journey JSON Form

```json
{
  "persona_id": "<<must match a persona>>",
  "task": "<<one task>>",
  "frequency": "daily",
  "steps": [
    {"step": "<<step text>>", "surface": "mobile"},
    {"step": "<<step text>>", "surface": "mobile", "friction": "data_input"},
    {"step": "<<step text>>", "surface": "mobile"}
  ],
  "friction_points": [
    {"step_index": 1, "tag": "data_input", "note": "<<concrete detail>>"}
  ],
  "desired_outcome": "<<measurable outcome>>",
  "next_task": "<<what they do next>>"
}
```

---

## Friction Taxonomy (Fixed Enum)

| Tag | Meaning | Typical Fix |
|---|---|---|
| `cognitive_load` | Too many fields/sections/related lists in view | Dynamic Forms, conditional visibility |
| `click_count` | Task takes more clicks than necessary | Quick Action, Path step, inline edit |
| `mode_switch` | Forces mobile→desktop or app→browser mid-task | Mobile-aware page, mobile Quick Action |
| `data_input` | Repeated typing, missing defaults, free text where picklist fits | Default values, picklist conversion |
| `search` | Cannot find record, list view, or related item | List view tuning, search layout, pinned views |

Any other tag is invalid. Capture extra detail in `note`, never invent a sixth tag.

---

## Handoff JSON Envelope

```json
{
  "personas": [],
  "journeys": [],
  "friction_backlog": [
    {
      "persona_id": "<<...>>",
      "task": "<<...>>",
      "friction_tag": "<<enum value>>",
      "recommended_target": "lightning-record-page-auditor | list-view-and-search-layout-auditor | path-designer | flow-builder | audit-validation-rules",
      "recommended_intervention": "<<specific config change>>"
    }
  ]
}
```

---

## Authoring Checklist

- [ ] PSG resolves to a real or named-planned PSG.
- [ ] ≥1 record type, ≥1 list view, ≥1 dashboard from real metadata.
- [ ] `mobile_pct + desktop_pct` ≈ 100 (±2).
- [ ] `posture_source` names how the split was measured.
- [ ] Each persona has ≥1 journey; each journey has ≥3 steps.
- [ ] Every friction tag is in the fixed enum.
- [ ] `next_task` is present and non-empty on every journey.
- [ ] No journey step has `surface: "system"` or describes triggers/callouts.
- [ ] Total persona count for the phase is ≤ 7.
- [ ] Friction backlog routes every item to a downstream agent.
