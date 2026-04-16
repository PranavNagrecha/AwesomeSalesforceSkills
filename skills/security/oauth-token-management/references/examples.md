# Examples — OAuth Token Management

## Example 1: Refresh token revocation ends all active API sessions for that grant

**Context:** A mobile app uses the authorization code flow with `refresh_token` scope. Security operations believes a device backup may have copied the refresh token and wants to stop all Salesforce API traffic from that device without disabling the whole Connected App.

**Problem:** An admin revokes only the current access token from Setup. The device silently obtains another access token using the stored refresh token, so the breach window stays open.

**Solution:**

1. Revoke the **refresh token** (or use the documented revoke flow that targets the refresh credential) for that user and Connected App, per Salesforce Help for revoking OAuth tokens.
2. Invalidate local storage on the device.
3. Force the user through authorization again so a **new** refresh token is minted under current policies.

**Why it works:** Revoking the refresh token removes the long-lived credential that can mint new access tokens; access-only revocation addresses a single session artifact, not the standing grant.

---

## Example 2: `invalid_grant` after tightening refresh token policy

**Context:** A packaged integration used refresh tokens with a “valid until revoked” policy for years. The security team changes the Connected App to expire refresh tokens after 90 days.

**Problem:** Overnight, scheduled jobs report `invalid_grant` from `https://login.salesforce.com/services/oauth2/token` and no code changes shipped.

**Solution:**

- Treat this as an expected invalidation of existing refresh tokens when policy changes are not backward-compatible with outstanding grants.
- Run a controlled **re-authorization** for each integration user (or rotate to JWT bearer if that better matches the new policy).
- Document for customers that policy tightening may require a one-time reconnect.

**Why it works:** Refresh token policy is evaluated when tokens are issued and refreshed; stricter policy often cannot apply retroactively to already-issued tokens without invalidating them.

---

## Example 3: Enabling refresh token rotation without updating middleware

**Context:** Salesforce refresh token rotation is enabled for the Connected App to reduce replay risk. The middleware stores the original refresh token in a database and overwrites it only on full service restart.

**Problem:** The first successful refresh returns a **new** refresh token in the token response, but the middleware ignores it. The next refresh attempt fails because the old refresh token was invalidated at rotation.

**Solution:**

- On every successful refresh response, persist the **latest** `refresh_token` field before using the new access token.
- Add monitoring for `invalid_grant` immediately after successful refreshes (often a sign of stale refresh persistence).

**Why it works:** Rotation assumes the client participates in the chain of refresh credentials; ignoring the new token breaks the contract described in Salesforce documentation for refresh token rotation.

---

## Anti-Pattern: Using the limits resource as a token validity check

**What practitioners do:** Call a lightweight REST resource on a timer to “see if the session is still good.”

**What goes wrong:** That pattern confuses **API availability** with **OAuth token semantics** and does not replace revoke, introspection, or proper 401 handling.

**Correct approach:** Track expiry from token response fields and session policy, refresh proactively, handle 401 with a single controlled refresh or re-auth path, and use documented introspection where required.
