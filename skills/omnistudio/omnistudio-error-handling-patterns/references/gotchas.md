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
