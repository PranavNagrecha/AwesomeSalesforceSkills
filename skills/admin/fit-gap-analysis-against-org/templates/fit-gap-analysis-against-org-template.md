# Fit-Gap Matrix — Template

Use this template for every fit-gap engagement. Both the markdown table (human-facing) and the JSON list (downstream-agent-facing) must be filled.

---

## Engagement Header

- **Customer / org name:**
- **Target org (URL or alias):**
- **Edition:** (Professional / Enterprise / Unlimited / Performance / Industries)
- **Reviewer:**
- **Probe date:**
- **AppExchange policy:** (open / managed-packages-only-with-approval / in-house-only)

## Org Probe Summary

- Edition: …
- Enabled features: …
- Installed managed packages: …
- License SKU counts (per persona): …
- Existing automation (per in-scope sObject): …

---

## Fit-Gap Matrix

| ID | Requirement | Tier | Effort | Risk Tags | Recommended Agent | Recommended Skills | AppExchange Alternatives | Notes |
|---|---|---|---|---|---|---|---|---|
| REQ-001 | | | | | | | | |
| REQ-002 | | | | | | | | |
| REQ-003 | | | | | | | | |

**Tier enum:** Standard / Configuration / Low-Code / Custom / Unfit
**Effort enum:** S / M / L / XL
**Risk tag enum:** license-blocker / data-skew / governance / customization-debt / no-AppExchange-equivalent
**Recommended Agent enum:** object-designer / flow-builder / apex-builder / architecture-escalation

---

## Per-sObject Workload Summary

| sObject | Standard | Configuration | Low-Code | Custom | Unfit | Total |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## Architecture-Escalation List (Unfit Rows Only)

| ID | Requirement | Decision Tree Branch | Escalation Note |
|---|---|---|---|
| | | | |

---

## Canonical JSON Row Schema

```json
{
  "requirement_id": "REQ-042",
  "title": "Auto-route inbound leads by region within 5 minutes",
  "description": "Inbound leads from web-to-lead must be routed to the regional rep within 5 minutes. SLA breach triggers escalation.",
  "source_persona": "Inside Sales Lead",
  "tier": "Low-Code",
  "effort": "M",
  "risk_tag": ["governance"],
  "recommended_agents": ["flow-builder"],
  "recommended_skills": [
    "admin/lead-routing-rules-design",
    "flow/record-triggered-flow-patterns"
  ],
  "appexchange_alternatives": [],
  "decision_tree_branch": null,
  "notes": "Re-uses existing assignment rule pattern; flag governance tag for naming-convention review."
}
```

### Field Rules

| Field | Required | Constraint |
|---|---|---|
| `requirement_id` | yes | Stable identifier (e.g. `REQ-001`); unique per matrix. |
| `title` | yes | One-line summary. |
| `description` | yes | Full requirement text. |
| `source_persona` | yes | The user role / profile that requested the requirement. |
| `tier` | yes | One of `Standard` / `Configuration` / `Low-Code` / `Custom` / `Unfit`. |
| `effort` | yes | One of `S` / `M` / `L` / `XL`. |
| `risk_tag` | yes | Array; may be empty. Each entry from the canonical taxonomy. |
| `recommended_agents` | yes | Array; required non-empty when `tier ∈ {Standard, Configuration, Low-Code, Custom}`. For `Unfit`, must equal `["architecture-escalation"]`. |
| `recommended_skills` | yes | Array; each entry is a skill ID resolvable in `agents/_shared/SKILL_MAP.md`. |
| `appexchange_alternatives` | yes | Array; may be empty. |
| `decision_tree_branch` | conditional | Required for `Unfit` rows; must reference a file under `standards/decision-trees/`. |
| `notes` | yes | Plain-language reviewer commentary. |

---

## Output JSON List Wrapper

```json
{
  "engagement": "<customer name>",
  "target_org": "<org alias>",
  "probe_date": "YYYY-MM-DD",
  "rows": [
    { "requirement_id": "REQ-001", "...": "..." },
    { "requirement_id": "REQ-002", "...": "..." }
  ],
  "summary": {
    "by_tier": { "Standard": 0, "Configuration": 0, "Low-Code": 0, "Custom": 0, "Unfit": 0 },
    "by_effort": { "S": 0, "M": 0, "L": 0, "XL": 0 },
    "risk_tag_count": 0,
    "appexchange_recommended": 0
  }
}
```
