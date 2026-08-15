# Gotchas — Apex-Defined Types

Non-obvious constraints on the Apex-defined data type. Almost all of them share
one property: the class compiles and deploys cleanly, and the failure appears
somewhere else.

---

## Gotcha 1: Inner Classes Are Not Supported

**What happens:** A nested DTO — the idiomatic Apex shape — produces a field Flow
cannot bind. The class compiles perfectly.

**When it occurs:** Any nested structure written as an inner class. Inner classes
are not supported by the Apex-defined data type, and neither is an outer class
that has the same name as an inner class.

**How to avoid:** Every type Flow touches is a separate top-level class in its own
file, including the nested ones. `List<DailyForecast>` is fine as a field; the
`DailyForecast` definition just cannot live inside `WeatherResponse`. Check for
name collisions across the org while you are at it.

---

## Gotcha 2: There Is No `Map`

**What happens:** A `Map<String, String>` field is invisible in Flow, with no
error explaining why.

**When it occurs:** Always. The supported field types are Boolean, Integer, Long,
Decimal, Double, Date, DateTime, and String — single values and lists of each —
plus lists of other supported Apex-defined types. `Map` is not among them.

**How to avoid:** Model as `List<KeyValue>` where `KeyValue` is its own top-level
class. But first ask whether you need the bag at all: Flow has no map either, so
looking up one key is a Loop with a Decision, which is O(n) per lookup and
multiplies by the interview batch size. If the flow only consumes three specific
keys, give the class three named fields and do the lookup in Apex, where `Map`
exists.

---

## Gotcha 3: A Missing `@AuraEnabled` Hides the Field Silently

**What happens:** A field exists on the class, is populated correctly in Apex, and
does not appear in the Flow picker.

**When it occurs:** The `@AuraEnabled` annotation on each field is required.
Without it the field is simply absent from Flow's view of the type — no error, no
warning.

**How to avoid:** Annotate every field. And note that `JSON.serialize` emits
unannotated fields happily, so a round-trip test does *not* catch a dropped
annotation. Guard it in code review or with a static check over the class source.

---

## Gotcha 4: Adding Any Constructor Removes the Required One

**What happens:** A convenience constructor is added and Flow can no longer build
instances of the type.

**When it occurs:** A no-argument constructor is required. Apex supplies one
implicitly only while you declare none; the moment a constructor with arguments
appears, the implicit one is gone.

**How to avoid:** Declare `public MyType() {}` explicitly, with a comment saying
why, so the next person adding a convenience constructor does not silently remove
the requirement. Better still, leave the type bare and put the convenience in a
factory method on a different class.

---

## Gotcha 5: Methods and Getters Are Not Supported

**What happens:** A class with a `calculateTotal()` helper or a property getter
behaves oddly in Flow rather than failing with a message that names the cause.

**When it occurs:** Class methods are not supported, and getter methods for
fields are not supported.

**How to avoid:** Keep the type data-only — public annotated fields and a
no-argument constructor. If it would be a `record` or a plain struct in another
language, that is the right shape. Behaviour belongs in the service that produces
or consumes the type.

---

## Gotcha 6: Renaming a Field Breaks the Flow at Run Time

**What happens:** A rename passes the compiler, passes deployment, and fails the
next time the flow runs — which for a scheduled or record-triggered flow is the
next batch, with no user present.

**When it occurs:** Referential integrity is not supported for Apex class fields:
if the field is modified or deleted in the class, the flow fails. Flow binds by
name at run time and there is no compile step over that boundary.

**How to avoid:** Treat the field names as a published interface. Inventory every
flow referencing the class before renaming, and treat the change as breaking with
the same discipline `flow/flow-versioning-strategy` applies to a flow's own input
variables. A build-time assertion over the serialized field-name set is the
cheapest available guard.

---

## Gotcha 7: A List of Lists Is Not Supported as a Field

**What happens:** A field intended to hold a matrix or a grouped structure cannot
be bound.

**When it occurs:** A flow does not support a list-of-lists data type when it is
a field on an Apex-defined flow variable.

**How to avoid:** Flatten. A `List<Row>` where `Row` is a top-level class holding
a `List<String>` expresses the same shape and is supported, because the nesting
happens through a named type rather than through a doubled collection.

---

## Gotcha 8: Mirroring the Upstream Schema Multiplies Your Commitments

**What happens:** A class faithfully mirrors a 60-field API response, and every
subsequent upstream change is a change the flow can break on.

**When it occurs:** Whenever "completeness" drives the model. Because referential
integrity is unsupported, every exposed field is a name you have committed not to
change without a caller inventory.

**How to avoid:** Model only what the flow consumes. Parse the full payload in
Apex, where a `Map<String, Object>` is available and free, and project the handful
of fields Flow needs. Name the class for its role, not its source, so nobody
assumes it must track the API one-for-one.

---

## Gotcha 9: `@InvocableVariable` and `@AuraEnabled` Are Not Interchangeable

**What happens:** An invocable's request class uses `@AuraEnabled`, or a returned
type uses `@InvocableVariable`, and the fields do not appear where expected.

**When it occurs:** They serve different roles. `@InvocableVariable` marks inputs
and outputs of an invocable action; `@AuraEnabled` is what makes a field visible
on an Apex-defined *variable* type in Flow. A class can legitimately need one, the
other, or both depending on how the flow uses it.

**How to avoid:** Decide the role first. Request and response wrappers for an
invocable use `@InvocableVariable`; a type bound as a Flow variable uses
`@AuraEnabled`. Getting this wrong produces a clean compile and an empty picker.

---

## Gotcha 10: Datetime Values Serialize in GMT

**What happens:** A date-time carried through an Apex-defined type displays an
unexpected value, or an off-by-one date appears at day boundaries.

**When it occurs:** Apex `Datetime` serializes in GMT while Flow renders in the
running user's time zone. If the upstream API sent a local time without an
offset, the interpretation is already wrong before Flow sees it.

**How to avoid:** Parse explicitly with a known offset at the Apex boundary. Where
the value is genuinely a calendar date rather than an instant — a delivery date, a
due date — use `Date` rather than `Datetime` and remove the class of bug
entirely.

---

## Gotcha 11: A Managed-Package Type Carries Its Namespace

**What happens:** A flow bound to an Apex-defined type from a managed package
breaks when the package is removed, or when equivalent code is unpacked into the
local namespace.

**When it occurs:** The type is referenced with the package namespace prefix.
Unpacking the class into the local namespace produces a different fully-qualified
name, and the binding does not follow.

**How to avoid:** Treat a packaged Apex-defined type as an external dependency of
every flow that binds it. If a package is being unpacked or replaced, inventory
the flows first — the rebinding is manual and there is no compiler to find them.

---

## Gotcha 12: Big Collections of Apex-Defined Types Cost Heap and Pause Storage

**What happens:** A screen flow holding a large collection of Apex-defined
records becomes sluggish between screens, and paused interviews grow.

**When it occurs:** Heap is 6 MB synchronous and 12 MB asynchronous, and a screen
flow serializes its variables between screens — so a fat collection is paid for on
every transition. Pausing stores that state.

**How to avoid:** Model the smallest useful shape (Gotcha 8 again, for a different
reason), and trim collections before a Pause element. Carrying identifiers and
re-fetching on resume is usually both cheaper and more correct than carrying full
structures across a pause that may last days.
