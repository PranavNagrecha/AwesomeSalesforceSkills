# LLM Anti-Patterns — Encrypted Field Queries

## Anti-Pattern 1: Encrypt Everything With Probabilistic

**What the LLM generates:** flips every sensitive field to
probabilistic.

**Why it happens:** "stronger is better."

**Correct pattern:** choose scheme by query pattern. Probabilistic only
for display-only fields.

## Anti-Pattern 2: LIKE Search On Encrypted Field

**What the LLM generates:** `WHERE Email__c LIKE 'jane%'`.

**Why it happens:** unaware of SOQL restriction.

**Correct pattern:** deterministic + exact match, or derived hash index,
or drop encryption.

## Anti-Pattern 3: Range Filter On Encrypted Amount

**What the LLM generates:** encrypt Amount, filter `> 10000`.

**Why it happens:** treats encryption as transparent.

**Correct pattern:** leave aggregatable numerics unencrypted; enforce
FLS / masking instead.

## Anti-Pattern 4: No Custom Index

**What the LLM generates:** deterministic field used in a hot query,
with no index request.

**Why it happens:** assumes index is automatic.

**Correct pattern:** request a custom index for deterministic fields
used as selective filters.

## Anti-Pattern 5: Debug Log The Value

**What the LLM generates:** `System.debug('SSN=' + contact.SSN__c)`.

**Why it happens:** standard debug pattern.

**Correct pattern:** never log encrypted values. Event Monitoring,
replay logs, and support dumps all persist debug output.
