# LLM Anti-Patterns — OAuth Token Management

Common mistakes AI coding assistants make when generating or advising on OAuth token lifecycle work on Salesforce.

## Anti-Pattern 1: Claiming a single universal access token lifetime

**What the LLM generates:** “Salesforce access tokens always expire in two hours, so set a timer for 110 minutes.”

**Why it happens:** Training data over-indexes on common defaults and omits the interaction between org Session Settings and Connected App session timeout.

**Correct pattern:**

```
Explain that effective access token lifetime follows Salesforce documentation for
Connected App session policies bounded by org session settings; use expires_in
from the token response plus clock skew rather than a hard-coded interval.
```

**Detection hint:** Phrases like “always 2 hours” or a single magic number with no mention of Connected App or org settings.

---

## Anti-Pattern 2: Treating access-token revocation as equivalent to killing refresh

**What the LLM generates:** “Revoke the session in Setup; the attacker cannot get new tokens.” (when only an access token or single session was cleared)

**Why it happens:** Conflation of UI “session” language with OAuth refresh grants and parallel workers.

**Correct pattern:**

```
Distinguish revoke targets: revoking a refresh token invalidates dependent access
tokens for that grant; revoking one access token does not automatically remove
the ability to mint new access tokens if a refresh token remains valid.
```

**Detection hint:** One vague “revoke token” step with no token type or endpoint parameter discussion.

---

## Anti-Pattern 3: Inventing custom token introspection URLs

**What the LLM generates:** A fabricated path such as `/services/oauth2/introspect/custom` or vendor-generic OpenID URLs without checking Salesforce’s documented introspection endpoint and prerequisites.

**Why it happens:** OpenID Connect introspection is standardized elsewhere; models generalize without Salesforce-specific paths and licensing notes.

**Correct pattern:**

```
Point to Salesforce Help for the OpenID Connect token introspection endpoint,
note org and Connected App constraints from that page, and avoid presenting
unverified URL shapes.
```

**Detection hint:** Non-documented hostnames, `/v1/` style paths atypical for Salesforce OAuth services, or “just POST JSON to /introspect” without citing Help.

---

## Anti-Pattern 4: Ignoring refresh token rotation return payloads

**What the LLM generates:** Sample refresh code that reads `access_token` from the response but discards a refreshed `refresh_token` field entirely.

**Why it happens:** Minimal OAuth 2.0 examples omit rotation; Salesforce’s rotation behavior is a platform-specific extension of client responsibilities.

**Correct pattern:**

```
When rotation is enabled, persist the latest refresh_token from every successful
refresh response before using the new access_token; document failure modes when
the old refresh is replayed.
```

**Detection hint:** Token refresh snippets with no assignment from `refresh_token` in the JSON body when rotation is in scope.

---

## Anti-Pattern 5: Advising JWT bearer “to avoid OAuth entirely”

**What the LLM generates:** “Skip OAuth—use JWT and you have no tokens to manage.”

**Why it happens:** JWT bearer reduces interactive refresh loops but still produces access tokens with lifetimes governed by session policy; the statement over-corrects.

**Correct pattern:**

```
JWT bearer flow still yields access tokens subject to session timeout rules; it
removes refresh-token handling for that design but does not remove token expiry
or revocation considerations.
```

**Detection hint:** Absolute language (“no tokens”, “no OAuth”) paired with JWT sales pitch.
