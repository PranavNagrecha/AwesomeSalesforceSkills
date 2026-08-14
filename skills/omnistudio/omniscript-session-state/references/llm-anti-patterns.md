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

---

## Anti-Pattern 6: Guest Save-for-Later as a Second PHI Store

**What the LLM generates:** Native OmniScript session persistence on a public Experience Cloud script so "users can come back."

**Why it happens:** Save and Resume is a platform feature; turning it on looks free.

**Correct pattern:** Off for guest flows. Resume credentials live server-side (hashed token), not as a session Id in the URL. If authenticated portal save-for-later is required, encrypt, TTL, and purge in the **same** job as the intake row. The session blob holds the PII the purge was meant to destroy.

**Detection hint:** Guest OmniScript with session save on; purge job that deletes application rows but not OmniScript saved sessions.

---

## Anti-Pattern 7: Resume Token in the URL Without Referrer Policy

**What the LLM generates:** `/s/resume?sid=…` linked from an email.

**Why it happens:** Deep links are convenient.

**Correct pattern:** Opaque token, short TTL, `referrer-policy` on the resume page. Experience Cloud logout ≠ OmniScript session end — detect re-auth.
