# Calculation Procedures — Work Template

Use this template when designing, reviewing, or troubleshooting a Calculation Procedure or Calculation Matrix task.

---

## Scope

**Skill:** `omnistudio/calculation-procedures`

**Request summary:** (fill in what the user asked for — e.g., "build pricing calculation procedure for product catalog", "debug why matrix lookup returns null", "add a new rate tier to the insurance matrix")

**Mode:**
- [ ] Mode 1 — Build from scratch
- [ ] Mode 2 — Review existing procedure or matrix
- [ ] Mode 3 — Troubleshoot a failure

---

## Context Gathered

Answer these before proceeding. Record answers here.

**Inputs (variables entering the procedure):**

| Variable Name | Data Type | Required? | Source |
|---------------|-----------|-----------|--------|
| | | | |
| | | | |

**Outputs (variables the caller expects back):**

| Variable Name | Data Type | Destination |
|---------------|-----------|-------------|
| | | |
| | | |

**Caller:**
- OmniScript action name:
- Integration Procedure element name:
- Apex method / Connect API endpoint:

**Referenced Calculation Matrices:**

| Matrix Name | Active Version? | Date Range Covered | Columns Used |
|-------------|-----------------|-------------------|--------------|
| | | | |

**Known constraints:**
- Salesforce API version:
- Org edition / OmniStudio license type:
- Any rate or rule change cadence (quarterly, annually, ad-hoc):

---

## Mode 1: Build from Scratch

### Step Sequence Plan

Document the planned step sequence before opening the designer.

| Step # | Step Name | Step Type | Purpose |
|--------|-----------|-----------|---------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

### Calculation Matrix Definition (if applicable)

**Matrix Name:**

**Input Columns:**

| Column API Name | Data Type | Example Value |
|-----------------|-----------|---------------|
| | | |

**Output Columns:**

| Column API Name | Data Type | Example Value |
|-----------------|-----------|---------------|
| | | |

**Versioning plan:**
- Version 1 StartDateTime:
- Version 1 EndDateTime (or leave blank for open-ended):
- Version 1 Rank:

### Activation Order

List activation order (leaf sub-procedures first, parent last):

1.
2.
3.

---

## Mode 2: Review Existing

### Activation Status Check

- [ ] Procedure version `IsActive = true`
- [ ] All referenced matrix versions active and covering expected date range
- [ ] Sub-procedure targets active before parent

### Variable Contract Check

- [ ] Input variable names match exactly what the caller passes (case-sensitive)
- [ ] Output variable names match exactly what the caller reads
- [ ] Variable data types match matrix column data types for every Lookup step

### Version Management Check

- [ ] No two matrix versions have the same `Rank` and overlapping date ranges
- [ ] Old/expired versions have `EndDateTime` set appropriately
- [ ] Procedure version history is meaningful (logic changes, not just data changes)

### Test Coverage Check

- [ ] Happy path test defined and passing
- [ ] Boundary value inputs tested (e.g., exact bracket edges for range columns)
- [ ] Missing/null input tested to verify graceful handling
- [ ] Future-dated execution tested if matrix versioning is date-effective

---

## Mode 3: Troubleshoot

### Symptom

Describe what is failing:

### Reproduction Steps

1.
2.
3.

### Checklist

- [ ] Is the procedure version active?
- [ ] Is the matrix version active and does its date range cover the execution time?
- [ ] Are variable names spelled correctly and matching the matrix column API names?
- [ ] Are data types consistent between procedure variables and matrix columns?
- [ ] Does the matrix have duplicate input combinations that cause non-deterministic lookup results?
- [ ] Are all sub-procedure targets active?
- [ ] Is looping enabled (`IsLoopingEnabled = true`) and is the loop termination condition correct?

### Root Cause (fill after investigation)

### Fix Applied

---

## Review Checklist (all modes)

Copy from SKILL.md and tick items as you complete them:

- [ ] Calculation Procedure version is activated
- [ ] Every referenced Calculation Matrix has an active version covering the expected date range
- [ ] Input variable names match matrix column names exactly (case-sensitive)
- [ ] Output variables mapped from matrix columns have compatible data types
- [ ] SubExpression step targets are activated before the parent procedure
- [ ] Built-in test execution passes with representative and boundary inputs
- [ ] Procedure is callable from the intended consumer
- [ ] Matrix versioning strategy documented

---

## Notes

Record any deviations from the standard pattern and the reason for each deviation.
