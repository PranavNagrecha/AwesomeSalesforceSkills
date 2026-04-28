# MoSCoW Prioritized Backlog — Template

Canonical handoff format for prioritized Salesforce backlog rows. Consumed by:

- `agents/release-train-planner/AGENT.md` — packs releases from the prioritized rows
- `agents/orchestrator/AGENT.md` — schedules which run-time agents to invoke when
- `agents/deployment-risk-scorer/AGENT.md` — scores risk per release based on the contained rows

---

## Table Skeleton

| story_id | moscow | moscow_subtag | effort | value | wsjf_score | release_target | rationale |
|---|---|---|---|---|---|---|---|
| STORY-001 | M |  | M | 5 |  | sprint-1 | Regulator order paragraph 4.2 |
| STORY-002 | S |  | M | 4 |  | sprint-1 | Pipeline dashboard for sales leadership |
| STORY-003 | C |  | S | 2 |  | sprint-2 | Lightning page polish |
| STORY-004 | W | won't-this-release | L | 3 |  | backlog | CPQ — deferred to Phase 2 |
| STORY-005 | W | won't-ever | M | 1 |  | archived | Custom UI to bypass Lightning — violates platform standard |

---

## JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "MoSCoW Prioritized Backlog Row",
  "type": "object",
  "required": ["story_id", "moscow", "effort", "value", "release_target", "rationale"],
  "properties": {
    "story_id": {
      "type": "string",
      "description": "Stable identifier for the user story or work item."
    },
    "moscow": {
      "type": "string",
      "enum": ["M", "S", "C", "W"],
      "description": "MoSCoW category: Must, Should, Could, Won't."
    },
    "moscow_subtag": {
      "type": ["string", "null"],
      "enum": ["won't-this-release", "won't-ever", null],
      "description": "Required for W rows. Null for M/S/C."
    },
    "effort": {
      "type": "string",
      "enum": ["S", "M", "L", "XL"],
      "description": "Effort tier. S = ≤0.5d, M = 1-3d, L = 3-10d, XL = >10d."
    },
    "value": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5,
      "description": "Business value tier as judged by the sponsor."
    },
    "wsjf_score": {
      "type": ["number", "null"],
      "description": "WSJF score, populated only when WSJF tie-break was applied."
    },
    "release_target": {
      "type": "string",
      "description": "Release identifier, or 'backlog' (Won't-this-release), or 'archived' (Won't-ever)."
    },
    "rationale": {
      "type": "string",
      "description": "One-sentence justification. Required for every W row, recommended for every M row."
    }
  }
}
```

---

## Capacity Math (run alongside the table)

```
team_capacity_days   = <integer>          # available person-days in the horizon
must_effort_days     = sum(effort_days for row in rows if row.moscow == 'M')
should_effort_days   = sum(effort_days for row in rows if row.moscow == 'S')

assert must_effort_days <= team_capacity_days
assert (must_effort_days + should_effort_days) <= 0.8 * team_capacity_days
```

Default effort-tier mapping (override per team):

| Tier | Days |
|---|---|
| S | 0.5 |
| M | 2 |
| L | 6 |
| XL | 12 |

---

## Conventions

- Do not commit a Must row without an effort tier and a value tier.
- Do not leave `moscow_subtag` blank on a W row.
- Do not invent `release_target` values — use only identifiers the team has named, plus `backlog` and `archived`.
- WSJF score is optional and only meaningful at the capacity boundary; do not score the entire backlog with WSJF.
