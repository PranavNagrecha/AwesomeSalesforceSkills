# Service Account Credential Rotation — Gotchas

## 1. The Password Never Expires Permission On The Service Account's Profile Or Permission Set

Password Never Expires is a user permission granted through a profile or permission set (secguide 262 L6398; API name `PasswordNeverExpires`, platform_events 264 L25315) — not a field on the User record, as an earlier version of this gotcha said. One grant disables password expiry for every user holding it. Audit profiles and permission sets for it.

## 2. Rotating A Secret Breaks Every Consumer Still On It

Connected app secret rotation without a coordinated cutover drops every consumer using the old secret. The metadata `consumerSecret` can't be edited after save (api_meta 264 L37441-37443). UNVERIFIED (2026-10-20): whether Setup offers a staged old-plus-new window is Help-only.

## 3. One Certificate Per Connected App

`ConnectedAppOauthConfig.certificate` is a single PEM-encoded certificate string (api_meta 264 L37419); the External Client App field is also singular (L67151-67155). There is no second slot for an overlap, so a JWT certificate change is a coordinated cutover or a move to a second app.

## 4. Named Credential Refresh Tokens

Salesforce refreshes expired or invalid access tokens on a 401 (api_meta 264 L66295-66298), but a refresh token only lives as long as the app's `refreshTokenPolicy` allows (default infinite, L37835-37836). UNVERIFIED (2026-10-20): that per-user refresh tokens are invalidated by a password change is Help-only. Plan user re-auth.

## 5. Removing A Connected App ≠ Revoking Tokens

UNVERIFIED (2026-10-20), Help-only: retiring the connected app UI-side does not revoke active OAuth tokens issued by it. Revoke explicitly and confirm with a failed call.
