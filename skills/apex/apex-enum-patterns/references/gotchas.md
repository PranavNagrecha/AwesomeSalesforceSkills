# Gotchas — Apex Enum Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: `Enum.valueOf(String)` throws on unknown input

Bare `MyEnum.valueOf('NOT_A_VALUE')` throws
`System.NoSuchElementException`. There is no `tryValueOf`. Always
wrap in try/catch when the input comes from configuration, a
field, or an HTTP request.

---

## Gotcha 2: Apex `switch on` is not exhaustive

The compiler does not warn when a `switch on Enum` omits a case.
Without a `when else` branch, the switch is a silent no-op for any
unhandled value. Always include `when else { throw ... }`.

---

## Gotcha 3: Ordinals are NOT stable across edits

`MyEnum.VALUE_A.ordinal()` returns the position of the value in the
declaration. If someone reorders or inserts values, ordinals shift.
Never persist ordinals — persist `name()` (the string) and convert
back via `valueOf`.

---

## Gotcha 4: No methods or fields on enum constants

Apex enums cannot have constructors, methods, or per-constant data —
unlike Java. Anything richer than a name needs a parallel `Map<Enum,
SomeType>` or a wrapper class.

---

## Gotcha 5: `global` enums cannot be safely renamed or removed

In a managed package, removing or renaming a `global` enum value is a
breaking change. Subscribers may have switched on the value, and their
Apex will fail to compile after the upgrade. Add only at the end of the
list; never delete.

---

## Gotcha 6: Enum values returned from JSON are strings

`JSON.serialize(MyEnum.VALUE_A)` produces `"VALUE_A"` — the string
form. `JSON.deserialize(...)` of an enum-valued field requires the
exact spelling and an unambiguous declaration. Mixing case (`"value_a"`)
fails silently.

---

## Gotcha 7: Comparing enum values with `==` is correct; `equals()` is not

```apex
if (a == RenewalAction.ESCALATE) { ... }   // correct
if (a.equals(RenewalAction.ESCALATE)) { } // works but unidiomatic
```

`==` on enums is identity comparison, which is what you want.

---

## Gotcha 8: Cannot have an enum inside an inner class

Enums must be top-level or directly nested in a top-level class. You
cannot declare an enum inside an inner class or a method. Move it up
one level.

---

## Gotcha 9: `Schema.PicklistEntry` does not return enums

Picklist entries return `String` values, not enum instances. There is
no automatic mapping. Build the `Map<String, MyEnum>` yourself; the
example in `examples.md` § 3 shows the canonical pattern.
