# Agent Testing and Evaluation — Work Template

Use this fill-in-the-blank template to plan and document an agent test suite, or to record a testing engagement for review.

---

## Scope

**Agent name (API Name):** ___________________________

**Org / environment:** [ ] Sandbox  [ ] Developer Edition  [ ] Production (post-deploy monitoring only)

**Testing purpose:**
[ ] Pre-launch validation before first activation
[ ] Regression check after topic/action change
[ ] CI/CD pipeline test suite authoring
[ ] Post-deploy monitoring setup
[ ] Other: ___________________________

---

## Topic Inventory

List each topic and its classification description. This is required before writing test cases.

| Topic API Name | Classification Description Summary | Adjacent Topics (potential boundary conflicts) |
|---|---|---|
| | | |
| | | |
| | | |

---

## Coverage Matrix

For each topic, document the utterances you will test. Minimum: 2 happy path, 2 edge case, 1 boundary, 1 out-of-scope.

### Topic: ___________________________

| Utterance | Type | Expected Topic | Notes |
|---|---|---|---|
| | Happy path | | |
| | Happy path | | |
| | Edge case | | |
| | Edge case (typo/paraphrase) | | |
| | Boundary (near: ___________) | | |
| | Out-of-scope | Escalation / decline | |

*(Copy this section for each topic.)*

---

## AiEvaluationDefinition Plan

**File name:** `___________________________`.aiEvaluationDefinition-meta.xml

**Subject agent:** ___________________________

**Test expectations per case:**

| Test Case # | Utterance | Expect Topic | Expect Action(s) | Instruction Adherence? |
|---|---|---|---|---|
| 1 | | | | [ ] Yes  [ ] No |
| 2 | | | | [ ] Yes  [ ] No |
| 3 | | | | [ ] Yes  [ ] No |

**Multi-turn conversation tests needed?** [ ] Yes  [ ] No

If yes, list flows that require conversation history:

| Flow Name | Turns in History | Final Test Utterance | Expected Outcome |
|---|---|---|---|
| | | | |

---

## Context Variables

List any context variables (session state, record IDs, user attributes) needed to make test cases realistic:

| Variable Name | Value / Type | Used In Test Cases |
|---|---|---|
| | | |

---

## Execution Plan

**Deployment command:**
```bash
sf project deploy start --source-dir force-app/main/default/aiEvaluationDefinitions
```

**Execute command:**
```bash
# POST to Connect API - replace ORG_DOMAIN, SESSION_ID, and DEFINITION_NAME
curl -X POST \
  https://ORG_DOMAIN.my.salesforce.com/services/data/v62.0/connect/einstein/ai-evaluations \
  -H "Authorization: Bearer SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"aiEvaluationName": "DEFINITION_NAME"}'
```

**Job ID captured:** ___________________________

**Baseline results saved to:** ___________________________

---

## Results Summary

**Run date:** ___________________________

**Total test cases:** _____

| Test Type | Total | Pass | Fail | Fail Rate |
|---|---|---|---|---|
| Topic tests | | | | |
| Action tests | | | | |
| Instruction adherence | | | | |

**Newly failing cases (vs baseline):**

| Test Case # | Utterance | Expected | Actual | Investigation |
|---|---|---|---|---|
| | | | | |

**Root cause of failures:**
- [ ] Topic classification description needs refinement — topic: ___________________________
- [ ] Competing topic classification description is too broad — topic: ___________________________
- [ ] Action configuration issue — action: ___________________________
- [ ] Topic instruction not followed — topic: ___________________________
- [ ] Utterance is a genuine boundary case — move to Tier 2 distribution testing

---

## Post-Deploy Monitoring Plan

**Enhanced Event Logs enabled on production agent?** [ ] Yes  [ ] No

**Metrics to track:**

| Metric | Baseline / Target | Review Frequency |
|---|---|---|
| Containment rate | | |
| Escalation rate | | |
| CSAT / satisfaction score | | |
| Topic activation accuracy | | |
| Instruction adherence score | | |

**Alert threshold:** Escalation rate increases by more than ___% over a ___-day rolling window → investigate and add test cases.

---

## Sign-Off Checklist

- [ ] Coverage matrix complete: happy path, edge case, boundary, out-of-scope for every topic
- [ ] AiEvaluationDefinition metadata authored and version-controlled
- [ ] All topic tests passing (100%)
- [ ] Action sequence tests passing for all primary flows
- [ ] Multi-turn conversation tests passing for context-dependent flows
- [ ] Baseline test results saved as a versioned artifact
- [ ] No regressions vs. baseline (newly broken cases resolved)
- [ ] Testing API execution integrated into the CI/CD promotion pipeline
- [ ] Live sandbox conversation test completed with real data
- [ ] Enhanced Event Logs enabled on production agent
- [ ] Post-deploy monitoring dashboard configured

---

## Notes

*(Record deviations from standard patterns, known limitations of the test suite, or decisions made.)*
