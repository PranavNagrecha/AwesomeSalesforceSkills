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

## Anti-Pattern 6: Claiming "View Encrypted Data" Gates Shield Plaintext

**What the LLM generates:** "Users need the *View Encrypted Data*
permission to see the decrypted value; without it they see `*********`"
— applied to a **Shield Platform Encryption** field. Test plans and
permission matrices are then built on toggling that permission.

**Why it happens:** Salesforce shipped two unrelated encryption
products. Classic Encryption (the legacy `Encrypted Text` custom field
type) genuinely does mask on "View Encrypted Data", and the bulk of
older blog/forum text describes it. The model blends that into Shield,
which is the product people actually ask about. The phrasing is
plausible and self-consistent, so nothing in the answer looks wrong.

**Correct pattern:** Shield Platform Encryption decrypts
**transparently** — anyone with field-level READ on the field sees
plaintext, in Apex, SOQL, reports, and the UI. "View Encrypted Data" has
been unnecessary for Shield since Spring '17. Restrict plaintext with
**field-level security** (profiles / permission sets), page layouts, and
sharing. State which product a claim applies to: Classic → "View
Encrypted Data"; Shield → FLS.

**Why this one matters more than the rest:** it fails in the dangerous
direction. It tells a reader their PII is masked from users who can in
fact read it in plaintext.

**Detection hint:** the string `View Encrypted Data` co-occurring with
`Shield`, `Platform Encryption`, `deterministic`, or `probabilistic` in
the same document, with no sentence scoping it to Classic Encryption.
Equivalently: any test plan whose "cannot see plaintext" row is a
permission toggle rather than an FLS change.
