# Gotchas — Apex Flow Invocation From Apex

Non-obvious Salesforce platform behaviors that cause real production problems.

## Gotcha 1: Screen Flows Cannot Run Headless

**What happens:** `Flow.Interview.createInterview('Case_Triage_Wizard', params).start()` throws at runtime with a message about the Flow type not supporting this invocation.

**When it occurs:** An admin converts an Autolaunched Flow to Screen (or vice versa) and the Apex caller is not updated.

**How to avoid:** Document the required Flow type in the Apex wrapper. Consider a CI check that fetches Flow metadata and asserts Type matches.

---

## Gotcha 2: Governor Limits Do Not Reset At The Flow Boundary

**What happens:** A trigger that calls a Flow that does 50 SOQLs and 50 DMLs now has the caller sitting at 50 SOQL + 50 DML — close to the ceiling. The trigger's own subsequent DML fails.

**When it occurs:** Whenever the Flow does meaningful work.

**How to avoid:** Treat the Flow invocation as part of the caller's budget. Monitor `Limits.getQueries()` before and after if you're near the ceiling.

---

## Gotcha 3: Typos In Output Variable Names Return `null`

**What happens:** `i.getVariableValue('finalprice')` returns `null` because the variable is actually `finalPrice`. Downstream code sees null and defaults wrongly.

**When it occurs:** Case-sensitivity mismatches, camelCase confusion.

**How to avoid:** Copy the exact API name from Flow Builder. Consider an integration test that reads every output and asserts non-null for at least one known-good input.

---

## Gotcha 4: Parameter Map Type Mismatches Are Runtime Errors

**What happens:** A Flow variable is `Number` (Decimal). Apex passes `1` (Integer). The runtime throws "Type mismatch" because Flow is strict about Decimal vs Integer in some versions.

**When it occurs:** Primitive boxing assumptions from Java/Apex bleed into Flow param maps.

**How to avoid:** Cast explicitly: `(Decimal) 1` → `Decimal.valueOf(1)`. For currencies and numerics always wrap in the expected type.

---

## Gotcha 5: `getVariableValue` Only Returns Output Variables

**What happens:** A developer sets `flowVar` as an input-only variable and expects to read it back after `start()`. They get `null`.

**When it occurs:** Developers think of Flow variables as "variables" rather than "input" vs "output" toggles.

**How to avoid:** In Flow Builder set the variable to "Available for Output" if Apex needs to read it post-run.

---

## Gotcha 6: Flow Interview Is Not Transactional With Itself

**What happens:** A Flow creates a record and then a later element fails. The created record is not rolled back automatically if the Apex caller catches the exception.

**When it occurs:** Any partial-failure Flow path.

**How to avoid:** Wrap the Apex invocation in `Savepoint` / `Database.rollback(savepoint)` if atomicity matters. Alternatively, design the Flow to be idempotent.

---

## Gotcha 7: Flow Interview Respects Running User Context

**What happens:** An `without sharing` Apex caller invokes a Flow; the Flow still runs with the calling user's record access. Records the Flow tries to read/update still must be visible/writable to the user.

**When it occurs:** Misunderstanding that Flow has an independent security context.

**How to avoid:** Flow runs "As Default (user/system context)" based on the Flow's advanced setting. To bypass sharing in the Flow, set Flow "How to Run the Flow" to "System Context With Sharing" or "System Context Without Sharing" explicitly.

---

## Gotcha 8: Repeat Invocation Of The Same Interview Has No Effect

**What happens:** A developer calls `i.start()` twice expecting a second run. The second call either no-ops or throws.

**When it occurs:** Developers treating `Interview` like a reusable template.

**How to avoid:** Create a new `Flow.Interview` instance for each run.
