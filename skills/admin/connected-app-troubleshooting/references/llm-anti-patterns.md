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

---

## Anti-Pattern 9: Quoting a canonical list of `LoginHistory.Status` values

**What the LLM generates.** "Look for `Status` = 'Invalid Password', 'Login
Rate Exceeded', 'User is Frozen', or 'Restricted IP'" — presented as the
platform's enumerated value set, often as a lookup table mapping each string to
a fix.

**Why it happens.** Every other picklist on the object publishes its values —
`LoginType`, `LoginSubType`, `TlsProtocol` are all documented lists — so the
shape of the answer is familiar and the model fills it in.

**Correct pattern.** `Status` is typed `string`, not picklist, and the Object
Reference says only that it "[d]isplays the status of the attempted login.
Status is either success or a reason for failure." There is no published value
set to match against. Query the rows, read the strings the org actually emitted,
and quote those. Use `LoginSubType`, which *is* a restricted picklist with a
documented OAuth value list, as the structured discriminator instead.

**Detection hint.** Any triage advice that pattern-matches `Status` against a
remembered catalog, or that filters on it, is wrong twice over — the values are
not published and the field is outside the twelve filterable ones (gotcha 11).

---

## Anti-Pattern 10: Delivering a diagnosis with no recorded evidence

**What the LLM generates.** "The refresh token policy is almost certainly set to
expire immediately — change it to valid until revoked." One cause, high
confidence, no queries run, no alternatives ruled out.

**Why it happens.** The most-documented cause is also the most probable one in
training data, and it is often right. Being often right is what makes the habit
survive.

**Correct pattern.** `invalid_grant` has at least five causes and the runbook has
eleven rows. Run the three evidence queries first, record what each returned
including zero-row results, and name which rows the evidence eliminated. The
diagnosis record in `templates/connected-app-diagnosis-record.yaml` exists for
this; the checker fails a record whose evidence entries lack a `result`.

**Detection hint.** A proposed fix that arrives before any query result, or a
write-up whose "root cause" section has no "ruled out" section, has skipped the
diagnosis and gone straight to the most familiar answer.
