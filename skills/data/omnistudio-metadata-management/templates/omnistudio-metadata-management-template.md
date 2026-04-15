# OmniStudio Metadata Management — Work Template

Use this template when performing dependency tracking, impact analysis, stale-component cleanup, or Metadata API Support auditing for OmniStudio components.

## Scope

**Skill:** `omnistudio-metadata-management`

**Request summary:** (fill in what the practitioner asked for)

**Analysis type:**
- [ ] Full org dependency graph
- [ ] Impact analysis for a specific component
- [ ] Stale component identification
- [ ] Metadata API Support pipeline audit

---

## Pre-Flight Context

Answer these before beginning any analysis:

| Question | Answer |
|---|---|
| Is OmniStudio Metadata API Support enabled in the target org? | |
| Are ALL orgs in the pipeline using the same mode (Metadata API or DataPack)? | |
| Which OmniStudio runtime is the org running? (Standard Runtime / Package Runtime) | |
| Is this org accessible for `sf project retrieve`? | |
| Component names or types in scope: | |

**If any org in the pipeline does NOT have OmniStudio Metadata API Support enabled:** stop and resolve the mixed-mode conflict before proceeding.

---

## Retrieve Command

```bash
sf project retrieve start \
  --metadata OmniProcess OmniDataTransform OmniUiCard OmniInteractionConfig \
  --target-org <alias> \
  --output-dir ./retrieved-omnistudio
```

Retrieved file locations:
- OmniUiCard: `force-app/main/default/omniUiCards/`
- OmniProcess: `force-app/main/default/omniProcesses/`
- OmniDataTransform: `force-app/main/default/omniDataTransforms/`
- OmniInteractionConfig: `force-app/main/default/omniInteractionConfigs/`

---

## Component Inventory

| Component API Name | Type | Sub-Type | Active? | Notes |
|---|---|---|---|---|
| | OmniProcess / OmniDataTransform / OmniUiCard / OmniInteractionConfig | OmniScript / Integration Procedure / DataRaptor / FlexCard | Yes / No | |

---

## Dependency Graph

> Note: This graph is built from parsed JSON bodies, NOT from Tooling API MetadataComponentDependency (which does not resolve OmniStudio cross-component references).

| Caller Component | Caller Type | Called Component | Called Type | Reference Field |
|---|---|---|---|---|
| | FlexCard / OmniScript / Integration Procedure | | DataRaptor / Integration Procedure / FlexCard | propertySet.dataRaptorBundleName / actionList[].actionAttributes.remoteClass / childElements[].propertySet.remoteClass |

---

## Impact Analysis (for specific target component)

**Target component:** (fill in)

**Components that call the target:**

| Caller API Name | Caller Type | Reference Location in JSON |
|---|---|---|
| | | |

**Safe to delete/rename?**
- [ ] No inbound references found — confirm against usage logs before deletion
- [ ] Inbound references exist — update all callers first (list above)

---

## Stale Component Candidates

Components with zero inbound references from other OmniStudio components:

| Component API Name | Type | Last Active Date (if available) | Recommendation |
|---|---|---|---|
| | | | Archive / Delete / Keep |

> Cross-reference against event monitoring or usage logs before recommending deletion — a FlexCard with no OmniStudio callers may still be launched directly from an App Page or Experience Cloud page.

---

## Metadata API Support Pipeline Audit

| Org | Alias | OmniStudio Metadata API Support Enabled? | Notes |
|---|---|---|---|
| | dev-sandbox | Yes / No | |
| | ci-sandbox | Yes / No | |
| | uat-sandbox | Yes / No | |
| | staging | Yes / No | |
| | production | Yes / No | |

**Remediation required if any row is "No":** enable the setting, wait for background component migration to complete, then re-run the pipeline.

---

## Checklist

- [ ] OmniStudio Metadata API Support confirmed enabled in all pipeline orgs
- [ ] All four metadata types retrieved successfully
- [ ] JSON body decoded and parsed for each component (not just XML outer structure)
- [ ] Reference extraction used type-specific JSON field paths (not Tooling API)
- [ ] Caller-callee graph built and spot-checked against a known relationship
- [ ] Impact list reviewed before any deletion or rename
- [ ] FlexCard-to-FlexCard child card references extracted and included in graph
- [ ] Stale candidates cross-checked against usage logs before deletion recommendation
- [ ] No roadmap features assumed as currently available

---

## Notes

(Record any deviations from the standard pattern, unresolved references found during parsing, or environment-specific constraints.)
