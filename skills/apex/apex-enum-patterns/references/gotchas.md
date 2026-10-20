# Gotchas — Apex Enum Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: `Enum.valueOf(String)` throws on unknown input

Bare `MyEnum.valueOf('NOT_A_VALUE')` throws: "an exception is thrown if the
input string doesn't match an enum value" (apexref 262 L214381-214382). UNVERIFIED (2026-10-20):
that the type is `System.NoSuchElementException` — the Apex Reference lists
that exception for items outside a list's bounds (L215015), not for
`valueOf` — and whether the match is case-sensitive (the guide's own example
calls `StatusCode.valueOf('delete_failed')`, L214406). There is no
`tryValueOf`. Wrap in try/catch on `Exception` when the input comes from
configuration, a field, or an HTTP request.

---

## Gotcha 2: Apex `switch on` is not exhaustive

Without a `when else` block, a `switch` with no matching `when` takes "no
action" (apex dev guide 264 L2865); `when else` is "recommended … although it
isn't required", especially with enum types, and must be the last block
(L2890-2894). There is no fall-through (L2867). Always include `when else {
throw ... }`.

---

## Gotcha 3: Ordinals are NOT stable across edits

`MyEnum.VALUE_A.ordinal()` returns the position of the value in the list of
Enum values, starting with zero (apexref 262 L214386-214387). If someone reorders or inserts values, ordinals shift.
Never persist ordinals — persist `name()` (the string) and convert
back via `valueOf`.

---

## Gotcha 4: No methods or fields on enum constants

Apex enums have no constructor syntax and cannot take user-defined methods
(apex dev guide 264 L1753, L1825) — unlike Java. UNVERIFIED (2026-10-20): that per-constant data is
impossible; the guide does not list it. Anything richer than a name needs a parallel `Map<Enum,
SomeType>` or a wrapper class.

---

## Gotcha 5: `global` enums cannot be safely renamed or removed

In a managed package, "you can't remove or reorder global enum values, although you can add new enum values" (apex dev guide 264 L43920). UNVERIFIED (2026-10-20): that subscribers' Apex fails to compile after a removal. The documented risk of an addition is that a subscriber `switch` over package enum values "might not behave as expected" unless it has a `when else` (L2890-2893). Add only at the end of the list; never delete.

---

## Gotcha 6: Enum values returned from JSON are strings

UNVERIFIED (2026-10-20): that `JSON.serialize(MyEnum.VALUE_A)` produces `"VALUE_A"`, that `JSON.deserialize(...)` of an enum-valued field requires exact spelling, and that mixed case fails silently. The only corpus statement is scoped to ConnectApi: "Enum values and exceptions cannot be serialized or deserialized" (apex dev guide 264 L26232). Convert at the boundary and test the real payload.

---

## Gotcha 7: Comparing enum values with `==` is correct; `equals()` is not

```apex
if (a == RenewalAction.ESCALATE) { ... }   // correct
if (a.equals(RenewalAction.ESCALATE)) { } // works but unidiomatic
```

UNVERIFIED (2026-10-20): that `==` on enums is identity comparison and that `equals()` works — neither is in the corpus; `==` is the form the guide itself uses (apex dev guide 264 L1765).

---

## Gotcha 8: Cannot have an enum inside an inner class

UNVERIFIED (2026-10-20): the nesting rule — the corpus defines enums with `public enum Season {WINTER, SPRING, SUMMER, FALL}` (apex dev guide 264 L1757) and states no placement restriction. If the compiler rejects an inner declaration, move it up one level.

---

## Gotcha 9: `Schema.PicklistEntry` does not return enums

Picklist entries (`Schema.PicklistEntry`; `public String getValue()`, apexref 262 L193712) return `String` values, not enum instances. There is
no automatic mapping. Build the `Map<String, MyEnum>` yourself; the
example in `examples.md` § 3 shows the canonical pattern.
