# LLM Anti-Patterns — Apex-Defined Types

## Anti-Pattern 1: Forgetting `@AuraEnabled`

**What the LLM generates:** a plain class with public fields.

**Why it happens:** defaults to Apex bean idioms.

**Correct pattern:** every field Flow must see has `@AuraEnabled`.

## Anti-Pattern 2: `Map<String, Object>` For "Flexibility"

**What the LLM generates:** a catch-all attribute map.

**Why it happens:** "loose typing is easier."

**Correct pattern:** `List<KeyValue>` with a typed sub-class. Flow can
bind and loop it.

## Anti-Pattern 3: Exposing Whole Upstream Schema

**What the LLM generates:** mirrors every field of the external API
response.

**Why it happens:** "completeness."

**Correct pattern:** expose only what the Flow actually consumes. Fewer
fields = fewer breaking changes.

## Anti-Pattern 4: Required-Arg Constructor

**What the LLM generates:** a class with `this(String a, Integer b)`.

**Why it happens:** Java instinct.

**Correct pattern:** no-arg constructor. Flow cannot pass args.

## Anti-Pattern 5: Renaming A Field Without Updating Flow

**What the LLM generates:** edits the Apex class, commits, moves on.

**Why it happens:** refactoring muscle memory.

**Correct pattern:** flow references bind by field name. Treat rename
as a breaking change and update every consuming Flow.

## Anti-Pattern 6: Mixing Behaviour Into The Type

**What the LLM generates:** adds helper methods, static factories,
validation inside the class.

**Why it happens:** "object-oriented design."

**Correct pattern:** keep Apex-Defined Types as data-only. Behaviour
lives in services that produce or consume them.
