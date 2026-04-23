# OmniScript Session State — Examples

## Example 1: Onboarding With Resume Email

**OmniScript:** 12-step customer onboarding.

**Persistence:** `Onboarding_Session__c` with fields for each step
section + `StepId__c`, `Version__c`, `ExpiresAt__c`.

**Save trigger:** on step transition, invoke DataRaptor Save.

**Resume:** sending a tokenized link via email, 48-hour expiry; token =
signed JWT with `sessionId` + `contactId`.

**Purge:** scheduled Flow deletes `ExpiresAt__c < NOW()` sessions
nightly.

---

## Example 2: Device-Hop Quote Configurator

User starts on desktop, switches to mobile. Resume link sent via SMS;
mobile OmniScript loads `Session__c` row; current step renders with
prior answers pre-populated from tracking.

**Security:** link expires 1h; session includes device fingerprint for
audit.

---

## Example 3: Conflict Detection

Two tabs open. Tab A changes step 5, saves version=3. Tab B (still at
version=2) tries to save; Save DR sees mismatch and routes to a "this
session is out of sync, refresh" step.

---

## Anti-Pattern: State In URL

A team serialized the entire OmniScript data JSON to base64 and put it
in the resume URL. Email systems clipped the URL, browser history
leaked PII, and Experience Cloud logs captured it. Fix: store on
server, reference by id only.
