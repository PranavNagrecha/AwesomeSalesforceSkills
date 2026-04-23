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
