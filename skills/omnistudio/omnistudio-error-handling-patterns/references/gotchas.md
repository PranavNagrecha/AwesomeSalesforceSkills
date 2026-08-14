# OmniStudio Error Handling — Gotchas

## 1. Step-Level Defaults Swallow Failures

The default `Fail On Step Error` is often unchecked. Critical writes pass through without the IP recognizing failure.

Avoid it: set these flags deliberately on every step that could fail.

## 2. DataRaptor Extract Returns Empty On Row-Level Failures

An Extract with a mapping error returns a 200 with empty rows. The caller cannot tell the difference between "no data" and "data that failed to map."

Avoid it: add a validation step after the Extract that asserts expected row shape.

## 3. OmniScript Fault Navigation Loses Data

Navigating to a fault step on error can reset user entries unless you carry them forward in OmniScript data JSON.

## 4. FlexCard `On Failure` Branches Get Skipped

Auto-generated FlexCard actions often leave the `On Failure` branch empty, so the UI shows a silent success.

Avoid it: every save action needs an explicit failure toast or error state.

## 5. Retry Without Idempotency Produces Duplicates

Retry buttons without correlation IDs or external-ID keys create duplicate records downstream every time the user taps retry.

---

## 6. IP Try-Catch With `failOnBlockError=false` Converts Faults Into HTTP 200

**What happens:** The IP wraps work in a Try Catch Block. The Catch logs and sets `error: true`. `failOnBlockError` is false, and many steps have `failOnStepError: false`. Callers (FlexCard, OmniScript, nested parent) see success. Apex remotes that catch and `return null` do the same.

**When it occurs:** Review checklists that require a Try-Catch but not a fail flag. Guest IPs that must "never throw."

**How to avoid:** Log, then fail. `failOnBlockError: true` (or Set Errors) after the log. `rollbackOnError: true` on the procedure. Map a real `failureResponse`. FlexCard Error state must key off that node — a blank card is a swallowed fault. See `templates/flow/FaultPath_Template` for the same idea on Flow; IPs need the equivalent.

---

## 7. Mapping `error: true` Is Not Set Errors

**What happens:** Zero Set Errors elements. HTTP Rest Actions still return 200 with an `error` node in JSON. OmniScript continues. FlexCards with no Error state render blank.

**When it occurs:** Teams treat the Catch block as the user-visible fault.

**How to avoid:** Set Errors (or throw) for contract failures. Reserve Try-Catch for compensated paths that still signal failure to the caller.

---

## 8. `ErrorLoggingEnabled` Writes OmniComponentErrorLog — Separate From App Logs

**What happens:** Omni Interaction Config `ErrorLoggingEnabled=true` lands Try-Catch responses in **OmniComponentErrorLog**. Ops watching a custom log object never see them.

**When it occurs:** Regulated orgs with a custom logging framework that "covers Omni."

**How to avoid:** Monitor both. Do not serialize the full OmniScript input map into either log — that is a second PII store (tokens, household JSON) outside session TTL. Mask at write.
