# LLM Anti-Patterns — Agentforce PII Redaction

## Anti-Pattern 1: Ship Raw Fields Into Prompt

**What the LLM generates:** `{{Contact.SSN__c}}` in template.

**Why it happens:** binds what's available.

**Correct pattern:** prompts receive a redacted context object, not raw
SObject references.

## Anti-Pattern 2: Rely On Trust Layer Alone

**What the LLM generates:** "Einstein Trust Layer handles PII."

**Why it happens:** assumes platform does all.

**Correct pattern:** redact before; Trust Layer is the last line.

## Anti-Pattern 3: Ad-Hoc Regex For Sensitive Categories

**What the LLM generates:** one regex per call site.

**Why it happens:** copy-paste pressure.

**Correct pattern:** a centralised detector module with tested patterns
and a change log.

## Anti-Pattern 4: Log The Raw Value While Logging The Masked One

**What the LLM generates:** `System.debug('raw=' + c.Email + ' masked='
+ m)`.

**Why it happens:** debugging crutch.

**Correct pattern:** never log raw PII. Audit log records the action
and field name only.

## Anti-Pattern 5: Unsanitised RAG Corpus

**What the LLM generates:** loads full KB into retriever.

**Why it happens:** assumes KB is safe.

**Correct pattern:** scan and sanitise KB; treat retrieved chunks as
inputs requiring redaction.
