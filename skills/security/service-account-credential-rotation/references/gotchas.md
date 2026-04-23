# Service Account Credential Rotation — Gotchas

## 1. `PasswordNeverExpires` On The User Record

A single checkbox disables the whole rotation program for a service account. Audit for it.

## 2. Rotating Secret Immediately Invalidates Old Sessions

Connected app secret rotation without a dual-credential grace window drops every consumer using the old secret.

## 3. JWT Cert Slot Limits

Connected apps allow a limited number of signing certs. Plan the handover window — do not pile up.

## 4. Named Credential Refresh Tokens

Refresh tokens for per-user named credentials invalidate if the user's password changes. User re-auth required.

## 5. Removing A Connected App ≠ Revoking Tokens

Retiring the connected app UI-side does not revoke active OAuth tokens issued by it. Revoke explicitly.
