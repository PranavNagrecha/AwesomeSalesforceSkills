# LLM Anti-Patterns — MFA Enforcement

## Anti-Pattern 1: "Enable MFA" Ticket = Done

**What the LLM generates:** a one-line plan "toggle MFA in Identity
settings."

**Why it happens:** sees MFA as a boolean.

**Correct pattern:** inventory users by type, handle SSO assertion,
migrate username/password integrations.

## Anti-Pattern 2: Treating Security Token As MFA

**What the LLM generates:** "user already has security token, they are
MFA'd."

**Why it happens:** conflates factors.

**Correct pattern:** security token is an API signature, not a second
authentication channel. MFA requires Authenticator / TOTP / key.

## Anti-Pattern 3: "Mark Integration User API-Only And Move On"

**What the LLM generates:** sets API-Only and skips MFA planning.

**Why it happens:** assumes flag exempts MFA. It does not.

**Correct pattern:** migrate to Connected App + OAuth (JWT or Client
Credentials).

## Anti-Pattern 4: Exception With No Expiry

**What the LLM generates:** an exception object without a required
expiry field.

**Why it happens:** "we'll review later."

**Correct pattern:** validation rule enforces max expiry; monthly review.

## Anti-Pattern 5: SSO Without Auth Context

**What the LLM generates:** SSO configured, done.

**Why it happens:** thinks IdP MFA is visible to Salesforce automatically.

**Correct pattern:** configure SAML `AuthnContextClassRef` or OIDC `amr`
to reflect MFA; verify in Login History.
