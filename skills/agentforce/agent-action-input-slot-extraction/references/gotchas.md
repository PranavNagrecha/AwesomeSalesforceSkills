# Gotchas — Agent Action Input Slot Extraction

Non-obvious behaviors that cause real production problems in this domain.

## Gotcha 1: Description text is the primary lever, not variable name

**What happens:** Engineer renames `String d` to `String appointmentDate`, expects extraction quality to improve. It doesn't.

**When it occurs:** Always — the LLM reads the `description` field much more heavily than the variable name.

**How to avoid:** Spend the optimization budget on description text. Variable names are for code readability.

---

## Gotcha 2: Date inputs default to running-user timezone

**What happens:** User in PT says "next Tuesday." Agent runs as integration user in UTC. Extracted date is one day off.

**When it occurs:** Any cross-timezone agent invocation.

**How to avoid:** State the timezone in the description (`"in the customer's local timezone, derived from User.TimeZoneSidKey"`). Or take the date as a string and parse explicitly with timezone in Apex.

---

## Gotcha 3: Required + un-extracted = built-in awkward re-prompt

**What happens:** Agent says "I need more information to proceed." User has no idea what's missing.

**When it occurs:** Required slots without configured per-slot re-prompts.

**How to avoid:** Always override the re-prompt per required slot. Name the slot, give an example.

---

## Gotcha 4: Hallucinated lookup IDs validate as well-formed

**What happens:** LLM emits `001000000000XYZAA`. SOQL returns no rows. The action throws a generic "record not found" the agent can't loop on.

**When it occurs:** Any `Id` input.

**How to avoid:** Never accept lookup IDs from the LLM. Take names; resolve in Apex with explicit ambiguity and not-found handling.

---

## Gotcha 5: Picklist case sensitivity

**What happens:** LLM emits "high"; Apex enum coercion to `Severity.HIGH` fails.

**When it occurs:** Any picklist/enum input where the description doesn't pin the case.

**How to avoid:** Either describe explicitly ("emit the uppercase value only") or normalize case in Apex (`String.toUpperCase()`) before coercion.
