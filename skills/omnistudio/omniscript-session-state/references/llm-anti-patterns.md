# LLM Anti-Patterns — OmniScript Session State

## Anti-Pattern 1: Answers In The URL

**What the LLM generates:** `?state=base64(answers)`.

**Why it happens:** "stateless" instinct.

**Correct pattern:** server-side session, URL carries an opaque token.

## Anti-Pattern 2: Save On Every Keystroke

**What the LLM generates:** input change → DataRaptor Save.

**Why it happens:** real-time feel.

**Correct pattern:** save on step boundary; debounce if mid-step save is
required.

## Anti-Pattern 3: No Expiry

**What the LLM generates:** `Session__c` with no retention field.

**Why it happens:** "keep data forever."

**Correct pattern:** tiered retention, scheduled purge.

## Anti-Pattern 4: PII In Plain Fields

**What the LLM generates:** SSN__c text(11), DOB__c date on Session.

**Why it happens:** modeled as regular record.

**Correct pattern:** encrypted fields or tokens to a vault; purge
aggressively.

## Anti-Pattern 5: Silent Overwrite

**What the LLM generates:** save ignores concurrent edits.

**Why it happens:** simpler code path.

**Correct pattern:** version field + conflict branch.
