# MFA Enforcement — Gotchas

## 1. SSO Without MFA Assertion Is Not MFA

If the IdP does MFA but the SAML assertion does not include an
MFA-level `AuthnContextClassRef`, Salesforce considers the session
single-factor. Reports look clean; audit will not.

## 2. Security Token Is Not A Second Factor

Appending a security token to a password is not MFA. It is a secret in
the same channel. Audits sometimes misreport this.

## 3. Integration User With Username/Password Will Break

Once MFA is enforced, legacy integrations doing SOAP login with
username/password will fail. Inventory and migrate before cutover, not
after the ticket queue explodes.

## 4. API-Only Permission Does Not Exempt MFA

Giving a user API-Only permission does not remove the MFA requirement.
Use a Connected App with OAuth instead.

## 5. "Permanent" Exceptions Drift

Exceptions with no expiry become permanent by neglect. Mandatory expiry
and monthly review are the only reliable controls.

## 6. Experience Cloud Users Are Separate

External/community users have their own MFA configuration. Do not
assume the internal MFA rollout covers them.

## 7. Authenticator Requires Mobile

Users without a mobile device need TOTP (Authy, Google Authenticator)
or a security key. Have the fallback path documented before rollout.

## 8. Session Timeout Interacts With MFA UX

Short session timeouts force frequent re-auth, each of which may
prompt MFA. Balance session lifetime with MFA friction.
