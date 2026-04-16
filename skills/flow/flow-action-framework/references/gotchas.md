# Gotchas — Flow Action Framework

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Apex action not listed despite compiling in the IDE

**What happens:** The Flow author searches the Apex action palette and the class never appears.

**When it occurs:** Common when the running user lacks Apex class access, the method is not `static`, the annotation is missing, the org has an older API version incompatible with the feature set, or the class lives in another namespace and is not `global`.

**How to avoid:** Grant **Apex Class Access** on profiles or permission sets, confirm `@InvocableMethod` on a `public static` or `global static` method, and recompile in the target org. For packaged code, verify the publisher exposed the invocable.

---

## Gotcha 2: Scalar mapping to a list-only invocable input

**What happens:** Flow validates in the builder but fails at runtime, or only the first conceptual row is processed as expected while bulk paths drop data.

**When it occurs:** Record-triggered after-save paths pass `$Record` while the Flow variable feeding Apex is typed as a single record but the interview is bulk; or a collection is never built before the Apex action.

**How to avoid:** Align variable types with the invocable signature: use SObject collection variables when the Apex input is `List<Wrapper>` representing many rows. Test with multi-record transactions.

---

## Gotcha 3: Unwired Apex action fault path

**What happens:** Any uncaught Apex exception or platform fault terminates the interview with a generic error; screen flows show a poor end-user message.

**When it occurs:** Teams accustomed to fault-tolerant standard actions omit the Apex action’s fault connector.

**How to avoid:** Always connect the fault path, capture `$Flow.FaultMessage`, and route to recovery UI or logging consistent with the automation’s reliability requirements.

---

## Gotcha 4: Subflow input/output renames break parents silently until activation

**What happens:** Child flow variable API names change; parent **Run Subflow** mappings become invalid or default to empty values.

**When it occurs:** Agile renaming of child flow variables without regression-testing all parent flows.

**How to avoid:** Treat child input/output API names as contract; version child flows or communicate breaking changes; run Flow test coverage or manual activation checks for each parent.
