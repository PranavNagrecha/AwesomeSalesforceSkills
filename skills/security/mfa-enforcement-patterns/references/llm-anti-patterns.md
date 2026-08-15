# LLM Anti-Patterns — MFA Enforcement

Mistakes AI assistants reliably make when asked to plan or troubleshoot MFA in
Salesforce.

## Anti-Pattern 1: "Enable MFA" as a One-Line Answer

**What the LLM generates:** "Turn on multi-factor authentication in Setup and require
it for all users."

**Why it happens:** MFA reads as a boolean, and the request is usually phrased as one.

**Correct pattern:**

```
The interactive-login case is already handled:

  "To help customers satisfy the MFA requirement, MFA is a default part of the
   direct login experience for production orgs."

The work is everything that is NOT a direct interactive login. Build the matrix
first:

  Direct interactive login  Salesforce default in production - already handled
  SSO users                 IdP policy; the OBLIGATION stays with you
  Non-human integration     token-based OAuth; no interactive login exists
  Human using user/password
    against an API          treat as an interactive user, not an integration
  Break-glass admin         MFA + a time-boxed exception + compensating control
  Experience Cloud/external separate configuration, separate decision

Every failed rollout fails on a population nobody listed - and it is never the
interactive users.
```

**Detection hint:** an MFA plan with no population segmentation, or one whose first
step is a Setup toggle.

---

## Anti-Pattern 2: Calling the Security Token a Second Factor

**What the LLM generates:** "The integration already appends a security token, so it
satisfies MFA."

**Why it happens:** The token is an additional secret, and "additional secret" reads
as "additional factor."

**Correct pattern:**

```
Salesforce's definition:

  "requires users to prove their identity by supplying two or more pieces of
   evidence (or factors) ... One factor is something the user KNOWS, such as
   their username and password. Other factors include something the user HAS,
   such as an authenticator app or security key."

A security token is something the user KNOWS, sent in the SAME channel as the
password. Two secrets in one channel is one factor.

The fix is not to relabel it. It is to remove the interactive login: migrate to
the client credentials or JWT bearer flow, where there is no password and no
challenge to complete.
```

**Detection hint:** "security token" offered as satisfying MFA, or a compliance
classification based on the number of strings sent rather than the mechanism.

---

## Anti-Pattern 3: Exempting Integration Users Instead of Migrating Them

**What the LLM generates:** "Add the integration users to the MFA exemption list so
the nightly jobs keep working."

**Why it happens:** It is the change that unblocks the cutover with the least work,
and exemption is a real feature.

**Correct pattern:**

```
An exemption preserves the problem. The credential stays a copyable string in a
config store, subject to profile password expiry, and it is exactly the shape
credential stuffing targets.

Migrate instead:

  <isClientCredentialEnabled>true</isClientCredentialEnabled>
  <oauthClientCredentialUser>etl.warehouse@example.com</oauthClientCredentialUser>

The platform enforces the design: oauthClientCredentialUser "must have the API
Only permission." You cannot bind a machine flow to a UI-capable identity.

Where no shared secret may cross the wire, use JWT bearer instead.

MFA then stops applying because there is no interactive login to protect - which
is a better outcome than an exemption that says the same thing on paper.
```

**Detection hint:** an MFA plan whose integration strategy is an exemption list rather
than a flow migration.

---

## Anti-Pattern 4: Treating SSO as Delegating the Obligation

**What the LLM generates:** "With SSO, MFA is enforced by your identity provider, so
no Salesforce-side work is needed."

**Why it happens:** The authentication genuinely moves to the IdP, and the
responsibility appears to move with it.

**Correct pattern:**

```
The requirement "applies equally to direct logins with a Salesforce username and
password and to logins via single sign-on (SSO)."

Two Salesforce-side tasks remain:

1. COVERAGE. Get the IdP owner to enumerate in writing which populations the MFA
   policy covers AND WHICH IT EXCLUDES. Coverage is about the exclusions -
   contractors, legacy groups, and service accounts are the usual gaps, and
   Salesforce cannot see them.

2. VISIBILITY. "Salesforce pulls the authentication method from JSON strings in
   the OpenID Connect token returned by your provider. Work with your provider
   to define the values used in the JSON strings." Without that agreement,
   Login History cannot show which logins met MFA and you have no evidence.

For an enforceable control rather than a report, use session security levels -
"Multi-factor authentication (MFA) requires HIGH_ASSURANCE."
```

**Detection hint:** an SSO answer with no coverage confirmation and no Authentication
Method References step.

---

## Anti-Pattern 5: Building a Report Where the Platform Can Refuse

**What the LLM generates:** "Report on Login History to identify users who logged in
without MFA and follow up with them."

**Why it happens:** Detective controls are easy to describe and require no
configuration risk.

**Correct pattern:**

```
For populations where a non-MFA session must not reach the data, the platform
can refuse rather than report:

  <ProfileSessionSetting xmlns="http://soap.sforce.com/2006/04/metadata">
      <profile>Finance Users</profile>
      <requiredSessionLevel>HIGH_ASSURANCE</requiredSessionLevel>
      <sessionTimeout>60</sessionTimeout>
  </ProfileSessionSetting>

  "Session security levels control access to certain types of resources based on
   the type of authentication used for logging in to the current session. For
   example, username and password authentication requires the standard session
   security level. Multi-factor authentication (MFA) requires HIGH_ASSURANCE."

Do NOT offer LOW as a lighter-touch option: "The LOW level isn't available or
used in the Salesforce UI. It's used at the API level, but users assigned to
this level experience unpredictable and reduced functionality."

And warn about the side effect of setting sessionTimeout per profile: "Changes
to the org-wide timeout value don't apply to users of this profile." That
profile is opted out of future org-wide session policy changes, permanently.
```

**Detection hint:** a purely detective MFA control for a sensitive population, or a
`requiredSessionLevel` recommendation with no note about the timeout side effect.

---

## Anti-Pattern 6: Designing an MFA "Exception" That the Platform No Longer Honours

**What the LLM generates:** a custom object with `User__c`, `Reason__c`, and
`Approved__c`, a note to review it periodically, and — the worse half — the
assumption that holding a row in it, or the "Waive Multi-Factor Authentication for
Exempt Users" permission, keeps the user off the MFA challenge.

**Why it happens:** The prompt asks for an exception process; periodic review is the
standard-sounding governance answer; and the model's training data predates the 2026
enforcement waves, when the waiver permission genuinely worked.

**Correct pattern:**

```
TWO separate errors to correct.

1. There is no exemption left to grant. After the 2026 enforcement waves the
   org-wide MFA setting cannot be deselected, and the "Waive Multi-Factor
   Authentication for Exempt Users" permission "no longer automatically
   exempt[s] users from MFA" - holders are "prompted to enroll and use an MFA
   verifier at login." A break-glass admin is also a PRIVILEGED user, so they
   need a PHISHING-RESISTANT verifier (built-in authenticator, passkey, FIDO2
   key, or certificate). Salesforce Authenticator and TOTP do not qualify.
   Dates and quotes: security/mfa-enforcement-strategy.

2. "Review periodically" is how records become permanent. Make the review
   structural:

  MFA_Elevated_Access__c
    User__c                  Lookup(User)      required
    Justification__c         Long Text Area    required
    Approver__c              Lookup(User)      required
    Review_Due__c            Date              required
    Verifier_Type__c         Picklist          required
        (Security Key | Built-in Authenticator | Passkey | Certificate)
    Compensating_Control__c  Text              required

  Validation rule:  Review_Due__c > TODAY() + 180
  Error: "Elevated-access reviews cannot be scheduled more than 180 days out.
          Renew with a fresh approval instead of extending."

  The 180 days is a governance convention, not a Salesforce requirement, and it
  bounds a REVIEW, not a waiver.

Renewal is a NEW RECORD with a NEW APPROVAL, never an edit to the date. An edit
is invisible; a new record with a new approver is an event someone must defend.

The compensating control field is not decoration - a register row without one is
a gap with paperwork. For a break-glass admin: vaulted credentials with checkout
logging, IP restriction where the address is static, a short session timeout,
and an alert on every login.

Send the expiring-soon report to the APPROVERS, not the security team.
```

**Detection hint:** an exception object with no required expiry, no validation rule
capping it, or no compensating control field.

---

## Anti-Pattern 7: Assuming API Only Exempts a Human

**What the LLM generates:** "Mark the user API Only — MFA doesn't apply to API-only
users."

**Why it happens:** API Only sounds like "not a person," and integrations are the
population MFA does not apply to.

**Correct pattern:**

```
API Only governs WHERE the identity can go - "they can access Salesforce only via
APIs, regardless of their other permissions" - not HOW it authenticates.

A human authenticating with a username and password is an interactive user with
the same obligation and the same phishing exposure, whatever the flag says.

Classify by WHO AUTHENTICATES:
  - a person, with a password  -> interactive user; MFA applies
  - an unattended process, with a token -> integration; no interactive login

For the analyst running scripts, either give them a normal user with MFA, or
move the tooling onto a token-based flow bound to a genuine service identity -
which the platform will require to have API Only anyway.
```

**Detection hint:** API Only offered as an MFA exemption mechanism, or a population
classified as "integration" on the basis of a permission rather than of who
authenticates.

---

## Anti-Pattern 8: Forgetting the Users Who Cannot Install an Authenticator App

**What the LLM generates:** a rollout plan whose enrolment guidance covers only the
Salesforce Authenticator mobile app.

**Why it happens:** It is the flagship path and the one the documentation leads with.

**Correct pattern:**

```
Salesforce's own definition already allows for the alternative: other factors
include "something the user has, such as an authenticator app OR SECURITY KEY."

Identify these populations during the matrix step, at T-30, because both
alternatives need procurement and distribution lead time:

  device-prohibited facilities   security keys
  call-centre / shared stations  security keys, or desktop TOTP
  no corporate mobile            desktop TOTP, or a security key

A plan that discovers them at cutover has a help-desk queue and no hardware.
```

**Detection hint:** enrolment guidance mentioning only a mobile app, with no fallback
path and no procurement lead time.

---

## Anti-Pattern 9: Ending the Migration When the New Flow Works

**What the LLM generates:** "Once the connected app returns tokens successfully, the
integration is migrated — you can enforce MFA."

**Why it happens:** The new path working is the visible success criterion.

**Correct pattern:**

```
Adding the new path is safe; removing the old one is the migration. Legacy flows
keep working silently - a fallback branch, an old deployment, a second consumer.

Completion criterion: 30 consecutive days with NO username-password flow subtype
in Login History for that identity. Login History distinguishes the flow -
client credentials, user-agent (including hybrid and ID-token variants),
username-password, and web-server (including hybrid web-server).

Then block the legacy flows at the org level, per Salesforce's own guidance:
"Important: For security, we recommend blocking user-agent and username-password
flows."

That block is the irreversible step, so it goes last - once the evidence says
nothing depends on the old path.
```

**Detection hint:** a migration plan with no observation window, or one that blocks
legacy flows before the evidence exists.
