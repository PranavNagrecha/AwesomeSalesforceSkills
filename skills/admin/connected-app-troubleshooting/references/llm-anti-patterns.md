# LLM Anti-Patterns — Connected App Troubleshooting

Mistakes AI assistants make when triaging Connected App OAuth
issues.

---

## Anti-Pattern 1: "Just retry" advice for `invalid_grant`

**What the LLM generates.** "Refresh tokens sometimes fail; add a
retry loop."

**Why it happens.** Generic API-error advice.

**Correct pattern.** `invalid_grant` after a previous success
points at refresh token policy. Diagnose via Login History and
fix the policy, not the client retry logic.

**Detection hint.** Any OAuth-error advice with "add retry"
without checking Login History first is missing the diagnosis.

---

## Anti-Pattern 2: Recommending Username-Password OAuth flow for new code

**What the LLM generates.** "Use the username-password OAuth
flow with the user's credentials and your Consumer Key/Secret."

**Why it happens.** Older training data; flow is heavily
documented historically.

**Correct pattern.** Username-Password is deprecated for new
integrations. Use JWT Bearer (server-to-server) or Web Server
flow (interactive).

**Detection hint.** Any new-integration recipe using
`grant_type=password` is dated.

---

## Anti-Pattern 3: Hardcoding credentials in the integration

**What the LLM generates.**

```python
CONSUMER_KEY = "3MV..."
CONSUMER_SECRET = "1234..."
REFRESH_TOKEN = "5Aep..."
```

**Why it happens.** Config-management is implicit.

**Correct pattern.** Environment variables / secret store
(client-side) or Named Credentials (Salesforce-side). Rotation
becomes a config change, not a code change.

**Detection hint.** Any integration recipe with literal
credentials is a security smell.

---

## Anti-Pattern 4: Not checking Login History before guessing

**What the LLM generates.** "Try regenerating the Consumer
Secret" or "Check your refresh token" without Login History
investigation.

**Why it happens.** Assumes the client error is the only
signal.

**Correct pattern.** Login History (Setup → Login History or
SOQL on `LoginHistory`) often shows clearer cause: "User not
assigned to app", "Restricted IP", "Inactive user", etc.

**Detection hint.** Any OAuth diagnosis that doesn't reference
Login History is starting from incomplete information.

---

## Anti-Pattern 5: JWT `sub` = User.Email

**What the LLM generates.**

```python
jwt_payload = {"sub": "user@example.com", ...}
```

**Why it happens.** Email is the human-recognizable identifier;
LLM picks it as the natural "subject".

**Correct pattern.** `sub` must be the User.Username, exactly as
in Setup → Users. Often differs from Email by an org-suffix
(`user@example.com.acmesandbox`).

**Detection hint.** Any JWT Bearer recipe using Email for `sub`
is going to fail with `invalid_grant`.

---

## Anti-Pattern 6: Default Refresh Token Policy for server-to-server

**What the LLM generates.** Setup steps for a server-to-server
integration that don't mention Refresh Token Policy.

**Why it happens.** The default looks like a normal value; the
silent-killer behavior isn't part of the LLM's salient knowledge.

**Correct pattern.** Always specify "Refresh token is valid
until revoked" for server-to-server in Connected App setup.

**Detection hint.** Any server-to-server Connected App setup
recipe that doesn't mention Refresh Token Policy is going to
produce day-2 failures.

---

## Anti-Pattern 7: IP enforcement on cloud-hosted integrations

**What the LLM generates.** "Add the integration's IP to the
user's profile Login IP Range."

**Why it happens.** "Tighter is more secure" instinct.

**Correct pattern.** Cloud IPs (AWS Lambda, etc.) are too
dynamic for IP-range pinning. Connected App IP Relaxation =
"Relax IP restrictions" + tight user permissions is the
standard pattern.

**Detection hint.** Any "add cloud IP to profile range"
recommendation for AWS Lambda / Azure Functions / similar is
not going to work reliably; the IP set rotates.

---

## Anti-Pattern 8: Not noting per-environment Consumer Key after deploy

**What the LLM generates.** "Deploy the Connected App via
metadata to production; integration will work."

**Why it happens.** "Deploy" feels complete.

**Correct pattern.** After Connected App metadata deploy,
fetch the new Consumer Key from production Setup and update the
integration's config. Keys are environment-specific.

**Detection hint.** Any Connected App deployment recipe that
doesn't include "fetch the new Consumer Key from the target
org" is going to fail with `invalid_client_id`.
