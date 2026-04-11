# Einstein Discovery Development — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `einstein-discovery-development`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before writing any code or configuration.

- **CRM Analytics license confirmed?** Yes / No
- **Prediction definition ID (1OR prefix):** (e.g., `1ORB000000000bOOAQ`)
- **Prediction definition status:** (must be `Enabled`)
- **Scoring mode required:** Single-record synchronous / Bulk async job / Both
- **Prediction factors and improvements required?** Yes / No
  - If yes: confirm `settings` block is included in request body
- **Model version active:** (note model ID with 1Ot prefix)
- **Last model refresh date:** (to assess whether retraining is needed)
- **Daily predictions limit headroom:** (check org limits before scheduling bulk jobs)

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: Single-Record Real-Time Predict (Apex callout to `POST /smartdatadiscovery/predict`)
- [ ] Pattern 2: Scheduled Bulk Scoring Job (`POST /smartdatadiscovery/predictjobs` with polling)
- [ ] Model Refresh + Activation (trigger refresh job, poll, activate new model, then score)
- [ ] Prediction History Query (`GET /smartdatadiscovery/predicthistory`)
- [ ] Other: (describe)

**Why this pattern:** (explain why the chosen pattern fits the use case)

---

## Predict Request Body (fill in before implementation)

```json
{
  "predictionDefinition": "<1OR_PREDICTION_DEFINITION_ID>",
  "type": "<Records | RawData | RecordOverrides>",

  // For type: Records
  "records": ["<RECORD_ID_1>", "<RECORD_ID_2>"],

  // For type: RawData (column names from GET /smartdatadiscovery/models/{modelId})
  // "columnNames": ["<col1>", "<col2>"],
  // "rows": [["<val1>", "<val2>"]],

  // Include settings if prediction factors or prescriptions are needed (required v50.0+)
  "settings": {
    "maxPrescriptions": 3,
    "maxMiddleValues": 3,
    "prescriptionImpactPercentage": 75
  }
}
```

---

## Bulk Job Configuration (if applicable)

```json
{
  "predictionDefinition": "<1OR_PREDICTION_DEFINITION_ID>",
  "filter": {
    "fieldName": "<FIELD_API_NAME>",
    "operator": "<eq | neq | gt | lt>",
    "value": "<VALUE>"
  }
}
```

**Job polling strategy:**
- Poll interval: every ___ seconds / minutes
- Terminal statuses to handle: `Completed` (success), `Failed` (alert), `Paused` (log and exit — auto-resumes tomorrow, do NOT delete or restart)

---

## Model Refresh Sequence (if applicable)

- [ ] POST `/smartdatadiscovery/refreshjobs` with `predictionDefinitionId`
- [ ] Poll refresh job until status = `Completed`
- [ ] GET `/smartdatadiscovery/predictiondefinitions/{predDefId}/models` — identify new model ID
- [ ] Activate new model version (PUT or Model Manager UI)
- [ ] Confirm active model ID updated before starting bulk scoring job

---

## Response Validation Checklist

After each predict call or bulk job:

- [ ] HTTP response code is 200
- [ ] Each `predictions[N].status` is `"Success"` (check all entries, not just index 0)
- [ ] `importWarnings.missingColumns` is empty — if non-empty, fix field mapping before trusting scores
- [ ] `importWarnings.mismatchedColumns` is empty
- [ ] If bulk job: status is `Completed` before reading output fields on records

---

## Review Checklist

Copy and tick items from SKILL.md as you complete them:

- [ ] CRM Analytics license confirmed; not using EPB for a regression/multiclass use case
- [ ] Prediction definition ID confirmed and status is `Enabled`
- [ ] API version is v50.0+ and `settings` object included if factors or prescriptions are needed
- [ ] Bulk job polling logic handles `Paused` as informational, not an error
- [ ] Model refresh job triggers explicit model activation before next scoring run
- [ ] `importWarnings.missingColumns` checked and empty
- [ ] Daily predictions limit and model version documented

---

## Notes

Record any deviations from the standard pattern and why.

- 
