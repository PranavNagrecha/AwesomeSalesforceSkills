# Embedded Analytics Architecture — Work Template

Use this template to document embedded CRM Analytics architecture decisions.

## Scope

**Skill:** `embedded-analytics-architecture`

**Page Context:** Lightning Record Page / Lightning App Page / Experience Cloud / Visualforce
**Object Type (if record page):** (fill in)
**Dashboards to Embed:** (list)
**Component Type:** LWC wave-wave-dashboard / Aura wave:waveDashboard (Visualforce only)

---

## Dashboard Configuration

| Dashboard Name | Dev Name Source | Record Context? | Filter/State Requirements |
|---|---|---|---|
| | Custom Metadata / Apex / Hard-coded (avoid) | Yes (record-id) / No | (describe state JSON needed) |

---

## Filter/State JSON Schema

For each embedded dashboard:

**Dashboard: [Name]**
```json
{
  "filters": [
    {
      "field": "ObjectName.FieldName",
      "operator": "in",
      "value": ["${recordId}"]
    }
  ]
}
```

---

## dashboardDevName Resolution

**Resolution mechanism:** Custom Metadata / Custom Setting / Apex method / Hard-coded (avoid)

```apex
// Custom Metadata retrieval example
public static String getDashboardDevName(String context) { ... }
```

---

## Cross-Dashboard Context Propagation (if applicable)

| Source Dashboard | Event/Selection | Target Dashboard | State Update Pattern |
|---|---|---|---|
| | selectionChanged event | | setState() call in parent LWC |

---

## Permission Model

| Context | Audience | Permission Required |
|---|---|---|
| Lightning Experience | Internal users | CRM Analytics license |
| Experience Cloud | Authenticated community | Analytics permission on profile |
| Experience Cloud | Guest users | Analytics for Guest Users permission (if enabled) |

---

## Performance Strategy

| Dashboard | Load Strategy | Rationale |
|---|---|---|
| [Above fold] | Eager | Visible immediately |
| [Below fold / in tab] | Lazy (on tab/scroll) | Avoid blocking page load |

---

## Review Checklist

- [ ] Component type chosen (LWC for Lightning/ExpCloud, Aura for Visualforce only)
- [ ] dashboardDevName NOT hard-coded — resolution mechanism designed
- [ ] state JSON schema documented for each dashboard
- [ ] record-id binding confirmed AND dashboard binding configured
- [ ] Cross-dashboard context propagation designed if needed
- [ ] Experience Cloud permission model confirmed
- [ ] Performance strategy (eager vs lazy load) specified
