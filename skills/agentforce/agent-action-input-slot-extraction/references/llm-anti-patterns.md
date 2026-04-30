# LLM Anti-Patterns — Agent Action Input Slot Extraction

Common mistakes AI coding assistants make when generating slot-extraction logic.

## Anti-Pattern 1: One-word descriptions

**What the LLM generates:**

```apex
@InvocableVariable(description='Date')
public Date appointmentDate;
```

**Why it happens:** LLM mirrors the variable name into the description.

**Correct pattern:** Description must include format, example, and reject clauses. The description is the LLM's instruction manual; "Date" tells it nothing useful.

**Detection hint:** Any `@InvocableVariable(description='<single word>')` line.

---

## Anti-Pattern 2: Accepting `Id` directly

**What the LLM generates:**

```apex
@InvocableVariable(required=true) public Id accountId;
```

**Why it happens:** Treats the action like a typed function call.

**Correct pattern:** Take a `String accountName`; resolve to Id in Apex. LLMs hallucinate well-formed IDs that point to no record.

**Detection hint:** Any invocable variable typed `Id` without an accompanying name-resolution helper class.

---

## Anti-Pattern 3: No re-prompt config for required slots

**What the LLM generates:** Required slot, no per-slot re-prompt configured.

**Why it happens:** Treats the agent's built-in re-prompt as adequate.

**Correct pattern:** Configure per-slot re-prompts naming the missing slot and giving an example. Generic re-prompts confuse users.

**Detection hint:** A required `@InvocableVariable` with no corresponding entry in the topic's re-prompt config.

---

## Anti-Pattern 4: Picklist input without value enumeration

**What the LLM generates:**

```apex
@InvocableVariable(description='Severity (low/medium/high)')
public String severity;
```

**Why it happens:** Treats "low/medium/high" as enough.

**Correct pattern:** Enumerate values *with synonym disambiguation* and emit normalization. "Severity: one of LOW (cosmetic, no impact), MEDIUM (workaround exists), HIGH (production blocked). Synonyms: 'critical'/'urgent' = HIGH; 'minor'/'trivial' = LOW. Emit uppercase only."

**Detection hint:** Picklist/enum descriptions lacking explicit value definitions or synonym mapping.

---

## Anti-Pattern 5: No test-utterance suite

**What the LLM generates:** Action implementation with descriptions, no test cases.

**Why it happens:** Treats slot extraction as deterministic.

**Correct pattern:** Maintain a YAML/CSV of utterance → expected slot values. Run through the agent test harness as a regression suite. Without measurement, description tuning is guessing.

**Detection hint:** Any agent-action implementation that ships without a test-utterance file in the same module.
