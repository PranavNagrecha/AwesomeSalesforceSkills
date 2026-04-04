# FlexCard Design — Work Template

Use this template when designing or reviewing a FlexCard. Fill in each section before writing any card configuration.

---

## Scope

**FlexCard Name (API):** (e.g. `AccountSummaryCard`)
**FlexCard Label:** (e.g. "Account Summary Card")
**Anchored Object:** (e.g. Account, Case, Contact)
**Placement:** (Lightning App Page / Experience Cloud Page / Record Page)
**Request summary:** (one sentence — what the card must do)

---

## Context Gathered

Answer these before designing:

- **OmniStudio mode:** Standard (Salesforce Industries) / Managed Package (ISV)
- **Data required:** list fields and related objects
- **Actions required:** Navigation / OmniScript Launch / DataRaptor / Apex / Custom LWC
- **Related lists required:** Yes / No — if yes, list the child object and expected record count
- **Real-time updates required:** Yes / No — if yes, specify the Platform Event or CDC channel
- **Deployment mechanism:** SFDX / Change Set / OmniStudio Migration Tool

---

## Data Source Design

| Data Source | Type | Justification |
|-------------|------|---------------|
| (name) | SOQL / Apex / DataRaptor / Integration Procedure / Streaming | (why this type for this data) |

If more than one data source is listed: document why consolidation into a single Integration Procedure is not possible.

**IP name (if used):** _______________
**IP inputs passed from card:** _______________
**IP output nodes used by card:** _______________

---

## Card States

| State | Template Purpose | Data Nodes Bound |
|-------|-----------------|-----------------|
| Default | Primary display | (list data paths) |
| Saved | Success confirmation | (static text or data path) |
| Error | Failure message | `{DataSource.errorMessage}` or equivalent |

> Error state must be configured. Do not leave it empty.

---

## Actions

| Label | Type | Target | Data Passed | On Success |
|-------|------|--------|-------------|------------|
| (e.g. "Escalate") | OmniScript Launch | EscalateCaseOS | `{Record.Id}` | Refresh card |
| (e.g. "View Detail") | Navigation | Record page | — | Navigate |

---

## Conditional Visibility Rules

| Element | Condition Expression | When Shown |
|---------|---------------------|------------|
| (button / section / field) | `{Record.Status} == 'Open'` | When case is open |
| ... | ... | ... |

Test each condition with:
- [ ] A record where the condition is `true`
- [ ] A record where the condition is `false`
- [ ] A record where the referenced field is `null`

---

## Child Cards and Flyouts

| Child Card Name | Parent Collection Node | Max Expected Records | Has Own Data Source? |
|----------------|----------------------|----------------------|---------------------|
| (e.g. CaseSummaryCard) | `{IntegrationProcedure.recentCases}` | 10 | No — data from parent IP |

> Child cards must not have independent data sources when used in iterated lists.

---

## Deployment Checklist

- [ ] Integration Procedure(s) deployed and activated in target environment
- [ ] DataRaptor(s) deployed and activated (if used)
- [ ] Child FlexCard(s) deployed and activated before parent
- [ ] Parent FlexCard deployed
- [ ] Parent FlexCard activated in target environment (compile step)
- [ ] Card tested on a live record in target environment — not just designer preview
- [ ] Error state tested by forcing a data source failure
- [ ] Lightning App Page or Experience Cloud page saved and activated after card addition

---

## Notes

Record any deviations from standard patterns and the reason:

- (e.g. "Used Apex data source instead of SOQL because query requires aggregation across a non-standard relationship not supported by SOQL action")
