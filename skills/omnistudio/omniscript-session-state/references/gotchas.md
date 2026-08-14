# OmniScript Session State — Gotchas

## 1. Native Tracking Has Schema Constraints

The OmniScript tracking object stores state as serialized blobs in a
few fields. Complex queries require custom session objects.

## 2. Big Object Queries Are Limited

Big Objects restrict filter fields to the index. Design the index
before you need to query.

## 3. Resume URLs Leak Via Referrer

If the resume page has outbound links, the token may appear in the
Referer header. Set `referrer-policy`.

## 4. Experience Cloud Session ≠ OmniScript Session

Experience Cloud can log the user out while the OmniScript thinks the
session is live. Detect re-auth needs.

## 5. Shield Encryption Alters Query Semantics

Encrypted fields cannot be used in some SOQL filters. Plan the schema
accordingly.

## 6. Scheduled Purge Can Miss Sessions Mid-Save

A purge job that deletes based on `ExpiresAt__c` can delete a session
while a save is in flight. Use a versioned soft-delete.

---

## 7. Guest OmniScript Session Persistence Is a Second PHI Store

**What happens:** Save-for-later / native OmniScript saved sessions sit **outside** the application token TTL and the intake-purge job. Guests reading other sessions is a documented class of issue. The session blob can hold the same PII the purge was meant to destroy.

**When it occurs:** Guest multi-step applications with session save on; Experience Cloud public sites.

**How to avoid:** Turn OmniScript session persistence **off** for guest flows. Keep resume credentials server-side (hashed token, not the session Id in the URL). If save-for-later is required for authenticated portal users, encrypt, TTL, and purge in the same job as the intake row. See `omnistudio-security` for ContextId; this gotcha is the store, not the Id.
