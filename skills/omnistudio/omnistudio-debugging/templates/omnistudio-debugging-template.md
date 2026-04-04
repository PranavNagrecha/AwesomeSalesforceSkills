# OmniStudio Debugging — Work Template

Use this template when diagnosing a broken OmniScript, DataRaptor, or Integration Procedure.

---

## 1. Failure Summary

**Asset type:** [ ] OmniScript  [ ] DataRaptor (Extract / Load / Transform / Turbo Extract)  [ ] Integration Procedure

**Asset name and version:**

**Environment where failure occurs:** [ ] Sandbox  [ ] Production  [ ] Both

**User context:** [ ] Internal admin  [ ] Internal restricted user  [ ] Experience Site / portal user  [ ] Guest

**Symptom observed:**
> _Describe what the user or system sees. Include any error text, empty result, missing data, or unexpected behavior._

---

## 2. Context Gathered

**Active version confirmed?** [ ] Yes — version: ______  [ ] Not yet confirmed

**Recent changes deployed?** [ ] Yes (describe below)  [ ] No  [ ] Unknown

**Named Credentials in play (list names):**

**Remote Site Settings required (list domains):**

**Custom Settings or Custom Metadata the asset depends on:**

---

## 3. Debug Mode Used

**OmniScript (Action Debugger):**
- [ ] Opened Preview tab in designer
- [ ] Opened Action Debugger panel
- [ ] Identified failing element: ______________________
- [ ] Inspected Input data node values
- [ ] Inspected Output / Error in the failing element node

**Integration Procedure (IP Debug tab):**
- [ ] Opened Debug tab in IP designer
- [ ] Pasted input JSON (attach or paste below)
- [ ] Ran debug execution
- [ ] Identified failing step: ______________________
- [ ] Noted status code and error message from step

**DataRaptor (Preview tab):**
- [ ] Opened Preview tab in DataRaptor designer
- [ ] Supplied sample input JSON (attach or paste below)
- [ ] Ran preview
- [ ] Inspected generated SOQL (Extract) or mapping output (Transform / Load)
- [ ] Verified result against expected output

---

## 4. Input JSON Used During Debug

```json
{
  "replace": "with the actual input used during debug run"
}
```

---

## 5. Findings

**Root cause:**
> _State the specific element, configuration item, data path, or environment dependency that caused the failure._

**Environment delta items missing from target org (if applicable):**

| Item | Status in Sandbox | Status in Production |
|------|------------------|----------------------|
| Named Credential: __________ | Present / Configured | Missing / Misconfigured |
| Remote Site Setting: __________ | Active | Missing / Inactive |
| Active version | v_______ | v_______ |
| Custom Setting: __________ | Populated | Missing / Stale |

---

## 6. Remediation Steps

- [ ] Fix identified in: [ ] Asset configuration  [ ] Named Credential  [ ] Remote Site Setting  [ ] Active version activation  [ ] Data path / null guard  [ ] Error handling
- [ ] Specific change made:
- [ ] Re-tested after fix using same debug method
- [ ] `rollbackOnError: true` confirmed on IP root
- [ ] `failureResponse` on critical elements is meaningful (not placeholder copy)
- [ ] Navigation Actions tested in deployed context (not just Preview)

---

## 7. Review Checklist

- [ ] Active version in target environment is the intended version
- [ ] Action Debugger used to trace element-level input/output in OmniScript
- [ ] IP Debug tab used with production-representative input JSON
- [ ] All HTTP actions use Named Credentials confirmed present in target org
- [ ] DataRaptor Preview run with input matching the runtime user's data shape
- [ ] `rollbackOnError: true` set at IP root
- [ ] Failure response text is meaningful and user-safe
- [ ] Remote Site Settings verified for all outbound HTTP domains

---

## 8. Notes

_Record any deviations from the standard debug approach, environment-specific quirks, or follow-up items._
