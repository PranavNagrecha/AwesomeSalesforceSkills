# LLM Anti-Patterns — Apex Enum Patterns

Common mistakes AI coding assistants make when generating or advising on Apex Enum Patterns.

---

## Anti-Pattern 1: Bare `Enum.valueOf(string)` against untrusted input

**What the LLM generates.**

```apex
RenewalAction a = RenewalAction.valueOf(record.Action__c);
```

**Correct pattern.** Wrap in try/catch with a fallback or typed
exception. `valueOf` throws `System.NoSuchElementException` for
unknown input — fatal in production when a picklist value drifts
from the enum.

**Detection hint.** Any `valueOf` call on an enum where the input
is a field, parameter, or HTTP body without surrounding try/catch.

---

## Anti-Pattern 2: `switch on Enum` without `when else`

**What the LLM generates.**

```apex
switch on action {
    when NOTIFY_OWNER { notifyOwner(opp); }
    when ESCALATE     { escalate(opp); }
}
```

**Correct pattern.** Always include `when else { throw new
IllegalArgumentException('Unhandled: ' + action); }`. Apex `switch`
is not exhaustive at compile time, and a missed case is silent.

**Detection hint.** Any `switch on` over an enum without a `when
else` branch is missing the exhaustiveness check.

---

## Anti-Pattern 3: Persisting `enum.ordinal()` to a field

**What the LLM generates.**

```apex
opp.RenewalAction__c = String.valueOf(action.ordinal());
```

**Correct pattern.** `opp.RenewalAction__c = action.name();`.
Ordinals shift when values are reordered or inserted; names are
stable.

**Detection hint.** Any `.ordinal()` call whose result is written
to an SObject field, JSON, or Custom Metadata is brittle.

---

## Anti-Pattern 4: Treating Apex enums like Java enums

**What the LLM generates.**

```apex
public enum Severity {
    LOW(1), MEDIUM(2), HIGH(3);
    private Integer level;
    private Severity(Integer level) { this.level = level; }
}
```

**Correct pattern.** Apex enums have no constructors, methods, or
per-constant data. Use a parallel map: `Map<Severity, Integer>
LEVELS = new Map<Severity, Integer>{ Severity.LOW => 1, ... }`.

**Detection hint.** Any constructor, method, or instance field on
an Apex enum is invalid — won't compile.

---

## Anti-Pattern 5: Reordering values in a `global` enum

**What the LLM generates.** A refactor that alphabetizes a `global
enum LicenseTier { ENTERPRISE, FREE, PRO }`.

**Correct pattern.** In managed packages, `global` enum values are
a stable contract. Add new values at the end; never reorder.
Subscribers compile against the old order via ordinals (even
indirectly through serialized data).

**Detection hint.** Any reorder of a `global` enum in a managed
package is a breaking change.

---

## Anti-Pattern 6: String dispatch instead of enum dispatch

**What the LLM generates.**

```apex
if (action == 'NOTIFY_OWNER') { ... }
else if (action == 'Escalate') { ... }   // case mismatch — silent miss
```

**Correct pattern.** Convert to enum at the boundary, then
`switch on RenewalAction`. The compiler catches enum typos; string
typos compile and fail at runtime.

**Detection hint.** Any chain of `if (str == 'LITERAL')` for an
enumerable concept should be promoted to a real enum.

---

## Anti-Pattern 7: Mixing case in JSON deserialization

**What the LLM generates.**

```apex
String body = '{"action":"escalate"}';
ActionRequest r = (ActionRequest) JSON.deserialize(body, ActionRequest.class);
```

If `ActionRequest.action` is typed as the `RenewalAction` enum,
deserialization fails because `'escalate'` is not the canonical
form `'ESCALATE'`. The LLM rarely surfaces this.

**Correct pattern.** Either type the field as `String` and convert
manually with normalization, or document and enforce the canonical
form upstream.

**Detection hint.** Any `JSON.deserialize` into a class with an
enum field where the input source is uncontrolled needs a
normalization layer.
