# LLM Anti-Patterns — Apex-Defined Types

Mistakes AI assistants reliably make when writing a class for Flow to bind. They
share a signature: the generated Apex compiles and deploys, and the flow cannot
use it.

---

## Anti-Pattern 1: Nesting With an Inner Class

**What the LLM generates:** a parent class containing an inner class for the
nested structure — the standard Apex DTO shape.

**Why it happens:** it is the correct and idiomatic pattern for every other use
of Apex wrapper classes, including LWC `@AuraEnabled` returns. Nothing about the
prompt signals that this one context forbids it.

**Correct pattern:** inner classes are not supported by the Apex-defined data
type. Every type Flow touches is a separate top-level class in its own file.
`List<DailyForecast>` as a field is fine; `DailyForecast` just cannot be declared
inside the parent. Also check that no outer class shares a name with an inner
class elsewhere, which is separately unsupported.

**Detection hint:** a nested `class` declaration inside a class whose fields
carry `@AuraEnabled`.

---

## Anti-Pattern 2: `Map<String, Object>` for Flexibility

**What the LLM generates:** a catch-all map field, usually justified as
future-proofing against schema change.

**Why it happens:** loose typing genuinely is more flexible in Apex, and the
model optimises for the requirement as stated rather than for the binding
constraint.

**Correct pattern:** `Map` is not on the supported type list — the supported set
is Boolean, Integer, Long, Decimal, Double, Date, DateTime, and String, single
values and lists. Model as `List<KeyValue>` with `KeyValue` as its own top-level
class. Better: ask whether the bag is needed at all. Flow has no map either, so a
key lookup is a Loop with a Decision, O(n) per lookup, multiplied by the interview
batch size. Named fields plus an Apex-side lookup is usually the right answer.

**Detection hint:** `Map<` in a class whose fields are `@AuraEnabled`.

---

## Anti-Pattern 3: Omitting `@AuraEnabled`

**What the LLM generates:** a plain class with public fields and no annotations.

**Why it happens:** it defaults to Apex bean idioms, and the annotation is
invisible in the problem statement. A round-trip test the model writes will pass
without it, which reinforces the mistake.

**Correct pattern:** every field Flow must see needs `@AuraEnabled`. Without it
the field is silently absent from Flow — no error. And note that
`JSON.serialize` emits unannotated fields, so a serialization test does not catch
this; it needs code review or a static check over the class source.

**Detection hint:** a public field with no annotation in a class described as an
Apex-defined type.

---

## Anti-Pattern 4: A Constructor With Required Arguments

**What the LLM generates:** `public PricingBreakdown(Decimal subtotal, Decimal
tax)` as a convenience, often alongside otherwise-correct code.

**Why it happens:** parameterised constructors are good design in every
language the model knows, and nothing signals that adding one removes the
implicit no-argument constructor.

**Correct pattern:** a no-argument constructor is required. Declare
`public MyType() {}` explicitly — with a comment saying why — so it survives the
next person adding a convenience constructor. Or keep the type bare and put the
convenience in a factory on a different class, where behaviour is allowed.

**Detection hint:** any constructor with parameters and no explicit no-argument
constructor alongside it.

---

## Anti-Pattern 5: Adding Methods or Getters

**What the LLM generates:** a `calculateTotal()` helper, a static `of(...)`
factory, validation in a setter, or a property getter.

**Why it happens:** encapsulation is correct object-oriented design and the model
is rewarded for it everywhere else.

**Correct pattern:** class methods are not supported, and getter methods for
fields are not supported. Keep the type data-only: public annotated fields and a
no-argument constructor. If it would be a `record` or a plain struct in another
language, that is the shape.

**Detection hint:** any method declaration in a class presented as an
Apex-defined type.

---

## Anti-Pattern 6: Mirroring the Whole Upstream Schema

**What the LLM generates:** a class with a field for every field in the API
response, described as complete and future-proof.

**Why it happens:** completeness is the safe-looking answer, and the model cannot
see which fields the flow consumes.

**Correct pattern:** referential integrity is not supported — modify or delete a
field in the class and the flow fails, at run time. Every exposed field is a name
you have committed not to change without a caller inventory, so 60 fields is 60
commitments to support one screen. Parse the full payload in Apex, where a
`Map<String, Object>` is free, and project only what the flow consumes.

**Detection hint:** a class with more fields than the flow's elements reference,
or a class named after the upstream API rather than its role.

---

## Anti-Pattern 7: Confusing `@InvocableVariable` With `@AuraEnabled`

**What the LLM generates:** `@AuraEnabled` on an invocable's request wrapper, or
`@InvocableVariable` on a type bound as a Flow variable.

**Why it happens:** both annotations make fields visible to Flow in some sense,
and the distinction between "input to an invocable action" and "field on an
Apex-defined variable type" is subtle.

**Correct pattern:** `@InvocableVariable` marks inputs and outputs of an
invocable; `@AuraEnabled` is what exposes fields on an Apex-defined variable type.
Getting it wrong produces a clean compile and an empty picker in Flow Builder.

**Detection hint:** `@AuraEnabled` on a class used only as an `@InvocableMethod`
parameter, or vice versa.

---

## Anti-Pattern 8: An Invocable That Takes a Single Record

**What the LLM generates:** `@InvocableMethod public static PricingBreakdown
run(PriceQuoteRequest req)` — a scalar signature.

**Why it happens:** it matches the requirement's phrasing ("return the pricing
for a quote") and produces the simplest correct-looking code.

**Correct pattern:** invocable methods take a `List<>` and return a `List<>` of
the same length in the same order, precisely so a flow can call them once with a
collection. A scalar signature forces the flow author into a per-iteration call
inside a loop, which defeats the Apex author's bulkification from outside the
class and is the usual reason an Apex-backed flow ends up slower than the
pure-Flow version it replaced.

**Detection hint:** an `@InvocableMethod` whose parameter or return type is not a
`List<>`.

---

## Anti-Pattern 9: Treating a Rename as a Refactor

**What the LLM generates:** a rename applied across the Apex codebase, with the
successful compile presented as verification.

**Why it happens:** rename-and-compile is the standard safe refactor everywhere
else, and the flow metadata is not in the model's context.

**Correct pattern:** Flow binds these fields by name at run time and there is no
compile step over that boundary. Referential integrity is explicitly unsupported.
Inventory every flow referencing the class before renaming, and add a build-time
assertion over the serialized field-name set so the next rename fails the build
rather than the next scheduled batch.

**Detection hint:** a field rename with no mention of flow consumers.

---

## Anti-Pattern 10: Ignoring the Cost of a Big Collection

**What the LLM generates:** a design that loads a large collection of
Apex-defined records into a screen flow variable and carries it across screens
and pauses.

**Why it happens:** the collection is the natural data structure for the
requirement, and heap is not visible in the prompt.

**Correct pattern:** heap is 6 MB synchronous and 12 MB asynchronous, and a
screen flow serializes its variables between screens, so the cost is paid on every
transition rather than once — and pausing stores that state. Model the smallest
useful shape and carry identifiers across a pause, re-fetching on resume, which is
also more correct for anything another user can edit.

**Detection hint:** an Apex-defined collection variable held across more than two
screens, or across a Pause element.
