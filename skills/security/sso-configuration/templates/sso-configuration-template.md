# SSO Configuration — Design and Cutover Workbook

Complete one workbook per identity provider being connected. Replace every
`[REPLACE: ...]` marker. A marker left in place means the decision has not been
made, not that it does not apply — record "not applicable" explicitly.

---

## 1. Scope and Trust Direction

**Org:** `[REPLACE: org name and My Domain login URL, e.g. acme -> https://acme.my.salesforce.com]`
**Environment:** `[REPLACE: production | full sandbox | partial sandbox | scratch]`
**Requested by:** `[REPLACE: name and team]`
**Target cutover date:** `[REPLACE: YYYY-MM-DD]`

Trust direction (tick all that apply):

- [ ] Salesforce is the **service provider** — an external IdP authenticates our users
- [ ] Salesforce is the **identity provider** — a downstream app trusts Salesforce
- [ ] Both, independently configured

Audience in scope:

- [ ] Internal users (Salesforce licences)
- [ ] Experience Cloud external users — site: `[REPLACE: site name]`
- [ ] API-only / integration users — plan: `[REPLACE: how these authenticate; they are not covered by an interactive browser flow]`

---

## 2. Mechanism Decision

| Question | Answer |
|---|---|
| Protocol the IdP speaks | `[REPLACE: SAML 2.0 | OpenID Connect | both]` |
| Chosen mechanism | `[REPLACE: SamlSsoConfig | AuthProvider | ExtlClntAppSamlConfigurablePolicies]` |
| Why not the alternative | `[REPLACE: one sentence]` |
| Delegated authentication considered? | `[REPLACE: no — reason | yes — record the Salesforce enablement request reference]` |

---

## 3. Identity Mapping

| Item | Value |
|---|---|
| `identityMapping` | `[REPLACE: FederationId | Username | UserId]` |
| `identityLocation` | `[REPLACE: SubjectNameId | Attribute]` |
| If `Attribute`, `attributeName` | `[REPLACE: attribute name, or n/a]` |
| Claim/attribute the IdP will send | `[REPLACE: e.g. user.objectid, employeeNumber]` |
| Who populates the Salesforce field | `[REPLACE: named owner + mechanism: data load / JIT / SCIM]` |

Pre-cutover data checks — record the counts, not "done":

```soql
-- Blanks in the in-scope population
SELECT COUNT(Id) FROM User
WHERE IsActive = true AND FederationIdentifier = null
  AND Profile.UserLicense.Name = '[REPLACE: licence name]'
```
Result: `[REPLACE: count — must be 0 before cutover]`

```soql
-- Collisions
SELECT FederationIdentifier, COUNT(Id) FROM User
WHERE IsActive = true AND FederationIdentifier != null
GROUP BY FederationIdentifier HAVING COUNT(Id) > 1
```
Result: `[REPLACE: count — must be 0 before cutover]`

---

## 4. Values Exchanged With the Identity Provider

Fill both columns. The left column is what Salesforce needs; the right is what the IdP team needs back.

| Salesforce needs from the IdP | Value |
|---|---|
| Issuer (`issuer`) | `[REPLACE: exact Issuer element the IdP emits]` |
| Sign-on URL (`loginUrl`) | `[REPLACE: IdP SSO endpoint — required for SP-initiated]` |
| Signing certificate (`validationCert`) | `[REPLACE: certificate label after upload to Certificate and Key Management]` |
| Certificate expiry | `[REPLACE: YYYY-MM-DD]` |
| Encrypts assertions? | `[REPLACE: no | yes -> decryptionCertificate = ...]` |

| IdP needs from Salesforce | Value |
|---|---|
| Audience / Entity ID (`samlEntityId`) | `[REPLACE: e.g. https://acme.my.salesforce.com]` |
| Assertion Consumer Service (Reply) URL | `[REPLACE: read from the saved SAML configuration page — do not construct it]` |
| Sign-on URL for the IdP app tile | `[REPLACE: My Domain login URL]` |
| NameID format | `[REPLACE: e.g. unspecified | emailAddress | persistent]` |
| Signature algorithm | `[REPLACE: RSA-SHA256 unless the IdP documents a limitation]` |

---

## 5. Provisioning

| Item | Decision |
|---|---|
| Approach | `[REPLACE: pre-provisioned | standard JIT | handler-based JIT | push/SCIM]` |
| `userProvisioning` | `[REPLACE: true | false]` |
| Handler class | `[REPLACE: class name implementing Auth.SamlJitHandler or Auth.RegistrationHandler, or n/a]` |
| Execution user | `[REPLACE: username — must hold Manage Users]` |
| Execution user's permission set | `[REPLACE: name — not a System Administrator profile]` |
| Deactivation / leaver process | `[REPLACE: how a user is disabled when they leave the IdP — JIT has no leaver event]` |

Handler test coverage — required negative paths:

- [ ] Required claim absent from the attribute map
- [ ] Claim present but matches no record (Contact, Account, Profile)
- [ ] Duplicate matching key
- [ ] Claim name case mismatch (the map is case-sensitive)

---

## 6. Session, MFA and Logout

| Item | Decision |
|---|---|
| Who asserts MFA | `[REPLACE: IdP | Salesforce | both — and why]` |
| `requireMfa` on the auth provider | `[REPLACE: true | false | n/a]` |
| `logoutUrl` | `[REPLACE: destination — do not leave at the https://salesforce.com default]` |
| Single logout configured | `[REPLACE: no | yes -> singleLogoutUrl + binding]` |
| Experience Cloud site logout URL | `[REPLACE: value or n/a]` |
| `errorUrl` | `[REPLACE: publicly reachable page that does NOT require authentication]` |
| Login IP ranges layered on top | `[REPLACE: no | yes — note that "Enforce login IP ranges on every request" affects all profiles with IP restrictions]` |

---

## 7. Break-Glass Plan

| Item | Value |
|---|---|
| Break-glass account | `[REPLACE: username — dedicated, non-human]` |
| Credential storage | `[REPLACE: vault path or secret name — never in this document]` |
| MFA method and who holds it | `[REPLACE: at least two named people]` |
| Login URL to use | `[REPLACE: exact My Domain login URL]` |
| Last successfully tested | `[REPLACE: YYYY-MM-DD, from a session-free browser]` |
| Re-test cadence | `[REPLACE: e.g. quarterly and after any password/MFA policy change]` |

---

## 8. Cutover Sequence

Two separate changes on two separate approvals.

1. **Enable** — deploy the configuration, assign it, pilot with `[REPLACE: pilot user]` while the login form is still available.
   Tested: SP-initiated `[ ]` · IdP-initiated `[ ]` · deep link to a record `[ ]` · logout `[ ]`
2. **Verify** — Setup → Login History shows the pilot arriving on the My Domain login URL. Evidence: `[REPLACE: date/time of the verified row]`
3. **Prove break-glass** — section 7 completed and dated.
4. **Enforce** — change the My Domain login policy so the generic hostnames stop accepting logins. Approved by: `[REPLACE: name]` on `[REPLACE: YYYY-MM-DD]`
5. **Rollback trigger and step** — `[REPLACE: what condition reverses step 4, and who can do it]`

---

## Validation

Run these before signing the workbook off. Every line must be a fact, not an intention.

- [ ] Identity-mapping blank count and collision count are both recorded as 0
- [ ] `samlEntityId` and the IdP's configured audience were compared character by character, including any trailing slash
- [ ] `errorUrl` was opened in a private window with no session and rendered a usable page
- [ ] `logoutUrl` is not `https://salesforce.com`
- [ ] Every handler-bearing configuration names an execution user holding Manage Users
- [ ] Certificate expiry dates and owners are recorded in section 4
- [ ] Break-glass account completed a real login through the My Domain URL, dated in section 7
- [ ] Enable and Enforce are booked as separate approvals on separate days
- [ ] `python3 skills/security/sso-configuration/scripts/check_sso_configuration.py --manifest-dir <metadata-dir>` exits 0

**Sign-off:** `[REPLACE: name]` — `[REPLACE: YYYY-MM-DD]`

## Notes and Deviations

`[REPLACE: record any deviation from the standard pattern and the reason — for example an RSA-SHA1 signature method forced by an IdP limitation, with the remediation date]`
