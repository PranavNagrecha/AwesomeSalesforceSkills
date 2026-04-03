# Gotchas - Flow Testing

## Debug Runs Feel Safer Than They Are

**What happens:** A successful manual debug session creates false confidence.

**When it occurs:** Teams substitute diagnostics for repeatable regression coverage.

**How to avoid:** Use Debug to learn, then convert the important path into a durable test asset.

---

## Fault Paths Rarely Get Covered Accidentally

**What happens:** Production failures appear in scenarios nobody ever tested.

**When it occurs:** Test data is created only for the expected happy path.

**How to avoid:** Design negative and fault scenarios explicitly and build the data needed to trigger them.

---

## Flow Tests Do Not Replace Boundary Tests

**What happens:** A flow test passes, but the invocable Apex or custom screen component still behaves incorrectly.

**When it occurs:** Teams assume the orchestration test covers every dependency in full depth.

**How to avoid:** Pair Flow Tests with Apex or LWC tests where the flow crosses into custom logic.

---

## Test Data Quality Drives Test Value

**What happens:** Tests pass because they rely on accidental org state rather than deliberate setup.

**When it occurs:** The test design does not define what data each path truly needs.

**How to avoid:** Build data per scenario and keep assumptions explicit.
